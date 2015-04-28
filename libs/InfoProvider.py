import os
from lxml import etree as ET
from Utils import *
import sublime


class InfoProvider():

    def __init__(self):
        self.include_list = []
        self.include_file_list = []
        self.color_list = []
        self.project_path = ""
        self.xml_path = ""

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
                self.color_list = {}
                for node in root.findall("color"):
                    self.color_list[node.attrib["name"]] = node.text
                log(self.color_list)

    def get_include_files(self, view):
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

    def update_include_list(self, view):
        self.include_list = []
        self.get_include_files(view)
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
