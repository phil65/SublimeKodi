import os
from lxml import etree as ET
from Utils import *
import sublime


class InfoProvider():

    def __init__(self):
        self.include_list = []
        self.var_list = []
        self.include_file_list = []

    def get_include_files(self, view):
        if view.file_name():
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
                # log("File List" + str(self.include_file_list))

    def update_include_list(self, view):
        self.include_list = []
        self.get_include_files(view)
        for path in self.include_file_list:
            self.include_list += get_tags_from_file(path, ["include", "variable", "constant"])

    def go_to_tag(self, view):
        keyword = findWord(view)
        goto_list = self.var_list + self.include_list
        if keyword:
            # log("goto list" + str(goto_list))
            for node in goto_list:
                if node["name"] == keyword:
                    sublime.active_window().open_file("%s:%s" % (node["file"], node["line"]), sublime.ENCODED_POSITION)
