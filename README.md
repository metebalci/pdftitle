# pdftitle

[![Build Status](https://travis-ci.com/metebalci/pdftitle.svg?branch=master)](https://travis-ci.com/metebalci/pdftitle)

pdftitle is a small utility to extract the title of a PDF article.

When you have some PDF articles where you cannot understand their content from their filenames, you can use this utility to extract the title and rename the files if you want. This utility does not look at the metadata of a PDF file. The title in the metadata can be empty. It works for ~80% of the PDFs I have and it is especially suited for PDF files of scientific articles.

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

(Much) more info can be seen in verbose mode with `-v`.

The program follows this procedure:

1. Look into every text object in the first page of a PDF document

2. If the font and font size is same in consequent text objects, group their content as one

3. Apply the algorithm, see below.

The assumption is that the title of the document is probably the text having the largest (or second largest etc.) font size in the first page and the one most close to the top of the page.

One problem is that not all documents uses space character between the words, so it is difficult to find word boundaries if space is not used. There is a recovery procedure for this, that may work.

It is possible that PDF has a character that does not exist in the font, in that case you receive an exception, and you can use the `--replace-missing-char` option to eliminate this issue.

Sometimes the found title has a strange case (first letter is small but last is big etc.), this can be corrected with `-t` option.

## Algorithms

There are three algorithms at the moment:

- original: finds the maximum font size, then finds the upmost (minimum Y) blocks with this font size and joins them.
- max2: finds the maximum font size, then first adds the block with maximum font size, then the second maximum size, then continues adding either of them until a block with different font size is found. the block order is the natural order in the pdf, no x-y sorting is performed.
- eliot: similar to original but can merge blocks having arbitrary number of font sizes ordered by size. the block order is y first then x. the font sizes to use are provided with --eliot-tfs option, this is the index of font sizes from the largest to the smallest, so --eliot-tfs 0,1 means the largest and the second largest fonts.

Algorithms are selected with -a option.

## Changes

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
    
