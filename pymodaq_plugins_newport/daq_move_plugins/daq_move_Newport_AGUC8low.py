from pymodaq.daq_move.utility_classes import DAQ_Move_base, comon_parameters, main
from pymodaq.daq_utils.daq_utils import ThreadCommand, getLineInfo, set_logger, get_module_name
from easydict import EasyDict as edict
from instruments.newport.agilis import AGUC2
import pyvisa
from serial.serialwin32 import SerialTimeoutException

logger = set_logger(get_module_name(__file__))


"""
Installation
------------
Install Newport AG-UC2-UC8 applet available here: https://www.newport.com/p/AG-UC8

This plugin use the instrumentkit library. Currently the version proposed on pypi 0.6.0
does not include the newport/agilis.py file that we are interrested in. We recommand to
install the library from git (not with pip), as it is explained in this page:
https://github.com/Galvant/InstrumentKit

$ git clone git@github.com:Galvant/InstrumentKit.git
$ cd InstrumentKit
$ python setup.py install

Troubleshooting
---------------
It happens that the plugin initialize correctly (green light in a daq_move) but still
sending a move order will have no effect.
Try to load the AGUC2 class and launch an order in an independent script and try again
with pymodaq. We do not know why but it seems to solve the problem...

"""

class DAQ_Move_Newport_AGUC8low(DAQ_Move_base):
    """
    """
    _controller_units = 'step'
    is_multiaxes = True
    channel_names = [1, 2, 3, 4]
    axis_names = [1, 2]

    # find available COM ports
    visa_rm = pyvisa.ResourceManager()
    infos = visa_rm.list_resources_info()
    ports = []
    for k in infos.keys():
        ports.append(infos[k].alias)
    port = 'COM9' if 'COM9' in ports else ports[0] if len(ports) > 0 else ''

    params = [
                 {'title': 'COM Port:', 'name': 'com_port', 'type': 'list', 'values': ports, 'value': port},
                 {'title': 'Firmware:', 'name': 'firmware', 'type': 'str', 'value': ''},
                 {'title': 'Channel:', 'name': 'channel', 'type': 'list', 'values': channel_names},
                 {'title': 'Axis:', 'name': 'axis', 'type': 'list', 'values': axis_names},
                 {'title': 'Sleep time (s):', 'name': 'sleep_time', 'type': 'float', 'value': 0.25},
                 {'title': 'MultiAxes:', 'name': 'multiaxes', 'type': 'group', 'visible': is_multiaxes, 'children': [
                     {'title': 'is Multiaxes:', 'name': 'ismultiaxes','type': 'bool', 'value': is_multiaxes},
                     {'title': 'Status:', 'name': 'multi_status', 'type': 'list', 'values': ['Master', 'Slave']},
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

        # we do not poll the moving since we consider an actuator without encoder
        # self.settings.child('epsilon').setValue(1)

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
                # self.controller = AGUC2.open_serial(
                #     port=self.settings.child('com_port').value(),
                #     baud=921600
                # )
                self.controller = self.visa_rm.open_resource(self.settings.child('com_port').value(),
                                                             baud_rate=921600)


                self.controller.read_termination = self.controller.CR + self.controller.LF
                self.controller.write_termination = self.controller.CR + self.controller.LF
                self.controller.timeout = 10
            self.flush_read()

            info = self.controller.query('VE')
            self.flush_read()
            self.settings.child('firmware').setValue(info)
            # Select the good channel.
            channel = self.settings.child('channel').value()
            order = "CC" + str(channel)
            self.controller.write(order)
            self.flush_read()

            # Configure the sleep time which is a time delay in second after each order.
            # The setter of the library does not work that is why we use this dirty way
            # by calling directly a private attribute.
            self.controller._sleep_time = self.settings.child('sleep_time').value()

            self.status.info = f"Actuator AGUC8 initialized on com port {self.settings.child('com_port').value()}"
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

        axis_number = self.settings.child('axis').value()
        order = f'{axis_number:.0f}PR{relative_move:.0f}'
        ready = False
        while not ready:
            try:

                self.controller.write(order)
                # status = self.controller.ag_query('TE')
                # if status != 'TE0':
                #     logger.warning(f'wrong return from controller {status}')
                self.flush_read()
                ready = True

            except SerialTimeoutException as e:
                logger.warning(str(e))

        self.poll_moving()

    def flush_read(self):
        while True:
            try:
                ret = self.controller.read()
                print(ret)
            except:
                break

    def move_Home(self):
        """

        """

        self.current_position = 0.
        self.target_position = 0.

        self.poll_moving()


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
        if param.name() == "sleep_time":
            self.controller._sleep_time = param.value()
        elif param.name() == 'channel':
            self.controller.write(f'CC{param.value()}')
            status = self.controller.query('TE')
            if status != 'TE0':
                logger.warning(f'wrong return from controller {status}')
            self.flush_read()
            channel = self.controller.query('CC?')
            param.setValue(int(channel[2:]))


    def close(self):
        """
        Terminate the communication protocol.
        Not implemented.
        """
        self.controller.close()


if __name__ == '__main__':
    main(__file__, False)
