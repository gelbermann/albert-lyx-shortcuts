# -*- coding: utf-8 -*-

"""Loads all LyX shortcuts for quick display and selection.

Usage: "l <full or partial name of symbol>"""

import json
import os
import subprocess
from collections import defaultdict
from pprint import pformat
from subprocess import CalledProcessError
from typing import Dict, List, Tuple

from albertv0 import *

__iid__ = "PythonInterface/v0.2"
__prettyname__ = "Lyx Shortcuts"
__version__ = "1.0"
__trigger__ = "l "
__author__ = "Niv Gelbermann"
__dependencies__ = []

# -------------------------------- Global Vars ------------------------------- #

MIN_QUERY_LENGTH = 2
ICON_PATH = iconLookup("albert")
HOME_DIR = os.environ["HOME"]
PLUGIN_DIR = os.path.join(HOME_DIR, ".lyx_shortcuts_plugin")
BINDINGS_FILE = os.path.join(PLUGIN_DIR, "all_lyx_bindings")
JSON_COMMON_BINDINGS = os.path.join(PLUGIN_DIR, "common_bindings")
ITEMS_AMOUNT = 5
statistics = None
default_items = []
all_bindings = []


# ---------------------------------------------------------------------------- #
#                             Albert API Functions                             #
# ---------------------------------------------------------------------------- #


def initialize():
    my_initialize()


def finalize():
    global statistics
    info(statistics)  # TODO: remove
    with open(JSON_COMMON_BINDINGS, "w") as f:
        json.dump(statistics, f, cls=StatisticsEncoder)


def handleQuery(query):
    if not query.isTriggered:
        return

    return my_handle_query(query)


# ---------------------------------------------------------------------------- #
#                                Logic Functions                               #
# ---------------------------------------------------------------------------- #


def my_initialize():
    # create hidden dir for plugin files
    if not os.path.exists(PLUGIN_DIR):
        os.mkdir(PLUGIN_DIR)

    bindings = collect_bindings()
    with open(BINDINGS_FILE, "w+") as f:
        f.write(bindings)

    # TODO: combine with above 'open' block
    global all_bindings
    with open(BINDINGS_FILE, "r") as f:
        all_bindings = [
            line.expandtabs()
            for line in f.readlines()
            if line.startswith("\\bind") and "self-insert" not in line
        ]

    global statistics
    if os.path.exists(JSON_COMMON_BINDINGS):
        with open(JSON_COMMON_BINDINGS, "r") as f:
            # https://pynative.com/python-convert-json-data-into-custom-python-object/
            statistics = json.load(f, cls=StatisticsDecoder)
    else:
        statistics = Statistics()
    info(statistics)  # TODO: remove

    global default_items
    for binding, shortcut in statistics.most_common(ITEMS_AMOUNT):
        item = Item(
            id=__prettyname__,
            icon=ICON_PATH,
            text=binding,
            subtext=shortcut,
            completion=binding,
            actions=[
                FuncAction(
                    text="Records selected binding and adds to clipboard",
                    callable=lambda: selection(binding, shortcut),
                ),
            ],
        )
        default_items.append(item)


def collect_bindings() -> str:
    """ Collect all LyX binding files available in user's system """

    def get_from_path(bindings_dir: str) -> str:
        bindings = ""
        for path, _, files in os.walk(bindings_dir):
            for file in files:
                if ".bind" not in file:
                    continue
                with open(os.path.join(path, file), "r") as f:
                    bindings += f.read()
        return bindings

    default_bindings = get_from_path("/usr/share/lyx/bind/")
    user_bindings = get_from_path("~/.lyx/bind/")

    return default_bindings + user_bindings


def grep_binding(keyword: str, amount: int) -> List[str]:
    filtered_bindings = []
    global all_bindings
    for line in all_bindings:
        if keyword in line:
            filtered_bindings.append(line)
            if len(filtered_bindings) == amount:
                break
    return filtered_bindings


def parse_binding_line(line: str) -> Tuple[str, str, str]:
    """Returns the binding itself (e.g. '\epsilon') and shortcut (e.g. M-m ...)"""
    binding_segments = line.split('"')
    shortcut = binding_segments[1]
    binding = binding_segments[3]
    if " " in binding:
        binding = binding.split()[-1]

    return shortcut, binding


def my_handle_query(query):
    if len(query.string) < MIN_QUERY_LENGTH:
        info("Short query -> displaying most common bindings")
        global default_items
        return default_items

    else:
        return get_binding_items(query)


def get_binding_items(query):
    binding_prefix = query.string
    filtered_bindings = grep_binding(binding_prefix, amount=ITEMS_AMOUNT)

    results = []
    for line in filtered_bindings:
        binding_shortcut, binding_text = parse_binding_line(line)
        item = Item(
            id=__prettyname__,
            icon=ICON_PATH,
            text=binding_text,
            subtext=binding_shortcut,
            completion=query.rawString,
            actions=[
                # FuncAction(
                #     text='Records selected binding and adds to clipboard',
                #     callable=lambda: common_bindings.save_selection(binding_text),
                # ),
                # ClipAction(text="ClipAction", clipboardText=binding_text),
                FuncAction(
                    text="Records selected binding and adds to clipboard",
                    callable=lambda: selection(binding_text, binding_shortcut),
                ),
            ],
        )
        results.append(item)
    return results


# It seems that adding both FuncAction and ClipAction (or generally, more than a single Action per Item)
# doesn't work as expected. Instead, only the first action is triggered.
# TODO: Open an issue about this.
# As a workaround, this function includes all the actions expected to happen on Item selection.
def selection(binding: str, shortcut: str):
    global statistics
    statistics.save_selection(binding, shortcut)

    # assumes `xclip` is installed # TODO: add to README.md
    try:
        subprocess.Popen(f'echo "{binding}" | xclip -selection clipboard', shell=True)
    except subprocess.SubprocessError:
        info('Child process, failed. Verify that you have "xclip" installed.')


# ---------------------------------------------------------------------------- #
#                                 Logic Classes                                #
# ---------------------------------------------------------------------------- #


class Statistics:
    def __init__(
        self,
        binding_to_count=dict(),
        binding_to_shortcut=dict(),
        count_to_bindings=dict(),
    ):
        self.binding_to_count = defaultdict(int)
        self.binding_to_count.update(binding_to_count)
        self.binding_to_shortcut = dict()
        self.binding_to_shortcut.update(binding_to_shortcut)
        self.count_to_bindings = defaultdict(list)
        self.count_to_bindings.update(count_to_bindings)

    def save_selection(self, binding: str, shortcut: str):
        prev_count = self.binding_to_count[binding]
        self.binding_to_count[binding] += 1
        self.binding_to_shortcut[binding] = shortcut
        self.count_to_bindings[prev_count + 1].append(binding)

        if prev_count != 0:
            self.count_to_bindings[prev_count].remove(binding)
            if self.count_to_bindings[prev_count] == []:
                del self.count_to_bindings[prev_count]

    # "My rule of thumb: __repr__ is for developers, __str__ is for customers."
    def __repr__(self):
        s1 = f"Binding -> count: \n{pformat(dict(self.binding_to_count))}"
        s3 = f"Binding -> shortcut: \n{pformat(dict(self.binding_to_shortcut))}"
        s2 = f"Count -> bindings with count: \n{pformat(dict(self.count_to_bindings))}"
        return f"\n{s1}\n{s2}\n{s3}"

    def most_common(self, amount: int) -> List[Tuple[str, str]]:
        keys = sorted(self.count_to_bindings.keys())[-amount:]
        res = []
        for count in keys:
            bindings = self.count_to_bindings[count]
            for binding in bindings:
                if len(res) != amount:
                    res.append((binding, self.binding_to_shortcut[binding]))
        return res


class StatisticsEncoder(json.JSONEncoder):
    """ Encoder for CommonBindingsCollector objects """

    def default(self, o):
        return o.__dict__


class StatisticsDecoder(json.JSONDecoder):
    """ Encoder for CommonBindingsCollector objects """

    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, d: Dict):
        if "binding_to_count" in d:
            # 'if' is required for using `object_hook`, since it operates recursively on
            # each member of every key in d
            return Statistics(
                d["binding_to_count"],
                d["binding_to_shortcut"],
                # Restore integer keys from str keys (e.g. restore key 1 from serialized key "1") for d["count_to_bindings"]
                {int(key): val for (key, val) in d["count_to_bindings"].items()},
            )
        return d
