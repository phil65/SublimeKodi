import sublime_plugin
import sublime
import re
import os
import sys
import json
import cgi
__file__ = os.path.normpath(os.path.abspath(__file__))
__path__ = os.path.dirname(__file__)
libs_path = os.path.join(__path__, 'libs')
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)
from polib import polib
from lxml import etree as ET
from PIL import Image
from InfoProvider import InfoProvider
from Utils import *
import webbrowser
INFOS = InfoProvider()
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

    def on_selection_modified_async(self, view):
        history = sublime.load_settings(SETTINGS_FILE)
        if len(view.sel()) > 1:
            return None
        if view.sel() and view.sel()[0] == self.prev_selection:
            return None
        elif not INFOS.project_path:
            return None
        # inside_bracket = False
        popup_label = None
        identifier = ""
        region = view.sel()[0]
        self.prev_selection = region
        view.hide_popup()
        scope_name = view.scope_name(region.b)
        selection = view.substr(view.word(region))
        line = view.line(region)
        line_contents = view.substr(line).lower()
        flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
        label_region = view.expand_by_class(region, flags, '$],')
        bracket_region = view.expand_by_class(region, flags, '<>')
        if label_region.begin() > bracket_region.begin() and label_region.end() < bracket_region.end():
            # inside_bracket = True
            identifier = view.substr(label_region)
            log(identifier)
        if "source.python" in scope_name:
            if "lang" in line_contents or "label" in line_contents or "string" in line_contents:
                popup_label = INFOS.return_label(view, selection)
            # elif popup_label and popup_label > 30000:
            #     popup_label = INFOS.return_label(view, selection)
        elif "text.xml" in scope_name:
            if identifier.startswith("VAR"):
                node_content = str(INFOS.return_node_content(identifier[4:]))
                ind1 = node_content.find('\\n')
                popup_label = cgi.escape(node_content[ind1 + 4:-16]).replace("\\n", "<br>")
                if popup_label:
                    popup_label = "&nbsp;" + popup_label
            elif identifier.startswith("INFO"):
                data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": ["%s"] },"id":1}' % identifier[5:]
                result = kodi_json_request(data)
                result = json.loads(result.decode("utf-8"))
                log(result)
                key, value = result["result"].popitem()
                if value:
                    popup_label = str(value)
            elif "<include" in line_contents:
                node_content = str(INFOS.return_node_content(findWord(view)))
                ind1 = node_content.find('\\n')
                popup_label = cgi.escape(node_content[ind1 + 2:-16]).replace("\\n", "<br>"). replace(" ", "&nbsp;")
                if popup_label:
                    popup_label = "&nbsp;" + popup_label
            elif "<font" in line_contents:
                node_content = str(INFOS.return_node_content(findWord(view)))
                ind1 = node_content.find('\\n')
                popup_label = cgi.escape(node_content[ind1 + 4:-12]).replace("\\n", "<br>")
                if popup_label:
                    popup_label = "&nbsp;" + popup_label
            elif "<label" in line_contents or "<property" in line_contents or "<altlabel" in line_contents or "localize" in line_contents:
                popup_label = INFOS.return_label(view, selection)
            elif "<textcolor" in line_contents or "<color" in line_contents:
                for item in INFOS.color_list:
                    if item["name"] == selection:
                        popup_label = item["content"]
                        break
            elif "<fadetime" in line_contents:
                popup_label = str(INFOS.return_node_content(findWord(view)))[2:-3]
            elif "<texture" in line_contents or "<alttexture" in line_contents or "<bordertexture" in line_contents or "<icon" in line_contents or "<thumb" in line_contents:
                region = view.sel()[0]
                line = view.line(region)
                line_contents = view.substr(line)
                scope_name = view.scope_name(region.begin())
                if "string.quoted.double.xml" in scope_name:
                    scope_area = view.extract_scope(region.a)
                    rel_image_path = view.substr(scope_area).replace('"', '')
                else:
                    root = ET.fromstring(line_contents)
                    rel_image_path = root.text
                if rel_image_path.startswith("special://skin/"):
                    imagepath = os.path.join(INFOS.project_path, rel_image_path.replace("special://skin/", ""))
                else:
                    imagepath = os.path.join(INFOS.project_path, "media", rel_image_path)
                if os.path.exists(imagepath) and not os.path.isdir(imagepath):
                    im = Image.open(imagepath)
                    file_size = os.path.getsize(imagepath) / 1024
                    popup_label = "Size: %s <br>File size: %.2f kb" % (str(im.size), file_size)
            elif "<control " in line_contents:
                # todo: add positioning based on parent nodes
                popup_label = str(INFOS.return_node_content(findWord(view)))[2:-3]
        if popup_label and history.get("tooltip_delay", 0) > -1:
            sublime.set_timeout_async(lambda: self.show_tooltip(view, popup_label), history.get("tooltip_delay", 0))

    def show_tooltip(self, view, tooltip_label):
        history = sublime.load_settings(SETTINGS_FILE)
        view.show_popup(tooltip_label, sublime.COOPERATE_WITH_AUTO_COMPLETE,
                        location=-1, max_width=history.get("tooltip_width", 1000), max_height=history.get("height", 300), on_navigate=lambda label_id, view=view: jump_to_label_declaration(view, label_id))

    def on_modified_async(self, view):
        if INFOS.project_path and view.file_name() and view.file_name().endswith(".xml"):
            self.is_modified = True

    def on_load_async(self, view):
        self.check_project_change()

    def on_activated_async(self, view):
        self.check_project_change()

    def on_post_save_async(self, view):
        log("saved " + view.file_name())
        if INFOS.project_path and view.file_name() and view.file_name().endswith(".xml"):
            history = sublime.load_settings(SETTINGS_FILE)
            if self.is_modified:
                if history.get("auto_reload_skin", True):
                    self.is_modified = False
                    sublime.active_window().run_command("execute_builtin", {"builtin": "ReloadSkin()"})
                INFOS.update_include_list()
                if view.file_name().endswith("colors/defaults.xml"):
                    INFOS.get_colors()
                if view.file_name().endswith("ont.xml"):
                    INFOS.get_fonts()
        if view.file_name().endswith(".po"):
            INFOS.update_labels()

    def check_project_change(self):
        view = sublime.active_window().active_view()
        if view and view.window():
            if not INFOS.settings_loaded:
                INFOS.get_settings()
            if not INFOS.labels_loaded:
                INFOS.get_builtin_label()
            if view.window():
                variables = view.window().extract_variables()
                if "folder" in variables:
                    project_folder = variables["folder"]
                    if project_folder and project_folder != self.actual_project:
                        self.actual_project = project_folder
                        log("project change detected: " + project_folder)
                        INFOS.init_addon(project_folder)
                        if INFOS.xml_folders:
                            log("Kodi project detected: " + project_folder)
                            INFOS.update_include_list()
                            INFOS.get_colors()
                            INFOS.get_fonts()
                            INFOS.update_labels()
                            sublime.status_message("SublimeKodi: successfully loaded addon")
                else:
                    log("Could not find folder path in project file")


class SetKodiFolderCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().show_input_panel("Set Kodi folder", KODI_PRESET_PATH, self.set_kodi_folder, None, None)

    def set_kodi_folder(self, path):
        if os.path.exists(path):
            sublime.load_settings(SETTINGS_FILE).set("kodi_path", path)
            sublime.save_settings(SETTINGS_FILE)
        else:
            sublime.message_dialog("Folder %s does not exist." % path)


class ExecuteBuiltinPromptCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.history = sublime.load_settings(SETTINGS_FILE)
        sublime.active_window().show_input_panel("Execute builtin", self.history.get("prev_json_builtin", ""), self.execute_builtin, None, None)

    def execute_builtin(self, builtin):
        self.history.set("prev_json_builtin", builtin)
        sublime.active_window().run_command("execute_builtin", {"builtin": builtin})


class ReloadKodiLanguageFilesCommand(sublime_plugin.WindowCommand):

    def run(self):
        INFOS.get_settings()
        INFOS.get_builtin_label()
        INFOS.update_labels()


class ExecuteBuiltinCommand(sublime_plugin.WindowCommand):

    def run(self, builtin):
        data = '{"jsonrpc":"2.0","id":1,"method":"Addons.ExecuteAddon","params":{"addonid":"script.toolbox", "params": { "info": "builtin", "id": "%s"}}}' % builtin
        result = kodi_json_request(data)
        log(result)


class GetInfoLabelsCommand(sublime_plugin.WindowCommand):

    def run(self, label_string):
        words = label_string.split(",")
        labels = ', '.join('"{0}"'.format(w) for w in words)
        data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": [%s] },"id":1}' % labels
        result = kodi_json_request(data)
        log(result)


class SearchForLabelCommand(sublime_plugin.WindowCommand):

    def is_visible(self):
        view = self.window.active_view()
        scope_name = view.scope_name(view.sel()[0].b)
        return "source.python" in scope_name or "text.xml" in scope_name

    def run(self):
        label_list = []
        for item in INFOS.string_list:
            label_list.append("%s (%s)" % (item["string"], item["id"]))
        sublime.active_window().show_quick_panel(label_list, lambda s: self.label_search_ondone_action(s), selected_index=0)

    def label_search_ondone_action(self, index):
        if not index == -1:
            view = self.window.active_view()
            scope_name = view.scope_name(view.sel()[0].b)
            if "text.xml" in scope_name:
                lang_string = "$LOCALIZE[%s]" % INFOS.id_list[index][1:]
            else:
                lang_string = INFOS.id_list[index][1:]
            view.run_command("insert", {"characters": lang_string})


class OpenKodiLogCommand(sublime_plugin.WindowCommand):

    def run(self):
        history = sublime.load_settings(SETTINGS_FILE)
        if sublime.platform() == "linux":
            self.log_file = os.path.join(os.path.expanduser("~"), ".%s" % APP_NAME, "temp", "%s.log" % APP_NAME)
        elif sublime.platform() == "windows":
            if history.get("portable_mode"):
                self.log_file = os.path.join(history.get("kodi_path"), "portable_data", "%s.log" % APP_NAME)
            else:
                self.log_file = os.path.join(os.getenv('APPDATA'), "%s" % APP_NAME, "%s.log" % APP_NAME)
        sublime.active_window().open_file(self.log_file)


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

    def run(self, edit):
        region = self.view.sel()[0]
        line = self.view.line(region)
        line_contents = self.view.substr(line)
        scope_name = self.view.scope_name(region.begin())
        if "string.quoted.double.xml" in scope_name:
            scope_area = self.view.extract_scope(region.a)
            rel_image_path = self.view.substr(scope_area).replace('"', '')
        else:
            root = ET.fromstring(line_contents)
            rel_image_path = root.text
        if rel_image_path.startswith("special://skin/"):
            rel_image_path = rel_image_path.replace("special://skin/", "")
            imagepath = os.path.join(INFOS.project_path, rel_image_path)
        else:
            imagepath = os.path.join(INFOS.project_path, "media", rel_image_path)
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


class GoToVariableCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        INFOS.go_to_tag(view=self.view)


class GoToIncludeCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        INFOS.go_to_tag(view=self.view)


class SearchForImageCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        return "source.python" in scope_name or "text.xml" in scope_name

    def run(self, edit):
        path, filename = os.path.split(self.view.file_name())
        self.imagepath = os.path.join(path, "..", "media")
        # self.pos = self.view.sel()
        if not os.path.exists(self.imagepath):
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
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        return "text.xml" in scope_name

    def run(self, edit):
        self.font_entries = []
        for node in INFOS.fonts:
            string_array = [node["name"], node["size"] + "  -  " + node["filename"]]
            self.font_entries.append(string_array)
        sublime.active_window().show_quick_panel(self.font_entries, lambda s: self.on_done(s), selected_index=0)

    def on_done(self, index):
        if index >= 0:
            self.view.run_command("insert", {"characters": self.font_entries[index][0]})
        sublime.active_window().focus_view(self.view)


class GoToOnlineHelpCommand(sublime_plugin.TextCommand):

    def is_visible(self):
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        return "text.xml" in scope_name

    def run(self, edit):
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
        # control_types = "|".join(controls.keys())
        region = self.view.sel()[0]
        line = self.view.line(region)
        line_contents = self.view.substr(line)
        try:
            root = ET.fromstring(line_contents + "</control>")
            control_type = root.attrib["type"]
            # log(controls[control_type])
            webbrowser.open_new(controls[control_type])
        except:
            log("error when trying to open from %s" % line_contents)

    def on_done(self, index):
        if index >= 0:
            self.view.run_command("insert", {"characters": self.font_entries[index][0]})
        sublime.active_window().focus_view(self.view)


class MoveToLanguageFile(sublime_plugin.TextCommand):

    def is_visible(self):
        scope_name = self.view.scope_name(self.view.sel()[0].b)
        if INFOS.project_path and INFOS.addon_lang_path:
            if "text.xml" in scope_name or "source.python" in scope_name:
                return True
        return False

    def run(self, edit):
        available_ids = []
        region = self.view.sel()[0]
        if region.begin() == region.end():
            sublime.message_dialog("Please select the complete label")
            return False
        word = self.view.substr(region)
        for label in INFOS.string_list:
            if label["string"].lower() == word.lower():
                available_ids.append(label)
        if available_ids:
            self.labels = []
            self.label_ids = []
            for item in available_ids:
                self.labels.append("%s %s" % (item["string"], item["id"]))
                self.label_ids.append(item["id"])
            self.labels.append("Create new label")
            sublime.active_window().show_quick_panel(self.labels, lambda s: self.on_done(s, region), selected_index=0)
        else:
            label_id = self.create_new_label(word)
            self.view.run_command("replace_text", {"label_id": label_id})

    def on_done(self, index, region):
        if self.labels[index] == "Create new label":
            label_id = self.create_new_label(self.view.substr(region))
        else:
            label_id = self.label_ids[index][1:]
        self.view.run_command("replace_text", {"label_id": label_id})

    def create_new_label(self, word):
        region = self.view.sel()[0]
        scope_name = self.view.scope_name(region.b)
        if "text.xml" in scope_name:
            start_id = 31000
        else:
            start_id = 32000
        po = polib.pofile(INFOS.addon_lang_path)
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
        po_index = int(label_id) - start_id
        po.insert(po_index, new_entry)
        po.save(INFOS.addon_lang_path)
        INFOS.update_labels()
        return label_id


class ReplaceTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, label_id):
        for region in self.view.sel():
            scope_name = self.view.scope_name(region.b)
            if "text.xml" in scope_name:
                template = "$LOCALIZE[%s]"
            else:
                template = "%s"
            self.view.replace(edit, region, template % str(label_id))


class SwitchXmlFolder(sublime_plugin.TextCommand):

    def is_visible(self):
        return len(INFOS.xml_folders) > 1

    def run(self, edit):
        self.element = None
        self.file = self.view.file_name()
        root = get_root_from_file(self.file)
        tree = ET.ElementTree(root)
        line, column = self.view.rowcol(self.view.sel()[0].b)
        elements = [e for e in tree.iter()]
        for e in elements:
            if line < e.sourceline:
                self.element = e
                log(tree.getpath(e))
                log(e.sourceline)
                break
    # if len(INFOS.xml_folders) > 2:
        sublime.active_window().show_quick_panel(INFOS.xml_folders, lambda s: self.on_done(s), selected_index=0, on_highlight=lambda s: self.show_preview(s))

    def show_preview(self, index):
        path = os.path.join(INFOS.project_path, INFOS.xml_folders[index], os.path.basename(self.file))
        sublime.active_window().open_file("%s:%i" % (path, self.element.sourceline), sublime.ENCODED_POSITION | sublime.TRANSIENT)
        # sublime.active_window().focus_view(self.view)

    def on_done(self, index):
        path = os.path.join(INFOS.project_path, INFOS.xml_folders[index], os.path.basename(self.file))
        sublime.active_window().open_file("%s:%i" % (path, self.element.sourceline), sublime.ENCODED_POSITION)
# def plugin_loaded():
#     view = sublime.active_window().active_view()
#     INFOS.update_include_list()
