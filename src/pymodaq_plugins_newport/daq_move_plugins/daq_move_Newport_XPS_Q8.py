from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from qtpy.QtCore import QThread
from pymodaq_plugins_newport.hardware import XPS_Q8_drivers 
import sys

from time import perf_counter_ns

class XPSPythonWrapper():
    
    def __init__(self):
        self.myxps = XPS_Q8_drivers.XPS()
        self.group = 'Group2' 
        self.positioner = self.group + '.Pos'
        self.socketId = None
        self._initCommands()
            
    def _initCommands(self):
        self.socketId = self.myxps.TCP_ConnectToServer('192.168.0.254', 5001, 20)
        # Check connection passed
        if (self.socketId == -1):
            print('Connection to XPS failed, check IP & Port')
            #sys.exit()
        #Group kill to be sure
        [errorCode, returnString] = self.myxps.GroupKill(self.socketId, self.group)
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupKill')
            #sys.exit ()
        #Initialize
        [errorCode, returnString] = self.myxps.GroupInitialize(self.socketId, self.group) 
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupInitialize')
            #sys.exit()
        #Définition du trigger sur MotionDone
        # [errorCode, returnString] = self.myxps.EventExtendedConfigurationTriggerSet(self.socketId, 'MotionDone',0,0,0,0)
        # if (errorCode != 0):
        #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationTriggerSet')
        #     sys.exit()
        # [errorCode, returnString] = self.myxps.EventExtendedConfigurationActionSet(self.socketId, , 0, 0, 0, 0)
        # if (errorCode != 0):
        #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationActionSet')
        #     sys.exit()
        # Home search
        self.moveHome()
            
    def checkConnected(self):
        return (self.socketId != -1) and (self.socketId is not None)
    
    def displayErrorAndClose(self, errorCode, APIName):
        if (errorCode != -2) and (errorCode != -108):
            [errorCode2, errorString] = self.myxps.ErrorStringGet(self.socketId, errorCode)
            if (errorCode2 != 0):
                print(APIName + ': ERROR ' + str(errorCode))
            else:
                print(APIName + ': ' + errorString)
        else:
            if (errorCode == -2):
                print(APIName + ': TCP timeout')
            if (errorCode == -108):
                print(APIName + ': The TCP/IP connection was closed by an administrator')
        self.closeTCPIP()

    def closeTCPIP(self):
        self.myxps.TCP_CloseSocket(self.socketId)
        
    def getPosition(self):
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self.positioner, 1)
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupPositionCurrentGet')
            sys.exit()  
        else:
            return(float(currentPosition))
            #print('Positioner ' + self.positioner + ' is in position ' + str(currentPosition))
    
    def moveAbsolute(self, value):
        [errorCode, returnString] = self.myxps.GroupMoveAbsolute(self.socketId, self.positioner, [value])
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupMoveAbsolute')
            sys.exit()
        #test : attente de finir le mouvement
        # [errorCode, returnString] = self.myxps.GroupMotionStatusGet(self.socketId, self.positioner, 1)
        # print(returnString)
        # if (errorCode != 0):
        #     self.displayErrorAndClose(errorCode, 'GroupMotionStatusGet')
        #     sys.exit()
        # t1 = perf_counter_ns()
        # while returnString == '1':
        #     [errorCode, returnString] = self.myxps.GroupMotionStatusGet(self.socketId, self.positioner, 1)
        #     print('looping')
        #     if (errorCode != 0):
        #         self.displayErrorAndClose(errorCode, 'GroupMotionStatusGet')
        #         sys.exit()
        # t2 = perf_counter_ns()

        
    def moveHome(self):
        [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self.group)
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupHomeSearch')
            sys.exit() 
            
# TODO:
# (1) change the name of the following class to DAQ_Move_TheNameOfYourChoice
# (2) change the name of this file to daq_move_TheNameOfYourChoice ("TheNameOfYourChoice" should be the SAME
#     for the class name and the file name.)
# (3) this file should then be put into the right folder, namely IN THE FOLDER OF THE PLUGIN YOU ARE DEVELOPING:
#     pymodaq_plugins_my_plugin/daq_move_plugins
class DAQ_Move_Newport_XPS_Q8(DAQ_Move_base):
    """ Instrument plugin class for an actuator.
    
    This object inherits all functionalities to communicate with PyMoDAQ’s DAQ_Move module through inheritance via
    DAQ_Move_base. It makes a bridge between the DAQ_Move module and the Python wrapper of a particular instrument.

    TODO Complete the docstring of your plugin with:
        * The set of controllers and actuators that should be compatible with this instrument plugin.
        * With which instrument and controller it has been tested.
        * The version of PyMoDAQ during the test.
        * The version of the operating system.
        * Installation instructions: what manufacturer’s drivers should be installed to make it run?

    Attributes:
    -----------
    controller: object
        The particular object that allow the communication with the hardware, in general a python wrapper around the
         hardware library.
         
    # TODO add your particular attributes here if any

    """
    _controller_units = 'mm'  # TODO for your plugin: put the correct unit here
    is_multiaxes = False  # TODO for your plugin set to True if this plugin is controlled for a multiaxis controller
    _axis_names = ['Axis1']  # TODO for your plugin: complete the list
    _epsilon = 600e-6  # TODO replace this by a value that is correct depending on your controller
    data_actuator_type = DataActuatorType['DataActuator']  # wether you use the new data style for actuator otherwise set this
    # as  DataActuatorType['float']  (or entirely remove the line)

    params = [   # TODO for your custom plugin: elements to be added here as dicts in order to control your custom stage
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)
    # _epsilon is the initial default value for the epsilon parameter allowing pymodaq to know if the controller reached
    # the target value. It is the developer responsibility to put here a meaningful value

    def ini_attributes(self):
        self.controller: XPSPythonWrapper = None

        #TODO declare here attributes you want/need to init with a default value
        pass

    def get_actuator_value(self):
        """Get the current value from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """
        pos = DataActuator(data=self.controller.getPosition())  # when writing your own plugin replace this line
        pos = self.get_position_with_scaling(pos)
        return pos

    def close(self):
        """Terminate the communication protocol"""
        self.controller.closeTCPIP()
        

    def commit_settings(self, param: Parameter):
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

        self.controller = self.ini_stage_init(old_controller=controller,
                                              new_controller=XPSPythonWrapper())

        info = "Platine init"
        initialized = self.controller.checkConnected()
        return info, initialized

    def move_abs(self, value: DataActuator):
        """ Move the actuator to the absolute target defined by value

        Parameters
        ----------
        value: (float) value of the absolute target positioning
        """
        value = self.check_bound(value)  #if user checked bounds, the defined bounds are applied here
        self.target_value = value
        value = self.set_position_with_scaling(value)  # apply scaling if the user specified one
        ## TODO for your custom plugin
        self.controller.moveAbsolute(value.value())  # when writing your own plugin replace this line
        #self.controller.moveAbsolute(value.value())  # do it twice to be sure
        self.emit_status(ThreadCommand('Update_Status', ['moveAbsolute command sent']))

        
    def move_rel(self, value: DataActuator):
        """ Move the actuator to the relative target actuator value defined by value

        Parameters
        ----------
        value: (float) value of the relative target positioning
        """
        value = self.check_bound(self.current_position + value) - self.current_position
        self.target_value = value + self.current_position
        value = self.set_position_relative_with_scaling(value)

        ## TODO for your custom plugin
        raise NotImplemented  # when writing your own plugin remove this line
        self.controller.your_method_to_set_a_relative_value(value.value())  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.moveHome()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))

    def stop_motion(self):
      """Stop the actuator and emits move_done signal"""

      ## TODO for your custom plugin
      raise NotImplemented  # when writing your own plugin remove this line
      self.controller.your_method_to_stop_positioning()  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


if __name__ == '__main__':
    main(__file__)
