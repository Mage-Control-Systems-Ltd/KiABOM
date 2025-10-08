from src.kiabom import *
from unittest.mock import mock_open, patch
import pytest
import os


def test_print_title_screen():
    print_title_screen()  # not really sure how to test this but it's good for coverage
    assert True


def test_open_output_file():
    output_file = "test.txt"

    m = mock_open()

    with patch("builtins.open", m):  # Patch open during this context
        f = open_output_file(output_file)

    # Assert open was used with 'w', encoding="utf-8-sig", newline=""
    test_path = os.path.join(os.getcwd(), output_file)
    m.assert_called_once_with(test_path, "w", encoding="utf-8-sig", newline="")

    # Check that the returned object is the mocked file handle
    assert f == m()

    # Check if it fails properly
    with pytest.raises(SystemExit) as exc_info:
        open_output_file("")

    assert exc_info.value.code == 1

    f.close()


def test_check_args():
    class Args:
        preset = "default"
        columns_preset = ""
        group_preset = ""
        list_suppliers = False
        list_supported_columns = False
        list_presets = False
        list_column_presets = False
        list_group_presets = False
        primary_supplier = "Mouser"
        secondary_supplier = "DigiKey"
        board_quantity = "1"
        currency = "GBP"
        input_xml = "test.xml"

    args = Args()

    # Check if it exits properly
    args.preset = "test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()  # reset args to defaults to test next condition

    args.columns_preset = "test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()  # reset args to defaults to test next condition

    args.group_preset = "test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()  # reset args to defaults to test next condition

    args.list_suppliers = True
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 0
    args = Args()  # reset args to defaults to test next condition

    args.list_supported_columns = True
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 0
    args = Args()

    args.list_presets = True
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 0
    args = Args()

    args.list_column_presets = True
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 0
    args = Args()

    args.list_group_presets = True
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 0
    args = Args()

    args.primary_supplier = "Test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.secondary_supplier = "Test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.board_quantity = "0"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.board_quantity = "1.5"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.board_quantity = "test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.board_quantity = "test"
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.currency = ""
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()

    args.input_xml = ""
    with pytest.raises(SystemExit) as exc_info:
        check_args(args)
    assert exc_info.value.code == 1
    args = Args()


def test_set_format_from_output_file_extension():
    assert set_format_from_output_file_extension("test.csv") == "csv"
    assert set_format_from_output_file_extension("test.html") == "html"
    assert set_format_from_output_file_extension("test.txt") == "txt"
    assert set_format_from_output_file_extension("test.CSV") == "csv"

    with pytest.raises(SystemExit) as exc_info:
        set_format_from_output_file_extension("test.test")
    assert exc_info.value.code == 1


def test_get_return_empty():
    (p, s) = get_return_empty(True, True)
    assert (p, s) == (True, True)

    (p, s) = get_return_empty(True, False)
    assert (p, s) == (True, True)

    (p, s) = get_return_empty(False, True)
    assert (p, s) == (False, True)

    (p, s) = get_return_empty(False, False)
    assert (p, s) == (False, False)


def test_has_internet():
    assert has_internet() == True
    assert has_internet("", timeout=1) == False


def test_get_columns():
    preset_dict = {
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
    }

    columns = ""
    preset = "default"

    columns_ret = get_columns(columns, preset)
    assert columns_ret == preset_dict["default"]

    preset = "test"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == [""]

    preset = "Minimal"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == preset_dict["minimal"]

    preset = "no-kicosT"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == preset_dict["no-kicost"]

    preset = "primary-only"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == preset_dict["primary-only"]

    preset = "MAGE"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == preset_dict["mage"]

    columns = "a,b,c"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == ["a", "b", "c"]


def test_fill_primary_list_gaps_with_secondary():
    a = ["a", "", "c", ""]
    b = ["", "b", "", "d"]

    fill_primary_list_gaps_with_secondary(a, b)

    assert a == ["a", "b", "c", "d"]


def test_net_class():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    with pytest.raises(SystemExit) as exc_info:
        net_obj = Net(
            "\\random\\path\\that\\will\\fail.xml", excludeBoard=True, excludeBOM=True
        )
    assert exc_info.value.code == 1

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=True)
    expected_refdes_groups = [["BT1"], ["D1"], ["R1"]]
    expected_refdes_groups_DNP = [["BT2"], ["D2"], ["R2"]]

    assert expected_refdes_groups == net_obj.refdes_groups
    assert expected_refdes_groups_DNP == net_obj.dnp.refdes_groups

    net_obj = Net(test_project_path, excludeBoard=False, excludeBOM=True)
    expected_refdes_groups = [["BT1"], ["D1"], ["H2"], ["R1"]]
    expected_refdes_groups_DNP = [["BT2"], ["D2"], ["R2"]]

    assert expected_refdes_groups == net_obj.refdes_groups
    assert expected_refdes_groups_DNP == net_obj.dnp.refdes_groups

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=False)
    expected_refdes_groups = [["BT1"], ["D1"], ["H1"], ["R1"]]
    expected_refdes_groups_DNP = [["BT2"], ["D2"], ["R2"]]

    assert expected_refdes_groups == net_obj.refdes_groups
    assert expected_refdes_groups_DNP == net_obj.dnp.refdes_groups

    net_obj = Net(test_project_path, excludeBoard=False, excludeBOM=False)
    expected_refdes_groups = [["BT1"], ["D1"], ["H1", "H2", "H3"], ["R1"]]
    expected_refdes_groups_DNP = [["BT2"], ["D2"], ["R2"]]

    assert expected_refdes_groups == net_obj.refdes_groups
    assert expected_refdes_groups_DNP == net_obj.dnp.refdes_groups

    class TestNet(BaseNet):
        pass

    try:
        test_net = TestNet(test_project_path, excludeBoard=False, excludeBOM=False)
    except NotImplementedError:
        assert True

    # Test if the behaviour is correct when no DNP components are present
    # Use the non-DNP components for testing extract_DNP(),
    # which should return a list with an empty component
    test_no_DNP = net_obj.dnp.extract_dnp(net_obj.components)

    assert len(test_no_DNP) == 1
    assert test_no_DNP[0].getRef() == "BOM-EMPTY"


def test_init_kicost():
    # Essential because of the debug messages
    # ONLY CALL THIS FUNCTION ONCE
    assert init_kicost() == True


def test_parts_mouser():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=True)

    parts = Parts("Mouser", net_obj, False, "GBP", ["Generic"], 1)
    parts_refs = parts.get_refs_from_kicost(parts.parts_list)
    assert net_obj.refdes_groups == parts_refs

    partsdnp = parts.dnp
    partsdnp_refs = parts.get_refs_from_kicost(partsdnp.parts_list)
    assert net_obj.dnp.refdes_groups == partsdnp_refs

    comp_count = parts.comp_count + partsdnp.comp_count
    assert comp_count == 6

    # Order code is based on MPN used for the LED in the test project. Taken from Mouser directly.
    test_part_order_code = "630-HSMW-C170-U0000"
    test_part_manf = "Broadcom / Avago"

    # Testing it retrieves the correct order code (blank entries removed)
    non_blank_parts_order_codes = [
        order_code for order_code in parts.order_codes if order_code != ""
    ]
    assert non_blank_parts_order_codes[0] == test_part_order_code

    non_blank_partsdnp_order_codes = [
        order_code for order_code in partsdnp.order_codes if order_code != ""
    ]
    assert non_blank_partsdnp_order_codes[0] == test_part_order_code

    # Testing it retrieves the correct manufacturer (blank entries removed)
    non_blank_parts_manf = [manf for manf in parts.manufacturers if manf != ""]
    assert non_blank_parts_manf[0] == test_part_manf

    non_blank_partsdnp_manf = [manf for manf in partsdnp.manufacturers if manf != ""]
    assert non_blank_partsdnp_manf[0] == test_part_manf


def test_parts_digikey():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=True)

    parts = Parts("DigiKey", net_obj, False, "GBP", ["Generic"], 1)
    parts_refs = parts.get_refs_from_kicost(parts.parts_list)
    assert net_obj.refdes_groups == parts_refs

    partsdnp = parts.dnp
    partsdnp_refs = parts.get_refs_from_kicost(partsdnp.parts_list)
    assert net_obj.dnp.refdes_groups == partsdnp_refs

    comp_count = parts.comp_count + partsdnp.comp_count
    assert comp_count == 6

    # Order code is based on MPN used for the LED in the test project. Taken from Mouser directly.
    test_part_order_code = "516-3993-1-ND"
    test_part_manf = "Broadcom Limited"

    # Testing it retrieves the correct order code (blank entries removed)
    non_blank_parts_order_codes = [
        order_code for order_code in parts.order_codes if order_code != ""
    ]
    assert non_blank_parts_order_codes[0] == test_part_order_code

    non_blank_partsdnp_order_codes = [
        order_code for order_code in partsdnp.order_codes if order_code != ""
    ]
    assert non_blank_partsdnp_order_codes[0] == test_part_order_code

    # Testing it retrieves the correct manufacturer (blank entries removed)
    non_blank_parts_manf = [manf for manf in parts.manufacturers if manf != ""]
    assert non_blank_parts_manf[0] == test_part_manf

    non_blank_partsdnp_manf = [manf for manf in partsdnp.manufacturers if manf != ""]
    assert non_blank_partsdnp_manf[0] == test_part_manf


def test_parts_return_empty():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=True)

    parts = Parts("DigiKey", net_obj, True, "GBP", ["Generic"], 1)

    empty_list = [""] * net_obj.group_count

    assert parts.stock == empty_list
    assert parts.order_codes == empty_list
    assert parts.manufacturers == empty_list
    assert parts.supplier == empty_list
    assert parts.quantity == empty_list
    assert parts.price_tiers == empty_list
    assert parts.price == empty_list
    assert parts.currency == empty_list


def test_write_to_file():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project2_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"
    test_csv2_path = dir_path + "\\test-project2.csv"
    test_html2_path = dir_path + "\\test-project2.html"
    test_txt2_path = dir_path + "\\test-project2.txt"
    kicad_netlist_reader.comp.__eq__ = get_equ("Value,Footprint,MPN,DNP,Rating", "", "")
    net_obj = Net(test_project2_path, excludeBoard=True, excludeBOM=True)
    primary_parts = Parts("Mouser", net_obj, False, "GBP", ["Generic"], 1)
    secondary_parts = Parts("DigiKey", net_obj, False, "GBP", ["Generic"], 1)
    file_data = PartsFileData(primary_parts, secondary_parts)
    columns = get_columns("", "default") + ["Rating", "Test"]

    f = open_output_file("test-project2.csv")
    write_to_file(f, "csv", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_csv2_path) == True
    os.remove("test-project2.csv")

    f = open_output_file("test-project2.html")
    write_to_file(f, "html", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_html2_path) == True
    os.remove("test-project2.html")

    f = open_output_file("test-project2.txt")
    write_to_file(f, "txt", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_txt2_path) == True
    os.remove("test-project2.txt")

    # INFO:
    # Test the file content with test-project1 which is a bigger project
    # If these tests fail maybe something changed in the API results like an order code or price
    # Only way to fully verify the tool works is to manually check that the output is correct
    test_project1_path = dir_path + "\\test-projects\\test-project1\\test-project1.xml"
    net_obj = Net(test_project1_path, excludeBoard=True, excludeBOM=True)
    primary_parts = Parts("Mouser", net_obj, False, "GBP", ["Generic"], 1)
    secondary_parts = Parts("DigiKey", net_obj, False, "GBP", ["Generic"], 1)
    file_data = PartsFileData(primary_parts, secondary_parts)
    columns = get_columns("", "default") + ["Rating"]
    # Prices fluctuate so the test can fail
    columns.remove("Unit/Reel Price")
    columns.remove("Total Price")

    # INFO:
    # When viewing and saving the *-expected.csv, Excel reformats it
    # by removing quotes and shortening numerical strings therefore be
    # careful when opening that file and make sure no edits are made
    f = open_output_file("test-project1.csv")
    write_to_file(f, "csv", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.csv", encoding="utf8").read().replace('"', "")
    expected_contents = (
        open("test-project1-expected.csv", encoding="utf8").read().replace('"', "")
    )
    assert actual_contents == expected_contents
    os.remove("test-project1.csv")

    f = open_output_file("test-project1.html")
    write_to_file(f, "html", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.html").read()
    expected_contents = open("test-project1-expected.html").read()
    assert actual_contents == expected_contents
    os.remove("test-project1.html")

    f = open_output_file("test-project1.txt")
    write_to_file(f, "txt", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.txt").read()
    expected_contents = open("test-project1-expected.txt").read()
    assert actual_contents == expected_contents
    os.remove("test-project1.txt")

    # INFO:
    # Test project 3 contains no DNP components which is important to test
    test_project3_path = dir_path + "\\test-projects\\test-project3\\test-project3.xml"
    net_obj = Net(test_project3_path, excludeBoard=True, excludeBOM=True)
    primary_parts = Parts("Mouser", net_obj, False, "GBP", ["Generic"], 1)
    secondary_parts = Parts("DigiKey", net_obj, False, "GBP", ["Generic"], 1)
    file_data = PartsFileData(primary_parts, secondary_parts)
    columns = get_columns("", "default") + ["Rating"]
    # Prices fluctuate so the test can fail
    columns.remove("Unit/Reel Price")
    columns.remove("Total Price")

    f = open_output_file("test-project3.csv")
    write_to_file(f, "csv", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project3.csv", encoding="utf8").read().replace('"', "")
    expected_contents = (
        open("test-project3-expected.csv", encoding="utf8").read().replace('"', "")
    )
    assert actual_contents == expected_contents
    os.remove("test-project3.csv")


def test_get_equ():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    net_obj = Net(test_project_path, excludeBoard=False, excludeBOM=False)
    group_fields = "Value,Footprint,DNP,MPN,Rating,Test"
    equ = get_equ(group_fields, "", "")

    # INFO:
    # False means the components are not equal and therefore should not be grouped.
    # True means they are equal and therefore group them
    assert equ(net_obj.components[1], net_obj.components[2]) == False
    assert equ(net_obj.components[3], net_obj.components[4]) == True
    assert equ(net_obj.components[0], net_obj.components[1]) == False
    assert (
        equ(net_obj.components[0], net_obj.dnp.components[0]) == False
    )  # Notice here how it's false but in the next tests it's true

    group_fields = "Value,Footprint,MPN,Rating,Test"
    equ = get_equ(group_fields, "", "")

    assert equ(net_obj.components[1], net_obj.components[2]) == False
    assert equ(net_obj.components[3], net_obj.components[4]) == True
    assert equ(net_obj.components[0], net_obj.components[1]) == False
    assert equ(net_obj.components[0], net_obj.dnp.components[0]) == True

    # Check if it fails properly when inputting >MAX_GROUP_FIELDS
    group_fields = "Value,Footprint,MPN,Rating,Test,Test,Test,Test,Test,Test"
    with pytest.raises(SystemExit) as exc_info:
        get_equ(group_fields, "", "")

    assert exc_info.value.code == 1

    # Check if it fails properly when not inputting Value or Footprint
    group_fields = "MPN,Rating,Test"
    with pytest.raises(SystemExit) as exc_info:
        get_equ(group_fields, "", "")

    assert exc_info.value.code == 1

    group_fields = "Footprint,MPN,Rating,Test"
    with pytest.raises(SystemExit) as exc_info:
        get_equ(group_fields, "", "")

    assert exc_info.value.code == 1

    group_fields = "Value,MPN,Rating,Test"
    with pytest.raises(SystemExit) as exc_info:
        get_equ(group_fields, "", "")

    assert exc_info.value.code == 1


def test_remove_ignore_mpn_parts():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project3\\test-project3.xml"

    net_obj = Net(test_project_path, excludeBoard=True, excludeBOM=True)

    ignore_mpns = ["Generic"]

    net_obj.grouped = remove_ignore_mpn_parts(net_obj.grouped, ignore_mpns)
    net_obj.refdes_groups = net_obj.get_refdes_from_net(net_obj.grouped)

    assert net_obj.refdes_groups == [["BT1"], ["D1"]]


def test_download_datasheets():
    dir_path = os.path.dirname(os.path.realpath(__file__))

    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"
    test_datasheet_path = dir_path + "\\datasheets\\HSMW-C170-U0000-DS100.pdf"
    test_datasheet_folder_path = dir_path + "\\datasheets"

    net_obj = Net(test_project_path, excludeBoard=False, excludeBOM=False)

    download_datasheets(net_obj.grouped, downloads_folder="datasheets")

    assert os.path.isfile(test_datasheet_path) == True

    os.remove(test_datasheet_path)
    os.rmdir(test_datasheet_folder_path)


def test_main():
    dir_path = os.path.dirname(os.path.realpath(__file__))
    test_project_path = dir_path + "\\test-projects\\test-project2\\test-project2.xml"

    argv = [test_project_path, "test-out.csv", "-d", "-q"]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 0

    argv = [test_project_path, "test-out.csv", "-k", "-q"]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 0

    argv = [test_project_path, "test-out.csv", "--remove-ignore-mpn-parts", "-q"]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 0

    # Testing for no config.yaml
    config_path = dir_path + "\\..\\src\\config.yaml"
    rename_path = dir_path + "\\..\\src\\aconfig.yaml"
    os.rename(config_path, rename_path)

    argv = [test_project_path, "test-out.csv", "-q"]
    with pytest.raises(SystemExit) as exc_info:
        main(argv)

    assert exc_info.value.code == 0
    os.rename(rename_path, config_path)

    os.remove("test-out.csv")
