Installation
============
There are two ways of installing and using KiABOM. One is using the executable (either the provided one or building one) and other is using it through Python. For regular users that aren't familiar with Python it is recommended to use the executable as that is a much less involved process. In this case, if it is preferred to not edit Path variables or move files, the executable path can be used instead of the plain ``kiabom`` invocation, i.e. ``C:\Users\USER\Documents\kiabom.exe``.

See the corresponding :ref:`Executable Installation <exec installation>` and :ref:`Python Installation <python installation>` sections for how to install KiABOM.

.. _exec installation:

Executable Installation
-----------------------
The currently provided executable and install script are for **Windows only** installations. Some instructions for using KiABOM on Linux and macOS are provided but have not been extensively tested yet.

Windows
^^^^^^^
Choose to automatically install KiABOM by running the command below in PowerShell which executes the install script ``kiabom-install.ps1`` or manually install it by moving the appropriate files and setting the environment variables. Once installation is done, make sure to restart any terminal and KiCAD instances so that the new Path environment variables are loaded.

Automatic Installation
......................
1. To automatically install KiABOM, run the command below in PowerShell,

.. code-block:: text

    irm "https://raw.githubusercontent.com/Mage-Control-Systems-Ltd/KiABOM/refs/heads/main/install/kiabom-install.ps1" | iex

The install script downloads and moves the ``kiabom.exe`` and ``config.yml`` files to ``C:\Users\USERNAME\AppData\Local\kiabom`` and then sets the correct environment variable.

2. If any issues with permissions arise, try running the script in a PowerShell with admin rights or execute the command below to make sure the correct permissions are used in the current PowerShell window,

.. code-block:: text

    Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process

Manual Installation
...................
1. First clone the repo, to get the executable, config file, and the Python source files.
2. The ``config.yml`` file contains the configuration for KiCost and the API keys, and it just needs to be next to where you have the executable. This is different from the usual KiCost installation where it is placed in another folder in the user directory.  
3. Copy the repo path or place the executable in any folder and make note of its path.
4. Edit your environment variables by searching ``Edit environment variables for your account`` in the start menu search, and clicking on the first result.
5. Find the Path variable under User and add the path of the folder containing the executable.
6. To test if it was done correctly, you may open a terminal window and type the command ``kiabom``, and you should be given the usage of the command, along with some nice ASCII art.

Linux
^^^^^
1. It is recommended that you create a Python virtual environment, although you could install to your system's Python and change the following steps accordingly. After creating and activating a Python virtual environment (See Python Packaging User Guide `here`_ for details on how to do that). Navigate to the repo location and go to the ``src/`` directory, and execute the following command to install KiABOM dependencies,

.. code-block:: text

   pip install -r requirements.txt

2. Install `pyinstaller` (on a virtual environment) and execute the following command in the repo `src/` directory to create the executable,
   
.. code-block:: text

    pyinstaller .\kiabom.py -F --add-data ../LICENSE:. --icon ..\images\kiabom-icon.ico

3. Place this executable somewhere where your system can find it so that it is accessible in every directory.

4. Place your `config.yml` next to the executable.

macOS
^^^^^
KiABOM has not been tested on macOS but it believed that the Linux instructions should be very similar and familiar to macOS users.

.. _python installation:

Python Installation
--------------------
If you don't want to use an executable, the sections below describe how it would be used via executing the script with Python. Make sure your `config.yml` file is next to `kiabom.py` if using this method.

In this process it is assumed you have Python 3 and ``pip`` installed. For Linux you also need ``python3-env``. Follow the steps below to do this installation,

Windows
^^^^^^^
1. Clone the repo to a known location.
2. An optional step would be to move or copy ``kiabom.py`` and ``config.yml`` files to ``C:\Users\USERNAME\AppData\Local\Programs\KiCad\9.0\bin\scripting\plugins``, which is where the rest of the shipped generator scripts are.
3. Open the KiCad Command Prompt by searching for it in the start menu.
4. Navigate to the repo location and go to the ``src/`` directory, and execute the command below to install KiABOM dependencies,

.. code-block:: text

   pip install -r requirements.txt

Linux
^^^^^
1. Clone the repo to a known location.
2. An optional step would be to move or copy ``kiabom.py`` and ``config.yml`` files to ``/usr/share/kicad/plugins/``, which is where the rest of the shipped generator scripts are.
3. It is recommended that you create a Python virtual environment, although you could install to your system's Python and change the following steps accordingly. After creating and activating a Python virtual environment (See Python Packaging User Guide `here`_ for details on how to do that). Navigate to the repo location and go to the ``src/`` directory, and execute the command below to install the dependencies,

.. code-block:: text

   pip install -r requirements.txt

.. _here: https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/

4. If it fails on `wxPython` you may need an external dependency, so install this below, 

.. code-block:: text

    sudo apt-get install libwebkit2gtk-4.1-dev

macOS
^^^^^
KiABOM has not been tested on macOS but it believed that the Linux instructions should be very similar and familiar to macOS users.

