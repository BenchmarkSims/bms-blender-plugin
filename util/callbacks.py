import xml.etree.ElementTree as ET

"""Utility to update the existing callbacks.xml with a list of new callbacks"""


def merge_callbacks_txt_with_callbacks_xml(
    callbacks_txt_file_path, callbacks_xml_file_path, output_file_path
):
    with open(callbacks_txt_file_path, "r") as names_file:
        names = names_file.read().splitlines()

    tree = ET.parse(callbacks_xml_file_path)
    root = tree.getroot()

    new_callbacks = 0
    for callback_name in names:
        found = False
        for callback in root.findall("Callback"):
            name_element = callback.find("Name")
            if name_element is not None and name_element.text == callback_name:
                found = True
                break

        if not found and callback_name.strip() != "":
            new_callback = ET.SubElement(root, "Callback")
            name = ET.SubElement(new_callback, "Name")
            name.text = callback_name

            description = ET.SubElement(new_callback, "Description")
            description.text = "Automatically added"

            new_callbacks += 1

    ET.indent(tree, space="\t", level=0)
    tree.write(output_file_path, encoding="utf-8", xml_declaration=True)
    print(f"parsed file, added {new_callbacks} new callbacks")

    xml_names = set()

    for callback in root.findall("Callback"):
        name_element = callback.find("Name")
        if name_element is not None:
            xml_names.add(name_element.text)

    missing_names = xml_names.difference(names)

    if missing_names:
        print(
            f"Elements present in XML but missing in the text file ({len(missing_names)}):"
        )
        for name in missing_names:
            print(name)
    else:
        print("All elements in the XML file are present in the text file.")


merge_callbacks_txt_with_callbacks_xml(
    "callbacks.txt",
    "callbacks.xml",
    "../../../.config/JetBrains/PyCharm2023.2/scratches/callbacks_updated.xml",
)
