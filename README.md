# [PyWebMem](https://zalo.github.io/PyWebMem/)

<p align="left">
  <a href="https://github.com/zalo/PyWebMem/deployments/activity_log?environment=github-pages">
      <img src="https://img.shields.io/github/deployments/zalo/PyWebMem/github-pages?label=Github%20Pages%20Deployment" title="Github Pages Deployment"></a>
  <a href="https://github.com/zalo/PyWebMem/commits/master">
      <img src="https://img.shields.io/github/last-commit/zalo/PyWebMem" title="Last Commit Date"></a>
  <a href="https://github.com/zalo/PyWebMem/blob/master/LICENSE">
      <img src="https://img.shields.io/github/license/zalo/PyWebMem" title="License: Apache V2"></a>  <!-- No idea what license this should be! -->
</p>

Proof of Concept for a high-speed shared memory communication protocol with the browser.

[![PyWebMem Connecting to the Demo WebPage](./PyWebMemProofOfConcept.gif)](https://zalo.github.io/PyWebMem/)

The Python script `main.py` will scan for instances of `chrome.exe`, and search for the magic ints `0123456789` and `987654321` to demarcate a shared memory zone.   It will then write directly into the memory of the Javascript interpreter, which will copy that data into a canvas for display.

It is currently very brittle!  (But this can be improved over time)

 # Dependencies
 - [mem_edit](https://pypi.org/project/mem-edit/) (GPLv3 Python Memory Scanner)
