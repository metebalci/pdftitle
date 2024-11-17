#!/bin/bash
echo "pdftitle -p why_does_social.pdf --translation-heuristic"
title=$(pdftitle -p why_does_social.pdf --translation-heuristic)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "Why Does Social Exclusion Hurt? The Relationship Between Socialand Physical Pain" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
