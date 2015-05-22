from Utils import *
import os


class RemoteDevice():

    def __init__(self):
        pass

    def setup(self, settings):
        self.settings = settings
        self.connected = False
        self.userdata_folder = "/sdcard/android/data/com.pivos.tofu/files/.tofu/"

    def adb_connect(self, ip):
        self.ip = ip
        result = command_line("adb", ["connect", str(ip)])
        self.log(result)
        self.connected = True

    def adb_reconnect(self, ip=None):
        if not ip:
            ip = self.ip
        result = command_line("adb", ["disconnect"])
        self.log(result)
        result = command_line("adb", ["connect", str(ip)])
        self.log(result)
        self.connected = True

    def adb_disconnect(self, ip=None):
        if not ip:
            ip = self.ip
        result = command_line("adb", ["disconnect"])
        self.log(result)
        result = command_line("adb", ["connect", str(ip)])
        self.log(result)
        self.connected = True

    def adb_push(self, source, target):
        if not target.endswith('/'):
            target += '/'
        result = command_line("adb", ["push", source.replace('\\', '/'), target.replace('\\', '/')])
        log(result)

    def adb_pull(self, path):
        command_line("adb", ["pull", path])

    def adb_restart_server(self):
        pass

    def push_to_box(self, addon, all_file=False):
        for root, dirs, files in os.walk(addon):
            # ignore git files
            if ".git" in root.split(os.sep):
                continue
            if not all_file and os.path.basename(root) not in ['1080i', '720p']:
                continue
            else:
                target = '%saddons/%s%s' % (self.userdata_folder, os.path.basename(addon), root.replace(addon, "").replace('\\', '/'))
                yield command_line("adb", ["shell", "mkdir", target])
            for f in files:
                if f.endswith('.pyc') or f.endswith('.pyo'):
                    continue
                yield push_file(os.path.join(root, f), target)

    def get_log():
        self.adb_pull("%stemp/xbmc.log" % self.userdata_folder)
        self.adb_pull("%stemp/xbmc.old.log" % self.userdata_folder)

    def log(self, text):
        try:
            import sublime
            wnd = sublime.active_window()
            wnd.run_command("log", {"label": line.strip()})
        except:
            log(text)
