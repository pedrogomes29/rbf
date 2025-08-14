#!/usr/bin/env bash

for items in 10000 8000 4000 2500 1400 1000 700 400 200 100 60 30 20 10
do
  echo "python3 ./model_search.py 0 ${items} 99 100 1"
  python3 ./model_search.py 0 ${items} 99 100 1
done