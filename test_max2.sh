#/bin/bash
title=$(pdftitle -p tests/data/paran2010.pdf -a max2 -t)
if [ $? -eq 0 ]; then
  if [ ! "$title" = "Settlement Remains From The Bronze And Iron Ages At Horbat Menorim (El-Manara), Lower Galilee" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
