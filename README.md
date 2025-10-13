# KiABOM: KiCad Automatic BOM Generation

![logo](images/kiabom-logo.svg)

See documentation at https://mage-control-systems-ltd.github.io/KiABOM/.

## Features
- 🧘‍♂️ Simple, portable, unformatted BOM generation.
- 🖥 Command-line interface. See the available [Options](https://mage-control-systems-ltd.github.io/KiABOM/usage.html#options) and [Example Uses](https://mage-control-systems-ltd.github.io/KiABOM/usage.html#example-uses).
- 🛠 Retrieves parts data from major distributors (leverages [KiCost](https://github.com/hildogjr/KiCost) components).
- 📑 Supports multiple output formats: CSV, HTML, and TXT.
- 🧹 Uses KiCad’s official kicad_netlist_reader module — no custom XML parsing needed.
- 🧠 Understands schematic property fields like *DNP*, *Exclude from Board*, and *Exclude from BOM*.
- 🚀 Skips specific MPN values for faster API requests.
- 👩🏼‍💻 Encourages customization of the generator script source code for flexible workflows.

## Licenses
KiABOM is licensed under the GNU General Public License v3.0 (GPLv3). This project includes and depends on the [kicad_netlist_reader](https://pypi.org/project/kicad-netlist-reader/) module, which is also licensed under the GPLv3. As a result, the KiABOM project as a whole is distributed under the terms of the GPLv3. Additionally, KiABOM incorporates components that are licensed under the MIT License. These MIT-licensed modules remain under their original license terms and are compatible with the GPLv3. For full licensing details, refer to the LICENSE file and visit https://www.gnu.org/licenses/gpl-3.0.html.
