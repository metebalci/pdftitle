# Development

These are some development specific notes for particular releases. They are both for the developers of pdftitle or -although not intended- integrators of pdftitle as a library to other projects.

## v0.14

- build system is changed from setup.py to pyproject.toml, build system is still setuptools.

## v0.13

- `get_title_from_doc` method can be used with PDFDocument objects
- `GetTitleParameters` class is added to not change the signature of `get_title_from_...` methods everytime a new option is added.
- new use_metadata parameters are added.
- `metadata.py` containing title extraction methods from the metadata is added.

## v0.12

- `pdftitle.py` is moved from the root folder of the project to `pdftitle` directory
- some functionality in `pdftitle.py` are moved into separate files (`device.py`, `interpreter.py`)
- custom logging functionality is removed and standard logging is implemented. the logging config is initialized in `run`, thus if `get_title_from_{file,io}` is used, the logging config should be explicitly initalized beforehand.
- pdftitle specific exceptions are moved and raised as PDFTitleException (it was Exception before)
- global variables are removed, thus the signature of `get_title_from_file` and `get_title_from_io` functions are changed to include the parameters (fixes #33)
- `get_title_from_io` method is splitted into multiple methods (one method for each algorithm etc.), but these are not supposed to be used publicly (all are `__` prefixed)
- `get_title_from_io` and `get_title_from_file` are also imported in `__init__.py`
- running pdftitle command only handles PDFTitleException gracefully (prints stack trace and exits with non-zero error code). it was handling Exception gracefully before.
- type hints are added for public methods
- most if not all string formatting is converted to f-strings 
- title case, ligature conversion and changing file name are not performed in `get_title_from_{file, io}` methods. `title.title()`, `pdftitle.convert_ligatures(title)` and `pdftitle.change_file_name(pdf_file, new_name)` methods should be called explicitly afterwards.
