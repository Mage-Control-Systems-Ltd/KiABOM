KiABOM documentation
====================

.. raw:: html 
   :file: ../images/kiabom-logo.svg

KiABOM is an automatic Bill Of Materials (BOM) generator script used to extract component information from a KiCad schematic, and use that information with `KiCost`_ to get part details from suppliers like the price, manufacturer, order-code, stock, and more. The currently supported suppliers are Mouser and Digikey.

.. _KiCost: https://github.com/hildogjr/KiCost

.. toctree::
   installation
   usage
   api
   comparisons
   development
   :maxdepth: 5
   :caption: Contents:

KiABOM is licensed under the GNU General Public License v3.0 (GPLv3). This project includes and depends on the `kicad_netlist_reader`_ module, which is also licensed under the GPLv3. As a result, the KiABOM project as a whole is distributed under the terms of the GPLv3. Additionally, KiABOM incorporates components that are licensed under the MIT License. These MIT-licensed modules remain under their original license terms and are compatible with the GPLv3. For full licensing details, refer to the LICENSE file and visit https://www.gnu.org/licenses/gpl-3.0.html

.. _kicad_netlist_reader: https://pypi.org/project/kicad-netlist-reader/
