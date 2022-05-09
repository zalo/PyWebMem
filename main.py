import cv2                   # OpenCV, Text Drawing Library
import ctypes
import numpy as np           # ndarray Library
from mem_edit import Process # GPL Memory Scanning and Writing Library
import time
import math

magic_number_start = 1234567890
magic_number_end   = 987654321
shared_memory_ranges = []

def scan_for_shared_memory(process_name = 'chrome.exe'):
    global shared_memory_ranges
    shared_memory_ranges.clear()
    for pid in Process.get_pids_by_name(process_name):
        with Process.open_process(pid) as p:
            # Search for Start and End Magic Numbers
            start_addrs = p.search_all_memory(ctypes.c_long(magic_number_start))
            if len(start_addrs) > 0:
                print("Start Addresses:", start_addrs)
                end_addrs = p.search_all_memory(ctypes.c_long(magic_number_end))
                print("End Addresses:", end_addrs)

                # If we have the same number of starts and ends, match them together!
                if len(start_addrs) == len(end_addrs):
                    for start_addr, end_addr in zip(start_addrs, end_addrs):
                        if end_addr - start_addr > 8:
                            shared_memory_ranges.append((pid, start_addr, end_addr))
                        else:
                            print("Memory range is too small to be shared! Skipping Process...")
                            continue
                else:
                    print("Number of Start Addresses and End Addresses do not match! Skipping Process...")
                    continue
    return shared_memory_ranges

def write_to_shared_memory(memory_ranges, input_array):
  for memory_range in memory_ranges:
    with Process.open_process(memory_range[0]) as p:
        # Ensure that the beginning and ending magic numbers are still valid
        #while (magic_number_start != p.read_memory(memory_range[1], ctypes.c_ulong()).value or
        #       magic_number_end   != p.read_memory(memory_range[2], ctypes.c_ulong()).value):
        #    print("Magic Numbers are not valid anymore!  Rescanning...")
        #    scan_for_shared_memory()

        beginning_addr = memory_range[1] + 8 # Add the header length to the start address

        # Check to see if Python has relinquished control of the memory and the array is shorter than the memory range
        if (p.read_memory(memory_range[1] + 4, ctypes.c_ulong()).value == 0 and
            memory_range[2] - beginning_addr >= input_array.size * input_array.itemsize):

            # Write the current array into shared memory
            p.write_memory_pointer(beginning_addr, input_array.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)), input_array.size)

            # Write a zero to the fifth number in the array, giving control back to javascript
            p.write_memory(memory_range[1] + 4, ctypes.c_uint8(128))

# Initialize the shared memory ranges
scan_for_shared_memory()

test_array = np.ones((480, 640, 4), dtype=np.uint8) * 129
start_time = time.time()

print("Running spinner for 10 seconds...")
while time.time() - start_time < 10.0:
    x_pos = int(math.cos(time.time() * 2) * 100) + 120
    y_pos = int(math.sin(time.time() * 2) * 100) + 220

    test_array = cv2.putText(test_array, 'Hello from PyWebMem!', (x_pos, y_pos), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA)
    test_array = ((test_array.astype(float) * 0.9) + (129 * 0.1)).astype(np.uint8)
    write_to_shared_memory(shared_memory_ranges, test_array)

    #time.sleep(0.0001)

print("Complete!")