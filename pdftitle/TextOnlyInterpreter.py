
from . import verbose_operator
from .TextState import TextState

from pdfminer import utils
from pdfminer.pdfinterp import PDFPageInterpreter, PDFInterpreterError
from pdfminer.psparser import literal_name

class TextOnlyInterpreter(PDFPageInterpreter):
    # -pylint: disable=too-many-public-methods

    def __init__(
            self, 
            rsrcmgr, 
            device):
        PDFPageInterpreter.__init__(self, rsrcmgr, device)
        self.mpts = TextState()

    # omit these operators
    def do_w(self, linewidth):
        verbose_operator("PDF OPERATOR w")

    def do_J(self, linecap):
        verbose_operator("PDF OPERATOR J")

    def do_j(self, linejoin):
        verbose_operator("PDF OPERATOR j")

    def do_M(self, miterlimit):
        verbose_operator("PDF OPERATOR M")

    def do_d(self, dash, phase):
        verbose_operator("PDF OPERATOR d")

    def do_ri(self, intent):
        verbose_operator("PDF OPERATOR ri")

    def do_i(self, flatness):
        verbose_operator("PDF OPERATOR i")

    def do_m(self, x, y):
        verbose_operator("PDF OPERATOR m")

    def do_l(self, x, y):
        verbose_operator("PDF OPERATOR l")

    def do_c(self, x1, y1, x2, y2, x3, y3):  # pylint: disable=too-many-arguments
        verbose_operator("PDF OPERATOR c")

    def do_y(self, x1, y1, x3, y3):
        verbose_operator("PDF OPERATOR y")

    def do_h(self):
        verbose_operator("PDF OPERATOR h")

    def do_re(self, x, y, w, h):
        verbose_operator("PDF OPERATOR re")

    def do_S(self):
        verbose_operator("PDF OPERATOR S")

    def do_s(self):
        verbose_operator("PDF OPERATOR s")

    def do_f(self):
        verbose_operator("PDF OPERATOR f")

    def do_f_a(self):
        verbose_operator("PDF OPERATOR fa")

    def do_B(self):
        verbose_operator("PDF OPERATOR B")

    def do_B_a(self):
        verbose_operator("PDF OPERATOR Ba")

    def do_b(self):
        verbose_operator("PDF OPERATOR b")

    def do_b_a(self):
        verbose_operator("PDF OPERATOR ba")

    def do_n(self):
        verbose_operator("PDF OPERATOR n")

    def do_W(self):
        verbose_operator("PDF OPERATOR W")

    def do_W_a(self):
        verbose_operator("PDF OPERATOR Wa")

    def do_CS(self, name):
        verbose_operator("PDF OPERATOR CS")

    def do_cs(self, name):
        verbose_operator("PDF OPERATOR cs")

    def do_G(self, gray):
        verbose_operator("PDF OPERATOR G")

    def do_g(self, gray):
        verbose_operator("PDF OPERATOR g")

    def do_RG(self, r, g, b):
        verbose_operator("PDF OPERATOR RG")

    def do_rg(self, r, g, b):
        verbose_operator("PDF OPERATOR rg")

    def do_K(self, c, m, y, k):
        verbose_operator("PDF OPERATOR K")

    def do_k(self, c, m, y, k):
        verbose_operator("PDF OPERATOR k")

    def do_SCN(self):
        verbose_operator("PDF OPERATOR SCN")

    def do_scn(self):
        verbose_operator("PDF OPERATOR scn")

    def do_SC(self):
        verbose_operator("PDF OPERATOR SC")

    def do_sc(self):
        verbose_operator("PDF OPERATOR sc")

    def do_sh(self, name):
        verbose_operator("PDF OPERATOR sh")

    def do_EI(self, obj):
        verbose_operator("PDF OPERATOR EI")

    def do_Do(self, xobjid):
        verbose_operator("PDF OPERATOR Do: xobjid=", xobjid)

    # text object begin/end
    def do_BT(self):
        verbose_operator("PDF OPERATOR BT")
        self.mpts.on_BT()

    def do_ET(self):
        verbose_operator("PDF OPERATOR ET")
        self.mpts.on_ET()

    # text state operators
    def do_Tc(self, space):
        verbose_operator("PDF OPERATOR Tc: space=", space)
        self.mpts.Tc = space

    def do_Tw(self, space):
        verbose_operator("PDF OPERATOR Tw: space=", space)
        self.mpts.Tw = space

    def do_Tz(self, scale):
        verbose_operator("PDF OPERATOR Tz: scale=", scale)
        self.mpts.Th = scale * 0.01

    def do_TL(self, leading):
        verbose_operator("PDF OPERATOR TL: leading=", leading)
        self.mpts.Tl = leading

    def do_Tf(self, fontid, fontsize):
        verbose_operator("PDF OPERATOR Tf: fontid=", fontid,
                         ", fontsize=", fontsize)
        try:
            self.mpts.Tf = self.fontmap[literal_name(fontid)]
            verbose_operator("font=", self.mpts.Tf.fontname)
            self.mpts.Tfs = fontsize
        except KeyError:
            # pylint: disable=raise-missing-from
            raise PDFInterpreterError('Undefined Font id: %r' % fontid)

    def do_Tr(self, render):
        verbose_operator("PDF OPERATOR Tr: render=", render)
        self.mpts.Tmode = render

    def do_Ts(self, rise):
        verbose_operator("PDF OPERATOR Ts: rise=", rise)
        self.mpts.Trise = rise

    # text-move operators

    def do_Td(self, tx, ty):
        verbose_operator("PDF OPERATOR Td: tx=", tx, ", ty=", ty)
        self.mpts.Tlm = utils.translate_matrix(self.mpts.Tlm, (tx, ty))
        self.mpts.Tm = self.mpts.Tlm

    def do_TD(self, tx, ty):
        verbose_operator("PDF OPERATOR TD: tx=", tx, ", ty=", ty)
        self.do_TL(-ty)
        self.do_Td(tx, ty)

    def do_Tm(self, a, b, c, d, e, f):  # pylint: disable=too-many-arguments
        verbose_operator("PDF OPERATOR Tm: matrix=", (a, b, c, d, e, f))
        self.mpts.Tlm = (a, b, c, d, e, f)
        self.mpts.Tm = self.mpts.Tlm

    # T*
    def do_T_a(self):
        verbose_operator("PDF OPERATOR T*")
        self.do_Td(0, self.mpts.Tl)

    # text-showing operators

    # show a string
    def do_Tj(self, s):
        verbose_operator("PDF operator Tj: s=", s)
        self.do_TJ([s])

    # ' quote
    # move to next line and show the string
    # same as:
    # T*
    # string Tj
    def do__q(self, s):
        verbose_operator("PDF operator q: s=", s)
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
        verbose_operator("PDF OPERATOR \": aw=", aw,
                         ", ac=", ac, ", s=", s)
        self.do_Tw(aw)
        self.do_Tc(ac)
        self.do__q(s)

    # show one or more text string, allowing individual glyph positioning
    # each element in the array is either a string or a number
    # if string, it is the string to show
    # if number, it is the number to adjust text position, it translates Tm
    def do_TJ(self, seq):
        verbose_operator("PDF OPERATOR TJ: seq=", seq)
        self.device.process_string(self.mpts, seq)
