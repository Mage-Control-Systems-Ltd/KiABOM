API
===
KiABOM utilises API requests to retrieve part data from suppliers, and saves the parsed data in the cache for the specified duration. The KiCad netlist reader module is used to read the schematic, and the MPN field value is used for the requests using the supplier APIs. The data from both primary and secondary suppliers is the combined into a single object which is then used to generate the BOM.

Summary
------------
.. currentmodule:: kiabom

.. rubric:: Functions

.. autosummary::

        get_footprint_name
        get_bom_row
        html_get_td_string
        html_get_table
        html_output_general_info
        writerow
        csv_write_bom
        csv_output_general_info
        write_to_file
        get_equ
        open_output_file
        print_title_screen
        get_columns
        has_internet
        download_datasheets
        check_args
        set_format_from_output_file_extension
        read_config
        main

.. rubric:: Classes

.. autosummary::

        KiCadNetlist
        SupplierAPI
        MouserAPI
        DigiKeyAPI
        PartsSearch
        CurrencyConverter
        BomData

Definitions
-----------
Definitions for the above summary tables.

Functions
`````````````
.. autofunction:: get_footprint_name
.. autofunction:: get_bom_row
.. autofunction:: html_get_td_string
.. autofunction:: html_get_table
.. autofunction:: html_output_general_info
.. autofunction:: writerow
.. autofunction:: csv_write_bom
.. autofunction:: csv_output_general_info
.. autofunction:: write_to_file
.. autofunction:: get_equ
.. autofunction:: open_output_file
.. autofunction:: print_title_screen
.. autofunction:: get_columns
.. autofunction:: has_internet
.. autofunction:: download_datasheets
.. autofunction:: check_args
.. autofunction:: set_format_from_output_file_extension
.. autofunction:: read_config
.. autofunction:: main

Classes
`````````````
.. autoclass:: KiCadNetlist
    :members:

.. autoclass:: SupplierAPI
    :members:

.. autoclass:: MouserAPI
    :members:

.. autoclass:: DigiKeyAPI
    :members:

.. autoclass:: PartsSearch
    :members:

.. autoclass:: CurrencyConverter
    :members:

.. autoclass:: BomData
    :members:

