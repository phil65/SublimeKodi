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
        undefined_refs, unused_defs = INFOS.check_variables()
    elif tag_type == "include":
        undefined_refs, unused_defs = INFOS.check_includes()
    elif tag_type == "font":
        undefined_refs, unused_defs = INFOS.check_fonts()
    elif tag_type == "label":
        undefined_refs, unused_defs = INFOS.check_labels()
    for e in undefined_refs:
        print("Undefined %s reference: %s" % (tag_type, e["name"]))
        print(e["file"] + ": " + str(e["line"]))
        print("")
    for e in unused_defs:
        print("Unused %s definition: %s" % (tag_type, e["name"]))
        print(e["file"] + ": line " + str(e["line"]))
        print("")

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
        check_tags("include")
        check_tags("variable")
        check_tags("font")
        check_tags("label")
        listitems = INFOS.check_values()
        for e in listitems:
            print(e["message"][0])
            print(e["message"][1])
            print("")

