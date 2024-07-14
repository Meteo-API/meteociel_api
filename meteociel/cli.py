"""Definitions of the commands for the CLI."""

import json
from datetime import datetime

import click
import numpy as np
import pandas as pd

import meteociel
from meteociel import cities, forecasts, soundings, stations


def clean_city_name(city_name: str):
    """Clean ``city_name`` by removing some patterns."""
    patterns = {" - ": "-", " – ": "–", " — ": "—", "'": "", " ": "_"}
    city_name = city_name.lower()
    for src, dst in patterns.items():
        city_name = city_name.replace(src, dst)

    return city_name


# Utilitary commands
@click.command("version")
def version():
    """Show the API version."""
    click.echo(f"meteociel-api {meteociel.__version__}")


@click.command("generate-database")
def generate_database():
    """Generate a database of cities for getting upper air sounding from observations."""
    cities.generate_database()


@click.command("search-city")
@click.option(
    "--sounding",
    default=None,
    type=click.BOOL,
    help=(
        "A boolean to be set on True if you want restrict your search to cities that have upper air"
        " soundings from observation. Set on False to force cities to have not souding and leave it"
        " blank if you're indifferent."
    ),
)
@click.option(
    "--station",
    default=None,
    type=click.BOOL,
    help=(
        "A boolean to be set on True if you want restrict your search to cities that a station. Set"
        " on False to force cities to have not station and leave it blank if you're indifferent."
    ),
)
@click.option(
    "--station-type",
    default=None,
    type=click.Choice(["synop", "secondaire", "amateur", "inactive"]),
    multiple=False,
    help=(
        "A string that describe the type of station you want:\n\n* synop: main stations\n\n* "
        "secondaire: secondary stations\n\n* amateur: amateur stations\n\n* inactive: inactive "
        "stations."
    ),
)
@click.option("--country", default=None, help="The country of the city you are searching for.")
@click.option(
    "--max-delta",
    default=2,
    type=click.INT,
    multiple=False,
    help=(
        "The maximum delta allowed into string comparison. The higher max-delta is, the higher the "
        "tolerance to typing errors will be, and the more likely a search will return many results."
    ),
)
@click.argument("name", default="", type=click.STRING)
def search_city(sounding, station, station_type, country, max_delta, name=""):
    """
    Search for a city in the database. NAME can be left blank to match all stations. Some options
    restrict the search to cities that meet these conditions.
    """
    keys = {}
    if isinstance(sounding, bool):
        keys["has-sounding"] = sounding
    if isinstance(station, bool):
        keys["has-station"] = station
    if isinstance(station_type, str):
        keys["station-type"] = station_type
    if isinstance(country, str):
        keys["country"] = country

    click.echo(json.dumps(cities.get_city(name, keys=keys, max_delta=max_delta), indent=4))


@click.command("quick-view")
@click.argument("filename", type=click.STRING)
def quick_view(filename: str):
    """Display the content of a CSV file in the terminal."""

    def adjust_length(string, length):
        return string + abs(length - len(string)) * " "

    dataframe = pd.read_csv(filename, delimiter=";")

    data = dataframe.to_dict()
    col_length = []
    for key, col in list(data.items())[1:]:
        col_length.append(max(len(key), *[len(str(x)) for x in list(col.values())]))

    click.echo("  ".join([length * "=" for length in col_length]))
    click.echo(
        "  ".join(
            [
                adjust_length(col_name, col_length[index])
                for index, col_name in enumerate(list(data.keys())[1:])
            ]
        )
    )
    click.echo("  ".join([length * "=" for length in col_length]))
    for _, row in dataframe.iterrows():
        click.echo(
            "  ".join(
                [
                    adjust_length(str(row[key]), col_length[index])
                    for index, key in enumerate(list(data.keys())[1:])
                ]
            )
        )

    click.echo("  ".join([length * "=" for length in col_length]))


# Data commands


@click.command("sounding-obs")
@click.option("-o", "--output", type=click.STRING, default="", help="The name of the output file.")
@click.argument(
    "date",
    type=click.DateTime(formats=("%Y-%m-%d %H", "%Y-%m-%d %Hh", "%Y/%m/%d %H", "%Y/%m/%d %Hh")),
)
@click.argument("city_name", type=click.STRING)
def get_sounding_obs(output: str, date: datetime, city_name: str):
    """
    Get the data of the upper air sounding from observation at the given city on the given date.
    """
    city_name, data = soundings.sounding_obs(date, city_name)

    # Automatic named output file
    if not output:
        output = (
            f"{clean_city_name(city_name)}_{date.year}{str(date.month).zfill(2)}"
            f"{str(date.day).zfill(2)}{str(date.hour).zfill(2)}h-loc_obs_sounding"
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")


@click.command("sounding-arome")
@click.option("-o", "--output", type=click.STRING, default="", help="The name of the output file.")
@click.option(
    "--lon", type=click.FLOAT, default=None, help="The longitude of the virtual sounding."
)
@click.option("--lat", type=click.FLOAT, default=None, help="The latitude of the virtual sounding.")
@click.option("--city-name", type=click.STRING, default="", help="The name of the city.")
@click.option(
    "-t",
    "--timestep",
    type=click.INT,
    default=1,
    help="The number of hours elapsed since the start of the AROME run.",
)
def get_sounding_arome(output: str, lon: float, lat: float, city_name: str, timestep: int):
    """Get the data of the upper air sounding observation from date and city's name."""
    city_name, data = soundings.sounding_arome(
        lon=lon, lat=lat, city_name=city_name, timestep=timestep
    )

    # Automatic named output file
    if not output:
        output = f"{clean_city_name(city_name)}_arome_sounding"

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")


@click.command("station")
@click.option("-o", "--output", type=click.STRING, default="", help="The name of the output file.")
@click.argument(
    "date",
    type=click.DateTime(formats=("%Y-%m-%d", "%Y/%m/%d")),
)
@click.argument("city_name", type=click.STRING)
def get_station(output: str, date: datetime, city_name: str):
    """Get the data of the upper air sounding observation from date and city's name."""
    city_name, data = stations.station(date, city_name)

    # Automatic named output file
    if not output:
        output = (
            f"{clean_city_name(city_name)}_{date.year}{str(date.month).zfill(2)}"
            f"{str(date.day).zfill(2)}_station"
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")


@click.command("forecast")
@click.option("-o", "--output", type=click.STRING, default="", help="The name of the output file.")
@click.option(
    "--mode",
    default="forecasts",
    type=click.Choice(["forecasts", "trends"]),
    multiple=False,
    help=(
        "By default, it's set on 'forecasts'. This option allows to select the time span: "
        "'forecasts' gives data from today up to three days ahead while 'trends' gives forecast "
        "from three to ten days ahead."
    ),
)
@click.option(
    "--model",
    default="gfs",
    type=click.Choice(
        ["gfs", "wrf", "wrf-1h", "arome", "arome-1h", "arpege-1h", "iconeu", "icond2"]
    ),
    multiple=False,
    help="By default the model is 'gfs'. This option allows to select to model to be used. Model "
    "can be chosen only in 'forecasts' mode, otherwise it will be ignored as GFS is the only "
    "available model for trends.",
)
@click.option(
    "--city-id",
    default=None,
    type=click.INT,
    help=(
        "By default, this feature is disabled. By passing directly the city id, the API will search"
        "by id rather than by name. The city id can be manually found by"
        "accessing: https://www.meteociel.fr/prevville.php, then search for the city you want, you"
        "will have an url of the form: https://www.meteociel.fr/previsions/CityId/CityName.htm."
        "CityId should be a number."
    ),
)
@click.argument("city_name", default="", type=click.STRING)
def get_forecast(output: str, mode: str, model: str, city_id: int, city_name: str):
    """Get the data of the forecasts or trends from the city name and given model."""
    city_name, data = forecasts.forecast(
        city_name=city_name, city_id=city_id, mode=mode, model=model
    )

    # Automatic named output file
    if not output:
        date = data["date"].values
        date_start = str(np.datetime_as_string(date[0], "h")).replace("-", "").replace("T", "")
        date_end = str(np.datetime_as_string(date[-1], "h")).replace("-", "").replace("T", "")
        output = f"{city_name}_{date_start}-{date_end}_{mode}" + (
            f"_{model}" if mode == "forecasts" else ""
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")
