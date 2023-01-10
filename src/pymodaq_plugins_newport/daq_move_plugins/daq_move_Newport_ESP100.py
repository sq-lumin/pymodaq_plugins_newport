
from pymodaq.control_modules.move_utility_classes import DAQ_Move_base, main
from pymodaq.daq_move.utility_classes import comon_parameters
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo
from pymodaq_plugins_newport.hardware.esp100 import ESP100
from easydict import EasyDict as edict
import pyvisa


class DAQ_Move_Newport_ESP100(DAQ_Move_base):
    """

    """

    _controller_units = 'mm'
    _axis = 1

    #find available COM ports
    visa_rm = pyvisa.ResourceManager()
    infos = visa_rm.list_resources_info()
    ports = []
    for k in infos.keys():
        ports.append(infos[k].alias)
    port = 'COM6' if 'COM6' in ports else ports[0] if len(ports) > 0 else ''
    #if ports==[]:
    #    ports.append('')


    is_multiaxes = False
    stage_names = []

    params= [{'title': 'Time interval (ms):', 'name': 'time_interval', 'type': 'int', 'value': 200},
             {'title': 'Controller Info:', 'name': 'controller_id', 'type': 'text', 'value': '', 'readonly': True},
             {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'limits': ports, 'value': port},
             {'title': 'Velocity:', 'name': 'velocity', 'type': 'float', 'value': 1.0},

            {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group','visible':is_multiaxes, 'children':[
                        {'title': 'is Multiaxes:', 'name': 'ismultiaxes', 'type': 'bool', 'value': is_multiaxes, 'default': False},
                        {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'value': 'Master', 'limits': ['Master', 'Slave']},
                        {'title': 'Axis:', 'name': 'axis', 'type': 'list',  'limits': stage_names},
                        
                        ]}]+comon_parameters

        
    def ini_attributes(self):
        self.settings.child('epsilon').setValue(0.01)
        self.controller: ESP100 = None
        

    def ini_stage(self, controller=None):
            
        self.ini_stage_init(old_controller=controller,
                            new_controller=ESP100())
        
        if self.settings.child('multiaxes','multi_status').value() == "Master":
            self.controller.init_communication(self.settings.child('com_port').value(), self._axis)
            
        controller_id = self.controller.get_controller_infos()
        self.settings.child('controller_id').setValue(controller_id)
        self.settings.child('velocity').setValue(self.controller.get_velocity(self._axis))
        self.settings.child('velocity').setOpts(max=self.controller.get_velocity_max(self._axis))
        self.settings.child('epsilon').setValue(0.1)

        info = f'Initialized with controller ID: {controller_id}'
        initialized = True
        return info, initialized

    def commit_settings(self,param):
        """
        to subclass to transfer parameters to hardware
        """
        if param.name() == 'velocity':
            self.controller.set_velocity(param.value(), self._axis)

    def close(self):
        """
            close the current instance of Piezo instrument.
        """
        self.controller.close_communication(self._axis)
        self.controller = None


    def get_actuator_value(self):
        """
            Check the current position from the hardware.

            Returns
            -------
            float
                The position of the hardware.

            See Also
            --------
            DAQ_Move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        position = self.controller.get_position(self._axis)
        pos = self.get_position_with_scaling(position)
        self.current_position = pos
        self.emit_status(ThreadCommand('check_position', [pos]))
        return self.target_position

    def move_abs(self,position):
        """

        Parameters
        ----------
        position: (float) target position of the given axis in um (or scaled units)

        Returns
        -------

        """
        position = self.check_bound(position)  #limits the position within the specified bounds (-100,100)
        self.target_position = position

        #get positions in controller units
        position = self.set_position_with_scaling(position)
        out = self.controller.move_axis('ABS', self._axis, position)

    def move_rel(self, position):
        """
            Make the hardware relative move of the Piezo instrument from the given position after thread command signal was received in DAQ_Move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            DAQ_Move_base.set_position_with_scaling, DAQ_Move_base.poll_moving

        """
        position = self.check_bound(self.current_position+position)-self.current_position
        self.target_position = position+self.current_position
        position = self.set_position_relative_with_scaling(position)

        out = self.controller.move_axis('REL', self._axis, position)

    def move_home(self):
        """
            Move to the absolute vlue 100 corresponding the default point of the Piezo instrument.

            See Also
            --------
            DAQ_Move_base.move_Abs
        """
        self.controller.move_home()

    def stop_motion(self):
      """
        Call the specific move_done function (depending on the hardware).

        See Also
        --------
        move_done
      """
      self.controller.stop_motion()


if __name__ == '__main__':
    
    main(__file__, init=False)
    