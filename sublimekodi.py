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
import platform
from itertools import chain
from subprocess import Popen
from xml.sax.saxutils import escape

__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_platform_path = os.path.join(__path__, 'libs-winlin')
if platform.system() == "Darwin":
    libs_platform_path = os.path.join(__path__, "libs-mac")
if libs_platform_path not in sys.path:
    sys.path.insert(0, libs_platform_path)

from lxml import etree as ET
from .libs.Utils import *
from .libs.InfoProvider import *
from .libs.RemoteDevice import RemoteDevice

INFOS = InfoProvider()
REMOTE = RemoteDevice()
# sublime.log_commands(True)
APP_NAME = "Kodi"
APP_NAME_LOWER = APP_NAME.lower()
if sublime.platform() == "linux":
    KODI_PRESET_PATH = "/usr/share/%s/" % APP_NAME_LOWER
elif sublime.platform() == "windows":
    KODI_PRESET_PATH = "C:/%s/" % APP_NAME_LOWER
elif platform.system() == "Darwin":
    KODI_PRESET_PATH = os.path.join(os.path.expanduser("~"), "Applications", "%s.app" % APP_NAME, "Contents", "Resources", APP_NAME)
else:
    KODI_PRESET_PATH = ""
SETTINGS_FILE = 'sublimekodi.sublime-settings'
SUBLIME_PATH = get_sublime_path()


class SublimeKodi(sublime_plugin.EventListener):

    def __init__(self, **kwargs):
        self.actual_project = None
        self.prev_selection = None
        self.is_modified = False
        self.settings_loaded = False

    def on_query_completions(self, view, prefix, locations):
        completions = []
        scope_name = view.scope_name(view.sel()[0].b)
        filename = view.file_name()
        if not filename:
            return []
        folder = filename.split(os.sep)[-2]
        if folder not in INFOS.include_list:
            return []
        if "text.xml" in scope_name:
            colors = []
            for node in INFOS.color_list:
                if node["name"] not in colors:
                    colors.append(node["name"])
                    completions.append(["%s (%s)" % (node["name"], node["content"]), node["name"]])
            for node in chain(INFOS.include_list[folder], INFOS.fonts[folder]):
                completions.append([node["name"], node["name"]])
            for node in chain(INFOS.builtins, INFOS.conditions):
                completions.append([node[0], node[0]])
            for item in WINDOW_NAMES:
                completions.append([item, item])
            for item in completions:
                for i, match in enumerate(re.findall(r"\([a-z,\]\[]+\)", item[1])):
                    item[1] = item[1].replace(match, "($%i)" % (i + 1))
            return completions.sort()
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
        scope_content = view.substr(view.extract_scope(region.b))
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
            if info_type in ["INFO", "ESCINFO", "VAR", "ESCVAR", "LOCALIZE"]:
                popup_label = INFOS.translate_square_bracket(info_type=info_type, info_id=info_id, folder=folder)
            if not popup_label:
                if "<include" in line_contents and "name=" not in line_contents:
                    node_content = str(INFOS.return_node_content(get_node_content(view, flags), folder=folder))
                    if len(node_content) < 1000:
                        popup_label = cgi.escape(node_content).replace("\n", "<br>"). replace(" ", "&nbsp;")
                    else:
                        popup_label = "include too big for preview"
                elif "<font" in line_contents and "</font" in line_contents:
                    popup_label = INFOS.get_font_info(selected_content, folder)
                elif "label" in line_contents or "<property" in line_contents or "<altlabel" in line_contents or "localize" in line_contents:
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
            if not popup_label and "constant.other.allcaps" in scope_name:
                if scope_content.lower() in WINDOW_NAMES:
                    popup_label = WINDOW_FILENAMES[WINDOW_NAMES.index(scope_content.lower())]
        # node = INFOS.template_root.find(".//control[@type='label']")
        # log(node)
        # popup_label = node.find(".//available_tags").text.replace("\\n", "<br>")
        if popup_label and self.settings.get("tooltip_delay", 0) > -1:
            sublime.set_timeout_async(lambda: self.show_tooltip(view, popup_label), self.settings.get("tooltip_delay", 0))

    def show_tooltip(self, view, tooltip_label):
        if self.css:
            tooltip_label = "<style>%s</style>" % self.css + tooltip_label
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
        if not INFOS.addon_xml_file or not view.file_name():
            return False
        if view.file_name().endswith(".xml"):
            if not self.is_modified:
                return False
            INFOS.update_xml_files()
            filename = os.path.basename(view.file_name())
            folder = view.file_name().split(os.sep)[-2]
            INFOS.reload_skin_after_save(view.file_name())
            if folder in INFOS.window_file_list and filename in INFOS.window_file_list[folder]:
                if self.settings.get("auto_reload_skin", True):
                    self.is_modified = False
                    view.window().run_command("execute_builtin", {"builtin": "ReloadSkin()"})
                if self.settings.get("auto_skin_check", True):
                    view.window().run_command("check_variables", {"check_type": "file"})
        if view.file_name().endswith(".po"):
            INFOS.update_addon_labels()

    def check_status(self):
        if not self.settings_loaded:
            self.settings = sublime.load_settings(SETTINGS_FILE)
            INFOS.get_settings(self.settings)
            INFOS.update_builtin_labels()
            css_file = 'Packages/SublimeKodi/' + self.settings.get('tooltip_css_file')
            self.css = sublime.load_resource(css_file)
            self.settings_loaded = True
        view = sublime.active_window().active_view()
        filename = view.file_name()
        if INFOS.addon_xml_file and filename and filename.endswith(".xml"):
            view.assign_syntax('Packages/SublimeKodi/KodiSkinXML.sublime-syntax')
        if filename and filename.endswith(".po"):
            view.assign_syntax('Packages/SublimeKodi/Gettext.tmLanguage')
        if filename and filename.endswith(".log"):
            view.assign_syntax('Packages/SublimeKodi/KodiLog.sublime-syntax')
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
        self.settings = sublime.load_settings(SETTINGS_FILE)
        active_device = "Set device: %s" % self.settings.get("remote_ip", "")
        listitems = [active_device, "Reconnect", "Send this add-on", "Get log", "Get Screenshot", "Clear cache", "Reboot"]
        self.window.show_quick_panel(listitems, lambda s: self.on_done(s), selected_index=0)

    def on_done(self, index):
        if index == -1:
            return None
        elif index == 0:
            self.window.show_input_panel("Set remote IP", self.settings.get("remote_ip", "192.168.0.1"), self.set_ip, None, None)
        elif index == 1:
            REMOTE.adb_reconnect_async()
            self.window.run_command("remote_actions")
        elif index == 2:
            REMOTE.push_to_box(INFOS.project_path)
        elif index == 3:
            plugin_path = os.path.join(sublime.packages_path(), "SublimeKodi")
            REMOTE.get_log(self.open_file, plugin_path)
        elif index == 4:
            plugin_path = os.path.join(sublime.packages_path(), "SublimeKodi")
            REMOTE.get_screenshot(self.open_file, plugin_path)
        elif index == 5:
            REMOTE.clear_cache()
        elif index == 6:
            REMOTE.reboot()

    def open_file(self, path):
        self.window.open_file(path)

    def set_ip(self, ip):
        self.settings.set("remote_ip", ip)
        sublime.save_settings(SETTINGS_FILE)
        self.window.run_command("remote_actions")


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
        INFOS.get_settings(sublime.load_settings(SETTINGS_FILE))
        INFOS.update_builtin_labels()
        INFOS.update_addon_labels()
        # view = self.window.active_view()
        # regions = view.find_by_selector("variable.parameter")
        # log(regions)
        # for region in regions:
        #     log(view.substr(region))
        #     view.sel().add(region)


class QuickPanelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        return bool(INFOS.addon_xml_file)

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
        self.options = [os.path.join(INFOS.project_path, "media")]
        for folder in os.listdir(os.path.join(INFOS.project_path, "themes")):
            self.options.append(os.path.join(INFOS.project_path, "themes", folder))
        self.window.show_quick_panel(self.options, lambda s: self.on_done(s), selected_index=0)

    @run_async
    def on_done(self, index):
        if index == -1:
            return None
        media_path = self.options[index]
        settings = sublime.load_settings(SETTINGS_FILE)
        for line in texturepacker_generator(media_path, settings):
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
        if index == -1:
            return None
        path = os.path.join(INFOS.get_userdata_folder(), "addons", self.nodes[index])
        Popen([SUBLIME_PATH, "-n", "-a", path])


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
        labels = []
        label_ids = []
        regexs = [r"\$LOCALIZE\[([0-9].*?)\]", r"\$ADDON\[.*?([0-9].*?)\]", r"(?:label|property|altlabel|label2)>([0-9].*?)<"]
        view = self.window.active_view()
        path = view.file_name()
        for po_file in INFOS.po_files:
            labels += [s.msgid for s in po_file]
            label_ids += [s.msgctxt for s in po_file]
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


class OpenActiveWindowXmlFromRemoteCommand(sublime_plugin.WindowCommand):

    @run_async
    def run(self):
        self.settings = sublime.load_settings(SETTINGS_FILE)
        folder = self.window.active_view().file_name().split(os.sep)[-2]
        data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": ["Window.Property(xmlfile)"] },"id":1}'
        result = send_json_request(data, self.settings)
        if not result:
            return None
        key, value = result["result"].popitem()
        if os.path.exists(value):
            self.window.open_file(value)
        for xml_file in INFOS.window_file_list[folder]:
            if xml_file == value:
                path = os.path.join(INFOS.project_path, folder, xml_file)
                self.window.open_file(path)
                return None


class SearchForLabelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        return bool(INFOS.po_files)

    def run(self):
        listitems = []
        self.id_list = []
        for po_file in INFOS.po_files:
            for entry in po_file:
                if entry.msgctxt not in self.id_list:
                    self.id_list.append(entry.msgctxt)
                    listitems.append(["%s (%s)" % (entry.msgid, entry.msgctxt), entry.comment])
        self.window.show_quick_panel(listitems, lambda s: self.label_search_ondone_action(s), selected_index=0)

    def label_search_ondone_action(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        label_id = int(self.id_list[index][1:])
        info_string = INFOS.build_translate_label(label_id, view)
        view.run_command("insert", {"characters": info_string})


class SearchForBuiltinCommand(sublime_plugin.WindowCommand):

    def run(self):
        listitems = [["%s" % (item[0]), item[1]] for item in INFOS.builtins]
        self.window.show_quick_panel(listitems, lambda s: self.builtin_search_on_done(s), selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": INFOS.builtins[index][0]})


class SearchForVisibleConditionCommand(sublime_plugin.WindowCommand):

    def run(self):
        listitems = [["%s" % (item[0]), item[1]] for item in INFOS.conditions]
        self.window.show_quick_panel(listitems, lambda s: self.builtin_search_on_done(s), selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": INFOS.conditions[index][0]})


class SearchForJsonCommand(sublime_plugin.WindowCommand):

    @run_async
    def run(self):
        settings = sublime.load_settings(SETTINGS_FILE)
        data = '{"jsonrpc":"2.0","id":1,"method":"JSONRPC.Introspect"}'
        result = send_json_request(data, settings=settings)
        self.listitems = [["%s" % (key), str(value)] for item in result["result"]["types"].items()]
        self.listitems += [["%s" % (key), str(value)] for item in result["result"]["methods"].items()]
        self.listitems += [["%s" % (key), str(value)] for item in result["result"]["notifications"].items()]
        self.window.show_quick_panel(self.listitems, lambda s: self.builtin_search_on_done(s), selected_index=0)

    def builtin_search_on_done(self, index):
        if index == -1:
            return None
        view = self.window.active_view()
        view.run_command("insert", {"characters": str(self.listitems[index][0])})


class OpenKodiLogCommand(sublime_plugin.WindowCommand):

    def run(self):
        filename = "%s.log" % APP_NAME_LOWER
        self.log_file = check_paths([os.path.join(INFOS.get_userdata_folder(), filename),
                                     os.path.join(INFOS.get_userdata_folder(), "temp", filename)])
        self.window.open_file(self.log_file)


class OpenSourceFromLog(sublime_plugin.TextCommand):

    def run(self, edit):
        for region in self.view.sel():
            if region.empty():
                line_contents = self.view.substr(self.view.line(region))
                ma = re.search('File "(.*?)", line (\d*), in .*', line_contents)
                if ma:
                    sublime.active_window().open_file("%s:%s" % (ma.group(1), ma.group(2)), sublime.ENCODED_POSITION)
                    return
                ma = re.search(r"', \('(.*?)', (\d+), (\d+), ", line_contents)
                if ma:
                    sublime.active_window().open_file("%s:%s:%s" % (ma.group(1), ma.group(2), ma.group(3)), sublime.ENCODED_POSITION)
                    return
            else:
                self.view.insert(edit, region.begin(), self.view.substr(region))


class PreviewImageCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        if not INFOS.media_path:
            return False
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        content = get_node_content(self.view, flags)
        return "/" in content or "\\" in content

    def run(self, edit):
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        path = get_node_content(self.view, flags)
        imagepath = INFOS.translate_path(path)
        if not os.path.exists(imagepath):
            return None
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
        return bool(INFOS.media_path)

    def run(self, edit):
        path, filename = os.path.split(self.view.file_name())
        self.imagepath = INFOS.media_path
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
        return bool(INFOS.fonts)

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
        if INFOS.project_path and INFOS.addon_po_files:
            if "text.xml" in scope_name or "source.python" in scope_name:
                return self.view.sel()[0].b != self.view.sel()[0].a
        return False

    def run(self, edit):
        self.label_ids = []
        self.labels = []
        region = self.view.sel()[0]
        if region.begin() == region.end():
            sublime.message_dialog("Please select the complete label")
            return False
        word = self.view.substr(region)
        for po_file in INFOS.po_files:
            for label in po_file:
                if label.msgid.lower() == word.lower() and label.msgctxt not in self.label_ids:
                    self.label_ids.append(label.msgctxt)
                    self.labels.append(["%s (%s)" % (label.msgid, label.msgctxt), label.comment])
        self.labels.append("Create new label")
        sublime.active_window().show_quick_panel(self.labels, lambda s: self.on_done(s, region), selected_index=0)

    def on_done(self, index, region):
        if index == -1:
            return None
        region = self.view.sel()[0]
        rowcol = self.view.rowcol(region.b)
        rel_path = self.view.file_name().replace(INFOS.project_path, "")
        line = str(rowcol[0] + 1)
        if self.labels[index] == "Create new label":
            label_id = INFOS.create_new_label(self.view.substr(region), rel_path, line)
        else:
            label_id = self.label_ids[index][1:]
            if 31000 <= int(label_id) < 33000:
                entry = INFOS.addon_po_files[0].find(self.label_ids[index], by="msgctxt")
                entry.occurrences.append((rel_path, line))
                INFOS.addon_po_files[0].save(INFOS.addon_po_files[0].fpath)
        self.view.run_command("replace_text", {"label_id": label_id})


class ReplaceTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label_id):
        for region in self.view.sel():
            new = INFOS.build_translate_label(int(label_id), self.view)
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
        if not num_items.isdigit():
            return None
        selected_text = self.view.substr(self.view.sel()[0])
        new_text = ""
        reg = re.search(r"\[(-?[0-9]+)\]", selected_text)
        offset = 0
        if reg:
            offset = int(reg.group(1))
        for i in range(0, int(num_items)):
            new_text = new_text + selected_text.replace("[%i]" % offset, str(i + offset)) + "\n"
            i += 1
        for region in self.view.sel():
            self.view.replace(edit, region, new_text)
            break


class EvaluateMathExpressionPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel("Write Equation (x = selected int)", "x", self.evaluate, None, None)

    def evaluate(self, equation):
        self.window.run_command("evaluate_math_expression", {'equation': equation})


class EvaluateMathExpressionCommand(sublime_plugin.TextCommand):

    def run(self, edit, equation):
        for i, region in enumerate(self.view.sel()):
            text = self.view.substr(region)
            if text.replace('-', '').isdigit():
                new_text = eval(equation.replace("x", text).replace("i", str(i)))
                self.view.replace(edit, region, str(new_text).replace(".0", ""))


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
                    "line": line + 1}
            self.nodes.append(node)
        self.window.show_quick_panel(INFOS.xml_folders, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))

    def on_done(self, index):
        if index == -1:
            return None
        node = self.nodes[index]
        self.window.open_file("%s:%i" % (node["file"], node["line"]), sublime.ENCODED_POSITION)


def plugin_loaded():
    REMOTE.setup(sublime.load_settings(SETTINGS_FILE))


class ColorPickerCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        settings = sublime.load_settings('KodiColorPicker.sublime-settings')
        settings.set('color_pick_return', None)
        self.window.run_command('color_pick_api_is_available', {'settings': 'KodiColorPicker.sublime-settings'})
        return bool(settings.get('color_pick_return', False))

    def run(self):
        settings = sublime.load_settings('KodiColorPicker.sublime-settings')
        settings.set('color_pick_return', None)
        self.window.run_command('color_pick_api_get_color', {'settings': 'KodiColorPicker.sublime-settings', 'default_color': '#ff0000'})
        color = settings.get('color_pick_return')
        if color:
            self.window.active_view().run_command("insert", {"characters": "FF" + color[1:]})
