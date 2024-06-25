"""
Manage forecasts and trends data for cities all around the world.
"""

import re
import warnings
from datetime import UTC, datetime, timedelta

import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from requests import get

from meteociel import utils

MODES = ("forecasts", "trends")

MODELS = ("gfs", "wrf", "wrf-1h", "arome", "arome-1h", "arpege-1h", "iconeu", "icond2")


class TooManyCitiesError(Exception):
    """If several cities can match the search."""


class UnknownModeError(Exception):
    """The given mode is unknown."""


class UnknownModelError(Exception):
    """The given model is unknown."""


def forecast_conv(data):
    """Adapt ``utils.conv`` to fit conversion from forecasts data."""
    return utils.conv(data, separators=("°", "%"), strip_char=(" ",))


def get_forecast_url(
    *, city_name: str = "", city_id: str = "", mode: str = "forecasts", model: str = "gfs"
):
    """
    Search and return the correct url to get the requested forecasts data.

    .. seealso:: The parameters are the same as for the ``meteociel.forecasts.forecast`` function.

    Parameters
    ----------
    city_name : ``str``, keyword_only, optionnal
        By default: ``""``. The requested city name.
    city_id : ``str``, keyword_only, optionnal
        By default: ``""``. By passing directly the city id, the API will search by id rather than
        by name.
    mode : ``str``, keyword_only, optionnal
        By default: ``"forecasts"``. There is two available modes:

        * ``"forecasts"`` that provides data for the three days ahead;

        * ``"trends"`` that provides data for the ten days ahead but with lower confidence.
    model : ``str``, keyword_only, optionnal
        By default: ``"gfs"``. The model from which the data are obtained.

        .. note::
            The ``model`` parameter is only available in ``"forecasts"`` mode, otherwise it will
            ignored.

    Returns
    -------
    out : ``str``
        The url of the data.

    Raises
    ------
    ConnectionError
        Can be raised if the request fails.
    TooManyCitiesError
        This exception is raised if the given city name match several cities.

    Exemples
    --------

        >>> from meteociel.forecasts import get_forecast_url
        >>> url = get_forecast_url(city_name="Toulouse 31000", mode="forecasts", model="gfs")
        >>> url
        https://www.meteociel.fr/previsions/10979/toulouse.htm

    """
    # Process mode and model
    if (mode := {"forecasts": "previsions", "trends": "tendances"}[mode]) == "previsions":
        mode = f"{mode}-{model}" if model != MODELS[0] else mode
    elif model != MODELS[0]:
        warnings.warn(
            "models are only available for forecasts, the given model will be ignored.",
            stacklevel=1,
        )

    # Searching for the requested city
    response = get(
        "https://www.meteociel.fr/prevville.php",
        params={"action": "getville", "villeid": city_id, "ville": city_name, "envoyer": "OK"},
        timeout=10,
    )
    if not response.ok:
        raise ConnectionError(f"connection failed with code: {response.status_code}")

    # Check if the city has been found on first pass
    url = re.search(r"<script lang=javascript>location.href='/([^'^/]+)/([^']+)'", response.text)

    # If city not found: try a second pass
    if not url:
        soup = BeautifulSoup(response.text, features="html5lib")
        cities = []
        for i in soup.find("table", {"border": "0", "width": "300px"}).find_all("li"):
            url, name = re.search(
                r"<li> <a href=\"/([^'^/]+)/([^']+)\">([^<]+) </a>  </li>", str(i.extract())
            ).groups()[1:]
            name = name.replace("\xa0(\xa0", " (").replace("\xa0)", ")")

            # If requested city has been found on second pass
            if city_name == name:
                return f"https://www.meteociel.fr/{mode}/{url}"
            cities.append(f"- {name}")

        # If the city hasn't been found
        raise TooManyCitiesError(
            f"too many cities can match your search, please choose one city in the "
            f"following list:\n{'\n'.join(cities)}"
        )

    # If the city has been found on first pass
    return f"https://www.meteociel.fr/{mode}/{url.groups()[1]}"


def process_datetime(data: list):
    """Manage the shift into ``data`` due to the date."""
    lagging_index = 0
    date = []
    start_time = datetime.now(UTC)
    start_time = datetime.strptime(f"{start_time.year} {start_time.month}", "%Y %m")
    for index, value in enumerate(data[0]):
        # If the row viewed is an hour
        if re.search(r"([0-2][0-9]:[0-5][0-9])", value):
            # Save the date
            date.append(start_time + timedelta(hours=int(data[0][index].split(":")[0])))

        # If it's a date
        else:
            # Update the start_date
            if lagging_index == 0:
                day = int(re.search(r"([0-9]+)", value).groups()[0])
                start_time += timedelta(days=day - 1)
            else:
                start_time += timedelta(days=1)

            # Save the date
            date.append(start_time + timedelta(hours=int(data[1][index].split(":")[0])))

            # Shift all the columns
            for i in range(len(data) - 1):
                if i == len(data) - 2:
                    data[i][index] = data[i + 1][lagging_index]
                else:
                    data[i][index] = data[i + 1][index]
            lagging_index += 1

    # Suppress the hours (first column), extra data (last column) and add the date
    del (data[0], data[-1])
    data.insert(0, date)


def forecast(
    *, city_name: str = "", city_id: str = "", mode: str = "forecasts", model: str = "gfs"
):
    """
    Get the data of the forecasts or trends from the city name or id and given model. You can give
    the name or the id, but at least one of the both. If you give both, the id will have an higher
    priority.

    .. warning::
        Some cities across the world have the same name, so be careful when dumping data. To be
        sure, you can search by city id. Moreover, all the models aren't available everywhere.

        .. table:: Available models
            :widths: auto

            ==========  =====================  ==========
            Model name  Coverage               Resolution
            ==========  =====================  ==========
            GFS         Global                 25km
            WRF         Western Europe [1]_    5km
            AROME       France                 1km
            ARPEGE      Europe                 10km
            ICON-EU     Europe                 7km
            ICON-D2     Central Europe         2.2km
            ==========  =====================  ==========

    .. [1] Western Europe: France, UK, Germany, Spain and Italy.

    Parameters
    ----------
    city_name : ``str``, keyword-only, optionnal
        By default: ``""``. The name of the requested city.
    city_id : ``str``, keyword-only, optionnal
        By default, this feature is disabled. By passing directly the city id, the API will search
        by id rather than by name. The city id can be manually found by
        accessing: https://www.meteociel.fr/prevville.php, then search for the city you want, you
        will have an url of the form: ``https://www.meteociel.fr/previsions/CityId/CityName.htm``
        where ``CityId`` should be a number.

        .. important::
            Search by identifier takes precedence over search by name.

    mode : ``str``, keyword_only, optionnal
        By default: ``"forecasts"``. There is two available modes:

        * ``"forecasts"`` that provides data for the three days ahead;

        * ``"trends"`` that provides data for the ten days ahead but with lower confidence.
    model : ``str``, keyword_only, optionnal
        By default: ``"gfs"``. The model from which the data are obtained. The available models are:

        * ``"gfs"``: an american global model (25km);

        * ``"wrf"``, ``"wrf-1h"``: an american non-hydrostatic limited area model (5km) you can
          pass ``"wrf-1h"`` to have hourly data;

        * ``"arome"``, ``"arome-1h"``: a french limited area model (1km), hourly data are also
          available;

        * ``"arpege-1h"``: a french global area (10km), only hourly data available;

        * ``"iconeu"``: a german limited-area model (7km);

        * ``"icond2"``: a german limited-area model (2.2km).

        .. note::
            The ``model`` parameter is only available in ``"forecasts"`` mode, otherwise it will
            ignored.

    Returns
    -------
    out : ``tuple(str, pd.DataFrame)``
        A tuple that contains two elements:

        * the name of the city;

        * the requested forecast data in a ``DataFrame``.

    Raises
    ------
    UnknownModeError
        This exception is raised if the given ``mode`` is unknown.
    UnknownModelError
        This exception is raised if the given ``model`` is unknown.

    Exemples
    --------
    Extraction of Paris (France) weather forecasts data with the hourly arome model::

        >>> from meteociel.forecasts import forecast
        >>> city_name, data = forecast(city_name="Paris (75000)", model="arome-1h")
        >>> data
                          date  temperature  windchill  ...  rain  humidity  pressure
        0  2024-06-23 03:00:00         15.0       15.0  ...     0      80.0    1019.0
        1  2024-06-23 04:00:00         14.0       14.0  ...     0      79.0    1020.0
        2  2024-06-23 05:00:00         14.0       14.0  ...     0      78.0    1020.0
        3  2024-06-23 06:00:00         14.0       14.0  ...     0      78.0    1020.0
        4  2024-06-23 07:00:00         14.0       14.0  ...     0      77.0    1020.0
        5  2024-06-23 08:00:00         15.0       15.0  ...     0      73.0    1021.0
        ...                ...          ...        ...  ...   ...       ...       ...
        41 2024-06-24 20:00:00         27.0       30.0  ...     0      41.0    1014.0

    Extraction of weather trends by id (here for Berlin, Germany)::

        >>> from meteociel.forecasts import forecast
        >>> city_name, data = forecast(city_id=49679, mode="trends")
        >>> city_name
        berlin
        >>> data
                          date  temperature  windchill  ...  rain  humidity  pressure
        0  2024-06-26 20:00:00         27.0       32.0  ...   0.0      53.0    1009.0
        1  2024-06-27 02:00:00         20.0       26.0  ...   1.6      82.0    1010.0
        2  2024-06-27 08:00:00         22.0       27.0  ...   0.0      72.0    1009.0
        3  2024-06-27 14:00:00         32.0       36.0  ...   0.0      39.0    1008.0
        4  2024-06-27 20:00:00         23.0       31.0  ...   1.7      82.0    1009.0
        5  2024-06-28 02:00:00         21.0       28.0  ...   1.5      91.0    1008.0
        ...                ...          ...        ...  ...   ...       ...       ...
        25 2024-07-03 02:00:00         14.0       12.0  ...   2.6      94.0    1007.0

    """
    if mode not in MODES:
        raise UnknownModeError(
            f"'{mode}' isn't a valid mode, please report to the documentation to see the available "
            f"modes"
        )

    if model not in MODELS:
        raise UnknownModelError(
            f"'{model}' isn't a valid model, please report to the documentation to see the "
            f"available models"
        )

    response = get(
        get_forecast_url(city_name=city_name, city_id=city_id, mode=mode, model=model), timeout=10
    )
    city_name = response.url[response.url.rfind("/") + 1 : -4]
    data = utils.get_data_from_html(
        response,
        {
            "style": "border-collapse: collapse;",
            "border": "1",
            "cellpadding": "2",
            "cellspacing": "0",
            "bordercolor": "#a0a0b0",
        },
        skiprows=2,
    )

    # Processing date and time
    process_datetime(data)

    wind_dir = [float(i.split(" : ")[1].strip(" °")) for i in data[3]]
    rain = []
    for i in data[6]:
        if i == "--":
            rain.append(0)
        else:
            try:
                rain.append(float(i.split()[0]))
            except ValueError:
                rain.append(np.nan)

    return city_name, pd.DataFrame.from_dict(
        {
            "date": data[0],
            "temperature": forecast_conv(data[1]),
            "windchill": forecast_conv(data[2]),
            "wind_dir": wind_dir,
            "wind_spd": forecast_conv(data[4]),
            "wind_gust": forecast_conv(data[5]),
            "rain": rain,
            "humidity": forecast_conv(data[7]),
            "pressure": forecast_conv(data[8]),
            # "weather": data[9],
        }
    )
