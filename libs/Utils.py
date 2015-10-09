# -*- coding: utf8 -*-

# Copyright (C) 2015 - Philipp Temminghoff <phil65@kodi.tv>
# This program is Free Software see LICENSE file for details

"""
SublimeKodi is a plugin to assist with Kodi skinning / scripting using Sublime Text 3
"""


import os
import base64
import json
import colorsys
import codecs
from urllib.request import Request, urlopen
import zipfile
import subprocess
import re
import platform
from threading import Thread
from functools import wraps
import time

from .polib import polib
from lxml import etree as ET


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    """
    Decorator which re-tries the function in case of Exception
    """
    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        log(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry

    return deco_retry


def run_async(func):
    """
    Decorator to put a function into a separate thread
    """
    @wraps(func)
    def async_func(*args, **kwargs):
        func_hl = Thread(target=func, args=args, kwargs=kwargs)
        func_hl.start()
        return func_hl

    return async_func


def check_busy(func):
    """
    Decorator to check for self.is_busy
    Only one of the decorated functions may run simultaniously
    """

    @wraps(func)
    def decorator(self, *args, **kwargs):
        if self.is_busy:
            message_dialog("Already busy. Please wait.")
            return None
        self.is_busy = True
        try:
            func(self, *args, **kwargs)
        except Exception as e:
            message_dialog(e)
        self.is_busy = False
    return decorator


def get_sublime_path():
    """
    get cmd call for different platforms to execute Sublime Text
    """
    if platform.system() in ['Darwin', 'Linux']:
        return "subl"
    elif os.path.exists(os.path.join(os.getcwd(), "sublime_text.exe")):
        return os.path.join(os.getcwd(), "sublime_text.exe")


def get_absolute_file_paths(directory):
    """
    Generate absolute file paths for the given directory
    """
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            yield os.path.abspath(os.path.join(dirpath, f))


def make_archive(folderpath, archive):
    """
    Create zip with path *archive from folder with path *folderpath
    """
    fileList = get_absolute_file_paths(folderpath)
    a = zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED)
    for f in fileList:
        path_list = re.split(r'[\\/]', f)
        rel_path = os.path.relpath(f, folderpath)
        if ".git" in path_list:
            continue
        if rel_path.startswith("media") and not rel_path.endswith(".xbt"):
            continue
        if rel_path.startswith("themes"):
            continue
        if f.endswith(('.pyc', '.pyo', '.zip')):
            continue
        if f.startswith(('.')):
            continue
        a.write(f, rel_path)
        yield rel_path
    a.close()


def to_hex(r, g, b, a=None):
    """
    return rgba hex values for ST tooltip
    """
    if a is None:
        a = 255
    return "#%02X%02X%02X%02X" % (r, g, b, a)


def get_cont_col(col):
    """
    gets contrast color for *col (used to ensure readability)
    """
    (h, l, s) = colorsys.rgb_to_hls(int(col[1:3], 16)/255.0, int(col[3:5], 16)/255.0, int(col[5:7], 16)/255.0)
    l1 = 1 - l
    if abs(l1 - l) < .15:
        l1 = .15
    (r, g, b) = colorsys.hls_to_rgb(h, l1, s)
    return to_hex(int(r * 255), int(g * 255), int(b * 255))  # true complementary


def check_bom(filepath):
    """
    check file *filepath for BOM, return True / False
    """
    file_bytes = min(32, os.path.getsize(filepath))
    with open(filepath, 'rb') as f:
        raw = f.read(file_bytes)
    return raw.startswith(codecs.BOM_UTF8)


def check_paths(paths):
    """
    Return first valid path of *paths list
    """
    for path in paths:
        if os.path.exists(path):
            return path
    return ""


def texturepacker_generator(media_path, settings, xbt_filename="Textures.xbt"):
    """
    yield command line output from running TexturePacker on *media_path,
    also needs *settings for TexturePacker path
    """
    tp_path = settings.get("texturechecker_path")
    if not tp_path:
        return None
    if platform.system() == "Linux":
        args = ['%s -dupecheck -input "%s" -output "%s"' % (tp_path, media_path, os.path.join(media_path, xbt_filename))]
    else:
        args = [tp_path, '-dupecheck', '-input "%s"' % media_path, '-output "%s"' % os.path.join(media_path, xbt_filename)]
    with subprocess.Popen(args, stdout=subprocess.PIPE, bufsize=1, universal_newlines=True, shell=True) as p:
        for line in p.stdout:
            yield line


def check_brackets(label):
    """
    check if all brackets in *label match, return True / False
    """
    stack = []
    pushChars, popChars = "<({[", ">)}]"
    for c in label:
        if c in pushChars:
            stack.append(c)
        elif c in popChars:
            if not stack:
                return False
            else:
                stackTop = stack.pop()
                balancingBracket = pushChars[popChars.index(c)]
                if stackTop != balancingBracket:
                    return False
    return not stack


def find_word(view):
    for region in view.sel():
        if region.begin() == region.end():
            word = view.word(region)
        else:
            word = region
        if not word.empty():
            return view.substr(word)
        else:
            return ""


def get_node_content(view, flags):
    for region in view.sel():
        try:
            bracket_region = view.expand_by_class(region, flags, '<>"[]')
            return view.substr(bracket_region)
        except:
            return ""


def jump_to_label_declaration(view, label_id):
    view.run_command("insert", {"characters": label_id})
    view.hide_popup()


def log(string):
    """
    prefixes "SublimeKodi:" and prints
    """
    print("SublimeKodi: " + str(string))


def prettyprint(string):
    """
    prints properly formatted output for json objects
    """
    print(json.dumps(string, sort_keys=True, indent=4, separators=(',', ': ')))


def message_dialog(label):
    """
    try to show ST message dialog with label *label,
    log() in case it fails
    """
    try:
        import sublime
        sublime.message_dialog(label)
    except:
        log(label)


def get_tags_from_file(path, node_tags):
    """
    returns list of dicts from xml file with path *path containing all nodes with tag name *node_tags
    """
    nodes = []
    if not os.path.exists(path):
        log("%s does not exist" % path)
        return []
    root = get_root_from_file(path)
    if root is None:
        return []
    xpath = ".//" + " | .//".join(node_tags)
    for node in root.xpath(xpath):
        if "name" in node.attrib:
            if node.find("./param") is not None and node.find("./definition") is None:
                continue
            include = {"name": node.attrib["name"],
                       "file": path,
                       "type": node.tag,
                       "content": ET.tostring(node, pretty_print=True, encoding="unicode"),
                       "line": node.sourceline}
            if node.getnext() is not None:
                include["length"] = node.getnext().sourceline - node.sourceline
            nodes.append(include)
    return nodes


def get_po_file(po_file_path):
    """
    return pofile object, go-to-failure in case of exception
    """
    try:
        log("Parsing po file %s" % po_file_path)
        return polib.pofile(po_file_path)
    except Exception as e:
        panel_log("Error in %s:\n %s" % (po_file_path, str(e)))
        return []


def get_root_from_file(xml_file):
    """
    return XML root node from file *filename
    """
    if not xml_file.endswith(".xml"):
        log("Tried to get root from non-xml file")
        return None
    if not os.path.exists(xml_file):
        return None
    try:
        parser = ET.XMLParser(remove_blank_text=True, remove_comments=True)
        tree = ET.parse(xml_file, parser)
        return tree.getroot()
    except Exception as e:
        # log("Error when parsing %s\n%s\nTry again with recover=True..." % (xml_file, e))
        # try:
        #     parser = ET.XMLParser(remove_blank_text=True, recover=True, remove_comments=True)
        #     tree = ET.parse(xml_file, parser)
        #     return tree.getroot()
        # except Exception as e:
        panel_log("Error in %s:\n %s" % (xml_file, str(e)))
        return None


def get_xml_file_paths(xml_path):
    """
    return list with absolute file paths from XML files in *xml_path
    """
    xml_files = []
    if not os.path.exists(xml_path):
        return []
    for xml_file in os.listdir(xml_path):
        filename = os.path.basename(xml_file)
        if filename.endswith(".xml"):
            if filename.lower() not in ["script-skinshortcuts-includes.xml", "font.xml"]:
                xml_files.append(xml_file)
    return xml_files


@run_async
def send_json_request_async(data, settings):
    """
    send JSON command *data to Kodi in separate thread,
    also needs *settings for remote ip etc.
    """
    return send_json_request(data, settings)


def send_json_request(data, settings):
    """
    send JSON command *data to Kodi,
    also needs *settings for remote ip etc.
    """
    address = settings.get("kodi_address", "http://localhost:8080")
    if not address:
        return None
    credentials = '%s:%s' % (settings.get("kodi_username", "kodi"), settings.get("kodi_password", ""))
    encoded_credentials = base64.b64encode(credentials.encode('UTF-8'))
    authorization = b'Basic ' + encoded_credentials
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    json_data = json.dumps(json.loads(data))
    post_data = json_data.encode('utf-8')
    request = Request(address + "/jsonrpc", post_data, headers)
    try:
        result = urlopen(request).read()
        result = json.loads(result.decode("utf-8"))
        prettyprint(result)
        return result
    except:
        return None


def get_refs_from_file(path, xpath):
    """
    load xml file from *path and return dict list for nodes which match *xpath
    """
    font_refs = []
    xml_file = os.path.basename(path)
    root = get_root_from_file(path)
    if root is None:
        return None
    for node in root.xpath(xpath):
        if node.getchildren():
            continue
        item = {"line": node.sourceline,
                "type": node.tag,
                "name": node.text,
                "filename": xml_file,
                "file": path}
        font_refs.append(item)
    return font_refs


def panel_log(text):
    try:
        import sublime
        wnd = sublime.active_window()
        wnd.run_command("log", {"label": text.strip()})
    except Exception as e:
        log(e)
        log(text)
