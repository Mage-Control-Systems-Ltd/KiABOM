KiABOM documentation
====================

.. raw:: html 
   :file: ../images/kiabom-logo.svg

KiABOM is an automatic Bill Of Materials (BOM) generator script used to extract component information from a KiCad schematic, and use that information with supplier APIs to get component details like the price, manufacturer, order-code, stock, and more. Currently supported suppliers are Mouser and Digikey.

Features
-----------------------
- 🧘‍♂️ Small, simple, portable, and unformatted BOM generation for KiCad.
- 🖥 Command-line interface. See the available :ref:`Options <options>` and :ref:`Example Uses <example_uses>`.
- 🛠 Retrieves parts data from major distributors in the specified currency.
- 💰 Uses caching for parts data and currency rates.
- 📑 Supports multiple output formats: CSV, HTML, TXT, and XLSX.
- 🧹 Uses KiCad’s provided ``kicad_netlist_reader`` module.
- 🧠 Understands schematic property fields like *DNP*, *Exclude from Board*, and *Exclude from BOM*.
- 🚀 Skips specific MPN values for faster API requests.
- 👩🏼‍💻 Encourages customization of the generator script source code for flexible workflows through presets.
- 🖱️ Useable through KiCad's own user interface.
- 📈 Designed to be used with supplier BOM tools.

Table of Contents
-----------------------
.. toctree::
   installation
   usage
   comparisons
   development
   api
   :maxdepth: 3

KiABOM is licensed under the GNU General Public License v3.0 (GPLv3). This project includes and depends on the `kicad_netlist_reader`_ module, which is also licensed under the GPLv3. As a result, the KiABOM project as a whole is distributed under the terms of the GPLv3. Additionally, KiABOM incorporates components that are licensed under the MIT License. These MIT-licensed modules remain under their original license terms and are compatible with the GPLv3. For full licensing details, refer to the LICENSE file and visit https://www.gnu.org/licenses/gpl-3.0.html

.. _kicad_netlist_reader: https://pypi.org/project/kicad-netlist-reader/
