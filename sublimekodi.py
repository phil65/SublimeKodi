import sublime_plugin
import sublime
import re
import os
import codecs
from xml.dom.minidom import parseString
APP_NAME = "kodi"
if sublime.platform() == "linux":
    KODI_PRESET_PATH = "/usr/share/%s/" % APP_NAME
    LOG_FILE = os.path.join(os.path.expanduser("~"), ".%s" % APP_NAME, "temp", "%s.log" % APP_NAME)
elif sublime.platform() == "windows":
    KODI_PRESET_PATH = "C:/%s/" % APP_NAME
    LOG_FILE = os.path.join(os.getenv('APPDATA'), "%s" % APP_NAME, "%s.log" % APP_NAME)
else:
    KODI_PRESET_PATH = ""

SETTINGS_FILE = 'sublimekodi.sublime-settings'
DEFAULT_LANGUAGE_FOLDER = "English"


class SublimeKodi(sublime_plugin.EventListener):

    def __init__(self, **kwargs):
        self.id_list = []
        self.string_list = []
        self.native_string_list = []
        self.labels_loaded = False
        self.settings_loaded = False
        self.actual_project = None

    def on_window_command(self, window, command_name, args):
        if command_name == "reload_kodi_language_files":
            self.get_settings()
            self.get_builtin_label()
            self.update_labels(window.active_view())
        elif command_name == "search_for_label":
            sublime.active_window().show_quick_panel(self.string_list, lambda s: self.label_search_ondone_action(s), selected_index=0)

    def label_search_ondone_action(self, index):
        lang_string = "$LOCALIZE[%s]" % self.id_list[index][1:]
        sublime.active_window().active_view().run_command("insert", {"characters": lang_string})

    def on_selection_modified_async(self, view):
        # log("on_selection_modified_async")
        sublime.set_timeout(lambda: self.run(view, 'selection_modified'), 500)

    def on_activated(self, view):
        if view:
            if not self.settings_loaded:
                self.get_settings()
            if not view.window():
                return True
            if not self.labels_loaded:
                self.get_builtin_label()
            if view.window().project_file_name() != self.actual_project:
                self.actual_project = view.window().project_file_name()
                self.update_labels(view)

    def run(self, view, where):
        if len(view.sel()) > 1:
            return
        else:
            view.hide_popup()
        if view.sel():
            scope_name = view.scope_name(view.sel()[0].b)
            selection = view.substr(view.word(view.sel()[0]))
            if "source.python" in scope_name or "text.xml" in scope_name:
                view.show_popup(self.return_label(view, selection), sublime.COOPERATE_WITH_AUTO_COMPLETE,
                                location=-1, max_width=1000, on_navigate=lambda label_id, view=view: jump_to_label_declaration(view, label_id))

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
                 os.path.join(path, "..", "language", self.language_folder, "strings.po")]
        path = checkPaths(paths)
        if path:
            return codecs.open(path, "r", "utf-8").read()
        else:
            return ""

    def get_kodi_lang_file(self):
        paths = [os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po"),
                 os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")]
        path = checkPaths(paths)
        if path:
            return codecs.open(path, "r", "utf-8").read()
        else:
            return ""

    def get_builtin_label(self):
        kodi_lang_file = self.get_kodi_lang_file()
        if kodi_lang_file:
            self.builtin_id_list = re.findall('^msgctxt \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)
            self.builtin_string_list = re.findall('^msgid \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)[1:]
            self.builtin_native_string_list = re.findall('^msgstr \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)[1:]
            self.labels_loaded = True
            log("Builtin labels loaded. Amount: %i" % len(self.builtin_string_list))

    def update_labels(self, view):
        if view.file_name():
            self.id_list = self.builtin_id_list
            self.string_list = self.builtin_string_list
            self.native_string_list = self.builtin_native_string_list
            path, filename = os.path.split(view.file_name())
            lang_file = self.get_addon_lang_file(path)
            if lang_file:
                self.id_list += re.findall('^msgctxt \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
                self.string_list += re.findall('^msgid \"(.*)\"[^\"]*', lang_file, re.MULTILINE)[1:]
                self.native_string_list += re.findall('^msgstr \"(.*)\"[^\"]*', lang_file, re.MULTILINE)[1:]
                log("Labels updated. Amount: %i" % len(self.id_list))


class SetKodiFolderCommand(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().show_input_panel("Set Kodi folder for language file", KODI_PRESET_PATH, self.set_kodi_folder, None, None)

    def set_kodi_folder(self, path):
        sublime.load_settings(SETTINGS_FILE).set("kodi_path", path)
        sublime.save_settings(SETTINGS_FILE)


class ReloadKodiLanguageFiles(sublime_plugin.WindowCommand):

    def run(self):
        pass


class SearchForLabel(sublime_plugin.WindowCommand):

    def run(self):
        pass


class OpenKodiLog(sublime_plugin.WindowCommand):

    def run(self):
        sublime.active_window().open_file(LOG_FILE)


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
        path, filename = os.path.split(self.view.file_name())
        region = self.view.sel()[0]
        line = self.view.line(region)
        line_contents = self.view.substr(line)
        scope_name = self.view.scope_name(region.begin())
        if "string.quoted.double.xml" in scope_name:
            scope_area = self.view.extract_scope(region.a)
            rel_image_path = self.view.substr(scope_area).replace('"', '')
        else:
            dom = parseString(line_contents)
            rel_image_path = dom.documentElement.childNodes[0].toxml()
        if rel_image_path.startswith("special://skin/"):
            rel_image_path = rel_image_path.replace("special://skin/", "")
            imagepath = os.path.join(path, "..", rel_image_path)
        else:
            imagepath = os.path.join(path, "..", "media", rel_image_path)
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


def checkPaths(paths):
    for path in paths:
        if os.path.exists(path):
            log("found path: %s" % path)
            return path
    return ""


def jump_to_label_declaration(view, label_id):
    view.run_command("insert", {"characters": label_id})
    view.hide_popup()


def log(string):
    print("SublimeKodi: " + string)
