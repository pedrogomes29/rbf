#!/usr/bin/env bash

for items in 10 20 30 60 100 200 400 700 1000 1400 2500 4000 8000 10000 16000 30000 50000
do
  echo "python3 ./model_search.py 0 ${items} 99 100 1"
  python3 ./model_search.py 0 ${items} 99 100 1
done