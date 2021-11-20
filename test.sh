#/bin/bash
title=$(pdftitle -p tests/data/knuth65.pdf)
if [ $? -eq 0 ]; then
  if [ ! "$title" = "On the Translation of Languages from Left to Right" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
