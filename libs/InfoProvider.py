# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
SublimeKodi is a tool to assist with Kodi skinning / scripting using Sublime Text 3
"""


import os
import re
import string
import platform
import webbrowser
from time import gmtime, strftime

from .Utils import *
from .polib import polib
from .ImageParser import get_image_size

APP_NAME = "kodi"
# c&p from wiki
WINDOW_MAP = [("home", "WINDOW_HOME", " 10000", "0", "Home.xml"),
              ("programs", "WINDOW_PROGRAMS", " 10001", "1", "MyPrograms.xml"),
              ("pictures", "WINDOW_PICTURES", " 10002", "2", "MyPics.xml"),
              ("filemanager", "WINDOW_FILES", "10003", "3", "FileManager.xml"),
              ("settings", "WINDOW_SETTINGS_MENU", "10004", "4", "Settings.xml"),
              ("systeminfo", "WINDOW_SYSTEM_INFORMATION", "10007", "7", "SettingsSystemInfo.xml"),
              ("screencalibration", "WINDOW_MOVIE_CALIBRATION", "10011", "11", "SettingsScreenCalibration.xml"),
              ("picturessettings", "WINDOW_SETTINGS_MYPICTURES", "10012", "12", "SettingsCategory.xml"),
              ("programssettings", "WINDOW_SETTINGS_MYPROGRAMS", "10013", "13", "SettingsCategory.xml"),
              ("weathersettings", "WINDOW_SETTINGS_MYWEATHER", "10014", "14", "SettingsCategory.xml"),
              ("musicsettings", "WINDOW_SETTINGS_MYMUSIC", " 10015", "15", "SettingsCategory.xml"),
              ("systemsettings", "WINDOW_SETTINGS_SYSTEM", "10016", "16", "SettingsCategory.xml"),
              ("videossettings", "WINDOW_SETTINGS_MYVIDEOS", "10017", "17", "SettingsCategory.xml"),
              ("servicesettings", "WINDOW_SETTINGS_SERVICE", " 10018", "18", "SettingsCategory.xml"),
              ("appearancesettings", "WINDOW_SETTINGS_APPEARANCE", "10019", "19", "SettingsCategory.xml"),
              ("pvrsettings", "WINDOW_SETTINGS_MYPVR", "10021", "21", "SettingsCategory.xml"),
              ("videos", "WINDOW_VIDEO_NAV", "10025", "25", "MyVideoNav.xml"),
              ("videoplaylist", "WINDOW_VIDEO_PLAYLIST", "10028", "28", "MyVideoPlaylist.xml"),
              ("loginscreen", "WINDOW_LOGINSCREEN", "10029", "29", "LoginScreen.xml"),
              ("profiles", "WINDOW_SETTINGS_PROFILES", "10034", "34", "SettingsProfile.xml"),
              ("addonbrowser", "WINDOW_ADDON_BROWSER", "10040", "40", "AddonBrowser.xml"),
              ("yesnodialog", "WINDOW_DIALOG_YES_NO", "10100", "100", "DialogYesNo.xml"),
              ("progressdialog", "WINDOW_DIALOG_PROGRESS", "10101", "101", "DialogProgress.xml"),
              ("virtualkeyboard", "WINDOW_DIALOG_KEYBOARD", "10103", "103", "DialogKeyboard.xml"),
              ("volumebar", "WINDOW_DIALOG_VOLUME_BAR", "10104", "104", "DialogVolumeBar.xml"),
              ("contextmenu", "WINDOW_DIALOG_CONTEXT_MENU", "10106", "106", "DialogContextMenu.xml"),
              ("infodialog", "WINDOW_DIALOG_KAI_TOAST", "10107", "107", "DialogKaiToast.xml"),
              ("numericinput", "WINDOW_DIALOG_NUMERIC", "10109", "109", "DialogNumeric.xml"),
              ("shutdownmenu", "WINDOW_DIALOG_BUTTON_MENU", "10111", "111", "DialogButtonMenu.xml"),
              ("mutebug", "WINDOW_DIALOG_MUTE_BUG", "10113", "113", "DialogMuteBug.xml"),
              ("playercontrols", "WINDOW_DIALOG_PLAYER_CONTROLS", "10114", "114", "PlayerControls.xml"),
              ("seekbar", "WINDOW_DIALOG_SEEK_BAR", "10115", "115", "DialogSeekBar.xml"),
              ("musicosd", "WINDOW_DIALOG_MUSIC_OSD", "10120", "120", "MusicOSD.xml"),
              ("visualisationpresetlist", "WINDOW_DIALOG_VIS_PRESET_LIST", "10122", "122", "VisualisationPresetList.xml"),
              ("osdvideosettings", "WINDOW_DIALOG_VIDEO_OSD_SETTINGS", "10123", "123", "VideoOSDSettings.xml"),
              ("osdaudiosettings", "WINDOW_DIALOG_AUDIO_OSD_SETTINGS", "10124", "124", "VideoOSDSettings.xml"),
              ("videobookmarks", "WINDOW_DIALOG_VIDEO_BOOKMARKS", "10125", "125", "VideoOSDBookmarks.xml"),
              ("filebrowser", "WINDOW_DIALOG_FILE_BROWSER", "10126", "126", "FileBrowser.xml"),
              ("networksetup", "WINDOW_DIALOG_NETWORK_SETUP", "10128", "128", "DialogNetworkSetup.xml"),
              ("mediasource", "WINDOW_DIALOG_MEDIA_SOURCE", "10129", "129", "DialogMediaSource.xml"),
              ("profilesettings", "WINDOW_PROFILE_SETTINGS", "10130", "130", "ProfileSettings.xml"),
              ("locksettings", "WINDOW_LOCK_SETTINGS", "10131", "131", "LockSettings.xml"),
              ("contentsettings", "WINDOW_DIALOG_CONTENT_SETTINGS", "10132", "132", "DialogContentSettings.xml"),
              ("favourites", "WINDOW_DIALOG_FAVOURITES", "10134", "134", "DialogFavourites.xml"),
              ("songinformation", "WINDOW_DIALOG_SONG_INFO", "10135", "135", "DialogSongInfo.xml"),
              ("smartplaylisteditor", "WINDOW_DIALOG_SMART_PLAYLIST_EDITOR", "10136", "136", "SmartPlaylistEditor.xml"),
              ("smartplaylistrule", "WINDOW_DIALOG_SMART_PLAYLIST_RULE", "10137", "137", "SmartPlaylistRule.xml"),
              ("busydialog", "WINDOW_DIALOG_BUSY", "10138", "138", "DialogBusy.xml"),
              ("pictureinfo", "WINDOW_DIALOG_PICTURE_INFO", "10139", "139", "DialogPictureInfo.xml"),
              ("addonsettings", "WINDOW_DIALOG_ADDON_SETTINGS", "10140", "140", "DialogAddonSettings.xml"),
              ("fullscreeninfo", "WINDOW_DIALOG_FULLSCREEN_INFO", "10142", "142", "DialogFullScreenInfo.xml"),
              ("karaokeselector", "WINDOW_DIALOG_KARAOKE_SONGSELECT", "10143", "143", "DialogKaraokeSongSelector.xml"),
              ("karaokelargeselector", "WINDOW_DIALOG_KARAOKE_SELECTOR", "10144", "144", "DialogKaraokeSongSelectorLarge.xml"),
              ("sliderdialog", "WINDOW_DIALOG_SLIDER", "10145", "145", "DialogSlider.xml"),
              ("addoninformation", "WINDOW_DIALOG_ADDON_INFO", "10146", "146", "DialogAddonInfo.xml"),
              ("textviewer", "WINDOW_DIALOG_TEXT_VIEWER", "10147", "147", "DialogTextViewer.xml"),
              ("peripherals", "WINDOW_DIALOG_PERIPHERAL_MANAGER", "10149", "149", "DialogPeripheralManager.xml"),
              ("peripheralsettings", "WINDOW_DIALOG_PERIPHERAL_SETTINGS", "10150", "150", "DialogPeripheralSettings.xml"),
              ("extendedprogressdialog", "WINDOW_DIALOG_EXT_PROGRESS", "10151", "151", "DialogExtendedProgressBar.xml"),
              ("mediafilter", "WINDOW_DIALOG_MEDIA_FILTER", "10152", "152", "DialogMediaFilter.xml"),
              ("subtitlesearch", "WINDOW_DIALOG_SUBTITLES", "10153", "153", "DialogSubtitles.xml"),
              ("musicplaylist", "WINDOW_MUSIC_PLAYLIST", "10500", "500", "MyMusicPlaylist.xml"),
              ("musicfiles", "WINDOW_MUSIC_FILES", "10501", "501", "MyMusicSongs.xml"),
              ("musiclibrary", "WINDOW_MUSIC_NAV", "10502", "502", "MyMusicNav.xml"),
              ("musicplaylisteditor", "WINDOW_MUSIC_PLAYLIST_EDITOR", "10503", "503", "MyMusicPlaylistEditor.xml"),
              ("tvchannels", "WINDOW_TV_CHANNELS", "10615", "615", "MyPVRChannels.xml"),
              ("tvrecordings", "WINDOW_TV_RECORDINGS", "10616", "616", "MyPVRRecordings.xml"),
              ("tvguide", "WINDOW_TV_GUIDE", "10617", "617", "MyPVRGuide.xml"),
              ("tvtimers", "WINDOW_TV_TIMERS", "10618", "618", "MyPVRTimers.xml"),
              ("tvsearch", "WINDOW_TV_SEARCH", "10619", "619", "MyPVRSearch.xml"),
              ("radiochannels", "WINDOW_RADIO_CHANNELS", "10620", "620", "MyPVRChannels.xml"),
              ("radiorecordings", "WINDOW_RADIO_RECORDINGS", "10621", "621", "MyPVRRecordings.xml"),
              ("radioguide", "WINDOW_RADIO_GUIDE", "10622", "622", "MyPVRGuide.xml"),
              ("radiotimers", "WINDOW_RADIO_TIMERS", "10623", "623", "MyPVRTimers.xml"),
              ("radiosearch", "WINDOW_RADIO_SEARCH", "10624", "624", "MyPVRSearch.xml"),
              ("pvrguideinfo", "WINDOW_DIALOG_PVR_GUIDE_INFO", "10602", "602", "DialogPVRGuideInfo.xml"),
              ("pvrrecordinginfo", "WINDOW_DIALOG_PVR_RECORDING_INFO", "10603", "603", "DialogPVRRecordingInfo.xml"),
              ("pvrtimersetting", "WINDOW_DIALOG_PVR_TIMER_SETTING", "10604", "604", "DialogPVRTimerSettings.xml"),
              ("pvrgroupmanager", "WINDOW_DIALOG_PVR_GROUP_MANAGER", "10605", "605", "DialogPVRGroupManager.xml"),
              ("pvrchannelmanager", "WINDOW_DIALOG_PVR_CHANNEL_MANAGER", "10606", "606", "DialogPVRChannelManager.xml"),
              ("pvrguidesearch", "WINDOW_DIALOG_PVR_GUIDE_SEARCH", "10607", "607", "DialogPVRGuideSearch.xml"),
              ("pvrosdchannels", "WINDOW_DIALOG_PVR_OSD_CHANNELS", "10610", "610", "DialogPVRChannelsOSD.xml"),
              ("pvrosdguide", "WINDOW_DIALOG_PVR_OSD_GUIDE", "10611", "611", "DialogPVRGuideOSD.xml"),
              ("selectdialog", "WINDOW_DIALOG_SELECT", "12000", "2000", "DialogSelect.xml"),
              ("musicinformation", "WINDOW_MUSIC_INFO", "12001", "2001", "DialogAlbumInfo.xml"),
              ("okdialog", "WINDOW_DIALOG_OK", "12002", "2002", "DialogOK.xml"),
              ("movieinformation", "WINDOW_VIDEO_INFO", "12003", "2003", "DialogVideoInfo.xml"),
              ("fullscreenvideo", "WINDOW_FULLSCREEN_VIDEO", "12005", "2005", "VideoFullScreen.xml"),
              ("visualisation", "WINDOW_VISUALISATION", "12006", "2006", "MusicVisualisation.xml"),
              ("slideshow", "WINDOW_SLIDESHOW", "12007", "2007", "SlideShow.xml"),
              ("filestackingdialog", "WINDOW_DIALOG_FILESTACKING", "12008", "2008", "DialogFileStacking.xml"),
              ("karaoke", "WINDOW_KARAOKELYRICS", "12009", "2009", "MusicKaraokeLyrics.xml"),
              ("weather", "WINDOW_WEATHER", "12600", "2600", "MyWeather.xml"),
              ("videoosd", "WINDOW_OSD", "12901", "2901", "VideoOSD.xml"),
              ("startup", "WINDOW_STARTUP_ANIM", "12999", "2999", "Startup.xml"),
              ("skinsettings", "WINDOW_SKIN_SETTINGS", "10035", "35", "SkinSettings.xml"),
              ("pointer", "-", "-", "105", "Pointer.xml"),
              ("musicoverlay", "WINDOW_MUSIC_OVERLAY", "12903", "2903", "MusicOverlay.xml"),
              ("videooverlay", "WINDOW_VIDEO_OVERLAY", "12904", "2904", "VideoOverlay.xml")]
WINDOW_FILENAMES = [item[4] for item in WINDOW_MAP]
WINDOW_NAMES = [item[0] for item in WINDOW_MAP]
WINDOW_IDS = [item[3] for item in WINDOW_MAP]


class InfoProvider(object):

    def __init__(self):
        self.include_list = {}
        self.include_file_list = {}
        self.window_file_list = {}
        self.color_list = []
        self.po_files = []
        self.addon_xml_file = ""
        self.color_file = ""
        self.project_path = ""
        self.addon_type = ""
        self.addon_name = ""
        self.kodi_po_files = []
        self.fonts = {}
        self.po_files = []
        self.xml_folders = []
        self.addon_po_files = []
        self.load_data()

    def load_data(self):
        """
        loads the xml with control nodes for sanity checking (controls.xml)
        as well as builtins including their help string (data.xml)
        """
        path = os.path.normpath(os.path.abspath(__file__))
        folder_path = os.path.split(path)[0]
        path = os.path.join(folder_path, "controls.xml")
        self.template_root = get_root_from_file(path)
        path = os.path.join(folder_path, "data.xml")
        root = get_root_from_file(path)
        self.builtins = []
        self.conditions = []
        for item in root.find("builtins"):
            self.builtins.append([item.find("code").text, item.find("help").text])
        for item in root.find("conditions"):
            self.conditions.append([item.find("code").text, item.find("help").text])
        # TODO: resolve includes

        # for node in self.template.iterchildren():
        #     log(node.tag)

    def init_addon(self, path):
        """
        scan addon folder and parse skin content etc
        """
        self.addon_type = ""
        self.addon_name = ""
        self.project_path = path
        self.addon_xml_file = check_paths([os.path.join(self.project_path, "addon.xml")])
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
                folder = check_paths(paths)
                self.xml_folders.append(folder)
        self.update_addon_labels()
        if self.xml_folders:
            log("Kodi project detected: " + path)
            self.update_include_list()
            self.update_xml_files()
            self.get_colors()
            self.get_fonts()
            # sublime.status_message("SublimeKodi: successfully loaded addon")

    @property
    def lang_path(self):
        """
        returns the add-on language folder path
        """
        paths = [os.path.join(self.project_path, "resources", "language"),
                 os.path.join(self.project_path, "language")]
        return check_paths(paths)

    @property
    def media_path(self):
        """
        returns the add-on media folder path
        """
        paths = [os.path.join(self.project_path, "media"),
                 os.path.join(self.project_path, "resources", "skins", "Default", "media")]
        return check_paths(paths)

    def get_check_listitems(self, check_type):
        """
        starts check with type check_type and returns result nodes
        """
        self.update_xml_files()
        checks = {"variable": self.check_variables,
                  "include": self.check_includes,
                  "font": self.check_fonts,
                  "label": self.check_labels,
                  "id": self.check_ids,
                  "general": self.check_values}
        return checks[check_type]()

    def check_xml_files(self):
        """
        Checks if the skin contains all core xml window files
        """
        for folder in self.xml_folders:
            for item in WINDOW_FILENAMES:
                if item not in self.window_file_list[folder]:
                    log("Skin does not include %s" % item)

    def get_colors(self):
        """
        create color list by parsing all color files
        """
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
                              "file": file_path}
                self.color_list.append(color_dict)
            log("color list: %i colors found" % len(self.color_list))

    def get_fonts(self):
        """
        create font dict by parsing first fontset
        """
        if not self.addon_xml_file or not self.xml_folders:
            return False
        self.fonts = {}
        for folder in self.xml_folders:
            paths = [os.path.join(self.project_path, folder, "Font.xml"),
                     os.path.join(self.project_path, folder, "font.xml")]
            font_file = check_paths(paths)
            if not font_file:
                return False
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

    def get_userdata_folder(self):
        """
        return userdata folder based on platform and portable setting
        """
        if platform.system() == "Linux":
            return os.path.join(os.path.expanduser("~"), ".%s" % APP_NAME)
        elif platform.system() == "Windows":
            if self.settings.get("portable_mode"):
                return os.path.join(self.settings.get("kodi_path"), "portable_data")
            else:
                return os.path.join(os.getenv('APPDATA'), "%s" % APP_NAME)
        elif platform.system() == "Darwin":
            return os.path.join(os.path.expanduser("~"), "Application Support", "%s" % APP_NAME, "userdata")

    def reload_skin_after_save(self, path):
        """
        update include, color and font infos, depending on open file
        """
        folder = path.split(os.sep)[-2]
        if folder in self.include_file_list:
            if path in self.include_file_list[folder]:
                self.update_include_list()
        if path.endswith("colors/defaults.xml"):
            self.get_colors()
        if path.endswith("ont.xml"):
            self.get_fonts()

    def update_include_list(self):
        """
        create include list by parsing all include files starting with includes.xml
        """
        self.include_list = {}
        for folder in self.xml_folders:
            xml_folder = os.path.join(self.project_path, folder)
            paths = [os.path.join(xml_folder, "Includes.xml"),
                     os.path.join(xml_folder, "includes.xml")]
            self.include_file_list[folder] = []
            self.include_list[folder] = []
            include_file = check_paths(paths)
            self.update_includes(include_file)
            log("Include List: %i nodes found in '%s' folder." % (len(self.include_list[folder]), folder))

    def update_includes(self, xml_file):
        """
        recursive, walks through include files and updates include list and include file list
        """
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
        """
        update list of all include and window xmls
        """
        self.window_file_list = {}
        for path in self.xml_folders:
            xml_folder = os.path.join(self.project_path, path)
            self.window_file_list[path] = get_xml_file_paths(xml_folder)
            log("found %i XMLs in %s" % (len(self.window_file_list[path]), xml_folder))

    def go_to_tag(self, keyword, folder):
        """
        jumps to the definition of ref named keyword
        """
        # TODO: need to add param with ref type
        if not keyword:
            return False
        if keyword.isdigit():
            for po_file in self.po_files:
                for entry in po_file:
                    if entry.msgctxt == "#" + keyword:
                        return "%s:%s" % (po_file.fpath, entry.linenum)
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
                if node["name"] == keyword and node["file"].endswith("defaults.xml"):
                    return "%s:%s" % (node["file"], node["line"])
            log("no node with name %s found" % keyword)
        return False

    def return_node_content(self, keyword=None, return_entry="content", folder=False):
        """
        get value from include list
        """
        if not keyword or not folder:
            return ""
        if folder in self.fonts:
            for node in self.fonts[folder]:
                if node["name"] == keyword:
                    return node[return_entry]
        if folder in self.include_list:
            for node in self.include_list[folder]:
                if node["name"] == keyword:
                    return node[return_entry]
        return ""

    def get_settings(self, settings):
        """
        load settings file
        """
        self.settings = settings
        self.kodi_path = settings.get("kodi_path")
        log("kodi path: " + self.kodi_path)

    def get_kodi_addons(self):
        addon_path = os.path.join(self.get_userdata_folder(), "addons")
        if os.path.exists(addon_path):
            return [f for f in os.listdir(addon_path) if not os.path.isfile(f)]
        else:
            return []

    def return_label(self, selection):
        """
        return formatted label for id in *selection
        """
        tooltips = ""
        if not selection.isdigit():
            return ""
        for po_file in self.po_files:
            hit = po_file.find("#" + selection, by="msgctxt")
            if not hit:
                continue
            folder = po_file.fpath.split(os.sep)[-2]
            if folder == "resources":
                folder = po_file.fpath.split(os.sep)[-3].replace("resource.language.", "")
            if hit.msgstr:
                tooltips += "<b>%s:</b> %s<br>" % (folder, hit.msgstr)
            else:
                tooltips += "<b>%s:</b> %s<br>" % (folder, hit.msgid)
        return tooltips

    def update_builtin_labels(self):
        """
        get core po files
        """
        po_files = self.get_po_files(os.path.join(self.kodi_path, "addons"))
        po_files2 = self.get_po_files(os.path.join(self.kodi_path, "language"))
        po_files3 = self.get_po_files(os.path.join(self.get_userdata_folder(), "addons"))
        self.kodi_po_files = po_files + po_files2 + po_files3

    def update_addon_labels(self):
        """
        get addon po files and update po files list
        """
        self.addon_po_files = self.get_po_files(self.lang_path)
        self.po_files = self.kodi_po_files + self.addon_po_files

    def get_po_files(self, lang_folder_root):
        """
        get list with pofile objects
        """
        po_files = []
        for item in self.settings.get("language_folders"):
            path = check_paths([os.path.join(lang_folder_root, item, "strings.po"),
                                os.path.join(lang_folder_root, item, "resources", "strings.po")])
            if os.path.exists(path):
                po_files.append(get_po_file(path))
        return po_files

    def get_color_info(self, color_string):
        color_info = ""
        for item in self.color_list:
            if item["name"] == color_string:
                color_hex = "#" + item["content"][2:]
                cont_color = get_cont_col(color_hex)
                alpha_percent = round(int(item["content"][:2], 16) / (16 * 16) * 100)
                color_info += '%s&nbsp;<a style="background-color:%s;color:%s">%s</a> %d %% alpha<br>' % (os.path.basename(item["file"]), color_hex, cont_color, item["content"], alpha_percent)
        if color_info:
            return color_info
        if all(c in string.hexdigits for c in color_string) and len(color_string) == 8:
            color_hex = "#" + color_string[2:]
            cont_color = get_cont_col(color_hex)
            alpha_percent = round(int(color_string[:2], 16) / (16 * 16) * 100)
            return '<a style="background-color:%s;color:%s">%d %% alpha</a>' % (color_hex, cont_color, alpha_percent)
        return color_info

    def get_ancestor_info(self, path, line):
        """
        iter through ancestors and return info about absolute position
        """
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
        """
        return formatted string containing font info
        """
        node_content = self.return_node_content(font_name, folder=folder)
        if not node_content:
            return ""
        root = ET.fromstring(node_content)
        label = ""
        for e in root.iterchildren():
            label += "<b>%s:</b> %s<br>" % (e.tag, e.text)
        return label

    def check_variables(self):
        """
        return message listitems containing non-existing / unused variables
        """
        var_regex = "\$(?:ESC)?VAR\[(.*?)\]"
        listitems = []
        for folder in self.xml_folders:
            var_refs = []
            for xml_file in self.window_file_list[folder]:
                path = os.path.join(self.project_path, folder, xml_file)
                with open(path, encoding="utf8", errors="ignore") as f:
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
        """
        return message listitems for non-existing / unused includes
        """
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
                    if ref["name"].startswith("$"):
                        break
                    ref["message"] = "Include not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused include defs
            ref_list = [d['name'] for d in var_refs]
            for node in self.include_list[folder]:
                if node["type"] == "include" and node["name"] not in ref_list:
                    node["message"] = "Unused include: %s" % node["name"]
                    listitems.append(node)
        return listitems

    def build_translate_label(self, label_id, view):
        """
        return correctly formatted translate label based on context
        """
        scope_name = view.scope_name(view.sel()[0].b)
        # TODO: blank string for settings.xml
        if "text.xml" in scope_name and self.addon_type == "python" and 32000 <= label_id <= 33000:
            return "$ADDON[%s %i]" % (self.addon_name, label_id)
        elif "text.xml" in scope_name:
            return "$LOCALIZE[%i]" % label_id
        elif "source.python" in scope_name and 32000 <= label_id <= 33000:
            return "ADDON.getLocalizedString(%i)" % label_id
        elif "source.python" in scope_name:
            return "xbmc.getLocalizedString(%i)" % label_id
        else:
            return str(label_id)

    def translate_path(self, path):
        """
        return translated path for textures
        """
        if path.startswith("special://skin/"):
            return os.path.join(self.project_path, path.replace("special://skin/", ""))
        else:
            return os.path.join(self.media_path, path)

    def get_image_info(self, path):
        imagepath = self.translate_path(path)
        if os.path.exists(imagepath) and not os.path.isdir(imagepath):
            width, height = get_image_size(imagepath)
            file_size = os.path.getsize(imagepath) / 1024
            return "<b>Dimensions:</b> %sx%s <br><b>File size:</b> %.2f kb" % (width, height, file_size)
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
                if ref["name"] not in fontlist + confluence_fonts:
                    ref["message"] = "Font not defined: %s" % ref["name"]
                    listitems.append(ref)
            # find unused font defs
            ref_list = [d['name'] for d in font_refs[folder]]
            if folder in self.fonts:
                for node in self.fonts[folder]:
                    if node["name"] not in ref_list + confluence_fonts:
                        node["message"] = "Unused font: %s" % node["name"]
                        listitems.append(node)
        return listitems

    def check_ids(self):
        window_regex = r"(?:Dialog.Close|Window.IsActive|Window.IsVisible|Window)\(([0-9]+)\)"
        control_regex = "^(?!.*IsActive)(?!.*Window.IsVisible)(?!.*Dialog.Close)(?!.*Window)(?!.*Row)(?!.*Column).*\(([0-9]*?)\)"
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
                                # "region": (match.start(1), match.end(1)),
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
                elif item["name"] in WINDOW_IDS:
                    windowname = WINDOW_NAMES[WINDOW_IDS.index(item["name"])]
                    item["message"] = "Window id: Please use %s instead of %s" % (windowname, item["name"])
                    listitems.append(item)
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
        if info_type in ["VAR", "ESCVAR"]:
            node_content = self.return_node_content(info_id, folder=folder)
            root = ET.fromstring(node_content)
            if root is None:
                return None
            label = ""
            for e in root.iterchildren():
                label += "<b>%s:</b><br>%s<br>" % (e.attrib.get("condition", "fallback"), e.text)
            return label
        elif info_type in ["INFO", "ESCINFO"]:
            data = '{"jsonrpc":"2.0","method":"XBMC.GetInfoLabels","params":{"labels": ["%s"] },"id":1}' % info_id
            result = send_json_request(data, self.settings)
            if result:
                key, value = result["result"].popitem()
                if value:
                    return str(value)
        elif info_type == "LOCALIZE":
            return self.return_label(info_id)
        return ""

    def create_new_po_file(self):
        """
        creates a new pofile and returns it (doesnt save yet)
        """
        po = polib.POFile()
        mail = ""
        actual_date = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        po.metadata = {
            'Project-Id-Version': '1.0',
            'Report-Msgid-Bugs-To': '%s' % mail,
            'POT-Creation-Date': actual_date,
            'PO-Revision-Date': actual_date,
            'Last-Translator': 'you <%s>' % mail,
            'Language-Team': 'English <%s>' % mail,
            'MIME-Version': '1.0',
            'Content-Type': 'text/plain; charset=utf-8',
            'Content-Transfer-Encoding': '8bit',
        }
        return po

    def create_new_label(self, word, filepath, line=""):
        """
        adds a label to the first pofile from settings (or creates new one if non-existing)
        """
        if self.addon_type == "skin":
            start_id = 31000
            index_offset = 0
        else:
            start_id = 32000
            index_offset = 2
        if not self.addon_po_files:
            po = self.create_new_po_file()
            lang_folder = self.settings.get("language_folders")[0]
            if self.addon_type == "skin":
                lang_path = os.path.join(self.project_path, "language", lang_folder)
            else:
                lang_path = os.path.join(self.project_path, "resources", "language", lang_folder)
            if not os.path.exists(lang_path):
                os.makedirs(lang_path)
            lang_path = os.path.join(lang_path, "strings.po")
            self.addon_po_files.append(lang_path)
            message_dialog("New language file created")
        else:
            po = self.addon_po_files[0]
        string_ids = []
        for entry in po:
            try:
                string_ids.append(int(entry.msgctxt[1:]))
            except:
                string_ids.append(entry.msgctxt)
        for label_id in range(start_id, start_id + 1000):
            if label_id not in string_ids:
                log("first free: " + str(label_id))
                break
        msgstr = "#" + str(label_id)
        new_entry = polib.POEntry(msgid=word,
                                  msgstr="",
                                  msgctxt=msgstr,
                                  occurrences=[(filepath, str(line))])
        po_index = int(label_id) - start_id + index_offset
        po.insert(po_index, new_entry)
        po.save(self.addon_po_files[0].fpath)
        self.update_addon_labels()
        return label_id

    def go_to_help(self, word):
        """
        open browser and go to wiki page for control with type *word
        """
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
        # labels = [s.msgid for s in self.po_files]
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
                                "identifier": element.text,
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
                                    "identifier": attr,
                                    "message": 'Label in attribute %s not translated: %s' % (check[1], attr),
                                    "line": element.sourceline}
                            listitems.append(item)
        # check if refs are defined in po files
        label_ids = []
        for po_file in self.po_files:
            label_ids += [entry.msgctxt for entry in po_file]
        for ref in refs:
            if "#" + ref["name"] not in label_ids:
                ref["message"] = "Label not defined: %s" % ref["name"]
                listitems.append(ref)
        return listitems

    def file_list_generator(self):
        if self.xml_folders:
            for folder in self.xml_folders:
                for xml_file in self.window_file_list[folder]:
                    yield os.path.join(self.project_path, folder, xml_file)

    def check_values(self):
        listitems = []
        for path in self.file_list_generator():
            new_items = self.check_file(path)
            listitems.extend(new_items)
        return listitems

    def check_file(self, path):
        xml_file = os.path.basename(path)
        # tags allowed for all controls
        common = ["description", "camera", "depth", "posx", "posy", "top", "bottom", "left", "right", "centertop", "centerbottom", "centerleft", "centerright", "width", "height", "visible", "include", "animation"]
        # tags allowed for containers
        list_common = ["defaultcontrol","focusedlayout", "itemlayout", "content", "onup", "ondown", "onleft", "onright", "oninfo", "onback", "orientation", "preloaditems", "scrolltime", "pagecontrol", "viewtype", "autoscroll", "hitrect"]
        label_common = ["font", "textcolor", "align", "aligny", "label"]
        # allowed child nodes for different control types (+ some other nodes)
        tag_checks = [[".//*[@type='button']/*", common + label_common + ["colordiffuse", "texturefocus", "texturenofocus", "label2", "wrapmultiline", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                          "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                          "focusedcolor", "angle", "hitrect", "enable"]],
                      [".//*[@type='radiobutton']/*", common + label_common + ["colordiffuse", "texturefocus", "texturenofocus", "selected", "disabledcolor", "selectedcolor", "shadowcolor", "textoffsetx",
                                                                               "textoffsety", "pulseonselect", "onclick", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "textwidth",
                                                                               "focusedcolor", "angle", "hitrect", "enable", "textureradioonfocus", "textureradioofffocus", "textureradioondisabled", "textureradiooffdisabled", "textureradioonnofocus",
                                                                               "textureradiooffnofocus", "textureradioon", "textureradiooff", "radioposx", "radioposy", "radiowidth", "radioheight"]],
                      [".//*[@type='spincontrol']/*", common + label_common + ["colordiffuse", "textureup", "textureupfocus", "textureupdisabled", "texturedown", "texturedownfocus", "texturedowndisabled", "spinwidth", "spinheight", "spinposx", "spinposy",
                                                                               "subtype", "disabledcolor", "focusedcolor", "shadowcolor", "textoffsetx", "textoffsety", "pulseonselect", "onfocus", "onunfocus", "onup", "onleft",
                                                                               "onright", "ondown", "onback", "hitrect", "enable", "showonepage", "reverse"]],
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
                      [".//*[@type='grouplist']/*", common + ["control", "align", "itemgap", "orientation", "onfocus", "onunfocus", "onup", "onleft", "onright", "ondown", "onback", "scrolltime", "usecontrolcoords", "defaultcontrol", "pagecontrol"]],
                      [".//*[@type='videowindow']/*", common],
                      [".//*[@type='visualisation']/*", common],
                      [".//*[@type='list']/*", common + list_common],
                      [".//*[@type='wraplist']/*", common + list_common + ["focusposition"]],
                      [".//*[@type='panel']/*", common + list_common],
                      [".//*[@type='fixedlist']/*", common + list_common + ["movement", "focusposition"]],
                      [".//content/*", ["item", "include"]],
                      [".//itemlayout/* | .//focusedlayout/*", ["control", "include"]],
                      ["/includes/*", ["include", "default", "constant", "variable"]],
                      ["/window/*", ["include", "defaultcontrol", "depth", "menucontrol", "onload", "onunload", "controls", "allowoverlay", "views", "coordinates", "animation", "visible", "zorder", "fontset", "backgroundcolor"]],
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
        # TODO: special cases: label for fadelabel
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
                        text = '%s type="%s"' % (node.getparent().tag, node.getparent().attrib["type"])
                    else:
                        text = node.getparent().tag
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "filename": xml_file,
                            "identifier": node.tag,
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
                                "identifier": attr,
                                "message": "invalid attribute for <%s>: %s" % (node.tag, attr),
                                "file": path}
                        listitems.append(item)
        # check conditions in element content
        xpath = ".//" + " | .//".join(bracket_tags)
        for node in root.xpath(xpath):
            if not node.text:
                message = "Empty condition: %s" % (node.tag)
                condition = ""
            elif not check_brackets(node.text):
                condition = str(node.text).replace("  ", "").replace("\t", "")
                message = "Brackets do not match: %s" % (condition)
            else:
                continue
            item = {"line": node.sourceline,
                    "type": node.tag,
                    "filename": xml_file,
                    "identifier": condition,
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
                        "identifier": condition,
                        "message": "Brackets do not match: %s" % (condition),
                        "file": path}
                listitems.append(item)
        # check for noop as empty action
        xpath = ".//" + " | .//".join(noop_tags)
        for node in root.xpath(xpath):
            if node.text == "-" or not node.text:
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "identifier": node.tag,
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
                            "identifier": node.tag,
                            "message": "Invalid multiple tags for %s: <%s>" % (node.getparent().tag, node.tag),
                            "file": path}
                    listitems.append(item)
        # Check tags which require specific values
        for check in allowed_text:
            xpath = ".//" + " | .//".join(check[0])
            for node in root.xpath(xpath):
                if node.text.startswith("$PARAM"):
                    continue
                if node.text.lower() not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "identifier": node.text,
                            "filename": xml_file,
                            "message": "invalid value for %s: %s" % (node.tag, node.text),
                            "file": path}
                    listitems.append(item)
        # Check attributes which require specific values
        for check in allowed_attr:
            for node in root.xpath(".//*[(@%s)]" % check[0]):
                if node.attrib[check[0]].startswith("$PARAM"):
                    continue
                if node.attrib[check[0]] not in check[1]:
                    item = {"line": node.sourceline,
                            "type": node.tag,
                            "identifier": node.attrib[check[0]],
                            "filename": xml_file,
                            "message": "invalid value for %s attribute: %s" % (check[0], node.attrib[check[0]]),
                            "file": path}
                    listitems.append(item)
        return listitems

    def check_file2(self, path):
        root = get_root_from_file(path)
        # xml_file = os.path.basename(path)
        # folder = path.split(os.sep)[-2]
        # root = self.resolve_includes(root, folder)
        log(path)
        if root is None:
            return []
        tree = ET.ElementTree(root)
        listitems = []
        log(self.template_root.tag)
        # find invalid tags
        for template in self.template_root:
            log(template.tag)
            for node in root.xpath(".//*[@type='%s']/*" % template.attrib.get("type")):
                # log("hello")
                pass
        return listitems


