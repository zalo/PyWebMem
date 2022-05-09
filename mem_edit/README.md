# mem_edit 

**mem_edit** is a multi-platform memory editing library written in Python.

**Homepage:** https://mpxd.net/code/jan/mem_edit

**Capabilities:**
* Scan all readable memory used by a process.
    * Optionally restrict searches to regions with read + write permissions.
    * Report on address space allocation
* Read/write using ctypes objects
    * Basic types, e.g. ```ctypes.c_ulong()```
    * Arrays, e.g. ```(ctypes.c_byte * 4)()```
    * Instances of ```ctypes.Structure or ctypes.Union``` and subclasses.
* Run on Windows and Linux


## Installation

**Dependencies:**
* python 3 (written and tested with 3.7 and 3.10)
* ctypes
* typing (for type annotations)


Install with pip, from PyPI (for the original release):
```bash
pip3 install mem_edit
```

Install with pip from this git repository (with additional functionality)
```bash
pip3 install git+https://github.com/zalo/mem_edit.git@master
```


## Documentation

Most functions and classes are documented inline.
To read the inline help,
```python3
import mem_edit
help(mem_edit.Process)
```

## Examples

Increment a magic number (unsigned long 1234567890) found in 'magic.exe':
```python3
    import ctypes
    from mem_edit import Process

    magic_number = ctypes.ulong(1234567890)

    pid = Process.get_pid_by_name('magic.exe')
    with Process.open_process(pid) as p:
        addrs = p.search_all_memory(magic_number)

        # We don't want to edit if there's more than one result...
        assert(len(addrs) == 1)

        # We don't actually have to read the value here, but let's do so anyways...
        num_ulong = p.read_memory(addrs[0], ctypes.c_ulong())
        num = num_ulong.value

        p.write_memory(addrs[0], ctypes.c_ulong(num + 1))
```

Narrow down a search after a value changes:
```python3
    import ctypes
    from mem_edit import Process

    initial_value = 40
    final_value = 55

    pid = Process.get_pid_by_name('monitor_me.exe')
    with Process.open_process(pid) as p:
        addrs = p.search_all_memory(ctypes.c_int(initial_value))

        input('Press enter when value has changed to ' + str(final_value))

        filtered_addrs = p.search_addresses(addrs, ctypes.c_int(final_value))

        print('Found addresses:')
        for addr in filtered_addrs:
            print(hex(addr))
```

Read and alter a structure:
```python3
    import ctypes
    from mem_edit import Process

    class MyStruct(ctypes.Structure):
        _fields_ = [
               ('first_member', ctypes.c_ulong),
               ('second_member', ctypes.c_void_p),
               ]

    pid = Process.get_pid_by_name('something.exe')

    with Process.open_process(pid) as p:
        s = MyStruct()
        s.first_member = 1234567890
        s.second_member = 0x1234

        addrs = p.search_all_memory(s)
        print(addrs)

        p.write_memory(0xafbfe0, s)
```
