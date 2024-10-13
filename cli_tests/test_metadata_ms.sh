#!/bin/bash
echo "testing: pdftitle -p metadata-sample.pdf"
title=$(pdftitle -p metadata-sample.pdf --use-metadata-stream)
if [ $? -eq 0 ]; then
  if [ ! "$title" = "PDF Metadata Sample" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
