# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""
This module has an Interpreter and TextState implementation.
Interpreter only interprets the operations relevant for pdftitle and uses a TextState
instance.
Interpreter calls Device implementation for actually (fake) drawing the text.
The references are from ISO 32000-2.
"""

import logging

from pdfminer import utils
from pdfminer.pdfinterp import PDFPageInterpreter, PDFInterpreterError
from pdfminer.psparser import literal_name


logger = logging.getLogger(__name__)


# 9.3 Text state parameters and operators
class TextState:
    """text state"""

    # pylint: disable=invalid-name, too-many-instance-attributes
    def __init__(self):
        # text state has 9 parameters, Table 102
        # Tc, Tw, Th, Tl, Tf, Tfs, Tmode, Trise, Tk
        # Tc=charspace added to each glyph after rendering
        # this is not the width of glyph, this is extra, so default is 0
        # operator Tc
        # unscaled text space units
        self.Tc = 0
        # Tw=similar to charspace but applies only to space char=ascii 32
        # operator Tw
        # unscaled text space units
        self.Tw = 0
        # Th=applies always horizontally
        # scales individual glyph widths by this
        # that is why default (scale of operator Tz) is unity, no change
        # actually it is specified in %, thus initial value is 100
        # but here the value is specified as float and normalized to 1
        # operator Tz
        self.Th = 1
        # Tl=distance between the baselines of adjacent text lines
        # always applies to vertical coordinate
        # operator TL
        # unscaled text space units
        self.Tl = 0
        # Tf=text font, Tfs=text font size
        # operator Tf selects both font and font size
        self.Tf = None
        self.Tfs = None
        # only about rendering
        # operator Tr
        # not used in this project
        # Tmode=3 means neither fill nor stroke text, thus invisible
        self.Tmode = 0
        # moves baseline up or down, so setting this to 0 resets it
        # operator Ts
        # unscaled text space units
        self.Trise = 0
        # Tk=text knockout parameter
        # operator gs (TK entry in parameter dictionary)
        # not used in this project
        self.Tk = 0
        # text matrix
        self.Tm = None
        # text line matrix
        self.Tlm = None

    def __repr__(self):
        return (
            f"<TextState: f={self.Tf}, fs={self.Tfs}, "
            + "c={self.Tc}, w={self.Tw}, "
            + "h={self.Th}, l={self.Tl}, "
            + "mode={self.Tmode}, rise={self.Trise}, "
            + "m={self.Tm}, lm={self.Tlm}>"
        )

    def on_BT(self):
        """on_BT initializes Tm annd Tlm to identity"""
        self.Tm = utils.MATRIX_IDENTITY
        self.Tlm = utils.MATRIX_IDENTITY

    def on_ET(self):
        """on_ET discards Tm and Tlm"""
        self.Tm = None
        self.Tlm = None


# pylint: disable=too-many-public-methods
class TextOnlyInterpreter(PDFPageInterpreter):
    """PDFPageInterpreter implementation"""

    def __init__(self, rsrcmgr, device):
        super().__init__(rsrcmgr, device)
        # using TextState above instead of self.textstate:PDFTextState
        self.mpts = TextState()
        self.log_all_operators = False

    # omit graphics state changing operators
    def do_w(self, linewidth):
        """set line width"""
        if self.log_all_operators:
            logger.debug("w linewidth=%s", linewidth)

    def do_J(self, linecap):
        """set line cap style"""
        if self.log_all_operators:
            logger.debug("J linecap=%s", linecap)

    def do_j(self, linejoin):
        """set line join style"""
        if self.log_all_operators:
            logger.debug("j linejoin=%s", linejoin)

    def do_M(self, miterlimit):
        """set miter limit"""
        if self.log_all_operators:
            logger.debug("M miterlimit=%s", miterlimit)

    def do_d(self, dash, phase):
        """set line dash pattern"""
        if self.log_all_operators:
            logger.debug("d dash=%s phase=%s", dash, phase)

    def do_ri(self, intent):
        """set color rendering intent"""
        if self.log_all_operators:
            logger.debug("ri intent=%s", intent)

    def do_i(self, flatness):
        """set flatness tolerance"""
        if self.log_all_operators:
            logger.debug("i flatness=%s", flatness)

    def do_gs(self, name):
        """set parameters from graphics state parameter dictionary"""
        if self.log_all_operators:
            logger.debug("gs name=%s", name)

    def do_m(self, x, y):
        """being new subpath"""
        if self.log_all_operators:
            logger.debug("m x=%s y=%s", x, y)

    def do_l(self, x, y):
        """append straight line segment to path"""
        if self.log_all_operators:
            logger.debug("l x=%s y=%s", x, y)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def do_c(self, x1, y1, x2, y2, x3, y3):
        """append curved segment to path"""
        if self.log_all_operators:
            logger.debug("c")

    def do_v(self, x2, y2, x3, y3):
        """append curved segment to path (initial point replicated)"""
        if self.log_all_operators:
            logger.debug("v")

    def do_y(self, x1, y1, x3, y3):
        """append curved segment to path (final point replicated)"""
        if self.log_all_operators:
            logger.debug("y")

    def do_h(self):
        """close subpath"""
        if self.log_all_operators:
            logger.debug("h")

    def do_re(self, x, y, w, h):
        """append rectangle to path"""
        if self.log_all_operators:
            logger.debug("re")

    def do_S(self):
        """stroke path"""
        if self.log_all_operators:
            logger.debug("S")

    def do_s(self):
        """close and stroke path"""
        if self.log_all_operators:
            logger.debug("s")

    def do_f(self):
        """fill path using nonzero winding number rule"""
        if self.log_all_operators:
            logger.debug("f")

    def do_F(self):
        """fill path using nonzero winding number rule (obsolete)"""
        if self.log_all_operators:
            logger.debug("F")

    def do_f_a(self):
        """fill path using even-odd rule"""
        if self.log_all_operators:
            logger.debug("fa")

    def do_B(self):
        """fill and stroke path using nonzero winding number rule"""
        if self.log_all_operators:
            logger.debug("B")

    def do_B_a(self):
        """fill and stroke path using even-odd rule"""
        if self.log_all_operators:
            logger.debug("Ba")

    def do_b(self):
        """close, fill, and stroke path using nonzero winding number rule"""
        if self.log_all_operators:
            logger.debug("b")

    def do_b_a(self):
        """close, fill, and stroke path using even-odd rule"""
        if self.log_all_operators:
            logger.debug("ba")

    def do_n(self):
        """end path without filling or stroking"""
        if self.log_all_operators:
            logger.debug("n")

    def do_W(self):
        """set clipping path using nonzero winding number rule"""
        if self.log_all_operators:
            logger.debug("W")

    def do_W_a(self):
        """set clipping path using even-odd rule"""
        if self.log_all_operators:
            logger.debug("Wa")

    def do_CS(self, name):
        """set color space for stroking operations"""
        if self.log_all_operators:
            logger.debug("CS")

    def do_cs(self, name):
        """set color space for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("cs")

    def do_G(self, gray):
        """set gray level for stroking operations"""
        if self.log_all_operators:
            logger.debug("G")

    def do_g(self, gray):
        """set gray level for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("g")

    def do_RG(self, r, g, b):
        """set RGB color for stroking operations"""
        if self.log_all_operators:
            logger.debug("RG")

    def do_rg(self, r, g, b):
        """set RGB color for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("rg")

    def do_K(self, c, m, y, k):
        """set CMYK color for stroking operations"""
        if self.log_all_operators:
            logger.debug("K")

    def do_k(self, c, m, y, k):
        """Set CMYK color for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("k")

    def do_SCN(self):
        """set color for stroking operations"""
        if self.log_all_operators:
            logger.debug("SCN")

    def do_scn(self):
        """set color for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("scn")

    def do_SC(self):
        """set color for stroking operations"""
        if self.log_all_operators:
            logger.debug("SC")

    def do_sc(self):
        """set color for nonstroking operations"""
        if self.log_all_operators:
            logger.debug("sc")

    def do_sh(self, name):
        """paint area defined by shading pattern"""
        if self.log_all_operators:
            logger.debug("sh")

    def do_BX(self):
        """begin compatibility section"""
        if self.log_all_operators:
            logger.debug("BX")

    def do_EX(self):
        """end compatibility section"""
        if self.log_all_operators:
            logger.debug("EX")

    def do_MP(self, tag):
        """define marked-content point"""
        if self.log_all_operators:
            logger.debug("MP tag=%s", tag)

    def do_DP(self, tag, props):
        """define marked-content point with property list"""
        if self.log_all_operators:
            logger.debug("DP tag=%s props=%s", tag, props)

    def do_BMC(self, tag):
        """begin marked-content sequence"""
        if self.log_all_operators:
            logger.debug("BMC tag=%s", tag)

    def do_BDC(self, tag, props):
        """begin marked-content sequence with property list"""
        if self.log_all_operators:
            logger.debug("BDC tag=%s props=%s", tag, props)

    def do_EMC(self):
        """end marked-content sequence"""
        if self.log_all_operators:
            logger.debug("EMC")

    def do_BI(self):
        """begin inline image object"""
        if self.log_all_operators:
            logger.debug("BI")

    def do_ID(self):
        """begin inline image data"""
        if self.log_all_operators:
            logger.debug("ID")

    def do_EI(self, obj):
        """end inline image object"""
        if self.log_all_operators:
            logger.debug("EI")

    # 9. Text
    # 9.4.1 General and Table 105
    def do_BT(self):
        """begin text object"""
        logger.debug("BT")
        self.mpts.on_BT()

    def do_ET(self):
        """end a text object"""
        logger.debug("ET")
        self.mpts.on_ET()

    # 9.3 Text state parameters and operators
    def do_Tc(self, space):
        """set character spacing"""
        logger.debug("Tc space=%s", space)
        self.mpts.Tc = space

    def do_Tw(self, space):
        """set the word spacing"""
        logger.debug("Tw space=%s", space)
        self.mpts.Tw = space

    def do_Tz(self, scale):
        """set the horizontal scaling"""
        logger.debug("Tz scale=%s", scale)
        self.mpts.Th = scale * 0.01

    def do_TL(self, leading):
        """set the text leading"""
        logger.debug("TL leading=%s", leading)
        self.mpts.Tl = leading

    def do_Tf(self, fontid, fontsize):
        """set the text font"""
        logger.debug("Tf fontid=%s, fontsize=%s", fontid, fontsize)
        try:
            self.mpts.Tf = self.fontmap[literal_name(fontid)]
            logger.debug("font=%s", self.mpts.Tf.fontname)
            self.mpts.Tfs = fontsize
        except KeyError as key_error:
            raise PDFInterpreterError(f"Undefined Font id: {fontid}") from key_error

    def do_Tr(self, render):
        """set the text rendering mode"""
        logger.debug("Tr render=%s", render)
        self.mpts.Tmode = render

    def do_Ts(self, rise):
        """Set the text rise"""
        logger.debug("Ts rise=%s", rise)

    # text-positioning operators
    # 9.4.2 Text-poitioning operators and Table 106
    def do_Td(self, tx, ty):
        """move to the start of the next line"""
        logger.debug("Td tx=%s, ty=%s", tx, ty)
        self.mpts.Tlm = utils.translate_matrix(self.mpts.Tlm, (tx, ty))
        self.mpts.Tm = self.mpts.Tlm

    def do_TD(self, tx, ty):
        """move to the start of the next line, also set leading"""
        logger.debug("TD tx=%s, ty=%s", tx, ty)
        # TD has the same effect as this code, Table 106
        self.do_TL(-ty)
        self.do_Td(tx, ty)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def do_Tm(self, a, b, c, d, e, f):
        """set text matrix and text line matrix"""
        logger.debug("Tm matrix=%s, %s, %s, %s, %s, %s", a, b, c, d, e, f)
        self.mpts.Tlm = (a, b, c, d, e, f)
        self.mpts.Tm = self.mpts.Tlm

    # T*
    def do_T_a(self):
        """move to the start of the next text line"""
        logger.debug("T*")
        # T* has the same effect as this code, Table 106
        self.do_TD(0, -self.mpts.Tl)

    # text-showing operators
    # 9.4.3 Text-showing operators and Table 107

    # each element in the array is either a string or a number
    # if string, it is the string to show
    # if number, it is the number to adjust text position, it translates Tm
    def do_TJ(self, seq):
        """show text, allowing individual glyph positioning"""
        logger.debug("TJ seq=%s", seq)
        self.device.process_string(self.mpts, seq)

    def do_Tj(self, s):
        """show text"""
        logger.debug("Tj s=%s", s)
        self.do_TJ([s])

    def do__q(self, s):
        """move to the next line and show the text"""
        logger.debug("q s=%s", s)
        # ' has the same effect as this code, Table 107
        self.do_T_a()
        self.do_Tj(s)

    def do__w(self, aw, ac, s):
        """move to the next line and show the text"""
        logger.debug('" aw=%s, ac=%s, s=%s', aw, ac, s)
        # " has the same effect as this code, Table 107
        self.do_Tw(aw)
        self.do_Tc(ac)
        self.do__q(s)

    # include XObject

    def do_Do(self, xobjid_arg):
        logger.debug("Do xobjid_arg=%s", xobjid_arg)
        # the method in the super class navigates to XObject and tries to render it
        # thus calls the appropriate feedback methods here
        super().do_Do(xobjid_arg)
