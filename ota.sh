#!/bin/bash

source ./venv/bin/activate

if [[ "$1" == "--date" && -n "$2" ]]; then
  python ./ota.py "$1" "$2"
else
  python ./ota.py
fi
