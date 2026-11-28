#!/usr/bin/env python3
"""Mechanical checks for development format 4 and general context format 5.

Usage: ssot-check.py [SSOT_DIR|FORMAT5_ENTRY] [--since COMMIT] (default: ./SSOT)
       ssot-check.py ENTRY_FILE [--space-root DIR] --owners [FILE ...]

Directories select README.md. For a named entry pass its file. --owners checks
only that entry and selected reachable Markdown files, excluding Git history.
Include intervening indexes. Paths are entry-relative. --space-root sets the
agreed containing directory for sibling owners in format 5.

--since COMMIT lists only mentions of files removed after COMMIT or in
uncommitted changes, and counts the older ones in one line; it also compares
confirmed invariants with COMMIT instead of HEAD. Closeout uses it to see what
its own batch changed.

Checks the entry and format, local links and anchors, register shape, unexplained
changes to confirmed rules, reviewed_through, document sizes and mentions of
removed paths outside decisions/ and research/. Doctor reviews truth, coverage
and readability.

Supported Markdown: ATX and Setext headings, fenced code blocks (``` and ~~~,
any length), HTML comments (also across lines), inline links and images with
optional titles, reference definitions, and pipe tables. Raw HTML other than
comments and <a name/id> anchors is not interpreted.

Read-only: this script never writes to the repository.

Output (stable, safe to parse): one finding per line, starting with ERROR,
WARN, INFO, or UNCHECKED; then one summary line that always starts with
"ssot-check: " followed by the verdict PASS, FAIL, or INCOMPLETE.

Exit codes: 0 = PASS (no errors; warnings allowed), 1 = FAIL (errors found),
2 = usage error (bad arguments or no SSOT directory), 3 = INCOMPLETE (the
checker crashed or could not examine part of the tree, such as an unreadable
directory or a failing git), which is never a pass.
"""

import argparse
import os
import re
import subprocess
import sys
import traceback
from urllib.parse import unquote

FORMAT = "4"
# Reading budgets count characters so short CJK docs are not over-penalised;
# higher UTF-8 byte thresholds (INFO) catch CJK token bloat and tool truncation.
README_WARN_CHARS = 8000
DOC_WARN_CHARS = 16000
DOC_INFO_BYTES = 24000
INLINE_SHARD_INFO_ROWS = 50
TOTAL_ENTRY_INFO_CHARS = 16000
TOTAL_ENTRY_INFO_BYTES = 24000
SHARD_INFO_CHARS = 16000
SHARD_INFO_BYTES = 24000
SHARD_INFO_ROWS = 50
COLD_SHARD_TRUNC_CHARS = 64000
COLD_SHARD_TRUNC_BYTES = 64000
ROW_INFO_CHARS = 500
ROW_INFO_BYTES = 900
REVIEWED_LAG_INFO_COMMITS = 100
DATED_HISTORY_INFO_HEADINGS = 5
DATED_EARLY_INFO_CHARS = 8000
ENTRY_SECTION_INFO_CHARS = 4000
COLD_TAIL_TRUNC_CHARS = 32000
COLD_TAIL_TRUNC_BYTES = 32000
COLD_TAIL_INVERTED_CHARS = 1000
COLD_INDEX_INFO_CHARS = 8000
COLD_INDEX_INFO_BYTES = 16000
COLD_INDEX_ROW_SOFT_CHARS = 250
COLD_INDEX_ROW_SOFT_BYTES = 500
COLD_INDEX_ROW_SOFT_COUNT = 3
COLD_INDEX_ROW_HARD_CHARS = 350
COLD_INDEX_ROW_HARD_BYTES = 700
MEGA_DOC_H2_SECTIONS = 6
CHECKBOX_TASK_INFO_COUNT = 5
CHECKBOX_WARM_INFO_COUNT = 8
RETIRED_INLINE_INFO_ROWS = 3
COMPACTION_ROLLUP_LIMIT = 5
COLD_SHARD_NAMES = ("retired", "archive", "history")
WARM_TIERS = {"warm", "hot", "active"}
COLD_DIRS = {"decisions", "research", "archive", "archives", "history"}
COLD_ZH_DIR_TOKENS = ("决策历史", "历史记录", "历史归档")
COLD_ZH_EXACT_DIRS = {"历史", "归档"}
COLD_INDEX_NAMES = {"readme", "index"}
COLD_INDEX_SUFFIXES = ("-index", "_index", "索引")
COLD_INDEX_STEMS = {"decisions-index", "history-index"}
COLD_STEM_SUFFIXES = ("-history", "_history", "-archive", "_archive", "-历史", "_历史", "-归档", "_归档")
COLD_EXACT_STEMS = {"history", "archive", "retired", "changelog"}
ENTRY_CORE_SECTIONS = (
    "map", "地图", "文档地图", "文件地图", "索引",
    "owners", "所有者", "权威文档",
    "task routes", "routes", "任务路由", "路由",
    "invariants", "不变量", "保护规则",
)
TASK_FILE_STEM_PREFIXES = ("tasks", "todo", "workarounds", "open-questions", "open_questions")
TASK_FILE_EXACT_STEMS = {"now", "task", "workaround"}
INSTRUCTION_FILES = (
    "AGENTS.md", "CLAUDE.md", "GEMINI.md",
    ".cursor/rules/ssot.mdc", ".cursorrules",
    ".windsurf/rules/ssot.md", ".windsurfrules",
    ".github/copilot-instructions.md",
)
INVARIANT_STATUSES = {"confirmed", "candidate", "retired"}
INVARIANT_HEADINGS = ("invariants", "不变量", "保护规则")
INVARIANT_COLUMNS = "ID | Kind | Rule | Explained in | Status | Source"
INVARIANT_HEADERS = (  # accepted header names per column, compared case-insensitively
    ("id",), ("kind", "类型"), ("rule", "规则"), ("explained in", "解释位置"),
    ("status", "状态"), ("source", "来源"),
)
V2_LEDGERS = ("STATUS.md", "HISTORY.md", ".bootstrap")

FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
ATX_RE = re.compile(r"^ {0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT_RE = re.compile(r"^ {0,3}(=+|-+)[ \t]*$")
INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
LABEL_RE = re.compile(r"!?\[(?:[^\[\]\\]|\\.|\[[^\]]*\])*\]\(")
REFDEF_RE = re.compile(r"^ {0,3}\[(?!\^)([^\]]+)\]:[ \t]*(<[^>]*>|\S+)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
ID_PAT = r"[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+"  # INV-01, CORE-RULE-2
INVARIANT_ID_RE = re.compile(f"^{ID_PAT}$")
SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
LINE_ANCHOR_RE = re.compile(r"^L(\d+)(?:-L?(\d+))?$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
COLD_HEADING_RE = re.compile(
    r"^(?:(?:history|archive)\s*[(（]\s*cold\s*[)）]|(?:历史记录|历史归档)\s*[(（]\s*冷读\s*[)）])(?:\s*[:：—-].*)?$",
    re.IGNORECASE,
)
ACTIVE_RESEARCH_RE = re.compile(
    r"^\s*(?:[-*+]\s*)?(?:\*\*)?(?:status|状态)(?:\*\*)?\s*[:：]\s*`?(?:active|进行中)\b",
    re.IGNORECASE,
)
CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+\[([ xX])\]\s")


class Report:
    def __init__(self, root, documents=None):
        self.root, self.documents = root, documents
        self.lines, self.compactions, self.unchecked = [], [], []
        self.errors = self.warnings = 0

    def add(self, level, path, line, message):
        where = (os.path.relpath(path, self.root) if path else ".") + (f":{line}" if line else "")
        self.lines.append(f"{level:<5} {where}  {message}")
        if level == "ERROR":
            self.errors += 1
        elif level == "WARN":
            self.warnings += 1

    def add_compaction(self, path, detail):
        self.compactions.append((os.path.relpath(path, self.root) if path else ".", detail))

    def finish(self, target):
        if self.compactions:
            grouped = {}
            for where, detail in self.compactions:
                items = grouped.setdefault(where, [])
                if detail not in items:
                    items.append(detail)
            entries = [f"{w} ({'; '.join(ds)})" for w, ds in grouped.items()]
            shown = ", ".join(entries[:COMPACTION_ROLLUP_LIMIT])
            if len(entries) > COMPACTION_ROLLUP_LIMIT:
                shown += f", and {len(entries) - COMPACTION_ROLLUP_LIMIT} more"
            self.add("INFO", None, None, f"compaction candidates ({len(entries)}): {shown}")
        for line in self.lines:
            print(line)
        for item in self.unchecked:
            print(f"UNCHECKED {item}")
        verdict = "INCOMPLETE" if self.unchecked else ("FAIL" if self.errors else "PASS")
        counts = f"{self.errors} error(s), {self.warnings} warning(s)" + (f", {len(self.unchecked)} part(s) not checked" if self.unchecked else "")
        print(f"ssot-check: {verdict} - {counts} in {target}")
        return {"INCOMPLETE": 3, "FAIL": 1, "PASS": 0}[verdict]


UNDECODABLE = set()


def read_text(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    if text.startswith("\ufeff"):
        text = text[1:]
    if "�" in text:
        UNDECODABLE.add(path)
    return text


def front_matter(text):
    """Return simple `key: value` pairs from a leading --- block, with YAML
    comments and quotes removed."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return data
        match = re.match(r"^([A-Za-z_][\w-]*):[ \t]*(.*?)[ \t]*$", line)
        if match:
            value = re.sub(r"(^|[ \t]+)#.*$", "", match.group(2)).strip()
            data[match.group(1)] = value.strip("'\"")
    return {}


# --- the line model --------------------------------------------------------

def _fm_end(lines):
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                return i + 1
    return 0


def _fence_step(line, fence, in_comment=False):
    if fence is None and not in_comment:
        m = FENCE_RE.match(line)
        if m and (m.group(1)[0] != "`" or "`" not in line[m.end():]):
            return m.group(1), True
    elif fence is not None:
        m = FENCE_RE.match(line)
        if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) and not line.strip()[len(m.group(1)):].strip():
            return None, True
        return fence, True
    return fence, False


def markdown_lines(text):
    """Yield (line_number, text) for Markdown outside front matter, fences and HTML comments."""
    lines = text.splitlines()
    fence, in_comment = None, False
    for index in range(_fm_end(lines), len(lines)):
        fence, fenced = _fence_step(lines[index], fence, in_comment)
        if fenced:
            continue
        visible, in_comment = strip_comments(lines[index], in_comment)
        yield index + 1, visible


def strip_comments(line, in_comment, comments_out=None):
    spans = [m.span() for m in INLINE_CODE_RE.finditer(line)]

    def opener(start):
        pos = line.find("<!--", start)
        while pos != -1 and any(a <= pos < b for a, b in spans):
            pos = line.find("<!--", pos + 4)
        return pos

    out, pos, opened = [], 0, None
    while pos <= len(line):
        if in_comment:
            end = line.find("-->", pos)
            if end == -1:
                return "".join(out), True
            if comments_out is not None and opened is not None:
                comments_out.append(line[opened:end])
            pos, in_comment, opened = end + 3, False, None
        else:
            begin = opener(pos)
            if begin == -1:
                out.append(line[pos:])
                break
            out.append(line[pos:begin])
            pos, in_comment, opened = begin + 4, True, begin + 4
    return "".join(out), in_comment


def blank_inline_code(line):
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


# --- headings and anchors --------------------------------------------------

def headings(text, md_lines=None):
    """Yield (line_number, level, heading_text) for ATX and Setext headings."""
    previous = None  # (number, text) of the last paragraph line
    for number, line in (markdown_lines(text) if md_lines is None else md_lines):
        atx = ATX_RE.match(line)
        if atx:
            yield number, len(atx.group(1)), (atx.group(2) or "").strip()
            previous = None
            continue
        setext = SETEXT_RE.match(line)
        if setext and previous is not None:
            yield previous[0], 1 if setext.group(1)[0] == "=" else 2, previous[1].strip()
            previous = None
            continue
        stripped = line.strip()
        is_paragraph = stripped and not stripped.startswith(("|", ">", "- ", "* ", "+ ")) \
            and not re.match(r"^\d+[.)] ", stripped) and not line.startswith(("    ", "\t"))
        if not is_paragraph:
            previous = None
        elif previous is None:
            previous = (number, line)


def heading_text(raw):
    """Approximate the rendered text GitHub slugs: links keep their label,
    inline code keeps its content, HTML tags are dropped."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"(\*\*|\*)(\S(?:.*?\S)?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)(__|_)(\S(?:.*?\S)?)\1(?!\w)", r"\2", text)
    return re.sub(r"<[^>]+>", "", text).strip()


def norm_heading(raw):
    return re.sub(r"^[\d.)\s]+", "", raw).lower()


def utf8_bytes(text):
    return len(text.encode("utf-8"))


def slug(text):
    """GitHub (github-slugger) anchor: lowercase, drop everything except
    letters, digits, underscore, hyphen and space, then each space -> '-'."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


_anchor_cache = {}
_real_cache = {}
SUBMODULE_ROOTS = set()
REPO_ROOT = [os.sep]  # set in main(): the repository containing SSOT/
GENERAL = [False]  # format 5 checks selected entry/direct local owners only


def real_path(path):
    res = _real_cache.get(path)
    if res is None:
        res = os.path.realpath(path)
        _real_cache[path] = res
    return res


def anchors(path):
    if path not in _anchor_cache:
        text = read_text(path)
        md_lines = list(markdown_lines(text))
        seen, found = {}, set()
        for _, _, raw in headings(text, md_lines):
            base = slug(heading_text(raw))
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f"{base}-{count}")
        for _, line in md_lines:
            found.update(re.findall(r"<a\s+(?:name|id)=\"([^\"]+)\"", line))
        _anchor_cache[path] = found
    return _anchor_cache[path]


# --- links -----------------------------------------------------------------

def parse_destination(line, start):
    """Parse an inline link destination starting right after ']('."""
    pos, n = start, len(line)
    while pos < n and line[pos] in " \t":
        pos += 1
    if pos < n and line[pos] == "<":
        end = line.find(">", pos)
        if end == -1:
            return None
        dest, pos = line[pos + 1:end], end + 1
    else:
        depth, begin = 0, pos
        while pos < n:
            ch = line[pos]
            if ch == "\\" and pos + 1 < n:
                pos += 2
                continue
            if ch in " \t":
                break
            if ch == "(":
                depth += 1
            elif ch == ")":
                if depth == 0:
                    break
                depth -= 1
            pos += 1
        dest = line[begin:pos]
    while pos < n and line[pos] in " \t":
        pos += 1
    if pos < n and line[pos] in "\"'(":
        end = line.find(")" if line[pos] == "(" else line[pos], pos + 1)
        if end == -1:
            return None
        pos = end + 1
        while pos < n and line[pos] in " \t":
            pos += 1
    return dest if pos < n and line[pos] == ")" else None


def links_in(line):
    for match in LABEL_RE.finditer(line):
        destination = parse_destination(line, match.end())
        if destination is not None:
            yield destination


def link_targets(text, md_lines=None):
    for number, line in (markdown_lines(text) if md_lines is None else md_lines):
        line = blank_inline_code(line)
        for destination in links_in(line):
            yield number, destination
        ref = REFDEF_RE.match(line)
        if ref:
            yield number, ref.group(2).strip("<>")


def is_local_link(target):
    return not SCHEME_RE.match(target) and (GENERAL[0] or not unquote(target).startswith("/"))


def resolve(doc, target):
    """Return (path or None, fragment) for a local link target."""
    target = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", target)  # CommonMark backslash escapes
    path_part, _, fragment = target.partition("#")
    path_part = unquote(path_part.partition("?")[0])
    if not path_part:
        return doc, fragment
    return os.path.normpath(os.path.join(os.path.dirname(doc), path_part)), fragment


def is_populated_dir(directory):
    try:
        return any(name != ".git" for name in os.listdir(directory))
    except OSError:
        return False


def check_link(report, doc, number, target, local_links=None, missing_links=None):
    target = target.strip()
    if not target or SCHEME_RE.match(target):
        return  # external URLs and mailto: are outside this checker's scope
    if unquote(target).startswith("/"):
        report.add("WARN", doc, number, f"absolute link path is machine-specific: {target}")
        if not GENERAL[0]:
            return
    resolved, fragment = resolve(doc, target)
    if report.documents is not None and resolved not in report.documents:
        return
    nested = None
    if not repository_local(resolved):
        if GENERAL[0]:
            try:
                os.stat(resolved)
            except FileNotFoundError:
                report.add("ERROR", doc, number, f"missing external-space target: {target}")
                return
            except OSError as error:
                report.unchecked.append(f"external-space target {target}: {error}")
                return
            report.add("INFO", doc, number, f"external-space route not read by this check: {target}")
            return
        nested = nested_git_root(resolved)
        if nested is None:
            report.add("WARN", doc, number,
                       f"link leaves the repository and only works where the same folders sit beside it: {target}")
            return
        if real_path(resolved) != nested and not is_populated_dir(nested):
            report.add("INFO", doc, number,
                       f"nested repository/submodule is not populated here; link target not verified: {target}")
            return
        if not os.path.exists(resolved):
            report.add("ERROR", doc, number, f"broken link (in nested repository): {target}")
            return
    elif not os.path.exists(resolved):
        if missing_links is not None:
            missing_links.append((doc, number, target, resolved))
        else:
            report.add("ERROR", doc, number, f"broken link: {target}")
        return
    elif local_links is not None and resolved != doc:
        local_links.append((doc, number, target, resolved))
    if not fragment or not os.path.isfile(resolved):
        return
    line_anchor = LINE_ANCHOR_RE.match(fragment)
    if line_anchor:
        with open(resolved, encoding="utf-8", errors="replace") as handle:
            length = sum(1 for _ in handle)
        start_line = int(line_anchor.group(1))
        end_line = int(line_anchor.group(2)) if line_anchor.group(2) is not None else start_line
        if start_line < 1 or end_line < start_line:
            report.add("ERROR", doc, number, f"invalid line anchor: {target}")
        elif end_line > length:
            report.add("ERROR", doc, number, f"line anchor past end of file: {target}")
        else:
            report.add("WARN", doc, number, f"line anchors drift when the file changes; link a heading: {target}")
    elif resolved.lower().endswith(".md") and unquote(fragment) not in anchors(resolved):
        report.add("ERROR", doc, number, f"missing heading anchor: {target}")


# --- hard-wrapped paragraphs --------------------------------------------------
# A paragraph written as several short lines reads as ragged text in an editor,
# and in Chinese or Japanese a line break inside a sentence can render as a
# stray space. Each paragraph and list item should be one line.

WRAP_MIN_RUN = 3        # consecutive lines of one paragraph
WRAP_MAX_WIDTH = 100    # every line of the run at most this wide (in characters)
BLOCK_START_RE = re.compile(r"^\s{0,3}(#|>|\||[-*+]\s|\d+[.)]\s|<|\[[^\]]+\]:|```|~~~)")


def hard_wrapped_paragraphs(text, md_lines=None):
    """Yield the first line number of each paragraph or list item that runs
    over WRAP_MIN_RUN or more short source lines."""
    run_start, run_length, in_item = None, 0, False
    for number, line in (markdown_lines(text) if md_lines is None else md_lines):
        stripped = line.strip()
        starts_item = bool(re.match(r"^\s*([-*+]|\d+[.)])\s", line))
        ends_run = not stripped or len(stripped) > WRAP_MAX_WIDTH or line.endswith(("  ", "\\")) \
            or (BLOCK_START_RE.match(line) and not starts_item) or line.startswith(("    ", "\t")) and not in_item
        if ends_run or starts_item:
            if run_length >= WRAP_MIN_RUN:
                yield run_start
            run_start, run_length, in_item = (number, 1, True) if starts_item and not ends_run else (None, 0, False)
            continue
        if run_start is None:
            run_start, run_length = number, 1
        else:
            run_length += 1
    if run_length >= WRAP_MIN_RUN:
        yield run_start


# --- cold-tier classification and bloat auto-discovery ----------------------

def doc_rel_parts(doc, ssot_dir):
    base = ssot_dir if inside(doc, ssot_dir) else REPO_ROOT[0]
    rel = os.path.relpath(real_path(doc), real_path(base))
    return [p.lower() for p in rel.split(os.sep) if p not in ("", ".")]


def is_cold_dir_part(part):
    return (part in COLD_DIRS
            or re.sub(r"^\d+[-_.\s]+", "", part) in COLD_ZH_EXACT_DIRS
            or any(tok in part for tok in COLD_ZH_DIR_TOKENS))


def is_cold_index(doc, ssot_dir, readme):
    parts = None if doc == readme else doc_rel_parts(doc, ssot_dir)
    if not parts:
        return False
    stem = os.path.splitext(parts[-1])[0]
    return stem in COLD_INDEX_STEMS or (any(is_cold_dir_part(p) for p in parts[:-1]) and (stem in COLD_INDEX_NAMES or stem.endswith(COLD_INDEX_SUFFIXES)))


def is_active_research(text, md_lines=None):
    src = markdown_lines(text) if md_lines is None else md_lines
    return any(ACTIVE_RESEARCH_RE.match(line) for _, (_, line) in zip(range(30), src))


def is_cold_archive(doc, ssot_dir, readme, text, md_lines=None):
    if doc == readme or is_cold_index(doc, ssot_dir, readme):
        return False
    tier = front_matter(text).get("ssot_tier", "").lower()
    if tier in WARM_TIERS or tier == "cold":
        return tier == "cold"
    parts = doc_rel_parts(doc, ssot_dir)
    if not parts:
        return False
    parents = parts[:-1]
    if any(p != "research" and is_cold_dir_part(p) for p in parents):
        return True
    if "research" in parents:
        return not is_active_research(text, md_lines)
    stem = os.path.splitext(parts[-1])[0]
    if stem.endswith(COLD_STEM_SUFFIXES):
        return True
    return False if (GENERAL[0] and stem in {"history", "archive"}) else stem in COLD_EXACT_STEMS


def is_declared_cold_shard(doc, text=None, is_entry=False):
    if is_entry:
        return False
    tier = front_matter(text).get("ssot_tier", "").lower() if text is not None else ""
    if tier in WARM_TIERS or tier == "cold":
        return tier == "cold"
    stem = os.path.splitext(os.path.basename(doc))[0].lower()
    return stem in COLD_SHARD_NAMES or stem.startswith("retired") or stem.endswith(("-retired", "_retired"))


def is_cold_retired_shard(doc, text=None, row_count=0, retired_count=0, active_count=0, is_entry=False):
    if is_entry or active_count > 0 or (text is not None and front_matter(text).get("ssot_tier", "").lower() in WARM_TIERS):
        return False
    return (row_count > 0 and retired_count == row_count) or (row_count == 0 and is_declared_cold_shard(doc, text, is_entry))


def is_cold_heading(raw):
    return bool(COLD_HEADING_RE.match(norm_heading(heading_text(raw)).strip()))


def scan_document_lines(text):
    lines = text.splitlines()
    start = _fm_end(lines)
    out = [(i + 1, lines[i]) for i in range(start)]
    fence, in_comment, opens, closes = None, False, [], []
    for i in range(start, len(lines)):
        line, num = lines[i], i + 1
        fence, fenced = _fence_step(line, fence, in_comment)
        if fenced:
            out.append((num, line))
            continue
        comments, was_in = [], in_comment
        visible, in_comment = strip_comments(line, in_comment, comments)
        for tok in comments:
            low = tok.strip().lower()
            if low == "ssot:cold":
                opens.append(num)
            elif low in ("/ssot:cold", "ssot:cold:end"):
                closes.append(num)
        if not ((was_in or line.strip()) and not visible.strip()):
            out.append((num, visible))
    return out, opens, closes


def in_cold_region(num, cold_start, inverted_spans):
    return cold_start is not None and num >= cold_start and not any(s <= num and (e is None or num < e) for s, e in inverted_spans)


def find_cold_boundary(vis_lines, all_headings, opens, closes):
    cold_m = opens[0] if opens else None
    cold_h = next(((n, l) for n, l, r in all_headings if l >= 2 and is_cold_heading(r)), None)
    if cold_m is None and cold_h is None:
        return None, (), 0
    spans = []
    if cold_m is not None and (cold_h is None or cold_m < cold_h[0]):
        cold_start, end_m = cold_m, next((c for c in closes if c > cold_m), None)
        if end_m is not None:
            in_cold, non_cold = False, end_m + 1
            for n, _, r in all_headings:
                if n > end_m and not in_cold and (is_cold_heading(r) or any(non_cold <= o < n for o in opens)):
                    spans.append((non_cold, min([n] + [o for o in opens if non_cold <= o < n])))
                    in_cold, non_cold = True, None
            if not in_cold:
                spans.append((non_cold, next((o for o in opens if o >= non_cold), None)))
        else:
            first_vis = next(((n, ln) for n, ln in vis_lines if n > cold_m and ln.strip()), None)
            custom_h = next(((n, l, r) for n, l, r in all_headings if first_vis and n == first_vis[0] and l >= 2), None)
            scan_after, cold_level = (custom_h[0], custom_h[1]) if (custom_h and not DATE_RE.search(custom_h[2])) else (cold_m, 2)
    else:
        cold_start, cold_level = cold_h
        end_m, scan_after = None, cold_start
    if end_m is None:
        in_cold, non_cold = True, None
        for n, l, r in all_headings:
            if n <= scan_after:
                continue
            if in_cold and l <= cold_level and not is_cold_heading(r) and not DATE_RE.search(r):
                in_cold, non_cold = False, n
            elif not in_cold and (is_cold_heading(r) or any(non_cold < o < n for o in opens)):
                spans.append((non_cold, n))
                in_cold, non_cold = True, None
        if not in_cold and non_cold is not None:
            spans.append((non_cold, next((o for o in opens if o > non_cold), None)))
    if not spans:
        return cold_start, (), 0
    inv = "\n".join(ln for n, ln in vis_lines if any(s <= n and (e is None or n < e) for s, e in spans))
    return cold_start, tuple(spans), len(inv)


def measure_visible(vis_lines, cold_start=None, inverted_spans=(), exclude_invariants=False):
    joined = "\n".join(
        ln for n, ln in vis_lines
        if not in_cold_region(n, cold_start, inverted_spans)
        and not (exclude_invariants and re.match(rf"^\s*\|\s*[`*]*{ID_PAT}", ln))
    )
    return len(joined), utf8_bytes(joined)


def h2_sections(vis_lines, all_headings, end_line=None, exclude_invariants=False):
    bounds, cur = [], None
    for n, l, r in all_headings:
        if end_line is not None and n >= end_line:
            break
        if l in (1, 2):
            if cur is not None:
                bounds.append((cur[0], n, cur[1]))
            cur = (n, r) if l == 2 else None
    if cur is not None:
        bounds.append((cur[0], end_line, cur[1]))
    return [(s, heading_text(r), len("\n".join(
        ln for n, ln in vis_lines
        if s <= n and (e is None or n < e) and not (exclude_invariants and re.match(rf"^\s*\|\s*[`*]*{ID_PAT}", ln))
    ))) for s, e, r in bounds]


def is_task_like_doc(doc, readme):
    stem = os.path.splitext(os.path.basename(doc))[0].lower()
    return doc == readme or stem in TASK_FILE_EXACT_STEMS or stem.startswith(TASK_FILE_STEM_PREFIXES)


def fmt_size(chars, nbytes, c_lim, b_lim, extra=""):
    if chars > c_lim:
        return f"{chars} characters{extra} (>{c_lim})", f"{chars} chars"
    return f"{nbytes} bytes ({chars} chars{extra}; >{b_lim} bytes)", f"{nbytes} bytes"


def row_limit_summary(rows, c_lim, b_lim):
    """Return (top_row, limit_label, top_size_label, compact_label) for rows=(num, key, chars, bytes)."""
    c_hits = sum(r[2] > c_lim for r in rows)
    if c_hits == len(rows):
        top = max(rows, key=lambda r: r[2])
        return top, f"{c_lim} characters", f"{top[2]} chars", f"{top[2]} chars", f">{c_lim} chars"
    if c_hits == 0:
        top = max(rows, key=lambda r: r[3])
        return top, f"{b_lim} bytes", f"{top[3]} bytes / {top[2]} chars", f"{top[3]} bytes", f">{b_lim} bytes"
    top = max(rows, key=lambda r: (r[2] > c_lim, r[2], r[3]))
    return top, f"{c_lim} characters or {b_lim} bytes", f"{top[2]} chars / {top[3]} bytes", f"{top[2]} chars / {top[3]} bytes", f">{c_lim} chars/{b_lim} bytes"


def check_cold_index_bloat(report, doc, md_lines, vis_lines, is_ssot_owned):
    ext = not GENERAL[0] and not is_ssot_owned
    prefix = "external owner, " if ext else ""
    ic, ib = measure_visible(vis_lines)
    if ic > COLD_INDEX_INFO_CHARS or ib > COLD_INDEX_INFO_BYTES:
        over_warn = ic > DOC_WARN_CHARS
        sz, csz = fmt_size(ic, ib, DOC_WARN_CHARS if over_warn else COLD_INDEX_INFO_CHARS, COLD_INDEX_INFO_BYTES)
        report.add("WARN" if (over_warn and is_ssot_owned) else "INFO", doc, None,
                   f"cold index is {sz}; keep cold indexes to one-line topic/date locators rather than replaying archive summaries")
        report.add_compaction(doc, f"{prefix}cold index {csz} -> {'propose trimming index' if ext else 'trim to 1-line locators'}")
    stats = {n: (len(ln), utf8_bytes(ln)) for n, ln in md_lines}
    soft, has_hard = [], False
    for tbl in pipe_tables(md_lines):
        if len(tbl) < 3 or len(tbl[1][1]) != len(tbl[0][1]) or not all(SEPARATOR_CELL_RE.match(c) for c in tbl[1][1]):
            continue
        for n, _ in tbl[2:]:
            rl, rb = stats.get(n, (0, 0))
            if rl > COLD_INDEX_ROW_SOFT_CHARS or rb > COLD_INDEX_ROW_SOFT_BYTES:
                soft.append((n, n, rl, rb))
                has_hard |= rl > COLD_INDEX_ROW_HARD_CHARS or rb > COLD_INDEX_ROW_HARD_BYTES
    if len(soft) >= COLD_INDEX_ROW_SOFT_COUNT or has_hard:
        top, lim_s, top_s, c_s, _ = row_limit_summary(soft, COLD_INDEX_ROW_SOFT_CHARS, COLD_INDEX_ROW_SOFT_BYTES)
        report.add("INFO", doc, top[0],
                   f"{len(soft)} cold-index table row(s) exceed {lim_s} (longest: line {top[0]} at {top_s}); "
                   "keep cold indexes to one-line locators without summary columns")
        report.add_compaction(doc, f"{prefix}{len(soft)} verbose index rows (max {c_s}) -> {'propose trimming index cells' if ext else 'trim index cells'}")


def check_completed_checkboxes(report, doc, readme, md_lines, cold_start, inverted_spans=(), is_external=False):
    checked = total = 0
    first_checked = None
    for n, line in md_lines:
        if in_cold_region(n, cold_start, inverted_spans):
            continue
        m = CHECKBOX_RE.match(line)
        if m:
            total += 1
            if m.group(1).lower() == "x":
                checked += 1
                first_checked = first_checked or n
    if (is_task_like_doc(doc, readme) and checked >= CHECKBOX_TASK_INFO_COUNT) or (checked >= CHECKBOX_WARM_INFO_COUNT and checked * 2 >= total):
        report.add("INFO", doc, first_checked,
                   f"{checked} completed checklist item(s) (`- [x]`) out of {total} in active document; archive or remove finished items so active reads stay concise")
        report.add_compaction(doc, f"external owner, {checked} completed checkboxes -> propose pruning" if is_external else f"{checked} completed checkboxes -> prune/archive finished items")


def check_document_bloat(report, doc, readme, ssot_dir, text, shard_paths, cold_shards, md_lines=None):
    if "/.bootstrap/" in doc:
        return None
    md_lines = list(markdown_lines(text)) if md_lines is None else md_lines
    is_reg = doc == readme or doc in shard_paths
    is_owned = doc == readme or (inside(doc, ssot_dir) and (not GENERAL[0] or doc in shard_paths))
    ext = not GENERAL[0] and not is_owned
    vis, opens, closes = scan_document_lines(text)
    if is_cold_index(doc, ssot_dir, readme):
        check_cold_index_bloat(report, doc, md_lines, vis, is_owned)
        return "cold"
    if doc in cold_shards or (doc not in shard_paths and is_cold_archive(doc, ssot_dir, readme, text, md_lines)):
        return "cold"
    all_h = list(headings(text, md_lines))
    c_start, inv_spans, inv_chars = find_cold_boundary(vis, all_h, opens, closes)
    wc, wb = measure_visible(vis, c_start, inv_spans, exclude_invariants=is_reg)
    tb = utf8_bytes(text)
    wh = [(n, l, r) for n, l, r in all_h if not in_cold_region(n, c_start, inv_spans)]
    wd = sum(1 for _, _, r in wh if DATE_RE.search(r))
    lim = README_WARN_CHARS if doc == readme else DOC_WARN_CHARS
    cdest = "a cold archive (or trailing ## History (cold) if layout is fixed)" if (GENERAL[0] or ext) else "a cold archive (decisions/ or *-history.md)"
    dact = "propose consolidation/cold archive" if ext else ("consolidate + cold archive (or ## History (cold) if layout fixed)" if GENERAL[0] else "consolidate + offload history to cold archive")
    pfx = "external owner, " if ext else ""
    sact = "propose split/consolidation" if (ext or GENERAL[0]) else "split by topic"
    dated_tail = f"consolidate current behavior and move superseded history to {cdest}"
    split_tail = "split it by topic or move detail out"
    def emit(level, line, msg, cand):
        report.add(level, doc, line, msg)
        report.add_compaction(doc, cand)
    if doc == readme:
        secs = h2_sections(vis, all_h, c_start, exclude_invariants=True)
        non_inv = [(n, t, c) for n, t, c in secs if not norm_heading(t).startswith(INVARIANT_HEADINGS)]
        if wc > lim:
            top = max(non_inv, key=lambda x: x[2]) if non_inv else None
            lg = f"; largest section: ## {top[1]} ({top[2]} chars)" if top and top[2] > 0 else ""
            if wd >= DATED_HISTORY_INFO_HEADINGS:
                emit("WARN", None, f"{wc} characters is past the {lim}-character reading budget (invariant rows not counted) and has {wd} dated headings{lg}; {dated_tail}", f"{wc} entry chars, {wd} dated headings -> {dact}")
            else:
                emit("WARN", None, f"{wc} characters is past the {lim}-character reading budget (invariant rows not counted){lg}; {split_tail}", f"{wc} entry prose chars -> trim/split entry")
        for sl, title, sc in non_inv:
            if not norm_heading(title).startswith(ENTRY_CORE_SECTIONS) and sc > ENTRY_SECTION_INFO_CHARS:
                emit("INFO", sl, f"entry section '## {title}' is {sc} characters (>{ENTRY_SECTION_INFO_CHARS}); move detail to a topic owner or prune resolved items", f"## {title} ({sc} chars) -> move detail or prune")
        if len(text) > TOTAL_ENTRY_INFO_CHARS or tb > TOTAL_ENTRY_INFO_BYTES:
            sz, csz = fmt_size(len(text), tb, TOTAL_ENTRY_INFO_CHARS, TOTAL_ENTRY_INFO_BYTES, ", including register rows")
            if len(text) > TOTAL_ENTRY_INFO_CHARS:
                sz = f"{len(text)} characters (including register rows; >{TOTAL_ENTRY_INFO_CHARS})"
            report.add("INFO", doc, None, f"total {os.path.basename(readme)} size is {sz}; large entries cause tool truncation — shard invariants or trim rows")
            if not any(w == os.path.relpath(readme, report.root) and "sharding" in d for w, d in report.compactions):
                report.add_compaction(doc, f"{csz} total -> propose sharding/trimming entry")
    else:
        h2 = sum(1 for _, l, _ in wh if l == 2)
        if wc > lim:
            lvl = "WARN" if is_owned else "INFO"
            if wd >= DATED_HISTORY_INFO_HEADINGS:
                emit(lvl, None, f"{wc} characters is past the {lim}-character reading budget and has {wd} dated headings; {dated_tail}", f"{pfx}{wc} chars, {wd} dated headings -> {dact}")
            elif not is_reg and h2 >= MEGA_DOC_H2_SECTIONS:
                emit(lvl, None, f"{wc} characters across {h2} level-2 sections is past the {lim}-character reading budget; consider splitting by topic or moving detail out", f"{pfx}{wc} chars, {h2} sections -> {sact}")
            else:
                emit(lvl, None, f"{wc} characters is past the {lim}-character reading budget{' (invariant rows not counted)' if is_reg else ''}; {split_tail}", f"{pfx}{wc} chars -> {sact}")
        elif wc > DATED_EARLY_INFO_CHARS and wd >= DATED_HISTORY_INFO_HEADINGS:
            emit("INFO", None, f"{wc} characters with {wd} dated headings; consolidate current state and move superseded history to {cdest}", f"{pfx}{wc} chars, {wd} dated headings -> {dact}")
        elif wb > DOC_INFO_BYTES:
            if wd >= DATED_HISTORY_INFO_HEADINGS:
                emit("INFO", None, f"{wb} bytes ({wc} chars; >{DOC_INFO_BYTES} bytes) with {wd} dated headings; {dated_tail}", f"{pfx}{wb} bytes, {wd} dated headings -> {dact}")
            else:
                sec = f" across {h2} level-2 sections" if not is_reg and h2 >= MEGA_DOC_H2_SECTIONS else ""
                csec = f", {h2} sections" if sec else ""
                emit("INFO", None, f"{wb} bytes ({wc} chars{sec}; >{DOC_INFO_BYTES} bytes) is past the UTF-8 reading budget; {split_tail}", f"{pfx}{wb} bytes{csec} -> {sact}")
    if c_start is not None:
        if inv_chars > COLD_TAIL_INVERTED_CHARS:
            emit("INFO", c_start, f"cold section starts above {inv_chars} characters of non-cold sections; move active sections above the cold boundary so partial head-reads land on current state",
                 f"{pfx}inverted cold tail ({inv_chars} active chars below) -> {'propose reordering top-down' if ext else 'reorder top-down'}")
        if len(text) > COLD_TAIL_TRUNC_CHARS or tb > COLD_TAIL_TRUNC_BYTES:
            sz, csz = fmt_size(len(text), tb, COLD_TAIL_TRUNC_CHARS, COLD_TAIL_TRUNC_BYTES, " including its cold tail")
            emit("INFO", c_start, f"total file size is {sz}; offload the cold tail to a separate cold history file to avoid tool truncation",
                 f"{pfx}{csz} incl. cold tail -> {'propose offloading cold tail' if ext else 'offload cold tail'}")
    check_completed_checkboxes(report, doc, readme, md_lines, c_start, inv_spans, ext)
    return c_start, inv_spans


# --- the invariants register -------------------------------------------------

def table_cells(line):
    """Split a pipe-table row into cells; outer pipes are optional in GFM."""
    stripped = line.strip()
    if stripped.startswith(("#", ">", "- ", "* ", "+ ")) or re.match(r"^\d+[.)]\s", stripped):
        return None
    if not re.search(r"(?<!\\)\|", blank_inline_code(stripped)):
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)]


def inside(path, root):
    rp, rr = real_path(path), real_path(root)
    return rp == rr or rp.startswith(rr + os.sep) if rr != os.sep else rp.startswith(os.sep)


def pipe_tables(lines):
    """Group consecutive Markdown pipe-table lines into lists of (line number, cells)."""
    tables, current, first_piped = [], [], False
    for number, line in lines:
        cells = table_cells(line)
        if cells is None:
            if len(current) >= 2 or (current and first_piped):
                tables.append(current)
            current, first_piped = [], False
        else:
            if not current:
                first_piped = line.lstrip().startswith("|")
            current.append((number, cells))
    if len(current) >= 2 or (current and first_piped):
        tables.append(current)
    return tables


def register_tables(lines, text):
    """The Invariants section's lines and its pipe tables (lists of (line number, cells)); None if no section."""
    sections = []
    current = None
    for number, level, raw in headings(text, lines):
        if current is not None and level <= current[1]:
            current[2] = number
            sections.append(current)
            current = None
        if current is None and norm_heading(raw).startswith(INVARIANT_HEADINGS):
            current = [number, level, None]
    if current is not None:
        sections.append(current)
    if not sections:
        return None
    fallback = None
    for start, _level, end in sections:
        body = [(n, line) for n, line in lines if n > start and (end is None or n < end)]
        tables = pipe_tables(body)
        if tables:
            return body, tables
        if fallback is None:
            fallback = (body, tables)
    return fallback


def is_invariants_subdir(path, ssot_dir):
    inv_dir = os.path.abspath(os.path.join(ssot_dir, "invariants"))
    target = os.path.abspath(path)
    return target != inv_dir and os.path.commonpath([target, inv_dir]) == inv_dir


def is_register_shard(path, ssot_dir, text=None):
    if is_invariants_subdir(path, ssot_dir):
        return True
    return text is not None and front_matter(text).get("ssot_register") == "shard"


def refdef_map(lines):
    return {m.group(1).lower(): m.group(2).strip("<>")
            for _, line in lines for m in [REFDEF_RE.match(line)] if m}


def line_links(line, refdefs):
    clean = blank_inline_code(line)
    targets = list(links_in(clean))
    for label, alt in re.findall(r"\[([^\]]+)\]\[([^\]]*)\]", clean):
        target = refdefs.get((alt or label).lower())
        if target:
            targets.append(target)
    return targets


def non_table_invariants_links(lines, body, tables=None):
    """Return local link targets on non-table lines inside ## Invariants."""
    refdefs = refdef_map(lines)
    table_lines = {num for tbl in (pipe_tables(body) if tables is None else tables) for num, _ in tbl}
    return [(number, target) for number, line in body if number not in table_lines
            for target in line_links(line, refdefs)]


def linked_shards(readme, lines, body, ssot_dir, selection=None, tables=None):
    """Return ([(shard_path, shard_text), ...], set_of_shard_link_lines) for linked register shards."""
    shards, seen_paths, shard_lines = [], set(), set()
    for number, target in non_table_invariants_links(lines, body, tables):
        if not is_local_link(target):
            continue
        path, _ = resolve(readme, target)
        if path == readme or path in seen_paths or not path.lower().endswith(".md"):
            continue
        if not repository_local(path):
            continue
        if selection is not None and path not in selection:
            shard_lines.add(number)
            continue
        if not os.path.isfile(path):
            if is_invariants_subdir(path, ssot_dir):
                shard_lines.add(number)
            continue
        shard_text = read_text(path)
        if is_register_shard(path, ssot_dir, shard_text):
            seen_paths.add(path)
            shards.append((path, shard_text))
            shard_lines.add(number)
    return shards, shard_lines


def rows_from_tables(tables, doc_path):
    rows = {}
    for table in tables:
        for number, cells in table:
            if len(cells) == 6:
                ident = cells[0].strip("`* ")
                if INVARIANT_ID_RE.match(ident):
                    rows.setdefault(ident, (doc_path, number, cells))
    return rows


def register_rows(text, doc_path=None):
    """Map each invariant ID to (line number, its six cells) — or (doc_path, line, cells) when doc_path is set."""
    found = register_tables(list(markdown_lines(text)), text)
    tables = found[1] if found else []
    if doc_path is not None:
        return rows_from_tables(tables, doc_path)
    return {ident: (number, cells) for ident, (_, number, cells) in rows_from_tables(tables, "").items()}


def validate_register_tables(report, doc, lines, body, tables, seen, shard_lines=(), doc_text=None, is_entry=False):
    refdefs = refdef_map(lines)
    stats = {n: (len(ln), utf8_bytes(ln)) for n, ln in lines}
    row_count, long_rows, retired_rows, active_rows = 0, [], [], []
    if not tables:
        for n, ln in body:
            if n not in shard_lines and re.search(rf"\b{ID_PAT}\b", blank_inline_code(ln)):
                report.add("ERROR", doc, n, f"invariants must be written as a table ({INVARIANT_COLUMNS}) so they can be checked")
                break
    for tbl in tables:
        hn, hdr = tbl[0]
        if len(hdr) != 6:
            report.add("ERROR", doc, hn, f"invariants table needs 6 columns: {INVARIANT_COLUMNS}")
            continue
        if any(c.strip("`* ").lower() not in names for c, names in zip(hdr, INVARIANT_HEADERS)):
            report.add("ERROR", doc, hn, f"invariants table columns must be, in order: {INVARIANT_COLUMNS} (or 类型 / 规则 / 解释位置 / 状态 / 来源)")
            continue
        if len(tbl) < 2 or len(tbl[1][1]) != 6 or not all(SEPARATOR_CELL_RE.match(c) for c in tbl[1][1]):
            report.add("ERROR", doc, hn, "invariants table needs a separator row (|---|---|...) under its header")
            continue
        for n, cells in tbl[2:]:
            if len(cells) != 6:
                report.add("ERROR", doc, n, "invariants row does not have 6 cells")
                continue
            ident, kind, rule, explained, status, source = cells
            ident, status = ident.strip("`* "), status.strip("`* ")
            if not INVARIANT_ID_RE.match(ident):
                report.add("ERROR", doc, n, f"invariant ID '{ident}' should look like INV-01")
            elif ident in seen:
                fd, fl = seen[ident]
                where = f"line {fl}" if fd == doc else f"{os.path.relpath(fd, report.root)}:{fl}"
                report.add("ERROR", doc, n, f"duplicate invariant ID {ident} (first on {where})")
            else:
                seen[ident] = (doc, n)
                row_count += 1
                rl, rb = stats.get(n, (0, 0))
                if rl > ROW_INFO_CHARS or rb > ROW_INFO_BYTES:
                    long_rows.append((n, ident, rl, rb))
            if not kind:
                report.add("ERROR", doc, n, f"invariant {ident} needs a kind (product promise, architecture invariant, or process rule)")
            if not rule:
                report.add("ERROR", doc, n, f"invariant {ident} has an empty rule")
            targets = line_links(explained, refdefs)
            if not targets:
                report.add("ERROR", doc, n, f"invariant {ident} needs a link to where it is explained")
            for target in targets:
                path = None if SCHEME_RE.match(target) else resolve(doc, target)[0]
                if GENERAL[0] and (path is None or not repository_local(path)):
                    report.add("INFO", doc, n, f"external explanation not checked: {target}")
                elif path is None or not repository_local(path) or not path.lower().endswith(".md"):
                    report.add("ERROR", doc, n, f"invariant {ident} needs a Markdown explanation in the same repository ({target}); URLs, other repositories, and symlink escapes are not explanations")
            if status.lower() not in INVARIANT_STATUSES:
                report.add("ERROR", doc, n, f"invariant {ident} status '{status}' must be confirmed, candidate, or retired")
            elif status.lower() == "retired":
                retired_rows.append((n, ident))
            else:
                active_rows.append((n, ident))
            if not source:
                report.add("ERROR", doc, n, f"invariant {ident} needs a source (user directive, decision, or date)")
    if active_rows and is_declared_cold_shard(doc, doc_text, is_entry=is_entry):
        report.add("WARN", doc, active_rows[0][0],
                   f"{len(active_rows)} active (confirmed/candidate) invariant row(s) in cold shard {os.path.basename(doc)}; "
                   "routine preflight skips cold shards — move active rules to an active shard or set ssot_tier: warm")
    cold_shard = is_cold_retired_shard(doc, doc_text, row_count, len(retired_rows), len(active_rows), is_entry=is_entry)
    if long_rows and not cold_shard:
        top, lim_s, top_s, _, clim = row_limit_summary(long_rows, ROW_INFO_CHARS, ROW_INFO_BYTES)
        others = [ident for _, ident, _, _ in long_rows if ident != top[1]][:3]
        extra = f"; also {', '.join(others)}{', ...' if len(long_rows) > 4 else ''}" if others else ""
        report.add("INFO", doc, top[0],
                   f"{len(long_rows)} register row(s) exceed {lim_s} (longest: {top[1]} at {top_s}{extra}); "
                   "keep each row to a concise constraint and move prose/history to Explained in")
        report.add_compaction(doc, f"{len(long_rows)} long rows {clim} -> trim rows")
    if len(retired_rows) >= RETIRED_INLINE_INFO_ROWS and not cold_shard:
        report.add("INFO", doc, retired_rows[0][0],
                   f"{len(retired_rows)} retired invariant row(s) inline in {os.path.basename(doc)}; "
                   "consider moving retired rows to a cold shard (such as invariants/retired.md) so active reads stay concise")
        if not is_entry:
            report.add_compaction(doc, f"{len(retired_rows)} retired rows -> invariants/retired.md")
    return row_count, cold_shard, len(retired_rows)


def looks_like_invariants_table(table):
    header = {cell.strip("`* ").lower() for cell in table[0][1]}
    matched_cols = sum(1 for names in INVARIANT_HEADERS if any(name in header for name in names))
    if matched_cols >= 2 or len(table[0][1]) == 6:
        return True
    return any(INVARIANT_ID_RE.match(cells[0].strip("`* ")) for _, cells in table[1:] if cells)


def invariants_sections(text, md_lines=None):
    """Return list of (start_line, end_line_or_None) spans for all INVARIANT_HEADINGS sections."""
    sections = []
    current = None
    for number, level, raw in headings(text, md_lines):
        if current is not None and level <= current[1]:
            sections.append((current[0], number))
            current = None
        if current is None and norm_heading(raw).startswith(INVARIANT_HEADINGS):
            current = (number, level)
    if current is not None:
        sections.append((current[0], None))
    return sections


def shard_register_tables(lines, text):
    sections = invariants_sections(text, lines)
    if not sections:
        all_tables = pipe_tables(lines)
        inv_tables = [table for table in all_tables if looks_like_invariants_table(table)]
        return lines, (inv_tables if inv_tables else all_tables)
    in_section = lambda num: any(start < num and (end is None or num < end) for start, end in sections)
    body = [(n, line) for n, line in lines if in_section(n)]
    outside = [(n, line) for n, line in lines if not in_section(n)]
    tables = []
    for start, end in sections:
        sec_lines = [(n, line) for n, line in lines if start < n and (end is None or n < end)]
        tables.extend(pipe_tables(sec_lines))
    for table in pipe_tables(outside):
        if looks_like_invariants_table(table):
            tables.append(table)
    tables.sort(key=lambda tbl: tbl[0][0])
    return body, tables


def check_invariants(report, readme, text, ssot_dir):
    lines = list(markdown_lines(text))
    found = register_tables(lines, text)
    if found is None:
        report.add("WARN", readme, None, "no Invariants section; add one (it may say there are none yet)")
        return [], set()
    body, tables = found
    shards, shard_lines = linked_shards(readme, lines, body, ssot_dir, report.documents, tables)
    seen = {}
    inline_rows, _, inline_retired = validate_register_tables(report, readme, lines, body, tables, seen, shard_lines, text, is_entry=True)
    inv_base = "invariants" if GENERAL[0] or os.path.basename(ssot_dir) != "SSOT" else "SSOT/invariants"
    if inline_rows >= INLINE_SHARD_INFO_ROWS:
        target = f"{inv_base}/<topic>.md (relative to entry dir)" if inv_base == "invariants" else f"{inv_base}/<topic>.md"
        report.add("INFO", readme, None, f"{inline_rows} inline invariant rows in {os.path.basename(readme)}; optional topic shards ({target}) keep entry reads small")
        if inline_retired >= RETIRED_INLINE_INFO_ROWS:
            report.add_compaction(readme, f"{inline_rows} inline; {inline_retired} retired -> propose sharding into {inv_base}/<topic>.md + {inv_base}/retired.md")
        else:
            report.add_compaction(readme, f"{inline_rows} inline -> propose sharding into {inv_base}/<topic>.md")
    elif inline_retired >= RETIRED_INLINE_INFO_ROWS:
        act = f"move to {inv_base}/retired.md" if any(is_declared_cold_shard(p, t) for p, t in shards) else f"propose {inv_base}/retired.md"
        report.add_compaction(readme, f"{inline_retired} retired -> {act}")
    cold_shards = set()
    for sp, st in shards:
        sl = list(markdown_lines(st))
        sb, stbl = shard_register_tables(sl, st)
        srows, is_cold, _ = validate_register_tables(report, sp, sl, sb, stbl, seen, (), st)
        sb_len = utf8_bytes(st)
        if is_cold:
            cold_shards.add(sp)
            if len(st) > COLD_SHARD_TRUNC_CHARS or sb_len > COLD_SHARD_TRUNC_BYTES:
                sz, csz = fmt_size(len(st), sb_len, COLD_SHARD_TRUNC_CHARS, COLD_SHARD_TRUNC_BYTES)
                report.add("INFO", sp, None, f"cold retired shard is {sz}; split by year or topic to avoid tool truncation")
                report.add_compaction(sp, f"cold shard {csz} -> split cold archive")
        elif len(st) > SHARD_INFO_CHARS or sb_len > SHARD_INFO_BYTES or srows > SHARD_INFO_ROWS:
            if len(st) > SHARD_INFO_CHARS or srows > SHARD_INFO_ROWS:
                sz, csz = f"{len(st)} characters and {srows} row(s) (>{SHARD_INFO_CHARS} chars or >{SHARD_INFO_ROWS} rows)", f"{len(st)} chars"
            else:
                sz, csz = f"{sb_len} bytes ({len(st)} chars) and {srows} row(s) (>{SHARD_INFO_BYTES} bytes)", f"{sb_len} bytes"
            report.add("INFO", sp, None, f"invariants shard is {sz}; split by sub-topic or trim rows to avoid tool truncation")
            report.add_compaction(sp, f"{csz}/{srows} rows -> split shard")
    return shards, cold_shards


# --- git -----------------------------------------------------------------------
# The checker never writes. These settings stop git from writing or running
# anything on its behalf: no optional index refresh, no filesystem-monitor hook,
# and no fetching of missing objects in a partial clone.
# Hooks and callers may export another worktree's Git routing. Every command
# here must inspect the requested repository, including its own history/index.
GIT_ROUTING_ENV = {
    "GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR", "GIT_INDEX_FILE",
    "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_SHALLOW_FILE",
    "GIT_PREFIX", "GIT_IMPLICIT_WORK_TREE",
}
GIT_ENV = {key: value for key, value in os.environ.items() if key not in GIT_ROUTING_ENV}
GIT_ENV.update(GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1")
GIT_SAFE = ("-c", "core.fsmonitor=false", "-c", "core.quotepath=off")


GIT_NO = 1  # rev-parse --verify --quiet and merge-base --is-ancestor answer "no" with 1


class GitError(Exception):
    pass


def git(directory, *args):
    result = subprocess.run(["git", *GIT_SAFE, "-C", directory, *args], env=GIT_ENV,
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False)
    return result.returncode, result.stderr


def git_output(directory, *args):
    """Return git's stdout, decoded without losing any byte of a file name.
    Raises GitError when git fails, FileNotFoundError when git is missing."""
    result = subprocess.run(["git", *GIT_SAFE, "-C", directory, *args], env=GIT_ENV,
                            capture_output=True, check=False)
    if result.returncode != 0:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise GitError(message or f"git {args[0]} exited with {result.returncode}")
    return result.stdout.decode("utf-8", "surrogateescape")


# --- mentions of files that no longer exist ------------------------------------
# SSOT names the file that holds a detail instead of copying it, so a file path
# is the main link between a document and the code. When a change deletes or
# moves that file, the sentence around it usually becomes wrong. Git can tell
# that a mentioned path existed and is gone; only a reader can tell whether the
# sentence meant the past. Records of the past (decisions/, research/) are not
# checked, and a line that names the removing commit counts as history.

PATH_SPAN_RE = re.compile(r"^((?:\.{1,2}/)*\.?[\w@+-][\w@.+-]*(?:/[\w@.+-]+)+)/?(?::\d+(?:-\d+)?|::\S+)?$")
REF_LABEL_RE = re.compile(r"!?\[(?:[^\[\]\\]|\\.)*\]\[[^\]]*\]")
HEX_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
HISTORY_DIRS = {"decisions", "research"}
SKIP_FILES = {"STATUS.md", "HISTORY.md", "_manifest.md"}  # v2 ledgers: never current guidance


def path_mentions(ssot_dir, doc, text, cold_start=None, inverted_spans=(), md_lines=None):
    """Yield (line, path, line_text) for inline code spans that hold only a path.
    A link's own label is skipped: the link target is what the link check tests."""
    relative = os.path.relpath(doc, ssot_dir).split(os.sep)
    if HISTORY_DIRS & {part.lower() for part in relative[:-1]} or ".bootstrap" in relative \
            or relative[-1] in SKIP_FILES:
        return
    for number, line in (markdown_lines(text) if md_lines is None else md_lines):
        if in_cold_region(number, cold_start, inverted_spans):
            continue
        labels = [m.span() for m in LABEL_RE.finditer(line)] + [m.span() for m in REF_LABEL_RE.finditer(line)]
        definition = REFDEF_RE.match(line)
        if definition:
            labels.append((0, definition.end(1)))
        for match in INLINE_CODE_RE.finditer(line):
            found = PATH_SPAN_RE.match(match.group(2).strip())
            if found and not any(a <= match.start() < b for a, b in labels):
                yield number, found.group(1), line


class PathIndex:
    """Answers whether a mention names a path in a set, or a folder above one.
    A mention written from the repository root must match from the first
    segment; an abbreviated one (`web/routes.py` for `src/app/web/routes.py`)
    may match any run of segments."""

    def __init__(self, mentions):
        self.exact = {path for path, is_exact in mentions if is_exact}
        self.exact_roots = {path.split("/", 1)[0] for path in self.exact}
        self.loose = {}
        for path, is_exact in mentions:
            if not is_exact:
                self.loose.setdefault(path.rsplit("/", 1)[-1], set()).add(path)
        self.loose_keys = set(self.loose)

    def matching(self, path):
        """Yield (mention, exact) for every mention that `path` falls under."""
        if not self.exact and not self.loose:
            return
        parts = path.split("/")
        has_exact = bool(self.exact) and parts[0] in self.exact_roots
        has_loose = bool(self.loose) and any(seg in self.loose_keys for seg in parts)
        if not has_exact and not has_loose:
            return
        for end in range(1, len(parts) + 1):
            head = None
            if has_exact:
                head = "/".join(parts[:end])
                if head in self.exact:
                    yield head, True
            if has_loose:
                for mention in self.loose.get(parts[end - 1], ()):
                    head = head or "/".join(parts[:end])
                    if head == mention or head.endswith("/" + mention):
                        yield mention, False


def present_paths(top):
    """Tracked and untracked (not ignored) paths that exist in the working tree.
    A sparse (skip-worktree) file counts as present: it was never removed."""
    deleted = set(git_output(top, "ls-files", "-z", "--deleted").split("\0"))
    present = set()
    for entry in git_output(top, "ls-files", "-z", "-t", "--cached", "--others", "--exclude-standard").split("\0"):
        tag, _, path = entry.partition(" ")
        if path and (tag == "S" or path not in deleted):
            present.add(path)
    return present


def removals(top, index, shallow):
    """Find when the paths the index asks about were removed. Returns
    {(mention, exact): [(old path, commit or None, date, new path or None)]},
    newest first; commit is None for a removal that is not committed yet.

    Only the index and the object store are read: comparing the working tree
    with a commit would run the repository's clean filters, which may do
    anything. A file deleted in the working tree but not staged is therefore
    reported as removed, without a new place even if it was moved."""
    found = {}

    def record(old, commit, date, new):
        for key in set(index.matching(old)):
            found.setdefault(key, []).append((old, commit, date, new))

    staged = iter(git_output(top, "diff", "-z", "--cached", "HEAD", "-M", "--name-status",
                             "--diff-filter=DR", "--").split("\0"))
    for status in staged:
        if status:
            old = next(staged)
            record(old, None, None, next(staged) if status.startswith("R") else None)
    for old in git_output(top, "ls-files", "-z", "--deleted").split("\0"):
        if old:
            record(old, None, None, None)
    # Without rename detection one pass is fast even on long histories; moves are
    # looked up afterwards, only in the commits that removed a mentioned path.
    # Ordinary commits are read one by one. A merge counts only for files it
    # removed itself while resolving (present in every parent); a removal it
    # inherits from a merged branch belongs to that branch's commit. A header
    # starts with "/", which no repository path can.
    for options, lead in ((("--no-merges",), "\n"), (("--merges", "-c"), "")):
        commit = date = None
        expect_lead = False
        log = git_output(top, "log", "HEAD", "-z", *options, "--no-renames", "--diff-filter=D",
                         "--name-only", "--format=/%H %as")
        for token in log.split("\0"):
            if expect_lead and lead and token.startswith(lead):
                token = token[len(lead):]
            elif token.startswith("/"):
                commit, date = token[1:].split(" ")
                expect_lead = True
                continue
            expect_lead = False
            if token:
                record(token, commit, date, None)
    moves, commits = {}, {event[1] for events in found.values() for event in events} - {None}
    for commit in commits:
        try:
            moved = iter(git_output(top, "diff-tree", "-z", "-r", "-M", "--name-status", "--diff-filter=R",
                                    "--root", "-m", "--first-parent", "--no-commit-id", commit).split("\0"))
        except GitError:
            if shallow:
                continue  # its parent lies beyond the shallow boundary: report the removal without a new place
            raise
        for status in moved:
            if status:
                old = next(moved)
                moves[(commit, old)] = next(moved)
    # Newest first, by position in the history rather than by clock, which can
    # tie or run backwards; uncommitted removals come before every commit.
    order = ({sha: at for at, sha in enumerate(git_output(top, "rev-list", "--topo-order", "HEAD").split())}
             if len(commits) > 1 else {})
    for key, events in found.items():
        events.sort(key=lambda event: -1 if event[1] is None else order.get(event[1], len(order)))
        found[key] = [(old, c, d, n or moves.get((c, old))) for old, c, d, n in events]
    return found


def check_removed_paths(report, ssot_dir, mentions, since):
    if not mentions and not since:
        return
    try:
        top = real_path(git_output(ssot_dir, "rev-parse", "--show-toplevel").rstrip("\n"))
    except FileNotFoundError:
        if since:
            report.unchecked.append(f"--since {since}: git is not available")
        else:
            report.add("INFO", None, None, "git is not available, so mentions of removed files were not checked")
        return
    except GitError as error:
        if "not a git repository" in str(error):
            if since:
                report.unchecked.append(f"--since {since}: not in a git work tree")
            else:
                report.add("INFO", None, None, "not in a git work tree, so mentions of removed files were not checked")
        else:
            report.unchecked.append(f"mentions of removed files: git failed ({error})")
        return
    head, stderr = git(top, "rev-parse", "--verify", "--quiet", "HEAD")
    if head == GIT_NO:
        if since:
            report.unchecked.append(f"--since {since}: repository has no commits")
        return
    if head != 0:
        report.unchecked.append(f"mentions of removed files: git failed ({stderr.strip() or head})")
        return
    if since and git(top, "rev-parse", "--verify", "--quiet", f"{since}^{{commit}}")[0] != 0:
        report.unchecked.append(f"--since {since} is not a commit in this repository")
        return
    if not mentions:
        return
    pending = {}
    for doc, num, written, text in mentions:
        if written.startswith(("./", "../")):
            full = os.path.normpath(os.path.join(os.path.dirname(doc), written))
            if os.path.lexists(full) or not inside(full, top):
                continue
            key = (os.path.relpath(real_path(full), top).replace(os.sep, "/"), True)
        elif os.path.lexists(os.path.join(top, written)):
            continue
        else:
            key = (written, False)
        pending.setdefault((doc, key), []).append((num, text))
    if not pending:
        return
    try:
        present = present_paths(top)
        exists = PathIndex({key for _, key in pending})
        listed = {key for path in present for key in exists.matching(path)}
        pending = {item: places for item, places in pending.items() if item[1] not in listed}
        if not pending:
            return
        shallow = git_output(top, "rev-parse", "--is-shallow-repository").strip() == "true"
        events = removals(top, PathIndex({key for _, key in pending}), shallow)
        recent = set(git_output(top, "rev-list", f"{since}..HEAD").split()) if since and events else None
    except (GitError, FileNotFoundError) as error:
        report.unchecked.append(f"mentions of removed files: git failed ({error})")
        return
    found = older = unknown = 0
    for (doc, key), places in sorted(pending.items(), key=lambda item: (item[0][0], item[1][0][0])):
        matches = events.get(key)
        if not matches:
            unknown += 1
            continue
        commits = {c for _, c, _, _ in matches} - {None}
        places = [(n, t) for n, t in places if not any(c.startswith(h) for h in HEX_RE.findall(t) for c in commits)]
        if not places:
            continue
        old, commit, date, new = matches[0]
        if recent is not None and commit is not None and commit not in recent:
            older += 1
            continue
        path = key[0]
        itself = [ev for ev in matches if ev[0] == path or ev[0].endswith("/" + path)]
        when = f"in {commit[:10]} ({date})" if commit else "in uncommitted changes"
        if not itself:
            name = f"`{path}` (a folder)"
        elif len({ev[0] for ev in itself}) > 1:
            name = f"`{path}` (matches {len({ev[0] for ev in itself})} removed files; the newest is `{old}`)"
        else:
            name = f"`{path}`" if old == path else f"`{path}` (`{old}`)"
        what = f"was moved to `{new}` {when}" if (itself and new and new in present) else f"was removed {when}"
        also = f" (also line {', '.join(str(n) for n, _ in places[1:])})" if len(places) > 1 else ""
        report.add("WARN", doc, places[0][0], f"{name} {what}{also}")
        found += 1
    if found:
        report.add("INFO", None, None, f"{found} mention(s) of files that no longer exist: correct the ones that describe current code; a deliberate mention of the past may stay, and naming the removing commit on its line silences this warning")
    if older:
        report.add("INFO", None, None, f"{older} mention(s) of files removed before {since} are not listed; run without --since to see them")
    if unknown and shallow:
        report.add("INFO", None, None, "this clone has shallow history, so files removed before its oldest commit are not recognised")


# --- confirmed invariants ------------------------------------------------------
# Only the user changes a confirmed rule (memory-model section 5), yet mining leads
# have rewritten confirmed rows while tidying the register: narrowed one to "a
# request, not a gate", added an exemption, dropped a duty. So each confirmed row
# of the base commit (HEAD, or --since) is compared with the working tree. A new
# kind, rule, or status, or a removed row, is an error unless the row's Source
# gained a date. This is a source-recording guard, not proof of acceptance;
# human-decision evidence and date meaning belong to memory-model section 3.
# A moved link or a reworded source changes nothing the rule says.

DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def _valid_iso_date(token):
    import datetime
    try:
        datetime.date.fromisoformat(token)
        return True
    except ValueError:
        return False


def check_confirmed(report, readme, text, since, ssot_dir=None, current_shards=()):
    base, directory, entry = since or "HEAD", os.path.dirname(readme), os.path.basename(readme)
    ssot_dir = ssot_dir or directory
    try:
        code, stderr = git(directory, "rev-parse", "--verify", "--quiet", f"{base}:./{entry}")
        if code == GIT_NO:
            return
        if code != 0:
            if "not a git repository" in stderr:
                report.add("INFO", None, None, "not in a git work tree, so changes to confirmed invariants were not checked")
            else:
                report.unchecked.append(f"confirmed invariants: git failed ({stderr.strip() or code})")
            return
        old_readme = git_output(directory, "cat-file", "blob", f"{base}:./{entry}")
        if front_matter(old_readme).get("ssot_format") not in {"3", FORMAT, "5"}:
            return
        old = register_rows(old_readme, readme)
        old_lines = list(markdown_lines(old_readme))
        old_found = register_tables(old_lines, old_readme)
        old_links = non_table_invariants_links(old_lines, old_found[0]) if old_found else []
        if old_links:
            git_top = real_path(git_output(directory, "rev-parse", "--show-toplevel").strip())
            real_readme = os.path.join(real_path(directory), entry)
            seen_old = set()
            for _, target in old_links:
                if not is_local_link(target):
                    continue
                sp, _ = resolve(readme, target)
                if sp == readme or sp in seen_old or not sp.lower().endswith(".md"):
                    continue
                old_abs, _ = resolve(real_readme, target)
                if os.path.commonpath([old_abs, git_top]) != git_top:
                    continue
                rel = os.path.relpath(old_abs, git_top).replace(os.sep, "/")
                if rel.startswith(".."):
                    continue
                sc, se = git(directory, "rev-parse", "--verify", "--quiet", f"{base}:{rel}")
                if sc == GIT_NO:
                    continue
                if sc != 0:
                    report.unchecked.append(f"confirmed invariants shard {rel}: git failed ({se.strip() or sc})")
                    continue
                blob = git_output(directory, "cat-file", "blob", f"{base}:{rel}")
                if is_register_shard(sp, ssot_dir, blob):
                    seen_old.add(sp)
                    _, ot = shard_register_tables(list(markdown_lines(blob)), blob)
                    for ident, row in rows_from_tables(ot, sp).items():
                        old.setdefault(ident, row)
    except OSError:
        report.add("INFO", None, None, "git is not available, so changes to confirmed invariants were not checked")
        return
    except GitError as error:
        report.unchecked.append(f"confirmed invariants: git failed ({error})")
        return
    new, when = register_rows(text, readme), f"since {since}" if since else "since the last commit"
    for sp, st in current_shards:
        _, nt = shard_register_tables(list(markdown_lines(st)), st)
        for ident, row in rows_from_tables(nt, sp).items():
            new.setdefault(ident, row)
    def comparable(cell, col):
        if col == 2:
            return re.sub(r"(?<!`)(`+)(?!`).*?(?<!`)\1(?!`)|\s+", lambda m: m[0] if m[1] else " ", cell)
        return " ".join(cell.strip("`* ").split()).lower()

    approved = []
    for ident, (old_doc, _, cells) in old.items():
        if comparable(cells[4], 4) != "confirmed":
            continue
        if ident not in new:
            report.add("ERROR", old_doc, None, f"confirmed invariant {ident} was removed {when}; restore it (a rule the user retires keeps its row, with status retired)")
            continue
        new_doc, num, now = new[ident]
        changed = [nm for nm, at in (("kind", 1), ("rule", 2), ("status", 4)) if comparable(cells[at], at) != comparable(now[at], at)]
        if not changed:
            continue
        dates = [d for d in DATE_RE.findall(now[5]) if _valid_iso_date(d)]
        before = [d for d in DATE_RE.findall(cells[5]) if _valid_iso_date(d)]
        if any(dates.count(d) > before.count(d) for d in dates):
            approved.append(ident)
            continue
        report.add("ERROR", new_doc, num,
                   f"confirmed invariant {ident} changed its {' and '.join(changed)} {when}. An editorial correction can cite the existing "
                   "decision; changing the protection requires acceptance. First check this task and existing owners for "
                   "human-decision evidence (memory-model section 3). With matching acceptance, keep only the "
                   "authorized change and repair Source with that evidence. Keep unknown approval dates unknown; "
                   "label any actual record/capture date as such, not as approval or replacement order. Without "
                   "acceptance, restore the protection and ask the user; if evidence conflicts, preserve the "
                   "protection and report the conflict. Do not revert only the register to hide disagreement "
                   "with accepted owners or code, or treat a passing check as truth")
    if approved:
        report.add("INFO", readme, None, f"confirmed invariant(s) {', '.join(approved)} changed {when} with a newly dated Source; verify the accepted decision and scope, then show each change to the user")


BLOCK_MARK_RE = re.compile(r"^<!-- SSOT-(CONTEXT|SKILL):(BEGIN|END) -->$", re.M)
F5_ENTRY_RE = re.compile(
    r"(?:through |本空间通过|本空间的入口为)(.+?)(?: \(`ssot_format: 5`\)|（`ssot_format: 5`）|\(`ssot_format: 5`\))"
    r"|^(.+?) defines this space \(`ssot_format: 5`\)", re.M)


def check_gitignored_links(report, ssot_dir, local_links, entry=None, missing_links=None):
    missing_links = missing_links or []
    local_links = local_links or []
    if not local_links and not missing_links:
        return
    try:
        top = os.path.realpath(git_output(ssot_dir, "rev-parse", "--show-toplevel").rstrip("\n"))
    except (FileNotFoundError, GitError):
        for doc, num, target, _ in missing_links:
            report.add("ERROR", doc, num, f"broken link: {target}")
        return
    rel_cache = {}

    def rel_in_top(path, dereference=True):
        ckey = (path, dereference)
        if ckey in rel_cache:
            return rel_cache[ckey]
        res = None
        if dereference:
            target_path = real_path(path)
            if target_path == top or target_path.startswith(top + os.sep):
                rel = os.path.relpath(target_path, top).replace(os.sep, "/")
                res = None if rel in (".", "") or rel.startswith("../") else rel
            rel_cache[ckey] = res
            return res
        # Preserve in-repo symlinks (both intermediate dirs and leaf) while handling
        # symlinked repo roots; stop at the first in-repo symlink so git check-ignore
        # never fails with "beyond a symbolic link".
        cur = os.path.normpath(os.path.abspath(path))
        if cur.startswith(top + os.sep):
            parts = cur[len(top) + 1:].split(os.sep)
        else:
            tail, parts = [], None
            while True:
                if real_path(cur) == top:
                    parts = list(reversed(tail)) if tail else None
                    break
                parent, name = os.path.split(cur)
                if parent == cur:
                    break
                tail.append(name)
                cur = parent
        if parts:
            prefix = top
            res = "/".join(parts)
            for idx, part in enumerate(parts):
                prefix = os.path.join(prefix, part)
                if os.path.islink(prefix):
                    res = "/".join(parts[:idx + 1])
                    break
        rel_cache[ckey] = res
        return res

    local_entries, missing_entries, unique = [], [], {}
    for src, dst, require_rel in ((local_links, local_entries, True), (missing_links, missing_entries, False)):
        for doc, num, target, resolved in src:
            rels = tuple(dict.fromkeys(r for r in (rel_in_top(resolved, False), rel_in_top(resolved, True)) if r))
            if rels or not require_rel:
                dst.append((doc, num, target, rels))
                for rel in rels:
                    unique[rel] = None
    entry_rel = rel_in_top(entry) if GENERAL[0] and entry else None
    if entry_rel:
        unique[entry_rel] = None
    ignored = set()
    if unique:
        try:
            res = subprocess.run(["git", *GIT_SAFE, "-C", top, "check-ignore", "-z", "--stdin"], env=GIT_ENV,
                                 input=("\0".join(unique) + "\0").encode("utf-8", "surrogateescape"),
                                 capture_output=True, check=False)
            if res.returncode == 0:
                ignored = set(filter(None, res.stdout.decode("utf-8", "surrogateescape").split("\0")))
            elif res.returncode != 1:
                report.add("UNCHECKED", entry or ssot_dir, None, f"git check-ignore failed (exit {res.returncode}); ignored-link checks incomplete")
        except OSError as exc:
            report.add("UNCHECKED", entry or ssot_dir, None, f"git check-ignore unavailable ({exc}); ignored-link checks incomplete")
    entry_ignored = bool(entry_rel and entry_rel in ignored)
    for doc, num, target, rels in missing_entries:
        if not entry_ignored and any(rel in ignored for rel in rels):
            report.add("ERROR", doc, num,
                       f"broken link to gitignored path (absent in worktree/clone — track target or use plain path/receipt text): {target}")
        else:
            report.add("ERROR", doc, num, f"broken link: {target}")
    if entry_ignored:
        return
    for doc, num, target, rels in local_entries:
        if any(rel in ignored for rel in rels):
            report.add("WARN", doc, num,
                       f"link targets gitignored path (breaks in worktrees/clones or after cleanup): {target}")


def extract_managed_block(text):
    norm = text.replace("\r\n", "\n")
    m = list(BLOCK_MARK_RE.finditer(norm))
    if len(m) != 2 or m[0].group(2) != "BEGIN" or m[1].group(2) != "END" or m[0].group(1) != m[1].group(1):
        return None, False
    return norm[m[0].start():m[1].end()], m[0].group(1) == "SKILL"


def check_instruction_blocks(report, root):
    tpl_root = os.path.normpath(os.path.join(os.path.dirname(real_path(__file__)), "..", "..", "..", "ssot-bootstrap", "assets", "templates"))
    if not os.path.isdir(tpl_root):
        return
    def is_zh(s):
        probe = s
        if "ssot_format: 5" in probe:
            hit = F5_ENTRY_RE.search(probe)
            ent = (hit.group(1) or hit.group(2)).strip() if hit else ""
            if ent:
                probe = probe.replace(ent, "")
        return any(k in probe for k in ("工作流", "长期 context", "保护规则", "回读", "本空间", "建库"))
    checked = set()
    for name in INSTRUCTION_FILES:
        path = os.path.join(root, name)
        if not os.path.isfile(path):
            continue
        real = real_path(path)
        if real in checked or not inside(real, root):
            continue
        checked.add(real)
        cur, legacy = extract_managed_block(read_text(path))
        if not cur:
            continue
        lang, fmt5 = ("zh" if is_zh(cur) else "en"), ("ssot_format: 5" in cur)
        tpl = "context-adapter.md" if fmt5 else "adapter-thin.md"
        lt, ft = os.path.join(tpl_root, lang, tpl), os.path.join(tpl_root, tpl)
        tpl_path = lt if os.path.isfile(lt) else (ft if os.path.isfile(ft) else None)
        exp, _ = extract_managed_block(read_text(tpl_path)) if tpl_path else (None, False)
        if not exp:
            continue
        if tpl_path == ft and ("zh" if is_zh(exp) else "en") != lang:
            report.add("INFO", path, None, f"managed block is {lang} while installed templates are {'zh' if is_zh(exp) else 'en'}; run the SSOT-CONTEXT installer with --check-block --lang {lang} to verify against {lang} templates")
            continue
        if fmt5:
            hit = F5_ENTRY_RE.search(cur)
            entry = (hit.group(1) or hit.group(2)).strip() if hit else ""
            if not entry or "ENTRY" not in exp:
                continue
            exp = exp.replace("ENTRY", entry)
        if cur != exp:
            report.add("INFO", path, None, f"managed block differs from installed templates{' (legacy SSOT-SKILL markers)' if legacy else ''}; run the SSOT-CONTEXT installer with --check-block / --sync-block")


def check_reviewed_through(report, readme, value, since=None):
    if not value:
        return
    if value.startswith("<"):
        report.add("WARN", readme, 1, "reviewed_through is still the template placeholder")
        return
    if not SHA_RE.match(value):
        report.add("ERROR", readme, 1, f"reviewed_through '{value}' must be a commit SHA; a branch name or HEAD moves on its own")
        return
    directory = os.path.dirname(readme)
    try:
        code, stderr = git(directory, "rev-parse", "--is-inside-work-tree")
        if code != 0:
            report.unchecked.append("reviewed_through: SSOT is not inside a git work tree" if "not a git repository" in stderr else f"reviewed_through: git failed ({stderr.strip() or f'exit code {code}'})")
            return
        exists, _ = git(directory, "rev-parse", "--verify", "--quiet", f"{value}^{{commit}}")
        if exists == GIT_NO:
            report.add("WARN", readme, 1, f"reviewed_through {value} is not a commit in this repository (rebased or squashed?); ask the user where catch-up should start")
            return
        ancestor = git(directory, "merge-base", "--is-ancestor", value, "HEAD")[0] if exists == 0 else exists
        if ancestor == GIT_NO:
            report.add("WARN", readme, 1, f"reviewed_through {value} is not an ancestor of HEAD, so the commits since then are not a simple range; ask the user where catch-up should start")
        elif ancestor != 0:
            report.unchecked.append(f"reviewed_through: git failed with exit code {ancestor}")
        elif not since:
            try:
                if git_output(directory, "rev-parse", "--is-shallow-repository").strip() != "true":
                    behind = int(git_output(directory, "rev-list", "--count", f"{value}..HEAD").strip())
                    if behind >= REVIEWED_LAG_INFO_COMMITS:
                        report.add("INFO", readme, 1, f"reviewed_through {value} is {behind} commits behind HEAD; consider a Doctor catch-up review")
            except (GitError, ValueError):
                pass
    except OSError:
        report.unchecked.append("reviewed_through: git is not available")


# --- main ----------------------------------------------------------------------

def is_git_root(path):
    dot = os.path.join(path, ".git")
    if not os.path.lexists(dot):
        return False
    try:
        return os.path.realpath(git_output(path, "rev-parse", "--show-toplevel").rstrip("\n")) == os.path.realpath(path)
    except FileNotFoundError:
        return os.path.isfile(dot) or os.path.isfile(os.path.join(dot, "HEAD"))
    except GitError:
        return False


def repository_root(directory):
    """Keep worktree identity across links, allowing aliases above the repository."""
    probe = os.path.abspath(directory)
    prefix = os.path.abspath(os.sep)
    seen = is_git_root(prefix)
    for part in probe.split(os.sep):
        if not part:
            continue
        prefix = os.path.join(prefix, part)
        if os.path.islink(prefix) and seen:
            probe = os.path.dirname(prefix)
            break
        seen |= is_git_root(prefix)
    fallback = probe if probe != directory else os.path.dirname(directory)
    try:
        return os.path.realpath(git_output(probe, "rev-parse", "--show-toplevel").rstrip("\n"))
    except GitError as error:
        if "not a git repository" not in str(error):
            raise
    except FileNotFoundError:
        pass
    return os.path.realpath(fallback)


def load_submodule_roots(root):
    gm = os.path.join(root, ".gitmodules")
    roots = set()
    if not os.path.isfile(gm):
        return roots
    for line in read_text(gm).splitlines():
        match = re.match(r"^\s*path\s*=\s*(.+?)\s*$", line)
        if match:
            sub = os.path.normpath(os.path.join(root, match.group(1).strip("'\"")))
            if inside(sub, root) and real_path(sub) != real_path(root):
                roots.add(real_path(sub))
    return roots


def nested_git_root(path):
    if not inside(path, REPO_ROOT[0]):
        return None
    # A nested worktree/submodule owns different facts even inside this root.
    directory = real_path(path)
    if not os.path.isdir(directory):
        directory = os.path.dirname(directory)
    root = real_path(REPO_ROOT[0])
    while directory != root:
        if directory in SUBMODULE_ROOTS or os.path.lexists(os.path.join(directory, ".git")):
            return directory
        parent = os.path.dirname(directory)
        if parent == directory:
            break
        directory = parent
    return None


def repository_local(path):
    return inside(path, REPO_ROOT[0]) and nested_git_root(path) is None


def checked_documents(ssot_dir, readme, report, shard_paths=()):
    """Follow intermediate links only inside an explicit selection, plus 1-hop links from entry and shards."""
    selection = report.documents
    documents = ({readme} if GENERAL[0] or selection is not None
                 else set(markdown_files(ssot_dir, report)))
    pending = [readme] if os.path.isfile(readme) and repository_local(readme) else []
    if selection is None:
        for path in sorted(shard_paths):
            if path != readme and os.path.isfile(path) and repository_local(path):
                documents.add(path)
                pending.append(path)
    while pending and documents != selection:
        doc = pending.pop()
        for _, target in link_targets(read_text(doc)):
            if not is_local_link(target):
                continue
            path, _ = resolve(doc, target)
            if path in documents or (selection is not None and path not in selection):
                continue
            if path.lower().endswith(".md") and repository_local(path) and os.path.isfile(path):
                documents.add(path)
                if selection is not None:
                    pending.append(path)
    if selection is not None:
        for path in sorted(selection - documents):
            report.add("ERROR", path, None, "selected owner must be an existing local Markdown file reachable through the selection")
        report.documents = documents
    yield from sorted(documents)


def markdown_files(ssot_dir, report):
    def unreadable(error):
        report.unchecked.append(f"{error.filename}: {error.strerror}")

    for directory, subdirs, files in os.walk(ssot_dir, onerror=unreadable):
        subdirs[:] = sorted(d for d in subdirs if d != ".git")
        for name in sorted(files):
            if name.lower().endswith(".md"):
                yield os.path.join(directory, name)


def ledgers(directory):
    for name in V2_LEDGERS:
        path = os.path.join(directory, name)
        if os.path.exists(path):
            yield path


def main(argv):
    if argv[1:] in (["-h"], ["--help"]):
        print((__doc__ or "").strip())
        return 0
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument("entry", nargs="?", default="SSOT")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--since")
    mode.add_argument("--owners", nargs="*")
    parser.add_argument("--space-root")
    args = parser.parse_args(argv[1:])
    since = args.since
    if since == "" or (since and since.startswith("-")):
        parser.error("--since requires a commit")
    selected = os.path.abspath(args.entry)
    named_entry, scoped = os.path.isfile(selected), args.owners is not None
    if scoped and not named_entry:
        parser.error("--owners requires an explicit entry file")
    space_root = None
    if args.space_root is not None:
        if not scoped:
            parser.error("--space-root requires --owners")
        space_root = os.path.realpath(args.space_root)
        if not args.space_root or not os.path.isdir(space_root) or not inside(selected, space_root):
            parser.error("--space-root must be a directory containing the entry")
    ssot_dir = os.path.dirname(selected) if named_entry else selected
    if not os.path.isdir(ssot_dir):
        print(f"ERROR no SSOT directory at {ssot_dir}")
        return 2
    documents = None
    if scoped:
        documents = {os.path.abspath(os.path.join(ssot_dir, name)) for name in args.owners} | {selected}
        entry_dir = os.path.realpath(ssot_dir)
        if os.path.realpath(selected) != os.path.join(entry_dir, os.path.basename(selected)):
            parser.error("select the entry file by its actual path")
    _anchor_cache.clear()
    _real_cache.clear()
    UNDECODABLE.clear()
    SUBMODULE_ROOTS.clear()
    report = Report(ssot_dir, documents)
    REPO_ROOT[0] = space_root or repository_root(ssot_dir)
    SUBMODULE_ROOTS.update(load_submodule_roots(REPO_ROOT[0]))
    readme = selected if named_entry else os.path.join(ssot_dir, "README.md")
    GENERAL[0] = False
    legacy, shards, cold_shards, text, meta = False, [], set(), None, None
    if named_entry and os.path.isfile(readme) and inside(readme, space_root or real_path(ssot_dir)):
        text = read_text(readme)
        meta = front_matter(text)
        if meta.get("ssot_format") == "5":
            GENERAL[0] = True
            REPO_ROOT[0] = space_root or real_path(ssot_dir)
    if not os.path.isfile(readme):
        report.add("ERROR", readme, None, "missing SSOT/README.md (the entry every task starts from)")
    elif not repository_local(readme):
        report.add("ERROR", readme, None, "README must belong to the same repository")
        if named_entry:
            return report.finish(readme)
    else:
        if text is None:
            text = read_text(readme)
            meta = front_matter(text)
            GENERAL[0] = meta.get("ssot_format") == "5"
        if space_root and not GENERAL[0]:
            parser.error("--space-root requires a format-5 entry")
        if GENERAL[0]:
            REPO_ROOT[0] = space_root or real_path(ssot_dir)
            if not scoped:
                report.add("INFO", readme, None, "format 5: selected entry and direct local owners; external routes are not read")
        selected_repo_readme = scoped and meta.get("ssot_format") == FORMAT and os.path.basename(readme) == "README.md"
        if named_entry and not (GENERAL[0] or selected_repo_readme):
            report.add("ERROR", readme, 1, "a named entry file requires ssot_format: 5 or a format-4 README with --owners (for format 4, pass the SSOT directory instead)")
            return report.finish(readme)
        if scoped:
            names = []
            for path in sorted(documents):
                relative = os.path.relpath(path, ssot_dir)
                if not inside(path, REPO_ROOT[0]) or real_path(path) != os.path.normpath(os.path.join(entry_dir, relative)):
                    parser.error(f"select a file inside the repository or space by its actual path: {relative}")
                names.append(relative)
            report.add("INFO", readme, None, f"selected files: {', '.join(names)}. Other link targets and Git history excluded")
        if meta.get("ssot_format") in {FORMAT, "5"}:
            if not meta.get("language"):
                report.add("ERROR", readme, 1, "front matter needs `language:` (for example en or zh-CN)")
            shards, cold_shards = check_invariants(report, readme, text, ssot_dir)
            if not scoped:
                check_confirmed(report, readme, text, since, ssot_dir, shards)
                check_reviewed_through(report, readme, meta.get("reviewed_through"), since)
            if not GENERAL[0] and not scoped:
                for path in ledgers(ssot_dir):
                    report.add("WARN", path, None, "v2 ledger left after migration; extract anything still valid, then remove it")
        elif meta.get("ssot_format") in {"2", "3"} or ("ssot_format" not in meta and any(ledgers(ssot_dir))):
            legacy = True
            report.add("INFO", readme, None, f"v{meta.get('ssot_format', '2')} layout; use ssot-bootstrap to migrate to format 4")
            report.unchecked.append("legacy SSOT requires migration; format 4 ownership was not checked")
        else:
            report.add("ERROR", readme, 1, "front matter needs supported `ssot_format: 4` or `ssot_format: 5`; for an unknown format, identify/upgrade its writer without downgrading the data")

    checkpoint = os.path.join(ssot_dir, "BOOTSTRAP.md")
    if not GENERAL[0] and not scoped and os.path.isfile(checkpoint):
        report.add("INFO", checkpoint, None, "bootstrap is unfinished; continue it with ssot-bootstrap")

    shard_paths = {path for path, _ in shards}
    mentions, local_links, missing_links = [], ([] if not scoped else None), ([] if not scoped else None)
    for doc in checked_documents(ssot_dir, readme, report, shard_paths):
        if not repository_local(doc):
            report.add("ERROR", doc, None, "document leaves the repository (possibly through a symlink)")
            continue
        text = read_text(doc)
        md_lines = list(markdown_lines(text))
        if doc != readme and doc not in shard_paths and not scoped and not legacy and is_register_shard(doc, ssot_dir, text):
            report.add("ERROR", doc, None, f"unlinked invariants shard is not linked under ## Invariants in {os.path.basename(readme)}")
        cold_info = check_document_bloat(report, doc, readme, ssot_dir, text, shard_paths, cold_shards, md_lines) if not legacy else None
        if cold_info != "cold":
            c_start, c_inv = cold_info if isinstance(cold_info, tuple) else (None, ())
            mentions.extend((doc, number, path, line) for number, path, line in path_mentions(ssot_dir, doc, text, c_start, c_inv, md_lines))
        for number, target in link_targets(text, md_lines):
            check_link(report, doc, number, target, local_links, missing_links)
        wrapped = list(hard_wrapped_paragraphs(text, md_lines))
        if wrapped and not legacy:
            lines = ", ".join(str(n) for n in wrapped[:5]) + (", ..." if len(wrapped) > 5 else "")
            report.add("WARN", doc, wrapped[0], f"{len(wrapped)} paragraph(s) are broken across short lines (lines {lines}); write each paragraph or list item as one line and let the editor wrap it")
    if not scoped:
        check_gitignored_links(report, ssot_dir, local_links, readme, missing_links)
        check_removed_paths(report, ssot_dir, mentions, since)
        if not legacy:
            check_instruction_blocks(report, REPO_ROOT[0])
    for path in sorted(UNDECODABLE):
        report.add("WARN", path, None, "not valid UTF-8; undecodable bytes were replaced while checking")
    surface = readme if GENERAL[0] else ssot_dir
    return report.finish(surface + " (selected files only)" if scoped else surface)


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:  # a checker bug must never look like a pass or a content error
        traceback.print_exc()
        print("ssot-check: INCOMPLETE - the checker crashed, so nothing was checked (TOOL FAILURE)")
        sys.exit(3)
