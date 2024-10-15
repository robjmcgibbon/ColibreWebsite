#! /bin/bash

google-chrome --new-window http://localhost:8000
cd build
python3 -m http.server
