# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
SublimeKodi is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""


import sublime_plugin
import sublime
import re
import os
import sys
import cgi
import webbrowser
from subprocess import Popen
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
from lxml import etree as ET
from InfoProvider import InfoProvider
from RemoteDevice import RemoteDevice
from Utils import *
from xml.sax.saxutils import escape
INFOS = InfoProvider()
REMOTE = RemoteDevice()
# sublime.log_commands(True)
APP_NAME = "kodi"
if sublime.platform() == "linux":
    KODI_PRESET_PATH = "/usr/share/%s/" % APP_NAME
elif sublime.platform() == "windows":
    KODI_PRESET_PATH = "C:/%s/" % APP_NAME
else:
    KODI_PRESET_PATH = ""
SETTINGS_FILE = 'sublimekodi.sublime-settings'


class SublimeKodi(sublime_plugin.EventListener):

    def __init__(self, **kwargs):
        self.actual_project = None
        self.prev_selection = None
        self.is_modified = False
        self.settings_loaded = False

    def on_query_completions(self, view, prefix, locations):
        completions = []
        scope_name = view.scope_name(view.sel()[0].b)
        folder = view.file_name().split(os.sep)[-2]
        if folder not in INFOS.include_list:
            return []
        if "text.xml" in scope_name:
            nodes = INFOS.include_list[folder] + INFOS.fonts[folder]
            for node in nodes:
                completions.append([node["name"], node["name"]])
            completions.sort()
            return completions
            # return (completions, sublime.INHIBIT_WORD_COMPLETIONS | sublime.INHIBIT_EXPLICIT_COMPLETIONS)

    def on_selection_modified_async(self, view):
        if len(view.sel()) > 1 or not INFOS.addon_xml_file:
            return None
        try:
            region = view.sel()[0]
            folder = view.file_name().split(os.sep)[-2]
        except:
            return None
        if region == self.prev_selection:
            return None
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        popup_label = ""
        identifier = ""
        info_type = ""
        info_id = ""
        self.prev_selection = region
        view.hide_popup()
        scope_name = view.scope_name(region.b)
        line = view.line(region)
        line_contents = view.substr(line).lower()
        label_region = view.expand_by_class(region, flags, '$],')
        bracket_region = view.expand_by_class(region, flags, '<>')
        selected_content = view.substr(view.expand_by_class(region, flags, '<>"[]'))
        if label_region.begin() > bracket_region.begin() and label_region.end() < bracket_region.end():
            identifier = view.substr(label_region)
            info_list = identifier.split("[", 1)
            info_type = info_list[0]
            if len(info_list) > 1:
                info_id = info_list[1]
        if "source.python" in scope_name:
            if "lang" in line_contents or "label" in line_contents or "string" in line_contents:
                word = view.substr(view.word(region))
                popup_label = INFOS.return_label(word)
        elif "text.xml" in scope_name:
            if info_type in ["INFO", "VAR", "LOCALIZE"]:
                popup_label = INFOS.translate_square_bracket(info_type=info_type, info_id=info_id, folder=folder)
            if not popup_label:
                if "<include" in line_contents and "name=" not in line_contents:
                    node_content = str(INFOS.return_node_content(get_node_content(view, flags), folder=folder))
                    popup_label = cgi.escape(node_content).replace("\n", "<br>"). replace(" ", "&nbsp;")
                elif "<font" in line_contents and "</font" in line_contents:
                    popup_label = INFOS.get_font_info(selected_content, folder)
                elif "<label" in line_contents or "<property" in line_contents or "<altlabel" in line_contents or "localize" in line_contents:
                    popup_label = INFOS.return_label(selected_content)
                elif "<fadetime" in line_contents:
                    popup_label = str(INFOS.return_node_content(get_node_content(view, flags), folder=folder))[2:-3]
                elif "<texture" in line_contents or "<alttexture" in line_contents or "<bordertexture" in line_contents or "<icon" in line_contents or "<thumb" in line_contents:
                    popup_label = INFOS.get_image_info(selected_content)
                elif "<control " in line_contents:
                    # TODO: add positioning based on parent nodes
                    line, column = view.rowcol(view.sel()[0].b)
                    popup_label = INFOS.get_ancestor_info(view.file_name(), line)
                if not popup_label:
                    popup_label = INFOS.get_color_info(selected_content)
        if popup_label and self.settings.get("tooltip_delay", 0) > -1:
            sublime.set_timeout_async(lambda: self.show_tooltip(view, popup_label), self.settings.get("tooltip_delay", 0))

    def show_tooltip(self, view, tooltip_label):
        view.show_popup(tooltip_label, sublime.COOPERATE_WITH_AUTO_COMPLETE,
                        location=-1, max_width=self.settings.get("tooltip_width", 1000), max_height=self.settings.get("height", 300), on_navigate=lambda label_id, view=view: jump_to_label_declaration(view, label_id))

    def on_modified_async(self, view):
        if INFOS.project_path and view.file_name() and view.file_name().endswith(".xml"):
            self.is_modified = True

    def on_load_async(self, view):
        self.check_status()
        # filename = view.file_name()
        # if INFOS.addon_xml_file and filename and filename.endswith(".xml"):
        #     self.root = get_root_from_file(filename)
        #     self.tree = ET.ElementTree(self.root)

    def on_activated_async(self, view):
        self.check_status()

    def on_deactivated_async(self, view):
        view.hide_popup()

    def on_post_save_async(self, view):
        if not INFOS.project_path or not view.file_name():
            return False
        if view.file_name().endswith(".xml"):
            if self.is_modified:
                if self.settings.get("auto_reload_skin", True):
                    self.is_modified = False
                    view.window().run_command("execute_builtin", {"builtin": "ReloadSkin()"})
                INFOS.reload_skin_after_save(view.file_name())
                if self.settings.get("auto_skin_check", True):
                    view.window().run_command("check_variables", {"check_type": "file"})
        if view.file_name().endswith(".po"):
            INFOS.update_addon_labels()

    def check_status(self):
        if not self.settings_loaded:
            self.settings = sublime.load_settings(SETTINGS_FILE)
            INFOS.get_settings(self.settings)
            INFOS.update_builtin_labels()
            self.settings_loaded = True
        view = sublime.active_window().active_view()
        filename = view.file_name()
        if INFOS.addon_xml_file and filename and filename.endswith(".xml"):
            view.set_syntax_file('Packages/SublimeKodi/KodiSkinXML.tmLanguage')
        if filename and filename.endswith(".po"):
            view.set_syntax_file('Packages/SublimeKodi/Gettext.tmLanguage')
        if filename and filename.endswith(".log"):
            view.set_syntax_file('Packages/SublimeKodi/KodiLog.sublime-syntax')
        if view and view.window() is not None:
            variables = view.window().extract_variables()
            if "folder" in variables:
                project_folder = variables["folder"]
                if project_folder and project_folder != self.actual_project:
                    self.actual_project = project_folder
                    log("project change detected: " + project_folder)
                    INFOS.init_addon(project_folder)
            else:
                log("Could not find folder path in project file")


class RemoteActionsCommand(sublime_plugin.WindowCommand):

    def run(self):
        listitems = ["Reconnect", "Send to box", "Get log", "Clear cache"]
        self.window.show_quick_panel(listitems, lambda s: self.on_done(s), selected_index=0)

    def on_done(self, index):
        if index == -1:
            return None
        elif index == 0:
            REMOTE.adb_reconnect_async()
            self.window.run_command("remote_actions")
        elif index == 1:
            REMOTE.push_to_box(INFOS.project_path)
        elif index == 2:
            plugin_path = os.path.join(sublime.packages_path(), "SublimeKodi")
            REMOTE.get_log(self.on_log_done, plugin_path)
        elif index == 3:
            REMOTE.clear_cache()

    def on_log_done(self, path):
        self.window.open_file(path)


class SetKodiFolderCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Set Kodi folder", KODI_PRESET_PATH, self.set_kodi_folder, None, None)

    def set_kodi_folder(self, path):
        if os.path.exists(path):
            sublime.load_settings(SETTINGS_FILE).set("kodi_path", path)
            sublime.save_settings(SETTINGS_FILE)
        else:
            sublime.message_dialog("Folder %s does not exist." % path)


class ExecuteBuiltinPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.window.show_input_panel("Execute builtin", self.settings.get("prev_json_builtin", ""), self.execute_builtin, None, None)

    def execute_builtin(self, builtin):
        self.settings.set("prev_json_builtin", builtin)
        self.window.run_command("execute_builtin", {"builtin": builtin})


class ExecuteBuiltinCommand(sublime_plugin.WindowCommand):

    def run(self, builtin):
        settings = sublime.load_settings(SETTINGS_FILE)
        data = '{"jsonrpc":"2.0","id":1,"method":"Addons.ExecuteAddon","params":{"addonid":"script.toolbox", "params": { "info": "builtin", "id": "%s"}}}' % builtin
        send_json_request_async(data, settings=settings)


class ReloadKodiLanguageFilesCommand(sublime_plugin.WindowCommand):

    def run(self):
        view = self.window.active_view()
        regions = view.find_by_selector("variable.parameter")
        log(regions)
        for region in regions:
            log(view.substr(region))
            view.sel().add(region)


class QuickPanelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        if INFOS.addon_xml_file:
            return True
        else:
            return False

    def on_done(self, index):
        if index == -1:
            return None
        node = self.nodes[index]
        view = self.window.open_file("%s:%i" % (node["file"], node["line"]), sublime.ENCODED_POSITION)
        self.select_text(view, node)

    def show_preview(self, index):
        node = self.nodes[index]
        self.window.open_file("%s:%i" % (node["file"], node["line"]), sublime.ENCODED_POSITION | sublime.TRANSIENT)
        # self.select_text(view, node)

    @run_async
    def select_text(self, view, node):
        while view.is_loading():
            pass
        view.sel().clear()
        text_point = view.text_point(node["line"] - 1, 0)
        line = view.line(text_point)
        if "identifier" in node:
            label = escape(node["identifier"])
            line_contents = view.substr(line)
            line_start = line_contents.find(label)
            num = line_contents.count(label)
            if num != 1:
                return False
            line_end = line_start + len(label)
            id_start = text_point + line_start
            id_end = text_point + line_end
            view.sel().add(sublime.Region(int(id_start), int(id_end)))


class BuildAddonCommand(sublime_plugin.WindowCommand):

    def run(self, pack_textures=True):
        self.build_skin(INFOS.project_path, pack_textures)

    @run_async
    def build_skin(self, skin_path, pack_textures):
        settings = sublime.load_settings(SETTINGS_FILE)
        for line in texturepacker_generator(skin_path, settings):
            self.window.run_command("log", {"label": line.strip()})
        zip_path = os.path.join(skin_path, os.path.basename(skin_path) + ".zip")
        for filename in make_archive(skin_path, zip_path):
            self.window.run_command("log", {"label": "zipped " + filename})
        do_open = sublime.ok_cancel_dialog("Zip file created!\nDo you want to open its location a with file browser?", "Open")
        if do_open:
            webbrowser.open(skin_path)


class OpenKodiAddonCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.nodes = INFOS.get_kodi_addons()
        self.window.show_quick_panel(self.nodes, lambda s: self.on_done(s), selected_index=0)

    def on_done(self, index):
        path = os.path.join(INFOS.get_userdata_folder(), "addons", self.nodes[index])
        Popen([get_sublime_path(), "-n", "-a", path])


class ShowFontRefsCommand(QuickPanelCommand):

    def run(self):
        listitems = []
        self.nodes = []
        view = self.window.active_view()
        INFOS.update_xml_files()
        font_refs = INFOS.get_font_refs()
        self.folder = view.file_name().split(os.sep)[-2]
        for ref in font_refs[self.folder]:
            if ref["name"] == "Font_Reg28":
                listitems.append(ref["name"])
                self.nodes.append(ref)
        if listitems:
            self.window.show_quick_panel(listitems, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))
        else:
            sublime.message_dialog("No references found")


class SearchFileForLabelsCommand(QuickPanelCommand):

    def run(self):
        listitems = []
        self.nodes = []
        regexs = [r"\$LOCALIZE\[([0-9].*?)\]", r"(?:label|property|altlabel|label2)>([0-9].*?)<"]
        view = self.window.active_view()
        path = view.file_name()
        labels = [s["string"] for s in INFOS.string_list]
        label_ids = [s["id"] for s in INFOS.string_list]
        # view.substr(sublime.Region(0, view.size()))
        with open(path, encoding="utf8") as f:
            for i, line in enumerate(f.readlines()):
                for regex in regexs:
                    for match in re.finditer(regex, line):
                        label_id = "#" + match.group(1)
                        if label_id in label_ids:
                            index = label_ids.index(label_id)
                            listitems.append("%s (%s)" % (labels[index], label_id))
                        node = {"file": path,
                                "line": i + 1}
                        self.nodes.append(node)
        if listitems:
            self.window.show_quick_panel(listitems, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))
        else:
            sublime.message_dialog("No references found")


class CheckVariablesCommand(QuickPanelCommand):

    def run(self, check_type):
        filename = self.window.active_view().file_name()
        if check_type == "file":
            self.nodes = INFOS.check_file(filename)
        else:
            self.nodes = INFOS.get_check_listitems(check_type)
        listitems = [[item["message"], os.path.basename(item["file"]) + ": " + str(item["line"])] for item in self.nodes]
        if listitems:
            self.window.show_quick_panel(listitems, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))
        elif not check_type == "file":
            sublime.message_dialog("No errors detected")


class GetInfoLabelsPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        self.window.show_input_panel("Get InfoLabels (comma-separated)", self.settings.get("prev_infolabel", ""), self.show_info_label, None, None)

    def show_info_label(self, label_string):
        self.settings.set("prev_infolabel", label_string)
        words = label_string.split(",")
        labels = ', '.join('"{0}"'.format(w) for w in words)
        data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": [%s] },"id":1}' % labels
        result = send_json_request(data, self.settings)
        if result:
            key, value = result["result"].popitem()
            sublime.message_dialog(str(value))


class SearchForLabelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        if INFOS.string_list:
            return True
        else:
            return False

    def run(self):
        label_list = []
        id_list = []
        for item in INFOS.string_list:
            if item["id"] not in id_list:
                id_list.append(item["id"])
                label_list.append(["%s (%s)" % (item["string"], item["id"]), item["comment"]])
        self.window.show_quick_panel(label_list, lambda s: self.label_search_ondone_action(s), selected_index=0)

    def label_search_ondone_action(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        scope_name = view.scope_name(view.sel()[0].b)
        label_id = int(INFOS.string_list[index]["id"][1:])
        info_string = INFOS.build_translate_label(label_id, scope_name)
        view.run_command("insert", {"characters": info_string})


class OpenKodiLogCommand(sublime_plugin.WindowCommand):

    def run(self):
        filename = "%s.log" % APP_NAME
        self.log_file = checkPaths([os.path.join(INFOS.get_userdata_folder(), filename),
                                    os.path.join(INFOS.get_userdata_folder(), "temp", filename)])
        self.window.open_file(self.log_file)


class OpenSourceFromLog(sublime_plugin.TextCommand):

    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                line = self.view.line(region)
                line_contents = self.view.substr(line)
                ma = re.search('File "(.*?)", line (\d*), in .*', line_contents)
                if ma:
                    target_filename = ma.group(1)
                    target_line = ma.group(2)
                    sublime.active_window().open_file("%s:%s" % (target_filename, target_line), sublime.ENCODED_POSITION)
                    return
                ma = re.search(r"', \('(.*?)', (\d+), (\d+), ", line_contents)
                if ma:
                    target_filename = ma.group(1)
                    target_line = ma.group(2)
                    target_col = ma.group(3)
                    sublime.active_window().open_file("%s:%s:%s" % (target_filename, target_line, target_col), sublime.ENCODED_POSITION)
                    return
            else:
                self.view.insert(edit, region.begin(), self.view.substr(region))


class PreviewImageCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        if INFOS.media_path():
            flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
            content = get_node_content(self.view, flags)
            if "/" in content or "\\" in content:
                return True
        return False

    def run(self, edit):
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        path = get_node_content(self.view, flags)
        imagepath = INFOS.translate_path(path)
        if os.path.exists(imagepath):
            if os.path.isdir(imagepath):
                self.files = []
                for (dirpath, dirnames, filenames) in os.walk(imagepath):
                    self.files.extend(filenames)
                    break
                self.files = [imagepath + s for s in self.files]
            else:
                self.files = [imagepath]
            sublime.active_window().show_quick_panel(self.files, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))

    def on_done(self, index):
        sublime.active_window().focus_view(self.view)

    def show_preview(self, index):
        if index >= 0:
            file_path = self.files[index]
            sublime.active_window().open_file(file_path, sublime.TRANSIENT)


class GoToTagCommand(sublime_plugin.WindowCommand):

    def run(self):
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        view = self.window.active_view()
        keyword = get_node_content(view, flags)
        folder = view.file_name().split(os.sep)[-2]
        position = INFOS.go_to_tag(keyword, folder)
        if position:
            self.window.open_file(position, sublime.ENCODED_POSITION)


class SearchForImageCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        if INFOS.media_path():
            return True
        else:
            return False

    def run(self, edit):
        path, filename = os.path.split(self.view.file_name())
        self.imagepath = INFOS.media_path()
        if not self.imagepath:
            log("Could not find file " + self.imagepath)
        self.files = []
        for path, subdirs, files in os.walk(self.imagepath):
            if "studio" in path or "recordlabel" in path:
                continue
            for filename in files:
                image_path = os.path.join(path, filename).replace(self.imagepath, "").replace("\\", "/")
                if image_path.startswith("/"):
                    image_path = image_path[1:]
                self.files.append(image_path)
        sublime.active_window().show_quick_panel(self.files, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))

    def on_done(self, index):
        items = ["Insert path", "Open Image"]
        if index >= 0:
            sublime.active_window().show_quick_panel(items, lambda s: self.insert_char(s, index), selected_index=0)
        else:
            sublime.active_window().focus_view(self.view)

    def insert_char(self, index, fileindex):
        if index == 0:
            self.view.run_command("insert", {"characters": self.files[fileindex]})
        elif index == 1:
            os.system("start " + os.path.join(self.imagepath, self.files[fileindex]))
        sublime.active_window().focus_view(self.view)

    def show_preview(self, index):
        if index >= 0:
            file_path = os.path.join(self.imagepath, self.files[index])
        sublime.active_window().open_file(file_path, sublime.TRANSIENT)


class SearchForFontCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        if INFOS.fonts:
            return True
        else:
            return False

    def run(self, edit):
        self.font_entries = []
        folder = self.view.file_name().split(os.sep)[-2]
        for node in INFOS.fonts[folder]:
            string_array = [node["name"], node["size"] + "  -  " + node["filename"]]
            self.font_entries.append(string_array)
        sublime.active_window().show_quick_panel(self.font_entries, lambda s: self.on_done(s), selected_index=0)

    def on_done(self, index):
        if index >= 0:
            self.view.run_command("insert", {"characters": self.font_entries[index][0]})
        sublime.active_window().focus_view(self.view)


class GoToOnlineHelpCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        region = self.view.sel()[0]
        line_contents = self.view.substr(self.view.line(region))
        scope_name = self.view.scope_name(region.b)
        return "text.xml" in scope_name and "<control " in line_contents

    def run(self, edit):
        region = self.view.sel()[0]
        line = self.view.line(region)
        line_contents = self.view.substr(line)
        try:
            root = ET.fromstring(line_contents + "</control>")
            control_type = root.attrib["type"]
            INFOS.go_to_help(control_type)
        except:
            log("error when trying to open from %s" % line_contents)


class MoveToLanguageFile(sublime_plugin.TextCommand):

    def is_visible(self):
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        if INFOS.project_path and INFOS.addon_lang_folders:
            if "text.xml" in scope_name or "source.python" in scope_name:
                if self.view.sel()[0].b != self.view.sel()[0].a:
                    return True
        return False

    def run(self, edit):
        self.label_ids = []
        self.labels = []
        region = self.view.sel()[0]
        if region.begin() == region.end():
            sublime.message_dialog("Please select the complete label")
            return False
        word = self.view.substr(region)
        for label in INFOS.string_list:
            if label["string"].lower() == word.lower():
                self.label_ids.append(label)
                self.labels.append(["%s (%s)" % (label["string"], label["id"]), label["comment"]])
        if self.label_ids:
            self.labels.append("Create new label")
            sublime.active_window().show_quick_panel(self.labels, lambda s: self.on_done(s, region), selected_index=0)
        else:
            label_id = INFOS.create_new_label(word)
            self.view.run_command("replace_text", {"label_id": label_id})

    def on_done(self, index, region):
        if index == -1:
            return None
        if self.labels[index] == "Create new label":
            label_id = INFOS.create_new_label(self.view.substr(region))
        else:
            label_id = self.label_ids[index]["id"][1:]
        self.view.run_command("replace_text", {"label_id": label_id})


class ReplaceTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label_id):
        for region in self.view.sel():
            scope_name = self.view.scope_name(region.b)
            label_id = int(label_id)
            new = INFOS.build_translate_label(label_id, scope_name)
            self.view.replace(edit, region, new)


class AppendTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label):
        self.view.insert(edit, self.view.size(), label + "\n")


class LogCommand(sublime_plugin.TextCommand):

    def run(self, edit, label, panel_name='example'):
        # get_output_panel doesn't "get" the panel, it *creates* it,
        # so we should only call get_output_panel once
        if not hasattr(self, 'output_view'):
            self.output_view = self.view.window().get_output_panel(panel_name)
        v = self.output_view
        v.insert(edit, v.size(), label + '\n')
        v.show(v.size())
        self.view.window().run_command("show_panel", {"panel": "output." + panel_name})


class CreateElementRowCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Enter number of items to generate", "1", on_done=self.generate_items, on_change=None, on_cancel=None)

    def generate_items(self, num_items):
        self.window.run_command("replace_xml_elements", {"num_items": num_items})


class ReplaceXmlElementsCommand(sublime_plugin.TextCommand):

    def run(self, edit, num_items):
        selected_text = self.view.substr(self.view.sel()[0])
        # new_text = selected_text + "\n"
        new_text = ""
        for i in range(1, int(num_items) + 1):
            new_text = new_text + selected_text.replace("[X]", str(i)) + "\n"
            i += 1
        for region in self.view.sel():
            self.view.replace(edit, region, new_text)
            break


class SwitchXmlFolderCommand(QuickPanelCommand):

    def is_visible(self):
        return len(INFOS.xml_folders) > 1

    def run(self):
        view = self.window.active_view()
        self.nodes = []
        line, column = view.rowcol(view.sel()[0].b)
        filename = os.path.basename(view.file_name())
        for folder in INFOS.xml_folders:
            path = os.path.join(INFOS.project_path, folder, filename)
            node = {"file": path,
                    "line": line}
            self.nodes.append(node)
        self.window.show_quick_panel(INFOS.xml_folders, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))


def plugin_loaded():
    REMOTE.setup(sublime.load_settings(SETTINGS_FILE))
