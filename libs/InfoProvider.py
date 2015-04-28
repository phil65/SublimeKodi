import os
from lxml import etree as ET
from Utils import *
import sublime


class InfoProvider():

    def __init__(self):
        self.include_list = []
        self.var_list = []
        self.include_file_list = []

    def update_variable_list(self, view):
        if view.file_name():
            # sublime.message_dialog("updated var list")
            path, filename = os.path.split(view.file_name())
            include_file = os.path.join(path, "Variables.xml")
            if os.path.exists(include_file):
                parser = ET.XMLParser(remove_blank_text=True)
                tree = ET.parse(include_file, parser)
                root = tree.getroot()
                self.var_list = []
                for node in root.findall("variable"):
                    var = {"name": node.attrib["name"],
                           "file": include_file,
                           "line": node.sourceline}
                    self.var_list.append(var)

    def get_include_files(self, view):
        path, filename = os.path.split(view.file_name())
        include_file = os.path.join(path, "Includes.xml")
        if os.path.exists(include_file):
            parser = ET.XMLParser(remove_blank_text=True)
            tree = ET.parse(include_file, parser)
            root = tree.getroot()
            self.include_file_list = [include_file]
            for node in root.findall("include"):
                if "file" in node.attrib:
                    self.include_file_list.append(os.path.join(path, node.attrib["file"]))
            log("File List" + str(self.include_file_list))

    def update_include_list(self, view):
        self.get_include_files(view)
        self.include_list = []
        for path in self.include_file_list:
            if os.path.exists(path):
                parser = ET.XMLParser(remove_blank_text=True)
                tree = ET.parse(path, parser)
                root = tree.getroot()
                for node in root.findall("include"):
                    if "name" in node.attrib:
                        include = {"name": node.attrib["name"],
                                   "file": path,
                                   "line": node.sourceline}
                        self.include_list.append(include)
        log("Include List" + str(self.include_list))

    def go_to_tag(self, view):
        keyword = findWord(view)
        goto_list = self.var_list + self.include_list
        if keyword:
            log("goto list" + str(goto_list))
            for node in goto_list:
                if node["name"] == keyword:
                    sublime.active_window().open_file("%s:%s" % (node["file"], node["line"]), sublime.ENCODED_POSITION)
