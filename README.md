# KiABOM: KiCad Automatic BOM Generation

![logo](images/kiabom-logo.svg)

See documentation at https://mage-control-systems-ltd.github.io/KiABOM/.

## Features
- 🧘‍♂️ Simple, portable, unformatted BOM generation.
- 🛠 Retrieves parts data from distributors (Uses parts of [KiCost](https://github.com/hildogjr/KiCost)).
- 📑 Supports CSV, HTML, and TXT outputs.
- 🧹 Uses the ``kicad_netlist_reader`` module, which the BOM generator scripts that ship with KiCad use, and does not do its own XML parsing.
- 🧠 Handles schematic property fields like 'DNP', 'Exclude from Board', and 'Exclude from BOM', as they appear on the schematic.
- 🚀 Built-in skipping of specific MPN values for faster API requests.
- 🖥 Encourages customisation of the generator script.

## Licenses
KiABOM is licensed under the GNU General Public License v3.0 (GPLv3). This project includes and depends on the [kicad_netlist_reader](https://pypi.org/project/kicad-netlist-reader/) module, which is also licensed under the GPLv3. As a result, the KiABOM project as a whole is distributed under the terms of the GPLv3. Additionally, KiABOM incorporates components that are licensed under the MIT License. These MIT-licensed modules remain under their original license terms and are compatible with the GPLv3. For full licensing details, refer to the LICENSE file and visit https://www.gnu.org/licenses/gpl-3.0.html.
