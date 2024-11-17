#!/bin/bash
echo "testing: pdftitle -p test.pdf -c"
cp knuth65.pdf test.pdf
title=$(pdftitle -p test.pdf -c)
if [ $? -eq 0 ]; then
  # first -c should succeed
  # second should fail
  cp knuth65.pdf test.pdf
  title=$(pdftitle -p test.pdf -c)
  if [ $? -eq 1 ]; then
    exit 0
  else
    exit 1
  fi
else
  exit 1
fi
