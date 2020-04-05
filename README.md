# pdftitle

[![Build Status](https://travis-ci.com/metebalci/pdftitle.svg?branch=master)](https://travis-ci.com/metebalci/pdftitle)

pdftitle is a small utility to extract the title of a PDF article.

When you have some PDF articles where you cannot understand their content from their filenames, you can use this utility to extract the title and rename the files if you want. This utility does not look at the metadata of a PDF file. The title in the metadata can be empty. It works for ~80% of the PDFs I have and it is especially suited for PDF files of scientific articles.

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

You can use it recursively in a directory, e.g.:

```
find . -type f -name "*.pdf" -exec pdftitle -p {} -c \;
```

More info can be seen in verbose mode with `-v`.

## Heuristics

Currently, it uses the following heuristic:

1. Look into every text object in the first page of a PDF document

2. If the font and font size is same in consequent text objects, group their content as one

3. Find the groups with maximum text size

4. If there are more than one group found, select the one the most close to top of the page

5. Title is in this group

So the assumption is that the title of the document is the text having the largest font size in the first page and the one most close to the top of the page.

One problem is not all documents uses space character between the words, so it is difficult to find word boundaries if space is not used.

There are two options that you can specify on the command line:

--replace-missing-char: if a glyph (i.e. look of character a) cannot be mapped into the character symbol (i.e. character a), normally an exception is raised. If you want no exception but replace it with something, specific it here.

pdftitle uses pdfminer.six project to parse PDF document with its own implementation of the PDF device and PDF interpreter. The names of the variables and calculations in the source code is very similar to how they are given in the PDF spec (http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf).

## Changes

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
    
