from setuptools import setup, find_packages
from codecs import open
from os import path


packagename = "pdftitle"

# consider the path of `setup.py` as root directory:
PROJECTROOT = path.dirname(__file__)
release_path = path.join(PROJECTROOT, "src", packagename, "release.py")
with open(release_path, encoding="utf8") as release_file:
    __version__ = release_file.read().split('__version__ = "', 1)[1].split('"', 1)[0]


with open("requirements.txt") as requirements_file:
    requirements = requirements_file.read()


with open(path.join(PROJECTROOT, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=packagename,
    version=__version__,
    description="pdftitle is a small utility to extract the title from a PDF file.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/metebalci/pdftitle",
    author="Mete Balci",
    author_email="metebalci@gmail.com",
    license="GPLv3",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: Utilities",
        "Programming Language :: Python :: 3.6",
    ],
    keywords="pdf text extract",
    packages=find_packages("src"),
    package_dir={"": "src"},
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "pdftitle=pdftitle:run",
        ],
    },
)
