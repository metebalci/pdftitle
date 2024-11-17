# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""pdftitle"""

import argparse
from importlib.metadata import version
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
from .metadata import get_title_from_document_information_dictionary
from .metadata import get_title_from_metadata_stream


logger = logging.getLogger(__name__)


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


def __get_pdfdocument(pdf_file: io.BufferedReader) -> PDFDocument:
    return PDFDocument(PDFParser(pdf_file))


# pylint: disable=too-many-locals
def __get_pdfdevice(
    doc: PDFDocument,
    page_number: int,
    replace_missing_char: Optional[str],
    translation_heuristic: bool,
) -> (PDFDevice, io.StringIO):

    resource_manager = PDFResourceManager()
    device = TextOnlyDevice(
        resource_manager, replace_missing_char, translation_heuristic
    )
    interpreter = TextOnlyInterpreter(resource_manager, device)

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
    if os.path.exists(new_name):
        raise PDFTitleException(f"a file named {new_name} already exists")

    os.rename(pdf_file, new_name)
    return new_name


# the defaults here are also used as defaults for command line arguments
# this class is added to not change the signature of the methods when a new option
# is added
# pylint: disable=too-few-public-methods
class GetTitleParameters:
    """parameters used by get_title methods"""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(
        self,
        use_document_information_dictionary: bool = False,
        use_metadata_stream: bool = False,
        page_number: int = 1,
        replace_missing_char: Optional[str] = None,
        translation_heuristic: bool = False,
        algorithm: str = ALGO_ORIGINAL,
        eliot_tfs: str = None,
    ):
        self.use_document_information_dictionary = use_document_information_dictionary
        self.use_metadata_stream = use_metadata_stream
        self.page_number = page_number
        self.replace_missing_char = replace_missing_char
        self.translation_heuristic = translation_heuristic
        self.algorithm = algorithm
        self.eliot_tfs = eliot_tfs


def get_title_from_doc(doc: PDFDocument, params: GetTitleParameters) -> Optional[str]:
    """get_title_from_doc"""

    metadata_stream_title = get_title_from_metadata_stream(doc)
    logger.debug("dc:title in metadata streams: %s", metadata_stream_title)

    document_info_dict_title = get_title_from_document_information_dictionary(doc)
    logger.debug(
        "Title in document information dictionary: %s", document_info_dict_title
    )

    # metadata streams are the current method
    if params.use_metadata_stream and metadata_stream_title is not None:
        logger.info("using the title from metadata stream")
        return metadata_stream_title

    # using document information dictionary is depreceated for title
    if (
        params.use_document_information_dictionary
        and document_info_dict_title is not None
    ):
        logger.info("using the title from document information dictionary")
        return document_info_dict_title

    # pdf may not allow extraction
    if not doc.is_extractable:
        raise PDFTitleException("PDF does not allow extraction")

    device, first_page_text = __get_pdfdevice(
        doc,
        params.page_number,
        params.replace_missing_char,
        params.translation_heuristic,
    )

    logger.info("all blocks")
    for block in device.blocks:
        logger.info(block)

    logger.info("algorithm: %s", params.algorithm)

    if params.algorithm == ALGO_ORIGINAL:
        title = __get_title_by_original_algorithm(device)

    elif params.algorithm == ALGO_MAX2:
        title = __get_title_by_max2_algorithm(device)

    elif params.algorithm == ALGO_ELIOT:
        title = __get_title_by_eliot_algorithm(device, params.eliot_tfs)

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


def get_title_from_io(
    pdf_file: io.BufferedReader,
    params: GetTitleParameters,
) -> Optional[str]:
    """get_title_from_io"""
    return get_title_from_doc(__get_pdfdocument(pdf_file), params)


def get_title_from_file(
    pdf_file: str,
    params: GetTitleParameters,
) -> Optional[str]:
    """get_title_from_file"""
    with open(pdf_file, "rb") as file_reader:
        return get_title_from_io(file_reader, params)


# pylint: disable=too-many-statements, too-many-branches
def run() -> None:
    """run command line"""
    try:
        # use parameters for default values to have them at a single place
        params = GetTitleParameters()
        parser = argparse.ArgumentParser(
            prog="pdftitle",
            description="extracts the title from a PDF file.",
            epilog="",
        )
        parser.add_argument(
            "--version",
            action="version",
            version=version("pdftitle"),
        )
        parser.add_argument(
            "-p",
            "--pdf",
            help="pdf file to extract title",
            required=True,
        )
        parser.add_argument(
            "-c",
            "--change-name",
            action="store_true",
            help="change the name of the pdf file to the found title",
            default=False,
        )
        parser.add_argument(
            "--do-not-convert-ligatures",
            help="do not convert ligatures like fi to individual chars",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "-l",
            "--list-blocks",
            action="store_true",
            help="list the found blocks",
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
            "-a",
            "--algo",
            help="algorithm to derive title, default is original that finds "
            + "the text with largest font size",
            required=False,
            default=params.algorithm,
            choices=[ALGO_ORIGINAL, ALGO_MAX2, ALGO_ELIOT],
        )
        parser.add_argument(
            "--replace-missing-char",
            help="replace missing char with the one specified",
            default=params.replace_missing_char,
        )
        parser.add_argument(
            "-m",
            "--use-metadata",
            help="use metadata if exists",
            action="store_true",
            default=False,
        )
        parser.add_argument(
            "--use-document-information-dictionary",
            help="use the title from the document information dictionary if exists",
            action="store_true",
            default=params.use_document_information_dictionary,
        )
        parser.add_argument(
            "--use-metadata-stream",
            help="use the title from the metadata stream if exists",
            action="store_true",
            default=params.use_metadata_stream,
        )
        parser.add_argument(
            "--eliot-tfs",
            help="the font size list to use for eliot algorithm, list "
            + "separated by comma e.g. 0,1,2, default 0 (max)",
            required=False,
            default=params.eliot_tfs,
        )
        parser.add_argument(
            "--page-number",
            help="the page number (default is 1) "
            + "to extract the title from (starts from 1)",
            required=False,
            type=int,
            default=params.page_number,
        )
        parser.add_argument(
            "--translation-heuristic",
            help="enable translation heuristic",
            action="store_true",
            required=False,
            default=params.translation_heuristic,
        )
        args = parser.parse_args()
        # configure logging
        # set default level to warning
        logging_format = "%(levelname)s/%(filename)s: %(message)s"
        logging.basicConfig(level=logging.WARNING, format=logging_format)
        # set the level of `pdftitle` to what is requested
        logging_level = logging.WARNING
        if args.verbose == 1:
            logging_level = logging.INFO

        elif args.verbose >= 2:
            logging_level = logging.DEBUG

        logging.getLogger("pdftitle").setLevel(logging_level)
        logger.info(args)

        # list blocks if -l is given
        # this is called early because there is no need to support this with algorithms
        # and no API function needed
        if args.list_blocks:
            with open(args.pdf, "rb") as pdf_file:
                doc = __get_pdfdocument(pdf_file)
                # pdf may not allow extraction
                if not doc.is_extractable:
                    raise PDFTitleException("PDF does not allow extraction")

                device, _ = __get_pdfdevice(
                    doc,
                    params.page_number,
                    params.replace_missing_char,
                    params.translation_heuristic,
                )

                # this is for formatting properly the output
                max_num_int_digits = None
                for block in sorted(device.blocks, key=lambda x: x[1], reverse=True):
                    font_size = block[1]
                    if max_num_int_digits is None:
                        max_num_int_digits = max(1, len(str(int(font_size))))
                    str_array = block[4]
                    format_str = f"%0{4+max_num_int_digits}.3f: %s"
                    print(format_str % (font_size, "".join(str_array).strip()))

        else:
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
                args.pdf,
                GetTitleParameters(
                    use_document_information_dictionary=(
                        args.use_metadata or args.use_document_information_dictionary
                    ),
                    use_metadata_stream=args.use_metadata or args.use_metadata_stream,
                    page_number=args.page_number,
                    replace_missing_char=args.replace_missing_char,
                    translation_heuristic=args.translation_heuristic,
                    algorithm=args.algo,
                    eliot_tfs=eliot_tfs,
                ),
            )

            logger.info("title: :%s", title)

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

            # change file name if -c is given
            if args.change_name:
                new_name = change_file_name(args.pdf, title)
                print(new_name)

            # or print title
            else:
                print(title)

        return 0

    except PDFTitleException:
        traceback.print_exc()
        return 1
