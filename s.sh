#!/bin/bash
. $HOME/esp/esp-idf/export.sh
cd codigo_esp
idf.py build
idf.py flash
idf.py monitor