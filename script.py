import os
import sys
import platform
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
libs_platform_path = os.path.join(__path__, 'libs-winlin')
if platform.system() == "Darwin":
    libs_platform_path = os.path.join(__path__, "libs-mac")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
if libs_platform_path not in sys.path:
    sys.path.insert(0, libs_platform_path)
from Utils import *
import json
from InfoProvider import InfoProvider
import codecs
import chardet
INFOS = InfoProvider()
RESULTS_FILE = "results.txt"

settings = """{
    "kodi_path": "C:/Kodi",
    "portable_mode": true,
    "language_folders": ["English", "resource.language.en_gb"]
}"""


def log(text):
    """
    logs text to both file and console
    """
    with codecs.open(RESULTS_FILE, "a", encoding='utf-8') as myfile:
        myfile.write(str(text) + "\n")
    try:
        print(text)
    except:
        print(text.encode(sys.stdout.encoding, errors='replace').decode("utf-8"))


def check_tags(check_type):
    """
    triggers of test of type "check_type", then formats and logs them
    """
    errors = INFOS.get_check_listitems(check_type)
    for e in errors:
        log(e["message"])
        path = "/".join(e["file"].split(os.sep)[-2:])
        log("%s: line %s\n" % (path, str(e["line"])))


def get_addons(reponames):
    """
    get available addons from the kodi addon repository
    """
    repo_list = 'http://mirrors.kodi.tv/addons/%s/addons.xml'
    addons = {}
    for reponame in reponames:
        req = urlopen(repo_list % reponame)
        data = req.read()
        req.close()
        root = ET.fromstring(data)
        for item in root.iter('addon'):
            addons[item.get('id')] = item.get('version')
    return addons


def check_dependencies(skinpath):
    """
    validate the addon dependencies
    """
    RELEASES = [{"version": '5.0.1',
                 "name": "gotham",
                 "allowed_addons": ['gotham']},
                {"version": '5.3.0',
                 "name": "helix",
                 "allowed_addons": ['gotham', 'helix']},
                {"version": '5.9.0',
                 "name": "isengard",
                 "allowed_addons": ['gotham', 'helix', 'isengard']}]
    imports = {}
    str_releases = " / ".join([item["name"] for item in RELEASES])
    repo = input('Enter Kodi version (%s): ' % str_releases)
    root = get_root_from_file(os.path.join(skinpath, 'addon.xml'))
    for item in root.iter('import'):
        imports[item.get('addon')] = item.get('version')
    for release in RELEASES:
        if repo == release["name"]:
            if imports['xbmc.gui'] > release["version"]:
                log('xbmc.gui version incorrect')
            addons = get_addons(release["allowed_addons"])
            break
    else:
        log('You entered an invalid Kodi version')
    del imports['xbmc.gui']
    for dep, ver in imports.items():
        if dep in addons:
            if ver > addons[dep]:
                log('%s version higher than in Kodi repository' % dep)
        else:
            log('%s not available in Kodi repository' % dep)


if __name__ == "__main__":
    from eol import eol
    open(RESULTS_FILE, 'w').close()
    if len(sys.argv) == 2:
        project_folder = sys.argv[1]
    else:
        project_folder = input("Enter Path to skin: ")
    INFOS.get_settings(json.loads(settings))
    INFOS.update_builtin_labels()
    INFOS.init_addon(project_folder)
    INFOS.update_xml_files()
    INFOS.check_xml_files()
    for path in INFOS.file_list_generator():
        if check_bom(path):
            log("found BOM. File: " + path)
        try:
            text = codecs.open(path, "rb", encoding='utf-8', errors="strict").read()
        except:
            log("Error when trying to read %s as UTF-8" % path)
            rawdata = codecs.open(path, "rb", errors="ignore").read()
            encoding = chardet.detect(rawdata)
            log("detected encoding: %s" % encoding["encoding"])
            text = codecs.open(path, "rb", encoding=encoding["encoding"]).read()
    result = eol.eol_info_from_path_patterns([project_folder], recursive=True, includes=[], excludes=['.svn', '.git'])
    for item in result:
        if item[1] == '\n' or None:
            continue
        elif item[1] == '\r':
            log("MAC Line Endings detected in " + item[0])
        else:
            log("Windows Line Endings detected in " + item[0])
    log("\n\nADDON DEPENDENCY CHECK\n\n")
    check_dependencies(project_folder)
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
