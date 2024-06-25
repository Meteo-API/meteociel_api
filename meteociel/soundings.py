"""
Manage the extraction of upper air sounding data.
"""

from datetime import datetime

import numpy as np
import pandas as pd
from requests import get

from meteociel import cities, utils

AVAILABLE_OBS_HOURS = (0, 6, 12, 18)


def sounding_conv(data):
    """Adapt ``utils.conv`` to fit conversion from sounding data."""
    return utils.conv(data, separators=("°", "%"), multi_value_sep=(" / ",), strip_char=(" ",))


def sounding_obs(date: datetime, city_name: str):
    """
    Get the data of the upper air sounding observation from the city name and date.

    Parameters
    ----------
    date : ``datetime``
        The date for which data is to be extracted in the form of a datetime object.

        .. warning::
            The upper air souding from observations are only available at 00:00, 06:00, 12:00 and
            18:00 (GMT).

    city_name : ``str``
        The name of the requested city.

    Returns
    -------
    out : ``tuple(str, pd.DataFrame)``
        A tuple that contains two elements:

        * the name of the city

        * A DataFrame that contains all the variables from the sounding.

    Exemples
    --------

        >>> from datetime import datetime
        >>> from meteociel.soundings import sounding_obs
        >>> city_name, data = sounding_obs(
        ...     datetime.strptime("2022-08-18 00", "%Y-%m-%d %H"), "Ajaccio"
        ... )
        >>> city_name
        'ajaccio'
        >>> data
              altitude  pressure  temperature  ...  dew_point     wind_u     wind_v
        0          5.0    1006.0         25.1  ...       18.1  28.342661  19.845745
        1         18.0    1004.0         25.0  ...       18.2  39.172546  23.537240
        2         31.0    1003.0         24.9  ...       18.3  38.624733  22.300000
        3         44.0    1002.0         25.2  ...       19.2  36.459669  21.050000
        4         57.0    1000.0         25.9  ...       20.5  35.247174  19.537828
        ...        ...       ...          ...  ...        ...        ...        ...
        2547   36313.0       5.0        -33.5  ...      -71.4  -7.700029  -5.391619
        2548   36453.0       5.0        -33.6  ...      -71.5  -8.375461  -4.267511
        2549   36602.0       5.0        -34.1  ...      -71.8  -8.715528  -3.521302
        2550   36758.0       5.0        -34.5  ...      -72.1  -8.833111  -3.214989
        2551   36908.0       5.0        -34.5  ...      -72.1  -8.833111  -3.214989
        >>> data["temperature"]
        0       25.1
        1       25.0
        2       24.9
        3       25.2
        4       25.9
                ...
        2547   -33.5
        2548   -33.6
        2549   -34.1
        2550   -34.5
        2551   -34.5
        Name: temperature, Length: 2552, dtype: float64

    """
    # Check that the requested hour is available
    if date.hour not in AVAILABLE_OBS_HOURS:
        available_hours = [f"{str(hour).zfill(2)}h" for hour in AVAILABLE_OBS_HOURS]
        raise ValueError(
            f"{str(date.hour).zfill(2)}h is not a valid hour for sounding from observations, the"
            f" available hours are: {', '.join(available_hours)}"
        )

    # Compute ids for extraction
    date_id = utils.get_seconds(date)
    city_id, city = list(cities.get_city(city_name, keys={"has-sounding": True}).items())[0]

    # Get the data
    response = get(
        "https://www.meteociel.fr/cartes_obs/sondage_display.php",
        params={"id": city_id, "date": date_id, "map": 4, "map2": 4},
        timeout=10,
    )
    data = utils.get_data_from_html(
        response,
        {
            "cellpadding": "2",
            "style": (
                "border-collapse: collapse; background-color: #80ffff; text-align:center; "
                "font-family: Verdana; font-size: 8pt"
            ),
            "border": "1",
        },
        skiprows=1,
    )

    wind_dir, wind_spd = sounding_conv(data[6])

    # Return a DataFrame
    return city["names"][0], pd.DataFrame.from_dict(
        {
            "altitude": sounding_conv(data[0])[::-1],
            "pressure": sounding_conv(data[1])[::-1],
            "temperature": sounding_conv(data[2])[::-1],
            "wetbulb_temperature": sounding_conv(data[3])[::-1],
            "dew_point": sounding_conv(data[4])[::-1],
            "humidity": sounding_conv(data[5])[::-1],
            "wind_u": -wind_spd * np.sin(np.radians(wind_dir))[::-1],
            "wind_v": -wind_spd * np.cos(np.radians(wind_dir))[::-1],
        }
    )


def sounding_arome(*, lon: float = None, lat: float = None, city_name: str = "", timestep: int = 1):
    """
    Extract the data of the upper air sounding simulated by the AROME model. You can pass
    coordinates or a city name. If you pass both, the city name will take priority.

    Parameters
    ----------
    lon : ``float``, keyword-only, optionnal
        By default: ``None``. The longitude of the sounding.
    lat : ``float``, keyword-only,  optionnal
        By default: ``None``. The latitude of the sounding.
    city_name : ``str``, keyword-only,  optionnal
        By default: ``""``. The name of the city where the simulated sounding is to be extracted.
    timestep : ``int``, keyword-only, optionnal
        By default: ``1``. The number of hours elapsed since the start of the AROME run.

    Returns
    -------
    out : ``tuple(str, pd.DataFrame)``
        A tuple that contains two elements:

        * the name of the city

        * A DataFrame that contains all the variables from the sounding.

    Exemples
    --------
    From city name::

        >>> from meteociel.soundings import sounding_arome
        >>> data = sounding_arome(city_name="Rennes")
        >>> data[0]  # city name
        'Rennes'
        >>> data[1]  # the sounding data
            altitude  pressure  temperature  ...      wind_v
        0       40.0    1018.0         14.0  ...  -28.123613
        1       58.0    1015.0         13.9  ...  -43.175688
        2       73.0    1013.0         13.8  ...  -60.051451
        3       88.0    1012.0         13.7  ...  -70.619716
        4      113.0    1009.0         13.5  ...  -87.114112
        5      138.0    1006.0         13.3  ...  -99.465583
                 ...       ...          ...  ...         ...
        48   15026.0     125.0        -50.9  ...  -16.390010

    From coordinates and with 12 hours of run::

        >>> from meteociel.soundings import sounding_arome
        >>> data = sounding_arome(lon=5, lat=42, timestep=12)
        >>> data[0]
        '42N-5E'
        >>> data[1]
            altitude  pressure  temperature              wind_v
        0        2.0    1016.0         17.5  ...  -5.353045e+00
        1       20.0    1013.0         17.4  ...  -2.890644e+01
        2       35.0    1011.0         17.2  ...  -2.917409e+01
        3       50.0    1010.0         17.1  ...  -4.476484e+01
        4       75.0    1007.0         16.9  ...  -6.075706e+01
        5      100.0    1004.0         16.7  ...  -6.718071e+01
                 ...       ...         ...   ...            ...
        48   15029.0     125.0        -51.0  ...  -2.098393e+01
    """
    if city_name:
        response = get(
            "https://www.meteociel.fr/temps-reel/lieuhelper.php",
            params={"str": city_name, "dept": 0},
            timeout=10,
        )

        if not response.ok:
            raise ConnectionError(f"connection failed with code: {response.status_code}")

        if response.text == "[NONE]":
            raise cities.CityNotFoundError("this city isn't known by Météociel")

        lon, lat = [float(i) for i in response.text.split("|")[3:5]]
        city_name = response.text.split("|")[0]

    if not lon and not lat:
        raise ValueError("you should give a couple of coordinates lon/lat or a city name")

    if not city_name:
        city_name = f"{lat}N-{lon}E"

    # Get the data
    response = get(
        "https://www.meteociel.fr/modeles/sondage2arome.php",
        params={
            "archive": 0,
            "ech": timestep,
            "map": 4,
            "wrf": 0,
            "region": "",
            "type": 1,
            "lon": lon,
            "lat": lat,
        },
        timeout=10,
    )
    data = utils.get_data_from_html(
        response,
        {
            "cellpadding": "2",
            "style": (
                "border-collapse: collapse; background-color: #80ffff; text-align:center; "
                "font-family: Verdana; font-size: 8pt"
            ),
            "border": "1",
        },
        skiprows=1,
    )

    # Get the date
    metadata = utils.get_data_from_html(response)[1][0].split()
    month = {
        "janvier": "01",
        "février": "02",
        "mars": "03",
        "avril": "04",
        "mai": "05",
        "juin": "06",
        "juillet": "07",
        "août": "08",
        "septembre": "09",
        "octobre": "10",
        "novembre": "11",
        "décembre": "12",
    }

    date = (
        f"{metadata[6]}{month[metadata[5]]}{str(metadata[4]).zfill(2)}{metadata[1]}+{timestep}h"
        if metadata
        else ""
    )

    wind_dir, wind_spd = sounding_conv(data[6])

    # Return a DataFrame
    return f"{city_name}_{date}", pd.DataFrame.from_dict(
        {
            "altitude": sounding_conv(data[0])[::-1],
            "pressure": sounding_conv(data[1])[::-1],
            "temperature": sounding_conv(data[2])[::-1],
            "wetbulb_temperature": sounding_conv(data[3])[::-1],
            "dew_point": sounding_conv(data[4])[::-1],
            "humidity": sounding_conv(data[5])[::-1],
            "wind_u": -wind_spd * np.sin(np.radians(wind_dir))[::-1],
            "wind_v": -wind_spd * np.cos(np.radians(wind_dir))[::-1],
        }
    )
