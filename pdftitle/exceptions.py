"""pdftitle exceptions"""

class PDFTitleException(Exception):
    """base class for all pdftitle exceptions"""
    def __init__(self, message):
        super().__init__(message)
