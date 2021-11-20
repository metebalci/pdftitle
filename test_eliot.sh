#/bin/bash
title=$(pdftitle -a eliot --eliot-tfs 1 -p tests/data/woo2019.pdf --replace-missing-char ' ')
if [ $? -eq 0 ]; then
  if [ ! "$title" = "Lactobacillus HY2782 and Biﬁdobacterium HY8002 Decrease Airway Hyperresponsiveness Induced by Chronic PM2.5 Inhalation in Mice" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
