import pyvisa
import numpy as np
from pymodaq_plugins_newport.hardware.serial_base import SerialBase


class ESP100(SerialBase):

    def init_communication(self, com_port, axis=1):
        if com_port in self.com_ports:
            super().init_communication(com_port, axis)
            self._controller.baud_rate = 19200

            self.turn_motor_on(axis)
        else:
            raise IOError('{:s} is not a valid port'.format(com_port))

    def turn_motor_on(self, axis=1):
        self._write_command(f'{axis}MO?')
        status = self._controller.read_ascii_values()[0]
        if not status:
            self._write_command(f'{axis}MO')

    def turn_motor_off(self, axis=1):
        self._write_command(f'{axis}MF?')
        status = self._controller.read_ascii_values()[0]
        if status:
            self._write_command(f'{axis}MF')

    def close_communication(self, axis=1):
        self.turn_motor_off(axis=axis)
        super().close_communication(axis)
        
    def move_home(self, axis=1):
        self._write_command(f'{axis}OR1')
        
    
    def get_velocity(self, axis=1):
        self._write_command(f'{axis}VA?')
        pos = self._controller.read_ascii_values()[0]
        return pos
    
    def get_velocity_max(self, axis=1):
        self._write_command(f'{axis}VU?')
        pos = self._controller.read_ascii_values()[0]
        return pos

    def get_position(self, axis=1):
        """ return the given axis position always in mm
        """
        self._write_command(f'{axis}TP')
        pos = self._controller.read_ascii_values()[0]
        return pos
