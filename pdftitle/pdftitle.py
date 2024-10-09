"""pdftitle"""

import argparse
import io
import logging
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

from .constants import ALGO_ORIGINAL, ALGO_MAX2, ALGO_ELIOT
from .exceptions import PDFTitleException
from .device import TextOnlyDevice
from .interpreter import TextOnlyInterpreter


logger = logging.getLogger(__name__)
__xobjids = []


def __xobject_hook(xobjid_args):
    __xobjids.append(xobjid_args)


def __get_title_by_original_algorithm(device: PDFDevice) -> str:
    # find max font size
    max_tfs = max(device.blocks, key=lambda x: x[1])[1]
    logger.info("max_tfs: %s", max_tfs)
    # find max blocks with max font size
    max_blocks = list(filter(lambda x: x[1] == max_tfs, device.blocks))
    # find the one with the highest y coordinate
    # this is the most close to top
    max_y = max(max_blocks, key=lambda x: x[3])[3]
    logger.info("max_y: %s", max_y)
    found_blocks = list(filter(lambda x: x[3] == max_y, max_blocks))
    logger.info("found blocks")

    for block in found_blocks:
        logger.info(block)

    block = found_blocks[0]
    title = "".join(block[4]).strip()
    return title


def __get_title_by_max2_algorithm(device: PDFDevice) -> str:
    # find max font size
    all_tfs = sorted(list(map(lambda x: x[1], device.blocks)), reverse=True)
    max_tfs = all_tfs[0]
    logger.info("max_tfs: %s", max_tfs)
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

    logger.info("selected blocks")
    for block in selected_blocks:
        logger.info(block)

    title = []
    for block in selected_blocks:
        title.append("".join(block[4]))

    title = "".join(title)
    return title


def __get_title_by_eliot_algorithm(device: PDFDevice, eliot_tfs: List[int]) -> str:
    logger.info("eliot-tfs: %s", eliot_tfs)
    # get all font sizes
    all_tfs = sorted(set(map(lambda x: x[1], device.blocks)), reverse=True)
    logger.info("all_tfs: %s", all_tfs)
    selected_blocks = []
    for tfs_index in eliot_tfs:
        current_tfs_index = all_tfs[tfs_index]
        for block in device.blocks:
            if block[1] == current_tfs_index:
                selected_blocks.append(block)

    # sort the selected blocks
    # y min first, then x min if y min is the same
    selected_blocks = sorted(selected_blocks, key=lambda block: (-block[3], block[2]))

    for block in selected_blocks:
        logger.info(block)

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
    interpreter = TextOnlyInterpreter(resource_manager, device, __xobject_hook)

    first_page = io.StringIO()
    converter = TextConverter(resource_manager, first_page, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    current_page_number = 0

    # list objects in verbose mode
    logger.info("<<< PDF objects >>>")
    for xref in doc.xrefs:
        for objid in xref.get_objids():
            obj = doc.getobj(objid)
            if isinstance(obj, dict):
                logger.info("pdfobj %s: %s %s", objid, obj.get("Type"), obj)

            else:
                logger.info("pdfobj %s: %s %s", objid, type(obj).__name__, obj)

    logger.info("<<< >>>")

    for page in PDFPage.create_pages(doc):
        current_page_number = current_page_number + 1
        logger.info("page %d", current_page_number)
        if current_page_number == page_number:
            logger.info("processing page %d", current_page_number)
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
        logger.debug("p: %d, t: %d, result: %s", p, t, result)
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


def __get_new_file_name(title: str) -> str:
    # Change the title to a more pleasant file name
    logger.info("title for change file name: %s", title)
    new_name = title.lower()  # Lower case name
    valid_chars = set(string.ascii_lowercase + string.digits + " ")
    new_name = "".join(c for c in new_name if c in valid_chars)
    new_name = new_name.replace(" ", "_") + ".pdf"
    logger.info("new file name: %s", new_name)
    return new_name


def change_file_name(pdf_file: str, title: str) -> str:
    """change pdf file name to title and return new name"""
    new_name = __get_new_file_name(title)
    os.rename(pdf_file, new_name)
    return new_name


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

    logger.info("all blocks")
    for block in device.blocks:
        logger.info(block)

    logger.info("algorithm: %s", algorithm)

    if algorithm == ALGO_ORIGINAL:
        title = __get_title_by_original_algorithm(device)

    elif algorithm == ALGO_MAX2:
        title = __get_title_by_max2_algorithm(device)

    elif algorithm == ALGO_ELIOT:
        title = __get_title_by_eliot_algorithm(device, eliot_tfs)

    else:
        raise PDFTitleException("unsupported ALGO")

    logger.info("title before space correction: %s", title)

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
            help="algorithm to derive title, default is original that finds "
            + "the text with largest font size",
            required=False,
            default=ALGO_ORIGINAL,
            choices=[ALGO_ORIGINAL, ALGO_MAX2, ALGO_ELIOT],
        )
        parser.add_argument(
            "--replace-missing-char",
            help="replace missing char with the one specified",
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
            action="count",
            help="enable verbose logging, use -vv for debug logging",
            default=0,
        )
        parser.add_argument(
            "--eliot-tfs",
            help="the font size list to use for eliot algorithm, list "
            + "separated by comma e.g. 0,1,2, default 0 (max) only",
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
        # configure logging
        # set default level to warning
        logging.basicConfig(level=logging.WARNING)
        # set the level of `pdftitle` to what is requested
        logging_level = logging.WARNING
        if args.verbose == 1:
            logging_level = logging.INFO
        elif args.verbose >= 2:
            logging_level = logging.DEBUG
        logging.getLogger("pdftitle").setLevel(logging_level)
        logger.info(args)

        # prepare eliot_tfs
        eliot_tfs = None
        if args.algo == ALGO_ELIOT:
            logger.info("args.eliot_tfs: %s", args.eliot_tfs)
            eliot_tfs = args.eliot_tfs.split(",")
            logger.info("eliot_tfs: %s", eliot_tfs)
            # convert to list of ints
            eliot_tfs = list(map(int, eliot_tfs))
            logger.info("final eliot_tfs: %s", eliot_tfs)

        else:
            eliot_tfs = [0]

        title = get_title_from_file(
            args.pdf, args.page_number, args.replace_missing_char, args.algo, eliot_tfs
        )

        # If no name was found, return a non-zero exit code
        if title is None:
            return 1

        # use title case if asked for
        if args.title_case:
            logger.info("before title case: %s", title)
            title = title.title()
            logger.info("after title case: %s", title)

        # convert ligatures unless disabled
        if not args.do_not_convert_ligatures:
            logger.info("before convert ligatures: %s", title)
            title = convert_ligatures(title)
            logger.info("after convert ligatures: %s", title)

        # change file name if asked for
        if args.change_name:
            new_name = change_file_name(args.pdf, title)
            print(new_name)

        else:
            print(title)

        return 0

    except PDFTitleException:
        traceback.print_exc()
        if len(__xobjids) > 0:
            print(
                "PDF contains XObjects and pdftitle does not support XObjects yet. "
                + "The reason for this error can be due to XObjects."
            )
        return 1
