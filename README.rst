pymodaq_plugins_newport (Newport Instruments)
#############################################

.. image:: https://img.shields.io/pypi/v/pymodaq_plugins_newport.svg
   :target: https://pypi.org/project/pymodaq_plugins_newport/
   :alt: Latest Version

.. image:: https://readthedocs.org/projects/pymodaq/badge/?version=latest
   :target: https://pymodaq.readthedocs.io/en/stable/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/PyMoDAQ/pymodaq_plugins_newport/workflows/Upload%20Python%20Package/badge.svg
    :target: https://github.com/PyMoDAQ/pymodaq_plugins_newport

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
* **AgilisSerial**: for controllers AG-UC8 and AG-UC2 tested with motorized mounts AG-M100N (no encoder)

Installation notes
==================

AGILIS AG-CU8
+++++++++++++

Install Newport AG-UC2-UC8 applet available here: https://www.newport.com/p/AG-UC8 and test that
you can communicate with this firmware.

This plugin use the included AgilisSerial wrapper communicating with the device using serial comunication
and the pyvisa package

$ python setup.py install

This last command should be executed in the python environment where you installed pymodaq.

Tested on Windows10 with pymodaq >= 3.3.0.
