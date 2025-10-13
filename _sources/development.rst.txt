Development
===========
To continue development, make sure to install the requirements in `requirements.txt`,

.. code-block:: text

    pip install -r requirements.txt

and also by using pyintaller (confirmed tested version is v6.12.0) to make it into a single executable using,

.. code-block:: text

    pyinstaller .\kiabom.py -F --add-data ../LICENSE:. --icon ..\images\kiabom-icon.ico

Using `Ruff`_ as the linter and formatter, pytest for testing and coverage, and pyright as the static type checker.

.. _Ruff: https://github.com/astral-sh/ruff

Philosophy
----------
- KiABOM should minimise the effort needed to create a Bill Of Materials in KiCad as much as possible, while also minimising complexity.
- Should always be thought of as a Bill Of Materials generator script written in Python, and not as a Python application.
- Should aim to have as few source files and configuration files as possible, to ensure portability as a BOM script.
- The schematic should always be the source of truth, and it should always base the component information and groups from the schematic using the KiCad netlist reader.
- Very little (if any) formatting should be done of the final output, leaving all formatting for the user to do after generation.

