import time
import pyvisa
from threading import Lock
from pyvisa.errors import VisaIOError
import pymodaq.daq_utils.daq_utils as utils
from pymodaq.utils.logger import set_logger, get_module_name

logger = set_logger(get_module_name(__file__), add_to_console=False)
visa_rm = pyvisa.ResourceManager()

_infos = visa_rm.list_resources_info()
COMPORTS = []
for k in _infos.keys():
    COMPORTS.append(_infos[k].alias)

lock = Lock()


class AgilisChannelError(Exception):
    pass


class AgilisAxisError(Exception):
    pass


class AgilisSerial:
    channel_indexes = [1, 2, 3, 4]  # for 'AG-UC8' else [1, 2]
    axis_indexes = [1, 2]
    _steps = {axis: 0 for axis in axis_indexes}

    def __init__(self):
        self._controller = None
        self._info = None
        self._timeout_wait_isready_ms = 10000

    def init_com_remote(self, com_port):
        self.open(com_port)
        self.reset()
        time.sleep(1)
        info = self.get_infos()
        self.set_local_remote('remote')
        return info

    def open(self, com_port):
        if com_port in COMPORTS:
            self._controller = visa_rm.open_resource(com_port, baud_rate=921600)
            time.sleep(1)

            self._controller.read_termination = self._controller.CR + self._controller.LF
            self._controller.write_termination = self._controller.CR + self._controller.LF
            self._controller.timeout = 10

    def get_infos(self):
        if self._controller is not None:
            if self._info is None:
                self._info = self.query('VE')
        if 'AG-UC8' in self._info:
            self.channel_indexes = [1, 2, 3, 4]
        else:
            self.channel_indexes = [1, 2]
        return self._info

    def set_local_remote(self, mode='remote'):
        if mode == 'remote':
            self.write('MR')
        else:
            self.write('ML')

    def reset(self):
        self.write('RS')

    def stop(self, axis: int):
        command = f'{axis:.0f}ST'
        self.write(command)

    def select_channel(self, channel_index: int):
        if channel_index not in self.channel_indexes:
            raise AgilisChannelError(f'The specified channel ({channel_index}) is not available in {self.channel_indexes}')
        order = "CC" + str(channel_index)
        self.write(order)

    def get_channel(self):
        channel = self.query('CC?')
        return int(channel[2:])

    def check_axis_index(self, axis_index: int):
        if axis_index not in self.axis_indexes:
            raise AgilisAxisError(
                f'The specified axis ({axis_index}) is not available in {self.axis_index}')

    def get_axis_isready(self, axis):
        self.check_axis_index(axis)
        command = f'{axis:.0f}TS'
        status = self.query(command)
        return status == f'{command}0'

    def wait_axis_ready(self, axis):
        time_start = time.perf_counter()
        while not self.get_axis_isready(axis):
            time.sleep(0.05)
            if time.perf_counter() - time_start > self._timeout_wait_isready_ms / 1000:
                self.stop(axis)
                raise TimeoutError(f"axis {axis} could'nt be ready after an elapsed time of"
                                   f" {self._timeout_wait_isready_ms} ms")

    def wait_query_is_not_none(self, axis):
        time_start = time.perf_counter()
        while not self.get_axis_isready(axis):
            time.sleep(0.05)
            if time.perf_counter() - time_start > self._timeout_wait_isready_ms / 1000:
                self.stop(axis)
                raise TimeoutError(f"axis {axis} could'nt be ready after an elapsed time of"
                                   f" {self._timeout_wait_isready_ms} ms")

    def move_rel(self, axis: int, steps: int):
        self.check_axis_index(axis)
        order = f'{axis:.0f}PR{steps:.0f}'
        self.write(order)
        self._steps[axis] += steps

    def counter_to_zero(self, axis):
        self.check_axis_index(axis)
        command = f'{axis:.0f}ZP'
        self.write(command)

    @utils.timer
    def get_step_counter(self, axis, read_controller=True):
        """
        Returns the number of accumulated steps in forward direction minus the number of steps in backward direction
        since powering the controller or since the last ZP (zero position) command
        """

        self.check_axis_index(axis)
        if read_controller:
            self.wait_axis_ready(axis)
            command = f'{axis:.0f}TP'
            steps_string = self.query(command)
            if steps_string is None or command not in steps_string:
                steps = self._steps[axis]
            else:
                steps = int(steps_string.split(command)[1])
                self._steps[axis] = steps
        else:
            steps = self._steps[axis]
        return steps

    def is_at_limits(self):
        """
        check if both axis of current channel are at the limit (if any)
        Returns
        -------
        bool: status of axis 1
        bool: status of axis 2
        """
        command = f'PH'
        ret = self.query(command)
        if ret == 'PH0':
            return False, False
        elif ret == 'PH1':
            return True, False
        elif ret == 'PH2':
            return False, True
        elif ret == 'PH3':
            return True, True

    def close(self):
        self._controller.close()

    def query(self, command: str):
        value = None
        try:
            lock.acquire()
            time_start = time.perf_counter()
            while value is None:
                self.write(command, isquery=True)
                value = self.flush_read()
                ret = self.check_errors(command)
                logger.debug(f'Error code {ret} returned from the query of the write of {command}')
                if value is None:
                    time.sleep(0.05)
                    if time.perf_counter() - time_start > self._timeout_wait_isready_ms / 1000:
                        raise TimeoutError(f"Timeout append during query of command {command}")
        except VisaIOError as e:
            logger.debug(str(e))
        finally:
            lock.release()
        return value

    def check_errors(self, command=''):
        ret = self._controller.query('TE')
        if ret != 'TE0':
            logger.warning(f'Error code {ret} returned from the query of the command {command}')
        return ret

    def write(self, command: str, isquery=True):
        try:
            if not isquery:
                lock.acquire()
            self._controller.write(command)
            if not isquery:
                ret = self.check_errors(command)
                logger.debug(f'Error code {ret} returned from the query of the write of {command}')
        except VisaIOError as e:
            logger.debug(str(e))
        finally:
            if not isquery:
                lock.release()

    def flush_read(self):
        ret = None
        while True:
            try:
                ret = self._controller.read()
                logger.debug(f'Read buffer was {ret}')
            except pyvisa.errors.VisaIOError:
                #  expected timeout
                break
        return ret


if __name__ == '__main__':
    ag = AgilisSerial()
    info = ag.init_com_remote('COM9')

    ag.close()
