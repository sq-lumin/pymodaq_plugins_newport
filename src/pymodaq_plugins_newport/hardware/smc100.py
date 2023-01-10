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

    def _str_to_float(self, command:str, string:str) -> float:
        return float(string.split(f'{command}')[1][:-2])


    def get_position(self, axis=1):
        """ return the given axis position always in mm
        """
        command = f'{axis}TP'
        self._write_command(command)
        pos = self._str_to_float(command, self.read())
        return pos
    
    def get_velocity(self, axis=1):
        command = f'{axis}VA?'
        self._write_command(command)
        pos = self._str_to_float(command[:-1],  self.read())
        return pos
    
    def get_velocity_max(self, axis=1):
        raise NotImplementedError
    
    def move_home(self, axis=1):
        self._write_command(f'{axis}OR')
        
    
    
    
if __name__ == '__main__':
    controller = SMC100()
    controller.init_communication('COM5')
    try:
        print(controller.get_controller_infos())
        print(f'Position is : {controller.get_position()}')
        controller.move_axis('REL', pos=-1.)
    except Exception as e:
        print(str(e))
    finally:
        controller.close_communication()
        
        
    
    