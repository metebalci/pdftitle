#!/bin/bash
echo "pdftitle -p why_does_social.pdf"
title=$(pdftitle -p why_does_social.pdf)
if [ $? -eq 0 ]; then
  echo "\"$title\""
  if [ ! "$title" = "WhyDoesSocialExclusionHurt?TheRelationshipBetweenSocialandPhysicalPain" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
