"""
Manage the cities from Meteociel.
"""

import json
import os
from difflib import Differ

from bs4 import BeautifulSoup
from requests import get

DATABASE_NAME = "cities_database.json"


class CityNotFoundError(Exception):
    """An exception to be raised if the requested city is unknown."""


def get_sounding_cities():
    """Extract all known cities with sounding data."""
    # Get the source code of the page.
    response = get(
        "https://www.meteociel.fr/observations-meteo/sondage.php", params={"map": 1}, timeout=10
    )
    if not response.ok:
        raise ConnectionError(f"connection failed with code: {response.status_code}")

    # Parse the source code with BeautifulSoup.
    soup = BeautifulSoup(response.text, features="html5lib")

    cities = {}
    for city in soup.find_all("a", {"href": "javascript:return false;"}):
        # Extract cities' name and id from the page.
        city_name = city.attrs["onmouseover"].split(",")[1]
        city_name = city_name[2 : city_name.find(" - Alt.")].lower()
        city_id = city.attrs["onclick"][10:-1]

        cities[city_id] = {
            "names": city_name.split(" / "),
        }

    return cities


def get_station_cities():
    """Extract all known cities with a station."""
    # Get the source code
    response = get("https://www.meteociel.fr/temps-reel/obs_villes.php", timeout=10)
    if not response.ok:
        raise ConnectionError(f"connection failed with code: {response.status_code}")

    # Parse it with BeautifulSoup
    soup = BeautifulSoup(response.text, features="html5lib")
    select = soup.find("select", {"id": "paysdept"})

    # Iterate on countries
    cities = {}
    for i in select.find_all("option")[1:]:
        if (deptpays := i.attrs["value"]) == "none":
            continue

        # Get the cities for the targeted country
        response = get(
            "https://www.meteociel.fr/cartes_obs/stationselect_helper.php",
            params={"deptpays": deptpays},
            timeout=10,
        )
        if not response.ok:
            raise ConnectionError(f"connection failed with code: {response.status_code}")

        known_station_types = ("synop", "metar", "amateur", "secondaire")

        # For each city
        for city in response.text.splitlines():
            fields = city.split("|")

            # Get city name
            city_name = fields[1].lower()[: fields[1].find("(") - 1]

            # Get station type
            code1, code2 = int(fields[2]), int(fields[4])
            station_type = "inactive" if (code1, code2) == (1, 1) else known_station_types[code1]

            # Get country
            if deptpays.startswith("dept"):
                deptpays = "france"

            cities[fields[0]] = {
                "names": city_name.split(" / "),
                "station-type": station_type,
                "country": deptpays,
            }

    return cities


def generate_database():
    """
    Generate a JSON database with all known cities from Météociel. The name of this database is
    set by the constant ``cities.DATABASE_NAME``. For each city, a dict of the following form is
    created::

        city_id: {
            "names"       : ["name1", "name2", ...],
            "has-sounding": bool (True or False)
            "has-station" : ``bool`` (True or False),
            "station-type": can be "synop", "metar", "secondaire", "amateur", "inactive" or "N/A"
                            if no station
            "country"     : ``the`` country can be "N/A" if unknown
        }

    Types of station:

    * ``synop`` are main stations;

    * ``metar`` are stations used by aviation;

    * ``secondaire`` are secondary stations;

    * ``amateur`` are stations maintained by non-professionnal;

    * ``inactive`` are stations that doesn't emit anymore.

    .. warning::
        This function need to gather thousand cities, so its execution can take several seconds.

    Exemples
    --------

        >>> from meteociel.cities import generate_database
        >>> generate_database()

    """
    station = get_station_cities()
    sounding = get_sounding_cities()

    db_cities = {}

    # Merge cities
    for station_id, station_city in station.items():
        # City with station and sounding
        if station_id in sounding:
            sounding_city = sounding[station_id]
            db_cities[station_id] = {
                "names": list({*station_city["names"], *sounding_city["names"]}),
                "has-sounding": True,
                "has-station": True,
                "station-type": station_city["station-type"],
                "country": station_city["country"],
            }

        # City with only station
        else:
            db_cities[station_id] = {
                "names": station_city["names"],
                "has-sounding": False,
                "has-station": True,
                "station-type": station_city["station-type"],
                "country": station_city["country"],
            }

    # City with only sounding
    for sounding_id, sounding_city in sounding.items():
        if sounding_id not in db_cities:
            db_cities[sounding_id] = {
                "names": sounding_city["names"],
                "has-sounding": True,
                "has-station": False,
                "station-type": "N/A",
                "country": "N/A",
            }

    with open(DATABASE_NAME, "w", encoding="utf-8") as file:
        json.dump(db_cities, file, indent=4)


def check_name(pattern, strings):
    """Check if ``pattern` is present at least in one of the string of ``strings``."""
    if not pattern:
        return True

    return any(pattern in string for string in strings)


def get_delta(pattern, strings):
    """Calculate the delta between two strings in order to compare them."""
    deltas = []
    for string in strings:
        deltas.append(
            sum(
                any(char.startswith(i) for i in ("+ ", "- "))
                for char in Differ().compare(string, pattern)
            )
        )
    return min(deltas)


def check_keys(keys, city):
    """Check if the city meet all the requested keys."""
    return all(city[key] == value for (key, value) in keys.items())


def get_city(target_name: str, *, keys: dict = None, max_delta: int = 2):
    """
    Search in the database for a targeted city. All the cities whose names contains ``target_name``
    will match. Furthermore, please note that the cities' is are ``str`` instance.

    .. warning::
        You must generate a database before using ``get_city``.

    .. tip::
        You can pass ``""`` as name to match all cities.

    Parameters
    ----------
    target_name : ``str``
        The name of the city you are looking for.
    keys : ``dict``, keyword-only, optionnal
        By default: ``{}``. In addition to the name a ``keys`` dictionnary can be given to restrict
        research. The items of ``keys`` must match the items of the cities database.
    max_delta : ``int``, keyword-only, optionnal
        By default ``2``. The maximum delta allowed when comparing the searched name with the names
        in the database. The higher ``max_delta`` is, the higher the tolerance to typing errors will
        be, and the more likely a search will return many results.

    Returns
    -------
    match : ``dict``
        The dictionnary that contains the cities that matched the search.

    Raises
    ------
    FileNotFoundError
        This exception is raised if database doesn't exist. In that case, check the spelling of
        ``cities.DATABASE_NAME`` if you are using a custom one or generate a database by calling
        ``cities.generate_database()``.
    CityNotFoundError
        Raised if the requested city has not been found in the database.

    Exemples
    --------

        >>> import json
        >>> from meteociel.cities import get_city
        >>> matches = get_city("Ajaccio")
        >>> json.dumps(matches, indent=4)
        {
            "7761": {
                "names": [
                    "ajaccio - campo dell'oro",
                    "ajaccio"
                ],
                "has-sounding": true,
                "has-station": true,
                "station-type": "synop",
                "country": "france"
            },
            "7752": {
                ...
            },
            "20004014": {
                ...
            }
        }
        >>> matches = get_city("Ajaccio", keys={"has-sounding": True})
        >>> json.dumps(matches, indent=4)
        {
            "7761": {
                "names": [
                    "ajaccio",
                    "ajaccio - campo dell'oro"
                ],
                "has-sounding": true,
                "has-station": true,
                "station-type": "synop"
                "country": "france"
            }
        }

    """
    if not keys:
        keys = {}

    # Open database
    if DATABASE_NAME not in os.listdir():
        raise FileNotFoundError(
            "no database for cities was found, please check the database name or generate a new one"
            " by calling generate_database (generate-database in CLI)"
        )
    with open(DATABASE_NAME, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    # Search for each known cities if the target is in the looked name
    target_name = target_name.lower()
    matches = {}
    for city_id, city in json_data.items():
        if (
            check_name(target_name, city["names"])
            or get_delta(target_name, city["names"]) <= max_delta
        ) and check_keys(keys, city):
            matches[city_id] = city

    if not matches:
        raise CityNotFoundError(
            f"there's no matches for the city: '{target_name}', you can check the spelling or try "
            f"to re-generate the database (generate-database in CLI)"
        )

    # if len(matches) > 1:
    #     warnings.warn(
    #         "several cities matches your query:\n" +
    #         "\n".join([f"{city}" for city in matches.values()])
    #     )

    return matches
