# Changelog

0.15:
  - XObject contents are supported
  - `--translation-heuristic` experimental option added

0.14:
  - `--version` option added
  - build system is migrated from setup.py to pyproject.toml

0.13:
  - new feature: the use of metadata if exists. it is not enabled by default.

0.12:
  - reorganized the project structure and files (see additional notes for v0.12 below)
  - fixes bug #31
  - pdfminer version updated
  - new feature: converts latin ligatures (ff, fi, fl, ffi, ffl, ft, st = Unicode FB00-FB06) to individual characters by default
  - started using standard logging, thus the log prints go to stderr

0.11:
  - functionally same as 0.10, including some pylint fixes.

0.10:
  - --page-number argument added. Related issue is [here](https://github.com/metebalci/pdftitle/issues/22).
  - potentially a fix implemented for some files having non-zero Trm[1] and Trm2[] elements. This change might cause different outputs than previous versions of pdftitle. This is related to the issue raised [here](https://github.com/metebalci/pdftitle/issues/24).
  - verbose and error messages improved. 
  - pdfminer version updated.

0.9:
  - retrieve_spaces function is made non-recursive.
  - eliot algorithm is implemented for [this issue](https://github.com/metebalci/pdftitle/issues/18), test file is woo2019.pdf
  - eliot-tfs option is implemented for eliot algorithm.
  - stack trace was printed only in verbose mode, this behavior is changed and now stack trace is printed always if there is an error.

0.8:
  - make the title like title case (-t) using Python title method.
  - pdfminer version updated.
  - algorithm flag (-a). default is the original algorithm so no change.
  - max2 algorithm is implemented for [this issue](https://github.com/metebalci/pdftitle/issues/15), test file is paran2010.pdf.

0.7:
  - changes and fixes for pylint based on [Jakob Guldberg Aaes](https://github.com/jakob1379)'s recommendation.
  - no functional changes.

0.6:
  - rename file name to title (-c). Contributed by [Tommy Odland](https://github.com/tommyod).
  - pdfminer version updated.

0.5:
  - fixed install problem with 0.4
  - pdfminer version updated.

0.4:
  - Merged #e4bb0d6 to detect and remove duplicate spaces in the returned title. Contributed by Jakob Guldberg Aaes (https://github.com/jakob1379).

0.3:
  - Merged #f65ff4c and #f5c60c0 for identifying spaces when no space char is used. Contributed by Fabien Couthouis (https://github.com/Fabien-Couthouis).

0.2:
  - changed version string to major.minor format.
  - pdftitle can be used as a library for a project, use get_title_from_io method
  - added chardet as a dependency
  - algorithm is changed but there are problems with finding the word boundaries
