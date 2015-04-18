import sublime_plugin
import sublime
import re
import os
import platform
import codecs
if platform.system() == "Linux":
    KODI_PRESET_PATH = "/usr/share/kodi/"
    LOG_FILE = os.path.join(os.path.expanduser("~"), ".kodi", "temp", "kodi.log")
elif platform.system() == "Windows":
    KODI_PRESET_PATH = "C:/Kodi/"
    LOG_FILE = os.path.join(os.getenv('APPDATA'), "KODI", "kodi.log")
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
            self.update_labels(window.active_view())
        elif command_name == "set_kodi_folder":
            sublime.active_window().show_input_panel("Set Kodi folder for language file", KODI_PRESET_PATH, self.set_kodi_folder, None, None)

    def on_text_command(self, view, command_name, args):
        # log(command_name)
        pass

    def on_selection_modified_async(self, view):
        # log("on_selection_modified_async")
        sublime.set_timeout(lambda: self.run(view, 'selection_modified'), 500)

    def on_activated(self, view):
        if view:
            if not self.settings_loaded:
                self.get_settings()
            if not view.window():
                return True
            if not self.labels_loaded or view.window().project_file_name() != self.actual_project:
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
                tooltips = self.string_list[index + 1]
                if self.use_native:
                    tooltips += "<br>" + self.native_string_list[index + 1]
                return tooltips
        return ""

    def set_kodi_folder(self, path):
        sublime.load_settings(SETTINGS_FILE).set("kodi_path", path)
        sublime.save_settings(SETTINGS_FILE)

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
        # sublime.save_settings(history_filename)

    def get_addon_lang_file(self, path):
        if os.path.exists(os.path.join(path, "resources", "language", self.language_folder, "strings.po")):
            lang_file_path = os.path.join(path, "resources", "language", self.language_folder, "strings.po")
            log("found addon language file in %s" % lang_file_path)
        elif os.path.exists(os.path.join(path, "..", "language", self.language_folder, "strings.po")):
            lang_file_path = os.path.join(path, "..", "language", self.language_folder, "strings.po")
            log("found addon language file in %s" % lang_file_path)
        else:
            log("could not find addon language file")
            return ""
        return codecs.open(lang_file_path, "r", "utf-8").read()

    def get_kodi_lang_file(self):
        if os.path.exists(os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po")):
            lang_file_path = os.path.join(self.kodi_path, "addons", "resource.language.en_gb", "resources", "strings.po")
            log("found Kodi language file in %s" % lang_file_path)
        elif os.path.exists(os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")):
            lang_file_path = os.path.join(self.kodi_path, "language", self.language_folder, "strings.po")
            log("found Kodi language file in %s" % lang_file_path)
        else:
            log("could not find Kodi language file")
            return ""
        return codecs.open(lang_file_path, "r", "utf-8").read()

    def update_labels(self, view):
        self.id_list = []
        self.string_list = []
        self.native_string_list = []
        if view.file_name():
            path, filename = os.path.split(view.file_name())
            lang_file = self.get_addon_lang_file(path)
            self.id_list += re.findall('^msgctxt \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
            self.string_list += re.findall('^msgid \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
            self.native_string_list += re.findall('^msgstr \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
        kodi_lang_file = self.get_kodi_lang_file()
        if kodi_lang_file:
            kodi_id_list = re.findall('^msgctxt \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)
            kodi_string_list = re.findall('^msgid \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)[1:]
            kodi_native_string_list = re.findall('^msgstr \"(.*)\"[^\"]*', kodi_lang_file, re.MULTILINE)[1:]
            self.id_list += kodi_id_list
            self.string_list += kodi_string_list
            self.native_string_list += kodi_native_string_list
            self.labels_loaded = True
            log("Addon labels updated. Amount: %i" % len(self.string_list))


class SetKodiFolderCommand(sublime_plugin.WindowCommand):

    def run(self):
        pass


class ReloadKodiLanguageFiles(sublime_plugin.WindowCommand):

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
            else:
                self.view.insert(edit, region.begin(), self.view.substr(region))


def jump_to_label_declaration(view, label_id):
    view.run_command("insert", {"characters": label_id})
    view.hide_popup()


def log(string):
    print("SublimeKodi: " + string)
