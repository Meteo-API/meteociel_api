"""Definitions of the commands for the CLI."""

import json
from datetime import datetime

import click
import matplotlib.pyplot as plt
from matplotlib.dates import AutoDateLocator, DateFormatter
import numpy as np
import pandas as pd
from rich.console import Console
from rich.table import Table

import meteociel
from meteociel import cities, forecasts, soundings, stations


def clean_city_name(city_name: str):
    """Clean ``city_name`` by removing some patterns."""
    patterns = {" - ": "-", " – ": "–", " — ": "—", "'": "", " ": "_"}
    city_name = city_name.lower()
    # name, date = city_name.split("_")
    # city_name = "_".join([name.lower(), date])
    for src, dst in patterns.items():
        city_name = city_name.replace(src, dst)

    return city_name


def wrap_text(string: str, max_length: int = 50):
    """Wrap the given string into several lines of the specified length."""
    if len(string) > max_length:
        return f"{string[: max_length]}\n{wrap_text(string[max_length: ], max_length)}"

    return string


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
def search_city(sounding, station, country, max_delta, name=""):
    """
    Search for a city in the database. NAME can be left blank to match all stations. Some options
    restrict the search to cities that meet these conditions.
    """
    keys = {}
    if isinstance(sounding, bool):
        keys["has-sounding"] = sounding
    if isinstance(station, bool):
        keys["has-station"] = station
    if isinstance(country, str):
        keys["country"] = country

    click.echo(json.dumps(cities.get_city(name, keys=keys, max_delta=max_delta), indent=4))


@click.command("read")
@click.argument("filename", type=click.STRING)
def read(filename: str):
    """Display the content of a CSV file in the terminal."""
    dataframe = pd.read_csv(filename, delimiter=";")

    table = Table(title=filename)
    for column_name in dataframe.columns[1: ]:
        table.add_column(column_name)

    for row in dataframe.iterrows():
        table.add_row(*[str(i) for i in row[1][1:]])

    console = Console()
    console.print(table)

@click.command("quick-look")
@click.option(
    "-o",
    "--output",
    type=click.STRING,
    default="",
    help="The name of the output file. If no output file name is provided, the figure will not be saved.",
)
@click.option(
    "-x",
    "--xaxis",
    type=click.STRING,
    help="The name of the variable to put on the x-axis",
)
@click.option(
    "-y",
    "--yaxis",
    type=click.STRING,
    help="The name of the variable to put on the y-axis.",
)
@click.option(
    "--date-format",
    "--fmt",
    type=click.STRING,
    default="",
    help="The format to be used to convert the time (x-axis only) into datetime instances.",
)
@click.argument("filename", type=click.STRING)
def quick_look(output: str, xaxis: str, yaxis: str, date_format: str, filename: str):
    """Opens and quickly plot the wanted variables using plt.scatter."""
    data = pd.read_csv(filename, delimiter=";")
    
    fig, axes = plt.subplots(layout="constrained")
    axes.scatter(
        (
            np.vectorize(lambda ts: datetime.strptime(ts, date_format))(data[xaxis])
            if date_format else
            data[xaxis]
        ),
        data[yaxis],
    )
    
    if date_format:
        axes.xaxis.set_major_formatter(DateFormatter(date_format))
        axes.tick_params(axis="x", labelrotation=45, labelrotation_mode="xtick")
    
    axes.set(
        title=wrap_text(filename),
        xlabel=xaxis,
        ylabel=yaxis,
    )
    axes.grid(True)

    if len(output):
        fig.savefig(output)
    else:
        plt.show()


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
    city_name, date, data = soundings.sounding_obs(date, city_name)

    # Automatic named output file
    if not output:
        output = (
            f"{clean_city_name(city_name)}_{date}_obs_sounding"
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")


@click.command("sounding-model")
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
    help="The number of hours elapsed since the start of the model run.",
)
@click.option(
    "-m",
    "--model",
    type=click.Choice(soundings.MODELS),
    default=soundings.MODELS[0],
    multiple=False,
    help="The model to be used, by default, it's sets on 'arome'.",
)
def get_sounding_model(output: str, lon: float, lat: float, city_name: str, timestep: int, model: str):
    """Get the data of the upper air sounding observation from date and city's name."""
    city_name, date, data = soundings.sounding_model(
        lon=lon, lat=lat, city_name=city_name, timestep=timestep, model=model
    )

    # Automatic named output file
    if not output:
        output = f"{clean_city_name(city_name)}_{date}_{model}_sounding"

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
    city_name, date, data = stations.station(date, city_name)

    # Automatic named output file
    if not output:
        output = (
            f"{clean_city_name(city_name)}_{date}_station"
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")


@click.command("forecast")
@click.option("-o", "--output", type=click.STRING, default="", help="The name of the output file.")
@click.option(
    "--mode",
    default="forecasts",
    type=click.Choice(forecasts.MODES),
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
    type=click.Choice(forecasts.MODELS),
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
        "By default, this feature is disabled. By passing directly the city id, the API will search "
        "by id rather than by name. The city id can be manually found by "
        "accessing: https://www.meteociel.fr/prevville.php, then search for the city you want, you "
        "will have an url of the form: https://www.meteociel.fr/previsions/CityId/CityName.htm. "
        "CityId should be a number."
    ),
)
@click.argument("city_name", default="", type=click.STRING)
def get_forecast(output: str, mode: str, model: str, city_id: int, city_name: str):
    """Get the data of the forecasts or trends from the city name and given model."""
    city_name, date, data = forecasts.forecast(
        city_name=city_name, city_id=city_id, mode=mode, model=model
    )

    # Automatic named output file
    if not output:
        output = f"{city_name}_{date}_{mode}" + (
            f"_{model}" if mode == "forecasts" else ""
        )

    if not output.endswith(".csv"):
        output += ".csv"
    data.to_csv(output, sep=";")
