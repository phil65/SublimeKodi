import os
from Utils import *
import re
from PIL import Image
from polib import polib
import string

DEFAULT_LANGUAGE_FOLDER = "English"


class InfoProvider():

    def __init__(self):
        self.include_list = {}
        self.include_file_list = {}
        self.window_file_list = {}
        self.color_list = []
        self.addon_xml_file = ""
        self.addon_lang_file = ""
        self.color_file = ""
        self.project_path = ""
        self.addon_type = ""
        self.addon_name = ""
        self.builtin_list = []
        self.fonts = {}
        self.string_list = []
        self.xml_folders = []
        self.addon_string_list = []

    def init_addon(self, path):
        self.addon_type = ""
        self.addon_name = ""
        self.project_path = path
        self.addon_lang_file = ""
        self.addon_xml_file = checkPaths([os.path.join(self.project_path, "addon.xml")])
        self.xml_folders = []
        self.fonts = []
        if self.addon_xml_file:
            root = get_root_from_file(self.addon_xml_file)
            for item in root.xpath("/addon[@id]"):
                self.addon_name = item.attrib["id"]
                break
            if root.find(".//import[@addon='xbmc.python']") is None:
                self.addon_type = "skin"
                for node in root.findall('.//res'):
                    self.xml_folders.append(node.attrib["folder"])
            else:
                self.addon_type = "python"
                # TODO: parse all python skin folders correctly
                paths = [os.path.join(self.project_path, "resources", "skins", "Default", "720p"),
                         os.path.join(self.project_path, "resources", "skins", "Default", "1080i")]
                folder = checkPaths(paths)
                self.xml_folders.append(folder)
        self.update_labels()
        if self.xml_folders:
            log("Kodi project detected: " + path)
            self.update_include_list()
            self.get_colors()
            self.get_fonts()
            # sublime.status_message("SublimeKodi: successfully loaded addon")

    def media_path(self):
        paths = [os.path.join(self.project_path, "media"),
                 os.path.join(self.project_path, "resources", "skins", "Default", "media")]
        return checkPaths(paths)

    def get_colors(self):
        self.color_list = []
        color_path = os.path.join(self.project_path, "colors")
        if not self.addon_xml_file or not os.path.exists(color_path):
            return False
        for path in os.listdir(color_path):
            log("found color file: " + path)
            file_path = os.path.join(color_path, path)
            root = get_root_from_file(file_path)
            for node in root.findall("color"):
                color_dict = {"name": node.attrib["name"],
                              "line": node.sourceline,
                              "content": node.text,
                              "filename": file_path}
                self.color_list.append(color_dict)
            log("color list: %i colors found" % len(self.color_list))

    def get_fonts(self):
        if not self.addon_xml_file or not self.xml_folders:
            return False
        self.fonts = {}
        for folder in self.xml_folders:
            paths = [os.path.join(self.project_path, folder, "Font.xml"),
                     os.path.join(self.project_path, folder, "font.xml")]
            font_file = checkPaths(paths)
            if font_file:
                self.fonts[folder] = []
                root = get_root_from_file(font_file)
                for node in root.find("fontset").findall("font"):
                    string_dict = {"name": node.find("name").text,
                                   "size": node.find("size").text,
                                   "line": node.sourceline,
                                   "content": ET.tostring(node, pretty_print=True, encoding="unicode"),
                                   "file": font_file,
                                   "filename": node.find("filename").text}
                    self.fonts[folder].append(string_dict)

    def reload_skin_after_save(self, path):
        folder = path.split(os.sep)[-2]
        if folder in self.include_file_list:
            if path in self.include_file_list[folder]:
                self.update_include_list()
        if path.endswith("colors/defaults.xml"):
            self.get_colors()
        if path.endswith("ont.xml"):
            self.get_fonts()

    def update_include_list(self):
        self.include_list = {}
        for folder in self.xml_folders:
            xml_folder = os.path.join(self.project_path, folder)
            paths = [os.path.join(xml_folder, "Includes.xml"),
                     os.path.join(xml_folder, "includes.xml")]
            self.include_file_list[folder] = []
            self.include_list[folder] = []
            include_file = checkPaths(paths)
            self.update_includes(include_file)
            log("Include List: %i nodes found in '%s' folder." % (len(self.include_list[folder]), folder))

    def update_includes(self, xml_file):
        # recursive, walks through include files and updates include list and include file list
        if os.path.exists(xml_file):
            folder = xml_file.split(os.sep)[-2]
            log("found include file: " + xml_file)
            self.include_file_list[folder].append(xml_file)
            self.include_list[folder] += get_tags_from_file(xml_file, ["include", "variable", "constant"])
            root = get_root_from_file(xml_file)
            for node in root.findall("include"):
                if "file" in node.attrib and node.attrib["file"] != "script-skinshortcuts-includes.xml":
                    xml_file = os.path.join(self.project_path, folder, node.attrib["file"])
                    self.update_includes(xml_file)
        else:
            log("Could not find include file " + xml_file)

    def update_xml_files(self):
        # update list of all include and window xmls
        self.window_file_list = {}
        for path in self.xml_folders:
            xml_folder = os.path.join(self.project_path, path)
            self.window_file_list[path] = get_xml_file_paths(xml_folder)

    def go_to_tag(self, keyword, folder):
        # jumps to the definition of ref named keyword
        # TODO: need to add param with ref type
        if keyword:
            if keyword.isdigit():
                for node in self.string_list:
                    if node["id"] == "#" + keyword:
                        if int(keyword) >= 31000 and int(keyword) <= 33000:
                            file_path = self.addon_lang_path
                        else:
                            file_path = self.kodi_lang_path
                        return "%s:%s" % (file_path, node["line"])
            else:
                # TODO: need to check for include file attribute
                for node in self.include_list[folder]:
                    if node["name"] == keyword:
                        return "%s:%s" % (node["file"], node["line"])
                for node in self.fonts[folder]:
                    if node["name"] == keyword:
                        path = os.path.join(self.project_path, folder, "Font.xml")
                        return "%s:%s" % (path, node["line"])
                for node in self.color_list:
                    if node["name"] == keyword and node["filename"].endswith("defaults.xml"):
                        return "%s:%s" % (node["filename"], node["line"])
                log("no node with name %s found" % keyword)
        return False

    def return_node_content(self, keyword=None, return_entry="content", folder=False):
        if keyword and folder:
            if folder in self.fonts:
                for node in self.fonts[folder]:
                    if node["name"] == keyword:
                        return node[return_entry]
            if folder in self.include_list:
                for node in self.include_list[folder]:
                    if node["name"] == keyword:
                        return node[return_entry]
                # log("no node with name %s found" % keyword)

    def return_label(self, selection):
        if selection.isdigit():
            id_string = "#" + selection
            for item in self.string_list:
                if id_string == item["id"]:
                    tooltips = item["string"]
                    if self.use_native:
                        tooltips += "<br>" + item["native_string"]
                    return tooltips
        return ""

    def get_settings(self, settings):
        self.settings = settings
        self.kodi_path = settings.get("kodi_path")
        log("kodi path: " + self.kodi_path)
        self.use_native = settings.get("use_native_language")
        if self.use_native:
            self.language_folder = settings.get("native_language")
            log("use native language: " + self.language_folder)
        else:
            self.language_folder = DEFAULT_LANGUAGE_FOLDER
            log("use default language: English")

    def get_builtin_label(self):
        paths = [os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po"),
                 os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")]
        self.kodi_lang_path = checkPaths(paths)
        if self.kodi_lang_path:
            self.builtin_list = get_label_list(self.kodi_lang_path)
            log("Builtin labels loaded. Amount: %i" % len(self.builtin_list))
        else:
            self.builtin_list = []
            log("Could not find kodi language file")
            return ""

    def update_labels(self):
        if not self.addon_xml_file:
            return False
        paths = [os.path.join(self.project_path, "resources", "language", self.language_folder, "strings.po"),
                 os.path.join(self.project_path, "language", self.language_folder, "strings.po"),
                 os.path.join(self.project_path, "language", "resource.language.en_gb", "strings.po")]
        self.addon_lang_path = checkPaths(paths)
        if self.addon_lang_path:
            self.addon_string_list = get_label_list(self.addon_lang_path)
            log("Addon Labels updated. Amount: %i" % len(self.addon_string_list))
        else:
            self.addon_string_list = []
            log("Could not find add-on language file")
        self.string_list = self.builtin_list + self.addon_string_list

    def get_color_info(self, color_string):
        color_info = ""
        for item in self.color_list:
            if item["name"] == color_string:
                color_hex = "#" + item["content"][2:]
                cont_color = get_cont_col(color_hex)
                alpha_percent = round(int(item["content"][:2], 16) / (16 * 16) * 100)
                color_info += '%s&nbsp;<a style="background-color:%s;color:%s">%s</a> %d %% alpha<br>' % (os.path.basename(item["filename"]), color_hex, cont_color, item["content"], alpha_percent)
        if color_info:
            return color_info
        if all(c in string.hexdigits for c in color_string) and len(color_string) == 8:
            color_hex = "#" + color_string[2:]
            cont_color = get_cont_col(color_hex)
            alpha_percent = round(int(color_string[:2], 16) / (16 * 16) * 100)
            return '<a style="background-color:%s;color:%s">%d %% alpha</a>' % (color_hex, cont_color, alpha_percent)
        return color_info

    def get_ancestor_info(self, path, line):
        element = None
        root = get_root_from_file(path)
        tree = ET.ElementTree(root)
        for e in tree.iter():
            if line <= e.sourceline:
                element = e
                break
        values = {}
        for anc in element.iterancestors():
            for sib in anc.iterchildren():
                if sib.tag in ["posx", "posy"]:
                    if sib.tag in values:
                        values[sib.tag].append(sib.text)
                    else:
                        values[sib.tag] = [sib.text]
        anc_info = ""
        for key, value in values.items():
            anc_info += "<b>%s:</b> %s <br>" % (key, str(value))
        if anc_info:
            return "<b>Absolute position</b><br>" + anc_info
        else:
            return ""

    def get_font_info(self, font_name, folder):
        node_content = str(self.return_node_content(font_name, folder=folder))
        root = ET.fromstring(node_content)
        label = ""
        for e in root.iterchildren():
            label += "<b>%s:</b> %s<br>" % (e.tag, e.text)
        return label

    def check_variables(self):
        var_regex = "\$VAR\[(.*?)\]"
        listitems = []
        for folder in self.xml_folders:
            var_refs = []
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                with codecs.open(path, encoding="utf8", errors="ignore") as f:
                    for i, line in enumerate(f.readlines()):
                        for match in re.finditer(var_regex, line):
                            item = {"line": i + 1,
                                    "type": "variable",
                                    "file": path,
                                    "name": match.group(1).split(",")[0]}
                            var_refs.append(item)
            for ref in var_refs:
                for node in self.include_list[folder]:
                    if node["type"] == "variable" and node["name"] == ref["name"]:
                        break
                else:
                    ref["message"] = "Variable not defined: %s" % ref["name"]
                    listitems.append(ref)
            ref_list = [d['name'] for d in var_refs]
            for node in self.include_list[folder]:
                if node["type"] == "variable" and node["name"] not in ref_list:
                    node["message"] = "Unused variable: %s" % node["name"]
                    listitems.append(node)
        return listitems

    def check_includes(self):
        listitems = []
        # include check for each folder separately
        for folder in self.xml_folders:
            var_refs = []
            # get all include refs
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                root = get_root_from_file(path)
                if root is None:
                    continue
                for node in root.xpath(".//include"):
                        if node.text and not node.text.startswith("skinshortcuts-"):
                            name = node.text
                            if "file" in node.attrib:
                                include_file = os.path.join(self.project_path, folder, node.attrib["file"])
                                if include_file not in self.include_file_list[folder]:
                                    self.update_includes(include_file)
                        elif node.find("./param") is not None:
                            name = node.attrib["name"]
                        else:
                            continue
                        item = {"line": node.sourceline,
                                "type": node.tag,
                                "file": path,
                                "name": name}
                        var_refs.append(item)
            # find undefined include refs
            for ref in var_refs:
                for node in self.include_list[folder]:
                    if node["type"] == "include" and node["name"] == ref["name"]:
                        break
                else:
                    ref["message"] = "Include not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused include defs
            ref_list = [d['name'] for d in var_refs]
            for node in self.include_list[folder]:
                if node["type"] == "include" and node["name"] not in ref_list:
                    node["message"] = "Unused include: %s" % node["name"]
                    listitems.append(node)
        return listitems

    def build_translate_label(self, label_id, scrope_name):
        if "text.xml" in scope_name and self.addon_type == "python" and 32000 <= label_id <= 33000:
            return "$ADDON[%s %i]" % (self.addon_name, label_id)
        elif "text.xml" in scope_name:
            return "$LOCALIZE[%i]" % label_id
        else:
            return label_id

    def translate_path(self, path):
        if path.startswith("special://skin/"):
            return os.path.join(self.project_path, path.replace("special://skin/", ""))
        else:
            return os.path.join(self.media_path(), path)

    def get_image_info(self, path):
        imagepath = self.translate_path(path)
        if os.path.exists(imagepath) and not os.path.isdir(imagepath):
            im = Image.open(imagepath)
            file_size = os.path.getsize(imagepath) / 1024
            return "<b>Dimensions:</b> %s <br><b>File size:</b> %.2f kb" % (str(im.size), file_size)
        return ""

    def get_font_refs(self):
        font_refs = {}
        for folder in self.xml_folders:
            font_refs[folder] = []
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                font_refs[folder].extend(get_refs_from_file(path, ".//font"))
        return font_refs

    def check_fonts(self):
        listitems = []
        font_refs = self.get_font_refs()
        # get confluence fonts..
        confluence_fonts = []
        confluence_font_file = os.path.join(self.kodi_path, "addons", "skin.confluence", "720p", "Font.xml")
        if os.path.exists(confluence_font_file):
            root = get_root_from_file(confluence_font_file)
            if root is not None:
                for node in root.find("fontset").findall("font"):
                    confluence_fonts.append(node.find("name").text)
            # check fonts from each folder independently....
        for folder in self.xml_folders:
            fontlist = ["-"]
            # create a list with all font names from default fontset
            if folder in self.fonts:
                for item in self.fonts[folder]:
                    fontlist.append(item["name"])
            # find undefined font refs
            for ref in font_refs[folder]:
                if ref["name"] not in fontlist:
                    ref["message"] = "Font not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused font defs
            ref_list = [d['name'] for d in font_refs[folder]]
            if folder in self.fonts:
                for node in self.fonts[folder]:
                    if node["name"] not in ref_list and node["name"] not in confluence_fonts:
                        node["message"] = "Unused font: %s" % node["name"]
                        listitems.append(node)
        return listitems

    def check_ids(self):
        window_regex = r"(?:Dialog.Close|Window.IsActive|Window.IsVisible|Window)\(([0-9]+)\)"
        control_regex = "^(?!.*IsActive)(?!.*Window.IsVisible)(?!.*Dialog.Close)(?!.*Window)(?!.*Row)(?!.*Column).*\(([0-9]*?)\)"
        builtin_window_ids = [0, 1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17,
                              18, 19, 20, 21, 25, 28, 29, 34, 40, 100, 101, 103,
                              104, 106, 107, 109, 111, 113, 114, 115, 120, 122, 123,
                              124, 125, 126, 128, 129, 130, 131, 132, 134, 135, 136,
                              137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147,
                              149, 150, 151, 152, 153, 500, 501, 502, 503, 615, 616,
                              617, 618, 619, 620, 621, 622, 623, 624, 602, 603, 604,
                              605, 606, 607, 610, 611, 2000, 2001, 2002, 2003, 2005,
                              2006, 2007, 2008, 2009, 2600, 2900, 2901, 2902, 2999]
        listitems = []
        for folder in self.xml_folders:
            window_ids = []
            window_refs = []
            control_refs = []
            defines = []
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                root = get_root_from_file(path)
                if root is None:
                    continue
                if "id" in root.attrib:
                    window_ids.append(root.attrib["id"])
                # get all nodes with ids....
                xpath = ".//*[@id]"
                for node in root.xpath(xpath):
                    item = {"name": node.attrib["id"],
                            "type": node.tag,
                            "file": path,
                            "line": node.sourceline}
                    defines.append(item)
                # get all conditions....
                xpath = ".//*[@condition]"
                for node in root.xpath(xpath):
                    for match in re.finditer(control_regex, node.attrib["condition"], re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        control_refs.append(item)
                    for match in re.finditer(window_regex, node.attrib["condition"], re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        window_refs.append(item)
                bracket_tags = ["visible", "enable", "usealttexture", "selected", "onclick", "onback"]
                xpath = ".//" + " | .//".join(bracket_tags)
                for node in root.xpath(xpath):
                    if not node.text:
                        continue
                    for match in re.finditer(control_regex, node.text, re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        control_refs.append(item)
                    for match in re.finditer(window_regex, node.text, re.IGNORECASE):
                        item = {"name": match.group(1),
                                "type": node.tag,
                                "file": path,
                                "line": node.sourceline}
                        window_refs.append(item)
                # check if all refs exist...
            define_list = [d['name'] for d in defines]
            for item in window_refs:
                if item["name"] in window_ids:
                    pass
                elif int(item["name"]) in builtin_window_ids:
                    pass
                else:
                    item["message"] = "Window ID not defined: " + item["name"]
                    listitems.append(item)
            for item in control_refs:
                if not item["name"] or item["name"] in define_list:
                    pass
                else:
                    item["message"] = "Control / Item ID not defined: " + item["name"]
                    listitems.append(item)
        return listitems

    def resolve_include(self, ref, folder):
        if not ref.text:
            return None
        include_names = [item["name"] for item in self.include_list[folder]]
        if ref.text not in include_names:
            return None
        index = include_names.index(ref.text)
        node = self.include_list[folder][index]
        root = ET.fromstring(node["content"])
        root = self.resolve_includes(root, folder)
        return root

    def resolve_includes(self, xml_source, folder):
        xpath = ".//include"
        for node in xml_source.xpath(xpath):
            if node.text:
                new_include = self.resolve_include(node, folder)
                if new_include is not None:
                    node.getparent().replace(node, new_include)
        return xml_source

    def translate_square_bracket(self, info_type, info_id, folder):
        if info_type == "VAR":
            node_content = str(self.return_node_content(info_id, folder=folder))
            root = ET.fromstring(node_content)
            label = ""
            for e in root.iterchildren():
                label += "<b>%s:</b> %s<br>" % (e.attrib.get("condition", "else"), e.text)
            return label
        elif info_type == "INFO":
            data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": ["%s"] },"id":1}' % info_id
            result = kodi_json_request(data, True, self.settings)
            if result:
                key, value = result["result"].popitem()
                if value:
                    return str(value)
        elif info_type == "LOCALIZE":
            return self.return_label(info_id)
        return ""

    def create_new_label(self, word):
        if self.addon_type == "skin":
            start_id = 31000
            index_offset = 0
        else:
            start_id = 32000
            index_offset = 2
        po = polib.pofile(self.addon_lang_path)
        string_ids = []
        for i, entry in enumerate(po):
            try:
                string_ids.append(int(entry.msgctxt[1:]))
            except:
                string_ids.append(entry.msgctxt)
        for label_id in range(start_id, start_id + 1000):
            if label_id not in string_ids:
                log("first free: " + str(label_id))
                break
        msgstr = "#" + str(label_id)
        new_entry = polib.POEntry(msgid=word, msgstr="", msgctxt=msgstr)
        po_index = int(label_id) - start_id + index_offset
        po.insert(po_index, new_entry)
        po.save(self.addon_lang_path)
        self.update_labels()
        return label_id

    def go_to_help(self, word):
        controls = {"group": "http://kodi.wiki/view/Group_Control",
                    "grouplist": "http://kodi.wiki/view/Group_List_Control",
                    "label": "http://kodi.wiki/view/Label_Control",
                    "fadelabel": "http://kodi.wiki/view/Fade_Label_Control",
                    "image": "http://kodi.wiki/view/Image_Control",
                    "largeimage": "http://kodi.wiki/view/Large_Image_Control",
                    "multiimage": "http://kodi.wiki/view/MultiImage_Control",
                    "button": "http://kodi.wiki/view/Button_control",
                    "radiobutton": "http://kodi.wiki/view/Radio_button_control",
                    "selectbutton": "http://kodi.wiki/view/Group_Control",
                    "togglebutton": "http://kodi.wiki/view/Toggle_button_control",
                    "multiselect": "http://kodi.wiki/view/Multiselect_control",
                    "spincontrol": "http://kodi.wiki/view/Spin_Control",
                    "spincontrolex": "http://kodi.wiki/view/Settings_Spin_Control",
                    "progress": "http://kodi.wiki/view/Progress_Control",
                    "list": "http://kodi.wiki/view/List_Container",
                    "wraplist": "http://kodi.wiki/view/Wrap_List_Container",
                    "fixedlist": "http://kodi.wiki/view/Fixed_List_Container",
                    "panel": "http://kodi.wiki/view/Text_Box",
                    "rss": "http://kodi.wiki/view/RSS_feed_Control",
                    "visualisation": "http://kodi.wiki/view/Visualisation_Control",
                    "videowindow": "http://kodi.wiki/view/Video_Control",
                    "edit": "http://kodi.wiki/view/Edit_Control",
                    "epggrid": "http://kodi.wiki/view/EPGGrid_control",
                    "mover": "http://kodi.wiki/view/Mover_Control",
                    "resize": "http://kodi.wiki/view/Resize_Control"
                    }
        webbrowser.open_new(controls[word])
        # control_types = "|".join(controls.keys())

    def check_labels(self):
        listitems = []
        refs = []
        regexs = [r"\$LOCALIZE\[([0-9].*?)\]", r"^(\d+)$"]
        label_regex = r"[A-Za-z]+"
        # labels = [s["string"] for s in self.string_list]
        checks = [[".//viewtype[(@label)]", "label"],
                  [".//fontset[(@idloc)]", "idloc"],
                  [".//label[(@fallback)]", "fallback"]]
        for folder in self.xml_folders:
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                root = get_root_from_file(path)
                if root is None:
                    continue
                # find all referenced label ids (in element content)
                for element in root.xpath(".//label | .//altlabel | .//label2 | .//value | .//onclick | .//property"):
                    if not element.text:
                        continue
                    for match in re.finditer(regexs[0], element.text):
                        item = {"name": match.group(1),
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                for element in root.xpath(".//label | .//altlabel | .//label2"):
                    if not element.text:
                        continue
                    if element.text.isdigit():
                        item = {"name": element.text,
                                "type": element.tag,
                                "file": path,
                                "line": element.sourceline}
                        refs.append(item)
                # check for untranslated strings...
                    elif "$" not in element.text and not len(element.text) == 1 and not element.text.endswith(".xml") and re.match(label_regex, element.text):
                        item = {"name": element.text,
                                "type": element.tag,
                                "file": path,
                                "message": "Label in <%s> not translated: %s" % (element.tag, element.text),
                                "line": element.sourceline}
                        listitems.append(item)
                # find some more references (in attribute values this time)....
                for check in checks:
                    for element in root.xpath(check[0]):
                        attr = element.attrib[check[1]]
                        for regex in regexs:
                            for match in re.finditer(regex, attr):
                                item = {"name": match.group(1),
                                        "type": element.tag,
                                        "file": path,
                                        "line": element.sourceline}
                                refs.append(item)
                        # find some more untranslated strings
                        if "$" not in attr and not attr.isdigit() and re.match(label_regex, attr):
                            item = {"name": attr,
                                    "type": element.tag,
                                    "file": path,
                                    "message": "Label in attribute not translated: %s" % attr,
                                    "line": element.sourceline}
                            listitems.append(item)
        # check if refs are defined in po files
        label_ids = [s["id"] for s in self.string_list]
        for ref in refs:
            if "#" + ref["name"] not in label_ids:
                ref["message"] = "Label not defined: %s" % ref["name"]
                listitems.append(ref)
        return listitems

    def check_values(self):
        listitems = []
        for folder in self.xml_folders:
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                new_items = self.check_file(path)
                listitems.extend(new_items)
        return listitems

    def check_file(self, path):
        xml_file = os.path.basename(path)
        # tags allowed for all controls
        common = ["description", "camera", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom", "centerleft", "centerright", "width", "height", "visible", "include", "animation"]
        # tags allowed for containers
        list_common = ["focusedlayout", "itemlayout", "content", "onup", "ondown", "onleft", "onright", "onback", "orientation", "preloaditems", "scrolltime", "pagecontrol", "viewtype", "autoscroll", "hitrect"]
        label_common = ["font", "textcolor", "align", "aligny", "label"]
        # allowed child nodes for different control types (+ some other nodes)
        tag_checks = [[".//*[@type='button']/*", common + label_common + ["colordiffuse", "texturefocus", "texturenofocus", "label2", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                          "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                          "focusedcolor", "invalidcolor", "angle", "hitrect", "enable"]],
                      [".//*[@type='radiobutton']/*", common + label_common + ["colordiffuse", "texturefocus", "texturenofocus", "selected", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                               "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                               "focusedcolor", "angle", "hitrect", "enable", "textureradioonfocus", "textureradioofffocus", "textureradioonnofocus",
                                                                               "textureradiooffnofocus", "textureradioon", "textureradiooff", "radioposx", "radioposy", "radiowidth", "radioheight"]],
                      [".//*[@type='spincontrol']/*", common + label_common + ["colordiffuse", "textureup", "textureupfocus", "texturedown", "texturedownfocus", "spinwidth", "spinheight", "spinposx", "spinposy",
                                                                               "subtype", "disabledcolor", "shadowcolor", "textoffsetx", "textoffsety", "pulseonselect", "onfocus", "onunfocus", "onup", "onleft",
                                                                               "onright", "ondown", "onback", "hitrect", "enable", "showonepage"]],
                      [".//*[@type='togglebutton']/*", common + label_common + ["colordiffuse", "texturefocus", "alttexturefocus", "alttexturenofocus", "altclick", "texturenofocus", "altlabel", "usealttexture",
                                                                                "disabledcolor", "shadowcolor", "textoffsetx", "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft",
                                                                                "onright", "ondown", "onback", "textwidth", "focusedcolor", "subtype", "hitrect", "enable"]],
                      [".//*[@type='label']/*", common + label_common + ["scroll", "scrollout", "info", "number", "angle", "haspath", "selectedcolor", "shadowcolor", "disabledcolor", "pauseatend", "wrapmultiline",
                                                                         "scrollspeed", "scrollsuffix", "textoffsetx", "textoffsety"]],
                      [".//*[@type='textbox']/*", common + label_common + ["autoscroll", "info", "selectedcolor", "shadowcolor", "pagecontrol"]],
                      [".//*[@type='edit']/*", common + label_common + ["colordiffuse", "hinttext", "textoffsetx", "textoffsety", "pulseonselect", "disabledcolor", "invalidcolor", "focusedcolor", "shadowcolor",
                                                                        "texturefocus", "texturenofocus", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth", "hitrect", "enable"]],
                      [".//*[@type='image']/*", common + ["align", "aligny", "aspectratio", "fadetime", "colordiffuse", "texture", "bordertexture", "bordersize", "info"]],
                      [".//*[@type='multiimage']/*", common + ["align", "aligny", "aspectratio", "fadetime", "colordiffuse", "imagepath", "timeperimage", "loop", "info", "randomize", "pauseatend"]],
                      [".//*[@type='scrollbar']/*", common + ["texturesliderbackground", "texturesliderbar", "texturesliderbarfocus", "textureslidernib", "textureslidernibfocus", "pulseonselect", "orientation",
                                                              "showonepage", "pagecontrol", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback"]],
                      [".//*[@type='progress']/*", common + ["texturebg", "lefttexture", "colordiffuse", "righttexture", "overlaytexture", "midtexture", "info", "reveal"]],
                      [".//*[@type='videowindow']/*", common],
                      [".//*[@type='visualisation']/*", common],
                      [".//*[@type='list']/*", common + list_common],
                      [".//*[@type='wraplist']/*", common + list_common + ["focusposition"]],
                      [".//*[@type='panel']/*", common + list_common],
                      [".//*[@type='fixedlist']/*", common + list_common + ["movement", "focusposition"]],
                      [".//content/*", ["item", "include"]],
                      [".//itemlayout/* | .//focusedlayout/*", ["control", "include"]],
                      ["/includes/*", ["include", "default", "constant", "variable"]],
                      ["/window/*", ["include", "defaultcontrol", "onload", "onunload", "controls", "allowoverlay", "views", "coordinates", "animation", "visible", "zorder", "fontset", "backgroundcolor"]],
                      ["/fonts/*", ["fontset"]],
                      [".//variable/*", ["value"]]]
        # allowed attributes for some specific nodes
        att_checks = [[["aspectratio"], ["description", "align", "aligny", "scalediffuse"]],
                      [["texture"], ["description", "background", "flipx", "flipy", "fallback", "border", "diffuse", "colordiffuse"]],
                      [["label"], ["description", "fallback"]],
                      [["autoscroll"], ["time", "reverse", "delay", "repeat"]],
                      [["defaultcontrol"], ["description", "always"]],
                      [["visible"], ["description", "allowhiddenfocus"]],
                      [["align", "aligny", "posx", "posy", "textoffsetx", "textoffsety"], ["description"]],
                      [["height", "width"], ["description", "min", "max"]],
                      [["camera"], ["description", "x", "y"]],
                      [["hitrect"], ["description", "x", "y", "w", "h"]],
                      [["onload", "onunload", "onclick", "onleft", "onright", "onup", "ondown", "onback", "onfocus", "onunfocus", "value"], ["description", "condition"]],
                      [["property"], ["description", "name", "fallback"]],
                      [["focusedlayout", "itemlayout"], ["description", "height", "width", "condition"]],
                      [["item"], ["description", "id"]],
                      [["control"], ["description", "id", "type"]],
                      [["variable"], ["description", "name"]],
                      [["include"], ["description", "name", "condition", "file"]],
                      [["animation"], ["description", "start", "end", "effect", "tween", "easing", "time", "condition", "reversible", "type", "center", "delay", "pulse", "loop", "acceleration"]],
                      [["effect"], ["description", "start", "end", "tween", "easing", "time", "condition", "type", "center", "delay", "pulse", "loop", "acceleration"]]]
        # all_tags = [d[0] for d in att_checks]
        # check correct parantheses for some nodes
        bracket_tags = ["visible", "enable", "usealttexture", "selected"]
        # check some nodes to use noop instead of "-" / empty
        noop_tags = ["onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback"]
        # check that some nodes only exist once on each level
        # todo: special cases: label for fadelabel
        double_tags = ["camera", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom", "centerleft", "centerright", "width", "height",
                       "colordiffuse", "texturefocus", "texturenofocus", "font", "selected", "textcolor", "disabledcolor", "selectedcolor",
                       "shadowcolor", "align", "aligny", "textoffsetx", "textoffsety", "pulseonselect", "textwidth", "focusedcolor", "invalidcolor", "angle", "hitrect"]
        # check that some nodes only contain specific text
        allowed_text = [[["align"], ["left", "center", "right", "justify"]],
                        [["aspectratio"], ["keep", "scale", "stretch", "center"]],
                        [["aligny"], ["top", "center", "bottom"]],
                        [["orientation"], ["horizontal", "vertical"]],
                        [["subtype"], ["page", "int", "float", "text"]],
                        [["action"], ["volume", "seek"]],
                        [["scroll", "randomize", "scrollout", "pulseonselect", "reverse", "usecontrolcoords"], ["false", "true", "yes", "no"]]]
        # check that some attributes may only contain specific values
        allowed_attr = [["align", ["left", "center", "right", "justify"]],
                        ["aligny", ["top", "center", "bottom"]],
                        ["flipx", ["true", "false"]],
                        ["flipy", ["true", "false"]]]
        root = get_root_from_file(path)
        # folder = path.split(os.sep)[-2]
        # root = self.resolve_includes(root, folder)
        if root is None:
            return []
        tree = ET.ElementTree(root)
        listitems = []
        # find invalid tags
        for check in tag_checks:
            for node in root.xpath(check[0]):
                if node.tag not in check[1]:
                    if "type" in node.getparent().attrib:
                        text = '"%s type="%s"' % (node.getparent().tag, node.getparent().attrib["type"])
                    else:
                        text = node.getparent().tag
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "message": "invalid tag for <%s>: <%s>" % (text, node.tag),
                            "file": path}
                    listitems.append(item)
        # find invalid attributes
        for check in att_checks:
            xpath = ".//" + " | .//".join(check[0])
            for node in root.xpath(xpath):
                for attr in node.attrib:
                    if attr not in check[1]:
                        item = {"line": node.sourceline,
                                "type": node.tag,
                                "filename": xml_file,
                                "message": "invalid attribute for <%s>: %s" % (node.tag, attr),
                                "file": path}
                        listitems.append(item)
        # check conditions in element content
        xpath = ".//" + " | .//".join(bracket_tags)
        for node in root.xpath(xpath):
            if not node.text:
                message = "Empty condition: %s" % (node.tag)
            elif not check_brackets(node.text):
                condition = str(node.text).replace("  ", "").replace("\t", "")
                message = "Brackets do not match: %s" % (condition)
            else:
                continue
            item = {"line": node.sourceline,
                    "type": node.tag,
                    "filename": xml_file,
                    "message": message,
                    "file": path}
            listitems.append(item)
        # check conditions in attribute values
        for node in root.xpath(".//*[@condition]"):
            if not check_brackets(node.attrib["condition"]):
                condition = str(node.attrib["condition"]).replace("  ", "").replace("\t", "")
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "filename": xml_file,
                        "message": "Brackets do not match: %s" % (condition),
                        "file": path}
                listitems.append(item)
        # check for noop as empty action
        xpath = ".//" + " | .//".join(noop_tags)
        for node in root.xpath(xpath):
            if node.text == "-" or not node.text:
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "filename": xml_file,
                        "message": "Use 'noop' for empty calls <%s>" % (node.tag),
                        "file": path}
                listitems.append(item)
        # check for not-allowed siblings for some tags
        xpath = ".//" + " | .//".join(double_tags)
        for node in root.xpath(xpath):
            if not node.getchildren():
                xpath = tree.getpath(node)
                if xpath.endswith("]") and not xpath.endswith("[1]"):
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "message": "Invalid multiple tags for %s: <%s>" % (node.getparent().tag, node.tag),
                            "file": path}
                    listitems.append(item)
        # Check tags which require specific values
        for check in allowed_text:
            xpath = ".//" + " | .//".join(check[0])
            for node in root.xpath(xpath):
                if node.text.lower() not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "message": "invalid value for %s: %s" % (node.tag, node.text),
                            "file": path}
                    listitems.append(item)
        # Check attributes which require specific values
        for check in allowed_attr:
            for node in root.xpath(".//*[(@%s)]" % check[0]):
                if node.attrib[check[0]] not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "message": "invalid value for %s attribute: %s" % (check[0], node.attrib[check[0]]),
                            "file": path}
                    listitems.append(item)
        return listitems
