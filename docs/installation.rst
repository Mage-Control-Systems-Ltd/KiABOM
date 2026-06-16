Installation
============
KiABOM can be used as a standalone Python script, or as an executable by using ``pyinstaller`` to build it. The installation instructions below essentially describe setting up these two options so that they can be used from the command line or through KiCad itself. If you already know how to accomplish this then there is nothing more to the installation section other than how to :ref:`Setup APIs <setup apis>`.

For users that aren't familiar with Python it is recommended to use the executable as that is a much less involved process. An executable is provided for Windows users as are instructions for how to build one for Linux and macOS.

See the corresponding :ref:`Executable Installation <exec installation>` and :ref:`Python Installation <python installation>` sections for how to install KiABOM. Make sure you also :ref:`Setup APIs <setup apis>` with your API keys. 

.. _exec installation:

Executable Installation
-----------------------
The currently provided executable is Windows only. Instructions for building KiABOM on Linux and macOS are provided.

Windows
^^^^^^^
Installing the executable for Windows involves placing it in a known location and adding it to the user Path environment variable. Once installation is done, make sure to restart any terminal and KiCAD instances so that the new Path environment variables are loaded.

1. Download the executable from the releases page or build one yourself.
2. Place the executable in a known location.
3. Edit your environment variables by searching ``Edit environment variables for your account`` in the start menu search, and clicking on the first result.
4. Find the Path variable under User and add the path of the folder containing the KiABOM executable.
5. To test if it was done correctly, you may open a terminal window and type the command ``kiabom --version``, and you should be given the usage of the command, along with some nice ASCII art.
6. Now you're ready to :ref:`Setup APIs <setup apis>`.

Linux
^^^^^
Installing the executable on Linux involves building it yourself using ``pyinstaller``.

1. Create a Python virtual environment (See Python Packaging User Guide `here`_ for details on how to do that).
2. Clone the repo, navigate to the project root directory and install the dependencies in the virtual environment with,

.. code-block:: text

   pip install -r src/requirements.txt

3. Also install `pyinstaller` and execute the following to build the executable,
   
.. code-block:: text

    pyinstaller src/kiabom.py -F --add-data LICENSE:. --icon images/kiabom-icon.ico

3. Place this executable somewhere where your system can find it so that it is accessible in every directory.
4. To test if it was done correctly, you may open a terminal window and type the command ``kiabom --version``, and you should be given the usage of the command, along with some nice ASCII art.
5. Now you're ready to :ref:`Setup APIs <setup apis>`.

macOS
^^^^^
KiABOM has not been tested on macOS but it believed that the Linux instructions should be very similar and familiar to macOS users.

.. _python installation:

Python Installation
--------------------
If you would like to call the Python script directly, the the instructions here detail how to do that. In this process it is assumed you have Python 3.11+ and ``pip`` installed.

Windows
^^^^^^^
The process below is for using KiABOM through KiCad via Python. The tool can be treated as a regular Python script which does not require this process.

1. Clone the repo to a known location.
2. Open the KiCad <VERSION> Command Prompt by searching for it in the start menu **OR** if you don't want to use it through KiCad, open any terminal.
3. Navigate to the repo location and install dependecies with,

.. code-block:: text

   pip install -r src/requirements.txt

4. An optional step would be to place ``kiabom.py`` in your KiCad installation's ``scripting/plugins`` folder, which is where the rest of the shipped generator scripts are.
5. Now you're ready to :ref:`Setup APIs <setup apis>`.


Linux
^^^^^
1. Clone the repo to a known location.
2. Navigate to the repo location and install dependecies to a virtual environment (See Python Packaging User Guide `here`_ for details on how to do that) with,

.. code-block:: text

   pip install -r src/requirements.txt

3. An optional step would be to place ``kiabom.py`` and the virtual environment in your KiCad installation's ``scripting/plugins`` folder, which is where the rest of the shipped generator scripts are.
4. Now you're ready to :ref:`Setup APIs <setup apis>`.

.. _here: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

macOS
^^^^^
KiABOM has not been tested on macOS but it believed that the Linux instructions should be very similar and familiar to macOS users.

.. _setup apis:

Setup APIs
-----------------------
To setup the APIs, you can either use the internal variables located at the start of ``kiabom.py`` (only possible when using Python to execute the script), or by setting up a ``config.yaml`` with the template below. This YAML file **must** be next to either the source file or executable, depending on what method you use.

.. code-block:: text

    DigiKey:
        client_id:
        client_secret:
        sandbox: false/true
    Mouser:
        key:

API usage is based on the current state of the supplier APIs in June 2026. To get parts data from Mouser you need to sign up for their `Search API`_. For DigiKey you need to go in their developer portal, create an Organisation, then create a Production app using `ProductInformation V4`_. You may be prompted for a login in some APIs like DigiKey.

.. _Search API: https://www.mouser.co.uk/api-search/
.. _ProductInformation V4: https://developer.digikey.com/products/product-information-v4

