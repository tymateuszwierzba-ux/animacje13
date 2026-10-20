"""Static checks for the generated datapacks."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"

FUNC_RE = re.compile(r"function\s+([a-z0-9_.\-]+:[a-z0-9_./\-]+)")
DIALOG_RE = re.compile(r'dialog\s+show\s+\S+\s+([a-z0-9_.\-]+:[a-z0-9_./\-]+)')
TAG_JSON_RE = re.compile(r'"dialog"\s*:\s*"([a-z0-9_.\-]+:[a-z0-9_./\-]+)"')
MACRO_RE = re.compile(r"\$\(([a-zA-Z0-9_]+)\)")


def strip_quotes(line: str) -> str:
    out = []
    in_str = False
    esc = False
    for ch in line:
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        out.append(ch)
    return "".join(out)


def balance(line: str) -> bool:
    s = strip_quotes(line)
    stack = []
    pairs = {")": "(", "]": "[", "}": "{"}
    for ch in s:
        if ch in "([{":
            stack.append(ch)
        elif ch in ")]}":
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


SCORE_KEYWORDS = {
    "if", "unless", "run", "as", "at", "in", "on", "positioned", "rotated",
    "facing", "align", "anchored", "store", "summon",
}
SCORE_OPS = {"<", "<=", "=", ">", ">=", "matches"}


def strip_json_strings(line: str) -> str:
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)


def check_scores(line: str) -> list[str]:
    """Validate argument arity of scoreboard clauses (catches stray objectives)."""
    errors: list[str] = []
    text = strip_json_strings(line)
    for match in re.finditer(r"\b(?:if|unless) score ", text):
        toks = text[match.end():].split()
        if len(toks) < 4:
            errors.append("if score: too few arguments")
            continue
        op = toks[2]
        if op not in SCORE_OPS:
            errors.append(f"if score: bad operator {op!r}")
            continue
        need = 1 if op == "matches" else 2
        rest = toks[3:]
        if len(rest) < need:
            errors.append("if score: missing operands")
            continue
        nxt = rest[need] if len(rest) > need else None
        if nxt is not None and nxt not in SCORE_KEYWORDS:
            errors.append(f"if score: unexpected token {nxt!r}")
    for match in re.finditer(r"scoreboard players operation ", text):
        toks = text[match.end():].split()
        if len(toks) != 5:
            errors.append(f"scoreboard operation: expected 5 arguments, got {len(toks)}")
    return errors


def check_snbt(line: str) -> list[str]:
    """Very small SNBT parser used to spot duplicate keys and broken compounds."""
    errors: list[str] = []
    i = 0
    n = len(line)

    def ws():
        nonlocal i
        while i < n and line[i] in " \t":
            i += 1

    def string():
        nonlocal i
        quote = line[i]
        i += 1
        while i < n:
            if line[i] == "\\":
                i += 2
                continue
            if line[i] == quote:
                i += 1
                return
            i += 1
        errors.append("unterminated string")

    def number():
        nonlocal i
        m = re.match(r"-?\d+(\.\d+)?([eE][+-]?\d+)?[bBsSlLfFdD]?", line[i:])
        if not m:
            errors.append(f"bad number at {line[i:i+12]}")
            i += 1
            return
        i += len(m.group(0))

    def value():
        nonlocal i
        ws()
        if i >= n:
            errors.append("unexpected end")
            return
        ch = line[i]
        if ch == '"' or ch == "'":
            string()
        elif ch == "{":
            compound()
        elif ch == "[":
            array()
        elif ch.isdigit() or ch == "-" or ch == "+":
            number()
        elif line.startswith("true", i) or line.startswith("false", i):
            i += 5 if line.startswith("false", i) else 4
        else:
            m = re.match(r"[A-Za-z_][A-Za-z0-9_./\-]*", line[i:])
            if not m:
                errors.append(f"bad value at {line[i:i+16]}")
                i += 1
                return
            i += len(m.group(0))

    def array():
        nonlocal i
        i += 1
        ws()
        if i < n and line[i] == "]":
            i += 1
            return
        while i < n:
            value()
            ws()
            if i < n and line[i] == ",":
                i += 1
                continue
            if i < n and line[i] == "]":
                i += 1
                return
            errors.append(f"bad array at {line[i:i+16]}")
            i += 1
            return

    def compound():
        nonlocal i
        i += 1
        keys = set()
        ws()
        if i < n and line[i] == "}":
            i += 1
            return
        while i < n:
            ws()
            key = None
            if i < n and line[i] in "\"'":
                start = i
                string()
                key = line[start + 1 : i - 1]
            else:
                m = re.match(r"[A-Za-z_][A-Za-z0-9_.\-+/]*", line[i:])
                if not m:
                    errors.append(f"bad key at {line[i:i+16]}")
                    i += 1
                    return
                key = m.group(0)
                i += len(key)
            if key in keys:
                errors.append(f"duplicate key {key}")
            keys.add(key)
            ws()
            if i >= n or line[i] != ":":
                errors.append(f"missing colon for {key}")
                return
            i += 1
            value()
            ws()
            if i < n and line[i] == ",":
                i += 1
                continue
            if i < n and line[i] == "}":
                i += 1
                return
            errors.append(f"bad compound at {line[i:i+16]}")
            return

    if line.startswith("{"):
        compound()
    elif line.startswith("["):
        array()
    else:
        return errors
    ws()
    if i != n:
        errors.append(f"trailing data at {line[i:i+16]}")
    return errors


def extract_nbt(command: str) -> str | None:
    # first top-level {...} or [...] argument
    for token in (" {", " served ", " value ", " value{", " run summon "):
        pass
    depth = 0
    start = None
    in_str = False
    esc = False
    for idx, ch in enumerate(command):
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
            continue
        if ch in "{[":
            if depth == 0:
                start = idx
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0 and start is not None:
                return command[start : idx + 1]
    return None


def main() -> int:
    problems: list[str] = []
    for version_dir in sorted(BUILD.iterdir()):
        if not version_dir.is_dir():
            continue
        label = version_dir.name
        func_dir = version_dir / "data/gti/function"
        dialog_dir = version_dir / "data/gti/dialog"
        funcs = {p.relative_to(func_dir).with_suffix("").as_posix(): p for p in func_dir.rglob("*.mcfunction")}
        dialogs = {p.relative_to(dialog_dir).with_suffix("").as_posix() for p in dialog_dir.rglob("*.json")}

        # JSON validity
        for path in version_dir.rglob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append(f"{label}: invalid JSON {path.relative_to(version_dir)}: {exc}")

        for name, path in funcs.items():
            text = path.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                if not balance(line):
                    problems.append(f"{label}:{name}:{lineno}: unbalanced brackets")
                    continue
                for err in check_scores(line):
                    problems.append(f"{label}:{name}:{lineno}: {err}")
                macros = []
                if line.startswith("$"):
                    macros = MACRO_RE.findall(line)
                    rendered = MACRO_RE.sub("0", line[1:])
                else:
                    rendered = line
                if line.startswith("$") and not macros:
                    problems.append(f"{label}:{name}:{lineno}: macro marker without macros")
                ref_scan = strip_quotes(rendered)
                if rendered.startswith(("tellraw ", "title ")):
                    ref_scan = ""
                for fn in FUNC_RE.findall(ref_scan):
                    if not fn.startswith("gti:"):
                        continue
                    target = fn.split(":", 1)[1]
                    if target not in funcs:
                        problems.append(f"{label}:{name}:{lineno}: missing function {fn}")
                for dl in DIALOG_RE.findall(ref_scan):
                    if dl.startswith("gti:") and dl.split(":", 1)[1] not in dialogs:
                        problems.append(f"{label}:{name}:{lineno}: missing dialog {dl}")
                rendered = MACRO_RE.sub("0", line[1:]) if line.startswith("$") else line
                payload = None
                if " run summon " in rendered:
                    payload = rendered.split(" run summon ", 1)[1].split(" ", 2)[-1]
                elif rendered.startswith("summon "):
                    parts = rendered.split(" ", 3)
                    if len(parts) > 3 and parts[3].startswith("{"):
                        payload = parts[3]
                elif " data merge entity " in rendered:
                    marker = " data merge entity "
                    rest = rendered.split(marker, 1)[1]
                    idx = rest.find(" {")
                    if idx >= 0:
                        payload = rest[idx + 1 :]
                elif " set value {" in rendered:
                    payload = rendered[rendered.index(" set value {") + 11 :]
                elif "dialog show" in rendered and "{" in rendered:
                    payload = rendered[rendered.index("{") :]
                if payload and payload.startswith("{"):
                    for err in check_snbt(payload):
                        problems.append(f"{label}:{name}:{lineno}: SNBT {err}")
                if len(line) > 30000:
                    problems.append(f"{label}:{name}:{lineno}: line too long ({len(line)})")

        for dialog in dialogs:
            path = dialog_dir / (dialog + ".json")
            data = json.loads(path.read_text(encoding="utf-8"))
            dtype = data.get("type")
            if "title" not in data or "external_title" not in data:
                problems.append(f"{label}: dialog {dialog}: missing title/external_title")
            if dtype == "minecraft:multi_action":
                if not isinstance(data.get("actions"), list):
                    problems.append(f"{label}: dialog {dialog}: actions missing")
                if not isinstance(data.get("inputs", []), list):
                    problems.append(f"{label}: dialog {dialog}: inputs invalid")
                for act in data.get("actions", []):
                    if "label" not in act or "action" not in act:
                        problems.append(f"{label}: dialog {dialog}: action missing label/action")
                    atype = act.get("action", {}).get("type")
                    if atype not in ("minecraft:run_command", "minecraft:show_dialog", "minecraft:dynamic/run_command"):
                        problems.append(f"{label}: dialog {dialog}: odd action type {atype}")
            if dtype == "minecraft:confirmation":
                if "yes" not in data or "no" not in data:
                    problems.append(f"{label}: dialog {dialog}: confirmation missing yes/no")
            text = path.read_text(encoding="utf-8")
            for ref in TAG_JSON_RE.findall(text):
                if ref.startswith("gti:") and ref.split(":", 1)[1] not in dialogs:
                    problems.append(f"{label}: dialog {dialog} references missing {ref}")

        # tag references
        answers = json.loads((version_dir / "data/gti/tags/item/answers.json").read_text())
        tags = {"gti:answers"} | {
            f"gti:equivalent/g{i}"
            for i in range(len(list((version_dir / "data/gti/tags/item/equivalent").glob("*.json"))))
        }
        for path in funcs.values():
            for ref in re.findall(r"#(gti:[a-z0-9_./]+)", path.read_text(encoding="utf-8")):
                if ref not in tags:
                    problems.append(f"{label}: missing item tag {ref}")

        print(f"{label}: {len(funcs)} functions, {len(dialogs)} dialogs, {len(answers['values'])} answers")

    if problems:
        print("\nPROBLEMS:")
        for p in problems[:120]:
            print(" -", p)
        print(f"\n{len(problems)} problem(s)")
        return 1
    print("\nAll static checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
