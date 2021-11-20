#/bin/bash
cp tests/data/knuth65.pdf test.pdf
title=$(pdftitle -p test.pdf -c)
if [ $? -eq 0 ]; then
  # title should be the new file name
  if [ ! "$title" = "on_the_translation_of_languages_from_left_to_right.pdf" ]; then
    exit 1
  fi
  # old file should not exist
  if [ -f "test.pdf" ]; then
    exit 1
  fi
  # new file exists
  if [ ! -f "on_the_translation_of_languages_from_left_to_right.pdf" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
