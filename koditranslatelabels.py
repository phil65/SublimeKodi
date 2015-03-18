import sublime_plugin
import sublime
import re
import os


class KodiTranslatedLabelToolTip(sublime_plugin.EventListener):

    def on_activate(self, view):
        sublime.set_timeout(lambda: self.run(view, 'activated'), 0)

    def on_selection_modified_async(self, view):
        sublime.set_timeout(lambda: self.run(view, 'selection_modified'), 0)

    def run(self, view, where):
        # view_settings = view.settings()
        # if view_settings.get('is_widget'):
        #     return

        # If we have multiple selections, don't show anything.
        if len(view.sel()) > 1:
            return
        else:
            view.hide_popup()
        scope_name = view.scope_name(view.sel()[0].b)
        selection = view.substr(view.word(view.sel()[0]))
        if "source.python" in scope_name or "text.xml" in scope_name:
            view.show_popup(self.return_label(view, selection), sublime.COOPERATE_WITH_AUTO_COMPLETE, location=-1, max_width=1000, on_navigate=lambda label_id, view=view: jump_to_label_declaration(view, label_id))

    def return_label(self, view, selection):
        if selection.isdigit():
            path, filename = os.path.split(view.file_name())
            if os.path.exists(os.path.join(path, "resources", "language", "English", "strings.po")):
                lang_file_path = os.path.join(path, "resources", "language", "English", "strings.po")
            elif os.path.exists(os.path.join(path, "..", "language", "English", "strings.po")):
                lang_file_path = os.path.join(path, "..", "language", "English", "strings.po")
            else:
                return ""
            lang_file = open(lang_file_path, "r").read()
            id_list = re.findall('^msgctxt \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
            id_string = "#" + selection
            if id_string in id_list:
                index = id_list.index(id_string)
                result = re.findall('^msgid \"(.*)\"[^\"]*', lang_file, re.MULTILINE)
                return result[index + 1]
        return ""


def jump_to_label_declaration(view, label_id):
    view.run_command("insert", {"characters": label_id})
    view.hide_popup()
