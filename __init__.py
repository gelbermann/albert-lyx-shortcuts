# -*- coding: utf-8 -*-

# TODO: update description:
"""Loads all LyX shortcuts for quick display and selection.

Usage: "lyxs <full or partial name of symbol>"""

from pprint import pformat
import tkinter as tk  # TODO: remove
import os
import subprocess
from time import sleep
from typing import List, Tuple

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


# ---------------------------------------------------------------------------- #
#                                 API Functions                                #
# ---------------------------------------------------------------------------- #


def initialize():
    try:
        os.mkdir(PLUGIN_DIR)
    except FileExistsError:
        pass  # ignore - dir already exists
    # for any other error: let it be raised. trace is available in Albert Python extension settings.

    bindings = collect_bindings()
    with open(BINDINGS_FILE, "w+") as f:
        f.write(bindings)


# NOTE: currently makes Albert crash completely, for some reason
# def finalize():
#     shutil.rmtree(BINDINGS_FILE)

#     # TODO: remove
#     shutil.rmtree(os.path.join(PLUGIN_DIR, "last_results"))


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
    bind_segments = line.split('"')
    bind_shortcut = bind_segments[1]
    bind_name = bind_segments[3]
    bind_desc = " ".join(bind_segments[1:])
    return bind_shortcut, bind_name, bind_desc


def get_binding_items(query):
    global iconPath
    # with open(os.path.join(PLUGIN_DIR, "last_results"), "ab") as f:
    #     f.write("handleQuery called")

    binding_prefix = query.string
    if len(binding_prefix) < 3:
        info("Too short query string - don't bother grepping inside bindings file")
        return

    filtered_bindings = find_binding(binding_prefix)

    results = []

    for bind_line in filtered_bindings[:5]:
        binding_shortcut, binding_name, binding_desc = parse_binding_line(bind_line)

        # TODO: add actions (copying parsed binding on item selection)
        item = Item(
            id=__prettyname__,
            icon=iconPath,
            text=binding_name,
            subtext=binding_desc,
            completion=query.rawString,  # TODO: change to something more useful
        )

        results.append(item)

    return results
