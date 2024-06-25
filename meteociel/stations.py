"""
Manage the extration of stations data.
"""

from datetime import datetime

import pandas as pd
from requests import get

from meteociel import cities, utils


def station_conv(data):
    """Adapt ``utils.conv`` to fit conversion from station data."""
    return utils.conv(
        data, separators=("°", "%"), multi_value_sep=(" (",), strip_char=("(", ")", " ")
    )


def station(date: datetime, city_name: str):
    """
    Get the data of the station from the city name and date.

    Parameters
    ----------
    date : ``datetime``
        The date for which data is to be extracted in the form of a datetime object.

        .. note::
            You should only pass year, month and day, all values after these three ones will be
            ignored.

    city_name : ``str``
        The name of the requested city.

    Returns
    -------
    out : ``tuple(str, pd.DataFrame)``
        A tuple that contains two elements:

        * the name of the city

        * A DataFrame that contains all the variables from the stations.

    Exemples
    --------

        >>> from datetime import datetime
        >>> from meteociel.stations import station
        >>> city_name, data = station(datetime.strptime("2022-08-18", "%Y-%m-%d"), "Ajaccio")
        >>> city_name
        'ajaccio'
        >>> data
            local hour  visibility  temperature  humidity  dew_point  wind_spd  wind_gust  pressure
        0         0h00        29.8         26.7      75.0       21.9       8.0       11.0    1006.6
        1         0h06        28.8         26.5      75.0       21.7       8.0       11.0    1006.5
        2         0h12        27.7         26.4      74.0       21.4       6.0        9.0    1006.6
        3         0h18        26.6         26.5      74.0       21.5       5.0        8.0    1006.7
        4         0h24        26.8         26.5      74.0       21.5       5.0        8.0    1006.5
        ..         ...         ...          ...       ...        ...       ...        ...       ...
        235      23h30        57.0         24.9      67.0       18.3      15.0       24.0    1010.3
        236      23h36        55.5         24.9      68.0       18.6      16.0       24.0    1010.3
        237      23h42        52.9         24.9      68.0       18.6      15.0       23.0    1010.3
        238      23h48        51.4         24.9      68.0       18.6      13.0       21.0    1010.3
        239      23h54        19.9         24.9      66.0       18.1      13.0       22.0    1010.4

    """
    city_id, city = list(cities.get_city(city_name, keys={"has-station": True}).items())[0]

    response = get(
        "https://www.meteociel.fr/temps-reel/obs_villes.php",
        params={
            "affint": 1,
            "code2": city_id,
            "jour2": date.day,
            "mois2": date.month - 1,
            "annee2": date.year,
        },
        timeout=10,
    )

    data = utils.get_data_from_html(
        response,
        {
            "width": "100%",
            "border": "1",
            "cellpadding": "1",
            "cellspacing": "0",
            "bordercolor": "#C0C8FE",
            "bgcolor": "#EBFAF7",
        },
    )

    wind_spd, wind_gust = station_conv(data[-3][1:])
    hour_name = "time (local)" if data[0][0] == "Heurelocale" else "time (GMT)"

    return city["names"][0], pd.DataFrame.from_dict(
        {
            hour_name: data[0][1:][::-1],
            "visibility": station_conv(data[-10][1:])[::-1],
            "temperature": station_conv(data[-9][1:])[::-1],
            "humidity": station_conv(data[-8][1:])[::-1],
            "dew_point": station_conv(data[-7][1:])[::-1],
            "wind_spd": wind_spd[::-1],
            "wind_gust": wind_gust[::-1],
            "pressure": station_conv(data[-2][1:])[::-1],
        }
    )
