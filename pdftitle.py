import sys
import argparse
import traceback
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.psparser import literal_name
from pdfminer.pdfpage import PDFPage, PDFTextExtractionNotAllowed
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfdevice import PDFDevice
from pdfminer import utils
from pdfminer.pdffont import PDFUnicodeNotDefined

VERBOSE = False
MISSING_CHAR = None
WITHIN_WORD_MOVE_LIMIT = 0
IDENTITY_MATRIX = (1, 0, 0, 0, 1, 0)

def verbose(*s):
    if VERBOSE:
        print(*s)

def verbose_operator(*s):
    if VERBOSE:
        print(*s)

class TextState(object):

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
        return

    def __repr__(self):
        return ('<TextState: f=%r, fs=%r, c=%r, w=%r, '
                'h=%r, l=%r, mode=%r, rise=%r, '
                'm=%r, lm=%r>' %
                (self.Tf, self.Tfs, self.Tc, self.Tw,
                    self.Th, self.Tl, self.Tmode, self.Trise,
                    self.Tm, self.Tlm))

    def on_BT(self):
        self.Tm = IDENTITY_MATRIX
        self.Tlm = IDENTITY_MATRIX
        return

    def on_ET(self):
        self.Tm = None
        self.Tlm = None
        return

class TextOnlyInterpreter(PDFPageInterpreter):

    def __init__(self, rsrcmgr, device):
        PDFPageInterpreter.__init__(self, rsrcmgr, device)
        self.mpts = TextState()

    # omit these operators
    def do_w(self, linewidth):
        return
    def do_J(self, linecap):
        return
    def do_j(self, linejoin):
        return
    def do_M(self, miterlimit):
        return
    def do_d(self, dash, phase):
        return
    def do_ri(self, intent):
        return
    def do_i(self, flatness):
        return
    def do_m(self, x, y):
        return
    def do_l(self, x, y):
        return
    def do_c(self, x1, y1, x2, y2, x3, y3):
        return
    def do_y(self, x1, y1, x3, y3):
        return
    def do_h(self):
        return
    def do_re(self, x, y, w, h):
        return
    def do_S(self):
        return
    def do_s(self):
        return
    def do_f(self):
        return
    def do_f_a(self):
        return
    def do_B(self):
        return
    def do_B_a(self):
        return
    def do_b(self):
        return
    def do_b_a(self):
        return
    def do_n(self):
        return
    def do_W(self):
        return
    def do_W_a(self):
        return
    def do_CS(self, name):
        return
    def do_cs(self, name):
        return
    def do_G(self, gray):
        return
    def do_g(self, gray):
        return
    def do_RG(self, r, g, b):
        return
    def do_rg(self, r, g, b):
        return
    def do_K(self, c, m, y, k):
        return
    def do_k(self, c, m, y, k):
        return
    def do_SCN(self):
        return
    def do_scn(self):
        return
    def so_SC(self):
        return
    def do_sc(self):
        return
    def do_sh(self, name):
        return
    def do_EI(self, obj):
        return
    def do_Do(self, xobjid):
        return

    # text object

    def do_BT(self):
        verbose_operator("PDF OPERATOR BT")
        self.mpts.on_BT()
        return

    def do_ET(self):
        verbose_operator("PDF OPERATOR ET")
        self.mpts.on_ET()
        return

    # text state operators

    def do_Tc(self, charSpace):
        verbose_operator("PDF OPERATOR Tc: charSpace=", charSpace)
        self.mpts.Tc = charSpace
        return

    def do_Tw(self, wordSpace):
        verbose_operator("PDF OPERATOR Tw: wordSpace=", wordSpace)
        self.mpts.Tw = wordSpace
        return

    def do_Tz(self, scale):
        verbose_operator("PDF OPERATOR Tz: scale=", scale)
        self.mpts.Th = scale * 0.01
        return

    def do_TL(self, leading):
        verbose_operator("PDF OPERATOR TL: leading=", leading)
        self.mpts.Tl = leading
        return

    def do_Tf(self, fontid, fontsize):
        verbose_operator("PDF OPERATOR Tf: fontid=", fontid, ", fontsize=", fontsize)
        try:
            self.mpts.Tf = self.fontmap[literal_name(fontid)]
            verbose_operator("font=", self.mpts.Tf.fontname)
            self.mpts.Tfs = fontsize
            return
        except KeyError:
            raise PDFInterpreterError('Undefined Font id: %r' % fontid)

    def do_Tr(self, render):
        verbose_operator("PDF OPERATOR Tr: render=", render)
        self.mpts.Tmode = render
        return

    def do_Ts(self, rise):
        verbose_operator("PDF OPERATOR Ts: rise=", rise)
        self.mpts.Trise = rise
        return

    # text-move operators

    def do_Td(self, tx, ty):
        verbose_operator("PDF OPERATOR Td: tx=", tx, ", ty=", ty)
        m = (1, 0, 0, 1, tx, ty)
        self.mpts.Tlm = utils.mult_matrix(m, self.mpts.Tlm)
        self.mpts.Tm = self.mpts.Tlm
        return

    def do_TD(self, tx, ty):
        verbose_operator("PDF OPERATOR TD: tx=", tx, ", ty=", ty)
        self.do_TL(-ty)
        self.do_Td(tx, ty)
        return

    def do_Tm(self, a, b, c, d, e, f):
        verbose_operator("PDF OPERATOR Tm: matrix=", (a, b, c, d, e, f))
        self.mpts.Tlm = (a, b, c, d, e, f)
        self.mpts.Tm = self.mpts.Tlm
        return

    # T*
    def do_T_a(self):
        verbose_operator("PDF OPERATOR T*")
        self.do_Td(0, self.mpts.Tl)
        return

    # text-showing operators

    def do_Tj(self, string):
        verbose_operator("PDF operator Tj: string=", string)
        self.do_TJ([string])
        return

    # ' quote
    def do__q(self, string):
        verbose_operator("PDF operator ': string=", string)
        self.do_T_a()
        self.do_Tj(string)
        return

    # " doublequote
    def do__w(self, aw, ac, string):
        verbose_operator("PDF OPERATOR \": aw=", aw, ", ac=", ac, ", string=", string)
        self.do_Tw(aw)
        self.do_Tc(ac)
        self.do__q(string)
        return

    def do_TJ(self, array):
        verbose_operator("PDF OPERATOR TJ: array=", array)
        self.device.show_string(self.mpts, array)
        return

class TextOnlyDevice(PDFDevice):

    def __init__(self, rsrcmgr):
        PDFDevice.__init__(self, rsrcmgr)
        self.last_state = None
        self.paragraph = []
        self.paragraph_map = {}
        return

    # at the end of the file, we need to recover last paragraph
    def recover_last_paragraph(self):
        if len(self.paragraph) > 0:
            self.paragraph_map[self.last_state[0]] = ' '.join(self.paragraph)
        return

    def show_string(self, ts, array):
        verbose(ts)
        sentence = []
        word = []
        m = (ts.Tfs * ts.Th, 0, 0, ts.Tfs, 0, ts.Trise)
        applicable_Tm = utils.mult_matrix(m, ts.Tm)
        (sx, _, _, sy, tx, ty) = applicable_Tm
        current_state = (sx, sy, tx, ty)
        if self.last_state == None:
            self.paragraph = []
            verbose('current paragraph becomes=', self.paragraph)
        elif current_state[0] == self.last_state[0]:
            verbose('DECISION: grouping the text object to last')
        else:
            verbose('DECISION: finalizing the paragraph')
            key = self.last_state[0]
            item = self.paragraph_map.get(key, '')
            if len(item) > 0:
                item = item = ' '
            new_item = ' '.join(self.paragraph)
            self.paragraph_map[key] = item + new_item
            self.paragraph = []
            verbose('current paragraph becomes=', self.paragraph)
        self.last_state = current_state
        for obj in array:
            verbose("processing obj=", obj)
            if utils.isnumber(obj):
                Tj = obj
                if Tj < WITHIN_WORD_MOVE_LIMIT:
                    verbose("DECISION: new word")
                    sentence.append(''.join(word))
                    verbose('current sentence becomes=', sentence)
                    word = []
                    verbose('current word becomes=', word)
                else:
                    verbose("DECISION: move inside the current word")
                if ts.Tf.is_vertical():
                    tx = 0
                    ty = ((Tj / 1000) * ts.Tfs)
                else:
                    tx = ((Tj / 1000) * ts.Tfs) * ts.Th
                    ty = 0
                ts.Tm = utils.mult_matrix((1, 0, 0, 1, tx, ty), ts.Tm)
            else:
                for cid in ts.Tf.decode(obj):
                    verbose("processing cid=", cid)
                    m = (ts.Tfs * ts.Th, 0, 0, ts.Tfs, 0, ts.Trise)
                    applicable_Tm = utils.mult_matrix(m, ts.Tm)
                    if cid == 32:
                        applicable_Tw = ts.Tw
                        sentence.append(''.join(word))
                        verbose('current sentence becomes=', sentence)
                        word = []
                    else:
                        try:
                            text = ts.Tf.to_unichr(cid)
                        except PDFUnicodeNotDefined:
                            if MISSING_CHAR:
                                text = MISSING_CHAR
                            else:
                                raise
                        word.append(text)
                        verbose('current word becomes=', word)
                        applicable_Tw = 0
                    w = ts.Tf.char_width(cid)
                    if ts.Tf.is_vertical():
                        tx = 0
                        ty = ((w - 0) * ts.Tfs + ts.Tc + applicable_Tw)
                    else:
                        tx = ((w - 0) * ts.Tfs + ts.Tc + applicable_Tw) * ts.Th
                        ty = 0
                    ts.Tm = utils.mult_matrix((1, 0, 0, 1, tx, ty), ts.Tm)
        if len(word) > 0:
            sentence.append(''.join(word))
            verbose('current sentence becomes=', sentence)
            word = []
            verbose('current word becomes=', word)
        self.paragraph.append(' '.join(sentence))
        verbose('current paragraph becomes=', self.paragraph)
        return

def get_title(pdf_file):
    with open(pdf_file, 'rb') as raw_file:
        parser = PDFParser(raw_file)
        # if pdf is protected with a pwd, 2nd param here is password
        doc = PDFDocument(parser)
        # pdf may not allow extraction
        if doc.is_extractable:
            rm = PDFResourceManager()
            dev = TextOnlyDevice(rm)
            interpreter = TextOnlyInterpreter(rm, dev)
            for page in PDFPage.create_pages(doc):
                interpreter.process_page(page)
                break
            dev.recover_last_paragraph()
            sizes = dev.paragraph_map.keys()
            verbose('there are ', len(sizes), ' text blocks with different font sizes')
            max_size = max(sizes)
            verbose('max font size', max_size);
            return ''.join(dev.paragraph_map[max_size])

def run():
    try:
        parser = argparse.ArgumentParser(
                prog='pdftitle',
                description='Extracts the title of a PDF article',
                epilog='')
        parser.add_argument('-p', '--pdf', help='pdf file', required=True)
        parser.add_argument('--replace-missing-char', help='replace missing char with the one specified')
        parser.add_argument('--within-word-move-limit', help='sets the limit for deciding word boundry for within word movement in array given for TJ operator', default=-50)
        parser.add_argument('-v', '--verbose', action='store_true', help='enable verbose logging')
        args = parser.parse_args()
        global VERBOSE, MISSING_CHAR, WITHIN_WORD_MOVE_LIMIT
        VERBOSE = args.verbose
        MISSING_CHAR = args.replace_missing_char
        WITHIN_WORD_MOVE_LIMIT = args.within_word_move_limit
        print(get_title(args.pdf))
        return 0
    except Exception as e:
        if VERBOSE:
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(run())
