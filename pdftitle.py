# pylint: disable=missing-module-docstring
# pylint: disable=missing-function-docstring
# pylint: disable=missing-class-docstring
# pylint: disable=invalid-name
import sys
import argparse
import traceback
import os
import string
from io import StringIO
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.psparser import literal_name
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfinterp import PDFInterpreterError
from pdfminer.pdfdevice import PDFDevice
from pdfminer import utils
from pdfminer.pdffont import PDFUnicodeNotDefined
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams

VERBOSE = False
MISSING_CHAR = None
WITHIN_WORD_MOVE_LIMIT = 0


def verbose(*s):
    if VERBOSE:
        print(*s)


def verbose_operator(*s):
    if VERBOSE:
        print(*s)


class TextState():
    # pylint: disable=too-many-instance-attributes
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
        return ('<TextState: f=%r, fs=%r, c=%r, w=%r, '
                'h=%r, l=%r, mode=%r, rise=%r, '
                'm=%r, lm=%r>' %
                (self.Tf, self.Tfs, self.Tc, self.Tw,
                 self.Th, self.Tl, self.Tmode, self.Trise,
                 self.Tm, self.Tlm))

    def on_BT(self):
        self.Tm = utils.MATRIX_IDENTITY
        self.Tlm = utils.MATRIX_IDENTITY

    def on_ET(self):
        self.Tm = None
        self.Tlm = None


class TextOnlyInterpreter(PDFPageInterpreter):
    # pylint: disable=too-many-public-methods

    def __init__(self, rsrcmgr, device):
        PDFPageInterpreter.__init__(self, rsrcmgr, device)
        self.mpts = TextState()

    # omit these operators
    def do_w(self, linewidth):
        pass

    def do_J(self, linecap):
        pass

    def do_j(self, linejoin):
        pass

    def do_M(self, miterlimit):
        pass

    def do_d(self, dash, phase):
        pass

    def do_ri(self, intent):
        pass

    def do_i(self, flatness):
        pass

    def do_m(self, x, y):
        pass

    def do_l(self, x, y):
        pass

    def do_c(self, x1, y1, x2, y2, x3, y3):  # pylint: disable=too-many-arguments
        pass

    def do_y(self, x1, y1, x3, y3):
        pass

    def do_h(self):
        pass

    def do_re(self, x, y, w, h):
        pass

    def do_S(self):
        pass

    def do_s(self):
        pass

    def do_f(self):
        pass

    def do_f_a(self):
        pass

    def do_B(self):
        pass

    def do_B_a(self):
        pass

    def do_b(self):
        pass

    def do_b_a(self):
        pass

    def do_n(self):
        pass

    def do_W(self):
        pass

    def do_W_a(self):
        pass

    def do_CS(self, name):
        pass

    def do_cs(self, name):
        pass

    def do_G(self, gray):
        pass

    def do_g(self, gray):
        pass

    def do_RG(self, r, g, b):
        pass

    def do_rg(self, r, g, b):
        pass

    def do_K(self, c, m, y, k):
        pass

    def do_k(self, c, m, y, k):
        pass

    def do_SCN(self):
        pass

    def do_scn(self):
        pass

    def so_SC(self):
        pass

    def do_sc(self):
        pass

    def do_sh(self, name):
        pass

    def do_EI(self, obj):
        pass

    def do_Do(self, xobjid):
        pass

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


class TextOnlyDevice(PDFDevice):

    def __init__(self, rsrcmgr):
        PDFDevice.__init__(self, rsrcmgr)
        self.last_state = None
        # contains (font, font_size, string)
        self.blocks = []
        # current block
        # font, font size, glyph y, [chars]
        self.current_block = None

    # at the end of the file, we need to recover last paragraph
    def recover_last_paragraph(self):
        if len(self.current_block[4]) > 0:
            self.blocks.append(self.current_block)

    # pdf spec, page 410
    def new_tx(self, w, Tj, Tfs, Tc, Tw, Th):  # pylint: disable=no-self-use,too-many-arguments
        return ((w - Tj / 1000) * Tfs + Tc + Tw) * Th

    # pdf spec, page 410
    def new_ty(self, w, Tj, Tfs, Tc, Tw):  # pylint: disable=no-self-use,too-many-arguments
        return (w - Tj / 1000) * Tfs + Tc + Tw

    def process_string(self, ts, array):
        verbose('SHOW STRING ts: ', ts)
        verbose('SHOW STRING array: ', array)
        for obj in array:
            verbose("processing obj: ", obj)
            # this comes from TJ, number translates Tm
            if utils.isnumber(obj):
                Tj = obj
                verbose("processing translation: ", Tj)
                # translating Tm, change tx, ty according to direction
                if ts.Tf.is_vertical():
                    tx = 0
                    ty = self.new_ty(0, Tj, ts.Tfs, 0, ts.Tw)
                else:
                    tx = self.new_tx(0, Tj, ts.Tfs, 0, ts.Tw, ts.Th)
                    ty = 0
                # update Tm accordingly
                ts.Tm = utils.translate_matrix(ts.Tm, (tx, ty))
                # there is an heuristic needed here, not sure what
                # if -Tj > ts.Tf.char_width('o'):
                #    self.draw_cid(ts, 0, force_space=True)
            else:
                verbose("processing string")
                for cid in ts.Tf.decode(obj):
                    self.draw_cid(ts, cid)

    def draw_cid(self, ts, cid, force_space=False):
        # pylint: disable=too-many-branches
        verbose("drawing cid: ", cid)
        Trm = utils.mult_matrix((ts.Tfs * ts.Th, 0, 0, ts.Tfs, 0, ts.Trise),
                                ts.Tm)
        if Trm[1] != 0:
            return
        if Trm[2] != 0:
            return
        verbose('Trm', Trm)
        if cid == 32 or force_space:
            Tw = ts.Tw
        else:
            Tw = 0
        try:
            if force_space:
                unichar = ' '
            else:
                unichar = ts.Tf.to_unichr(cid)
        except PDFUnicodeNotDefined:
            if MISSING_CHAR:
                unichar = MISSING_CHAR
            else:
                raise
        (gx, gy) = utils.apply_matrix_pt(Trm, (0, 0))
        verbose("drawing unichar: '", unichar, "' @", gx, ",", gy)
        tfs = Trm[0]
        if self.current_block is None:
            self.current_block = (ts.Tf, tfs, gx, gy, [unichar])
        elif ((self.current_block[0] == ts.Tf) and
              (self.current_block[1] == tfs)):
            self.current_block[4].append(unichar)
        else:
            self.blocks.append(self.current_block)
            self.current_block = (ts.Tf, tfs, gx, gy, [unichar])
        verbose('current block: ', self.current_block)
        verbose('blocks: ', self.blocks)
        if force_space:
            pass
        else:
            w = ts.Tf.char_width(cid)
            if ts.Tf.is_vertical():
                tx = 0
                ty = self.new_ty(w, 0, ts.Tfs, ts.Tc, Tw)
            else:
                tx = self.new_tx(w, 0, ts.Tfs, ts.Tc, Tw, ts.Th)
                ty = 0
            ts.Tm = utils.translate_matrix(ts.Tm, (tx, ty))


def get_title_from_io(pdf_io):
    # pylint: disable=too-many-locals
    parser = PDFParser(pdf_io)
    # if pdf is protected with a pwd, 2nd param here is password
    doc = PDFDocument(parser)

    # pdf may not allow extraction
    # pylint: disable=no-else-return
    if doc.is_extractable:
        rm = PDFResourceManager()
        dev = TextOnlyDevice(rm)
        interpreter = TextOnlyInterpreter(rm, dev)

        first_page = StringIO()
        converter = TextConverter(rm, first_page, laparams=LAParams())
        page_interpreter = PDFPageInterpreter(rm, converter)

        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)
            page_interpreter.process_page(page)
            break

        converter.close()
        first_page_text = first_page.getvalue()
        first_page.close()
        dev.recover_last_paragraph()
        verbose('all blocks')

        for b in dev.blocks:
            verbose(b)

        # find max font size
        max_tfs = max(dev.blocks, key=lambda x: x[1])[1]
        verbose('max_tfs: ', max_tfs)
        # find max blocks with max font size
        max_blocks = list(filter(lambda x: x[1] == max_tfs, dev.blocks))
        # find the one with the highest y coordinate
        # this is the most close to top
        max_y = max(max_blocks, key=lambda x: x[3])[3]
        verbose('max_y: ', max_y)
        found_blocks = list(filter(lambda x: x[3] == max_y, max_blocks))
        verbose('found blocks')

        for b in found_blocks:
            verbose(b)
        block = found_blocks[0]
        title = ''.join(block[4]).strip()

        # Retrieve missing spaces if needed
        if " " not in title:
            title = retrieve_spaces(first_page_text, title)

        # Remove duplcate spaces if any are present
        if "  " in title:
            title = " ".join(title.split())

        return title
    else:
        return None


def get_title_from_file(pdf_file):
    with open(pdf_file, 'rb') as raw_file:
        return get_title_from_io(raw_file)


def retrieve_spaces(first_page, title_without_space, p=0, t=0, result=""):
    # Correct the space problem
    #  if the document does not use space character between the words
    # Stop condition : all the first page has been explored or
    #  we have explored all the letters of the title

    # pylint: disable=no-else-return
    if (p >= len(first_page) or t >= len(title_without_space)):
        return result

    # Add letter to our result if it corresponds to the title
    elif first_page[p].lower() == title_without_space[t].lower():
        result += first_page[p]
        t += 1

    elif t != 0:
        # Add spaces if there is space or a wordwrap
        if first_page[p] == " " or first_page[p] == "\n":
            result += " "
        # If letter p-1 in page corresponds to letter t-1 in title,
        #  but lette p does not corresponds to letter p,
        # we are not exploring the title in the page
        else:
            t = 0
            result = ""

    return retrieve_spaces(
        first_page, title_without_space, p+1, t, result)


def run():
    try:
        parser = argparse.ArgumentParser(
            prog='pdftitle',
            description='Extracts the title of a PDF article',
            epilog='')
        parser.add_argument('-p', '--pdf',
                            help='pdf file', required=True)
        parser.add_argument('--replace-missing-char',
                            help='replace missing char with the one specified')
        parser.add_argument('-c', '--change-name', action='store_true',
                            help='change the name of the pdf file')
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='enable verbose logging')

        # Parse aguments and set global parameters
        args = parser.parse_args()
        global VERBOSE, MISSING_CHAR  # pylint: disable=W0603
        VERBOSE = args.verbose
        MISSING_CHAR = args.replace_missing_char
        title = get_title_from_file(args.pdf)

        # If no name was found, return a non-zero exit code
        if title is None:
            return 1

        # If the user wants to change the name of the file
        if args.change_name:

            # Change the title to a more pleasant file name
            new_name = title.lower()  # Lower case name
            valid_chars = set(string.ascii_lowercase + string.digits + " ")
            new_name = "".join(c for c in new_name if c in valid_chars)
            new_name = new_name.replace(' ', '_') + ".pdf"

            os.rename(args.pdf, new_name)
            print(new_name)
        else:
            print(title)

        return 0

    except Exception as e:  # pylint: disable=W0612,W0703
        if VERBOSE:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run())
