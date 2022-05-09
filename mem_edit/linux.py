"""
Implementation of Process class for Linux
"""

from typing import List, Tuple, Optional
from os import strerror
import os
import os.path
import signal
import ctypes
import ctypes.util
import logging

from .abstract import Process as AbstractProcess
from .utils import ctypes_buffer_t, MemEditError


logger = logging.getLogger(__name__)


ptrace_commands = {
    'PTRACE_GETREGS': 12,
    'PTRACE_SETREGS': 13,
    'PTRACE_ATTACH': 16,
    'PTRACE_DETACH': 17,
    'PTRACE_SYSCALL': 24,
    'PTRACE_SEIZE': 16902,
    }


# import ptrace() from libc
_libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
_ptrace = _libc.ptrace
_ptrace.argtypes = (ctypes.c_ulong,) * 4
_ptrace.restype = ctypes.c_long


def ptrace(command: int, pid: int = 0, arg1: int = 0, arg2: int = 0) -> int:
    """
    Call ptrace() with the provided pid and arguments. See the ```man ptrace```.
    """
    logger.debug('ptrace({}, {}, {}, {})'.format(command, pid, arg1, arg2))
    result = _ptrace(command, pid, arg1, arg2)
    if result == -1:
        err_no = ctypes.get_errno()
        if err_no:
            raise MemEditError('ptrace({}, {}, {}, {})'.format(command, pid, arg1, arg2) +
                               ' failed with error {}: {}'.format(err_no, strerror(err_no)))
    return result


class Process(AbstractProcess):
    pid = None

    def __init__(self, process_id: int):
        ptrace(ptrace_commands['PTRACE_SEIZE'], process_id)
        self.pid = process_id

    def close(self):
        os.kill(self.pid, signal.SIGSTOP)
        os.waitpid(self.pid, 0)
        ptrace(ptrace_commands['PTRACE_DETACH'], self.pid, 0, 0)
        os.kill(self.pid, signal.SIGCONT)
        self.pid = None

    def write_memory(self, base_address: int, write_buffer: ctypes_buffer_t):
        with open('/proc/{}/mem'.format(self.pid), 'rb+') as mem:
            mem.seek(base_address)
            mem.write(write_buffer)

    def write_memory(self, base_address: int, write_buffer: ctypes_buffer_t, size: int):
        raise NotImplementedError
        #with open('/proc/{}/mem'.format(self.pid), 'rb+') as mem:
        #    mem.seek(base_address)
        #    mem.write(write_buffer)

    def read_memory(self, base_address: int, read_buffer: ctypes_buffer_t) -> ctypes_buffer_t:
        with open('/proc/{}/mem'.format(self.pid), 'rb+') as mem:
            mem.seek(base_address)
            mem.readinto(read_buffer)
        return read_buffer

    def get_path(self) -> str:
        try:
            with open('/proc/{}/cmdline', 'rb') as f:
                return f.read().decode().split('\x00')[0]
        except FileNotFoundError:
            return ''

    @staticmethod
    def list_available_pids() -> List[int]:
        pids = []
        for pid_str in os.listdir('/proc'):
            try:
                pids.append(int(pid_str))
            except ValueError:
                continue
        return pids

    @staticmethod
    def get_pid_by_name(target_name: str) -> Optional[int]:
        for pid in Process.list_available_pids():
            try:
                logger.debug('Checking name for pid {}'.format(pid))
                with open('/proc/{}/cmdline'.format(pid), 'rb') as cmdline:
                    path = cmdline.read().decode().split('\x00')[0]
            except FileNotFoundError:
                continue

            name = os.path.basename(path)
            logger.debug('Name was "{}"'.format(name))
            if path is not None and name == target_name:
                return pid

        logger.info('Found no process with name {}'.format(target_name))
        return None

    @staticmethod
    def get_pids_by_name(target_name: str) -> Optional[int]:
        pids = []
        for pid in Process.list_available_pids():
            try:
                logger.debug('Checking name for pid {}'.format(pid))
                with open('/proc/{}/cmdline'.format(pid), 'rb') as cmdline:
                    path = cmdline.read().decode().split('\x00')[0]
            except FileNotFoundError:
                continue

            name = os.path.basename(path)
            logger.debug('Name was "{}"'.format(name))
            if path is not None and name == target_name:
                pids.append(pid)

        #logger.info('Found no process with name {}'.format(target_name))
        return pids

    def list_mapped_regions(self, writeable_only: bool = True) -> List[Tuple[int, int]]:
        regions = []
        with open('/proc/{}/maps'.format(self.pid), 'r') as maps:
            for line in maps:
                bounds, privileges = line.split()[0:2]

                if 'r' not in privileges:
                    continue

                if writeable_only and 'w' not in privileges:
                    continue

                start, stop = (int(bound, 16) for bound in bounds.split('-'))
                regions.append((start, stop))
        return regions
