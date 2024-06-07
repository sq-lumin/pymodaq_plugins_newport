from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, comon_parameters_fun, main, DataActuatorType,\
    DataActuator  # common set of parameters for all actuators
from pymodaq.utils.daq_utils import ThreadCommand # object used to send info back to the main thread
from pymodaq.utils.parameter import Parameter
from qtpy.QtCore import QThread
from pymodaq_plugins_newport.hardware import XPS_Q8_drivers 
import sys

from time import perf_counter_ns

class XPSPythonWrapper():
    """Simplified XPS wrapper, calls methods from the wrapper given by Newport. See XPS_Q8_drivers"""
    
    def __init__(self, ip:str = None, port:int = None, group:str = None, positionner:str = None, plugin = None):
        #init the wrapper given by Newport and some attributes
        self.myxps = XPS_Q8_drivers.XPS()   #Instanciate the driver from Newport
        
        #keep a ref of the plugin to emit (error) messages
        self._plugin = plugin 
        
        #required to connect via TCP/IP
        self._ip = ip
        self._port = port
        self.socketId = -1
        
        #Definition of the stage
        self._group = group 
        self._positioner = positionner
        self._full_positionner_name = f'{group}.{positionner}'
        
        #Some required initialisation steps
        self._initCommands()
            
    def _initCommands(self):
        """Runs some initial commands : connect to the XPS server, group kill, group intialize, move home.
        Some configs could be added here as well"""
        self.socketId = self.myxps.TCP_ConnectToServer(self._ip, self._port, 20)    #20s timeout
        # Check connection passed
        if (self.socketId == -1):
            self._plugin.emit_status(ThreadCommand('Update_Status', ['Connection to XPS failed, check IP & Port']))
        else:
            self._plugin.emit_status(ThreadCommand('Update_Status', ['Connected to XPS']))
        
            #Group kill to be sure
            [errorCode, returnString] = self.myxps.GroupKill(self.socketId, self._group)
            if (errorCode != 0):
                self.displayErrorAndClose(errorCode, 'GroupKill')

            #Initialize
            [errorCode, returnString] = self.myxps.GroupInitialize(self.socketId, self._group) 
            if (errorCode != 0):
                self.displayErrorAndClose(errorCode, 'GroupInitialize')
            
            #Home search
            self.moveHome()
            
            #Definition of the MotionDone trigger
            # [errorCode, returnString] = self.myxps.EventExtendedConfigurationTriggerSet(self.socketId, 'MotionDone',0,0,0,0)
            # if (errorCode != 0):
            #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationTriggerSet')
            #     sys.exit()
            # [errorCode, returnString] = self.myxps.EventExtendedConfigurationActionSet(self.socketId, , 0, 0, 0, 0)
            # if (errorCode != 0):
            #     self.displayErrorAndClose(errorCode, 'EventExtendedConfigurationActionSet')
            #     sys.exit()
        
            
            
    def checkConnected(self):
        """Returns true if the connection was successful, else false."""
        return (self.socketId != -1)
    
    def displayErrorAndClose(self, errorCode, APIName):
        """Method to recover an error string based on an error code. Closes the TCPIP connection afterwards"""
        if (errorCode != -2) and (errorCode != -108):
            [errorCode2, errorString] = self.myxps.ErrorStringGet(self.socketId, errorCode)
            if (errorCode2 != 0):
                self._plugin.emit_status(ThreadCommand('Update_Status', [f'{APIName} : ERROR {errorCode}']))
            else:
                self._plugin.emit_status(ThreadCommand('Update_Status', [f'{APIName} : {errorString}']))
        else:
            if (errorCode == -2):
                self._plugin.emit_status(ThreadCommand('Update_Status', [f'{APIName} : TCP timeout']))
            if (errorCode == -108):
                self._plugin.emit_status(ThreadCommand('Update_Status', [f'{APIName} : The TCP/IP connection was closed by an administrator']))
        self.closeTCPIP()

    def closeTCPIP(self):
        """Call the method to close the socket."""
        self.myxps.TCP_CloseSocket(self.socketId)
        
    def getPosition(self):
        """Returns current the position"""
        [errorCode, currentPosition] = self.myxps.GroupPositionCurrentGet(self.socketId, self._full_positionner_name, 1)
        if (errorCode != 0):
            self.displayErrorAndClose(errorCode, 'GroupPositionCurrentGet')
            sys.exit()  
        else:
            return(float(currentPosition))
    
    def moveAbsolute(self, value):
        """Moves the stage to the position value."""
        if (self.socketId != -1):
            [errorCode, returnString] = self.myxps.GroupMoveAbsolute(self.socketId, self._full_positionner_name, [value])
            if (errorCode != 0):
                self.displayErrorAndClose(errorCode, 'GroupMoveAbsolute')
            
    
    def moveRelative(self, value):
        """Moves the stage to value relative to it's current position."""
        if (self.socketId != -1):
            [errorCode, returnString] = self.myxps.GroupMoveRelative(self.socketId, self._full_positionner_name, [value])
            if (errorCode != 0):
                self.displayErrorAndClose(errorCode, 'GroupMoveRelative')
                
    def moveHome(self):
        """Moves the stage to it's home"""
        if (self.socketId != -1):
            [errorCode, returnString] = self.myxps.GroupHomeSearch(self.socketId, self._group)
            if (errorCode != 0):
                self.displayErrorAndClose(errorCode, 'GroupHomeSearch')

    
    def setGroup(self, group:str):
        self._group = group
        self._full_positionner_name = f'{group}.{self._positionner}'
    
    def setPositionner(self, positionner:str):
        self._positionner = positionner
        self._full_positionner_name = f'{self._group}.{positionner}'
    
    def setIP(self, IP:str):
        """Sets a new IP address. Does not automatically try to connect with it, call retryConnection."""
        self._ip = IP
    
    def setPort(self, port:int):
        """Sets a new port. Does not automatically try to connect with it, call retryConnection."""
        self._port = port
        
    def retryConnection(self):
        """Closes the connection and runs the init sequence again.
        Called by the plugin after any change to the IP address or port parameters."""
        self.closeTCPIP()
        self._initCommands()
    
class DAQ_Move_Newport_XPS_Q8(DAQ_Move_base):
    """ Instrument plugin class for Newport_XPS_Q8 Motion Controller.
    
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
    _controller_units = 'mm'  
    is_multiaxes = False  
    _axis_names = ['Axis1'] 
    _epsilon = 600e-6  
    data_actuator_type = DataActuatorType['DataActuator']  


    params = [{'title':'XPS IP address :', 'name':'xps_ip_address', 'type' : 'str', 'value' : '192.168.0.254'}, #IP address of my system
              {'title':'XPS Port :', 'name':'xps_port', 'type' : 'int', 'value' : 5001}, #Port of my system, should be the same for others ?
              {'title':'Group :', 'name':'group', 'type' : 'str', 'value' : 'Group2'},    #Group to be moved
              {'title':'Positionner :', 'name':'positionner', 'type' : 'str', 'value' : 'Pos'}    #positionner to be moved
                ] + comon_parameters_fun(is_multiaxes, axis_names=_axis_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: XPSPythonWrapper = None

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
        if param.name() == 'xps_ip_address':
            self.controller.setIP(param.value())
            self.controller.retryConnection()
        elif param.name() == 'xps_port':
            self.controller.setPort(param.value())
            self.controller.retryConnection()
        elif param.name() == 'group':
            self.controller.setGroup(param.value())
        elif param.name() == 'positionner':
            self.controller.setPositionner(param.value())
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
                                              new_controller=XPSPythonWrapper(
                                                  ip = self.settings.child('xps_ip_address').value(),
                                                  port = self.settings.child('xps_port').value(),
                                                  group = self.settings.child('group').value(),
                                                  positionner = self.settings.child('positionner').value(),
                                                  plugin = self
                                                  ))

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

        self.controller.moveAbsolute(value.value())  

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
 
        self.controller.moveRelative(value.value())  
        self.emit_status(ThreadCommand('Update_Status', ['moveRelative command sent']))

    def move_home(self):
        """Call the reference method of the controller"""
        self.controller.moveHome()  # when writing your own plugin replace this line
        self.emit_status(ThreadCommand('Update_Status', ['Moved home']))

    def stop_motion(self):
      """NOT IMPLEMENTED --- Stop the actuator and emits move_done signal"""

      ## Not possible to implement with this system as far as I'm aware.
      
      raise NotImplementedError  # when writing your own plugin remove this line
      self.controller.your_method_to_stop_positioning()  # when writing your own plugin replace this line
      self.emit_status(ThreadCommand('Update_Status', ['Some info you want to log']))


if __name__ == '__main__':
    main(__file__)
