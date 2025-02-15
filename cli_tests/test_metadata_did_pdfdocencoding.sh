#!/bin/bash
echo "testing: pdftitle -p did-pdfdocencoding.pdf"
title=$(pdftitle -p did-pdfdocencoding.pdf --use-document-information-dictionary)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "Wordmall för rapporter" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
