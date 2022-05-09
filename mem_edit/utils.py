"""
Utility functions and types:

  Type definition for buffers:
    ctypes_buffer_t
  Custom exception type:
    MemEditError

  Search for a buffer inside another buffer:
    search_buffer(needle_buffer, haystack_buffer)
  Check if two buffers (ctypes objects) store equal values:
    ctypes_equal(a, b)
"""

from typing import List, Union
import ctypes


ctypes_buffer_t = Union[ctypes._SimpleCData, ctypes.Array, ctypes.Structure, ctypes.Union]


class MemEditError(Exception):
    pass


def search_buffer_verbatim(needle_buffer: ctypes_buffer_t,
                           haystack_buffer: ctypes_buffer_t,
                           ) -> List[int]:
    """
    Search for a buffer inside another buffer, using a direct (bitwise) comparison

    Args:
        needle_buffer: Buffer to search for.
        haystack_buffer: Buffer to search in.

    Returns:
        List of offsets where the `needle_buffer` was found.
    """
    found = []

    haystack = bytes(haystack_buffer)
    needle = bytes(needle_buffer)

    start = 0
    result = haystack.find(needle, start)
    while start < len(haystack) and result != -1:
        found.append(result)
        start = result + 1
        result = haystack.find(needle, start)
    return found


def search_buffer(needle_buffer: ctypes_buffer_t,
                  haystack_buffer: ctypes_buffer_t,
                  ) -> List[int]:
    """
    Search for a buffer inside another buffer, using `ctypes_equal` for comparison.
    Much slower than `search_buffer_verbatim`.

    Args:
        needle_buffer: Buffer to search for.
        haystack_buffer: Buffer to search in.

    Returns:
        List of offsets where the needle_buffer was found.
    """
    found = []
    read_type = type(needle_buffer)
    for offset in range(0, len(haystack_buffer) - ctypes.sizeof(needle_buffer)):
        v = read_type.from_buffer(haystack_buffer, offset)
        if ctypes_equal(needle_buffer, v):
            found.append(offset)
    return found


def ctypes_equal(a: ctypes_buffer_t,
                 b: ctypes_buffer_t,
                 ) -> bool:
    """
    Check if the values stored inside two ctypes buffers are equal.
    """
    if not type(a) == type(b):
        return False

    if isinstance(a, ctypes.Array):
        return a[:] == b[:]
    elif isinstance(a, ctypes.Structure) or isinstance(a, ctypes.Union):
        for attr_name, attr_type in a._fields_:
            a_attr, b_attr = (getattr(x, attr_name) for x in (a, b))
            if isinstance(a, ctypes_buffer_t):
                if not ctypes_equal(a_attr, b_attr):
                    return False
            elif not a_attr == b_attr:
                return False

        return True
    else:
        return a.value == b.value
