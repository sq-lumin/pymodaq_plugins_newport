# -*- coding: utf-8 -*-
"""
Created on Mon Jan  9 15:57:26 2023

@author: lb19g16
"""
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main  # base class
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun  # common set of parameters for all actuators
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo  # object used to send info back to the main thread
from easydict import EasyDict as edict  # type of dict

from pymodaq_plugins_newport.hardware.smc100 import SMC100
import pyvisa

VISA_rm = pyvisa.ResourceManager()
infos = VISA_rm.list_resources_info()
com_ports = [infos[key].alias for key in infos.keys() if infos[key].alias is not None]
VISA_rm.close()


class DAQ_Move_Newport_SMC100(DAQ_Move_base):
    """Plugin for the Template Instrument

    This object inherits all functionality to communicate with PyMoDAQ Module through inheritance via DAQ_Move_base
    It then implements the particular communication with the instrument

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library
    # TODO add your particular attributes here if any

    """
    _controller_units = 'mm'  # TODO for your plugin: put the correct unit here
    is_multiaxes = True  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    axes_names = ['1']  # The axis list represents the number of smc controllers, indexed: first=1, second=2 etc.
    _epsilon = 0.0001
    params = [  {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'limits': com_ports, 'value': 'COM17'},
              # TODO for your custom plugin: elements to be added here as dicts in order to control your custom stage
                ] + comon_parameters_fun(is_multiaxes, axes_names)

    def ini_attributes(self):
        #  TODO declare the type of the wrapper (and assign it to self.controller) you're going to use for easy
        #  autocompletion
        self.controller: SMC100 = None

        #TODO declare here attributes you want/need to init with a default value
        pass

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        axis = int(self.settings.child('multiaxes', 'axis').value())
        pos = self.controller.get_position(axis)  # when writing your own plugin replace this line
        print(f'pos is {pos}')
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.close_communication(axis)  # when writing your own plugin replace this line

    def commit_settings(self, param):
        """Apply the consequences of a change of value in the detector settings

        Parameters
        ----------
        param: Parameter
            A given parameter (within detector_settings) whose value has been changed by the user
        """
        ## TODO for your custom plugin
        if param.name() == "a_parameter_you've_added_in_self.params":
           self.controller.your_method_to_apply_this_param_change()
        else:
            pass

    def ini_stage(self, controller=None):
        """Actuator communication initialization

        Parameters
        ----------
        controller: (object)
            custom object of a PyMoDAQ plugin (Slave case). None if only one actuator by controller (Master case)

        Returns
        -------
        info: str
        initialized: bool
            False if initialization failed otherwise True
        """

        self.ini_stage_init(old_controller=controller,
                            new_controller=SMC100())
        if self.settings['multiaxes', 'multi_status'] == "Master":
            self.controller.init_communication(
                self.settings['com_port'])
        axis = int(self.settings.child('multiaxes', 'axis').value())
        info = self.controller.get_controller_infos(axis)
        initialized = True  # todo
        return info, initialized

    def move_abs(self, value):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """

        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        ## TODO for your custom plugin
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_axis(axis=axis,pos=value)  # when writing your own plugin replace this line

    def move_rel(self, value):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_axis('REL',axis=axis,pos=value)  # when writing your own plugin replace this line


    def move_home(self):
        """Call the reference method of the controller"""

        ## TODO for your custom plugin
        axis = int(self.settings.child('multiaxes', 'axis').value())
        self.controller.move_home(axis)  # when writing your own plugin replace this line


    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""

      axis = int(self.settings.child('multiaxes', 'axis').value())
      self.controller.stop_motion(axis)  # when writing your own plugin replace this line


if __name__ == '__main__':
    main(__file__)