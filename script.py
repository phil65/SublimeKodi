import os
import sys
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
from Utils import *
import json
from InfoProvider import InfoProvider
INFOS = InfoProvider()
RESULTS_FILE = "results.txt"

settings = """{
    "kodi_path": "C:/Kodi",
    "portable_mode": true
}"""


def log(text):
    with open(RESULTS_FILE, "a") as myfile:
        myfile.write(text + "\n")
    try:
        print(text)
    except:
        print(text.encode(sys.stdout.encoding, errors='replace').decode("utf-8"))


def check_tags(tag_type):
    if tag_type == "variable":
        errors = INFOS.check_variables()
    elif tag_type == "include":
        errors = INFOS.check_includes()
    elif tag_type == "font":
        errors = INFOS.check_fonts()
    elif tag_type == "label":
        errors = INFOS.check_labels()
    elif tag_type == "general":
        errors = INFOS.check_values()
    elif tag_type == "id":
        errors = INFOS.check_ids()
    for e in errors:
        content = e["message"]
        log(content)
        path = "/".join(e["file"].split(os.sep)[-2:])
        log("%s: line %s\n" % (path, str(e["line"])))


if __name__ == "__main__":
    open(RESULTS_FILE, 'w').close()
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
                if check_bom(path):
                    log("found BOM. File: " + path)
        log("\n\nINCLUDE CHECK\n\n")
        check_tags("include")
        log("\n\nVARIABLE CHECK\n\n")
        check_tags("variable")
        log("\n\nFONT CHECK\n\n")
        check_tags("font")
        log("\n\nLABEL CHECK\n\n")
        check_tags("label")
        log("\n\nID CHECK\n\n")
        check_tags("id")
        log("\n\nCHECK FOR COMMON MISTAKES\n\n")
        check_tags("general")

