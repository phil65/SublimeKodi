import os
from lxml import etree as ET
import base64
import json
import threading
import colorsys
import codecs
from polib import polib
from urllib.request import Request, urlopen


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


def check_bom(filename):

    bytes = min(32, os.path.getsize(filename))
    raw = open(filename, 'rb').read(bytes)

    if raw.startswith(codecs.BOM_UTF8):
        return True
    else:
        return False


def checkPaths(paths):
    for path in paths:
        if os.path.exists(path):
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
    print("SublimeKodi: " + str(string))


def message_dialog(string):
    try:
        import sublime
        sublime.message_dialog(string)
    except:
        log(string)


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
        po_file_content = codecs.open(po_file_path, "r", "utf-8").read()
        po = polib.pofile(po_file_content)
        for entry in po:
            string = {"id": entry.msgctxt,
                      "line": entry.linenum,
                      "string": entry.msgid,
                      "native_string": entry.msgstr}
            listitems.append(string)
        return listitems
    except Exception as e:
        log(po_file_path)
        log(e)
        message_dialog("Error:\n %s" % (e))
        return []


def get_root_from_file(xml_file):
    try:
        parser = ET.XMLParser(remove_blank_text=True, remove_comments=True)
        tree = ET.parse(xml_file, parser)
        return tree.getroot()
    except Exception as e:
        log("Error when parsing %s\n%s\nTry again with recover=True..." % (xml_file, e))
        try:
            parser = ET.XMLParser(remove_blank_text=True, recover=True, remove_comments=True)
            tree = ET.parse(xml_file, parser)
            return tree.getroot()
        except Exception as e:
            message_dialog("Could not load %s" % (xml_file, e))
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


def kodi_json_request(data, wait=False, settings=None):
    request_thread = json_request_thread(data, settings)
    request_thread.start()
    if wait:
        request_thread.join(1)
        return request_thread.result
    else:
        return True


class json_request_thread(threading.Thread):

    def __init__(self, data=None, settings=None):
        threading.Thread.__init__(self)
        self.data = data
        self.result = None
        self.settings = settings

    def run(self):
        self.result = send_json_request(self.data, self.settings)
        return True


def send_json_request(data, settings):
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
        log(result)
        return result
    except:
        return None


def get_refs_from_file(path, xpath):
    font_refs = []
    xml_file = os.path.basename(path)
    root = get_root_from_file(path)
    if root is not None:
        for node in root.xpath(xpath):
            if not node.getchildren():
                item = {"line": node.sourceline,
                        "type": node.tag,
                        "name": node.text,
                        "filename": xml_file,
                        "file": path}
                font_refs.append(item)
    return font_refs
