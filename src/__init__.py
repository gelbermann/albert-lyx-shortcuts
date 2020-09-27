# -*- coding: utf-8 -*-

# TODO: update description:
"""Loads all LyX shortcuts for quick display and selection.

Usage: "lyxs <full or partial name of symbol>"""

from io import UnsupportedOperation
import os
import pickle
import subprocess
from pprint import pformat
from time import sleep
from typing import List, Tuple
from collections import defaultdict

from albertv0 import *

__iid__ = "PythonInterface/v0.2"
__prettyname__ = "Lyx Shortcuts"
__version__ = "1.0"
__trigger__ = "lyxs "
__author__ = "Niv Gelbermann"
__dependencies__ = []

iconPath = iconLookup("albert")

HOME_DIR = os.environ["HOME"]
PLUGIN_DIR = os.path.join(HOME_DIR, ".lyx_shortcuts_plugin")
BINDINGS_FILE = os.path.join(PLUGIN_DIR, "all_lyx_bindings")

common_bindings = None
PICKLED_COMMON_BINDINGS = os.path.join(PLUGIN_DIR, "common_bindings")

# ---------------------------------------------------------------------------- #
#                                 API Functions                                #
# ---------------------------------------------------------------------------- #


def initialize():
    try:
        os.mkdir(PLUGIN_DIR)
    except FileExistsError:
        pass  # ignore - dir already exists
    # other exceptions are raised to logs

    bindings = collect_bindings()
    with open(BINDINGS_FILE, "w+") as f:
        f.write(bindings)

    global common_bindings
    with open(PICKLED_COMMON_BINDINGS, "rb") as pickle_file:
        try:
            common_bindings = pickle.load(pickle_file)
        except UnsupportedOperation:
            # pickled file doesn't exist yet
            common_bindings = defaultdict(list)

    info(pformat(dict(common_bindings)))  # TODO: remove


# NOTE: currently makes Albert crash completely, for some reason
def finalize():
    #     shutil.rmtree(BINDINGS_FILE)

    global common_bindings
    with open(PICKLED_COMMON_BINDINGS, "wb") as pickle_file:
        pickle.dump(common_bindings, pickle_file)


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


def find_binding(keyword: str) -> List[str]:
    command = f"grep -ie '{keyword}'"
    with open(BINDINGS_FILE) as f:
        bindings = f.read()
    output = subprocess.check_output(command, shell=True, input=bindings.encode())
    return output.decode().expandtabs().splitlines()


def parse_binding_line(line: str) -> Tuple[str, str, str]:
    """Return the binding itself (e.g. '\epsilon') and shortcut (e.g. M-m ...)"""

    binding_segments = line.split('"')
    shortcut = binding_segments[1]
    binding = binding_segments[3]
    if " " in binding:
        binding = binding.split()[-1]

    return shortcut, binding


def save_selection(binding: str):
    pass


def get_binding_items(query):
    global iconPath

    binding_prefix = query.string
    if len(binding_prefix) < 3:
        info("Too short query string - don't bother grepping inside bindings file")
        return

    filtered_bindings = find_binding(binding_prefix)

    results = []

    for line in filtered_bindings[:5]:
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
                ClipAction(text="ClipAction", clipboardText=binding_text),
                FuncAction(
                    text='Saves selected binding in "db"',
                    callable=lambda: save_selection(binding_text),
                ),
            ],
        )

        results.append(item)

    return results
