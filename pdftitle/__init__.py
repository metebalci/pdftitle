# SPDX-FileCopyrightText: 2024 Mete Balci
#
# SPDX-License-Identifier: GPL-3.0-or-later

"""pdftitle module level imports"""

from .constants import ALGO_ORIGINAL, ALGO_MAX2, ALGO_ELIOT
from .pdftitle import get_title_from_doc, get_title_from_io, get_title_from_file
from .pdftitle import GetTitleParameters
from .pdftitle import run
