import os
from lxml import etree as ET


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
    parser = ET.XMLParser(remove_blank_text=True)
    tree = ET.parse(xml_file, parser)
    return tree.getroot()
