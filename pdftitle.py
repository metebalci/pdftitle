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
ALGO = "original"
ELIOT_TFS = [0]
TITLE_CASE = False
PAGE_NUMBER = 1

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
        if self.current_block is None:
            raise Exception("current block is None, this might be a bug. " +
                            "please report it together with the pdf file")
        if len(self.current_block[4]) > 0:
            self.blocks.append(self.current_block)

    # pdf spec, 5.3.3 text space details
    def new_tx(self, w, Tj, Tfs, Tc, Tw, Th):  # pylint: disable=no-self-use,too-many-arguments
        return ((w - Tj / 1000) * Tfs + Tc + Tw) * Th

    # pdf spec, 5.3.3 text space details
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

    # pylint: disable=too-many-branches
    def draw_cid(self, ts, cid, force_space=False):
        verbose("drawing cid: ", cid)
        # see official PDF Reference 5.3.3 Text Space Details
        Trm = utils.mult_matrix(
            (ts.Tfs * ts.Th,    0,              # ,0
             0,                 ts.Tfs,         # ,0
             0,                 ts.Trise        # ,1
             ),
             ts.Tm)
        verbose('Trm', Trm)
        # note: before v0.10, Trm[1] and Trm[2] is checked to be 0
        # and if it is not, the character omitted (return from func)
        # this is correct if only translation Trm[4,5] and
        # scaling Trm[0,3] exists
        # but theoretically Trm[1,2] can also have values
        if cid == 32 or force_space:
            Tw = ts.Tw
        else:
            Tw = 0
        try:
            if force_space:
                unichar = ' '
            else:
                unichar = ts.Tf.to_unichr(cid)
        except PDFUnicodeNotDefined as unicode_not_defined:
            if MISSING_CHAR:
                unichar = MISSING_CHAR
            else:
                raise Exception("PDF contains a unicode char that does not " +
                                "exist in the font") from unicode_not_defined
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
            # below Tj is sent as zero because it is adjust in the caller
            if ts.Tf.is_vertical():
                tx = 0
                ty = self.new_ty(w, 0, ts.Tfs, ts.Tc, Tw)
            else:
                tx = self.new_tx(w, 0, ts.Tfs, ts.Tc, Tw, ts.Th)
                ty = 0
            ts.Tm = utils.translate_matrix(ts.Tm, (tx, ty))


# pylint: disable=too-many-branches, too-many-locals, too-many-statements
def get_title_from_io(pdf_io):
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

        current_page_number = 0

        for page in PDFPage.create_pages(doc):
            current_page_number = current_page_number + 1
            verbose("page", current_page_number)
            if current_page_number == PAGE_NUMBER:
                verbose("processing page", current_page_number)
                interpreter.process_page(page)
                page_interpreter.process_page(page)
                current_page_number = -1
                break

        if current_page_number == 0:
            raise Exception("file has no pages")

        if current_page_number > 0:
            raise Exception("specified page does not exist")

        converter.close()
        first_page_text = first_page.getvalue()
        first_page.close()
        dev.recover_last_paragraph()
        verbose('all blocks')

        for b in dev.blocks:
            verbose(b)

        # pylint: disable=W0603
        global ALGO, ELIOT_TFS
        verbose('algo: %s' % ALGO)
        if ALGO == "original":
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

        elif ALGO == "max2":
            # find max font size
            all_tfs = sorted(list(map(lambda x: x[1], dev.blocks)), reverse=True)
            max_tfs = all_tfs[0]
            verbose('max_tfs: ', max_tfs)
            selected_blocks = []
            max2_tfs = -1
            for b in dev.blocks:
                if max2_tfs == -1:
                    if b[1] == max_tfs:
                        selected_blocks.append(b)
                    elif len(selected_blocks) > 0: # max is added
                        selected_blocks.append(b)
                        max2_tfs = b[1]
                else:
                    if b[1] == max_tfs or b[1] == max2_tfs:
                        selected_blocks.append(b)
                    else:
                        break

            for b in selected_blocks:
                verbose(b)

            title = []
            for b in selected_blocks:
                title.append(''.join(b[4]))
            title = ''.join(title)

        elif ALGO == 'eliot':
            verbose('eliot-tfs: %s' % ELIOT_TFS)
            # get all font sizes
            all_tfs = sorted(set(map(lambda x: x[1], dev.blocks)), reverse=True)
            verbose('all_tfs: %s' % all_tfs)
            selected_blocks = []
            # pylint: disable=cell-var-from-loop
            for tfs_index in ELIOT_TFS:
                selected_blocks.extend(
                    list(filter(lambda b: b[1] == all_tfs[tfs_index],
                                dev.blocks)))
            # sort the selected blocks, put y min first, then x min if y min is
            # same
            # 1000000 is a magic number here, assuming no x value is greater
            # than that
            selected_blocks = sorted(selected_blocks,
                                     key=lambda b:b[3]*1000000 + b[2])
            for b in selected_blocks:
                verbose(b)
            title = []
            for b in selected_blocks:
                title.append(''.join(b[4]))
            title = ''.join(title)

        else:
            raise Exception("unsupported ALGO")

        verbose('title before space correction: %s' % title)

        # Retrieve missing spaces if needed
        # warning: if you use eliot algorithm with multiple tfs
        # this procedure may not work
        if " " not in title:
            title_with_spaces = retrieve_spaces_opt(first_page_text, title)
            # the procedure above may return empty string
            # in that case, leave the title as it is
            if len(title_with_spaces) > 0:
                title = title_with_spaces

        # Remove duplcate spaces if any are present
        if "  " in title:
            title = " ".join(title.split())

        return title
    else:
        raise Exception("PDF does not allow extraction")


def get_title_from_file(pdf_file):
    with open(pdf_file, 'rb') as raw_file:
        return get_title_from_io(raw_file)


# this procedure is not used anymore
# it is left here at the moment only for reference
def retrieve_spaces(first_page, title_without_space, p=0, t=0, result=""):
    # Correct the space problem
    #  if the document does not use space character between the words
    # Stop condition : all the first page has been explored or
    #  we have explored all the letters of the title

    verbose('p: %s' % p)
    verbose('t: %s' % t)
    verbose('result: %s' % result)

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
        #  but letter p does not corresponds to letter p,
        # we are not exploring the title in the page
        else:
            t = 0
            result = ""

    return retrieve_spaces(first_page, title_without_space, p+1, t, result)


# optimized, recursion removed
def retrieve_spaces_opt(first_page, title_without_space, p=0, t=0, result=""):
    while True:
        verbose('p: %s, t: %s, result: %s' % (p, t, result))
        # Stop condition : all the first page has been explored or
        #  we have explored all the letters of the title

        # pylint: disable=no-else-return
        if (p >= len(first_page) or t >= len(title_without_space)):
            return result

        elif first_page[p].lower() == title_without_space[t].lower():
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


def run():
    try:
        parser = argparse.ArgumentParser(
            prog='pdftitle',
            description='Extracts the title of a PDF article',
            epilog='')
        parser.add_argument('-p', '--pdf',
                            help='pdf file',
                            required=True)
        parser.add_argument('-a', '--algo',
                            help='algorithm to derive title, default is ' +
                            'original that finds the text with largest ' +
                            'font size',
                            required=False,
                            default="original")
        parser.add_argument('--replace-missing-char',
                            help='replace missing char with the one ' +
                            'specified')
        parser.add_argument('-c', '--change-name', action='store_true',
                            help='change the name of the pdf file')
        parser.add_argument('-t', '--title-case', action='store_true',
                            help='modify the case of final title to be ' +
                            'title case')
        parser.add_argument('-v', '--verbose',
                            action='store_true',
                            help='enable verbose logging')
        parser.add_argument('--eliot-tfs',
                            help='the font size list to use for eliot ' +
                            'algorithm, list separated by comma e.g. 0,1,2 ,' +
                            'default 0 (max) only',
                            required=False,
                            default='0')
        parser.add_argument('--page-number',
                            help='the page number (instead of first page) ' +
                            'to extract the title from (starts from 1)',
                            required=False,
                            type=int,
                            default=1)

        # Parse aguments and set global parameters
        args = parser.parse_args()
        # pylint: disable=W0603
        global VERBOSE, MISSING_CHAR, ALGO, ELIOT_TFS, TITLE_CASE, PAGE_NUMBER
        VERBOSE = args.verbose
        verbose(args)
        MISSING_CHAR = args.replace_missing_char
        ALGO = args.algo
        PAGE_NUMBER = args.page_number
        if ALGO == 'eliot':
            ELIOT_TFS = args.eliot_tfs.split(',')
            # convert to list of ints
            ELIOT_TFS = list(map(int, ELIOT_TFS))
        TITLE_CASE = args.title_case
        title = get_title_from_file(args.pdf)

        if TITLE_CASE:
            verbose('before title case: %s' % title)
            title = title.title()

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
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(run())
