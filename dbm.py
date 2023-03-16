##!/usr/bin/env python3
# -*- coding: UTF-8 -*-
# Version 1.1.0
import os
from platform import system
from time import sleep

import trace_module.trace as trace
import warnings

warnings.filterwarnings("ignore")

def clear_screen():
    os.system("clear")

if __name__ == "__main__":
    try:
        if system() == 'Linux':
            clear_screen()
            trace.main("perf", None)
        else:
            trace.main("perf", None)

    except KeyboardInterrupt:
        print("\nExiting ..")
        sleep(2)
