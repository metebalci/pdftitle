#!/bin/bash
echo "pdftitle -p why_does_social.pdf"
title=$(pdftitle -p why_does_social.pdf)
echo "\"$title\""
if [ $? -eq 0 ]; then
  if [ ! "$title" = "WhyDoesSocialExclusionHurt?TheRelationshipBetweenSocialandPhysicalPain" ]; then
    exit 1
  fi
  exit 0
else
  exit 1
fi
