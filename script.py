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
project_folder = "C:\\Kodi\\portable_data\\addons\\skin.xperience1080"
settings = """{
    "kodi_path": "C:/Kodi",
    "portable_mode": true,
    "use_native_language": false,
    "native_language": "Chinese (Simple)",
    "kodi_address": "http://localhost:8080",
    "kodi_username": "kodi",
    "kodi_password": "",
    "auto_reload_skin": true,
    "tooltip_height": 300,
    "tooltip_width": 1000,
    "tooltip_delay": 0,
    "auto_skin_check": true

}"""


def check_tags(tag_type):
    if tag_type == "variable":
        undefined_refs, unused_defs = INFOS.check_variables()
    elif tag_type == "include":
        undefined_refs, unused_defs = INFOS.check_includes()
    elif tag_type == "font":
        undefined_refs, unused_defs = INFOS.check_fonts()
    for e in undefined_refs:
        print("Undefined %s reference: %s" % (tag_type, e["name"]))
        print(e["file"] + ": " + str(e["line"]))
        print("")
    for e in unused_defs:
        print("Unused %s definition: %s" % (tag_type, e["name"]))
        print(e["file"] + ": line " + str(e["line"]))
        print("")

if __name__ == "__main__":
    INFOS.get_settings(json.loads(settings))
    INFOS.get_builtin_label()
    INFOS.init_addon(project_folder)
    if INFOS.xml_folders:
        INFOS.update_xml_files()
        check_tags("include")
        check_tags("variable")
        check_tags("font")
        listitems = INFOS.check_values()
        for e in listitems:
            print(e["message"][0])
            print(e["message"][1])
            print("")

