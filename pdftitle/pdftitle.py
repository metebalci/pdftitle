# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name
# pylint: disable=consider-using-f-string
import argparse
from io import StringIO
import os
import string
import sys
import traceback
from typing import Optional

from . import set_verbose, is_verbose, verbose
from .PDFTitleException import PDFTitleException
from .TextOnlyDevice import TextOnlyDevice
from .TextOnlyInterpreter import TextOnlyInterpreter

from pdfminer import utils
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams


def get_title_from_io(
        pdf_file_raw,
        page_number:int,
        replace_missing_char:Optional[str],
        algorithm:str,
        eliot_tfs:Optional[str]) -> str:
    parser = PDFParser(pdf_file_raw)
    # if pdf is protected with a pwd, 2nd param here is password
    doc = PDFDocument(parser)

    # pdf may not allow extraction
    # pylint: disable=no-else-return
    if doc.is_extractable:
        rm = PDFResourceManager()
        dev = TextOnlyDevice(rm, replace_missing_char)
        interpreter = TextOnlyInterpreter(rm, dev)

        first_page = StringIO()
        converter = TextConverter(rm, first_page, laparams=LAParams())
        page_interpreter = PDFPageInterpreter(rm, converter)

        current_page_number = 0

        # list objects in verbose mode
        if is_verbose():
            for xref in doc.xrefs:
                for objid in xref.get_objids():
                    obj = doc.getobj(objid)
                    if isinstance(obj, dict):
                        verbose('%s: %s %s' % (objid, obj.get('Type'), obj))
                    elif isinstance(obj, list):
                        verbose('%s: %s' % (objid, obj))
                    else:
                        verbose('%s: %s' % (objid, obj))

        for page in PDFPage.create_pages(doc):
            current_page_number = current_page_number + 1
            verbose("page", current_page_number)
            if current_page_number == page_number:
                verbose("processing page", current_page_number)
                interpreter.process_page(page)
                page_interpreter.process_page(page)
                current_page_number = -1
                break

        if current_page_number == 0:
            raise PDFTitleException("file has no pages")

        if current_page_number > 0:
            raise PDFTitleException("specified page does not exist")

        converter.close()
        first_page_text = first_page.getvalue()
        first_page.close()
        dev.recover_last_paragraph()
        verbose('all blocks')

        for b in dev.blocks:
            verbose(b)

        verbose('algo: %s' % algorithm)
        if algorithm == "original":
            # find max font size
            max_tfs = max(dev.blocks, key=lambda x: x[1])[1]
            verbose('max_tfs: ', max_tfs)
            # find max blocks with max font size
            max_blocks = list(filter(lambda x: x[1] == max_tfs, dev.blocks))
            # find the one with the highest y coordinate
            # this is the most close to top
            max_y = max(max_blocks, key=lambda x: x[3])[3]
            verbose('max_y: ', max_y)
            found_blocks = list(filter(lambda x: x[3] == max_y, max_blocks))
            verbose('found blocks')

            for b in found_blocks:
                verbose(b)
            block = found_blocks[0]
            title = ''.join(block[4]).strip()

        elif algorithm == "max2":
            # find max font size
            all_tfs = sorted(list(map(lambda x: x[1], dev.blocks)), reverse=True)
            max_tfs = all_tfs[0]
            verbose('max_tfs: ', max_tfs)
            selected_blocks = []
            max2_tfs = -1
            for b in dev.blocks:
                if max2_tfs == -1:
                    if b[1] == max_tfs:
                        selected_blocks.append(b)
                    elif len(selected_blocks) > 0: # max is added
                        selected_blocks.append(b)
                        max2_tfs = b[1]
                else:
                    if b[1] == max_tfs or b[1] == max2_tfs:
                        selected_blocks.append(b)
                    else:
                        break

            for b in selected_blocks:
                verbose(b)

            title = []
            for b in selected_blocks:
                title.append(''.join(b[4]))
            title = ''.join(title)

        elif algorithm == 'eliot':
            verbose('eliot-tfs: %s' % eliot_tfs)
            # get all font sizes
            all_tfs = sorted(set(map(lambda x: x[1], dev.blocks)), reverse=True)
            verbose('all_tfs: %s' % all_tfs)
            selected_blocks = []
            # pylint: disable=cell-var-from-loop
            for tfs_index in eliot_tfs:
                selected_blocks.extend(
                    list(filter(lambda b: b[1] == all_tfs[tfs_index],
                                dev.blocks)))
            # sort the selected blocks
            # y min first, then x min if y min is the same
            selected_blocks = sorted(
                    selected_blocks,
                    key=lambda b:(-b[3], b[2]))
            for b in selected_blocks:
                verbose(b)
            title = []
            for b in selected_blocks:
                title.append(''.join(b[4]))
            title = ''.join(title)

        else:
            raise PDFTitleException("unsupported ALGO")

        verbose('title before space correction: %s' % title)

        # Retrieve missing spaces if needed
        # warning: if you use eliot algorithm with multiple tfs
        # this procedure may not work
        if " " not in title:
            title_with_spaces = retrieve_spaces(first_page_text, title)
            # the procedure above may return empty string
            # in that case, leave the title as it is
            if len(title_with_spaces) > 0:
                title = title_with_spaces

        # Remove duplcate spaces if any are present
        if "  " in title:
            title = " ".join(title.split())

        return title
    else:
        raise PDFTitleException("PDF does not allow extraction")


def get_title_from_file(
        pdf_file:str,
        page_number:int,
        replace_missing_char:Optional[str],
        algorithm:str,
        eliot_tfs:Optional[str]) -> str:
    with open(pdf_file, 'rb') as raw_file:
        return get_title_from_io(
                raw_file, 
                page_number,
                replace_missing_char,
                algorithm,
                eliot_tfs)


def retrieve_spaces(
        first_page, 
        title_without_space, 
        p=0, 
        t=0, 
        result=""):
    while True:
        verbose('p: %s, t: %s, result: %s' % (p, t, result))
        # Stop condition : all the first page has been explored or
        #  we have explored all the letters of the title

        # pylint: disable=no-else-return
        if (p >= len(first_page) or t >= len(title_without_space)):
            return result

        elif first_page[p].lower() == title_without_space[t].lower():
            result += first_page[p]
            t += 1

        elif t != 0:
            # Add spaces if there is space or a wordwrap
            if first_page[p] == " " or first_page[p] == "\n":
                result += " "
            # If letter p-1 in page corresponds to letter t-1 in title,
            #  but letter p does not corresponds to letter p,
            # we are not exploring the title in the page
            else:
                t = 0
                result = ""

        p += 1


def run() -> None:
    try:
        parser = argparse.ArgumentParser(
            prog='pdftitle',
            description='extracts the title from a PDF file.',
            epilog='')
        parser.add_argument(
                '-p', '--pdf',
                help='pdf file',
                required=True)
        parser.add_argument(
                '-a', '--algo',
                help='algorithm to derive title, default is ' +
                'original that finds the text with largest ' +
                'font size',
                required=False,
                default="original")
        parser.add_argument(
                '--replace-missing-char',
                help='replace missing char with the one ' +
                'specified',
                default=None)
        parser.add_argument(
                '-c', '--change-name', 
                action='store_true',
                help='change the name of the pdf file',
                default=False)
        parser.add_argument(
                '-t', '--title-case', 
                action='store_true',
                help='modify the case of final title to be ' +
                'title case',
                default=False)
        parser.add_argument(
                '-v', '--verbose',
                action='store_true',
                help='enable verbose logging',
                default=False)
        parser.add_argument(
                '--eliot-tfs',
                help='the font size list to use for eliot ' +
                'algorithm, list separated by comma e.g. 0,1,2 ,' +
                'default 0 (max) only',
                required=False,
                default='0')
        parser.add_argument(
                '--page-number',
                help='the page number (default is 1) ' +
                'to extract the title from (starts from 1)',
                required=False,
                type=int,
                default=1)
        args = parser.parse_args()
        # set verbose flag first
        set_verbose(args.verbose)
        verbose(args)
        eliot_tfs = None

        if args.algo == 'eliot':
            verbose('args.eliot_tfs: %s' % args.eliot_tfs)
            eliot_tfs = args.eliot_tfs.split(',')
            verbose('eliot_tfs: %s' % eliot_tfs)
            # convert to list of ints
            eliot_tfs = list(map(int, eliot_tfs))
            verbose('final eliot_tfs: %s' % eliot_tfs)

        title = get_title_from_file(
                args.pdf, 
                args.page_number,
                args.replace_missing_char,
                args.algo,
                eliot_tfs)

        if args.title_case:
            verbose('before title case: %s' % title)
            title = title.title()

        # If no name was found, return a non-zero exit code
        if title is None:
            return 1

        # If the user wants to change the name of the file
        if args.change_name:
            # Change the title to a more pleasant file name
            new_name = title.lower()  # Lower case name
            valid_chars = set(string.ascii_lowercase + string.digits + " ")
            new_name = "".join(c for c in new_name if c in valid_chars)
            new_name = new_name.replace(' ', '_') + ".pdf"
            os.rename(args.pdf, new_name)
            print(new_name)

        else:
            print(title)

        return 0

    except PDFTitleException as e:
        traceback.print_exc()
        return 1
