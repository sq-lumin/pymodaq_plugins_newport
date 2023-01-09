# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 15:41:28 2023

@author: weber


Wrapper around the serial communication with a particular SMC100 controller whose most methods from the SerialBase object 

"""

import pyvisa
import numpy as np
from pymodaq_plugins_newport.hardware.serial_base import SerialBase


class SMC100(SerialBase):
   
    def init_communication(self, com_port, axis=1):
        if com_port in self.com_ports:
            super().init_communication(com_port, axis)
            self._controller.baud_rate = 57600
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))
