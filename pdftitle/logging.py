"""logging support."""


class Logger:
    """Logger effectively a singleton but not enforced"""

    def __init__(self):
        self._verbose = False

    def set_verbose(self, verbose_mode: bool) -> None:
        """set verbose mode"""
        self._verbose = verbose_mode

    def is_verbose(self) -> bool:
        """return verbose mode"""
        return self._verbose

    def verbose(self, *args):
        """print in verbose mode, ignore otherwise"""
        if self._verbose:
            print(*args)

    def verbose_operator(self, *args):
        """print in verbose mode, ignore otherwise, used in PDF operators"""
        if self._verbose:
            print(*args)


logger = Logger()


def verbose(*args):
    """print if verbose"""
    logger.verbose(args)


def verbose_operator(*args):
    """print if verbose"""
    logger.verbose_operator(args)
