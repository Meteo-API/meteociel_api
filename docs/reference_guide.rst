Reference Guide
===============

Architecture of ``meteociel-api``
---------------------------------
Package structure::

	  ┌───────────┐         ┌──────────┐                     │
	┌─┤ cities.py │         │ utils.py ├──────────┐          │ Modules for package operation
	│ └─────┬─────┘         └───┬──────┘          │          │
	│       └──────────┬────────┘                 │          │
	│─ ─ ─ ─ ─ ─ ─ ─ ─ │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│─ ─ ─ ─ ─ ─ ─ ─ ─ ─
	│        ┌─────────┴────────┐                 │          │
	│ ┌──────┴───────┐   ┌──────┴──────┐   ┌──────┴───────┐  │
	│ │ soundings.py │   │ stations.py │   │ forecasts.py │  │ Data extraction modules
	│ └──────┬───────┘   └──────┬──────┘   └──────┬───────┘  │
	└────────┴─────────┬────────┴─────────────────┘          │
	 ─ ─ ─ ─ ─ ─ ─ ─ ─ │ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ 
	  ┌─────┐          │         ┌─────┐                     │
	  │ API ├──────────┴─────────┤ CLI │                     │ User interface
	  └─────┘                    └─────┘                     │

* ``utils.py`` provides some useful functions to ``soundings.py``, ``stations.py`` and ``forecasts.py``;

* ``cities.py`` provides informations on cities to ``soundings.py`` and ``stations.py``;

* ``soudings.py``, ``stations.py`` and ``forecasts.py`` are designed to be used in the API and the CLI;

* API and CLI are also using ``cities.py``

Modules for package operation
-----------------------------
.. toctree::
	:maxdepth: 2

	meteociel.utils
	meteociel.cities


Data extraction modules
-----------------------
.. toctree::
	:maxdepth: 2

	meteociel.soundings
	meteociel.stations
	meteociel.forecasts
