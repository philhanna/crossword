#! /bin/bash
find .. -name '__pycache__' | xargs -i rm -r {}
