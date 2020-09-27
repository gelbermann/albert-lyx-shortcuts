# -*- coding: utf-8 -*-

"""Loads all LyX shortcuts for quick display and selection.

Usage: "lyxs <full or partial name of symbol>"""

import json
import os
import subprocess
from collections import defaultdict
from pprint import pformat
from typing import Dict, List, Tuple
from types import SimpleNamespace as Namespace

from albertv0 import *

__iid__ = "PythonInterface/v0.2"
__prettyname__ = "Lyx Shortcuts"
__version__ = "1.0"
__trigger__ = "lyxs "
__author__ = "Niv Gelbermann"
__dependencies__ = []

# -------------------------------- Global vars ------------------------------- #

iconPath = iconLookup("albert")
HOME_DIR = os.environ["HOME"]
PLUGIN_DIR = os.path.join(HOME_DIR, ".lyx_shortcuts_plugin")
BINDINGS_FILE = os.path.join(PLUGIN_DIR, "all_lyx_bindings")
JSON_COMMON_BINDINGS = os.path.join(PLUGIN_DIR, "common_bindings")
common_bindings = None


# ---------------------------------------------------------------------------- #
#                                 API Functions                                #
# ---------------------------------------------------------------------------- #


def initialize():
    if not os.path.exists(PLUGIN_DIR):
        os.mkdir(PLUGIN_DIR)

    bindings = collect_bindings()
    with open(BINDINGS_FILE, "w+") as f:
        f.write(bindings)

    global common_bindings
    if os.path.exists(JSON_COMMON_BINDINGS):
        with open(JSON_COMMON_BINDINGS, "r") as f:
            # https://pynative.com/python-convert-json-data-into-custom-python-object/
            common_bindings = json.load(f, cls=CBCDecoder)
    else:
        common_bindings = CommonBindingsCollector()
    info(common_bindings)  # TODO: remove


def finalize():
    global common_bindings
    info(common_bindings)  # TODO: remove
    with open(JSON_COMMON_BINDINGS, "w") as f:
        json.dump(common_bindings, f, cls=CBCEncoder)


def handleQuery(query):
    if not query.isTriggered:
        return

    return get_binding_items(query)


# ---------------------------------------------------------------------------- #
#                                Logic Functions                               #
# ---------------------------------------------------------------------------- #

# version of `collect_bindings` relying on os module
def collect_bindings() -> str:
    def get_from_path(bindings_dir: str) -> str:
        bindings = ""
        for path, dirs, files in os.walk(bindings_dir):
            for file in files:
                if ".bind" not in file:
                    continue
                with open(os.path.join(path, file), "r") as f:
                    bindings += f.read()
        return bindings

    default_bindings = get_from_path("/usr/share/lyx/bind/")
    user_bindings = get_from_path("~/.lyx/bind/")

    return default_bindings + user_bindings


# version of `collect_bindings` relying on bash
# def collect_bindings() -> None:
#     p = subprocess.call(os.path.join(os.getcwd(), "collect_bindings.sh"))


def grep_binding(keyword: str, amount: int) -> List[str]:
    if len(keyword) < 3:
        info("Too short query string - don't bother grepping inside bindings file")
        return []

    # Search for keyword in file,
    # while IGNORING bindings whose value is "self-insert" and nothing more
    command = f'grep -ie "{keyword}" | grep -v "self-insert"'

    with open(BINDINGS_FILE) as f:
        bindings = f.read()
    output = subprocess.check_output(command, shell=True, input=bindings.encode())
    return output.decode().expandtabs().splitlines()[:amount]


def parse_binding_line(line: str) -> Tuple[str, str, str]:
    """Returns the binding itself (e.g. '\epsilon') and shortcut (e.g. M-m ...)"""

    binding_segments = line.split('"')
    shortcut = binding_segments[1]
    binding = binding_segments[3]
    if " " in binding:
        binding = binding.split()[-1]

    return shortcut, binding


def get_binding_items(query):
    global iconPath, common_bindings

    binding_prefix = query.string
    filtered_bindings = grep_binding(binding_prefix, amount=5)

    results = []
    for line in filtered_bindings:
        info(line)
        binding_shortcut, binding_text = parse_binding_line(line)
        # info(binding_shortcut)
        # info(binding_text)
        item = Item(
            id=__prettyname__,
            icon=iconPath,
            text=binding_text,
            subtext=binding_shortcut,
            completion=query.rawString,
            actions=[
                # FuncAction(
                #     text='Saves selected binding in "db"',
                #     callable=lambda: common_bindings.save_selection(binding_text),
                # ),
                ClipAction(text="ClipAction", clipboardText=binding_text),
            ],
        )
        results.append(item)

    return results


class CommonBindingsCollector:
    def __init__(self, binding_to_count={}, count_to_bindings={}):
        self.binding_to_count = defaultdict(int)
        self.binding_to_count.update(binding_to_count)
        self.count_to_bindings = defaultdict(list)
        self.count_to_bindings.update(count_to_bindings)

    def save_selection(self, binding: str):
        info(f"Saving binding '{binding}' in db")
        info(f"db: {pformat(self)}")
        prev_count = self.binding_to_count[binding]
        self.binding_to_count[binding] += 1
        self.count_to_bindings[prev_count + 1].append(binding)

        if prev_count != 0:
            self.count_to_bindings[prev_count].remove(binding)
            if self.count_to_bindings[prev_count] == []:
                del self.count_to_bindings[prev_count]

    # "My rule of thumb: __repr__ is for developers, __str__ is for customers."
    def __repr__(self):
        s1 = f"Bindings -> count: \n{pformat(dict(self.binding_to_count))}"
        s2 = f"Count -> bindings with count: \n{pformat(dict(self.count_to_bindings))}"
        return f"\n{s1}\n{s2}"

    def toJson(self):
        return json.dumps(self.__dict__)


class CBCEncoder(json.JSONEncoder):
    """ Encoder for CommonBindingsCollector objects """

    def default(self, o):
        return o.__dict__


class CBCDecoder(json.JSONDecoder):
    """ Encoder for CommonBindingsCollector objects """

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, d: Dict):
        if "binding_to_count" in d:
            # 'if' is required for using `object_hook`, since it operates recursively on
            # each member of every key in d
            return CommonBindingsCollector(
                d["binding_to_count"], d["count_to_bindings"]
            )
        return d
