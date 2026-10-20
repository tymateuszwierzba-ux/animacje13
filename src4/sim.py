"""Tiny Minecraft command interpreter used to smoke-test the generated pack.

Supports the subset the datapack relies on: scoreboards, execute chains,
data storage, tags, entity summons/selection, function calls with macros.
Not a full implementation - enough to catch logic bugs headlessly.
"""

from __future__ import annotations

import json
import random
import re
from pathlib import Path

SELECTOR_RE = re.compile(r"@([aerspn])(\[[^\]]*\])?")
SUMMON_RE = re.compile(r"^summon (\S+) (~[^ ]* ~[^ ]* ~[^ ]*)(?: (.*))?$")


def parse_nbt(text: str):
    """Parse the SNBT subset used by summon commands into python objects."""
    pos = 0

    def ws():
        nonlocal pos
        while pos < len(text) and text[pos] in " \t\n":
            pos += 1

    def value():
        nonlocal pos
        ws()
        if pos >= len(text):
            raise ValueError("eof")
        ch = text[pos]
        if ch == "{":
            pos += 1
            out = {}
            ws()
            if text[pos] == "}":
                pos += 1
                return out
            while True:
                ws()
                key = string_or_bare()
                ws()
                assert text[pos] == ":", f"expected : at {pos}: {text[pos-20:pos+20]}"
                pos += 1
                out[key] = value()
                ws()
                if text[pos] == ",":
                    pos += 1
                    continue
                assert text[pos] == "}", f"expected }} at {pos}"
                pos += 1
                return out
        if ch == "[":
            pos += 1
            out = []
            ws()
            if text[pos] == "]":
                pos += 1
                return out
            while True:
                out.append(value())
                ws()
                if text[pos] == ",":
                    pos += 1
                    continue
                assert text[pos] == "]"
                pos += 1
                return out
        if ch == '"':
            return string_or_bare()
        m = re.match(r"[-+]?[0-9.]+[bslfd]?", text[pos:])
        if m:
            raw = m.group(0)
            pos += len(raw)
            suffix = raw[-1] if raw[-1] in "bslfd" else ""
            body = raw[:-1] if suffix else raw
            if suffix == "b":
                return body not in ("0", "false")
            if "." in body or suffix in ("f", "d"):
                return float(body)
            return int(body)
        word = string_or_bare()
        if word == "true":
            return True
        if word == "false":
            return False
        return word

    def string_or_bare():
        nonlocal pos
        if text[pos] == '"':
            pos += 1
            out = []
            while text[pos] != '"':
                if text[pos] == "\\":
                    pos += 1
                out.append(text[pos])
                pos += 1
            pos += 1
            return "".join(out)
        start = pos
        while pos < len(text) and text[pos] not in "{}[],:\"":
            pos += 1
        return text[start:pos].strip()

    result = value()
    return result


class Entity:
    def __init__(self, etype: str, pos, nbt: dict):
        self.type = etype
        self.pos = list(pos)
        self.tags = set(nbt.get("Tags", []))
        self.nbt = nbt
        self.scores: dict[str, int] = {}
        self.alive = True

    def __repr__(self):
        return f"<{self.type} {sorted(self.tags)}>"


class Sim:
    def __init__(self, root: Path, seed: int = 1):
        self.root = root
        self.funcs = {
            p.relative_to(root / "data/gti/function").with_suffix("").as_posix(): p
            for p in (root / "data/gti/function").rglob("*.mcfunction")
        }
        self.scores: dict[tuple[str, str], int] = {}
        self.objectives: dict[str, str] = {}
        self.storage: dict[str, dict] = {}
        self.entities: list[Entity] = []
        self.players: list[Entity] = []
        self.rng = random.Random(seed)
        self.pos = [0.5, 64.0, 0.5]
        self.dim = "minecraft:overworld"
        self.sender = "@s"
        self.ctx = None
        self.log: list[str] = []
        self.macros: dict[str, str] = {}
        self.returned = None
        self.depth = 0
        self.unsupported = []
        self.stack = []

    # ---------------------------------------------------------------- helpers
    def player(self, name: str = "Steve") -> Entity:
        for p in self.players:
            if p.nbt.get("Name") == name:
                return p
        p = Entity("player", self.pos, {"Name": name})
        self.players.append(p)
        return p

    def score(self, holder: str, obj: str) -> int:
        for p in self.players:
            if p.nbt.get("Name") == holder:
                return p.scores.get(obj, 0)
        return self.scores.get((holder, obj), 0)

    def set(self, holder: str, obj: str, value: int) -> None:
        if obj not in self.objectives:
            raise RuntimeError(f"unknown objective {obj}")
        for p in self.players:
            if p.nbt.get("Name") == holder:
                p.scores[obj] = int(value)
                return
        self.scores[(holder, obj)] = int(value)

    def run_file(self, name: str, macro: dict | None = None) -> None:
        if name not in self.funcs:
            raise RuntimeError(f"missing function {name}")
        self.depth += 1
        self.stack.append(name)
        if self.depth > 60:
            raise RuntimeError("call depth exceeded")
        saved = self.macros
        self.macros = macro or {}
        try:
            for raw in self.funcs[name].read_text().splitlines():
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if line.startswith("$"):
                    line = re.sub(
                        r"\$\(([a-zA-Z0-9_]+)\)",
                        lambda m: str(self.macros.get(m.group(1), ""))
                        if not isinstance(self.macros.get(m.group(1)), list) else "",
                        line[1:],
                    )
                    if not line:
                        continue
                self.run(line)
                if self.returned is not None:
                    value = self.returned
                    self.returned = None
                    self.depth -= 1
                    self.macros = saved
                    # propagate to caller of `return run`
                    raise FunctionReturn(value)
        finally:
            self.macros = saved
            self.depth -= 1
            self.stack.pop()

    def call(self, name: str, macro: dict | None = None):
        try:
            self.run_file(name, macro)
        except FunctionReturn as done:
            return done.value
        return None

    # ---------------------------------------------------------------- selectors
    def select(self, token: str) -> list:
        match = SELECTOR_RE.match(token)
        if not match:
            raise RuntimeError(f"bad selector {token}")
        kind, argtext = match.group(1), match.group(2) or ""
        args = {}
        if argtext:
            for part in re.findall(r'([a-z_]+)=(\{[^}]*\}|"[^"]*"|[^,\]]+)', argtext):
                args[part[0]] = part[1]
        if kind == "s":
            if self.ctx is not None:
                pool = [self.ctx]
            elif self.sender in ("Steve", "@s"):
                pool = [self.player("Steve")]
            else:
                pool = [p for p in self.players if p.nbt.get("Name") == self.sender]
        elif kind == "a":
            pool = list(self.players)
        elif kind == "e":
            pool = list(self.players) + [e for e in self.entities if e.alive]
        elif kind == "p":
            pool = list(self.players)
        else:
            pool = list(self.players)

        tag_required = [v for k, v in args.items() if k == "tag" and not v.startswith("!")]
        tags = re.findall(r'tag=([!\w.]+)', argtext)
        for tag in tags:
            if tag.startswith("!"):
                pool = [e for e in pool if tag[1:] not in e.tags]
            else:
                pool = [e for e in pool if tag in e.tags]
        if "scores" in argtext:
            for obj, spec in re.findall(r"([\w.]+)=([-0-9.]+)", argtext.split("scores={")[1].split("}")[0]):
                def keep(e, obj=obj, spec=spec):
                    val = e.scores.get(obj, self.scores.get((e.nbt.get("Name", ""), obj), 0))
                    if ".." in spec:
                        lo, hi = spec.split("..")
                        lo = int(lo) if lo else None
                        hi = int(hi) if hi else None
                        return (lo is None or val >= lo) and (hi is None or val <= hi)
                    return val == int(float(spec))
                pool = [e for e in pool if keep(e)]
        if "type=" in argtext:
            wanted = args.get("type")
            if wanted == "player":
                pool = [e for e in pool if e.type == "player"]
        sort = args.get("sort")
        limit = args.get("limit")
        if sort == "nearest":
            pool.sort(key=lambda e: sum((a - b) ** 2 for a, b in zip(e.pos, self.pos)))
        elif sort == "random":
            self.rng.shuffle(pool)
        if limit:
            pool = pool[: int(limit)]
        return pool

    # ---------------------------------------------------------------- commands
    def run(self, line: str) -> None:
        if line.startswith("execute "):
            return self.run_execute(line[len("execute "):])
        if line.startswith("scoreboard "):
            return self.cmd_scoreboard(line[len("scoreboard "):])
        if line.startswith("function "):
            parts = line.split()
            name = parts[1].split(":", 1)[1]
            macro = None
            if len(parts) >= 5 and parts[2] == "with":
                macro = self.resolve_storage(" ".join(parts[3:]))
            return self.call(name, macro)
        if line.startswith("data "):
            return self.cmd_data(line[len("data "):])
        if line.startswith("tag "):
            parts = line.split()
            targets = self.select(parts[1])
            for target in targets:
                if parts[2] == "add":
                    target.tags.add(parts[3])
                elif parts[2] == "remove":
                    target.tags.discard(parts[3])
            return
        if line.startswith("summon "):
            return self.cmd_summon(line)
        if line.startswith("kill "):
            for target in self.select(line.split()[1]):
                target.alive = False
                if target in self.entities:
                    self.entities.remove(target)
            return
        if line.startswith("return "):
            rest = line[len("return "):]
            if rest.startswith("run "):
                inner = rest[4:]
                # only scoreboard get is used with `return run`
                if inner.startswith("scoreboard players get "):
                    parts = inner.split()
                    value = self.score(parts[3], parts[4])
                    raise FunctionReturn(value)
                self.run(inner)
                raise FunctionReturn(1)
            raise FunctionReturn(int(rest))
        if line.startswith("bossbar ") or line.startswith("dialog ") or line.startswith("title "):
            return
        if line.startswith(("tellraw ", "particle ", "playsound ", "random ", "tp ", "setblock ",
                            "fill ", "scoreboard ", "advancement ", "gamerule ")):
            if line.startswith("tp "):
                parts = line.split()
                if len(parts) > 3 and parts[2].startswith("~"):
                    self.pos = [self.pos[0], self.pos[1], self.pos[2]]
            return
        self.unsupported.append(line.split()[0] if line.split() else '?')
        return

    def resolve_storage(self, spec: str):
        if spec.startswith("entity "):
            rest = spec[len("entity "):].split(None, 1)
            targets = self.select(rest[0])
            if not targets:
                raise RuntimeError("no entity")
            data = targets[0].nbt
            path = rest[1] if len(rest) > 1 else ""
            return self.get_path(data, path) if path else data
        if not spec.startswith("storage "):
            raise RuntimeError(f"unsupported nbt source {spec}")
        rest = spec[len("storage "):].split(None, 1)
        namespace = rest[0]
        path = rest[1] if len(rest) > 1 else ""
        if "." in namespace.split(":")[1] and namespace.count(".") >= 1:
            head, _, tail = namespace.partition(".")
            if head in self.storage:
                namespace = head
                path = (tail + ("." + path if path else ""))
        data = self.storage.get(namespace, {})
        if not path:
            return data
        return self.get_path(data, path)

    def get_path(self, data, path: str):
        tokens = re.findall(r'"[^"]*"|[^.\[\]]+|\[[0-9]+\]', path)
        node = data
        for token in tokens:
            if token.startswith("["):
                node = node[int(token[1:-1])]
            elif token.startswith('"'):
                node = node[token[1:-1]]
            else:
                node = node[token]
        return node

    def set_path(self, data, path: str, value) -> None:
        tokens = re.findall(r'"[^"]*"|[^.\[\]]+|\[[0-9]+\]', path)
        node = data
        for token in tokens[:-1]:
            if token.startswith("["):
                node = node[int(token[1:-1])]
            elif token.startswith('"'):
                node = node[token[1:-1]]
            else:
                node = node[token]
        last = tokens[-1]
        if last.startswith("["):
            node[int(last[1:-1])] = value
        elif last.startswith('"'):
            node[last[1:-1]] = value
        else:
            node[last] = value

    # ---------------------------------------------------------------- parts
    def cmd_scoreboard(self, text: str) -> None:
        parts = text.split()
        if parts[0] == "objectives":
            if parts[1] == "add":
                self.objectives[parts[2]] = parts[3]
            return
        if parts[0] != "players":
            return
        action = parts[1]
        if action == "enable":
            return
        if action == "get":
            holder, obj = parts[2], parts[3]
            if holder.startswith("@"):
                targets = self.select(holder)
                if not targets:
                    raise FunctionReturn(0)
                holder = targets[0].nbt.get("Name", "")
            raise FunctionReturn(self.score(holder, obj))
        targets = self.select(parts[2]) if parts[2].startswith("@") else [parts[2]]
        obj = parts[3]
        if action == "set":
            value = int(float(parts[4]))
            for target in targets:
                _, _, val = self.apply_holder(target, obj, value)
                self.set_holder(target, obj, val)
        elif action in ("add", "remove"):
            amount = int(float(parts[4]))
            if action == "remove":
                amount = -amount
            for target in targets:
                base = self.get_holder(target, obj)
                self.set_holder(target, obj, base + amount)
        elif action == "operation":
            op = parts[4]
            source = parts[5]
            sobj = parts[6]
            if source.startswith("@"):
                sel = self.select(source)
                if not sel:
                    return
                sval = self.get_holder(sel[0], sobj)
            else:
                sval = self.score(source, sobj)
            for target in targets:
                base = self.get_holder(target, obj)
                if op == "=":
                    result = sval
                elif op == "+=":
                    result = base + sval
                elif op == "-=":
                    result = base - sval
                elif op == "*=":
                    result = base * sval
                elif op == "/=":
                    if sval == 0:
                        return
                    result = int(base / sval)
                elif op == "%=":
                    if sval == 0:
                        return
                    result = int(base % sval)
                elif op in ("<", ">"):
                    result = min(base, sval) if op == "<" else max(base, sval)
                elif op == "><":
                    result = sval
                else:
                    raise RuntimeError(f"bad operation {op}")
                self.set_holder(target, obj, result)

    def apply_holder(self, target, obj, value):
        return target, obj, value

    def get_holder(self, target, obj) -> int:
        if isinstance(target, str):
            return self.score(target, obj)
        return target.scores.get(obj, 0)

    def set_holder(self, target, obj, value: int) -> None:
        if isinstance(target, str):
            self.set(target, obj, value)
        else:
            target.scores[obj] = int(value)

    def cmd_data(self, text: str) -> None:
        words = text.split()
        action = words[0]
        if words[1] == "entity":
            return self.cmd_data_entity(action, text)
        if words[1] != "storage":
            return
        namespace = words[2]
        root = self.storage.setdefault(namespace, {})
        rest = text[len(" ".join(words[:3])):].strip()

        if action in ("remove", "get"):
            path = rest
            if action == "get":
                value = self.get_path(root, path)
                raise FunctionReturn(value if isinstance(value, int) else 1)
            tokens = re.findall(r'"[^"]*"|[^.\[\]]+', path)
            node = root
            for token in tokens[:-1]:
                node = node[token[1:-1] if token.startswith('"') else token]
            last = tokens[-1]
            node.pop(last[1:-1] if last.startswith('"') else last, None)
            return

        # action == modify
        if " set value " in rest:
            path, payload = rest.split(" set value ", 1)
            self.store(path, parse_nbt(payload), root)
        elif " set from " in rest:
            path, source = rest.split(" set from ", 1)
            self.store(path, self.resolve_storage(source), root)
        elif " append value " in rest:
            path, payload = rest.split(" append value ", 1)
            node = self.get_path(root, path) if path else root
            if not isinstance(node, list):
                raise RuntimeError(f"append to non-list {path}")
            node.append(parse_nbt(payload))
        elif " merge value " in rest:
            path, payload = rest.split(" merge value ", 1)
            node = self.get_path(root, path) if path else root
            node.update(parse_nbt(payload))
        elif " prepend value " in rest:
            path, payload = rest.split(" prepend value ", 1)
            node = self.get_path(root, path) if path else root
            node.insert(0, parse_nbt(payload))
        else:
            raise RuntimeError(f"unsupported data modify: {text}")

    def cmd_data_entity(self, action: str, text: str) -> None:
        if action == "merge":
            target, payload = text[len("merge entity "):].split(" ", 1)
            data = parse_nbt(payload)
            for entity in self.select(target):
                entity.nbt.update(data)
                if "Tags" in data:
                    entity.tags = set(data["Tags"])
            return
        if action == "remove":
            target, path = text[len("remove entity "):].split(" ", 1)
            for entity in self.select(target):
                tokens = re.findall(r'"[^"]*"|[^.\[\]]+', path)
                node = entity.nbt
                for token in tokens[:-1]:
                    node = node[token[1:-1] if token.startswith('"') else token]
                last = tokens[-1]
                node.pop(last[1:-1] if last.startswith('"') else last, None)
            return
        if action == "modify":
            target, rest = text[len("modify entity "):].split(" ", 1)
            targets = self.select(target)
            if not targets:
                return
            entity = targets[0]
            if " set value " in rest:
                path, payload = rest.split(" set value ", 1)
                self.store(path, parse_nbt(payload), entity.nbt)
            return

    def store(self, path: str, value, root) -> None:
        if not path:
            root.update(value)
            return
        try:
            self.set_path(root, path, value)
        except (KeyError, TypeError, IndexError):
            self.create_path(root, path, value)

    def create_path(self, root, path: str, value) -> None:
        tokens = re.findall(r'"[^"]*"|[^.\[\]]+|\[[0-9]+\]', path)
        node = root
        for index, token in enumerate(tokens):
            key = token[1:-1] if token.startswith('"') else token
            last = index == len(tokens) - 1
            if last:
                node[key] = value
                break
            nxt = tokens[index + 1]
            if key not in node or not isinstance(node[key], (dict, list)):
                node[key] = [] if nxt.startswith("[") else {}
            node = node[key]

    def cmd_summon(self, line: str) -> None:
        match = SUMMON_RE.match(line)
        if not match:
            return
        etype, pos_text, rest = match.groups()
        nbt = parse_nbt(rest) if rest and rest.strip().startswith("{") else {}
        coords = []
        for token, base in zip(pos_text.split(), self.pos):
            if token.startswith("~"):
                coords.append(base + (float(token[1:]) if len(token) > 1 else 0.0))
            else:
                coords.append(float(token))
        entity = Entity(etype, coords, nbt)
        if etype == "player":
            self.players.append(entity)
        else:
            self.entities.append(entity)

    def run_execute(self, text: str) -> None:
        # tokenise respecting braces/brackets/quotes
        tokens = []
        depth = 0
        current = []
        in_str = False
        for ch in text:
            if in_str:
                current.append(ch)
                if ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
                current.append(ch)
                continue
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
            if ch == " " and depth == 0:
                tokens.append("".join(current))
                current = []
            else:
                current.append(ch)
        if current:
            tokens.append("".join(current))

        index = 0
        store = None

        def take():
            nonlocal index
            value = tokens[index]
            index += 1
            return value

        def toggle_ok(condition: bool) -> bool:
            return condition

        while index < len(tokens):
            word = tokens[index]
            if word == "run":
                index += 1
                rest = " ".join(tokens[index:])
                try:
                    value = self.run(rest)
                    success = True
                except FunctionReturn as raised:
                    value = raised.value
                    success = True
                except RuntimeError:
                    value, success = 0, False
                if store is not None:
                    target = store["target"]
                    payload = int(value or 0) * store.get("scale", 1) if store["kind"] == "result" else int(success)
                    if target == "score":
                        self.set_holder(store["holder"], store["objective"], payload)
                    elif target == "storage":
                        root = self.storage.setdefault(store["namespace"], {})
                        self.store(store["path"], payload, root)
                return
            index += 1
            if word == "as":
                targets = self.select(tokens[index])
                index += 1
                if not targets:
                    return
                rest = " ".join(tokens[index:])
                for target in list(targets):
                    saved_sender, saved_ctx = self.sender, self.ctx
                    self.sender = target.nbt.get("Name", "@s") if target.type == "player" else "@s"
                    self.ctx = target
                    try:
                        self.run_execute(rest)
                    finally:
                        self.sender, self.ctx = saved_sender, saved_ctx
                return
            if word == "at":
                targets = self.select(tokens[index])
                index += 1
                if not targets:
                    return
                rest = " ".join(tokens[index:])
                for target in list(targets):
                    saved = list(self.pos)
                    self.pos = list(target.pos)
                    try:
                        self.run_execute(rest)
                    finally:
                        self.pos = saved
                return
            if word in ("positioned",):
                coord_text = " ".join(tokens[index:index + 3])
                index += 3
                newpos = []
                for token, base in zip(coord_text.split(), self.pos):
                    if token.startswith("~"):
                        newpos.append(base + (float(token[1:]) if len(token) > 1 else 0.0))
                    elif token.startswith("^"):
                        newpos.append(base)
                    else:
                        newpos.append(float(token))
                saved = list(self.pos)
                self.pos = newpos
                self.run_execute(" ".join(tokens[index:]))
                self.pos = saved
                return
            if word in ("align", "anchored", "rotated", "facing", "in", "on"):
                # skip the argument (facing takes two, positioned-style handled above)
                if word in ("facing", "rotated"):
                    index += 1 if tokens[index] not in ("entity",) else 2
                elif word == "in":
                    self.dim = tokens[index]
                    index += 1
                elif word == "on":
                    index += 1
                else:
                    index += 1
                continue
            if word == "if" or word == "unless":
                want = word == "if"
                sub = tokens[index]
                index += 1
                if sub == "score":
                    holder = tokens[index]; index += 1
                    obj = tokens[index]; index += 1
                    op = tokens[index]; index += 1
                    if op == "matches":
                        spec = tokens[index]; index += 1
                        value = self.get_holder(self.resolve_holder(holder), obj)
                        if ".." in spec:
                            lo, _, hi = spec.partition("..")
                            lo_v = int(lo) if lo else None
                            hi_v = int(hi) if hi else None
                            ok = (lo_v is None or value >= lo_v) and (hi_v is None or value <= hi_v)
                        else:
                            ok = value == int(spec)
                    else:
                        other = tokens[index]; index += 1
                        sobj = tokens[index]; index += 1
                        left = self.get_holder(self.resolve_holder(holder), obj)
                        right = self.get_holder(self.resolve_holder(other), sobj)
                        ok = {"<": left < right, "<=": left <= right, "=": left == right,
                              ">": left > right, ">=": left >= right}[op]
                elif sub == "data":
                    kind = tokens[index]; index += 1
                    spec = tokens[index]; index += 1
                    path = ""
                    if index < len(tokens) and not tokens[index].startswith(("{", "run")):
                        path = tokens[index]; index += 1
                    matcher = None
                    if index < len(tokens) and tokens[index].startswith("{"):
                        matcher = parse_nbt(tokens[index]); index += 1
                    try:
                        if kind == "storage":
                            value = self.resolve_storage(f"storage {spec} {path}".strip())
                        elif kind == "entity":
                            targets = self.select(spec)
                            value = self.get_path(targets[0].nbt, path) if targets and path else {}
                        else:
                            value = {}
                        ok = True
                    except Exception:
                        value, ok = None, False
                    if ok and matcher is not None:
                        ok = isinstance(value, dict) and all(
                            value.get(k) == v for k, v in matcher.items()
                        )
                elif sub == "entity":
                    sel = tokens[index]; index += 1
                    ok = bool(self.select(sel))
                elif sub == "items":
                    # execute if items entity <target> <slot> <predicate>
                    kind = tokens[index]; index += 1
                    if kind == "entity":
                        target = tokens[index]; index += 1
                        slot = tokens[index]; index += 1
                        predicate = tokens[index]; index += 1
                        held = None
                        for sel in self.select(target):
                            if sel.type == "player":
                                held = sel.nbt.get("SelectedItem", {}).get("id")
                        ok = bool(held) and predicate.startswith("#")
                    else:
                        index += 3
                        ok = True
                elif sub == "dimension":
                    wanted = tokens[index]; index += 1
                    ok = wanted == self.dim
                elif sub == "loaded":
                    index += 1
                    ok = True
                elif sub == "function":
                    name = tokens[index].split(":")[-1]; index += 1
                    ok = bool(self.call(name))
                else:
                    ok = True
                if ok != want:
                    return
                continue
            if word == "store":
                kind = tokens[index]; index += 1
                target = tokens[index]; index += 1
                scale = 1
                if target == "score":
                    holder = tokens[index]; index += 1
                    objective = tokens[index]; index += 1
                    if kind == "result" and re.fullmatch(r"-?\d+", tokens[index] or ""):
                        scale = int(tokens[index]); index += 1
                    store = {"kind": kind, "target": "score", "holder": self.resolve_holder(holder),
                             "objective": objective, "scale": scale}
                elif target == "storage":
                    namespace = tokens[index]; index += 1
                    path_parts = []
                    while tokens[index] not in ("int", "float", "double", "long", "byte", "short", "bool"):
                        path_parts.append(tokens[index]); index += 1
                    index += 1  # value type
                    if re.fullmatch(r"-?\d+", tokens[index] or ""):
                        scale = int(tokens[index]); index += 1
                    store = {"kind": kind, "target": "storage", "namespace": namespace,
                             "path": " ".join(path_parts).replace(" ", ""), "scale": scale}
                else:
                    store = None
                continue
            # unknown subcommand: abort
            return

    def resolve_holder(self, token: str):
        if token.startswith("@"):
            sel = self.select(token)
            if not sel:
                return "__none__"
            return sel[0] if sel[0].type != "player" else sel[0].nbt.get("Name", "")
        return token


class FunctionReturn(Exception):
    def __init__(self, value):
        self.value = value
