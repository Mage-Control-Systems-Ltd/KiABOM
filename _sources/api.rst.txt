API
===
KiABOM utilises KiCost to retrieve part data from suppliers, and to use the cache functionalities it provides. The KiCad netlist reader module is used to read the schematic, and the KiCost data is matched to what was read so that it is outputed in the correct order. To retrieve more data, the KiCost query functions are overwritten but made sure to achieve the same functionality for compatibility.

Summary
------------
.. currentmodule:: kiabom

.. rubric:: Functions

.. autosummary::

        check_args
        check_empty_dnp
        digikey_new_query_part_info
        download_datasheets
        fill_primary_list_gaps_with_secondary
        get_columns
        get_equ
        get_footprint_name
        get_html_td_string
        get_return_empty
        get_total_price_sum
        has_internet
        init_kicost
        main
        match_netlist_refs_with_api_refs
        mouser_new_query_part_info
        open_output_file
        output_general_info_csv
        output_general_info_html
        print_title_screen
        refs_sort
        remove_ignore_mpn_parts
        set_format_from_output_file_extension
        set_html_table
        write_parts_to_csv
        write_to_file
        writerow

.. rubric:: Classes

.. autosummary::

        BaseNet
        BaseParts
        BasePartsFileData
        Net
        NetDNP
        Parts
        PartsDNP
        PartsFileData
        PartsFileDataDNP

Definitions
-----------
Definitions for the above summary tables.

Functions
`````````````
.. autofunction:: check_args
.. autofunction:: check_empty_dnp
.. autofunction:: digikey_new_query_part_info
.. autofunction:: download_datasheets
.. autofunction:: fill_primary_list_gaps_with_secondary
.. autofunction:: get_columns
.. autofunction:: get_equ
.. autofunction:: get_footprint_name
.. autofunction:: get_html_td_string
.. autofunction:: get_return_empty
.. autofunction:: get_total_price_sum
.. autofunction:: has_internet
.. autofunction:: init_kicost
.. autofunction:: main
.. autofunction:: match_netlist_refs_with_api_refs
.. autofunction:: mouser_new_query_part_info
.. autofunction:: open_output_file
.. autofunction:: output_general_info_csv
.. autofunction:: output_general_info_html
.. autofunction:: print_title_screen
.. autofunction:: refs_sort
.. autofunction:: remove_ignore_mpn_parts
.. autofunction:: set_format_from_output_file_extension
.. autofunction:: set_html_table
.. autofunction:: write_parts_to_csv
.. autofunction:: write_to_file
.. autofunction:: writerow

Classes
`````````````
.. autoclass:: BaseNet
    :members:

.. autoclass:: BaseParts
    :members:

.. autoclass:: BasePartsFileData
    :members:

.. autoclass:: Net
    :members:

.. autoclass:: NetDNP
    :members:

.. autoclass:: Parts
    :members:

.. autoclass:: PartsDNP
    :members:

.. autoclass:: PartsFileData
    :members:

.. autoclass:: PartsFileDataDNP
    :members:

