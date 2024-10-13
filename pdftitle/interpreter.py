# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""PDFInterpreter implementation"""

import logging

from pdfminer import utils
from pdfminer.pdfinterp import PDFPageInterpreter, PDFInterpreterError
from pdfminer.psparser import literal_name


logger = logging.getLogger(__name__)


class TextState:
    """text state"""

    # pylint: disable=invalid-name, too-many-instance-attributes
    def __init__(self):
        # charspace added to each glyph after rendering
        # this is not the width of glyph, this is extra, so default is 0
        # operator Tc
        # unscaled text space units
        self.Tc = 0
        # similar to charspace but applies only to space char=ascii 32
        # operator Tw
        # unscaled text space units
        self.Tw = 0
        # applies always horizontally
        # scales individual glyph widths by this
        # that is why default (scale of operator Tz) is 100, 100%, no change
        # operator Tz
        self.Th = 1
        # distance between the baselines of adjacent text lines
        # always applies to vertical coordinate
        # operator TL
        # unscaled text space units
        self.Tl = 0
        # operator Tf selects both font and font size
        self.Tf = None
        self.Tfs = None
        # only about rendering
        # operator Tr
        self.Tmode = 0
        # moves baseline up or down, so setting this to 0 resets it
        # operator Ts
        # unscaled text space units
        self.Trise = 0
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
        """on_BT"""
        self.Tm = utils.MATRIX_IDENTITY
        self.Tlm = utils.MATRIX_IDENTITY

    def on_ET(self):
        """on_ET"""
        self.Tm = None
        self.Tlm = None


# pylint: disable=too-many-public-methods
class TextOnlyInterpreter(PDFPageInterpreter):
    """PDFPageInterpreter implementation"""

    def __init__(self, rsrcmgr, device, xobject_hook):
        PDFPageInterpreter.__init__(self, rsrcmgr, device)
        self.mpts = TextState()
        self.xobject_hook = xobject_hook

    # omit these operators
    def do_w(self, linewidth):
        logger.debug("PDF OPERATOR w")

    def do_J(self, linecap):
        logger.debug("PDF OPERATOR J")

    def do_j(self, linejoin):
        logger.debug("PDF OPERATOR j")

    def do_M(self, miterlimit):
        logger.debug("PDF OPERATOR M")

    def do_d(self, dash, phase):
        logger.debug("PDF OPERATOR d")

    def do_ri(self, intent):
        logger.debug("PDF OPERATOR ri")

    def do_i(self, flatness):
        logger.debug("PDF OPERATOR i")

    def do_m(self, x, y):
        logger.debug("PDF OPERATOR m")

    def do_l(self, x, y):
        logger.debug("PDF OPERATOR l")

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def do_c(self, x1, y1, x2, y2, x3, y3):
        logger.debug("PDF OPERATOR c")

    def do_y(self, x1, y1, x3, y3):
        logger.debug("PDF OPERATOR y")

    def do_h(self):
        logger.debug("PDF OPERATOR h")

    def do_re(self, x, y, w, h):
        logger.debug("PDF OPERATOR re")

    def do_S(self):
        logger.debug("PDF OPERATOR S")

    def do_s(self):
        logger.debug("PDF OPERATOR s")

    def do_f(self):
        logger.debug("PDF OPERATOR f")

    def do_f_a(self):
        logger.debug("PDF OPERATOR fa")

    def do_B(self):
        logger.debug("PDF OPERATOR B")

    def do_B_a(self):
        logger.debug("PDF OPERATOR Ba")

    def do_b(self):
        logger.debug("PDF OPERATOR b")

    def do_b_a(self):
        logger.debug("PDF OPERATOR ba")

    def do_n(self):
        logger.debug("PDF OPERATOR n")

    def do_W(self):
        logger.debug("PDF OPERATOR W")

    def do_W_a(self):
        logger.debug("PDF OPERATOR Wa")

    def do_CS(self, name):
        logger.debug("PDF OPERATOR CS")

    def do_cs(self, name):
        logger.debug("PDF OPERATOR cs")

    def do_G(self, gray):
        logger.debug("PDF OPERATOR G")

    def do_g(self, gray):
        logger.debug("PDF OPERATOR g")

    def do_RG(self, r, g, b):
        logger.debug("PDF OPERATOR RG")

    def do_rg(self, r, g, b):
        logger.debug("PDF OPERATOR rg")

    def do_K(self, c, m, y, k):
        logger.debug("PDF OPERATOR K")

    def do_k(self, c, m, y, k):
        logger.debug("PDF OPERATOR k")

    def do_SCN(self):
        logger.debug("PDF OPERATOR SCN")

    def do_scn(self):
        logger.debug("PDF OPERATOR scn")

    def do_SC(self):
        logger.debug("PDF OPERATOR SC")

    def do_sc(self):
        logger.debug("PDF OPERATOR sc")

    def do_sh(self, name):
        logger.debug("PDF OPERATOR sh")

    def do_EI(self, obj):
        logger.debug("PDF OPERATOR EI")

    def do_Do(self, xobjid_arg):
        logger.debug("PDF OPERATOR Do: xobjid=%s", xobjid_arg)
        if self.xobject_hook is not None:
            self.xobject_hook(xobjid_arg)

    # text object begin/end
    def do_BT(self):
        logger.debug("PDF OPERATOR BT")
        self.mpts.on_BT()

    def do_ET(self):
        logger.debug("PDF OPERATOR ET")
        self.mpts.on_ET()

    # text state operators
    def do_Tc(self, space):
        logger.debug("PDF OPERATOR Tc: space=%s", space)
        self.mpts.Tc = space

    def do_Tw(self, space):
        logger.debug("PDF OPERATOR Tw: space=%s", space)
        self.mpts.Tw = space

    def do_Tz(self, scale):
        logger.debug("PDF OPERATOR Tz: scale=%s", scale)
        self.mpts.Th = scale * 0.01

    def do_TL(self, leading):
        logger.debug("PDF OPERATOR TL: leading=%s", leading)
        self.mpts.Tl = leading

    def do_Tf(self, fontid, fontsize):
        logger.debug("PDF OPERATOR Tf: fontid=%s, fontsize=%s", fontid, fontsize)
        try:
            self.mpts.Tf = self.fontmap[literal_name(fontid)]
            logger.debug("font=%s", self.mpts.Tf.fontname)
            self.mpts.Tfs = fontsize
        except KeyError as key_error:
            raise PDFInterpreterError(f"Undefined Font id: {fontid}") from key_error

    def do_Tr(self, render):
        logger.debug("PDF OPERATOR Tr: render=%s", render)
        self.mpts.Tmode = render

    def do_Ts(self, rise):
        logger.debug("PDF OPERATOR Ts: rise=%s", rise)
        self.mpts.Trise = rise

    # text-move operators

    def do_Td(self, tx, ty):
        logger.debug("PDF OPERATOR Td: tx=%s, ty=%s", tx, ty)
        self.mpts.Tlm = utils.translate_matrix(self.mpts.Tlm, (tx, ty))
        self.mpts.Tm = self.mpts.Tlm

    def do_TD(self, tx, ty):
        logger.debug("PDF OPERATOR TD: tx=%s, ty=%s", tx, ty)
        self.do_TL(-ty)
        self.do_Td(tx, ty)

    # pylint: disable=too-many-arguments, too-many-positional-arguments
    def do_Tm(self, a, b, c, d, e, f):
        logger.debug("PDF OPERATOR Tm: matrix=%s, %s, %s, %s, %s, %s", a, b, c, d, e, f)
        self.mpts.Tlm = (a, b, c, d, e, f)
        self.mpts.Tm = self.mpts.Tlm

    # T*
    def do_T_a(self):
        logger.debug("PDF OPERATOR T*")
        self.do_Td(0, self.mpts.Tl)

    # text-showing operators

    # show a string
    def do_Tj(self, s):
        logger.debug("PDF operator Tj: s=%s", s)
        self.do_TJ([s])

    # ' quote
    # move to next line and show the string
    # same as:
    # T*
    # string Tj
    def do__q(self, s):
        logger.debug("PDF operator q: s=%s", s)
        self.do_T_a()
        self.do_Tj(s)

    # " doublequote
    # move to next line and show the string
    # using aw word spacing, ac char spacing
    # same as:
    # aw Tw
    # ac Tc
    # string '
    def do__w(self, aw, ac, s):
        logger.debug('PDF OPERATOR ": aw=%s, ac=%s, s=%s', aw, ac, s)
        self.do_Tw(aw)
        self.do_Tc(ac)
        self.do__q(s)

    # show one or more text string, allowing individual glyph positioning
    # each element in the array is either a string or a number
    # if string, it is the string to show
    # if number, it is the number to adjust text position, it translates Tm
    def do_TJ(self, seq):
        logger.debug("PDF OPERATOR TJ: seq=%s", seq)
        self.device.process_string(self.mpts, seq)
