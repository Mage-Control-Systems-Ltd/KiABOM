Development
===========
Run
----
To continue development, make sure to install the requirements in ``requirements.txt``, preferably in a virtual environment:

.. code-block:: console

    pip install -r src/requirements.txt

If you want to build, test, lint and update documentation - or you want to do some of those things and are fine installing all extra packages - install the extra requirements (defined in ``pyproject.toml``):

.. code-block:: console

    pip install --group dev

Test and lint
--------------
The project uses  `Ruff`_ as the linter and formatter, pytest for testing and coverage, and pyright as the static type checker.

.. _Ruff: https://github.com/astral-sh/ruff

A ``config.yaml`` file with your API keys placed next to ``kiabom.py`` is required to run the tests. In the future there may be changes in the supplier's API data structures or part numbers could mean different things. This will affect the 'expected' results from the testing, and therefore would have to be updated accordingly.

To run the testing and linting, the extra packages required should be installed (not necessary if you have installed the ``dev`` group):

.. code-block:: console

    pip install --group lint
    pip install --group test

All tests can be run from the root folder using:

.. code-block:: console

    python -m pytest

Build
------

You can also manually run the ``build.yml`` workflow on GitHub:
    https://github.com/Mage-Control-Systems-Ltd/KiABOM/actions/workflows/build.yml

To build locally, the extra packages required should be installed (not necessary if you have installed the ``dev`` group):

.. code-block:: console

    pip install --group build

Running ``buildtools/build.py`` from the project root generates ``kiabom.exe`` in ``/dist``.  You can also run pyinstaller to do the same thing:

.. code-block:: console

    pyinstaller src/kiabom.py -F --add-data LICENSE:. --icon images/kiabom-icon.ico

Document
----------

One method to view .rst file previews locally is the Esbonio extension for VSCode. This requires the ``sphinx-build`` package which you can install (not necessary if you have installed the ``dev`` group):

.. code-block:: console

    pip install --group docs

Philosophy
===========
- KiABOM should minimise the effort needed to create a Bill Of Materials in KiCad as much as possible, while also minimising complexity.
- Should always be thought of as a Bill Of Materials generator script written in Python, and not as a Python application.
- Should aim to have as few source files and configuration files as possible, to ensure portability as a BOM script.
- The schematic should always be the source of truth, and it should always base the component information and groups from the schematic using the KiCad netlist reader.
- Very little (if any) formatting should be done of the final output, leaving all formatting for the user to do after generation.
