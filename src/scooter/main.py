import enum
import os
import re
import sys
import urllib.parse
from typing import Annotated

import typer


class Scheme(str, enum.Enum):
    VSCODE = "vscode"
    IDEA = "idea"
    FILE = "file"


class Pattern(str, enum.Enum):
    MYPY_PATTERN = "mypy"
    PY_PATTERN = "py"

    def regex(self):
        if self == Pattern.MYPY_PATTERN:
            regex = r"(?P<path>([\w\.]+\/)+\w+\.\w+)(:(?P<line>\d+))?"
        elif self == Pattern.PY_PATTERN:
            regex = r'File "(?P<path>.+?)", line (?P<line>\d+)'

        return re.compile(regex)


def make_url(fullpath, line: str, scheme: Scheme):
    if scheme == Scheme.VSCODE:
        line = f":{line}" if line else ""
        return "vscode://file/" + urllib.parse.quote(fullpath) + line
    if scheme == Scheme.IDEA:
        line = f"&line={line}" if line else ""
        return "idea://open?file=" + urllib.parse.quote(fullpath) + line
    return "file://" + urllib.parse.quote(fullpath)


def osc8(url, text):
    ESC = "\x1b"
    return f"{ESC}]8;;{url}{ESC}\\{text}{ESC}]8;;{ESC}\\"


def cli(
    scheme: Annotated[
        Scheme,
        typer.Option("--scheme", "-s", help="URL scheme used for generated links."),
    ] = Scheme.VSCODE,
    pattern: Annotated[
        Pattern,
        typer.Option("--pattern", "-p", help="Pattern for tool."),
    ] = Pattern.MYPY_PATTERN,
):
    """Linkify relative file paths from stdin using OSC-8."""
    rx = pattern.regex()
    root = os.path.abspath(".")

    for raw in sys.stdin:
        line = raw.rstrip("\n")
        out, last = [], 0
        for m in rx.finditer(line):
            rel = m.group("path")
            ln = m.group("line")
            full = os.path.abspath(os.path.join(root, rel))
            out.append(line[last : m.start()])
            text = m.group(0)  # keep original (includes trailing :)
            if os.path.exists(full):
                url = make_url(full, ln, scheme)
                out.append(osc8(url, text))
            else:
                out.append(text)  # leave as-is if file not found
            last = m.end()
        out.append(line[last:])
        sys.stdout.write(("".join(out)) + "\n")


def main():
    typer.run(cli)


if __name__ == "__main__":
    main()
