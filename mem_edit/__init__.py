"""
mem_edit

mem_edit is a multi-platform (Windows and Linux) python package for
  reading, writing, and searching in the working memory of running
  programs.

To get started, try:

    from mem_edit import Process
    help(Process)

"""
import platform

from .utils import MemEditError


__author__ = 'Jan Petykiewicz'

from .VERSION import __version__
version = __version__       # legacy compatibility


system = platform.system()
if system == 'Windows':
    from .windows import Process
elif system == 'Linux':
    from .linux import Process
else:
    raise MemEditError('Only Linux and Windows are currently supported.')
