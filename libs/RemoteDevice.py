# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
SublimeKodi is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""


from .Utils import *
import os


class RemoteDevice():

    def __init__(self):
        self.is_busy = False
        pass

    def setup(self, settings):
        self.settings = settings
        self.connected = False
        self.userdata_folder = self.settings.get("remote_userdata_folder")
        self.ip = self.settings.get("remote_ip")

    def cmd(self, program, args, log=True):
        command = [program]
        for arg in args:
            command.append(arg)
        self.panel_log(" ".join(command))
        try:
            output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            # log(output.decode("utf-8"))
            if log:
                self.panel_log("%s" % (output.decode("utf-8").replace('\r', '').replace('\n', '')))
        except subprocess.CalledProcessError as e:
            self.panel_log("%s\nErrorCode: %s" % (e, str(e.returncode)))
        except Exception as e:
            self.panel_log(e)
        # proc = subprocess.Popen(['echo', '"to stdout"'],
        #                     stdout=subprocess.PIPE)
        # stdout_value = proc.communicate()[0]

    # @check_busy
    def adb_connect(self, ip):
        self.ip = ip
        self.panel_log("Connect to remote with ip %s" % ip)
        self.cmd("adb", ["connect", str(ip)])
        self.connected = True

    @run_async
    @check_busy
    def adb_connect_async(self, ip):
        self.adb_connect(ip)

    @check_busy
    def adb_reconnect(self, ip=""):
        if not ip:
            ip = self.ip
        self.adb_disconnect()
        self.adb_connect(ip)

    @run_async
    def adb_reconnect_async(self, ip=""):
        self.adb_reconnect(ip)

    # @check_busy
    def adb_disconnect(self):
        self.panel_log("Disconnect from remote")
        self.cmd("adb", ["disconnect"])
        self.connected = False

    @run_async
    @check_busy
    def adb_disconnect_async(self):
        self.adb_disconnect()

    @check_busy
    def adb_push(self, source, target):
        if not target.endswith('/'):
            target += '/'
        self.cmd("adb", ["push", source.replace('\\', '/'), target.replace('\\', '/')])

    @run_async
    @check_busy
    def adb_push_async(self, source, target):
        self.adb_push(source, target)

    @check_busy
    def adb_pull(self, path, target):
        self.cmd("adb", ["pull", path, target])

    @run_async
    @check_busy
    def adb_pull_async(self, path, target):
        self.adb_pull(path, target)

    @run_async
    @check_busy
    def adb_restart_server(self):
        pass

    @run_async
    @check_busy
    def push_to_box(self, addon, all_file=False):
        self.panel_log("push %s to remote" % addon)
        for root, dirs, files in os.walk(addon):
            # ignore git files
            if ".git" in root.split(os.sep):
                continue
            if not all_file and os.path.basename(root) not in ['1080i', '720p']:
                continue
            else:
                target = '%saddons/%s%s' % (self.userdata_folder, os.path.basename(addon), root.replace(addon, "").replace('\\', '/'))
                self.cmd("adb", ["shell", "mkdir", target])
            for f in files:
                if f.endswith(('.pyc', '.pyo')):
                    continue
                self.cmd("adb", ["push", os.path.join(root, f).replace('\\', '/'), target.replace('\\', '/')])
        self.panel_log("All files pushed")

    @run_async
    def get_log(self, open_function, target):
        self.panel_log("Pull logs from remote")
        self.adb_pull("%stemp/xbmc.log" % self.userdata_folder, target)
        # self.adb_pull("%stemp/xbmc.old.log" % self.userdata_folder)
        self.panel_log("Finished pulling logs")
        open_function(os.path.join(target, "xbmc.log"))

    @run_async
    @check_busy
    def get_screenshot(self, f_open, target):
        self.panel_log("Pull screenshot from remote")
        self.cmd("adb", ["shell", "screencap", "-p", "/sdcard/screen.png"])
        self.cmd("adb", ["pull", "/sdcard/screen.png", target])
        self.cmd("adb", ["shell", "rm", "/sdcard/screen.png"])
        # self.adb_pull("%stemp/xbmc.old.log" % self.userdata_folder)
        self.panel_log("Finished pulling screenshot")
        f_open(os.path.join(target, "screen.png"))

    @run_async
    @check_busy
    def clear_cache(self):
        self.cmd("adb", ["shell", "rm", "-rf", os.path.join(self.userdata_folder, "temp")])

    @run_async
    def reboot(self):
        self.cmd("adb", ["reboot"])

    def panel_log(self, text):
        try:
            import sublime
            wnd = sublime.active_window()
            wnd.run_command("log", {"label": text.strip()})
        except Exception as e:
            log(e)
            log(text)
