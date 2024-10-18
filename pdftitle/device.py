# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
This module has a Device implementation.
Device implementation interprets the text drawing. Based on text state, it figures out
the blocks (text blocks having the same font and the same font size). These blocks are
then used by the algorithms to extract the title.
The references are from ISO 32000-2.
"""

import logging

from pdfminer import utils
from pdfminer.pdfdevice import PDFDevice
from pdfminer.pdffont import PDFUnicodeNotDefined

from .exceptions import PDFTitleException


logger = logging.getLogger(__name__)


class TextOnlyDevice(PDFDevice):
    """PDFDevice implementation"""

    def __init__(self, rsrcmgr, missing_char, translation_heuristic):
        super().__init__(rsrcmgr)
        self.last_state = None
        # contains (font, font_size, string)
        self.blocks = []
        # current block
        # font, font size, glyph y, [chars]
        self.current_block = None
        # replacement missing_char
        self.missing_char = missing_char
        self.translation_heuristic = translation_heuristic

    # at the end of the file, we need to recover last block
    def recover_last_paragraph(self):
        """recover_last_paragraph"""
        if self.current_block is None:
            raise PDFTitleException(
                "current block is None, this might be a bug. "
                + "please report it together with the pdf file"
            )

        if len(self.current_block[4]) > 0:
            self.blocks.append(self.current_block)

    # 9.4.4 Text space details
    # displacement after a glyph is painted, horizontal writing mode
    # w0: glyph's horizontal displacement
    # pylint: disable=invalid-name, too-many-arguments, too-many-positional-arguments
    def new_tx(self, w0, Tj, Tfs, Tc, Tw, Th):
        """new_tx"""
        return ((w0 - Tj / 1000) * Tfs + Tc + Tw) * Th

    # 9.4.4 Text space details
    # displacement after a glyph is painted, vertical writing mode
    # w1: glyph's vertical displacement
    # pylint: disable=invalid-name, too-many-arguments, too-many-positional-arguments
    def new_ty(self, w1, Tj, Tfs, Tc, Tw):
        """new_ty"""
        return (w1 - Tj / 1000) * Tfs + Tc + Tw

    def process_string(self, ts, array):
        """process_string"""
        logger.debug("process_string ts array=%s", array)
        for obj in array:
            logger.debug('processing text obj="%s"', obj)
            # if the obj is a number, it means a translation (Tj)
            if utils.isnumber(obj):
                Tj = obj
                logger.debug("processing translation=%s", Tj)
                # translating Tm, change tx and ty according to direction
                # here glyph's displacement (w0, w1) is set to 0
                if ts.Tf.is_vertical():
                    tx = 0
                    ty = self.new_ty(0, Tj, ts.Tfs, 0, ts.Tw)

                else:
                    tx = self.new_tx(0, Tj, ts.Tfs, 0, ts.Tw, ts.Th)
                    ty = 0

                # update Tm accordingly
                ts.Tm = utils.translate_matrix(ts.Tm, (tx, ty))
                # if there is a translation, there can be a word boundary
                # if the displacement due to translation is larger than
                # factor * the displacement due to space character
                # then add a space to current block if there is any
                # factor <= 1
                if self.translation_heuristic:
                    factor = 0.9
                    w_space = ts.Tf.char_width(32)
                    tx_w = self.new_tx(w_space, 0, ts.Tfs, 0, ts.Tw, ts.Th)
                    ty_w = self.new_ty(w_space, 0, ts.Tfs, 0, ts.Tw)
                    add_space = False
                    if ts.Tf.is_vertical():
                        logger.debug(
                            "w_space=%s ty_w=%s Tj=%s ty=%s", w_space, ty_w, Tj, ty
                        )
                        if ty >= (ty_w * factor):
                            add_space = True

                    else:
                        logger.debug(
                            "w_space=%s tx_w=%s Tj=%s tx=%s", w_space, tx_w, Tj, tx
                        )
                        if tx >= (tx_w * factor):
                            add_space = True

                    if add_space and self.current_block is not None:
                        logger.debug("add space to block due to translation")
                        space = ts.Tf.to_unichr(32)
                        self.current_block[4].append(space)

                    logger.debug(
                        "w=%s tx=%s ty=%s Tj=%s tx=%s ty=%s",
                        w_space,
                        self.new_tx(w_space, 0, ts.Tfs, 0, ts.Tw, ts.Th),
                        self.new_ty(w_space, 0, ts.Tfs, 0, ts.Tw),
                        Tj,
                        self.new_tx(0, Tj, ts.Tfs, 0, ts.Tw, ts.Th),
                        self.new_ty(0, Tj, ts.Tfs, 0, ts.Tw),
                    )

            else:
                logger.debug("processing string")
                for cid in ts.Tf.decode(obj):
                    self.draw_cid(ts, cid)

    # pylint: disable=too-many-branches
    def draw_cid(self, ts, cid):
        """draw_cid"""
        logger.debug("drawing cid: %s", cid)
        # 9.4.4 Text space details
        # Trm text rendering matrix
        # here CTM is omitted since we are not rendering to a screen etc.
        # fmt: off
        Trm = utils.mult_matrix(
            (ts.Tfs * ts.Th,    0,              # ,0
             0,                 ts.Tfs,         # ,0
             0,                 ts.Trise        # ,1
             ),
             ts.Tm)
        # fmt: on
        logger.debug("Trm %s", Trm)
        # note: before v0.10, Trm[1] and Trm[2] is checked to be 0
        # and if it is not, the character omitted (return from func)
        # this is correct if only translation Trm[4,5] and
        # scaling Trm[0,3] exists
        # but theoretically Trm[1,2] can also have values

        # textstate.Tw is used for spaces, otherwise it is 0
        if cid == 32:
            Tw = ts.Tw

        else:
            Tw = 0

        try:
            unichar = ts.Tf.to_unichr(cid)
        except PDFUnicodeNotDefined as unicode_not_defined:
            if self.missing_char:
                unichar = self.missing_char

            else:
                raise PDFTitleException(
                    "PDF contains a unicode char that does not exist in the font"
                    + ", consider using --replace-missing-char option"
                ) from unicode_not_defined

        (gx, gy) = utils.apply_matrix_pt(Trm, (0, 0))
        logger.debug("drawing unichar: %s @%d,%d", unichar, gx, gy)
        tfs = Trm[0]
        # if there is no current block, create one
        if self.current_block is None:
            self.current_block = (ts.Tf, tfs, gx, gy, [unichar])

        # if there is a current block, check if it is the same font and same font size
        # if so, then append the char to the current block
        elif (self.current_block[0] == ts.Tf) and (self.current_block[1] == tfs):
            self.current_block[4].append(unichar)

        # if font and/or font size is different, a new block is created
        else:
            self.blocks.append(self.current_block)
            self.current_block = (ts.Tf, tfs, gx, gy, [unichar])

        logger.debug("current block: %s", self.current_block)
        logger.debug("blocks: %s", self.blocks)
        # update text matrix according to glyph's displacement
        w = ts.Tf.char_width(cid)
        # below Tj is set to zero because the translation values in text objects
        # are handled in process_string method
        if ts.Tf.is_vertical():
            tx = 0
            ty = self.new_ty(w, 0, ts.Tfs, ts.Tc, Tw)

        else:
            tx = self.new_tx(w, 0, ts.Tfs, ts.Tc, Tw, ts.Th)
            ty = 0

        # update text matrix by the combined displacement
        ts.Tm = utils.translate_matrix(ts.Tm, (tx, ty))
