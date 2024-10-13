# pdftitle

[![CircleCI](https://circleci.com/gh/metebalci/pdftitle/tree/master.svg?style=svg)](https://circleci.com/gh/metebalci/pdftitle/tree/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

pdftitle is a small utility to extract the title of a PDF article.

When you have some PDF articles where you cannot understand their content from their filenames, you can use this utility to extract the title and rename the files if you want. This utility does not look at the metadata of a PDF file. It is particularly suited for PDF files of scientific articles.

pdftitle uses pdfminer.six project to parse PDF document with its own implementation of the PDF device and PDF interpreter. The names of the variables and calculations in the source code is very similar to how they are given in the PDF spec (http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf).

## Installation

```
pip install pdftitle
```

## Usage

`pdftitle -p <pdf-file>` returns the title of the document if found.

```
$ pdftitle -p knuth65.pdf 
On the Translation of Languages from Left to Right
```

`pdftitle -p <pdf-file> -c` changes the document file name to the title of the document if found while removing the non-ascii chars. This command prints the new file name.

```
$ pdftitle -p knuth65.pdf -c
on_the_translation_of_languages_from_left_to_right.pdf
```

For debugging purposes, more info can be seen in verbose mode with `-v` (logging level INFO) or `-vv` (logging level DEBUG).

The program follows this procedure:

1. Look into every text object in the first page (or given page with --page-number) of a PDF document

2. If the font and font size is the same in consequent text objects, group their content as one

3. Apply the selected algorithm to extract the title, see below.

The assumption is that the title of the document is probably the text having the largest (or second largest etc.) font size (possibly in the first page) and the one most close to the top of the page.

One problem is that not all documents uses space character between the words, so it is difficult to find word boundaries if space is not used. There is a recovery procedure for this, that may work.

It is possible that PDF has a character that does not exist in the font, in that case you will receive an error, and you can use the `--replace-missing-char` option to eliminate this problem.

Sometimes the found title has a strange case (first letter is small but last is big etc.), this can be corrected with `-t` option.

The title may include a ligature (single character/glyph used for multiple characters/glyphs). Starting with 0.12, the latin ligatures defined in Unicode (ff, fi, fl, ffi, ffl, ft, st) is converted to individual characters (e.g. fi ligature is changed to f and i characters). This behavior can be disabled with `--do-not-convert-ligatures`. The ligatures of other languages defined in Unicode (Armenian and Hebrew) are not converted.

## Algorithms

There are three algorithms at the moment:

- original: finds the maximum font size, then finds the upmost (minimum Y) blocks with this font size and joins them.

- max2: finds the maximum font size, then first adds the block with maximum font size, then the second maximum size, then continues adding either of them until a block with different font size is found. the block order is the natural order in the pdf, no x-y sorting is performed.

- eliot: similar to original but can merge blocks having arbitrary number of font sizes ordered by size. the block order is y first then x. the font sizes to use are provided with --eliot-tfs option, this is the index of font sizes from the largest to the smallest, so --eliot-tfs 0,1 means the largest and the second largest fonts.

Algorithms are selected with -a option.

## Logging

Since v0.12, pdftitle uses standard python logging and prints at levels info (with -v) and debug (with -vv) to stderr by default.

## Contributing

The best way to help development is to create an issue and discuss it there first. 

Unless already discussed and decided, please do not create pull requests directly.

## Contributors

The contributors of the merged pull requests are shown in [GitHub's contributors page](https://github.com/metebalci/pdftitle/graphs/contributors).

Some of the pull requests I could not merge but implemented fully or partially in different ways, so I would like to give them credit here:

- [@cknoll](https://github.com/cknoll) for structuring the repo in a standard way in [#29](https://github.com/metebalci/pdftitle/pull/29)
- [@jakob1379](https://github.com/jakob1379) for adding pylint checks in [#11](https://github.com/metebalci/pdftitle/pull/11)

## Changes

0.12:
  - reorganized the project structure and files (see additional notes for v0.12 below)
  - fixes bug [#31]()
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
    
## Additional notes for v0.12

The expected and normal use of pdftitle from the command line is not changed. However, if you have integrated pdftitle to another project (i.e. using it as a library), which is not the purpose of the project, you should be aware of the following changes:

- `pdftitle.py` is moved from the root folder of the project to `pdftitle` directory
- some functionality in `pdftitle.py` are moved into separate files (`device.py`, `interpreter.py`)
- custom logging functionality is removed and standard logging is implemented. the logging config is initialized in `run`, thus if `get_title_from_{file, io}` is used, the logging config should be explicitly initalized beforehand.
- pdftitle specific exceptions are moved and raised as PDFTitleException (it was Exception before)
- global variables are removed, thus the signature of `get_title_from_file` and `get_title_from_io` functions are changed to include the parameters (fixes #33)
- `get_title_from_io` method is splitted into multiple methods (one method for each algorithm etc.), but these are not supposed to be used publicly (all are `__` prefixed)
- `get_title_from_io` and `get_title_from_file` are also imported in `__init__.py`
- running pdftitle command only handles PDFTitleException gracefully (prints stack trace and exits with non-zero error code). it was handling Exception gracefully before.
- type hints are added for public methods
- most if not all string formatting is converted to f-strings 
- title case, ligature conversion and changing file name are not performed in `get_title_from_{file, io}` methods. `title.title()`, `pdftitle.convert_ligatures(title)` and `pdftitle.change_file_name(pdf_file, new_name)` methods should be called explicitly afterwards.
