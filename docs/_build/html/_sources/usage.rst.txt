Usage
=====
KiABOM detects the use of an 'MPN' field in the schematic symbols. The field name is **very specific** and **case sensitive**. It also ignores searching for part numbers with the values 'Generic', 'TBD', and 'Manufacturer's Stock' in the MPN field. Therefore, to use KiABOM, create an MPN field in each symbol and add the MPN in that field description.

You can use the generator either through the terminal or through KiCad itself. See the relevant sections below for more information and the :ref:`Example Uses <example_uses>` section for some example command options. Supports all modern KiCad versions using Python v3.9+.

Using Through a Terminal
-------------------------
KiABOM can be treated (depending on your installation) as an executable application or a Python script. In both cases options would be passed to it the same way. See the :ref:`Options <options>` section for the list of options and example commands you can use with the tool.

Using Through KiCad
---------------------
There are three ways of using KiABOM through KiCad. One is via the Legacy BOM generator menu, the second one is the netlist exporter, and the third one is with a jobset file. All methods use the Generator command line format as specified in the `KiCad documentation`_. The options used with each method also get saved by KiCad, so you only need to set your configuration once.

.. _KiCad Documentation: https://docs.kicad.org/9.0/en/eeschema/eeschema.html#generator-command-line-format

.. _commands:

Depending on how KiABOM was installed, you may want to use different commands. If using the executable you would use,

.. code-block:: text

    kiabom "%I" "%B".csv [options]

If using a Python installation you would use,

.. code-block:: text

    python path/to/kiabom.py "%I" "%B".csv [options]

And if using a Python virtual environment you would use,

.. code-block:: text

    path/to/python/venv/bin/python /path/to/kiabom.py "%I" "%B".csv [options]

These commands use the current schematic as input to KiABOM and the project name as the CSV name. The `.csv` extension can be changed to `.html` or `.txt` and the output format will be detected and changed by the generator.

Via Legacy BOM Generator
^^^^^^^^^^^^^^^^^^^^^^^^^
1. In any schematic go to `Tools -> Generate Legacy Bill of Materials...` and click the `+` sign under the 'BOM generator scripts'.

2. Find either the KiABOM executable or Python file, select it, and add an appropriate generator name.

3. Depending on your installation the command in the text box will change. See the  :ref:`commands <commands>` listed above for which commands to use. 

4. Clicking `Generate` should then output the auto-generated BOM in the project root directory.

This method is the recommended method as you can see the output of KiABOM in the dialogue box if anything fails.

Via Netlist Exporter
^^^^^^^^^^^^^^^^^^^^^
1. First open the schematic editor in any project and go to `File -> Export -> Netlist...`.

2. Click Add Exporter, add the title KiABOM and depending on your installation the command in the text box will change. See the  :ref:`commands <commands>` listed above for which commands to use. 

3. Clicking `Export Netlist` should then output the auto-generated BOM in the project root directory.

This method is only listed to show that it is possible and it is definitely viable even if it's not the recommended way. The only quirks with this method is that there is no feedback to the user of what happened, and it is done through the Netlist generator.

Via a Jobsets File
^^^^^^^^^^^^^^^^^^^^^
1. To use KiABOM with a jobsets file, the schematic XML must also be generated. To accomplish this, in a jobsets file create a ``Special: Execute Command`` job type and in the ``Command:`` text box, enter the following to generate the schematic XML file,

.. code-block:: text

    kicad-cli sch export netlist --format kicadxml "${PROJECTNAME}.kicad_sch"

2. Then create another job of the same type and input your KiABOM command with your options, as given in the previous two sections. Depending on your installation the command in the text box will change. See the  :ref:`commands <commands>` listed above for which commands to use. 

**Note:** Due to jobsets not using format specifiers, instead of ``%I`` and ``%B`` you would use ``${PROJECTNAME}`` as used in step 1 above.

3. Make sure to save this jobsets file.

Using With Supplier BOM Tools
--------------------------------
Some suppliers offer BOM tools that assist with ordering parts if you already have the MPNs or the Supplier Order Codes. Using KiABOM's CSV output format, the BOM can be uploaded to these tools, and by specifying the correct column types, the parts can be automatically detected and then ordered. See below for example instructions for how to do that with `Mouser's BOM Tool`_. `DigiKey myLists`_ is their version of a BOM tool and has a very similar process.  

.. _Mouser's BOM Tool: https://www.mouser.co.uk/bom/
.. _DigiKey myLists: https://www.digikey.co.uk/en/mylists/

Go to the Mouser BOM tool and upload your BOM CSV file. In the next page you will set the column types. Assuming you are using the `default` column preset, set the `Quantity` column as `Quantity 1`, `Description` as `Description`, `Manufacturer` as `Mfr Name`, `MPN` as `Mfr Part Number`, and the `Order Code` as the `Mouser Part Number`. In the next page set the appropriate settings and once done proceed to the next page. From here you can add the parts listed to your basket and submit an order. Multiples of the same BOM can be added to basket for multiple boards using the same BOM for a single board.

Some tips for this process is that the ``--no-headers`` column might need to be used to get rid of the column headers before inputting to a BOM tool. Also using ``--remove-ignore-mpn-parts`` will remove parts with the ignore MPN values from the BOM, thus saving you time removing these from the result list.

.. _advanced customisations:

Advanced Customisations
-------------------------
KiABOM is written such that it is as portable and as easy to understand as possible. For this reason, advanced users are encouraged to edit the source code for having their custom column and group presets. After modifying the source `pyinstaller` can then be used to generate an executable if desired by doing,

.. code-block:: text

    pyinstaller .\kiabom.py -F --add-data ../LICENSE:. --icon ..\images\kiabom-icon.ico

Adding User Custom Presets
^^^^^^^^^^^^^^^^^^^^^^^^^^
To add custom column presets add a dictionary entry to the ``column_preset_dict`` defined after the import statements. Any of the listed supported column values (shown by using the ``--list-supported-columns`` option) can be entered and then your preset can then be used by using the ``--column-preset PRESET`` option.

For custom grouping presets it is the same process but by using the ``group_preset_dict`` and by specifying yourcustom preset with ``--group-preset PRESET``. A limitation placed for the group presets is that they should contain at least the ``Value`` and ``Footprint`` group values. This is in place to promote a good standard of BOM generation.

Both of these preset groups can be used together by specifying ``--preset PRESET`` which uses ``preset_dict`` to specify both the group and column presets. The presets in this variable are in a ``COLUMNS PRESET, GROUP PRESET`` format. See below for an example on how to use these variables for customisation (dots imply ommission of the other entries),

.. code-block:: python
   
    column_preset_dict = {
        .
        .
        .
        "custom-columns": [
            "Value",
            "Footprint",
            "MPN",
            "Custom Field",
        ],
    }

    group_preset_dict = {
        .
        .
        .
        "custom-group": [
            "Value",
            "Footprint",
            "Custom Field",
        ],
    }

    preset_dict = {
        .
        .
        .
        "custom": [
            "custom-columns",
            "custom-groups",
        ],
    }

Then your custom preset can be used with,

.. code-block:: text

    kiabom input_xml output.csv --preset custom

.. _options:

Options
------------
The ``--help`` page for KiABOM is shown below along with some examples,

.. code-block:: text

    usage: kiabom.py input_xml output_file [options]

    Automatic BOM tool for KiCAD.

    positional arguments:
      input_xml             input the path to the XML file generated from the KiCAD schematic.
      output_file           name of the output CSV or HTML file. It will be outputed in the same directory where the script is run from.
    options:
      -h, --help            show this help message and exit
      --version             output the KiABOM version.
      --info                append to the output some general info about the generated BOM like, board quantity, schematic name, component count, date, and generator used.
      --no-headers          don't output BOM column headers.
      -k, --no-kicost       disable the KiCost integration.
      --preset PRESET       specify both the columns and group presets at the same time with this option. Both '--columns-preset' and '--group-preset' overwrite this option.
      --columns-preset COLUMNS_PRESET
                            set a BOM preset for what part data should be outputed. Overwrites '--columns' if it comes after. Use '--append-columns' to append columns to a preset. Choose between 'Default', 'Minimal', 'No-KiCost', and 'Mage'.
      --group-preset GROUP_PRESET
                            choose a group preset. Available ones are 'Default', 'Minimal', and 'Mage'. Append to a preset with '--append-groups'.
      -g, --group-by GROUP_BY
                            choose what symbol fields to group by, Grouping by 'Value' and 'Footprint' is mandatory. Choose up to 5 additional fields to group by. Use values separated by commas and place values in quotes in they contain spaces
      -c, --columns COLUMNS
                            set the columns to be outputed. Use values separated by commas and place values in quotes in they contain spaces. Overwrites '--preset' if it comes after. Use '--    append-columns' to append columns to a preset and `--list-supported-columns' to list valid column values.
      -a, --append-columns APPEND_COLUMNS
                            append columns to the selected preset. Use values separated by commas and place values in quotes in they contain spaces.
      --append-groups APPEND_GROUPS
                            append to a group preset.
      --ignore-mpns IGNORE_MPNS
                            add more MPN field values to ignore. This option appends the default option of 'Generic','TBD','Manufacturer's Stock', and '' (blank). Use values separated by commas and place values in quotes in they contain spaces.
      -p, --primary-supplier PRIMARY_SUPPLIER
                            select primary supplier from supplier list. View by executing KiABOM with '--list-suppliers' option.
      -s, --secondary-supplier SECONDARY_SUPPLIER
                            select secondary supplier. View by executing KiABOM with '--list-suppliers' option.
      -d, --download-datasheets
                            optionally donwload the datasheets for the parts with valid URLs in a 'Datasheet' field. Files get downloaded to a 'datasheets' folder in the current working directory.
      -u, --primary-only    only use the primary supplier.
      -q, --quiet           silence warnings
      --kefbom, --keep-exclude-from-bom
                            include the components with the 'Exclude from BOM' property set.
      --kefboard, --keep-exclude-from-board
                            include the components with the 'Exclude from Board' property set.
      -b, --board-quantity BOARD_QUANTITY
                            select board quantity, default is 1.
      --sum                 add a summation of the total price to the end of the table.
      --currency CURRENCY   select the currency, currently supports 'GBP', 'EUR', and 'USD' options.
      --remove-ignore-mpn-parts
                            remove parts from the BOM that contain the ignore MPN values. This options was implemented specifically for supplier BOM tools.
      --list-suppliers      list supported suppliers.
      --list-presets        list built-in presets.
      --list-column-presets
                            list built-in column presets.
      --list-group-presets  list built-in group presets.
      --list-supported-columns
                            list supported column values. Any symbol field can also be a column value.

.. _example_uses:

Example Uses
^^^^^^^^^^^^
The examples listed here will assume the executable is installed on your system but they could easily be replaced with ``python kiabom.py input_xml output_file [options]``.

Default behaviour for the tool is to generate a CSV in the default column and grouping presets. The auto-generated name of the output is 'kiabom-output-HHMMSSddmmyy.csv' which also contains the date and time of generation. The output will contain headers, will be for 1 board of your schematic, use GBP as the currency, and will retrieve the parts data from the suppliers.

.. code-block:: text

    kiabom input_xml

You can fully customise the outputted columns based on the list shown from the ``--list-supported-columns`` option. For example you can create a BOM with no headers, in HTML format, without parts data, that only has the Designator, DNP, Unit/Reel Price, Footprint, and Value,

.. code-block:: text

    kiabom input_xml output.html --no-headers --columns "Designator,DNP,Unit/Reel Price,Footprint,Value" --no-kicost

Adding a symbol field to the BOM can be done by using the appropriate preset and appending columns to that. Grouping can also be done on that field. You can even only output one supplier instead of two,

.. code-block:: text

    kiabom input_xml output.csv --append-columns Rating --append-groups Rating --primary-only

More information can be outputted than just the parts data like generator info and board quantity by specifying ``--info`` and to get a total price sum by using ``--sum``.

.. code-block:: text

    kiabom input_xml output.csv --sum --info

Datasheets can be downloaded by specifying ``--download-datasheets``, which downloads the files located at the links in the 'Datasheet' symbol field in a 'datasheets' folder in the current directory. The symbols with the 'Exclude From BOM' and 'Exclude From Board' properties can also be used in the BOM with ``--kefbom`` and ``--kefboard``. 

.. code-block:: text

    kiabom input_xml output.csv --download-datasheets --kefbom --kefboard

Currently only two suppliers are supported (Mouser and DigiKey), but in the future the suppliers will be specified with the appropriate options.

Presets can be used to simplify the columns and groupings used in the BOM. For example to output a BOM for JLCPCB, you would execute,

.. code-block:: text

    kiabom input_xml output.csv --preset jlcpcb

which is the same as,

.. code-block:: text

    kiabom input_xml output.csv --columns-preset jlcpcb --group-preset jlcpcb

Using the command above you can mix and match columns and group presets,

.. code-block:: text

    kiabom input_xml output.csv --columns-preset default --group-preset minimal

Contributions are welcome for any presets or columns you would like the generator to support!

Lastly, editing the generator file is encouraged to create your own presets. See the  :ref:`Advanced Customisations <advanced customisations>` section for how to customise KiABOM's source code to get more out of the generator. 
