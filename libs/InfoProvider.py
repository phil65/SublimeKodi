import os
from lxml import etree as ET
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
        self.id_list = []
        self.string_list = []
        self.native_string_list = []
        self.builtin_id_list = []
        self.builtin_string_list = []
        self.builtin_native_string_list = []
        self.labels_loaded = False
        self.settings_loaded = False

    def init_addon(self, path):
        self.project_path = path
        paths = [os.path.join(self.project_path, "1080i"),
                 os.path.join(self.project_path, "720p")]
        self.xml_path = checkPaths(paths)

    def get_colors(self):
        if self.project_path:
            paths = [os.path.join(self.project_path, "colors", "defaults.xml")]
            color_file = checkPaths(paths)
            if color_file:
                log("found color file: " + color_file)
                parser = ET.XMLParser(remove_blank_text=True)
                tree = ET.parse(color_file, parser)
                root = tree.getroot()
                self.color_dict = {}
                for node in root.findall("color"):
                    self.color_dict[node.attrib["name"]] = node.text
                log("color list: %i colors found" % len(self.color_dict))

    def get_include_files(self):
        if self.project_path:
            paths = [os.path.join(self.xml_path, "Includes.xml"),
                     os.path.join(self.xml_path, "includes.xml")]
            include_file = checkPaths(paths)
            if include_file:
                log("found include file: " + include_file)
                parser = ET.XMLParser(remove_blank_text=True)
                tree = ET.parse(include_file, parser)
                root = tree.getroot()
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
            log("include_list" + str(self.include_list))
            for node in self.include_list:
                if node["name"] == keyword:
                    sublime.active_window().open_file("%s:%s" % (node["file"], node["line"]), sublime.ENCODED_POSITION)
                    return True
            log("no node with name %s found" % keyword)

    def return_label(self, view, selection):
        if selection.isdigit():
            id_string = "#" + selection
            if id_string in self.id_list:
                index = self.id_list.index(id_string)
                tooltips = self.string_list[index]
                if self.use_native:
                    tooltips += "<br>" + self.native_string_list[index]
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
        path = checkPaths(paths)
        if path:
            return codecs.open(path, "r", "utf-8").read()
        else:
            log("Could not find addon language file")
            log(paths)
            return ""

    def get_kodi_lang_file(self):
        paths = [os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po"),
                 os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")]
        path = checkPaths(paths)
        if path:
            return codecs.open(path, "r", "utf-8").read()
        else:
            log("Could not find kodi language file")
            log(paths)
            return ""

    def get_builtin_label(self):
        kodi_lang_file = self.get_kodi_lang_file()
        if kodi_lang_file:
            po = polib.pofile(kodi_lang_file)
            self.builtin_id_list = []
            self.builtin_string_list = []
            self.builtin_native_string_list = []
            for entry in po:
                self.builtin_id_list.append(entry.msgctxt)
                self.builtin_string_list.append(entry.msgid)
                self.builtin_native_string_list.append(entry.msgstr)
            self.labels_loaded = True
            log("Builtin labels loaded. Amount: %i" % len(self.builtin_string_list))

    def update_labels(self):
        if self.project_path:
            self.id_list = self.builtin_id_list
            self.string_list = self.builtin_string_list
            self.native_string_list = self.builtin_native_string_list
            lang_file = self.get_addon_lang_file(self.project_path)
            po = polib.pofile(lang_file)
            log("Update labels for: %s" % self.project_path)
            for entry in po:
                self.builtin_id_list.append(entry.msgctxt)
                self.builtin_string_list.append(entry.msgid)
                self.builtin_native_string_list.append(entry.msgstr)
            log("Labels updated. Amount: %i" % len(self.id_list))
