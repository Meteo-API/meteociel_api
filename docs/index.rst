Météociel API's documentation
=============================


Description
-----------
Météociel API is a small Python API for the website `Météociel <https://www.meteociel.fr/>`_. This API allows to dump data from:

* all the stations known by Météociel (all around the world)

* forecasts and trends

* upper air sounding (observations) (Western Europe only)

* upper air sounding (simulated by AROME) (France only)


Installation
------------
You can install this package from sources in a virtual environment by executing these commands in a terminal::

	$ cd meteociel_api
	$ python -m venv venv
	$ source venv/bin/activate
	$ pip install -e .

Under Windows please enter ``$ venv\Scripts\activate`` instead of ``$ source venv/bin/activate``.

You can also compile the documentation::

	$ cd docs
	$ pip install -r requirements.txt
	$ make html

Then, open the file ``meteociel_api/docs/_build/html/index.html``.


Licence
-------
This code is provided under the GNU General Public Licence v3.0+ (GPLv3+).

Please refer to LICENCE file for further informations.


Content
-------
.. toctree::
	:maxdepth: 2	

	Home <self>
	User Guide <user_guide>
	Reference guide <reference_guide>
	Contributor's guide <contributor_guide>
