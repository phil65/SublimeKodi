import os
from lxml import etree as ET
import sublime
import base64
import json
import threading
from urllib.request import Request, urlopen
SETTINGS_FILE = 'sublimekodi.sublime-settings'


def checkPaths(paths):
    for path in paths:
        if os.path.exists(path):
            log("found path: %s" % path)
            return path
    return ""


def findWord(view):
    for region in view.sel():
        if region.begin() == region.end():
            word = view.word(region)
        else:
            word = region
        if not word.empty():
            return view.substr(word)
        else:
            return ""


def jump_to_label_declaration(view, label_id):
    view.run_command("insert", {"characters": label_id})
    view.hide_popup()


def log(string):
    print("SublimeKodi: " + str(string))


def get_tags_from_file(path, node_tags):
    nodes = []
    if os.path.exists(path):
        root = get_root_from_file(path)
        for node_tag in node_tags:
            for node in root.findall(node_tag):
                if "name" in node.attrib:
                    include = {"name": node.attrib["name"],
                               "file": path,
                               "type": node.tag,
                               "content": ET.tostring(node, pretty_print=True),
                               "line": node.sourceline}
                    if node.getnext() is not None:
                        include["length"] = node.getnext().sourceline - node.sourceline
                    nodes.append(include)
    else:
        log("%s does not exist" % path)
    return nodes


def get_root_from_file(xml_file):
    try:
        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(xml_file, parser)
        return tree.getroot()
    except:
        sublime.message_dialog("Error when parsing %s" % xml_file)
        return None


def get_include_file_paths(xml_path):
    if xml_path:
        paths = [os.path.join(xml_path, "Includes.xml"),
                 os.path.join(xml_path, "includes.xml")]
        include_file = checkPaths(paths)
        if include_file:
            log("found include file: " + include_file)
            root = get_root_from_file(include_file)
            include_file_list = [include_file]
            for node in root.findall("include"):
                if "file" in node.attrib:
                    include_file_list.append(os.path.join(xml_path, node.attrib["file"]))
            log("File List: %i files found." % len(include_file_list))
            return include_file_list
        else:
            log("Could not find include file")
            log(paths)
            return []
    else:
        return []


def get_xml_file_paths(xml_path):
    xml_files = []
    if os.path.exists(xml_path):
            for xml_file in os.listdir(xml_path):
                if xml_file.endswith(".xml"):
                    xml_files.append(xml_file)
            log("File List: %i files found." % len(xml_files))
            return xml_files
    else:
        return []


def kodi_json_request(data, wait=False):
    request_thread = json_request_thread(data)
    request_thread.start()
    if wait:
        request_thread.join()
        return request_thread.result
    else:
        return True


class json_request_thread(threading.Thread):

    def __init__(self, data=None):
        threading.Thread.__init__(self)
        self.data = data
        self.result = None

    def run(self):
        history = sublime.load_settings(SETTINGS_FILE)
        address = history.get("kodi_address", "http://localhost:8080") + "/jsonrpc"
        credentials = '%s:%s' % (history.get("kodi_username", "kodi"), history.get("kodi_password", ""))
        encoded_credentials = base64.b64encode(credentials.encode('UTF-8'))
        authorization = b'Basic ' + encoded_credentials
        headers = {'Content-Type': 'application/json', 'Authorization': authorization}
        json_data = json.dumps(json.loads(self.data))
        post_data = json_data.encode('utf-8')
        request = Request(address, post_data, headers)
        result = urlopen(request).read()
        result = json.loads(result.decode("utf-8"))
        log(result)
        self.result = result
        return result
