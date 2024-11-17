#!/bin/bash
echo "testing: pdftitle -a eliot --eliot-tfs 1 -p woo2019.pdf --replace-missing-char ' '"
title=$(pdftitle -a eliot --eliot-tfs 1 -p woo2019.pdf --replace-missing-char ' ')
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "Lactobacillus HY2782 and Bifidobacterium HY8002 Decrease Airway Hyperresponsiveness Induced by Chronic PM2.5 Inhalation in Mice" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
