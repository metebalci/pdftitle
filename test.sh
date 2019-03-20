#/bin/bash
title=$(pdftitle -p knuth65.pdf)
echo "$title"
if [ $? -eq 0 ]; then
  if [ "$title" = "On the Translation of Languages from Left to Right" ]; then
    exit 0
  else
    exit 1
  fi
else
  exit 1
fi
