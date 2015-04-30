import os
from Utils import *
import sublime
import codecs
from polib import polib


SETTINGS_FILE = 'sublimekodi.sublime-settings'
DEFAULT_LANGUAGE_FOLDER = "English"


class InfoProvider():

    def __init__(self):
        self.include_list = []
        self.include_file_list = []
        self.color_dict = {}
        self.project_path = ""
        self.xml_path = ""
        self.builtin_list = []
        self.fonts = []
        self.string_list = []
        self.xml_folders = []
        self.addon_string_list = []
        self.labels_loaded = False
        self.settings_loaded = False

    def init_addon(self, path):
        self.project_path = path
        addon_xml_file = checkPaths([os.path.join(self.project_path, "addon.xml")])
        if addon_xml_file:
            root = get_root_from_file(addon_xml_file)
            self.xml_folders = []
            for node in root.findall('.//res'):
                self.xml_folders.append(node.attrib["folder"])
            self.xml_path = os.path.join(path, self.xml_folders[0])

    def get_colors(self):
        if self.project_path:
            paths = [os.path.join(self.project_path, "colors", "defaults.xml")]
            color_file = checkPaths(paths)
            if color_file:
                log("found color file: " + color_file)
                root = get_root_from_file(color_file)
                self.color_dict = {}
                for node in root.findall("color"):
                    self.color_dict[node.attrib["name"]] = node.text
                log("color list: %i colors found" % len(self.color_dict))

    def get_fonts(self):
        if self.xml_path:
            paths = [os.path.join(self.xml_path, "Font.xml"),
                     os.path.join(self.xml_path, "font.xml")]
            self.font_file = checkPaths(paths)
            if self.font_file:
                root = get_root_from_file(self.font_file)
                self.fonts = []
                for node in root.find("fontset").findall("font"):
                    string_dict = {"name": node.find("name").text,
                                   "size": node.find("size").text,
                                   "line": node.sourceline,
                                   "content": ET.tostring(node, pretty_print=True),
                                   "filename": node.find("filename").text}
                    self.fonts.append(string_dict)

    def get_include_files(self):
        if self.xml_path:
            paths = [os.path.join(self.xml_path, "Includes.xml"),
                     os.path.join(self.xml_path, "includes.xml")]
            include_file = checkPaths(paths)
            if include_file:
                log("found include file: " + include_file)
                root = get_root_from_file(include_file)
                self.include_file_list = [include_file]
                for node in root.findall("include"):
                    if "file" in node.attrib:
                        self.include_file_list.append(os.path.join(self.xml_path, node.attrib["file"]))
                log("File List: %i files found." % len(self.include_file_list))
            else:
                log("Could not find include file")
                log(paths)

    def update_include_list(self):
        self.include_list = []
        self.get_include_files()
        for path in self.include_file_list:
            self.include_list += get_tags_from_file(path, ["include", "variable", "constant"])
            # log("%s: %i nodes" % (path, len(self.include_list)))
        log("Include List: %i nodes found." % len(self.include_list))

    def go_to_tag(self, view):
        keyword = findWord(view)
        if keyword:
            if keyword.isdigit():
                for node in self.string_list:
                    if node["id"] == "#" + keyword:
                        if int(keyword) >= 31000 and int(keyword) <= 33000:
                            file_path = self.addon_lang_path
                        else:
                            file_path = self.kodi_lang_path
                        sublime.active_window().open_file("%s:%s" % (file_path, node["line"]), sublime.ENCODED_POSITION)
                        return True
            else:
                for node in self.include_list:
                    if node["name"] == keyword:
                        sublime.active_window().open_file("%s:%s" % (node["file"], node["line"]), sublime.ENCODED_POSITION)
                        return True
                for node in self.fonts:
                    if node["name"] == keyword:
                        sublime.active_window().open_file("%s:%s" % (self.font_file, node["line"]), sublime.ENCODED_POSITION)
                        return True
                log("no node with name %s found" % keyword)

    def return_node_content(self, keyword=None, return_entry="content"):
        if keyword:
            for node in self.fonts:
                if node["name"] == keyword:
                    return node[return_entry]

            for node in self.include_list:
                if node["name"] == keyword:
                    return node[return_entry]
            log("no node with name %s found" % keyword)

    def return_label(self, view, selection):
        if selection.isdigit():
            id_string = "#" + selection
            for item in self.string_list:
                if id_string == item["id"]:
                    tooltips = item["string"]
                    if self.use_native:
                        tooltips += "<br>" + item["native_string"]
                    return tooltips
        return ""

    def get_settings(self):
        history = sublime.load_settings(SETTINGS_FILE)
        self.kodi_path = history.get("kodi_path")
        log("kodi path: " + self.kodi_path)
        self.use_native = history.get("use_native_language")
        if self.use_native:
            self.language_folder = history.get("native_language")
            log("use native language: " + self.language_folder)
        else:
            self.language_folder = DEFAULT_LANGUAGE_FOLDER
            log("use default language: English")
        self.settings_loaded = True

    def get_addon_lang_file(self, path):
        paths = [os.path.join(path, "resources", "language", self.language_folder, "strings.po"),
                 os.path.join(path, "language", self.language_folder, "strings.po")]
        self.addon_lang_path = checkPaths(paths)
        if self.addon_lang_path:
            return codecs.open(self.addon_lang_path, "r", "utf-8").read()
        else:
            log("Could not find addon language file")
            log(paths)
            return ""

    def get_kodi_lang_file(self):
        paths = [os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po"),
                 os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")]
        self.kodi_lang_path = checkPaths(paths)
        if self.kodi_lang_path:
            return codecs.open(self.kodi_lang_path, "r", "utf-8").read()
        else:
            log("Could not find kodi language file")
            log(paths)
            return ""

    def get_builtin_label(self):
        kodi_lang_file = self.get_kodi_lang_file()
        if kodi_lang_file:
            po = polib.pofile(kodi_lang_file)
            self.builtin_list = []
            for entry in po:
                string = {"id": entry.msgctxt,
                          "line": entry.linenum,
                          "string": entry.msgid,
                          # "file": self.kodi_lang_path,
                          "native_string": entry.msgstr}
                self.builtin_list.append(string)
            self.labels_loaded = True
            log("Builtin labels loaded. Amount: %i" % len(self.builtin_list))

    def update_labels(self):
        if self.project_path:
            lang_file = self.get_addon_lang_file(self.project_path)
            po = polib.pofile(lang_file)
            log("Update labels for: %s" % self.project_path)
            self.addon_string_list = []
            for entry in po:
                string = {"id": entry.msgctxt,
                          "line": entry.linenum,
                          "string": entry.msgid,
                          # "file": self.addon_lang_path,
                          "native_string": entry.msgstr}
                self.addon_string_list.append(string)
            self.string_list = self.builtin_list + self.addon_string_list
            log("Addon Labels updated. Amount: %i" % len(self.addon_string_list))
