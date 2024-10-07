
VERBOSE = False

def set_verbose(v:bool) -> None:
    global VERBOSE
    VERBOSE = v

def is_verbose() -> bool:
    global VERBOSE
    return VERBOSE

def verbose(*s):
    global VERBOSE
    if VERBOSE:
        print(*s)

def verbose_operator(*s):
    global VERBOSE
    if VERBOSE:
        print(*s)

from .pdftitle import get_title_from_io, get_title_from_file
from .pdftitle import run
