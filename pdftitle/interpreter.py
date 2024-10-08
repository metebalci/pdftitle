"""PDFInterpreter implementation"""

from pdfminer import utils
from pdfminer.pdfinterp import PDFPageInterpreter, PDFInterpreterError
from pdfminer.psparser import literal_name

from .logging import verbose_operator

class TextState():
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
        return (f'<TextState: f={self.Tf}, fs={self.Tfs}, ' +
                'c={self.Tc}, w={self.Tw}, ' +
                'h={self.Th}, l={self.Tl}, ' +
                'mode={self.Tmode}, rise={self.Trise}, ' +
                'm={self.Tm}, lm={self.Tlm}>')

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
    def __init__(
            self,
            rsrcmgr,
            device):
        PDFPageInterpreter.__init__(self, rsrcmgr, device)
        self.mpts = TextState()

    # omit these operators
    def do_w(self, linewidth):
        verbose_operator('PDF OPERATOR w')

    def do_J(self, linecap):
        verbose_operator('PDF OPERATOR J')

    def do_j(self, linejoin):
        verbose_operator('PDF OPERATOR j')

    def do_M(self, miterlimit):
        verbose_operator('PDF OPERATOR M')

    def do_d(self, dash, phase):
        verbose_operator('PDF OPERATOR d')

    def do_ri(self, intent):
        verbose_operator('PDF OPERATOR ri')

    def do_i(self, flatness):
        verbose_operator('PDF OPERATOR i')

    def do_m(self, x, y):
        verbose_operator('PDF OPERATOR m')

    def do_l(self, x, y):
        verbose_operator('PDF OPERATOR l')

    # pylint: disable=too-many-arguments
    def do_c(self, x1, y1, x2, y2, x3, y3):
        verbose_operator('PDF OPERATOR c')

    def do_y(self, x1, y1, x3, y3):
        verbose_operator('PDF OPERATOR y')

    def do_h(self):
        verbose_operator("PDF OPERATOR h")

    def do_re(self, x, y, w, h):
        verbose_operator('PDF OPERATOR re')

    def do_S(self):
        verbose_operator('PDF OPERATOR S')

    def do_s(self):
        verbose_operator('PDF OPERATOR s')

    def do_f(self):
        verbose_operator('PDF OPERATOR f')

    def do_f_a(self):
        verbose_operator('PDF OPERATOR fa')

    def do_B(self):
        verbose_operator('PDF OPERATOR B')

    def do_B_a(self):
        verbose_operator('PDF OPERATOR Ba')

    def do_b(self):
        verbose_operator('PDF OPERATOR b')

    def do_b_a(self):
        verbose_operator('PDF OPERATOR ba')

    def do_n(self):
        verbose_operator('PDF OPERATOR n')

    def do_W(self):
        verbose_operator('PDF OPERATOR W')

    def do_W_a(self):
        verbose_operator('PDF OPERATOR Wa')

    def do_CS(self, name):
        verbose_operator('PDF OPERATOR CS')

    def do_cs(self, name):
        verbose_operator('PDF OPERATOR cs')

    def do_G(self, gray):
        verbose_operator('PDF OPERATOR G')

    def do_g(self, gray):
        verbose_operator('PDF OPERATOR g')

    def do_RG(self, r, g, b):
        verbose_operator('PDF OPERATOR RG')

    def do_rg(self, r, g, b):
        verbose_operator('PDF OPERATOR rg')

    def do_K(self, c, m, y, k):
        verbose_operator('PDF OPERATOR K')

    def do_k(self, c, m, y, k):
        verbose_operator('PDF OPERATOR k')

    def do_SCN(self):
        verbose_operator('PDF OPERATOR SCN')

    def do_scn(self):
        verbose_operator('PDF OPERATOR scn')

    def do_SC(self):
        verbose_operator('PDF OPERATOR SC')

    def do_sc(self):
        verbose_operator('PDF OPERATOR sc')

    def do_sh(self, name):
        verbose_operator('PDF OPERATOR sh')

    def do_EI(self, obj):
        verbose_operator('PDF OPERATOR EI')

    def do_Do(self, xobjid_arg):
        verbose_operator(f'PDF OPERATOR Do: xobjid={xobjid_arg}')

    # text object begin/end
    def do_BT(self):
        verbose_operator('PDF OPERATOR BT')
        self.mpts.on_BT()

    def do_ET(self):
        verbose_operator('PDF OPERATOR ET')
        self.mpts.on_ET()

    # text state operators
    def do_Tc(self, space):
        verbose_operator(f'PDF OPERATOR Tc: space={space}')
        self.mpts.Tc = space

    def do_Tw(self, space):
        verbose_operator(f'PDF OPERATOR Tw: space={space}')
        self.mpts.Tw = space

    def do_Tz(self, scale):
        verbose_operator(f'PDF OPERATOR Tz: scale={scale}')
        self.mpts.Th = scale * 0.01

    def do_TL(self, leading):
        verbose_operator(f'PDF OPERATOR TL: leading={leading}')
        self.mpts.Tl = leading

    def do_Tf(self, fontid, fontsize):
        verbose_operator(f'PDF OPERATOR Tf: fontid={fontid}, ' +
                'fontsize={fontsize}')
        try:
            self.mpts.Tf = self.fontmap[literal_name(fontid)]
            verbose_operator(f'font={self.mpts.Tf.fontname}')
            self.mpts.Tfs = fontsize
        except KeyError as key_error:
            raise PDFInterpreterError(f'Undefined Font id: {fontid}') from key_error

    def do_Tr(self, render):
        verbose_operator(f'PDF OPERATOR Tr: render={render}')
        self.mpts.Tmode = render

    def do_Ts(self, rise):
        verbose_operator(f'PDF OPERATOR Ts: rise={rise}')
        self.mpts.Trise = rise

    # text-move operators

    def do_Td(self, tx, ty):
        verbose_operator(f'PDF OPERATOR Td: tx={tx}, ty={ty}')
        self.mpts.Tlm = utils.translate_matrix(self.mpts.Tlm, (tx, ty))
        self.mpts.Tm = self.mpts.Tlm

    def do_TD(self, tx, ty):
        verbose_operator(f'PDF OPERATOR TD: tx={tx}, ty={ty}')
        self.do_TL(-ty)
        self.do_Td(tx, ty)

    def do_Tm(self, a, b, c, d, e, f):
        verbose_operator(f'PDF OPERATOR Tm: matrix={a}, {b}, {c}. {d}, {e}, {f}')
        self.mpts.Tlm = (a, b, c, d, e, f)
        self.mpts.Tm = self.mpts.Tlm

    # T*
    def do_T_a(self):
        verbose_operator('PDF OPERATOR T*')
        self.do_Td(0, self.mpts.Tl)

    # text-showing operators

    # show a string
    def do_Tj(self, s):
        verbose_operator(f'PDF operator Tj: s={s}')
        self.do_TJ([s])

    # ' quote
    # move to next line and show the string
    # same as:
    # T*
    # string Tj
    def do__q(self, s):
        verbose_operator(f'PDF operator q: s={s}')
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
        verbose_operator(f'PDF OPERATOR \": aw={aw}, ac={ac}, s={s}')
        self.do_Tw(aw)
        self.do_Tc(ac)
        self.do__q(s)

    # show one or more text string, allowing individual glyph positioning
    # each element in the array is either a string or a number
    # if string, it is the string to show
    # if number, it is the number to adjust text position, it translates Tm
    def do_TJ(self, seq):
        verbose_operator(f'PDF OPERATOR TJ: seq={seq}')
        self.device.process_string(self.mpts, seq)
