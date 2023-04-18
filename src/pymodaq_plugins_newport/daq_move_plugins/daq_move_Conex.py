
from pymodaq.control_modules.move_utility_classes import comon_parameters_fun, main, DAQ_Move_base

from pymodaq.utils.daq_utils import ThreadCommand, getLineInfo
from easydict import EasyDict as edict
import sys
import clr
from serial.tools import list_ports


conex_path = 'C:\\Program Files\\Newport\\Piezo Motion Control\\Newport CONEX-AGAP Applet\\Samples'
sys.path.append(conex_path)
clr.AddReference("ConexAGAPCmdLib")
import Newport.ConexAGAPCmdLib as Conexcmd

COMPORTS = [str(port)[0:4] for port in list(list_ports.comports())]


class DAQ_Move_Conex(DAQ_Move_base):
    """
        Wrapper object to access the conex fonctionnalities, similar wrapper for all controllers.

        =============== ==================
        **Attributes**   **Type**
        *ports*          list
        *conex_path*     string
        *params*         dictionnary list
        =============== ==================

        See Also
        --------
        daq_utils.ThreadCommand
    """

    _controller_units = 'µm'

    # find available COM ports

    is_multiaxes = True
    axes_names = ['U', 'V']
    _epsilon = 0.0001

    params = [{'title': 'controller library:', 'name': 'conex_lib', 'type': 'browsepath', 'value': conex_path},
              {'title': 'Controller Name:', 'name': 'controller_name', 'type': 'str', 'value': '', 'readonly': True},
              {'title': 'Motor ID:', 'name': 'motor_id', 'type': 'str', 'value': '', 'readonly': True},
              {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'limits': COMPORTS},
              {'title': 'Controller address:', 'name': 'controller_address', 'type': 'int', 'value': 1, 'default': 1,
               'min': 1},
              ] + comon_parameters_fun(is_multiaxes, axes_names, epsilon=_epsilon)

    def ini_attributes(self):
        self.controller: Conexcmd.ConexAGAPCmds = None
        self.settings.child('bounds', 'is_bounds').setValue(True)
        self.settings.child('bounds', 'min_bound').setValue(-0.02)
        self.settings.child('bounds', 'max_bound').setValue(0.02)

    def commit_settings(self,param):
        """
            | Activate any parameter changes on the PI_GCS2 hardware.
            |
            | Called after a param_tree_changed signal from daq_move_main.

        """

        pass

    def ini_stage(self, controller=None):
        """

        """
        self.controller = self.ini_stage_init(controller, Conexcmd.ConexAGAPCmds())

        if self.settings['multiaxes', 'multi_status'] == "Master":
            out = self.controller.OpenInstrument(self.settings['com_port'][0:4])

        controller_name = self.controller.VE(self.settings['controller_address'], "", "")[1]
        motor_id = self.controller.ID_Get(self.settings['controller_address'], "", "")[1]
        self.settings.child('controller_name').setValue(controller_name)
        self.settings.child('motor_id').setValue(motor_id)
        info = controller_name + " / " + motor_id
        initialized = out == 0
        return info, initialized

    def close(self):
        """
            close the current instance of instrument.
        """
        self.controller.CloseInstrument()

    def stop_motion(self):
        """
            See Also
            --------
            daq_move_base.move_done
        """
        self.controller.ST(self.settings.child(('controller_address')).value(),"")
        self.move_done()

    def get_actuator_value(self):
        """
            Get the current hardware position with scaling conversion given by get_position_with_scaling.

            See Also
            --------
            daq_move_base.get_position_with_scaling, daq_utils.ThreadCommand
        """
        pos = self.controller.TP(self.settings['controller_address'],
                                 self.settings['multiaxes', 'axis'], 0.0000, "")[1]
        pos = self.get_position_with_scaling(pos)
        self.current_position = pos
        return pos

    def move_abs(self, position):
        """
            Make the hardware absolute move from the given position after thread command signal was received in daq_move_main.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            daq_move_base.set_position_with_scaling, daq_move_base.poll_moving

        """
        position = self.check_bound(position)
        self.target_position = position

        position = self.set_position_with_scaling(position)
        out = self.controller.PA_Set(self.settings['controller_address'],
                                     self.settings['multiaxes', 'axis'], position, "")

    def move_rel(self, position):
        """
            | Make the hardware relative move from the given position after thread command signal was received in daq_move_main.
            |
            | The final target position is given by **current_position+position**.

            =============== ========= =======================
            **Parameters**  **Type**   **Description**

            *position*       float     The absolute position
            =============== ========= =======================

            See Also
            --------
            daq_move_base.set_position_with_scaling, daq_move_base.poll_moving

        """
        position = self.check_bound(self.current_position + position) - self.current_position
        self.target_position = position + self.current_position

        position = self.set_position_relative_with_scaling(position)

        out = self.controller.PR_Set(self.settings['controller_address'],
                                     self.settings['multiaxes', 'axis'], position, "")

    def move_home(self):
        """
            Make the absolute move to original position (0).

            See Also
            --------
            move_Abs
        """
        self.move_abs(0)


if __name__ == '__main__':
    main(__file__, init=False)
