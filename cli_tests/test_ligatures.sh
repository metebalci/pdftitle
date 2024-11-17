#!/bin/bash
echo "testing: pdftitle -p 1506.02640.pdf"
title=$(pdftitle -p 1506.02640.pdf)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "You Only Look Once: Unified, Real-Time Object Detection" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
