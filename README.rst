pdftitle
=======================

pdftitle is a small utility to extract the title of a PDF article.

When you have some PDF articles where you cannot understand their content from their filenames, you can use this utility to extract the title and rename the files if you want. This utility does not look at the metadata of a PDF file. The title in the metadata can be empty. It works for ~80% of the PDFs I have and it is especially suited for PDF files of scientific articles.

 python -m pdftitle -p <pdf-file>

or, because a console script should be created by pip

 pdftitle -p <pdf-file>

returns the estimated title of the document. In case of error, nothing is written to system output. Much more info can be seen in verbose mode including the stack trace in case of error.

Currently, it uses the following heuristic:

1. Look into every text object in the first page of a PDF document

2. If the font size is same in consequent text objects, group their content as one

3. Find the group with maximum text size

4. Print the contents of the group

So the assumption is that the title of the document is the text having the largest font size in the first page.

I have some PDFs that it cannot decode the text due to missing character mapping.

There are two options that you can specify on the command line:

* --replace-missing-char: if a glyph (i.e. look of character a) cannot be mapped into the character symbol (i.e. character a), normally an exception is raised. If you want no exception but replace it with something, specific it here.
* --within-word-move-limit: in a single text line (for advanced users: I mean the TJ operator in PDF), movements can be specified, a movement can be both a space and not, so it is not straightforward to find word boundaries. The default value of this is -50, which seems to be OK for most cases. You may want to increase or decrease this if you experience broken or connected words.

pdftitle uses pdfminer.six project to parse PDF document with its own implementation of the PDF device and PDF interpreter. The names of the variables and calculations in the source code is very similar to how they are given in the PDF spec (http://www.adobe.com/content/dam/Adobe/en/devnet/acrobat/pdfs/pdf_reference_1-7.pdf).
