"""
Abstract class for cross-platform memory editing.
"""

from typing import List, Tuple, Optional, Union, Generator
from abc import ABCMeta, abstractmethod
from contextlib import contextmanager
import copy
import ctypes
import logging

from . import utils
from .utils import ctypes_buffer_t


logger = logging.getLogger(__name__)


class Process(metaclass=ABCMeta):
    """
    This class is used to interact with processes running on the system
      (i.e., by reading from or writing to the memory used by a given process).

    The static methods
        `Process.list_available_pids()`
        `Process.get_pid_by_name(executable_filename)`
      can be used to help find the process id (pid) of the target process. They are
      provided for convenience only; it is probably better to use the tools built
      in to your operating system to discover the pid of the specific process you
      would like to edit.

    Once you have found the pid, you are ready to construct an instance of Process
      and use it to read and write to memory. Once you are done with the process,
      use `.close()` to free up the process for access by other debuggers etc.
    ```
        p = Process(1239)
        p.close()
    ```

    To read/write to memory, first create a buffer using ctypes:
    ```
        buffer0 = (ctypes.c_byte * 5)(39, 50, 03, 40, 30)
        buffer1 = ctypes.c_ulong()
    ```
      and then use
    ```
        p.write_memory(0x2fe, buffer0)

        val0 = p.read_memory(0x220, buffer0)[:]

        val1a = p.read_memory(0x149, buffer1).value
        val2b = buffer1.value
        assert(val1a == val2b)
    ```

    Searching for a value can be done in a number of ways:
      Search a list of addresses:
        `found_addresses = p.search_addresses([0x1020, 0x1030], buffer0)`
      Search the entire memory space:
        `found_addresses = p.search_all_memory(buffer0, writeable_only=False)`

    You can also get a list of which regions in memory are mapped (readable):
        `regions = p.list_mapped_regions(writeable_only=False)`
     which can be used along with search_buffer(...) to re-create .search_all_memory(...):
    ```
        found = []
        for region_start, region_stop in regions:
            region_buffer = (ctypes.c_byte * (region_stop - region_start))()
            p.read_memory(region_start, region_buffer)
            found += utils.search_buffer(ctypes.c_ulong(123456790), region_buffer)
    ```
    Other useful methods include the context manager, implemented as a static method:
    ```
        with Process.open_process(pid) as p:
            # use p here, no need to call p.close()
    ```
      .get_path(), which reports the path of the executable file which was used
      to start the process:
    ```
        executable_path = p.get_path()
    ```
      and deref_struct_pointer, which takes a pointer to a struct and reads out the struct members:
    ```
        # struct is a list of (offset, buffer) pairs
        struct_defintion = [(0x0, ctypes.c_ulong()),
                            (0x20, ctypes.c_byte())]
        values = p.deref_struct_pointer(0x0feab4, struct_defintion)
    ```
      which is shorthand for
    ```
        struct_addr = p.read_memory(0x0feab4, ctypes.c_void_p())
        values = [p.read_memory(struct_addr + 0x0, ctypes.c_ulong()),
                  p.read_memory(struct_addr + 0x20, ctypes.c_byte())]
    ```
    =================

    Putting all this together, a simple program which alters a magic number in the only running
      instance of 'magic.exe' might look like this:
    ```
        import ctypes
        from mem_edit import Process

        magic_number = ctypes.ulong(1234567890)

        pid = Process.get_pid_by_name('magic.exe')
        with Process.open_process(pid) as p:
            addrs = p.search_all_memory(magic_number)
            assert(len(addrs) == 1)
            p.write_memory(addrs[0], ctypes.c_ulong(42))
    ```
    Searching for a value which changes:
    ```
        pid = Process.get_pid_by_name('monitor_me.exe')
        with Process.open_process(pid) as p:
            addrs = p.search_all_memory(ctypes.c_int(40))
            input('Press enter when value has changed to 55')
            filtered_addrs = p.search_addresses(addrs, ctypes.c_int(55))
            print('Found addresses:')
            for addr in filtered_addrs:
                print(hex(addr))
    ```
    """

    @abstractmethod
    def __init__(self, process_id: int):
        """
        Constructing a Process object prepares the process with specified process_id for
          memory editing. Finding the `process_id` for the process you want to edit is often
          easiest using os-specific tools (or by launching the process yourself, e.g. with
          `subprocess.Popen(...)`).

        Args:
            process_id: Process id (pid) of the target process
        """
        pass

    @abstractmethod
    def close(self):
        """
        Detach from the process, removing our ability to edit it and
          letting other debuggers attach to it instead.

        This function should be called after you are done working with the process
          and will no longer need it. See the `Process.open_process(...)` context
          manager to avoid having to call this function yourself.
        """
        pass

    @abstractmethod
    def write_memory(self, base_address: int, write_buffer: ctypes_buffer_t):
        """
        Write the given buffer to the process's address space, starting at `base_address`.

        Args:
            base_address: The address to write at, in the process's address space.
            write_buffer: A ctypes object, for example, `ctypes.c_ulong(48)`,
                `(ctypes.c_byte * 3)(43, 21, 0xff)`, or a subclass of `ctypes.Structure`,
                which will be written into memory starting at `base_address`.
        """
        pass

    @abstractmethod
    def write_memory_pointer(self, base_address: int, write_pointer: ctypes_buffer_t, size: int):
        """
        Write the given pointer to the process's address space, starting at `base_address`.

        Args:
            base_address: The address to write at, in the process's address space.
            write_pointer: A ctypes pointer which will be written into memory starting at `base_address`.
            size: The size of the data to write from the pointer.
        """
        pass

    @abstractmethod
    def read_memory(self, base_address: int, read_buffer: ctypes_buffer_t) -> ctypes_buffer_t:
        """
        Read into the given buffer from the process's address space, starting at `base_address`.

        Args:
            base_address: The address to read from, in the process's address space.
            read_buffer: A `ctypes` object, for example. `ctypes.c_ulong()`,
                `(ctypes.c_byte * 3)()`, or a subclass of `ctypes.Structure`, which will be
                overwritten with the contents of the process's memory starting at `base_address`.

        Returns:
            `read_buffer` is returned as well as being overwritten.
        """
        pass

    @abstractmethod
    def list_mapped_regions(self, writeable_only=True) -> List[Tuple[int, int]]:
        """
        Return a list of `(start_address, stop_address)` for the regions of the address space
          accessible to (readable and possibly writable by) the process.
        By default, this function does not return non-writeable regions.

        Args:
            writeable_only: If `True`, only return regions which are also writeable.
                Default `True`.

        Returns:
            List of `(start_address, stop_address)` for each accessible memory region.
        """
        pass

    @abstractmethod
    def get_path(self) -> str:
        """
        Return the path to the executable file which was run to start this process.

        Returns:
            A string containing the path.
        """
        pass

    @staticmethod
    @abstractmethod
    def list_available_pids() -> List[int]:
        """
        Return a list of all process ids (pids) accessible on this system.

        Returns:
            List of running process ids.
        """
        pass

    @staticmethod
    @abstractmethod
    def get_pid_by_name(target_name: str) -> Optional[int]:
        """
        Attempt to return the process id (pid) of a process which was run with an executable
          file with the provided name. If no process is found, return None.

        This is a convenience method for quickly finding a process which is already known
          to be unique and has a well-defined executable name.

        Don't rely on this method if you can possibly avoid it, since it makes no
          attempt to confirm that it found a unique process and breaks trivially (e.g. if the
          executable file is renamed).

        Args:
            target_name: Name of the process to find the PID for

        Returns:
            Process id (pid) of a process with the provided name, or `None`.
        """
        pass

    def deref_struct_pointer(self,
                             base_address: int,
                             targets: List[Tuple[int, ctypes_buffer_t]],
                             ) -> List[ctypes_buffer_t]:
        """
        Take a pointer to a struct and read out the struct members:
        ```
            struct_defintion = [(0x0, ctypes.c_ulong()),
                                (0x20, ctypes.c_byte())]
            values = p.deref_struct_pointer(0x0feab4, struct_defintion)
        ```
        which is shorthand for
        ```
            struct_addr = p.read_memory(0x0feab4, ctypes.c_void_p())
            values = [p.read_memory(struct_addr + 0x0, ctypes.c_ulong()),
                      p.read_memory(struct_addr + 0x20, ctypes.c_byte())]
        ```

        Args:
            base_address: Address at which the struct pointer is located.
            targets: List of `(offset, read_buffer)` pairs which will be read from the struct.

        Return:
            List of read values corresponding to the provided targets.
        """
        base = self.read_memory(base_address, ctypes.c_void_p()).value
        values = [self.read_memory(base + offset, buffer) for offset, buffer in targets]
        return values

    def search_addresses(self,
                         addresses: List[int],
                         needle_buffer: ctypes_buffer_t,
                         verbatim: bool = True,
                         ) -> List[int]:
        """
        Search for the provided value at each of the provided addresses, and return the addresses
          where it is found.

        Args:
            addresses: List of addresses which should be probed.
            needle_buffer: The value to search for. This should be a `ctypes` object of the same
                sorts as used by `.read_memory(...)`, which will be compared to the contents of
                memory at each of the given addresses.
            verbatim: If `True`, perform bitwise comparison when searching for `needle_buffer`.
                If `False`, perform `utils.ctypes_equal`-based comparison. Default `True`.

        Returns:
            List of addresses where the `needle_buffer` was found.
        """
        found = []
        read_buffer = copy.copy(needle_buffer)

        if verbatim:
            def compare(a, b):
                return bytes(read_buffer) == bytes(needle_buffer)
        else:
            compare = utils.ctypes_equal

        for address in addresses:
            self.read_memory(address, read_buffer)
            if compare(needle_buffer, read_buffer):
                found.append(address)
        return found

    def search_all_memory(self,
                          needle_buffer: ctypes_buffer_t,
                          writeable_only: bool = True,
                          verbatim: bool = True,
                          ) -> List[int]:
        """
        Search the entire memory space accessible to the process for the provided value.

        Args:
            needle_buffer: The value to search for. This should be a ctypes object of the same
                sorts as used by `.read_memory(...)`, which will be compared to the contents of
                memory at each accessible address.
            writeable_only: If `True`, only search regions where the process has write access.
                Default `True`.
            verbatim: If `True`, perform bitwise comparison when searching for `needle_buffer`.
                If `False`, perform `utils.ctypes_equal-based` comparison. Default `True`.

        Returns:
            List of addresses where the `needle_buffer` was found.
        """
        found = []
        if verbatim:
            search = utils.search_buffer_verbatim
        else:
            search = utils.search_buffer

        for start, stop in self.list_mapped_regions(writeable_only):
            try:
                region_buffer = (ctypes.c_byte * (stop - start))()
                self.read_memory(start, region_buffer)
                found += [offset + start for offset in search(needle_buffer, region_buffer)]
            except OSError:
                logger.error('Failed to read in range  0x{} - 0x{}'.format(start, stop))
        return found

    @classmethod
    @contextmanager
    def open_process(cls, process_id: int) -> Generator['Process', None, None]:
        """
        Context manager which automatically closes the constructed Process:
        ```
            with Process.open_process(2394) as p:
                # use p here
                # no need to run p.close()
        ```

        Args:
            process_id: Process id (pid), passed to the Process constructor.

        Returns:
            Constructed Process object.
        """
        process = cls(process_id)
        yield process
        process.close()
