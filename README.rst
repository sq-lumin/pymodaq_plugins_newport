pymodaq_plugins_newport (Newport Instruments)
#############################################

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_newport.svg
   :target: https://pypi.org/project/pymodaq_plugins_newport/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/CEMES-CNRS/pymodaq_plugins_newport/workflows/Upload%20Python%20Package/badge.svg
    :target: https://github.com/CEMES-CNRS/pymodaq_plugins_newport

PyMoDAQ plugin for instruments from Newport (Conex, ESP100, AG-CU8...)


Authors
=======

* Sebastien J. Weber
* David Bresteau (david.bresteau@cea.fr)

Instruments
===========
Below is the list of instruments included in this plugin

Actuators
+++++++++

* **Conex**: Piezo actuators from the CONEX-AGAP series"
* **Newport_ESP100**: ESP100 motion controllers
* **AGILIS AG-CU8**: tested with motorized mounts AG-M100N (no encoder)

Installation notes
==================

AGILIS AG-CU8
+++++++++++++

Install Newport AG-UC2-UC8 applet available here: https://www.newport.com/p/AG-UC8 and test that
you can communicate with this firmware.

This plugin use the instrumentkit library. Currently the version proposed on pypi 0.6.0
does not include the newport/agilis.py file that we are interrested in. We recommand to
install the library from git (not with pip), as it is explained in this page:
https://github.com/Galvant/InstrumentKit

$ git clone git@github.com:Galvant/InstrumentKit.git

$ cd InstrumentKit

$ python setup.py install

This last command should be executed in the python environment where you installed pymodaq.

Tested on Windows10 with pymodaq 3.3.0.
