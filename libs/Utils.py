import os
from lxml import etree as ET
import sublime
import base64
import json
import threading
import colorsys
from polib import polib
from urllib.request import Request, urlopen
SETTINGS_FILE = 'sublimekodi.sublime-settings'


def tohex(r, g, b, a=None):
    if a is None:
        a = 255
    return "#%02X%02X%02X%02X" % (r, g, b, a)


def get_cont_col(col):
    (h, l, s) = colorsys.rgb_to_hls(int(col[1:3], 16)/255.0, int(col[3:5], 16)/255.0, int(col[5:7], 16)/255.0)
    l1 = 1 - l
    if abs(l1 - l) < .15:
        l1 = .15
    (r, g, b) = colorsys.hls_to_rgb(h, l1, s)
    return tohex(int(r * 255), int(g * 255), int(b * 255))  # true complementary


def checkPaths(paths):
    for path in paths:
        if os.path.exists(path):
            log("found path: %s" % path)
            return path
    return ""


def check_brackets(str):
    stack = []
    pushChars, popChars = "<({[", ">)}]"
    for c in str:
        if c in pushChars:
            stack.append(c)
        elif c in popChars:
            if not len(stack):
                return False
            else:
                stackTop = stack.pop()
                balancingBracket = pushChars[popChars.index(c)]
                if stackTop != balancingBracket:
                    return False
    return not len(stack)


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


def get_node_content(view):
    for region in view.sel():
        try:
            flags = sublime.CLASS_WORD_START | sublime.CLASS_WORD_END
            bracket_region = view.expand_by_class(region, flags, '<>"')
            log(view.substr(bracket_region))
            return view.substr(bracket_region)
        except:
            log("Could not get node content")
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
        xpath = ".//" + " | .//".join(node_tags)
        for node in root.xpath(xpath):
            if "name" in node.attrib:
                if node.find("./param") is not None:
                    continue
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


def get_label_list(po_file_path):
    listitems = []
    try:
        po = polib.pofile(po_file_path)
        for entry in po:
            string = {"id": entry.msgctxt,
                      "line": entry.linenum,
                      "string": entry.msgid,
                      "native_string": entry.msgstr}
            listitems.append(string)
        return listitems
    except Exception as e:
        sublime.message_dialog("Error:\n %s" % (e))
        return []


def get_root_from_file(xml_file):
    try:
        parser = ET.XMLParser(remove_blank_text=True)
        tree = ET.parse(xml_file, parser)
        return tree.getroot()
    except:
        sublime.message_dialog("Error when parsing %s" % xml_file)
        return None


def get_xml_file_paths(xml_path):
    xml_files = []
    if os.path.exists(xml_path):
            for xml_file in os.listdir(xml_path):
                filename = os.path.basename(xml_file)
                if filename.endswith(".xml"):
                    if filename.lower() not in ["script-skinshortcuts-includes.xml", "font.xml"]:
                        xml_files.append(xml_file)
            log("File List: %i files found." % len(xml_files))
            return xml_files
    else:
        return []


def kodi_json_request(data, wait=False):
    request_thread = json_request_thread(data)
    request_thread.start()
    if wait:
        request_thread.join(1)
        return request_thread.result
    else:
        return True


class json_request_thread(threading.Thread):

    def __init__(self, data=None):
        threading.Thread.__init__(self)
        self.data = data
        self.result = None

    def run(self):
        self.result = send_json_request(self.data)
        return True


def send_json_request(data):
    history = sublime.load_settings(SETTINGS_FILE)
    address = history.get("kodi_address", "http://localhost:8080")
    if not address:
        return None
    credentials = '%s:%s' % (history.get("kodi_username", "kodi"), history.get("kodi_password", ""))
    encoded_credentials = base64.b64encode(credentials.encode('UTF-8'))
    authorization = b'Basic ' + encoded_credentials
    headers = {'Content-Type': 'application/json', 'Authorization': authorization}
    json_data = json.dumps(json.loads(data))
    post_data = json_data.encode('utf-8')
    request = Request(address + "/jsonrpc", post_data, headers)
    try:
        result = urlopen(request).read()
        result = json.loads(result.decode("utf-8"))
        log(result)
        return result
    except:
        log("Could not connect to Kodi")
        return None

