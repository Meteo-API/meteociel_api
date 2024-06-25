Contributor's guide
===================

Installing lint packages
------------------------
Some packages are used to ensure a minimum quality of code:

* ``isort``

* ``black``

* ``flake8``, ``flake8-bugbear``, ``flake8-builtins``, ``flake8-comprehensions``, ``flake8-mutable``

* ``pylint``

You can enter this command in a terminal to install all these package with pip::

	pip install isort black flake8 flake8-bugbear flake8-builtins flake8-comprehensions flake8-mutable pylint


Coding style
------------
The black coding style has been used here in addition to few manual checks provided by ``flake8`` and ``pylint``.

The maximum length of lines has been set on 100 characters.


Check code
----------
First, check the import order::

	isort module.py

Use ``black`` to clean the module::

	black --line-length 100 module.py

Pass ``flake8``::
	
	flake8 --max-line-length 100 module.py

And finally ``pylint`` (it disabled the empty first line of docstring)::

	pylint --enable-all-extensions --disable=C0199 module.py


Minimum required
----------------
A perfect code isn't necessary, but you should avoid as much as possible the errors. The following warnings from lint tools are tolerated:

* ``flake8 E203`` (conflict with ``black``);

* ``pylint R2004`` (magic value comparison);

* ``pylint R0913`` only for ``cli.py`` (too many arguments).

