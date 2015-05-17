import os
import sys
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
from polib import polib
from lxml import etree as ET
from PIL import Image
from Utils import *
import json
from InfoProvider import InfoProvider
INFOS = InfoProvider()

settings = """{
    "kodi_path": "C:/Kodi",
    "portable_mode": true
}"""


def check_tags(tag_type):
    if tag_type == "variable":
        errors = INFOS.check_variables()
    elif tag_type == "include":
        errors = INFOS.check_includes()
    elif tag_type == "font":
        errors = INFOS.check_fonts()
    elif tag_type == "label":
        errors = INFOS.check_labels()
    for e in errors:
        content = e["message"].encode(sys.stdout.encoding, errors='replace').decode("utf-8")
        print(content)
        print("%s: line %s\n" % (e["file"], str(e["line"])))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        project_folder = sys.argv[1]
    else:
        project_folder = input("Enter Path to skin: ")
    INFOS.get_settings(json.loads(settings))
    INFOS.get_builtin_label()
    INFOS.init_addon(project_folder)
    if INFOS.xml_folders:
        INFOS.update_xml_files()
        for folder in INFOS.xml_folders:
            for xml_file in INFOS.window_file_list[folder]:
                path = os.path.join(INFOS.project_path, folder, xml_file)
                check_bom(path)
        print("\n\nINCLUDE CHECK\n\n")
        check_tags("include")
        print("\n\nVARIABLE CHECK\n\n")
        check_tags("variable")
        print("\n\nFONT CHECK\n\n")
        check_tags("font")
        print("\n\nLABEL CHECK\n\n")
        check_tags("label")
        listitems = INFOS.check_values()
        for e in listitems:
            print(e["message"])
            print(e["file"] + "\n")
