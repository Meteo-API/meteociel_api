# Météociel  API

[![Documentation Status](https://readthedocs.org/projects/meteociel-api/badge/?version=latest)](https://meteociel-api.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/github/license/Meteo-API/meteociel_api?color=green)](https://github.com/Meteo-API/meteociel_api/blob/main/LICENSE)
[![Upload Python Package](https://github.com/Meteo-API/meteociel_api/actions/workflows/python-publish.yml/badge.svg)](https://github.com/Meteo-API/meteociel_api/actions/workflows/python-publish.yml)
[![PyPi](https://img.shields.io/pypi/v/cra)](https://pypi.org/project/cra/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

## Description
Météociel API is a small Python API for the website [Météociel](https://www.meteociel.fr/). This API allows to dump data from:

* all the stations known by Météociel (all around the world)

* upper air sounding (observations) (Western Europe only)

* upper air sounding (simulated by AROME) (France only)

A full documentation is available on [ReadTheDocs](http://meteociel-api.rtfd.io/).

## Installation

You can install this package [from PyPI](https://pypi.org/project/meteociel-api/): `pip install meteociel-api`.

You can install also install it from sources in a virtual environment by executing these commands in a terminal:
```
$ git clone https://github.com/Meteo-API/meteociel_api.git
$ cd meteociel_api
$ python -m venv venv
$ source venv/bin/activate
$ pip install -e .
```

Under windows please enter `$ venv\Scripts\activate` instead of `$ source venv/bin/activate`.

## Basic use
The installation provides two API for Météociel:

* a first one in the terminal (CLI)

* a second one as a Python package

To use the CLI, you should start by creating a database for cities by entering: `meteociel generate-database`. Once this step is done, you're free to run commands to dump data from Météociel. Help can be display by running: `meteociel --help` or `meteociel [COMMAND NAME] --help`.

In Python script, you have to start by creating the database too:
```python
from meteociel.cities import generate_database
generate_database()
```
Then you are free to dump data with the modules: `meteociel.stations` and `meteociel.soundings`.

## Compiling documentation
To compile documentation, you should have `make` installed on your computer. Then you can install the dependancies and compile:
```bash
$ cd meteociel_api/docs
$ pip install -r requirements.txt
$ make html
```

You can find the compiled html documentation in `meteociel_api/docs/_build/html/index.html`

## License
This code is provided under the GNU General Public License v3.0 (GPLv3).

Please refer to [LICENSE](https://github.com/Meteo-API/meteociel_api/blob/main/LICENSE) file for further informations. 
