User Guide
==========

Installing and configuring ``meteociel-api``
--------------------------------------------
First you have to install ``meteociel-api`` from the sources. It's recommanded to use a virtual environment::

	$ git clone https://github.com/Meteo-API/meteociel_api.git
	$ cd meteociel_api
	$ python -m venv venv
	$ source venv/bin/activate
	$ pip install -e .

Under Windows please enter ``$ venv\Scripts\activate`` instead of ``$ source venv/bin/activate``.

Once ``meteociel-api`` is installed, you should generate the cities database. This database will contains all the cities that are known by Météociel over the world. These cities provide stations and measures. As ``meteociel-api`` is designed to work in CLI and in script, there is two way to generate this database. In a terminal::

	$ meteociel generate-database

Or in a Python script::
	
	from meteociel.cities import generate_database
	generate_database()

.. warning::
	You must have this database in your working directory. 

.. tip::
	In script mode you can change the database name and path by modifying the constant ``cities.DATABASE_NAME``.


Get stations measurements
-------------------------
To get stations measures you will need two things:

* the date ``YYYY/MM/DD``;

* the name of the cities.

In CLI, the gestion of date is simplified, you just have to pass the string at the correct format and the city name::

	$ meteociel station "2022/08/18" "Paris"

In that mode, the data will be saved into a CSV file (separated with ``;``). You can force the output file name by giving a value to the ``-o`` (or ``--output``) option::

	$ meteociel station --output "paris.csv" "2022/08/18" "Paris"

In a Python script, you have to convert the string to a ``datetime`` object on your own before pass it as an argument::

	from datetime import datetime
	from meteociel.stations import station
	
	# Convert the string into a datetime object with the given format
	date = datetime.strptime("2022/08/18", "%Y/%m/%d")
	
	# Get the station data
	data = station(date, "Paris")

In that case ``data`` is a tuple that contains:

* the name of the city (can be useful if the given city name is approximate);

* the data of the station in a ``pandas.DataFrame``.


Get upper air sounding data from observations
---------------------------------------------
Météociel also provide sounding data from obervations. These data are only available at 00h, 06h, 12h and 18h for a given day, and for some countries there is less hours than that (e.g. in France, only at 00h and 12h). To get sounding data, you need the date, hour and the city.

You can pass by the terminal and get a CSV file::

	$ meteociel sounding-obs "2022/08/12 00h" "Bordeaux"

You can force the output file name by giving a value to the ``-o`` (or ``--output``) option::

	$ meteociel sounding-obs --output "bordeaux.csv" "2022/08/12 00h" "Bordeaux"

In script mode, you have to convert the date on your own, just like for stations::

	from datetime import datetime
	from meteociel.soundings import sounding_obs

	# Convert the string into a datetime object with the given format
	date = datetime.strptime("2022/08/18 00h", "%Y/%m/%d %Hh")
	
	# Get the station data
	data = sounding_obs(date, "Bordeaux")

In that case ``data`` is a tuple that contains:

* the name of the city (can be useful if the given city name is approximate);

* the data of the sounding in a ``pandas.DataFrame``.


Get upper air sounding data from AROME model
--------------------------------------------
You can also get the simulated sounding from AROME model. To get data from AROME, you need either the coordinates (lon/lat) or the city name you want. You can also precise the timestep of the simulation. If you give a ``timestep``, you'll get the forecast data ``timestep`` hours after the start of the AROME run.

.. note::
	This service has no archive, so you can only access the last run of AROME.

.. warning::
	AROME is a french model, so data will be available for France only.

In a terminal, the data will be stored into a CSV file::

	$ meteociel sounding-arome --output "42N-5E.csv" --lon 5 --lat 42

you can also access data by using ``--city-name``::
	
	$ meteociel sounding-arome --city-name "Paris" --timestep 5

In this example, the extracted data is 5 hours ahead the model start, e.g. if the model start at 00h and you request ``timestep=5`` you'll get the forecast for 05h.

You can also use a Python script to access data::

	from meteociel.soundings import sounding_arome
	
	# From lon/lat
	data = sounding_arome(lon=5, lat=42)
	
	# From city name
	data = sounding_arome(city_name="Paris", timestep=5)

Here again, ``data`` is a tuple that contain:

* the name of the city (or the coordinates) and the date of the virtual sounding (like: ``YYYYMMDDHH+timestep``);

* the data from the sounding in a ``pandas.DataFrame``.


Get forecasts or trends data
----------------------------
This API also provides a tool to extract forecasts data. You can choose two modes:

* ``forecasts``: short term forecasts (up to three days);

* ``trends``: long term forecasts (up to ten days), only with GFS.

In ``forecasts`` mode, you can choose the model you want. Here is a summary:

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

All the models have different caracteristics. The tighter the resolution is, the better the result should be. By default, GFS is used.

To dump forecast data, as always, two differents ways, with a terminal or in a script.

In a terminal, use ``meteociel forecasts`` command::

	$ meteociel forecast --mode "forecasts" --model "arpege-1h" "Paris (75000)"

You can also make a research with city id. The city id can be manually found by accessing `this page <https://www.meteociel.fr/prevville.php>`_, then search for the city you want, you will have an url of the form: ``https://www.meteociel.fr/previsions/CityId/CityName.htm``, where ``CityId`` is a number. You can pass it by using ``--city-id`` option::

	$ meteociel forecast --city-id 49679

You can also dump data from a Python script::

	from meteociel.forecasts import forecast
	
	# From city name
	city_name, data = forecast(city_name="Paris (75000)", model="arome-1h")
	
	# From city id
	city_name, data = forecast(city_id=49679, mode="trends")


CSV quick view
--------------
This API provides also a little feature in CLI only that allows you to see the content of a CSV file in the terminal::

	$ meteociel quick-view csv_filename.csv

.. note::
	This function is designed to work with CSV generated by ``meteociel`` and may not work with all CSV file.

