"""pdftitle"""

import argparse
import io
import os
import string
import traceback
from typing import Optional, List

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

from .logging import logger, verbose
from .exceptions import PDFTitleException
from .device import TextOnlyDevice
from .interpreter import TextOnlyInterpreter


def __get_title_by_original_algorithm(device: PDFDevice) -> str:
    # find max font size
    max_tfs = max(device.blocks, key=lambda x: x[1])[1]
    verbose(f"max_tfs: {max_tfs}")
    # find max blocks with max font size
    max_blocks = list(filter(lambda x: x[1] == max_tfs, device.blocks))
    # find the one with the highest y coordinate
    # this is the most close to top
    max_y = max(max_blocks, key=lambda x: x[3])[3]
    verbose(f"max_y: {max_y}")
    found_blocks = list(filter(lambda x: x[3] == max_y, max_blocks))
    verbose("found blocks")

    if logger.is_verbose():
        for block in found_blocks:
            verbose(block)

    block = found_blocks[0]
    title = "".join(block[4]).strip()
    return title


def __get_title_by_max2_algorithm(device: PDFDevice) -> str:
    # find max font size
    all_tfs = sorted(list(map(lambda x: x[1], device.blocks)), reverse=True)
    max_tfs = all_tfs[0]
    verbose(f"max_tfs: {max_tfs}")
    selected_blocks = []
    max2_tfs = -1
    for block in device.blocks:
        if max2_tfs == -1:
            if block[1] == max_tfs:
                selected_blocks.append(block)
            elif len(selected_blocks) > 0:  # max is added
                selected_blocks.append(block)
                max2_tfs = block[1]
        else:
            if block[1] == max_tfs or block[1] == max2_tfs:
                selected_blocks.append(block)
            else:
                break

    verbose("selected blocks")
    if logger.is_verbose():
        for block in selected_blocks:
            verbose(block)

    title = []
    for block in selected_blocks:
        title.append("".join(block[4]))

    title = "".join(title)
    return title


def __get_title_by_eliot_algorithm(device: PDFDevice, eliot_tfs: List[int]) -> str:
    verbose(f"eliot-tfs: {eliot_tfs}")
    # get all font sizes
    all_tfs = sorted(set(map(lambda x: x[1], device.blocks)), reverse=True)
    verbose(f"all_tfs: {all_tfs}")
    selected_blocks = []
    for tfs_index in eliot_tfs:
        current_tfs_index = all_tfs[tfs_index]
        for block in device.blocks:
            if block[1] == current_tfs_index:
                selected_blocks.append(block)

    # sort the selected blocks
    # y min first, then x min if y min is the same
    selected_blocks = sorted(selected_blocks, key=lambda block: (-block[3], block[2]))

    if logger.is_verbose():
        for block in selected_blocks:
            verbose(block)

    title = []
    for block in selected_blocks:
        title.append("".join(block[4]))

    title = "".join(title)
    return title


# pylint: disable=too-many-locals
def __get_pdfdevice(
    pdf_file: io.BufferedReader, page_number: int, replace_missing_char: Optional[str]
):
    parser = PDFParser(pdf_file)
    # if pdf is protected with a pwd, 2nd param here is password
    doc = PDFDocument(parser)
    # pdf may not allow extraction
    if not doc.is_extractable:
        raise PDFTitleException("PDF does not allow extraction")

    resource_manager = PDFResourceManager()
    device = TextOnlyDevice(resource_manager, replace_missing_char)
    interpreter = TextOnlyInterpreter(resource_manager, device)

    first_page = io.StringIO()
    converter = TextConverter(resource_manager, first_page, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    current_page_number = 0

    # list objects in verbose mode
    if logger.is_verbose():
        for xref in doc.xrefs:
            for objid in xref.get_objids():
                obj = doc.getobj(objid)
                if isinstance(obj, dict):
                    verbose(f'{objid}: {obj.get("Type")} {obj}')
                elif isinstance(obj, list):
                    verbose("{objid}: {obj}")
                else:
                    verbose("{objid}: {obj}")

    for page in PDFPage.create_pages(doc):
        current_page_number = current_page_number + 1
        verbose(f"page {current_page_number}")
        if current_page_number == page_number:
            verbose(f"processing page {current_page_number}")
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
    device.recover_last_paragraph()

    return device, first_page_text


def __retrieve_spaces(
    first_page,
    title_without_space,
    p=0,  # pylint: disable=invalid-name
    t=0,  # pylint: disable=invalid-name
    result="",
):
    """retrieve_spaces"""
    while True:
        verbose(f"p: {p}, t: {t}, result: {result}")
        # Stop condition : all the first page has been explored or
        #  we have explored all the letters of the title

        if p >= len(first_page) or t >= len(title_without_space):
            return result

        if first_page[p].lower() == title_without_space[t].lower():
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


def convert_ligatures(text: str) -> str:
    """
    converts latin ligatures (ff, fi, fl, ffi, ffl, ft, st) to individual chars
    see: Unicode Alphabetic Presentation Forms
    https://unicode.org/charts/PDF/UFB00.pdf
    """
    converted = []
    for single_character in text:
        ch_as_utf8 = bytes(single_character, "utf-8")
        if ch_as_utf8 == b"\xef\xac\x80":
            converted.append("f")
            converted.append("f")

        elif ch_as_utf8 == b"\xef\xac\x81":
            converted.append("f")
            converted.append("i")

        elif ch_as_utf8 == b"\xef\xac\x82":
            converted.append("f")
            converted.append("l")

        elif ch_as_utf8 == b"\xef\xac\x83":
            converted.append("f")
            converted.append("f")
            converted.append("i")

        elif ch_as_utf8 == b"\xef\xac\x84":
            converted.append("f")
            converted.append("f")
            converted.append("l")

        elif ch_as_utf8 == b"\xef\xac\x85":
            converted.append("f")
            converted.append("t")

        elif ch_as_utf8 == b"\xef\xac\x86":
            converted.append("s")
            converted.append("t")

        else:
            converted.append(single_character)

    return "".join(converted)


def get_title_from_io(
    pdf_file: io.BufferedReader,
    page_number: int,
    replace_missing_char: Optional[str],
    algorithm: str,
    eliot_tfs: str,
) -> str:
    """get_title_from_io"""

    device, first_page_text = __get_pdfdevice(
        pdf_file, page_number, replace_missing_char
    )

    verbose("all blocks")

    if logger.is_verbose():
        for block in device.blocks:
            verbose(block)

    verbose(f"algo: {algorithm}")

    if algorithm == "original":
        title = __get_title_by_original_algorithm(device)

    elif algorithm == "max2":
        title = __get_title_by_max2_algorithm(device)

    elif algorithm == "eliot":
        title = __get_title_by_eliot_algorithm(device, eliot_tfs)

    else:
        raise PDFTitleException("unsupported ALGO")

    verbose(f"title before space correction: {title}")

    # Retrieve missing spaces if needed
    # warning: if you use eliot algorithm with multiple tfs
    # this procedure may not work
    if " " not in title:
        title_with_spaces = __retrieve_spaces(first_page_text, title)
        # the procedure above may return empty string
        # in that case, leave the title as it is
        if len(title_with_spaces) > 0:
            title = title_with_spaces

    # Remove duplcate spaces if any are present
    if "  " in title:
        title = " ".join(title.split())

    return title


def get_title_from_file(
    pdf_file: str,
    page_number: int,
    replace_missing_char: Optional[str],
    algorithm: str,
    eliot_tfs: str,
) -> str:
    """get_title_from_file"""
    with open(pdf_file, "rb") as raw_file:
        return get_title_from_io(
            raw_file, page_number, replace_missing_char, algorithm, eliot_tfs
        )


def run() -> None:
    """run command line"""
    try:
        parser = argparse.ArgumentParser(
            prog="pdftitle",
            description="extracts the title from a PDF file.",
            epilog="",
        )
        parser.add_argument("-p", "--pdf", help="pdf file", required=True)
        parser.add_argument(
            "-a",
            "--algo",
            help="algorithm to derive title, default is "
            + "original that finds the text with largest "
            + "font size",
            required=False,
            default="original",
            choices=["original", "max2", "eliot"],
        )
        parser.add_argument(
            "--replace-missing-char",
            help="replace missing char with the one " + "specified",
            default=None,
        )
        parser.add_argument(
            "--do-not-convert-ligatures",
            help="do not convert ligatures like fi to individual chars",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-c",
            "--change-name",
            action="store_true",
            help="change the name of the pdf file",
            default=False,
        )
        parser.add_argument(
            "-t",
            "--title-case",
            action="store_true",
            help="modify the case of final title to be title case",
            default=False,
        )
        parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="enable verbose logging",
            default=False,
        )
        parser.add_argument(
            "--eliot-tfs",
            help="the font size list to use for eliot "
            + "algorithm, list separated by comma e.g. 0,1,2 ,"
            + "default 0 (max) only",
            required=False,
            default="0",
        )
        parser.add_argument(
            "--page-number",
            help="the page number (default is 1) "
            + "to extract the title from (starts from 1)",
            required=False,
            type=int,
            default=1,
        )
        args = parser.parse_args()
        # set verbose flag first
        logger.set_verbose(args.verbose)
        verbose(args)
        eliot_tfs = None

        if args.algo == "eliot":
            verbose(f"args.eliot_tfs: {args.eliot_tfs}")
            eliot_tfs = args.eliot_tfs.split(",")
            verbose(f"eliot_tfs: {eliot_tfs}")
            # convert to list of ints
            eliot_tfs = list(map(int, eliot_tfs))
            verbose(f"final eliot_tfs: {eliot_tfs}")

        else:
            eliot_tfs = [0]

        title = get_title_from_file(
            args.pdf, args.page_number, args.replace_missing_char, args.algo, eliot_tfs
        )

        # If no name was found, return a non-zero exit code
        if title is None:
            return 1

        if args.title_case:
            verbose(f"before title case: {title}")
            title = title.title()

        if not args.do_not_convert_ligatures:
            title = convert_ligatures(title)

        # If the user wants to change the name of the file
        if args.change_name:
            # Change the title to a more pleasant file name
            new_name = title.lower()  # Lower case name
            valid_chars = set(string.ascii_lowercase + string.digits + " ")
            new_name = "".join(c for c in new_name if c in valid_chars)
            new_name = new_name.replace(" ", "_") + ".pdf"
            os.rename(args.pdf, new_name)
            print(new_name)

        else:
            print(title)

        return 0

    except PDFTitleException:
        traceback.print_exc()
        return 1
