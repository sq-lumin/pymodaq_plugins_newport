from pymodaq.daq_move.utility_classes import DAQ_Move_base, comon_parameters, main
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, set_logger, get_module_name
from easydict import EasyDict as edict

from pymodaq_plugins_newport.hardware.AGUC8wrapper import AGUC8, COMPORTS
logger = set_logger(get_module_name(__file__))


class DAQ_Move_Newport_AGUC8low(DAQ_Move_base):
    """
    """
    _controller_units = 'step'
    is_multiaxes = True
    channel_names = AGUC8.channel_names
    axis_names = AGUC8.axis_names
    port = 'COM9' if 'COM9' in COMPORTS else COMPORTS[0] if len(COMPORTS) > 0 else ''

    params = [
                 {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'limits': COMPORTS, 'value': port},
                 {'title': 'Firmware:', 'name': 'firmware', 'type': 'str', 'value': ''},
                 {'title': 'Channel:', 'name': 'channel', 'type': 'list', 'limits': channel_names},
                 {'title': 'Axis:', 'name': 'axis', 'type': 'list', 'limits': axis_names},
                 {'title': 'Sleep time (s):', 'name': 'sleep_time', 'type': 'float', 'value': 0.25},
                 {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group', 'visible': is_multiaxes, 'children': [
                     {'title': 'is Multiaxes:', 'name': 'ismultiaxes','type': 'bool', 'value': is_multiaxes},
                     {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'limits': ['Master', 'Slave']},
                  ]}
             ] + comon_parameters

    def __init__(self, parent=None, params_state=None):
        """
        Initialize the class.
        """

        super().__init__(parent, params_state)
        self.controller = None

        self._abs_steps = 0  # will keep a trace of the incremental steps (just as if there was an encoder)
        self.current_position = 0
        self.target_position = 0

    def ini_stage(self, controller=None):
        """
        Actuator communication initialization

        Parameters
        ----------
        controller: (object) custom object of a PyMoDAQ plugin (Slave case).
            None if only one actuator by controller (Master case)

        Returns
        -------
        self.status (edict): with initialization status: three fields:
            * info (str)
            * controller (object) initialized controller
            * initialized: (bool): False if initialization failed otherwise True
        """
        try:
            # initialize the stage and its controller status
            # controller is an object that may be passed to other instances of
            # DAQ_Move_Mock in case
            # of one controller controlling multiactuators (or detector)

            self.status.update(edict(info="", controller=None, initialized=False))

            # check whether this stage is controlled by a multiaxe controller
            # (to be defined for each plugin)
            # if multiaxes then init the controller here if Master state otherwise use
            # external controller
            if self.settings.child('multiaxes', 'ismultiaxes').value()\
                    and self.settings.child('multiaxes',
                                            'multi_status').value() == "Slave":
                if controller is None:
                    raise Exception('no controller has been defined externally while'
                                    'this axe is a slave one')
                else:
                    self.controller = controller
            else:  # Master stage
                self.controller = AGUC8()
                self.controller.open(self.settings.child('com_port').value())
                info = self.controller.get_infos()

                self.controller.select_channel(self.settings.child('channel').value())

            info = self.controller.get_infos()
            self.settings.child('firmware').setValue(info)

            self.status.info = info
            self.status.controller = self.controller
            self.status.initialized = True

            return self.status

        except Exception as e:
            self.emit_status(
                ThreadCommand('Update_Status', [getLineInfo() + str(e), 'log']))
            self.status.info = getLineInfo() + str(e)
            self.status.initialized = False
            return self.status

    def check_position(self):
        """
        Get the current position from the hardware with scaling conversion.

        Returns
        -------
        float: The position obtained after scaling conversion.
        """

        return self.target_position

    def move_Abs(self, position):
        """
        Move the actuator to the absolute target defined by position.
        Parameters
        ----------
        position: (flaot) value of the absolute target positioning
        """
        position = self.check_bound(position)
        rel_position = position - self.current_position
        self.move_Rel(rel_position)

    def move_Rel(self, relative_move):
        """
        Move the actuator to the relative target actuator value defined by
            relative_move

        Parameters
        ----------
        relative_move: (float) value of the relative distance to travel in
            number of steps. It has to be converted to int since here the unit is in
            number of steps.
        """
        # the syntax of the order is given by Newport documentation Agilis Series
        # User’s Manual v2.2.x
        # We do not use the move_relative command from the library since it raises an
        # error.
        relative_move = self.check_bound(self.current_position + relative_move) - self.current_position
        relative_move = self.set_position_relative_with_scaling(relative_move)
        self.target_position = relative_move + self.current_position

        self.controller.move_rel(self.settings.child('axis').value(), int(relative_move))

    def move_Home(self):
        """

        """
        self.current_position = 0.
        self.target_position = 0.

    def stop_motion(self):
        """
        Stop an ongoing move.
        Not implemented.
        """

        pass

    def commit_settings(self, param):
        """
        Called after a param_tree_changed signal from DAQ_Move_main.
        """
        if param.name() == 'channel':
            self.controller.select_channel(param.value())
            param.setValue(int(self.controller.read_channel()))

    def close(self):
        """
        Terminate the communication protocol.
        """
        self.controller.close()


if __name__ == '__main__':
    main(__file__, False)
