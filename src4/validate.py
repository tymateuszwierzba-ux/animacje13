"""Static checks for the generated 4.0 packs (no game required)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

BUILD = Path(__file__).resolve().parent.parent / "build4"

FUNC_RE = re.compile(r"\bfunction\s+(gti:[a-z0-9_./]+)")
DIALOG_RE = re.compile(r"\bdialog\s+(?:show\s+@\S+\s+)?(gti:[a-z0-9_./]+)")
TAG_RE = re.compile(r"#(gti:[a-z0-9_./]+)")
MACRO_RE = re.compile(r"\$\(([a-zA-Z0-9_]+)\)")
SCORE_KEYWORDS = {"if", "unless", "run", "as", "at", "in", "on", "positioned", "rotated",
                  "facing", "align", "anchored", "store", "summon"}
SCORE_OPS = {"<", "<=", "=", ">", ">=", "matches"}


def strip_strings(line: str) -> str:
    return re.sub(r'"(?:[^"\\]|\\.)*"', '""', line)


def balance(line: str) -> bool:
    depth_b = depth_c = 0
    in_str = False
    escape = False
    for ch in line:
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "[":
            depth_b += 1
        elif ch == "]":
            depth_b -= 1
        elif ch == "{":
            depth_c += 1
        elif ch == "}":
            depth_c -= 1
        if depth_b < 0 or depth_c < 0:
            return False
    return depth_b == 0 and depth_c == 0 and not in_str


def check_scores(line: str) -> list[str]:
    errors: list[str] = []
    text = strip_strings(line)
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
    for match in re.finditer(r"scores=\{([^}]*)\}", text):
        body = match.group(1)
        for pair in filter(None, body.split(",")):
            if "=" not in pair:
                errors.append(f"selector score without '=': {pair}")
    return errors


def main() -> int:
    problems: list[str] = []
    for version_dir in sorted(BUILD.iterdir()):
        if not version_dir.is_dir():
            continue
        label = version_dir.name
        func_dir = version_dir / "data/gti/function"
        dialog_dir = version_dir / "data/gti/dialog"
        funcs = {p.relative_to(func_dir).with_suffix("").as_posix(): p
                 for p in func_dir.rglob("*.mcfunction")}
        dialogs = {p.relative_to(dialog_dir).with_suffix("").as_posix()
                   for p in dialog_dir.rglob("*.json")}

        for path in version_dir.rglob("*.json"):
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                problems.append(f"{label}: invalid JSON {path.relative_to(version_dir)}: {exc}")

        for name, path in funcs.items():
            for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                if not line.strip():
                    continue
                if not balance(line):
                    problems.append(f"{label}:{name}:{lineno}: unbalanced brackets")
                    continue
                for err in check_scores(line):
                    problems.append(f"{label}:{name}:{lineno}: {err}")
                macros = MACRO_RE.findall(line)
                if line.startswith("$"):
                    if not macros:
                        problems.append(f"{label}:{name}:{lineno}: macro marker without macros")
                    rendered = MACRO_RE.sub("0", line[1:])
                else:
                    if macros:
                        problems.append(f"{label}:{name}:{lineno}: macro outside a macro line")
                    rendered = line
                scan = strip_strings(rendered)
                if rendered.startswith(("tellraw ", "title ")):
                    scan = ""
                for target in FUNC_RE.findall(scan):
                    if target.split(":", 1)[1] not in funcs:
                        problems.append(f"{label}:{name}:{lineno}: missing function {target}")
                for target in DIALOG_RE.findall(scan):
                    if target.split(":", 1)[1] not in dialogs:
                        problems.append(f"{label}:{name}:{lineno}: missing dialog {target}")
                if len(line) > 30000:
                    problems.append(f"{label}:{name}:{lineno}: line too long ({len(line)})")

        for name in dialogs:
            data = json.loads((dialog_dir / (name + ".json")).read_text(encoding="utf-8"))
            if "title" not in data or "external_title" not in data:
                problems.append(f"{label}: dialog {name}: missing title/external_title")
            dtype = data.get("type")
            if dtype == "minecraft:multi_action":
                if not isinstance(data.get("actions"), list):
                    problems.append(f"{label}: dialog {name}: actions missing")
                for act in data.get("actions", []):
                    if "label" not in act or "action" not in act:
                        problems.append(f"{label}: dialog {name}: malformed action")
                    atype = act.get("action", {}).get("type")
                    if atype not in ("minecraft:run_command", "minecraft:show_dialog",
                                     "minecraft:dynamic/run_command"):
                        problems.append(f"{label}: dialog {name}: odd action {atype}")
            if dtype == "minecraft:confirmation" and ("yes" not in data or "no" not in data):
                problems.append(f"{label}: dialog {name}: confirmation missing yes/no")
            text = (dialog_dir / (name + ".json")).read_text(encoding="utf-8")
            for ref in re.findall(r'"dialog"\s*:\s*"(gti:[a-z0-9_./]+)"', text):
                if ref.split(":", 1)[1] not in dialogs:
                    problems.append(f"{label}: dialog {name}: missing dialog {ref}")

        answers = json.loads((version_dir / "data/gti/tags/item/answers.json").read_text())
        tags = {"gti:answers"} | {
            f"gti:equivalent/g{i}"
            for i in range(len(list((version_dir / "data/gti/tags/item/equivalent").glob("*.json"))))
        }
        for path in funcs.values():
            for ref in TAG_RE.findall(path.read_text(encoding="utf-8")):
                if ref not in tags:
                    problems.append(f"{label}: missing item tag {ref}")

        print(f"{label}: {len(funcs)} functions, {len(dialogs)} dialogs, "
              f"{len(answers['values'])} answers")

    if problems:
        print("\nPROBLEMS:")
        for problem in problems[:120]:
            print(" -", problem)
        print(f"\n{len(problems)} problem(s)")
        return 1
    print("\nAll static checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
