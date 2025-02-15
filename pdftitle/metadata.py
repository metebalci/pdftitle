# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""metadata extractor implementation"""

import logging
from typing import Optional
from xml.etree import ElementTree

from pdfminer.pdfdocument import PDFDocument
from pdfminer.encodingdb import EncodingDB

from .exceptions import PDFTitleException


logger = logging.getLogger(__name__)


def get_title_from_document_information_dictionary(doc: PDFDocument) -> Optional[str]:
    """
    extracts Title from document information dictionary
    if not exists, returns None
    """
    # doc.info = None is actually not possible
    if doc.info is None:
        return None

    # pdfminer checks all trailers so adds info from every trailer to a list
    # called doc.info
    for info_from_one_trailer in doc.info:
        logger.debug("document information dictionary: %s", info_from_one_trailer)
        title = info_from_one_trailer.get("Title", None)
        if title is not None:
            logger.info("title found in document information dictionary: %s", title)
            # see 7.9.2.2.1 Text string type > General
            # title is of type text string
            # which can be encoded as PdfDocEncoding, UTF-8 or UTF-16BE
            if (len(title) >= 2) and (title[0] == 254) and (title[1] == 255):
                logger.debug("title is encoded as utf-16be")
                try:
                    title = title.decode("utf-16")
                except UnicodeDecodeError:
                    logger.debug("cannot decode title as utf-16")
                    return None

            elif (
                (len(title) >= 3)
                and (title[0] == 239)
                and (title[1] == 187)
                and (title[2] == 191)
            ):
                logger.debug("title is encoded as utf-8")
                try:
                    title = title.decode("utf-8")
                except UnicodeDecodeError:
                    logger.debug("cannot decode title as utf-8")
                    return None

            else:
                logger.debug("title is encoded as PdfDocEncoding")
                decoded_title = []
                for b in title:
                    c = EncodingDB.pdf2unicode.get(b, None)
                    if c is None:
                        logger.debug("cannot decode title as PdfDocEncoding")
                        return None

                    decoded_title.append(c)

                title = "".join(decoded_title)

            # return only if it is not empty
            if len(title.strip()) > 0:
                return title

    return None


def get_title_from_metadata_stream(doc: PDFDocument) -> Optional[str]:
    """
    extracts Title from metadata streams
    if not exists, returns None
    """
    # document-level metadata might be attached through the catalog dictionary
    metadata_objref = doc.catalog.get("Metadata", None)
    logger.debug("metadata objref in catalog: %s", metadata_objref)
    metadata_stream = None
    if metadata_objref is not None:
        metadata_stream = metadata_objref.resolve()

    # theoretically this can be still done if catalog does not have metadata
    # but not sure if it makes sense
    #
    # if not, search all objects to find a metadata stream
    # just in case it is not attached to the catalog dictionary
    # else:
    #    for xref in doc.xrefs:
    #        for obj_id in xref.get_objids():
    #            obj = doc.getobj(obj_id)
    #            if isinstance(obj, PDFStream):
    #                if obj.attrs.get("Type", None) == LIT("Metadata"):
    #                    if obj.attrs.get("Subtype", None) == LIT("XML"):
    #                        logger.info("found metadata by searching all objects")
    #                        metadata_stream = obj

    title = None
    if metadata_stream is not None:
        logger.debug("metadata stream: %s", metadata_stream)
        xml = metadata_stream.rawdata.decode("utf-8").strip()
        logger.debug("metadata xml: %s", xml)
        try:
            root = ElementTree.fromstring(xml)
        except ElementTree.ParseError:
            logger.debug("cannot parse metadata xml")
            return None
        logger.debug("metadata root: %s", root)
        title_elements = root.findall(".//{http://purl.org/dc/elements/1.1/}title")
        if title_elements is None or len(title_elements) == 0:
            # no title found
            title = None
            logger.info("no dc:title element found")

        elif len(title_elements) == 1:
            # one title metadata found
            title_element = title_elements[0]
            logger.debug("one dc:title element found")
            # pylint: disable=line-too-long
            alt_elements = title_element.findall(
                "./{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Alt/{http://www.w3.org/1999/02/22-rdf-syntax-ns#}li"
            )
            if len(alt_elements) > 0:
                logger.debug("it has alternative languages")
                for alt_element in alt_elements:
                    lang = alt_element.get("{http://www.w3.org/XML/1998/namespace}lang")
                    logger.debug("lang: %s", lang)
                    if lang == "x-default":
                        title = alt_element.text
                        logger.info("title found in dc:title set as default: %s", title)
                        break

            else:
                title = title_element.text
                logger.info("title found in one dc:title element: %s", title)

        else:
            logger.error("more than one dc:title elements found")
            # more than one title metadata found, error
            for title_element in title_elements:
                logger.error("dc:title element: %s", title_element)

            raise PDFTitleException("more than one title metadata")

    # return only if it is not an empty string
    if title is not None and len(title.strip()) > 0:
        return title

    return None
