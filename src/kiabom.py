# KiABOM, Automatic Bill Of Materials generator for KiCAD.
# Copyright (C) 2025 Mage Control Systems Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
@package
Output: CSV, HTML, and TXT.
Grouped By: Value, Footprint, DNP, MPN, and Rating (Default preset)
Sorted By: Ref

KiABOM, Automatic Bill Of Materials generator for KiCAD.

Command line:
    python "pathToFile/kiabom.py" "%I" "%O.csv" [options]
"""

__version__ = "1.8.0"
__author__ = "Yiannis Michael (ymich9963)"
__license__ = "GNU General Public License v3.0 only"

import csv
import io
import sys
import argparse
import re
import os
import http.client
import ast
from datetime import datetime
from collections import OrderedDict
import colorama
import requests
import kicad_netlist_reader
from kicad_netlist_reader import comp, netlist

from kicost import (
    solve_parts_qtys,
    get_logger,
    init_all_loggers,
    log,
    set_distributors_progress,
    ProgressConsole,
    load_config,
    SEPRTR,
    DistData,
)
from kicost.__main__ import configure_from_environment
from kicost.config import fill_missing_with_defaults
from kicost.distributors import (
    api_digikey,
    api_mouser,
    configure_apis,
    init_distributor_dict,
    get_distributors_iter,
)
from kicost.distributors.api_mouser import (
    MouserPartSearchRequest,
    in_stock_re_1,
    in_stock_re_2,
    get_number,
)
from kicost.edas import get_part_groups
from kicost.edas.tools import group_parts
from kicost.global_vars import PartGroup

MAX_GROUP_FIELDS = 7
QUIET = False

column_preset_dict = {
    "default": [
        "Group ID",
        "Quantity",
        "Schematic Ref",
        "DNP",
        "Description",
        "Datasheet",
        "Footprint",
        "Value",
        "Manufacturer",
        "MPN",
        "Preferred Supplier",
        "Order Code",
        "Alt. Supplier",
        "Alt. Order Code",
        "Unit/Reel Price",
        "Total Price",
    ],
    "minimal": [
        "Group ID",
        "Quantity",
        "Schematic Ref",
        "DNP",
        "Description",
        "Footprint",
        "Value",
        "MPN",
        "Preferred Supplier",
        "Order Code",
        "Unit/Reel Price",
        "Total Price",
    ],
    "no-kicost": [
        "Group ID",
        "Quantity",
        "Schematic Ref",
        "DNP",
        "Description",
        "Footprint",
        "Value",
    ],
    "primary-only": [
        "Group ID",
        "Quantity",
        "Schematic Ref",
        "DNP",
        "Description",
        "Datasheet",
        "Footprint",
        "Value",
        "Manufacturer",
        "MPN",
        "Preferred Supplier",
        "Order Code",
        "Unit/Reel Price",
        "Total Price",
    ],
    "mage": [
        "Schematic Ref",
        "DNP",
        "Description",
        "Footprint",
        "Value",
        "Rating",
        "Manufacturer",
        "MPN",
        "Preferred Supplier",
        "Order Code",
        "Alt. Supplier",
        "Alt. Order Code",
        "Unit/Reel Price",
    ],
    "jlcpcb": [
        "Comment",
        "Designator",
        "Footprint",
    ],
    "custom": [
        "",
    ],
}

group_preset_dict = {
    "default": [
        "Value",
        "Footprint",
        "DNP",
        "MPN",
    ],
    "minimal": [
        "Value",
        "Footprint",
    ],
    "mage": [
        "Value",
        "Footprint",
        "MPN",
        "DNP",
        "Rating",
    ],
    "jlcpcb": [
        "Value",  # same as 'Comment' column
        "Footprint",
    ],
    "custom": [
        "",
    ],
}

# Format is [columns preset, group preset]
preset_dict = {
    "default": [
        "default",
        "default",
    ],
    "minimal": [
        "minimal",
        "minimal",
    ],
    "mage": [
        "mage",
        "mage",
    ],
    "jlcpcb": [
        "jlcpcb",
        "jlcpcb",
    ],
    "custom": [
        "",
    ],
}


class BaseNet:
    """Base Net class where Net and NetDNP inherit their shared members

    :param input_xml: Input XML file name.
    :param net: Netlist reader object.
    :param components: List of components from the schematic.
    :param grouped: List of grouped compoentns.
    :param group_count: Number of groups.
    :param refdes_groups: List of reference designators from the netlist.
    """

    def __init__(self, input_xml: str, excludeBOM: bool, excludeBoard: bool) -> None:
        self.input_xml = input_xml

        # Initialise
        self.net = netlist()

        # Generate a netlist tree from the one provided in the command line option
        try:
            self.net = kicad_netlist_reader.netlist(input_xml)
        except ValueError:
            print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Unable to open XML file. Please check path is correct or that the file exists.",
                file=sys.stderr,
            )
            sys.exit(1)

        # Get the list of components
        self.components = self.get_components(excludeBOM, excludeBoard)

        # Get all of the components in groups of matching parts + values
        self.grouped = self.net.groupComponents(self.components)
        self.group_count = len(self.grouped)

        # Extract the reference designator groups from the netlist
        self.refdes_groups = self.get_refdes_from_net(self.grouped)

    def get_components(self, excludeBOM: bool, excludeBoard: bool):
        """Get the grouped components. Implemented in BaseNet to force implementation in children.

        :param excludeBOM: Boolean value of whether to include symbols with the exclude from BOM property set.
        :param excludeBoard: Boolean value of whether to include symbols with the exclude from Board property set.
        :raises NotImplementedError: Error raised when function not implemented in children.
        """
        raise NotImplementedError("Must implement get_components() in subclass")

    def get_refdes_from_net(self, grouped: list[list[comp]]) -> list[list[str]]:
        """Get reference designators from KiCAD netlist reader

        :param grouped: List of kicad_netlist_reader component groups.
        :return: A list of reference designator groups.
        """
        refs_groups = []
        for group in grouped:
            refs_list = []
            for component in group:
                refs_list.append(component.getRef())
            refs_groups.append(refs_list)
        return refs_groups


class Net(BaseNet):
    """Contains data read by the netlist reader.

    :param dnp: NetDNP object containing information about DNP components.
    """

    def __init__(self, input_xml: str, excludeBOM: bool, excludeBoard: bool) -> None:
        super().__init__(input_xml, excludeBOM, excludeBoard)
        print(
            f"Received {colorama.Fore.LIGHTYELLOW_EX}{len(self.components)}{colorama.Style.RESET_ALL} components from netlist.",
            flush=True,
        )
        print(
            f"Grouped netlist components into {colorama.Fore.LIGHTYELLOW_EX}{self.group_count}{colorama.Style.RESET_ALL} component groups.",
            flush=True,
        )

        self.dnp = NetDNP(input_xml, excludeBOM, excludeBoard)

    def get_components(self, excludeBOM: bool, excludeBoard: bool) -> list[comp]:
        """Get the grouped components

        :param excludeBOM: Boolean value of whether to include symbols with the exclude from BOM property set.
        :param excludeBoard: Boolean value of whether to include symbols with the exclude from Board property set.
        :return: List of grouped kicad_netlist_reader components.
        """
        # Get components without DNP components
        return self.net.getInterestingComponents(
            excludeBOM=excludeBOM, excludeBoard=excludeBoard, DNP=True
        )


class NetDNP(BaseNet):
    """Contains data read by the netlist reader for DNP components."""

    def __init__(self, input_xml: str, excludeBOM: bool, excludeBoard: bool) -> None:
        super().__init__(input_xml, excludeBOM, excludeBoard)
        print(
            f"Received {colorama.Fore.LIGHTYELLOW_EX}{len(self.components)}{colorama.Style.RESET_ALL} DNP components from netlist.",
            flush=True,
        )
        print(
            f"Grouped DNP netlist components into {colorama.Fore.LIGHTYELLOW_EX}{self.group_count}{colorama.Style.RESET_ALL} component groups.",
            flush=True,
        )

    def get_components(self, excludeBOM: bool, excludeBoard: bool) -> list[comp]:
        """Get the grouped components and extract the DNP components.

        :param excludeBOM: Boolean value of whether to include symbols with the exclude from BOM property set.
        :param excludeBoard: Boolean value of whether to include symbols with the exclude from Board property set.
        :return: List of grouped DNP kicad_netlist_reader components.
        """
        # Get DNP components
        return self.extract_dnp(
            self.net.getInterestingComponents(
                excludeBOM=excludeBOM, excludeBoard=excludeBoard, DNP=False
            )
        )

    def extract_dnp(self, component_list: list[comp]) -> list[comp]:
        """Extract the DNP components from a comp list.

        :param component_list: List of components from the kicad_netlist_reader.
        :return: A list of the DNP components.
        """
        dnp_component_list = [comp for comp in component_list if comp.getDNP()]
        # Need to give an empty component in case there are no DNP components in the schematic
        # If we don't do this KiCost duplicates the output.
        if not dnp_component_list:
            empty_net = kicad_netlist_reader.netlist()
            empty_net.addElement("comp")
            empty_net._curr_element.addAttribute("ref", "BOM-EMPTY")
            empty_component_list = empty_net.getInterestingComponents()
            return empty_component_list

        return dnp_component_list


class BaseParts:
    """Base class for the Parts and PartsDNP classes containing KiCost part details as lists."""

    def __init__(
        self,
        supplier: str,
        net_obj: Net | NetDNP,
        return_empty: bool,
        currency: str,
        ignore_mpns: list,
        board_quantity: int,
    ) -> None:
        if return_empty:
            self.stock = [""] * net_obj.group_count
            self.order_codes = [""] * net_obj.group_count
            self.manufacturers = [""] * net_obj.group_count
            self.supplier = [""] * net_obj.group_count
            self.quantity = [""] * net_obj.group_count
            self.price_tiers = [""] * net_obj.group_count
            self.price = [""] * net_obj.group_count
            self.currency = [""] * net_obj.group_count
        else:
            api_parts_list = self.search_parts_kicost(
                net_obj, supplier.lower(), currency, ignore_mpns
            )
            api_part_refs = self.get_refs_from_kicost(api_parts_list)

            self.comp_count = len(api_parts_list)
            self.parts_list = self.match_api_parts_list_with_reader_list(
                api_part_refs, net_obj.refdes_groups, api_parts_list
            )
            self.stock = self.get_stock_from_kicost(self.parts_list, supplier.lower())
            self.order_codes = self.get_order_code_from_kicost(
                self.parts_list, supplier.lower()
            )
            self.manufacturers = self.get_manufacturer_from_kicost(
                self.parts_list, supplier.lower()
            )
            self.supplier = self.get_supplier_list(supplier.lower(), self.order_codes)
            self.quantity = self.get_quantity_from_kicost(
                self.parts_list, board_quantity
            )
            self.price_tiers = self.get_price_tiers_from_kicost(
                self.parts_list, supplier.lower()
            )
            self.price = self.get_price_from_kicost(self.quantity, self.price_tiers)
            self.currency = self.get_currency_symbol_list(
                currency.lower(), self.order_codes
            )

    def search_parts_kicost(
        self, net_obj: Net | NetDNP, supplier: str, currency: str, ignore_mpns: list
    ) -> list[PartGroup]:
        """Search the distributor for the parts given by the input XML file.

        :param net_obj: Net object containing relevant information from the kicad_netlist_reader.
        :param supplier: Supplier text.
        :param currency: Currency code.
        :param ignore_mpns: List of strings to ignore if found in the MPN field.
        :return: Parts data as an OrderedDict.
        """
        # Get groups of identical parts.
        parts = OrderedDict()
        prj_info = []
        components, info = get_part_groups(
            "kicad", net_obj.input_xml, [], [" "], [supplier]
        )

        # Remove components not in the netlist before the API request
        components = self.keep_only_components_in_netlist(
            components, net_obj.refdes_groups
        )

        # Set the MPN of the parts with the ignore_mpns to blank
        components = self.set_blank_val_to_ignore_mpns(components, ignore_mpns)

        parts.update(components)
        info["qty"] = 1
        prj_info.append(info)

        # Group part out of the module to be possible to merge different project lists, ignore some field to merge given in the `group_fields`.
        FIELDS_SPREADSHEET = ["refs", "value", "desc", "footprint", "manf", "manf#"]
        FIELDS_MANFCAT = [d + "#" for d in get_distributors_iter()] + ["manf#"]
        FIELDS_MANFQTY = [d + "#_qty" for d in get_distributors_iter()] + ["manf#_qty"]
        FIELDS_IGNORE = (
            FIELDS_SPREADSHEET + FIELDS_MANFCAT + FIELDS_MANFQTY + ["pricing"]
        )

        group_fields = []
        for _, fields in list(parts.items()):
            for f in fields:
                # Merge all extra fields that read on the files that will not be displayed (Needed to check `user_fields`).
                if f not in FIELDS_IGNORE and SEPRTR not in f:
                    # Not include repetitive field names or fields with the separator `:` defined on `SEPRTR`.
                    group_fields += [f]

        # Always ignore 'desc' ('description') and 'var' ('variant') fields, merging the components in groups.
        group_fields += ["desc", "var"]
        group_fields = set(group_fields)
        parts = group_parts(parts, group_fields, 1)

        # Compute the qtys
        solve_parts_qtys(parts, False, prj_info)

        # Assign the new function and get the distributor pricing/etc for each part.
        if supplier == "mouser":
            api_mouser._query_part_info = mouser_new_query_part_info
            try:
                api_mouser.query_part_info(parts, [supplier], [currency])
            except AttributeError:
                print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Possible issue with your Mouser API keys. Check your config.yaml.",
                    file=sys.stderr,
                )
                sys.exit(1)
        elif supplier == "digikey":
            api_digikey._query_part_info = digikey_new_query_part_info
            try:
                api_digikey.query_part_info(parts, [supplier], [currency])
            except AttributeError:
                print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Possible issue with your DigiKey API keys. Check your config.yaml.",
                    file=sys.stderr,
                )
                sys.exit(1)

        return parts

    def set_blank_val_to_ignore_mpns(
        self, components: OrderedDict, ignore_mpns: list[str]
    ) -> OrderedDict:
        """Set the 'manf#' value in the components dict to blank
        so that the ignore_mpns parts are skipped by the KiCost API.

        :param components: OrderedDict of components and their information.
        :param ignore_mpns: List of the MPN strings to not search for.
        :return: A list with the MPN values that should be ignored set to blank.
        """
        for val in list(components.values()):
            if "manf#" in val:
                if val["manf#"] in ignore_mpns:
                    del val["manf#"]
            else:
                continue

        return components

    def keep_only_components_in_netlist(
        self, components: OrderedDict, net_refs_groups: list[list[str]]
    ) -> OrderedDict:
        """Reads all the components KiCost found from the XML and
        keeps only those that were read initially from net.getInterestingComponents().

        :param components: OrderedDict of components and their information.
        :param net_refs_groups: List of the reference groups from the netlist reader.
        :return: OrderedDict of components and their information but only those that match the ones from the netlist reader.
        """
        # Put all the net refdes in an easy to access list
        refs_list = []
        for refs_group in net_refs_groups:
            for ref in refs_group:
                refs_list.append(ref)

        # Remove all the refdes that are not in the net ref groups
        for key in list(components.keys()):
            if key not in refs_list:
                components.pop(key)

        return components

    def get_refs_from_kicost(self, parts: list[PartGroup]) -> list[list[str]]:
        """Get reference designators from KiCost API.
        Also sorting them so that the output is a bit more similar
        to the netlist reader when debugging.

        :param parts: List of PartGroup objects.
        :return: List of reference groups.
        """
        refs = []
        for p in parts:
            p.refs.sort(key=refs_sort)
            refs.append(p.refs)

        return refs

    # Match the KiCost API result with the KiCAD net list reader
    def match_api_parts_list_with_reader_list(
        self,
        api_refs_groups: list[list[str]],
        net_refs_groups: list[list[str]],
        api_parts_list: list[PartGroup],
    ) -> list[PartGroup]:
        """Match the KiCost API result with the KiCAD net list reader

        :param api_refs_groups: List of the reference designator groups from KiCost.
        :param net_refs_groups: List of the reference designator groups from KiCAD.
        :param api_parts_list: List of the parts returned from KiCost.
        :return: A PartsGroup list where all parts match the KiCAD netlist reader sequence.
        """
        # Find where the KiCost reference designators are compared to the KiCAD netlist reference designators
        matched_index_list = match_netlist_refs_with_api_refs(
            net_refs_groups, api_refs_groups
        )

        matched_part_groups = []
        for index_group in matched_index_list:
            # Check here is due to the case where there are no DNP components and therefore the list is empty.
            if index_group:
                # Get the first index group since for each ref we only care about the groups here
                first_ref_group = index_group[0]

                # In index 2 for every entry is the group position in the API parts list
                matched_api_part_list_ref = first_ref_group[2]

                # Therefore get that index and match it
                matched_part_groups.append(
                    api_parts_list[int(matched_api_part_list_ref)]
                )

        return matched_part_groups

    def get_stock_from_kicost(self, parts: list[PartGroup], supplier: str) -> list[str]:
        """Get the stock from the returned KiCost parts list.

        :param parts: List of parts returned from KiCost.
        :param supplier: Supplier name.
        :return: List of the stock with blanks when none was found.
        """
        stock = []
        for part in parts:
            if part.dd:
                stock.append(str(part.dd[supplier].qty_avail))
            else:
                stock.append("")
        return stock

    def get_order_code_from_kicost(
        self, parts: list[PartGroup], supplier: str
    ) -> list[str]:
        """Get the order code from the returned KiCost parts list.

        :param parts: List of parts returned from KiCost.
        :param supplier: Supplier name.
        :return: List of the order codes with blanks when none was found.
        """
        order_code = []
        for part in parts:
            if part.dd:
                order_code.append(part.dd[supplier].part_num)
            else:
                order_code.append("")
        return order_code

    def get_manufacturer_from_kicost(
        self, parts: list[PartGroup], supplier: str
    ) -> list[str]:
        """Get the manufacturer from the returned KiCost parts list.

        :param parts: List of parts returned from KiCost.
        :param supplier: Supplier name.
        :return: List of the manufacturers with blanks when none was found.
        """
        extra_info = []
        manufacturer = []
        for part in parts:
            if part.dd:
                # dd is a DistData object in global_vars
                extra_info.append(part.dd[supplier].extra_info)
            else:
                extra_info.append({})

        for info in extra_info:
            if supplier == "mouser":
                manufacturer.append(info.get("manufacturer", ""))
            elif supplier == "digikey":
                # KiCost returns a dict in string form for some reason
                manf_dict = info.get("manufacturer", "")
                # Check if the dict string exists
                if manf_dict:
                    # Convert the dict string to an actual dict
                    # Put in try-catch in case literal_eval() fails since
                    # the dict is actually a KiCost class (again)
                    try:
                        manf_dict = ast.literal_eval(str(manf_dict))
                    except Exception:
                        manf_dict = {}
                    manufacturer.append(manf_dict.get("value", ""))
                else:
                    manufacturer.append("")
        return manufacturer

    def get_supplier_list(self, supplier: str, order_codes: list[str]) -> list[str]:
        """Get the supplier list for all parts returned from KiCost.

        :param supplier: Supplier text.
        :param order_codes: List of the order codes.
        :return: List of the suppliers for all the returned parts.
        """
        suppler_list = []
        for order_code in order_codes:
            if order_code != "":
                if supplier == "mouser":
                    suppler_list.append("Mouser")
                elif supplier == "digikey":
                    suppler_list.append("DigiKey")
                else:
                    suppler_list.append("Supplier")
            else:
                suppler_list.append("")

        return suppler_list

    def get_quantity_from_kicost(
        self, parts: list[PartGroup], board_quantity: int
    ) -> list[str]:
        """Get the quantity from the returned KiCost parts.

        :param parts: List of parts returned from KiCost.
        :param board_quantity: Specified board quantity from the options.
        :return: List of all the quantities detected by KiCost.
        """
        qty_list = []
        for part in parts:
            if part.dd:
                if part.qty:
                    qty_list.append(str(int(part.qty) * board_quantity))
                else:
                    qty_list.append("")
            else:
                qty_list.append("")
        return qty_list

    def get_price_tiers_from_kicost(
        self, parts: list[PartGroup], supplier: str
    ) -> list[dict]:
        """Get the price tiers from the returned parts list.

        :param parts: List of parts returned from KiCost.
        :param supplier: Supplier string.
        :return: List of price tiers.
        """
        price_tiers = []
        for part in parts:
            if part.dd:
                price_tiers.append(part.dd[supplier].price_tiers)
            else:
                price_tiers.append({})
        return price_tiers

    def get_price_from_kicost(
        self, quantity: list[str], price_tiers: list[dict]
    ) -> list[str]:
        """Get the price from the price tiers based on the quantity.

        :param quantity: Quantity from the number of parts in the group.
        :param price_tiers: Price tiers returned from the API.
        :return: List of the prices in string format.
        """
        price = []
        price_key = 0
        for pos, price_dict in enumerate(price_tiers):
            if price_dict:
                for key in price_dict:
                    if key < int(quantity[pos]):
                        price_key = key
                    else:
                        price_key = list(price_dict.keys())[0]
                price.append(str(float(price_dict[price_key])))
            else:
                price.append("")
        return price

    def get_currency_symbol_list(
        self, currency: str, order_codes: list[str]
    ) -> list[str]:
        """Get a list with all the currency values for the parts.

        :param currency: Currency string, e.g. GBP, USD, or EUR.
        :param order_codes: Order codes list.
        :return: A list with the currency symbols where a valid order code was found.
        """
        currency_symbol_list = []
        for order_code in order_codes:
            if order_code != "":
                if currency == "gbp":
                    currency_symbol_list.append("£")
                elif currency == "usd":
                    currency_symbol_list.append("$")
                elif currency == "eur":
                    currency_symbol_list.append("€")
                else:
                    currency_symbol_list.append("")
            else:
                currency_symbol_list.append("")

        return currency_symbol_list


# Contains parts data retrieved by KiCost
class Parts(BaseParts):
    """Contains non-DNP parts data retrieved by KiCost for a specific supplier.

    :param dnp: A PartsFileDataDNP object instance.
    """

    def __init__(
        self,
        supplier: str,
        net_obj: Net,
        return_empty: bool,
        currency: str,
        ignore_mpns: list,
        board_quantity: int,
    ) -> None:
        super().__init__(
            supplier, net_obj, return_empty, currency, ignore_mpns, board_quantity
        )
        self.dnp = PartsDNP(
            supplier, net_obj.dnp, return_empty, currency, ignore_mpns, board_quantity
        )

        if not return_empty:
            print(
                f"Searched {supplier}, found {colorama.Fore.LIGHTYELLOW_EX}{self.comp_count + self.dnp.comp_count}{colorama.Style.RESET_ALL} valid parts.",
                flush=True,
            )


class PartsDNP(BaseParts):
    """Contains DNP parts data retrieved by KiCost for a specific supplier"""

    def __init__(
        self,
        supplier: str,
        net_obj: NetDNP,
        return_empty: bool,
        currency: str,
        ignore_mpns: list,
        board_quantity: int,
    ) -> None:
        super().__init__(
            supplier, net_obj, return_empty, currency, ignore_mpns, board_quantity
        )


class BasePartsFileData:
    """Class containing the file data that is common between DNP and non-DNP parts.
    Has data from both primary and secondary suppliers.

    :param manufacturer: Manufacturer list.
    :param primary_order_codes: Primary order codes list.
    :param primary_supplier: Primary supplier list containing the primary supplier string.
    :param secondary_order_codes: Secondary order codes list.
    :param secondary_supplier: Secondary supplier list containing the secondary supplier string.
    :param price: List containing the prices for each part.
    :param currency_symbol: Currency symbol for each part.
    """

    def __init__(
        self, primary_parts_obj: Parts | PartsDNP, secondary_parts_obj: Parts | PartsDNP
    ) -> None:
        self.manufacturer = fill_primary_list_gaps_with_secondary(
            primary_parts_obj.manufacturers, secondary_parts_obj.manufacturers
        )
        self.primary_order_codes = primary_parts_obj.order_codes
        self.primary_supplier = primary_parts_obj.supplier
        self.secondary_order_codes = secondary_parts_obj.order_codes
        self.secondary_supplier = secondary_parts_obj.supplier
        self.price = fill_primary_list_gaps_with_secondary(
            primary_parts_obj.price, secondary_parts_obj.price
        )
        self.currency_symbol = primary_parts_obj.currency

        # If one of the lists above is empty, assume there are no DNP components and return empty lists
        if not self.manufacturer:
            self.manufacturer = [""]
            self.primary_order_codes = [""]
            self.primary_supplier = [""]
            self.secondary_order_codes = [""]
            self.secondary_supplier = [""]
            self.price = [""]
            self.currency_symbol = [""]


def fill_primary_list_gaps_with_secondary(
    primary_list: list[str], secondary_list: list[str]
) -> list[str]:
    """Fills the gaps in the primary list with the data from the secondary list.

    :param primary_list: A list containining blank or filled string data.
    :param secondary_list: A list containining blank or filled string data.
    :return: Primary list with its blanks filled by the secondary list.
    """
    out_list = primary_list
    for pos, _ in enumerate(primary_list):
        if primary_list[pos] == "" and secondary_list[pos] != "":
            out_list[pos] = secondary_list[pos]
    return out_list


class PartsFileData(BasePartsFileData):
    """Contains data of the parts as simple lists for outputting.

    :param dnp: A PartsFileDataDNP object instance.
    """

    def __init__(self, primary_parts_obj: Parts, secondary_parts_obj: Parts) -> None:
        super().__init__(primary_parts_obj, secondary_parts_obj)
        self.dnp = PartsFileDataDNP(primary_parts_obj.dnp, secondary_parts_obj.dnp)


class PartsFileDataDNP(BasePartsFileData):
    """Contains DNP CSV data of the DNP parts"""

    def __init__(
        self, primary_parts_obj: PartsDNP, secondary_parts_obj: PartsDNP
    ) -> None:
        super().__init__(primary_parts_obj, secondary_parts_obj)


def mouser_new_query_part_info(
    parts: OrderedDict, distributors: list[str], currency: list[str]
):
    """Used to override the api_digikey._query_part_info function to return additional part details
    like the manufacturer.

    :param parts: Parts read by KiCost.
    :param distributors: The chosen distributor which in this case will be digikey.
    :param currency: Chosen currency of returned prices.
    """
    DIST_NAME = "mouser"
    if DIST_NAME not in distributors:
        return
    field_cat = DIST_NAME + "#"
    for part in parts:
        partnumber = None
        data = None
        # Get the Mouser P/N for this part
        part_stock = part.fields.get(field_cat)
        if part_stock:
            partnumber = part_stock
            prefix = "mou"
        else:
            # No Mouser P/N, search using the manufacturer code
            partnumber = part.fields.get("manf#")
            prefix = "mpn"
        if partnumber:
            request, loaded = api_mouser.cache.load_results(prefix, partnumber)
            if loaded:
                data = MouserPartSearchRequest.get_clean_response(request)
            else:
                request = MouserPartSearchRequest("partnumber", api_mouser.key)
                if request.part_search(partnumber):
                    data = request.get_clean_response(request.response_parsed)
                    api_mouser.cache.save_results(
                        prefix, partnumber, request.response_parsed
                    )

        if data is None:
            if not QUIET:
                if partnumber == "" or partnumber is None:
                    pass
                else:
                    # breakpoint()
                    print(
                        f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} No information found at Mouser for part(s) '{','.join(part.refs)}' with MPN '{partnumber}'."
                    )
        else:
            if not part.datasheet:
                datasheet = data["DataSheetUrl"]
                if datasheet:
                    part.datasheet = datasheet
            if not part.lifecycle:
                lifecycle = data["LifecycleStatus"]
                if lifecycle:
                    part.lifecycle = lifecycle.lower()
            dd = part.dd.get(DIST_NAME, DistData())
            dd.qty_increment = dd.moq = int(data["Min"])
            dd.url = data["ProductDetailUrl"]
            dd.part_num = data["MouserPartNumber"]
            dd.qty_avail = 0
            availability = data["Availability"]
            dd.qty_avail_comment = availability
            res_stock = in_stock_re_1.match(availability)
            if not res_stock:
                res_stock = in_stock_re_2.match(availability)
            if res_stock:
                dd.qty_avail = int(res_stock.group(1))
            pb = data["PriceBreaks"]
            dd.currency = pb[0]["Currency"] if pb else currency
            dd.price_tiers = {p["Quantity"]: get_number(p["Price"]) for p in pb}
            # Extra information
            if data["Manufacturer"]:
                dd.extra_info["manufacturer"] = data["Manufacturer"]
            part.dd[DIST_NAME] = dd


def digikey_new_query_part_info(
    parts: OrderedDict, distributors: list[str], currency: list[str]
):
    """Used to override the api_digikey._query_part_info function to return additional part details
    like the manufacturer.

    :param parts: Parts read by KiCost.
    :param distributors: The chosen distributor which in this case will be digikey.
    :param currency: Chosen currency of returned prices.
    """
    part_code = ""
    DIST_NAME = "digikey"
    if DIST_NAME not in distributors:
        return
    field_cat = DIST_NAME + "#"

    # This is handled in KiCost in the api_digikey.py configure() function. That function does some other things but this should be ok.
    if api_digikey.version == 3:
        from kicost_digikey_api_v3 import by_digikey_pn, by_manf_pn, by_keyword
    else:
        from kicost_digikey_api_v4 import by_digikey_pn, by_manf_pn, by_keyword

    # Setup progress bar to track progress of server queries.
    for part in parts:
        data = None
        # Get the Digi-Key P/N for this part
        part_stock = part.fields.get(field_cat)
        if part_stock:
            o = by_digikey_pn(part_stock)
            data = o.search()
            if data is None:
                if not QUIET:
                    print(
                        f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} The '{part_stock}' Digi-Key code is not valid."
                    )
                o = by_keyword(part_stock)
                data = o.search()
        else:
            # No Digi-Key P/N, search using the manufacturer code
            part_code = part.fields.get("manf#")
            if part_code:
                o = by_manf_pn(part_code)
                data = o.search()
                if data is None:
                    o = by_keyword(part_code)
                    data = o.search()
        if data is None:
            if not QUIET:
                if part_code == "" or part_code is None:
                    pass
                else:
                    print(
                        f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} No information found at DigiKey for part(s) '{','.join(part.refs)}' with MPN '{part_code}'."
                    )
        else:
            if api_digikey.version == 3:
                # Extract v3 data
                primary_datasheet = data.primary_datasheet
                product_status = data.product_status.lower()
                specs = {
                    sp.parameter.lower(): (sp.parameter, sp.value)
                    for sp in data.parameters
                }
                ro_hs_status = data.ro_hs_status
                minimum_order_quantity = data.minimum_order_quantity
                product_url = data.product_url
                digi_key_part_number = data.digi_key_part_number
                quantity_available = data.quantity_available
                price_tiers = {
                    p.break_quantity: p.unit_price for p in data.standard_pricing
                }
                product_description = data.product_description
                manufacturer = data.manufacturer
            else:
                # Extract v4 data
                p = data.product  # The selected product
                m = p.match  # The selected variant
                primary_datasheet = p.datasheet_url
                product_status = p.product_status.status.lower()
                specs = {
                    sp.parameter_text.lower(): (sp.parameter_text, sp.value_text)
                    for sp in p.parameters
                }
                ro_hs_status = p.classifications.rohs_status
                minimum_order_quantity = m.minimum_order_quantity
                product_url = p.product_url
                digi_key_part_number = m.digi_key_product_number
                quantity_available = m.quantity_availablefor_package_type
                price_tiers = {
                    p.break_quantity: p.unit_price for p in m.standard_pricing
                }
                product_description = p.description.product_description
                manufacturer = p.manufacturer.name

            # Fill internal structure
            part.datasheet = primary_datasheet
            part.lifecycle = product_status
            specs["rohs"] = ("RoHS", ro_hs_status)
            part.update_specs(specs)
            dd = part.dd.get(DIST_NAME, DistData())
            dd.qty_increment = dd.moq = minimum_order_quantity
            dd.url = product_url
            dd.part_num = digi_key_part_number
            dd.qty_avail = quantity_available
            dd.currency = data.search_locale_used.currency
            dd.price_tiers = price_tiers
            dd.extra_info["manufacturer"] = manufacturer
            part.dd[DIST_NAME] = dd
            dd.extra_info["desc"] = product_description


def match_netlist_refs_with_api_refs(
    lst1: list[list[str]], lst2: list[list[str]]
) -> list[list[str]]:
    """Matches the group number and location of a reference in lst1
    to what group and location it is in lst2, and uses counters to store the indexes.
    In this software's case, lst1 = Net list reader reference groups
    and lst2 = API reference groups.

    This function used to be used for extracting from the KiCost result only the
    components present in the net list. Now it is used to sort the KiCost result
    exactly how the net list reader does it so that the results can simply be indexed.

    Format of returned list is [lst1_group_index, lst1_ref_index, lst2_group_index, lst2_ref_index].

    :param lst1: List with nested lists of strings.
    :param lst2: List with nested lists of strings.
    :return: List with nested lists of indexes where lst1 nested items match lst2 nested items. Goupred based on the location in lst1.
    """
    matched_ref_list = []
    grouped_matched_ref_list = []

    # Get all the lst1 items that match in lst2, and store their locations in matched_ref_list
    for lst1_group_counter, lst1_group in enumerate(lst1):
        for lst1_ref_counter, lst1_ref in enumerate(lst1_group):
            for lst2_group_counter, lst2_group in enumerate(lst2):
                for lst2_ref_counter, lst2_ref in enumerate(lst2_group):
                    if lst1_ref == lst2_ref:
                        # ref is the location of the corresponding refdes in both lists
                        ref = [
                            lst1_group_counter,
                            lst1_ref_counter,
                            lst2_group_counter,
                            lst2_ref_counter,
                        ]
                        matched_ref_list.append(ref)

    # Due to how the for-loop is structured, the length of the first list is the length of the desired final list
    matched_num = len(lst1)

    # Initialise a list with empty nested lists to store each group
    for i in range(matched_num):
        grouped_matched_ref_list.append([])

    # Find the where the item was in lst1 and group it with items that also belong in that group
    for i, group in enumerate(grouped_matched_ref_list):
        for ref in matched_ref_list:
            if i == ref[0]:
                group.append(ref)

    return grouped_matched_ref_list


def refs_sort(ref: str) -> list[int]:
    """Used as a sort key in get_refs_from_kicost().

    For example, KiCost sorts a reference like so ['R2', 'R9', 'R13', 'R14', 'R10']
    whereas kicad_netlist_reader sorts it like so ['R2', 'R9', 'R10', 'R13', 'R14'].
    Therefore for optimum matching between the two outputs, they need to be sorted the same
    way.

    :param ref: Reference designator string.
    :return: A list
    """

    return [int(ref_int) for ref_int in re.findall(r"\d+", ref)]


def init_kicost() -> bool:
    """Initialise KiCost by initialising the logger and the APIs.

    :return: True or Fasle (Success or Failure).
    """
    # Set up logging verbosity
    log.set_domain("kicost")
    init_all_loggers(
        log.init(), log.get_logger("kicost.distributors"), log.get_logger("kicost.edas")
    )
    log.set_verbosity(get_logger(), None, True)
    set_distributors_progress(ProgressConsole)

    # Determine if application is a script file or an executable
    application_path = ""
    if getattr(sys, "frozen", False):
        application_path = os.path.dirname(sys.executable)
    elif __file__:
        application_path = os.path.dirname(__file__)

    config_name = "config.yaml"
    config_path = os.path.join(application_path, config_name)

    api_found = False
    api_options = {}
    if os.path.isfile(config_path):
        api_options = load_config(config_path)

        # Check if at least one API key was found
        for api in list(api_options.values()):
            if api:
                api_found = True

    if api_found:
        configure_from_environment(api_options, False)
        fill_missing_with_defaults()
        configure_apis(api_options)
        init_distributor_dict()

    return api_found


def check_empty_dnp(component: comp) -> bool:
    """Fixes issue of outputting an empty DNP component list, which is what happens when
       no DNP components exist in the XML. The empty DNP value is set by extract_dnp().

    :param component: Component to check.
    :return: True or False.
    """
    return bool(component.getRef() == "BOM-EMPTY")


def write_parts_to_csv(
    out,
    board_quantity: int,
    columns: list[str],
    grouped: list[list[comp]],
    output_data: PartsFileData | PartsFileDataDNP,
):
    """Write grouped parts into the opened CSV file

    :param out: A csv.writer object to use for writing to the CSV.
    :type out: csv.writer
    :param board_quantity: Board quantity.
    :param columns: Columns list for what data to output.
    :param grouped: List of lists of components from the kicad_netlist_reader.
    :param output_data: Parts data that will be used to populate the table.
    """
    c = grouped[0][0]  # Initialise with the first component in the first group
    row = []

    # Output component information organized by group, aka as collated:
    for pos, group in enumerate(grouped):
        del row[:]
        refs = ""
        refs_l = []

        # Add the reference of every component in the group and
        # keep a reference to the component so that the other data
        # can be filled in once per group
        for component in group:
            refs_l.append(component.getRef())
            c = component

        refs = ", ".join(refs_l)

        # Check if an empty component was used for the DNP parts
        # which means no DNP components in the XML
        if check_empty_dnp(c):
            return

        quantity = len(group) * board_quantity

        # Add values based on the columns
        for name in columns:
            if name == "Group ID":
                row.append(c.getDNPString() + str(pos + 1))
            elif name == "Quantity":
                row.append(quantity)
            elif name == "Schematic Ref" or name == "Designator":
                row.append(refs)
            elif name == "DNP":
                row.append(c.getDNPString())
            elif name == "Description":
                row.append(c.getField("Description"))
            elif name == "Datasheet":
                row.append(c.getField("Datasheet"))
            elif name == "Footprint":
                row.append(get_footprint_name(c.getFootprint()))
            elif name == "Value" or name == "Comment":
                row.append(c.getValue())
            elif name == "Rating":
                row.append(c.getField("Rating"))
            elif name == "Manufacturer":
                row.append(output_data.manufacturer[pos])
            elif name == "MPN":
                row.append(c.getField("MPN"))
            elif name == "Preferred Supplier":
                row.append(output_data.primary_supplier[pos])
            elif name == "Order Code":
                row.append(output_data.primary_order_codes[pos])
            elif name == "Alt. Supplier":
                row.append(output_data.secondary_supplier[pos])
            elif name == "Alt. Order Code":
                row.append(output_data.secondary_order_codes[pos])
            elif name == "Unit/Reel Price":
                row.append(
                    output_data.currency_symbol[pos] + str(output_data.price[pos])
                )
            elif name == "Total Price":
                if output_data.price[pos] != "":
                    row.append(
                        output_data.currency_symbol[pos]
                        + str(quantity * float(output_data.price[pos]))
                    )
                else:
                    row.append(output_data.price[pos])
                # To output custom fields if they exist in the symbol properties
            elif c.getField(name):
                row.append(c.getField(name))
            else:
                row.append("")

        writerow(out, row)


def get_html_td_string(string: str) -> str:
    """Get a string as a table data cell HTML element.

    :param string: Text to be placed between the <td> and </td>.
    :return: String encloded by <td> and </td>.
    """
    return "<td>" + string + "</td>"


def set_html_table(
    html_text: str,
    board_quantity: int,
    columns: list[str],
    grouped: list[list[comp]],
    output_data: PartsFileData | PartsFileDataDNP,
) -> str:
    """Set the table in the HTML string.

    :param html_text: HTML string.
    :param board_quantity: Board quantity.
    :param columns: Columns list for what data to output.
    :param grouped: List of lists of components from the kicad_netlist_reader.
    :param output_data: Parts data that will be used to populate the table.
    :return: HTML table string containing all the parts data.
    """
    c = grouped[0][0]  # Initialise with the first component in the first group

    # Output all of the component information
    for pos, group in enumerate(grouped):
        refs_l = []
        refs = ""

        # Add the reference of every component in the group and
        # keep a reference to the component so that the other data
        # can be filled in once per group
        for component in group:
            refs_l.append(component.getRef())
            c = component

        refs = ", ".join(refs_l)

        # Check if an empty component was used for the DNP parts
        # which means no DNP components in the XML
        if check_empty_dnp(c):
            break

        quantity = len(group) * board_quantity

        # Add values based on the columns
        row = "\t<tr>"
        for name in columns:
            if name == "Group ID":
                row += get_html_td_string(c.getDNPString() + str(pos + 1))
            elif name == "Quantity":
                row += get_html_td_string(str(quantity))
            elif name == "Schematic Ref" or name == "Designator":
                row += get_html_td_string(refs)
            elif name == "DNP":
                row += get_html_td_string(c.getDNPString())
            elif name == "Description":
                row += get_html_td_string(c.getField("Description"))
            elif name == "Datasheet":
                row += get_html_td_string(c.getField("Datasheet"))
            elif name == "Footprint":
                row += get_html_td_string(get_footprint_name(c.getFootprint()))
            elif name == "Value" or name == "Comment":
                row += get_html_td_string(c.getValue())
            elif name == "Rating":
                row += get_html_td_string(c.getField("Rating"))
            elif name == "Manufacturer":
                row += get_html_td_string(output_data.manufacturer[pos])
            elif name == "MPN":
                row += get_html_td_string(c.getField("MPN"))
            elif name == "Preferred Supplier":
                row += get_html_td_string(output_data.primary_supplier[pos])
            elif name == "Order Code":
                row += get_html_td_string(output_data.primary_order_codes[pos])
            elif name == "Alt. Supplier":
                row += get_html_td_string(output_data.secondary_supplier[pos])
            elif name == "Alt. Order Code":
                row += get_html_td_string(output_data.secondary_order_codes[pos])
            elif name == "Unit/Reel Price":
                row += get_html_td_string(
                    output_data.currency_symbol[pos] + str(output_data.price[pos])
                )
            elif name == "Total Price":
                if output_data.price[pos] != "":
                    row += get_html_td_string(
                        output_data.currency_symbol[pos]
                        + str(quantity * float(output_data.price[pos]))
                    )
                else:
                    row += get_html_td_string(output_data.price[pos])
                # To output custom fields if they exist in the symbol properties
            elif c.getField(name):
                row += get_html_td_string(c.getField(name))
            else:
                row += get_html_td_string("")
        row += "</tr>\n\t\t\t"
        html_text = html_text.replace("<!--TABLEROW-->", row + "<!--TABLEROW-->")

    return html_text


def get_footprint_name(text: str) -> str:
    """Get the footprint name from the Lib:Name string in the footprint symbol field.

    :param text: Footprint field string.
    :return: Footprint name or blank.
    """
    # In the case of no colon in the footprint field for some reason
    try:
        return text.split(":", 1)[1]
    except IndexError:
        return ""


# Global variable to be used in the equ functions
global_group_fields = []


def get_equ(group_fields: str, group_preset: str, append_groups: str):
    """Return the selected equivalence function to be used in grouping

    :param group_fields: String of comma separated group values.
    :param group_preset: Specified group preset.
    :param append_groups: String of comma separated values to append to a preset.
    :return: Equivalence (__equ__) function.
    :rtype: Function returning True or False.
    """
    global global_group_fields

    # Define the equivalence functions to be returned
    def kiabom_equ_dnp(self, other):
        result = False
        if self.getValue() == other.getValue():
            if self.getFootprint() == other.getFootprint():
                if self.getDNP() == other.getDNP():
                    if self.getField(global_group_fields[0]) == other.getField(
                        global_group_fields[0]
                    ):
                        if self.getField(global_group_fields[1]) == other.getField(
                            global_group_fields[1]
                        ):
                            if self.getField(global_group_fields[2]) == other.getField(
                                global_group_fields[2]
                            ):
                                if self.getField(
                                    global_group_fields[3]
                                ) == other.getField(global_group_fields[3]):
                                    result = True
        return result

    def kiabom_equ(self, other):
        result = False
        if self.getValue() == other.getValue():
            if self.getFootprint() == other.getFootprint():
                if self.getField(global_group_fields[0]) == other.getField(
                    global_group_fields[0]
                ):
                    if self.getField(global_group_fields[1]) == other.getField(
                        global_group_fields[1]
                    ):
                        if self.getField(global_group_fields[2]) == other.getField(
                            global_group_fields[2]
                        ):
                            if self.getField(global_group_fields[3]) == other.getField(
                                global_group_fields[3]
                            ):
                                if self.getField(
                                    global_group_fields[4]
                                ) == other.getField(global_group_fields[4]):
                                    result = True
        return result

    if group_fields:
        group_fields_list = group_fields.split(",")
    else:
        group_preset = group_preset.lower()
        group_fields_list = group_preset_dict.get(group_preset, [""])

    group_fields_list = group_fields_list + append_groups.split(",")
    group_fields_list = [
        group_field for group_field in group_fields_list if group_field != ""
    ]  # Remove blank entries

    if len(group_fields_list) > MAX_GROUP_FIELDS:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} More than {MAX_GROUP_FIELDS} group fields are not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Initialise all group fields to be the last group field because the API doesn't like blank strings
    global_group_fields = [group_fields_list[-1]] * MAX_GROUP_FIELDS

    # Populate with the inputted group fields
    for index, group_field in enumerate(group_fields_list):
        global_group_fields[index] = group_field

    # Get the text before removal to output to terminal
    global_group_fields_text = ",".join(list(dict.fromkeys(global_group_fields)))

    # Remove the mandatory fields so the rest can be user defined
    detected = 0
    mandatory_fields = ["Value", "Footprint"]
    for mandatory_field in mandatory_fields:
        if mandatory_field in global_group_fields:
            detected = detected + 1
            global_group_fields.remove(mandatory_field)

    if detected < len(mandatory_fields):
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Grouping by 'Value' and 'Footprint' is mandatory.",
            file=sys.stderr,
        )
        sys.exit(1)

    if "DNP" in global_group_fields:
        global_group_fields.remove("DNP")
        equ = kiabom_equ_dnp
    else:
        equ = kiabom_equ

    print(
        f"Grouping components by: '{colorama.Fore.LIGHTYELLOW_EX}{global_group_fields_text}{colorama.Style.RESET_ALL}'."
    )
    return equ


def writerow(acsvwriter, columns: list[str]):
    """Override csv.writer's writerow() to support encoding conversion (initial encoding is utf8)

    :param acsvwriter: A csv.writer object used to write the columns list.
    :type acsvwriter: csv.writer
    :param columns: A list of string values to write as a row.
    """
    utf8row = []
    for col in columns:
        utf8row.append(str(col))
    acsvwriter.writerow(utf8row)


def open_output_file(output_file: str) -> io.TextIOWrapper:
    """Open the file to be used for outputing the BOM data.

    :param output_file: Output file name.
    :return: A file object.
    """
    # Output should be at the current working directory
    output_path = os.path.join(os.getcwd(), output_file)

    # Open the output file to write to, if the file cannot be opened output an error
    try:
        f = open(output_path, "w", encoding="utf-8-sig", newline="")
    except IOError:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Can't open output file {output_path} for writing. Make sure the file is closed, or you have permission to write to the location, and try again.",
            file=sys.stderr,
        )
        sys.exit(1)
    return f


def print_title_screen():
    """Print the title splash."""
    print(
        rf"""
    {colorama.Fore.LIGHTYELLOW_EX}
     _   ___  ___  ______  ________  ___
    | | / (_)/ _ \ | ___ \|  _  |  \/  |
    | |/ / _/ /_\ \| |_/ /| | | | .  . |
    |    \| |  _  || ___ \| | | | |\/| |
    | |\  \ | | | || |_/ /\ \_/ / |  | |
    \_| \_/_\_| |_/\____/  \___/\_|  |_/
    {colorama.Style.RESET_ALL}

    KiABOM is licensed under GPL v3, and comes with ABSOLUTELY NO WARRANTY.
    Use '-h'/'--help' option for the full list of comnmands. Use '-q'/'--quiet' to silence warnings.
    """,
        file=sys.stdout,
    )


def output_general_info_csv(out, net: netlist, board_quantity: int):
    """

    :param out: A csv.writer object created with csv.writer().
    :type out: csv.writer.
    :param net: The netlist object created by opening the XML with kicad_netlist_reader.
    :param board_quantity: Board quantity.
    """
    writerow(out, [""])
    writerow(out, ["Board Quantity:", str(board_quantity)])
    writerow(out, ["Schematic:", str(net.getSource())])
    writerow(out, ["Component Count:", str(len(net.components))])
    writerow(out, ["Date:", str(net.getDate())])
    writerow(out, ["Generator:", sys.argv[0], " KiABOM v", __version__])
    writerow(out, ["Link: https://github.com/Mage-Control-Systems/kiabom"])


def output_general_info_html(html: str, net: netlist, board_quantity: int) -> str:
    """Output some general info afte the HTML BOM table.

    :param html: HTML string.
    :param net: Netlist object opened using kicad_netlist_reader.
    :param board_quantity: Board quantity.
    :return: HTML string.
    """
    html = html.replace("<!--QUANTITY-->", "Board Quantity" + str(board_quantity))
    html = html.replace("<!--SOURCE-->", "Schematic" + str(net.getSource()))
    html = html.replace(
        "<!--COMPCOUNT-->", "Component Count:" + str(len(net.components))
    )
    html = html.replace("<!--DATE-->", "Date:" + str(net.getDate()))
    html = html.replace(
        "<!--TOOL-->", "Generator:" + sys.argv[0] + " KiABOM v" + __version__
    )
    html = html.replace(
        "<!--LINK-->", "Link: https://github.com/Mage-Control-Systems/kiabom"
    )

    return html


def get_columns(columns: str, preset: str) -> list[str]:
    """Get the specified columns for use during BOM generation.

    :param columns: Comma separated string of the columns names.
    :param preset: Specified column list preset.
    :return: A column string list.
    """

    if columns:
        columns_ret = columns.split(",")
    else:
        preset = preset.lower()
        columns_ret = column_preset_dict.get(preset, [""])

    return columns_ret


def has_internet(test_address: str = "8.8.8.8", timeout: int = 5) -> bool:
    """Check if there is a valid internet connection.

    :param test_address: Address used to test for internet connection.
    :param timeout: Time to wait until a valid internet connection is established.
    :return: True or False on whether there is an internet connection.
    """
    conn = http.client.HTTPSConnection(test_address, timeout=timeout)
    try:
        conn.request("HEAD", "/")
        return True
    except OSError:
        return False
    finally:
        conn.close()


def get_return_empty(no_kicost: bool, primary_only: bool) -> tuple:
    """Get if any parts need to not be searched and returned empty lists

    :param no_kicost: Flag if no KiCost should be used
    :param primary_only: Flag if only the primary supplier should be used

    :return: A tuple of boolean values. Used to decide if the suppliers objects should be empty lists.
    """
    primary_supplier_return_empty = False
    secondary_supplier_return_empty = False

    if no_kicost is True and primary_only is True:
        primary_supplier_return_empty = True
        secondary_supplier_return_empty = True
    elif no_kicost is True and primary_only is False:
        primary_supplier_return_empty = True
        secondary_supplier_return_empty = True
    elif no_kicost is False and primary_only is True:
        primary_supplier_return_empty = False
        secondary_supplier_return_empty = True
    elif no_kicost is False and primary_only is False:
        primary_supplier_return_empty = False
        secondary_supplier_return_empty = False

    return (primary_supplier_return_empty, secondary_supplier_return_empty)


def download_datasheets(
    grouped: list[list[comp]], downloads_folder: str = "datasheets", timeout: int = 2
):
    """Download the datasheets from the 'Datasheets' symbol field

    :param grouped: A list containing lists of grouped parts
    :param downloads_folder: Downloads folder name
    :param timeout: Time in seconds where the internet connection will time out.
    """
    downloads_path = os.path.join(os.getcwd(), downloads_folder)

    # Create the directory
    try:
        os.mkdir(downloads_path)
    except FileExistsError:
        pass
    except PermissionError:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Permission denied, unable to create '{downloads_path}' folder. Will not download datasheets.",
            file=sys.stderr,
        )
        return

    # Get the URLs
    urls = []
    for group in grouped:
        for component in group:
            urls.append(component.getField("Datasheet"))

    # Remove the ones with "~" values
    urls = [url for url in urls if url != "~"]

    # Split the urls and the last list entry is the filename
    file_paths = []
    for url in urls:
        full_filename = url.split("/")[-1]
        name, ext = os.path.splitext(full_filename)
        if url.split("/")[0] in ["https:", "http:"] and name != "":
            if ext == "":
                full_filename = full_filename + ".pdf"
            file_paths.append(os.path.join(downloads_path, full_filename))
        else:
            if not QUIET:
                print(
                    f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} URL '{url}' is not valid - skipping."
                )
            urls.remove(url)

    # Combine the URLs and the file paths to make them more easily iterable
    datasheet_dict = dict(zip(file_paths, urls))

    # Download
    for path, url in datasheet_dict.items():
        try:
            r = requests.get(url, allow_redirects=True, timeout=timeout)
        except requests.exceptions.ReadTimeout:
            print(f"URL '{url}' timed out - skipping.")
            if not QUIET:
                print(
                    f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} URL '{url}' timed out - skipping."
                )
            continue
        with open(path, "wb") as f:
            f.write(r.content)
        full_filename = url.split("/")[-1]
        print(
            f"Downloaded '{colorama.Fore.LIGHTYELLOW_EX}{full_filename}{colorama.Style.RESET_ALL}'."
        )

    print(
        f"Datasheets downloaded in '{colorama.Fore.LIGHTYELLOW_EX}{downloads_path}{colorama.Style.RESET_ALL}'."
    )


def check_args(args: argparse.Namespace):
    """Check the input arguments are valid.

    :param args: Input arguments.
    """
    supported_suppliers = ["Mouser", "DigiKey"]
    supported_currencies = ["GBP", "USD", "EUR"]

    if args.preset.lower() in preset_dict:
        if args.columns_preset == "":
            args.columns_preset = preset_dict[args.preset.lower()][0]
        if args.group_preset == "":
            args.group_preset = preset_dict[args.preset.lower()][1]
    else:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Specified preset '{args.preset}' not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.list_suppliers:
        print("Supported suppliers are:\n\n\t", "\n\t".join(supported_suppliers))
        sys.exit(0)

    if args.list_presets:
        print("Built in presets are:\n")
        for key, val in preset_dict.items():
            print("{key}:\n\t{val}\n".format(key=key, val="\n\t".join(val)))
        sys.exit(0)

    if args.list_group_presets:
        print("Built in group presets are:\n")
        for key, val in group_preset_dict.items():
            print("{key}:\n\t{val}\n".format(key=key, val="\n\t".join(val)))
        sys.exit(0)

    if args.list_column_presets:
        print("Built in column presets are:\n")
        for key, val in column_preset_dict.items():
            print("{key}:\n\t{val}\n".format(key=key, val="\n\t".join(val)))
        sys.exit(0)

    if args.list_supported_columns:
        print("Supported columns are:\n")
        print(
            "\t{list} \n[+ any symbol field]".format(
                list="\n\t".join(
                    [
                        "Quantity",
                        "Schematic Ref",
                        "Designator",
                        "DNP",
                        "Description",
                        "Datasheet",
                        "Footprint",
                        "Value",
                        "Comment",
                        "Manufacturer",
                        "MPN",
                        "Preferred Supplier",
                        "Order Code",
                        "Alt. Supplier",
                        "Alt. Order Code",
                        "Unit/Reel Price",
                        "Total Price",
                    ]
                )
            )
        )
        sys.exit(0)

    if args.primary_supplier.lower() not in [
        supplier.lower() for supplier in supported_suppliers
    ]:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Primary supplier '{args.primary_supplier}' not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.secondary_supplier.lower() not in [
        supplier.lower() for supplier in supported_suppliers
    ]:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Secondary supplier '{args.primary_supplier}' not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.currency.lower() not in [
        currency.lower() for currency in supported_currencies
    ]:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Currency '{args.currency}' not supported.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.board_quantity.isdigit():
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Detected non-integer board quantity, please input an integer as the quantity.",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        args.board_quantity = int(args.board_quantity)

    if args.board_quantity < 1:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Cannot have board quantity less than 1.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.input_xml == "":
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Please specify a schematic XML.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.columns_preset not in column_preset_dict:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Selected columns preset '{args.columns_preset}' not supported. Please do '--list-column-presets' to show the valid inputs.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.group_preset not in group_preset_dict:
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Selected group preset '{args.columns_preset}' not supported. Please do '--list-group-presets' to show the valid inputs.",
            file=sys.stderr,
        )
        sys.exit(1)


def get_total_price_sum(
    parts_prices: list[str], parts_prices_dnp: list[str], board_quantity: int
) -> float:
    """Get the total price sum to add to the end of the BOM table

    :param parts_prices: List of part prices.
    :param parts_price_dnp: List of DNP part prices.
    :param board_quantity: Specified board quantity.
    :return: Total price sum.
    """
    price_sum = 0.0
    for price in parts_prices:
        if price:
            price_sum += board_quantity * float(price)
    for price in parts_prices_dnp:
        if price:
            price_sum += board_quantity * float(price)
    return price_sum


def write_to_file(
    f: io.TextIOWrapper,
    output_format: str,
    headers_flag: bool,
    info_flag: bool,
    sum_flag: bool,
    board_quantity: int,
    columns: list[str],
    net_obj: Net,
    parts_file_data: PartsFileData,
):
    """Write to the corresponding file the collated data.

    :param f: File object
    :param output_format: Selected output format.
    :param headers_flag: Flag to output headers to the BOM table.
    :param info_flag: Flag to output extra info to the end of the file.
    :param sum_flag: Flag to output the total price sum after the BOM table.
    :param board_quantity: Specify board quantity.
    :param columns: Columns to be used when outputting BOM.
    :param net_obj: A Net object.
    :param parts_file_data: A PartsFileData object.
    """
    if output_format in ("csv", "txt"):
        # Create a new csv writer object to use as the output formatter
        out = csv.writer(
            f, lineterminator="\n", delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL
        )

        # Output column headings
        if headers_flag:
            writerow(out, columns)

        # Output the component groups to the csv based on data retrieved by the suppliers
        write_parts_to_csv(
            out, board_quantity, columns, net_obj.grouped, parts_file_data
        )
        write_parts_to_csv(
            out, board_quantity, columns, net_obj.dnp.grouped, parts_file_data.dnp
        )

        if sum_flag:
            # Remove blank entries to get the symbol in the first entry
            currency_symbol = [x for x in parts_file_data.currency_symbol if x][0]

            writerow(out, [""])
            writerow(
                out,
                [
                    "Total Price Sum:",
                    currency_symbol
                    + str(
                        get_total_price_sum(
                            parts_file_data.price,
                            parts_file_data.dnp.price,
                            board_quantity,
                        )
                    ),
                ],
            )

        # Output column headings and some info about the generator/script
        if info_flag:
            output_general_info_csv(out, net_obj.net, board_quantity)

    elif output_format == "html":
        # Start with a basic html template
        html = """
        # <!DOCTYPE html PUBLIC   "-//W3C//DTD XHTML 1.0 Transitional//EN"
        #     "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">
            <head>
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <title>KiABOM Bill Of Materials</title>
            </head>
            <body>
            <h1>KiABOM HTML Bill Of Materials</h1>
            <p><!--QUANTITY--></p>
            <p><!--SOURCE--></p>
            <p><!--DATE--></p>
            <p><!--TOOL--></p>
            <p><!--COMPCOUNT--></p>
            <p><!--LINK--></p>
            <table border="1">
            <!--TABLEROW-->
            </table>
            </body>
        </html>
            """

        if headers_flag:
            row = "\t<tr>"
            for column in columns:
                row += "<th>" + column + "</th>"
            row += "</tr>\n\t\t\t"
            html = html.replace("<!--TABLEROW-->", row + "<!--TABLEROW-->")

        # Output the component groups to the csv based on data retrieved by the suppliers
        html = set_html_table(
            html, board_quantity, columns, net_obj.grouped, parts_file_data
        )
        html = set_html_table(
            html, board_quantity, columns, net_obj.dnp.grouped, parts_file_data.dnp
        )

        if sum_flag:
            # Remove blank entries to get the symbol in the first entry
            currency_symbol = [x for x in parts_file_data.currency_symbol if x][0]

            row = "\t<tr>"
            row += get_html_td_string("Total Price Sum:")
            row += get_html_td_string(
                currency_symbol
                + str(
                    get_total_price_sum(
                        parts_file_data.price, parts_file_data.dnp.price, board_quantity
                    )
                )
            )
            row += "</tr>\n\t\t\t"
            html = html.replace("<!--TABLEROW-->", row + "<!--TABLEROW-->")

        # Output column headings and some info about the generator/script
        if info_flag:
            html = output_general_info_html(html, net_obj.net, board_quantity)

        f.write(html)


def set_format_from_output_file_extension(output_file: str) -> str:
    """Automatically set the output format based on the output file extension

    :param output_file: Output file name.
    :return: Output file format.
    """
    output_format = ""
    supported_formats = ["csv", "html", "txt"]
    ext = output_file.split(".")[-1]

    if ext.lower() in supported_formats:
        output_format = ext.lower()

    if output_format == "":
        print(
            f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Output format '{output_format}' not supported. Supported ones are CSV, HTML, and TXT.",
            file=sys.stderr,
        )
        sys.exit(1)

    return output_format


def remove_ignore_mpn_parts(
    grouped: list[list[comp]], ignore_mpns: list[str]
) -> list[list[comp]]:
    new_grouped = []
    for group in grouped:
        component = group[0]
        mpn = component.getField("MPN")
        if mpn not in ignore_mpns:
            new_grouped.append(group)

    return new_grouped


def main(argv: list[str]):
    """Main function executed when __name__ is "__main__".

    :param argv: Argument vector containing command line options.
    """
    global QUIET

    # Print some nice ASCII art
    print_title_screen()

    datetime_text = datetime.now().strftime("%H%M%S%d%m%y")

    parser = argparse.ArgumentParser(
        usage="%(prog)s input_xml output_file [options]",
        description="Automatic BOM tool for KiCAD.",
    )
    parser.add_argument(
        "input_xml",
        help="input the path to the XML file generated from the KiCAD schematic.",
        nargs="?",
        default="",
    )
    parser.add_argument(
        "output_file",
        help="name of the output CSV or HTML file. It will be outputed in the same directory where the script is run from.",
        nargs="?",
        default=f"kiabom-output-{datetime_text}.csv",
    )
    parser.add_argument(
        "--version",
        help="output the KiABOM version.",
        action="version",
        version="%(prog)s " + __version__,
    )
    parser.add_argument(
        "--info",
        help="append to the output some general info about the generated BOM like, board quantity, schematic name, component count, date, and generator used.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--no-headers",
        help="don't output BOM column headers.",
        action="store_false",
        default=True,
    )
    parser.add_argument(
        "-k",
        "--no-kicost",
        help="disable the KiCost integration.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--preset",
        help="specify both the columns and group presets at the same time with this option. Both '--columns-preset' and '--group-preset' overwrite this option.",
        default="Default",
    )
    parser.add_argument(
        "--columns-preset",
        help="set a BOM preset for what part data should be outputed. Overwrites '--columns' if it comes after. Use '--append-columns' to append columns to a preset. Choose between 'Default', 'Minimal', 'No-KiCost', and 'Mage'.",
        default="",
    )
    parser.add_argument(
        "--group-preset",
        help="choose a group preset. Available ones are 'Default', 'Minimal', and 'Mage'. Append to a preset with '--append-groups'.",
        default="default",
    )
    parser.add_argument(
        "-g",
        "--group-by",
        help="choose what symbol fields to group by, Grouping by 'Value' and 'Footprint' is mandatory. Choose up to 5 additional fields to group by. Use values separated by commas and place values in quotes in they contain spaces",
        default="",
    )
    parser.add_argument(
        "-c",
        "--columns",
        help="set the columns to be outputed. Use values separated by commas and place values in quotes in they contain spaces. Overwrites '--preset' if it comes after. Use '--append-columns' to append columns to a preset and `--list-supported-columns' to list valid column values.",
        default="",
    )
    parser.add_argument(
        "-a",
        "--append-columns",
        help="append columns to the selected preset. Use values separated by commas and place values in quotes in they contain spaces.",
        default="",
    )
    parser.add_argument(
        "--append-groups",
        help="append to a group preset.",
        default="",
    )
    parser.add_argument(
        "--ignore-mpns",
        help="add more MPN field values to ignore. This option appends the default option of 'Generic','TBD','Manufacturer's Stock', and '' (blank). Use values separated by commas and place values in quotes in they contain spaces.",
        default="",
    )
    parser.add_argument(
        "-p",
        "--primary-supplier",
        help="select primary supplier from supplier list. View by executing KiABOM with '--list-suppliers' option.",
        default="Mouser",
    )
    parser.add_argument(
        "-s",
        "--secondary-supplier",
        help="select secondary supplier. View by executing KiABOM with '--list-suppliers' option.",
        default="DigiKey",
    )
    parser.add_argument(
        "-d",
        "--download-datasheets",
        help="optionally donwload the datasheets for the parts with valid URLs in a 'Datasheet' field. Files get downloaded to a 'datasheets' folder in the current working directory.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-u",
        "--primary-only",
        help="only use the primary supplier.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "-q", "--quiet", help="silence warnings", action="store_true", default=False
    )
    parser.add_argument(
        "--kefbom",
        "--keep-exclude-from-bom",
        help="include the components with the 'Exclude from BOM' property set.",
        action="store_false",
        default=True,
    )
    parser.add_argument(
        "--kefboard",
        "--keep-exclude-from-board",
        help="include the components with the 'Exclude from Board' property set.",
        action="store_false",
        default=True,
    )
    parser.add_argument(
        "-b",
        "--board-quantity",
        help="select board quantity, default is 1.",
        default="1",
    )
    parser.add_argument(
        "--sum",
        help="add a summation of the total price to the end of the table.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--currency",
        help="select the currency, currently supports 'GBP', 'EUR', and 'USD' options.",
        default="GBP",
    )
    parser.add_argument(
        "--remove-ignore-mpn-parts",
        help="remove parts from the BOM that contain the ignore MPN values. This options was implemented specifically for supplier BOM tools.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--list-suppliers",
        help="list supported suppliers.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--list-presets",
        help="list built-in presets.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--list-column-presets",
        help="list built-in column presets.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--list-group-presets",
        help="list built-in group presets.",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--list-supported-columns",
        help="list supported column values. Any symbol field can also be a column value.",
        action="store_true",
        default=False,
    )

    args = parser.parse_args(args=argv)

    check_args(args)

    # Autodetect output format if not given
    output_format = set_format_from_output_file_extension(args.output_file)

    QUIET = args.quiet

    # Open the output file for writing. Do that at the start to check if the file is open.
    f = open_output_file(args.output_file)

    # Override the component equivalence operator for grouping
    kicad_netlist_reader.comp.__eq__ = get_equ(
        args.group_by, args.group_preset.lower(), args.append_groups
    )

    # Initialise Net object to read everything from the XML file
    print("Reading schematic XML file...", flush=True)
    net_obj = Net(args.input_xml, excludeBOM=args.kefbom, excludeBoard=args.kefboard)

    ignore_mpns = [
        "Generic",
        "TBD",
        "Manufacturer's Stock",
        "",
    ] + args.ignore_mpns.split(",")

    # Remove parts with the ignore MPN values if specified
    if args.remove_ignore_mpn_parts:
        net_obj.grouped = remove_ignore_mpn_parts(net_obj.grouped, ignore_mpns)
        net_obj.group_count = len(net_obj.grouped)
        net_obj.refdes_groups = net_obj.get_refdes_from_net(net_obj.grouped)

        net_obj.dnp.grouped = remove_ignore_mpn_parts(net_obj.dnp.grouped, ignore_mpns)
        net_obj.dnp.group_count = len(net_obj.dnp.grouped)
        net_obj.dnp.refdes_groups = net_obj.get_refdes_from_net(net_obj.dnp.grouped)

    # If no internet then just skip the KiCost integration
    if not has_internet():
        args.no_kicost = True
        args.download_datasheets = False
        print(
            "Detected no internet, KiCost and downloading datasheets is unavailable.",
            flush=True,
        )

    # Initialise the KiCost logger and APIs
    if not args.no_kicost:
        if init_kicost():
            print("Initialised KiCost.", flush=True)
        else:
            print(
                "Config file'config.yaml' not found; continuing without the KiCost integration.",
                flush=True,
            )
            args.no_kicost = True
    else:
        print("Disabled KiCost integration.", flush=True)

    (primary_ret_empty, secondary_ret_empty) = get_return_empty(
        args.no_kicost, args.primary_only
    )

    # Initialise Suppliers class to search for parts in the specified suppliers
    primary_supplier_parts = Parts(
        args.primary_supplier,
        net_obj,
        primary_ret_empty,
        args.currency,
        ignore_mpns,
        int(args.board_quantity),
    )
    secondary_supplier_parts = Parts(
        args.secondary_supplier,
        net_obj,
        secondary_ret_empty,
        args.currency,
        ignore_mpns,
        int(args.board_quantity),
    )

    # Columns to be used for each part.
    columns = get_columns(
        args.columns, args.columns_preset
    ) + args.append_columns.split(",")
    columns = [column for column in columns if column != ""]  # Remove blank entries
    print(
        f"Columns for the BOM will be: {colorama.Fore.LIGHTYELLOW_EX}{','.join(columns)}{colorama.Style.RESET_ALL}."
    )

    # Create the file data based on what was returned from KiCost and the net reader
    parts_file_data = PartsFileData(primary_supplier_parts, secondary_supplier_parts)

    # Finally write the data to file
    write_to_file(
        f,
        output_format,
        args.no_headers,
        args.info,
        args.sum,
        args.board_quantity,
        columns,
        net_obj,
        parts_file_data,
    )
    print(
        f"Wrote results to '{colorama.Fore.LIGHTYELLOW_EX}{args.output_file}{colorama.Style.RESET_ALL}'.",
        flush=True,
    )

    if args.download_datasheets:
        print("Downloading datasheets...")
        datasheets_folder = "datasheets"
        download_datasheets(net_obj.grouped, downloads_folder=datasheets_folder)

    print("\nKiABOM finished!\n")

    f.close()

    # Exit with code 0 to signal to the OS that the program finished succesfully
    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
