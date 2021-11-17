import time
import pyvisa
from threading import Lock
from pyvisa.errors import VisaIOError

from pymodaq.daq_utils.daq_utils import set_logger, get_module_name

logger = set_logger(get_module_name(__file__))
visa_rm = pyvisa.ResourceManager()

_infos = visa_rm.list_resources_info()
COMPORTS = []
for k in _infos.keys():
    COMPORTS.append(_infos[k].alias)

lock = Lock()


class AGUC8:
    channel_names = [1, 2, 3, 4]
    axis_names = [1, 2]

    def __init__(self):
        self._controller = None
        self._info = None
        self._timeout_wait_isready_ms = 10000

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
        return self._info

    def reset(self):
        # todo test it
        self.write('RS')

    def stop(self, axis: int):
        # todo test it
        command = f'{axis:.0f}ST'
        self.write(command)

    def select_channel(self, channel_index: int):
        order = "CC" + str(channel_index)
        self.write(order)

    def get_channel(self):
        #todo test it
        channel = self.query('CC?')
        return int(channel[2:])

    def get_axis_isready(self, axis):
        command = f'{axis:.0f}TS'
        status = self.query(command)
        return status == 0

    def move_rel(self, axis: int, steps: int):
        time_start = time.perf_counter()
        while not self.get_axis_isready(axis):
            time.sleep(0.05)
            if time.perf_counter() - time_start > self._timeout_wait_isready / 1000:
                self.stop(axis)
                raise TimeoutError(f"axis {axis} could'nt be ready after an elapsed time of"
                                   f" {self._timeout_wait_isready} ms")

        order = f'{axis:.0f}PR{steps:.0f}'
        self.write(order)

    def counter_to_zero(self, axis):
        command = f'{axis:.0f}ZP'
        self.write(command)

    def get_step_counter(self, axis):
        """
        Returns the number of accumulated steps in forward direction minus the number of steps in backward direction
        since powering the controller or since the last ZP (zero position) command
        """
        command = f'{axis:.0f}TP'
        steps = self.query(command)
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
            value = self._controller.query(command)
            ret = self._controller.query('TE')
            if ret != 0:
                logger.warning(f'Error code {ret} returned from the query of the command {command}')
        except VisaIOError as e:
            logger.debug(str(e))
        finally:
            lock.release()
        return value

    def write(self, command: str):
        try:
            lock.acquire()
            self._controller.write(command)
            ret = self._controller.query('TE')
            if ret != 0:
                logger.warning(f'Error code {ret} returned from the write of the command {command}')
        except VisaIOError as e:
            logger.debug(str(e))
        finally:
            lock.release()

    def flush_read(self):
        while True:
            try:
                ret = self._controller.read()
                print(f'Flushing returned: {ret}')
            except:
                break

