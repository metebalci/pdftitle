#!/bin/bash
echo "testing: pdftitle -p did-utf16be.pdf"
title=$(pdftitle -p did-utf16be.pdf --use-document-information-dictionary)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "Framework for ER-Completeness of Two-Dimensional Packing Problems" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
