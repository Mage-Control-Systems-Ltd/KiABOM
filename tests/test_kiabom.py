from src.kiabom import *
from unittest.mock import mock_open, patch
import pytest
import os
from pathlib import Path
import pickle

# NOTE: If the tests that use pickle require re-writing for new data, they should be
# run normally with the API keys, and then pickle should be used to cache the new API
# result. This result should then be loaded for the test

def test_print_title_screen():
    print_title_screen()  # not really sure how to test this but it's good for coverage
    assert True


def test_open_output_file():
    output_file = "test.txt"

    m = mock_open()

    with patch("builtins.open", m):  # Patch open during this context
        f = open_output_file(output_file)

    # Assert open was used with 'w', encoding="utf-8-sig", newline=""
    test_path = os.path.normpath(output_file)
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
        output_format = "csv"

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

    args.output_format = ""
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


def test_has_internet():
    assert has_internet() == True
    assert has_internet("", timeout=1) == False


def test_get_columns():
    columns = ""
    preset = "default"

    columns_ret = get_columns(columns, preset)
    assert columns_ret == column_preset_dict["default"]

    preset = "test"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == [""]

    preset = "Minimal"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == column_preset_dict["minimal"]

    preset = "no-apI"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == column_preset_dict["no-api"]

    preset = "primary-only"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == column_preset_dict["primary-only"]

    preset = "MAGE"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == column_preset_dict["mage"]

    columns = "a,b,c"
    columns_ret = get_columns(columns, preset)
    assert columns_ret == ["a", "b", "c"]


def test_kicadnetlist_class():
    dir_path = Path(__file__).resolve().parent
    test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"

    with pytest.raises(SystemExit) as exc_info:
        net_obj = KiCadNetlist(
            "\\random\\path\\that\\will\\fail.xml", excludeBoard=True, excludeBOM=True, DNP=False
        )
    assert exc_info.value.code == 1

    net_obj = KiCadNetlist(test_project_path, excludeBoard=True, excludeBOM=True, DNP=False)
    expected_refdes_groups = [['BT1'], ['BT2'], ['D1'], ['D2'], ['R1'], ['R2']]

    assert expected_refdes_groups == net_obj.refdes_groups

    net_obj = KiCadNetlist(test_project_path, excludeBoard=False, excludeBOM=True, DNP=True)
    expected_refdes_groups = [["BT1"], ["D1"], ["H2"], ["R1"]]

    assert expected_refdes_groups == net_obj.refdes_groups

    net_obj = KiCadNetlist(test_project_path, excludeBoard=True, excludeBOM=False, DNP=True)
    expected_refdes_groups = [["BT1"], ["D1"], ["H1"], ["R1"]]

    assert expected_refdes_groups == net_obj.refdes_groups

    net_obj = KiCadNetlist(test_project_path, excludeBoard=False, excludeBOM=False, DNP=True)
    expected_refdes_groups = [["BT1"], ["D1"], ["H1", "H2", "H3"], ["R1"]]

    assert expected_refdes_groups == net_obj.refdes_groups

    ignore_mpns = ["Generic"]

    net_obj.remove_ignore_mpn_parts(ignore_mpns)

    assert net_obj.refdes_groups == [["BT1"], ["D1"], ["H1", "H2", "H3"]]


def test_apiparts_mouser():
    api_status = init_apis()
    assert api_status == {"mouser": "success", "digikey": "success"}


    with open("test_api_cache/test_apiparts_mouser.pickle", 'rb') as f:
        parts = pickle.load(f)
        # This simulates the following code snippet
        # api_status = init_apis()
        # dir_path = Path(__file__).resolve().parent
        # test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"
        # net_obj = KiCadNetlist(test_project_path, excludeBoard=True, excludeBOM=True, DNP=False)
        # parts = ApiParts("Mouser", net_obj, "GBP", ["Generic"], api_status)

    assert parts.comp_count == 2

    # Order code is based on MPN used for the LED in the test project. Taken from Mouser directly.
    test_part_order_code = "630-HSMW-C170-U0000"
    test_part_manf = "Broadcom / Avago"

    # Testing it retrieves the correct order code and manf (blank entries removed)
    non_blank_parts = [ part for part in parts.parts_list if part.get("Order Code") ]
    assert non_blank_parts[0].get("Order Code") == test_part_order_code
    assert non_blank_parts[0].get("Manufacturer") == test_part_manf


def test_apiparts_digikey():
    with open("test_api_cache/test_apiparts_digikey.pickle", 'rb') as f:
        parts = pickle.load(f)
        # This simulates the following code snippet
        # api_status = init_apis()
        # dir_path = Path(__file__).resolve().parent
        # test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"
        # net_obj = KiCadNetlist(test_project_path, excludeBoard=True, excludeBOM=True, DNP=False)
        # parts = ApiParts("DigiKey", net_obj, "GBP", ["Generic"], api_status)

    # Order code is based on MPN used for the LED in the test project. Taken from Mouser directly.
    test_part_order_code = "516-3993-1-ND"
    test_part_manf = "Broadcom Limited"

    # Testing it retrieves the correct order code and manf (blank entries removed)
    non_blank_parts = [ part for part in parts.parts_list if part.get("Order Code") ]
    assert non_blank_parts[0].get("Order Code") == test_part_order_code
    assert non_blank_parts[0].get("Manufacturer") == test_part_manf


def test_apiparts_return_empty():
    dir_path = Path(__file__).resolve().parent
    test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"

    net_obj = KiCadNetlist(test_project_path, excludeBoard=True, excludeBOM=True, DNP=False)

    with open("test_api_cache/test_apiparts_return_empty.pickle", 'rb') as f:
        parts = pickle.load(f)

    empty_list = [{}] * net_obj.group_count

    assert parts.parts_list == empty_list

def test_write_to_file():
    api_status = init_apis()
    assert api_status == {"mouser": "success", "digikey": "success"}

    kicad_netlist_reader.comp.__eq__ = get_equ("Value,Footprint,MPN,DNP,Rating", "", "")

    dir_path = Path(__file__).resolve().parent
    test_project2_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"
    net_obj = KiCadNetlist(test_project2_path, excludeBoard=True, excludeBOM=True, DNP=False)

    # Pickle replaces: primary_parts = ApiParts("Mouser", net_obj, "GBP", ["Generic"], api_status)
    with open('test_api_cache/test_write_to_file_mouser.pickle', 'rb') as f:
        primary_parts = pickle.load(f)

    # Pickle replaces secondary_parts = ApiParts("DigiKey", net_obj, "GBP", ["Generic"], api_status)
    with open('test_api_cache/test_write_to_file_digikey.pickle', 'rb') as f:
        secondary_parts = pickle.load(f)

    file_data = BomData(primary_parts, secondary_parts, net_obj.refdes_groups, 1)
    columns = get_columns("", "default") + ["Rating", "Test"]

    test_csv2_path = dir_path / "test-project2.csv"
    f = open_output_file(str(test_csv2_path))
    write_to_file(f, "csv", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_csv2_path) == True
    os.remove(test_csv2_path)

    test_html2_path = dir_path / "test-project2.html"
    f = open_output_file(str(test_html2_path))
    write_to_file(f, "html", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_html2_path) == True
    os.remove(test_html2_path)

    test_txt2_path = dir_path / "test-project2.txt"
    f = open_output_file(str(test_txt2_path))
    write_to_file(f, "txt", True, True, True, 1, columns, net_obj, file_data)
    f.close()
    assert os.path.isfile(test_txt2_path) == True
    os.remove(test_txt2_path)

# Very important test
def test_contents():
    kicad_netlist_reader.comp.__eq__ = get_equ("Value,Footprint,MPN,DNP,Rating", "", "")
    dir_path = Path(__file__).resolve().parent

    # Test the file content with test-project1 which is a bigger project
    test_project1_path = dir_path / "test-projects" / "test-project1" / "test-project1.xml"
    net_obj = KiCadNetlist(test_project1_path, excludeBoard=True, excludeBOM=True, DNP=False)

    # Load the cache instead of calling the objects
    with open('test_api_cache/test_contents_project1_mouser.pickle', 'rb') as f:
        primary_parts = pickle.load(f)
    with open('test_api_cache/test_contents_project1_digikey.pickle', 'rb') as f:
        secondary_parts = pickle.load(f)

    file_data = BomData(primary_parts, secondary_parts, net_obj.refdes_groups, 1)
    columns = get_columns("", "default") + ["Rating"]
    columns.remove("Unit/Reel Price")
    columns.remove("Total Price")

    # INFO: When viewing and saving the *-expected.csv, Excel reformats it
    # by removing quotes and shortening numerical strings therefore be
    # careful when opening that file and make sure no edits are made
    f = open_output_file("test-project1.csv")
    write_to_file(f, "csv", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.csv", encoding="utf8").read().replace('"', "")
    expected_contents = (
        open("tests/test-project1-expected.csv", encoding="utf8").read().replace('"', "")
    )
    assert actual_contents == expected_contents
    os.remove("test-project1.csv")

    f = open_output_file("test-project1.html")
    write_to_file(f, "html", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.html").read()
    expected_contents = open("tests/test-project1-expected.html").read()
    assert actual_contents == expected_contents
    os.remove("test-project1.html")

    f = open_output_file("test-project1.txt")
    write_to_file(f, "txt", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project1.txt").read()
    expected_contents = open("tests/test-project1-expected.txt").read()
    assert actual_contents == expected_contents
    os.remove("test-project1.txt")

    # Test project 3 contains no DNP components which is important to test
    test_project3_path = dir_path / "test-projects" / "test-project3" / "test-project3.xml"
    net_obj = KiCadNetlist(test_project3_path, excludeBoard=True, excludeBOM=True, DNP=False)

    with open('test_api_cache/test_contents_project3_mouser.pickle', 'rb') as f:
        primary_parts = pickle.load(f)

    with open('test_api_cache/test_contents_project3_digikey.pickle', 'rb') as f:
        secondary_parts = pickle.load(f)

    file_data = BomData(primary_parts, secondary_parts, net_obj.refdes_groups, 1)

    columns = get_columns("", "default") + ["Rating"]
    # Prices fluctuate so the test can fail
    columns.remove("Unit/Reel Price")
    columns.remove("Total Price")

    f = open_output_file("test-project3.csv")
    write_to_file(f, "csv", True, False, False, 2, columns, net_obj, file_data)
    f.close()
    actual_contents = open("test-project3.csv", encoding="utf8").read().replace('"', "")
    expected_contents = (
        open("tests/test-project3-expected.csv", encoding="utf8").read().replace('"', "")
    )
    assert actual_contents == expected_contents
    os.remove("test-project3.csv")


def test_get_equ():
    dir_path = Path(__file__).resolve().parent
    test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"

    net_obj = KiCadNetlist(test_project_path, excludeBoard=False, excludeBOM=False, DNP=False)
    group_fields = "Value,Footprint,DNP,MPN,Rating,Test"
    equ = get_equ(group_fields, "", "")

    # False means the components are not equal and therefore should not be grouped.
    # True means they are equal and therefore group them
    # Components net_obj.components list  ['BT1', 'BT2', 'D1', 'D2', 'H1', 'H2', 'H3', 'R1', 'R2'] == []
    assert equ(net_obj.components[0], net_obj.components[1]) == False
    assert equ(net_obj.components[2], net_obj.components[3]) == False
    assert equ(net_obj.components[4], net_obj.components[5]) == False
    assert equ(net_obj.components[0], net_obj.components[2]) == False

    group_fields = "Value,Footprint,MPN,Rating,Test"
    equ = get_equ(group_fields, "", "")

    assert equ(net_obj.components[0], net_obj.components[1]) == True
    assert equ(net_obj.components[2], net_obj.components[3]) == True
    assert equ(net_obj.components[4], net_obj.components[5]) == False
    assert equ(net_obj.components[1], net_obj.components[3]) == False

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



def test_download_datasheets():
    dir_path = Path(__file__).resolve().parent

    test_project_path = dir_path / "test-projects" / "test-project2" / "test-project2.xml"
    test_datasheet_folder_path = dir_path / "test-datasheets"
    test_datasheet_path = test_datasheet_folder_path / "HSMW-C170-U0000-DS100.pdf"

    net_obj = KiCadNetlist(test_project_path, excludeBoard=False, excludeBOM=False, DNP=False)

    download_datasheets(net_obj.grouped, downloads_folder=test_datasheet_folder_path)

    assert os.path.isfile(test_datasheet_path) == True

    os.remove(test_datasheet_path)
    os.rmdir(test_datasheet_folder_path)


def test_init_apis():
    dir_path = Path(__file__).resolve().parent

    # Testing for no config.yaml
    config_path = dir_path / ".." / "src" / "config.yaml"
    rename_path = dir_path / ".." / "src" / "aconfig.yaml"
    os.rename(str(config_path), str(rename_path))

    with pytest.raises(SystemExit) as exc_info:
        init_apis()

    assert exc_info.value.code == 1
    os.rename(str(rename_path), str(config_path))
