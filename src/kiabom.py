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
    python "path/to/kiabom.py" "%I" "%O.csv" [options]
"""

__version__ = "2.0.0"
__author__ = "Yiannis Michael (ymic9963)"
__license__ = "GNU General Public License v3.0 only"

import csv
import io
import sys
import argparse
import os
import http.client
import colorama
import requests
import yaml
import time
import pickle
import re
import kicad_netlist_reader
from pathlib import Path
from kicad_netlist_reader import comp, netlist
from mouser import api, base
import digikey
from digikey.v4.productinformation import KeywordRequest


EPOCH_TIME = epoch_time = int(time.time())
MAX_GROUP_FIELDS = 7
QUIET = False
DIR_PATH = Path(__file__).resolve().parent
CACHE_PATH = DIR_PATH / "kiabom_cache"

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
        "no-api": [
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


class KiCadNetlist:
    """Class containing KiCad netlist data

    :param input_xml: Input XML file name.
    :param net: Netlist reader object.
    :param components: List of components from the schematic.
    :param grouped: List of grouped compoentns.
    :param group_count: Number of groups.
    """

    def __init__(
            self, input_xml: str | Path, excludeBOM: bool, excludeBoard: bool, DNP: bool
            ) -> None:
        self.input_xml = input_xml

        # Initialise
        self.net = netlist()

        # Generate a netlist tree from the one provided in the command line option
        try:
            self.net = kicad_netlist_reader.netlist(str(input_xml))
        except ValueError:
            print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Unable to open XML file. Please check path is correct or that the file exists.",
                    file=sys.stderr,
                    )
            sys.exit(1)

        # Get the list of components
        self.components = self.net.getInterestingComponents(
                excludeBOM=excludeBOM, excludeBoard=excludeBoard, DNP=DNP
                )

        print(
                f"Received {colorama.Fore.LIGHTYELLOW_EX}{len(self.components)}{colorama.Style.RESET_ALL} components from netlist.",
                flush=True,
                )

        # Get all of the components in groups of matching parts + values
        self.grouped = self.net.groupComponents(self.components)
        self.group_count = len(self.grouped)

        print(
                f"Grouped netlist components into {colorama.Fore.LIGHTYELLOW_EX}{self.group_count}{colorama.Style.RESET_ALL} component groups.",
                flush=True,
                )

        self.refdes_groups = []
        self.get_refdes_from_net()

    def get_refdes_from_net(self):
        """Get reference designators from KiCAD netlist reader

        :param grouped: List of kicad_netlist_reader component groups.
        :return: A list of reference designator groups.
        """
        self.refdes_groups = []
        for group in self.grouped:
            refs_list = []
            for component in group:
                refs_list.append(component.getRef())
            self.refdes_groups.append(refs_list)

    def remove_ignore_mpn_parts(self, ignore_mpns: list[str]):
        new_grouped = []
        for group in self.grouped:
            # First component in group
            component = group[0]
            mpn = component.getField("MPN")
            if mpn not in ignore_mpns:
                new_grouped.append(group)
        self.grouped = new_grouped

        # Update reference designator list and group count
        self.get_refdes_from_net()
        self.group_count = len(self.grouped)

class SupplierAPI:
    def __init__(self, currency_code: str, cache_ttl: int, time: int = EPOCH_TIME):
        self.name = ""
        self.api_status = ""
        self.comp_count = 0
        self.cache_comp_count = 0
        self.cache_path = Path()
        self.currency = ""
        self.cache_ttl = cache_ttl
        self.time = time

        if currency_code == "GBP":
            self.currency = "£"
        elif currency_code == "USD":
            self.currency = "$"
        elif currency_code == "EUR":
            self.currency = "€"

    def api_init(self, config: dict) -> str:
        raise NotImplementedError("Must implement in derived subclass")

    def search(self, mpn: str) -> list:
        raise NotImplementedError("Must implement in derived subclass")

    def parse(self, parts: list[dict]) -> list[dict]:
        raise NotImplementedError("Must implement in derived subclass")

    def get_part(self, mpn: str, ignore_mpns=[""]) -> dict:
        if mpn in ignore_mpns:
            return {}

        cached_part = self.cache_query(mpn)

        if self.cache_ttl >= 0:
            # Important to accept empty dicts
            if cached_part != None:
                self.cache_comp_count = self.cache_comp_count + 1
                return cached_part

        parts = self.search(mpn)
        parts = self.parse(parts)

        # Use the first entry by default
        found_part = parts[0]

        # If there is an exact MPN match use that instead
        for part in parts:
            if part.get("MPN") == mpn:
                found_part = part
                break

        if self.cache_ttl >= 0:
            self.cache_part(mpn, found_part)

        self.comp_count = self.comp_count + 1
        return found_part

    def cache_mpn_normalise(self, mpn):
        mpn = mpn.replace("/","-")
        mpn = mpn.replace("\\","-")

        return mpn

    def cache_query(self, mpn: str) -> dict | None:
        mpn = self.cache_mpn_normalise(mpn)
        cached_file = None
        for (_, _, files) in os.walk(self.cache_path):
            for f in files:
                if mpn in f:
                    cached_file = self.cache_path / f
                    break

        if not cached_file:
            return None

        match = re.search("^.+___(.+).pickle",cached_file.name)
        if not match:
            return None

        file_lifetime = self.time - int(match.group(1))

        # If the file is older than the TTL then
        # don't return part and delete cache so that
        # it can be re-cached
        if file_lifetime > self.cache_ttl:
            os.remove(cached_file)
            return None

        try:
            with open(cached_file, 'rb') as f:
                return pickle.load(f)
        except FileNotFoundError or IOError:
            return None
        
    def cache_part(self, mpn, data):
        mpn = self.cache_mpn_normalise(mpn)
        filename = mpn + "___" + str(self.time) + ".pickle"
        cache_file = self.cache_path / filename
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)

    def print_stats(self):
        print( f"Searched {self.name}, requested {colorama.Fore.LIGHTYELLOW_EX}{self.comp_count}{colorama.Style.RESET_ALL} parts and retrieved {colorama.Fore.LIGHTYELLOW_EX}{self.cache_comp_count}{colorama.Style.RESET_ALL} from cache.", flush=True,)


class MouserAPI(SupplierAPI):
    def __init__(self, config: dict, currency: str, cache_ttl: int):
        super().__init__(currency, cache_ttl)
        self.api_status = self.api_init(config)
        self.name = "Mouser"
        self.cache_path = CACHE_PATH / "mouser_cache"

    def api_init(self, config: dict) -> str:
        mouser_entry = config.get("Mouser", {})
        mouser_key = mouser_entry.get("key")

        if not mouser_entry:
            return "no config entry detected"

        if not mouser_key:
            return "no API key detected"

        os.makedirs(self.cache_path, exist_ok=True)

        def _new_get_api_keys(*arg):
            return [ "", mouser_key, ]

        base.get_api_keys = _new_get_api_keys

        return "success"


    def search(self, mpn: str) -> list:
        mpn = mpn.strip()

        # Search by Part-Number
        obj = api.MouserPartSearchRequest("partnumber")
        obj.part_search(mpn, option="None")  # instead of "None" can be "Exact"
        res = obj.get_response()

        # Check for errors or print the returned results
        if res is None or res == {}:
            print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Error during request for MPN: {mpn}."
                    )
            return [{}]

        search_results = res.get("SearchResults")
        if not search_results:
            return [{}]

        result_count = search_results.get("NumberOfResult", 0)
        if result_count == 0:
            if not QUIET:
                print(
                        f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} No results on Mouser for part number '{mpn}' "
                        )
            return [{}]

        parts = []
        for part in search_results.get("Parts", [""]):
            parts.append(part)

        return parts


    def get_price_tiers(self, price_tiers_list: list[dict]) -> dict:
        if not price_tiers_list:
            return {}

        price_tiers_dict = {}
        for price_tier in price_tiers_list:
            price_tiers_dict[price_tier["Quantity"]] = float(price_tier["Price"][1:])

        return price_tiers_dict


    def parse(self, parts: list[dict]) -> list[dict]:
        # If no parts were found
        if parts[0] == {}:
            return [{}]

        parsed_parts = []
        for part in parts:
            parsed_dict = {}
            parsed_dict["Datasheet"] = part.get("DataSheetUrl", "")
            parsed_dict["Description"] = part.get("Description", "")
            parsed_dict["Manufacturer"] = part.get("Manufacturer", "")
            parsed_dict["MPN"] = part.get("ManufacturerPartNumber", "")
            parsed_dict["Order Code"] = part.get("MouserPartNumber", "")
            parsed_dict["Stock"] = part.get("AvailabilityInStock", "")
            parsed_dict["Product Page"] = part.get("ProductDetailUrl", "")
            parsed_dict["Price Tiers"] = self.get_price_tiers(
                    part.get("PriceBreaks", [])
                    )
            parsed_parts.append(parsed_dict)

        return parsed_parts


class DigiKeyAPI(SupplierAPI):
    def __init__(self, config: dict, currency: str, cache_ttl: int):
        super().__init__(currency, cache_ttl)
        self.cache_path = CACHE_PATH / "digikey_cache"
        self.name = "DigiKey"
        self.api_status = self.api_init(config)

    def api_init(self, config: dict) -> str:
        digikey_entry = config.get("DigiKey", {})
        digikey_client_id = digikey_entry.get("client_id")
        digikey_client_secret = digikey_entry.get("client_secret")
        digikey_sandbox = digikey_entry.get("sandbox")

        if not digikey_entry:
            return "no config entry"

        if not digikey_client_id:
            return "no client ID"

        if not digikey_client_secret:
            return "no client secret"

        if digikey_sandbox is None:
            digikey_sandbox = "False"

        os.makedirs(self.cache_path, exist_ok=True)

        os.environ["DIGIKEY_CLIENT_ID"] = digikey_client_id
        os.environ["DIGIKEY_CLIENT_SECRET"] = digikey_client_secret
        os.environ["DIGIKEY_CLIENT_SANDBOX"] = str(digikey_sandbox)
        os.environ["DIGIKEY_STORAGE_PATH"] = str(self.cache_path)

        return "success"


    def search(self,
            mpn: str, site: str = "uk", language: str = "en", currency: str = "gbp"
            ) -> list[dict]:
        mpn = mpn.strip()

        # x_digikey_locale_site: Two letter code for Digi-Key product website to search on. Different countries sites have different part restrictions, supported languages, and currencies. Acceptable values include: US, CA, JP, UK, DE, AT, BE, DK, FI, GR, IE, IT, LU, NL, NO, PT, ES, KR, HK, SG, CN, TW, AU, FR, IN, NZ, SE, MX, CH, IL, PL, SK, SI, LV, LT, EE, CZ, HU, BG, MY, ZA, RO, TH, PH.
        # x_digikey_locale_language: Two letter code for language to search on. Langauge must be supported by the selected site. If searching on keyword, this language is used to find productes. Acceptable values include: en, ja, de, fr, ko, zhs, zht, it, es, he, nl, sv, pl, fi, da, no.
        # x_digikey_locale_currency: Three letter code for Currency to return part pricing for. Currency must be supported by the selected site. Acceptable values include: USD, CAD, JPY, GBP, EUR, HKD, SGD, TWD, KRW, AUD, NZD, INR, DKK, NOK, SEK, ILS, CNY, PLN, CHF, CZK, HUF, RON, ZAR, MYR, THB, PHP.
        # Search for parts
        search_request = KeywordRequest(keywords=mpn, offset=0)
        res = digikey.keyword_search(
                body=search_request,
                x_digikey_locale_site=site,
                x_digikey_locale_language=language,
                x_digikey_locale_currency=currency,
                )
        if res is None:
            print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Error during request"
                    )
            return [{}]

        res_dict = res.to_dict()
        result_count = res_dict.get("products_count", 0)
        if result_count == 0:
            if not QUIET:
                print(
                        f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} No results on DigiKey for part number '{mpn}' "
                        )
            return [{}]

        parts = []
        for product in res_dict["products"]:
            parts.append(product)

        return parts


    def get_order_code(self, product_variations: list[dict]) -> str:
        if not product_variations:
            return ""

        # Get the Order Code with Cut Tape package type
        selected_product_variations = product_variations[0]
        for prod_var in product_variations:
            id = prod_var.get("package_type", {}).get("id", {})
            if id == 2:  # Cut Tape package type id
                selected_product_variations = prod_var
                break

        return selected_product_variations["digi_key_product_number"]


    def get_order_code_price_tiers(self,
            order_code: str, product_variations: list[dict]
            ) -> dict:
        if not product_variations:
            return {}

        found_product = {}
        for product in product_variations:
            if product["digi_key_product_number"] == order_code:
                found_product = product

        price_tiers_dict = {}
        for price_tier in found_product["standard_pricing"]:
            price_tiers_dict[price_tier["break_quantity"]] = float(price_tier["unit_price"])

        return price_tiers_dict


    def parse(self, parts: list[dict]) -> list[dict]:
        # If no parts were found
        if parts[0] == {}:
            return [{}]

        parsed_parts = []
        for part in parts:
            parsed_dict = {}
            parsed_dict["Datasheet"] = part.get("datasheet_url", "")
            parsed_dict["Description"] = part.get("description", {}).get( "product_description", "")
            parsed_dict["Manufacturer"] = part.get("manufacturer", {}).get("name", "")
            parsed_dict["MPN"] = part.get("manufacturer_product_number", "")
            parsed_dict["Order Code"] = self.get_order_code( part.get("product_variations", []))
            parsed_dict["Stock"] = part.get("quantity_available", "")
            parsed_dict["Price Tiers"] = self.get_order_code_price_tiers( parsed_dict["Order Code"], part.get("product_variations", []))
            parsed_parts.append(parsed_dict)

        return parsed_parts

class PartsSearch:
    """Class containing parts data from the API"""

    def __init__(
            self,
            supplier: str,
            net_obj: KiCadNetlist,
            currency: str,
            ignore_mpns: list,
            config: dict,
            cache_ttl: int
            ) -> None:
        self.parts_list = [{} for _ in range(net_obj.group_count)]
        self.supplier = SupplierAPI("", -1)

        if config.get(supplier.lower()) != "disabled":
            if supplier.lower() == "mouser":
                self.supplier = MouserAPI(config, currency, cache_ttl)
            elif supplier.lower() == "digikey":
                self.supplier = DigiKeyAPI(config, currency, cache_ttl)

            # Update class members with API results if initialisation was succesful
            if self.supplier.api_status == "success":
                print(f"Searching {self.supplier.name}...")
                self.parts_list = self.search_parts( net_obj, ignore_mpns)
                self.supplier.print_stats()
            else:
                print( f"{colorama.Fore.LIGHTYELLOW_EX}WARNING:{colorama.Style.RESET_ALL} {self.supplier.name} API not initialised: {self.supplier.api_status}.", flush=True,)


    def search_parts(
            self, net_obj: KiCadNetlist, ignore_mpns: list
            ) -> list[dict]:
        parts = []
        for group in net_obj.grouped:
            component = group[0]
            mpn = component.getField("MPN")
            parts.append(self.supplier.get_part(mpn, ignore_mpns))

        return parts


class BomData:
    """Class containing the file data required to create the BOM.
    Has data from both primary and secondary suppliers.

    :param manufacturer: Manufacturer list.
    :param primary_order_codes: Primary order codes list.
    :param primary_supplier: Primary supplier list containing the primary supplier string.
    """

    def __init__(
            self,
            pri_obj: PartsSearch,
            sec_obj: PartsSearch,
            refdes_groups: list[list[str]],
            board_quantity: int,
            ) -> None:
        self.pri_res = pri_obj.parts_list
        self.sec_res = sec_obj.parts_list

        self.currency_symbol = ""
        if pri_obj.supplier.currency:
            self.currency_symbol = pri_obj.supplier.currency
        elif sec_obj.supplier.currency:
            self.currency_symbol = sec_obj.supplier.currency

        self.insert_in_result(self.pri_res, "Supplier", pri_obj.supplier.name)
        self.insert_in_result(self.sec_res, "Supplier", sec_obj.supplier.name)

        self.com_res = []
        for pri, sec in zip(self.pri_res, self.sec_res):
            if pri:
                self.com_res.append(pri)
            else:
                self.com_res.append(sec)

        self.insert_in_result(self.com_res, "Currency", self.currency_symbol)

        if len(refdes_groups) != len(self.com_res):
            print(
                    f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} The length of the reference designator groups and API result must match because the index is used to match API result with the netlist. Aborting BOM generation..."
                    )
            sys.exit(1)

        # Get the quantities for each part and insert into common result
        for group, part in zip(refdes_groups, self.com_res):
            part["Quantity"] = int(len(group) * board_quantity)

        # Get the price for each part and insert into common result
        for part in self.com_res:
            if part.get("MPN"):
                price_tiers = part.get("Price Tiers", {})
                for key in price_tiers.keys():
                    part["Price"] = float(price_tiers.get(key))
                    if key > part["Quantity"]:
                        break
            else:
                part["Price"] = ""

        self.total_price = 0
        for part in self.com_res:
            price = part.get("Price")
            if price and price != "":
                self.total_price = self.total_price + price

    def insert_in_result(self, result: list[dict], key: str, val: str):
        for part in result:
            # Check if a result for the part was been found. Could be any API field
            if part.get("Order Code"):
                part.update({key: val})

def get_bom_row(
        pos: int,
        group: list[comp],
        columns: list[str],
        opdata: BomData,
        ) -> list[str]:
    """Generate a BOM row as a list of strings."""

    c = group[0] # Initialise with the first component in the first group

    # Add the reference of every component in the group and
    # keep a reference to the component so that the other data
    # can be filled in once per group
    refs = ", ".join(component.getRef() for component in group)

    quantity = opdata.com_res[pos].get("Quantity", "")
    price = opdata.com_res[pos].get("Price", "")
    currency_symbol = opdata.com_res[pos].get("Currency", "")

    row = []

    for name in columns:
        if name == "Group ID":
            row.append(str(pos + 1))
        elif name == "Quantity":
            row.append(str(quantity))
        elif name in ("Schematic Ref", "Designator"):
            row.append(refs)
        elif name == "DNP":
            row.append("DNP" if c.getDNP() else " ") # Space character needed for sorting in spreadsheet software
        elif name == "Description":
            row.append(c.getField("Description"))
        elif name == "Datasheet":
            row.append(c.getField("Datasheet"))
        elif name == "Footprint":
            row.append(get_footprint_name(c.getFootprint()))
        elif name in ("Value", "Comment"):
            row.append(c.getValue())
        elif name == "Rating":
            row.append(c.getField("Rating"))
        elif name == "Manufacturer":
            row.append(opdata.com_res[pos].get("Manufacturer", ""))
        elif name == "MPN":
            row.append(c.getField("MPN"))
        elif name == "Preferred Supplier":
            row.append(opdata.pri_res[pos].get("Supplier", ""))
        elif name == "Order Code":
            row.append(opdata.pri_res[pos].get("Order Code", ""))
        elif name == "Alt. Supplier":
            row.append(opdata.sec_res[pos].get("Supplier", ""))
        elif name == "Alt. Order Code":
            row.append(opdata.sec_res[pos].get("Order Code", ""))
        elif name == "Unit/Reel Price":
            row.append(f"{currency_symbol}{price}")
        elif name == "Total Price":
            if price != "":
                row.append(f"{currency_symbol}{quantity * float(price)}")
            else:
                row.append("")
        elif c.getField(name):
            row.append(c.getField(name))
        else:
            row.append("")

    return row


def csv_write_bom(out, columns, grouped, opdata):
    for pos, group in enumerate(grouped):
        writerow(out, get_bom_row(pos, group, columns, opdata))


def html_get_td_string(string: str) -> str:
    """Get a string as a table data cell HTML element.

    :param string: Text to be placed between the <td> and </td>.
    :return: String encloded by <td> and </td>.
    """
    return "<td>" + string + "</td>"


def html_get_table(html_text, columns, grouped, opdata):
    for pos, group in enumerate(grouped):
        values = get_bom_row(pos, group, columns, opdata)
        row = (
                "\t<tr>"
                + "".join(html_get_td_string(str(v)) for v in values)
                + "</tr>\n\t\t\t"
                )
        html_text = html_text.replace(
                "<!--TABLEROW-->",
                row + "<!--TABLEROW-->",
                )

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
    output_file = os.path.normpath(output_file)

    # Open the output file to write to, if the file cannot be opened output an error
    try:
        f = open(output_file, "w", encoding="utf-8-sig", newline="")
    except IOError:
        print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Can't open output file '{output_file}' for writing. Make sure the file is closed, folder exists, or you have permission to write to the location, and try again.",
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


def csv_output_general_info(out, net: netlist, board_quantity: int):
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


def html_output_general_info(html: str, net: netlist, board_quantity: int) -> str:
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

    columns_ret = [col.strip() for col in columns_ret]
    return columns_ret


def has_internet(test_address: str = "8.8.8.8", timeout: int = 3) -> bool:
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


def download_datasheets(
        grouped: list[list[comp]], downloads_folder: str | Path = "datasheets", timeout: int = 2
        ):
    """Download the datasheets from the 'Datasheets' symbol field

    :param grouped: A list containing lists of grouped parts
    :param downloads_folder: Downloads folder name
    :param timeout: Time in seconds where the internet connection will time out.
    """
    downloads_path = Path(downloads_folder)

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
    supported_formats = ["csv", "html", "txt"]

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
        for key, val in column_preset_dict.items():
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

    if args.output_format.lower() not in supported_formats:
        print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Selected output format '{args.output_format}' not supported.",
                file=sys.stderr,
                )
        sys.exit(1)

    if not args.cache_ttl.isdigit():
        print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Detected non-integer board quantity, please input an integer as the quantity.",
                file=sys.stderr,
                )
        sys.exit(1)
    else:
        args.cache_ttl = int(args.cache_ttl)

    if args.cache_ttl < 0:
        print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Cannot have cache TTL less than 0.",
                file=sys.stderr,
                )
        sys.exit(1)

def write_to_file(
        f: io.TextIOWrapper,
        output_format: str,
        headers_flag: bool,
        info_flag: bool,
        sum_flag: bool,
        board_quantity: int,
        columns: list[str],
        net_obj: KiCadNetlist,
        bom_data: BomData,
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
        csv_write_bom(out, columns, net_obj.grouped, bom_data)

        if sum_flag:
            writerow(out, [""])
            writerow(
                    out,
                    [
                        "Total Price Sum:",
                        bom_data.currency_symbol + str(bom_data.total_price),
                        ],
                    )

        # Output column headings and some info about the generator/script
        if info_flag:
            csv_output_general_info(out, net_obj.net, board_quantity)

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
        html = html_get_table(html, columns, net_obj.grouped, bom_data)

        if sum_flag:
            row = "\t<tr>"
            row += html_get_td_string("Total Price Sum:")
            row += html_get_td_string(
                    bom_data.currency_symbol + str(bom_data.total_price)
                    )
            row += "</tr>\n\t\t\t"
            html = html.replace("<!--TABLEROW-->", row + "<!--TABLEROW-->")

        # Output column headings and some info about the generator/script
        if info_flag:
            html = html_output_general_info(html, net_obj.net, board_quantity)

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
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Output format '{output_format}' not supported. Supported ones are 'CSV', 'HTML', and 'TXT'.",
                file=sys.stderr,
                )
        sys.exit(1)

    return output_format

def read_config() -> dict:
    config_path = DIR_PATH / "config.yaml"
    try:
        with open(config_path, "r") as f:
            try:
                return yaml.safe_load(f)
            except yaml.YAMLError as e:
                print(
                        f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} Error reading config.yaml file:",
                        e,
                        )
                sys.exit(1)
    except FileNotFoundError or IOError:
        print(
                f"{colorama.Fore.RED}ERROR:{colorama.Style.RESET_ALL} config.yaml could not be opened for reading. Use '--no-api' to skip config check."
                )
        sys.exit(1)


def main(argv: list[str]):
    """Main function executed when __name__ is "__main__".

    :param argv: Argument vector containing command line options.
    """
    global QUIET

    # Print some nice ASCII art
    print_title_screen()

    parser = argparse.ArgumentParser(
            usage="%(prog)s input_xml [options]",
            description="Automatic BOM tool for KiCAD.",
            )
    parser.add_argument(
            "input_xml",
            help="input the path to the XML file generated from the KiCAD schematic.",
            nargs="?",
            default="",
            )
    parser.add_argument(
            "-o",
            "--output",
            help="file path to output the BOM file, e.g. 'BOM.csv' or 'exports/BOM.csv'",
            default="",
            )
    parser.add_argument(
            "-f",
            "--output-format",
            help="specify the output format. If an output file name is provided this argument is ignored",
            default="csv",
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
            "--no-api",
            help="disable using the APIs to retrieve online parts data. Using this option also skips the config check.",
            action="store_true",
            default=False,
            )
    parser.add_argument(
            "--preset",
            help="specify both the columns and group presets at the same time with this option. Both '--columns-preset' and '--group-preset' overwrite this option. Use '--list-presets' to list available.",
            default="Default",
            )
    parser.add_argument(
            "--columns-preset",
            help="set a BOM preset for what part data should be outputed. Overwrites '--columns' if it comes after. Use '--append-columns' to append columns to a preset. Use '--list-column-presets' to list available.",
            default="",
            )
    parser.add_argument(
            "--group-preset",
            help="choose a group preset. Use '--list-group-presets' to list available. Append to a preset with '--append-groups'.",
            default="default",
            )
    parser.add_argument(
            "-g",
            "--group-by",
            help="choose what symbol fields to group by, Grouping by 'Value' and 'Footprint' is mandatory. Choose up to 5 additional fields to group by. Use values separated by commas and place values in quotes if they contain spaces.",
            default="",
            )
    parser.add_argument(
            "-c",
            "--columns",
            help="set the columns to be outputed. Place column names inside quotes and separate them using a comma. Quotes are not required if column names don't contain spaces. Overwrites '--preset' if it comes after. Use '--append-columns' to append columns to a preset and `--list-supported-columns' to list valid column values.",
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
            "-q",
            "--quiet",
            help="silence warnings",
            action="store_true",
            default=False
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
            action="store_true",
            default=False,
            )
    parser.add_argument(
            "--remove-dnp",
            help="remove DNP components from BOM.",
            action="store_true",
            default=False,
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
    parser.add_argument(
            "--cache-ttl",
            help="cache time to live (TTL) in seconds. Defaults to 60 * 60 * 24 = 1 day",
            default=str(60*60*24),
            )
    parser.add_argument(
            "--no-cache",
            help="completely ignore any stored cache",
            action="store_true",
            default=False,
            )

    args = parser.parse_args(args=argv)

    check_args(args)

    # If no output file name create it from the input file name
    if args.output == "":
        args.output = (
                os.path.splitext(os.path.basename(args.input_xml))[0]
                + "."
                + args.output_format
                )
    else:
        # If it is given use its file extension to set the format
        args.output_format = set_format_from_output_file_extension(args.output)

    # Open the file before anything else to check if it is writeable
    f = open_output_file(args.output)

    QUIET = args.quiet

    # Override the component equivalence operator for grouping
    kicad_netlist_reader.comp.__eq__ = get_equ(
            args.group_by, args.group_preset.lower(), args.append_groups
            )

    # Initialise Net object to read everything from the XML file
    print("Reading schematic XML file...", flush=True)
    net_obj = KiCadNetlist(
            args.input_xml,
            excludeBOM=args.kefbom,
            excludeBoard=args.kefboard,
            DNP=args.remove_dnp,
            )

    ignore_mpns = [
            "Generic",
            "TBD",
            "Manufacturer's Stock",
            "",
            ] + args.ignore_mpns.split(",")

    # Remove parts with the ignore MPN values if specified
    if args.remove_ignore_mpn_parts:
        net_obj.remove_ignore_mpn_parts(ignore_mpns)

    # If no internet then just skip the API integration
    if not has_internet():
        args.no_api = True
        args.download_datasheets = False
        print(
                "Detected no internet, using APIs and downloading datasheets is unavailable.",
                flush=True,
                )

    # Read config to initialise APIs
    config = {}
    if args.no_api:
        print("Disabled API integration.", flush=True)
        config = {args.primary_supplier.lower(): "disabled", args.secondary_supplier.lower(): "disabled"}
    else:
        config = read_config()

    # Set cache ttl to -1 if no cache is to be used
    if args.no_cache:
        print("Disabled cache.", flush=True)
        args.cache_ttl = -1

    # Search for the parts using the APIs
    primary_supplier_parts = PartsSearch( args.primary_supplier, net_obj, args.currency, ignore_mpns, config, args.cache_ttl)
    secondary_supplier_parts = PartsSearch( args.secondary_supplier, net_obj, args.currency, ignore_mpns, config, args.cache_ttl)

    # Columns to be used for each part.
    columns = get_columns( args.columns, args.columns_preset) + args.append_columns.split(",")
    columns = [column for column in columns if column != ""]  # Remove blank entries
    print(
            f"Columns for the BOM will be: {colorama.Fore.LIGHTYELLOW_EX}{','.join(columns)}{colorama.Style.RESET_ALL}.",
            flush=True,
            )

    # Combine the Parts objects with the quantities to create the BOM data
    bom_data = BomData(
            primary_supplier_parts,
            secondary_supplier_parts,
            net_obj.refdes_groups,
            args.board_quantity,
            )

    # Finally write the data to file
    write_to_file(
            f,
            args.output_format,
            args.no_headers,
            args.info,
            args.sum,
            args.board_quantity,
            columns,
            net_obj,
            bom_data,
            )

    print(
            f"Wrote results to '{colorama.Fore.LIGHTYELLOW_EX}{args.output}{colorama.Style.RESET_ALL}'.",
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
