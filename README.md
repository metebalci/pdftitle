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

1. If any of `--use-metadata` options are given, metadata streams (for dc:title) and/or document information dictionary (for Title) are checked. If there is a metadata entry, this is used as title and document is not checked further. See [Metadata](#metadata) section for more information.

2. Every text object in the first page (or given page with --page-number) of a PDF document is checked.

3. If the font and font size is the same in consequent text objects, their content is grouped as one larger text.

4. Selected algorithm is applied to extract the title. See [Algorithms](#algorithms) section for more information.

The assumption is that the title of the document is probably the text having the largest (or sometimes second largest etc.) font size (possibly in the first page) and it is the one most close to the top of the page.

One problem is that not all documents uses space character between the words, so it is difficult to find word boundaries if space is not used. There is a recovery procedure for this, that may work.

It is possible that PDF has a character that does not exist in the font, in that case you will receive an error, and you can use the `--replace-missing-char` option to eliminate this problem.

Sometimes the found title has a strange case (first letter is small but last is big etc.), this can be corrected with `-t` option.

The title may include a ligature (single character/glyph used for multiple characters/glyphs). Starting with 0.12, the latin ligatures defined in Unicode (ff, fi, fl, ffi, ffl, ft, st) is converted to individual characters (e.g. fi ligature is changed to f and i characters). This behavior can be disabled with `--do-not-convert-ligatures`. The ligatures of other languages defined in Unicode (Armenian and Hebrew) are not converted.

There is an experimental option `--translation-heuristic` which uses the translations given to TJ operator to guess word boundaries. It sometimes works, sometimes partially works and sometimes does not work and harms the actual result.

The reason metadata is not used by default is that the title entry in metadata in many documents do not contain the actual title (but an identifier etc.).

## Algorithms

There are three algorithms at the moment:

- original: finds the maximum font size, then finds the upmost (minimum Y) blocks with this font size and joins them.

- max2: finds the maximum font size, then first adds the block with maximum font size, then the second maximum size, then continues adding either of them until a block with different font size is found. the block order is the natural order in the pdf, no x-y sorting is performed.

- eliot: similar to original but can merge blocks having arbitrary number of font sizes ordered by size. the block order is y first then x. the font sizes to use are provided with --eliot-tfs option, this is the index of font sizes from the largest to the smallest, so --eliot-tfs 0,1 means the largest and the second largest fonts.

Algorithms are selected with -a option.

## List Blocks

For information, or to help using eliot algorithm, the list of blocks can be printed with `-l` option. This is supported only with default algorithm (when no `-a` provided). For example:

```
$ pdftitle -l -p knuth65.pdf
11.194: On the Translation of Languages from Left to Right
09.250: Mathematics Department, California Institute of Technology, Pasadena, California
09.250: some k
09.250: context free language, a (simple) phrase structure language, a constituent-structure language, a definable set, a BNF language, a Chomsky type 2 (or type 4) language, a push-down automaton language,
09.250: translatable from left to right;
08.258: (1965)
08.258: DONALD E. KNUTtt
08.258: There has been much recent interest in languages whose grammar is sufficiently simple that an efficient left-to-right parsing algorithm can be mechanically produced from the grammar. In this paper, we define LR(k) grammars, which are perhaps the most general ones of this type, and they provide the basis for understanding all of the special tricks which have been used in the construction of parsing algorithms for languages with simple structure, e.g. algebraic lan- guages. We give algorithms for deciding if a given grammar satisfies the LR (k) condition, for given k, and also give methods for generating recognizers for LR(k) grammars. It is shown that the problem of whether or not a grammar is LR(k) for
08.258: is undecidable, and the paper concludes by establishing various connections between LR(k) grammars and deterministic languages. In particular, the LR(c) con- dition is a natural analogue, for grammars, of the deterministic condition, for languages. I. INTI~ODUCTION AND DEFINITIONS The word "language" will be used here to denote a set of character strings which has been variously called a
08.258: etc. Such languages have aroused wide interest because they serve as approximate models for natural languages and computer programming languages, among others. In this paper we single out an important class of languages wl~fich will be called
08.258: this means if we read the characters of a string from left to right, and look a given finite number of characters ahead , we are able to parse the given string without ever backing up to consider a previous decision. Such languages are particularly important in the case of com- puter programming, since this condition means a parsing algorithm can be mechanically constructed which requires an execution time at worst proportional to the length of the string being parsed. Special-purpose 607
06.403: INFORMATION AND CONTROL 8, 607-639
```

The title is the first block (with the maximum font size). Thus, the default algorithm works fine for this pdf. The number before `:` is the font size.

## Metadata

PDF has two metadata options to keep the title of the document. The old method is to use the document information dictionary. The new method is to use a metadata stream. pdftitle supports both with `--use-document-information-dictionary` and `--use-metadata-stream` options. Also, both of them can be enabled by using `--use-metadata` or `-m` option, which then enables both by giving priority to the new method, metadata stream. These are not enabled by default because, to my experience, some/many/most documents do not have the actual title in the metadata but a document identifier.

## Logging

Since v0.12, pdftitle uses standard python logging and prints at levels info (with -v) and debug (with -vv) to stderr by default.

## Contributing

The best way to help development is to create an issue and discuss it there first. 

Unless already discussed and decided, please do not create pull requests directly, it can be difficult to integrate them.

## Contributors

The contributors of the merged pull requests are shown in [GitHub's contributors page](https://github.com/metebalci/pdftitle/graphs/contributors).

Some of the pull requests I could not merge but implemented fully or partially in different ways, so I would like to give them credit here:

- [@cknoll](https://github.com/cknoll) for structuring the repo in a standard way in [#29](https://github.com/metebalci/pdftitle/pull/29)
- [@jakob1379](https://github.com/jakob1379) for adding pylint checks in [#11](https://github.com/metebalci/pdftitle/pull/11)

## Changelog

See [CHANGELOG.md](https://github.com/metebalci/pdftitle/blob/master/CHANGELOG.md).

## Development

See [DEVELOPMENT.md](https://github.com/metebalci/pdftitle/blob/master/DEVELOPMENT.md).
