#!/bin/bash
echo "testing: pdftitle -p knuth65.pdf"
title=$(pdftitle -p knuth65.pdf)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "On the Translation of Languages from Left to Right" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
