#!/bin/bash

# runs actual test scripts named as test_*.sh 

for test_script in test_*.sh
do
  echo "running: $test_script"
  bash $test_script
  retval=$?
  if [ $retval -ne 0 ]; then
    echo "error"
    exit $retval
  fi
done
