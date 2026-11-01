#!/usr/bin/env python3
"""Mechanical checks for a repository SSOT/ directory (SSOT Skill v3).

Usage: ssot-check.py [SSOT_DIR] [--since COMMIT]      (default: ./SSOT)

--since COMMIT lists only mentions of files removed after COMMIT or in
uncommitted changes, and counts the older ones in one line. Closeout uses it
to see what its own batch removed.

Checks only what a program can decide: the entry file and its format marker,
local links and heading anchors, the invariants register shape, the
reviewed_through commit, size warnings, and file paths in inline code that git
history says were removed or moved (outside decisions/ and research/). It never proves that a document is
true, complete, or readable; that is the job of the agent review in
ssot-doctor.

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

import os
import re
import subprocess
import sys
import traceback
from urllib.parse import unquote

FORMAT = "3"
# Reading budgets are counted in characters, not bytes, so documents in
# languages with multi-byte scripts (Chinese, Japanese) are not penalised.
README_WARN_CHARS = 8000
DOC_WARN_CHARS = 16000
INVARIANT_STATUSES = {"confirmed", "candidate", "retired"}
INVARIANT_HEADINGS = ("invariants", "不变量")
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
INVARIANT_ID_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+$")  # INV-01, CORE-RULE-2
SEPARATOR_CELL_RE = re.compile(r"^:?-{3,}:?$")
LINE_ANCHOR_RE = re.compile(r"^L(\d+)(?:-L?\d+)?$")
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")


class Report:
    def __init__(self, root):
        self.root = root
        self.lines = []
        self.errors = 0
        self.warnings = 0
        self.unchecked = []  # parts the checker could not examine; any of them makes the run exit 3

    def add(self, level, path, line, message):
        where = os.path.relpath(path, self.root) if path else "."
        if line:
            where += f":{line}"
        self.lines.append(f"{level:<5} {where}  {message}")
        if level == "ERROR":
            self.errors += 1
        elif level == "WARN":
            self.warnings += 1


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

def markdown_lines(text):
    """Yield (line_number, text) for every line a reader sees as Markdown:
    front matter, fenced code, and HTML comments removed (a comment may end
    mid-line, and the rest of that line still counts). Fence lines and lines
    inside fences are skipped entirely."""
    lines = text.splitlines()
    start = 0
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                start = index + 1
                break
    fence = None
    in_comment = False
    for index in range(start, len(lines)):
        line = lines[index]
        if fence is None and not in_comment:
            match = FENCE_RE.match(line)
            if match:
                fence = match.group(1)
                continue
        elif fence is not None:
            match = FENCE_RE.match(line)
            if match and match.group(1)[0] == fence[0] and len(match.group(1)) >= len(fence) \
                    and not line.strip()[len(match.group(1)):].strip():
                fence = None
            continue
        visible, in_comment = strip_comments(line, in_comment)
        yield index + 1, visible


def strip_comments(line, in_comment):
    code_spans = [match.span() for match in INLINE_CODE_RE.finditer(line)]

    def opener(start):
        begin = line.find("<!--", start)
        while begin != -1 and any(a <= begin < b for a, b in code_spans):
            begin = line.find("<!--", begin + 4)
        return begin

    out = []
    position = 0
    while position <= len(line):
        if in_comment:
            end = line.find("-->", position)
            if end == -1:
                return "".join(out), True
            position = end + 3
            in_comment = False
        else:
            begin = opener(position)
            if begin == -1:
                out.append(line[position:])
                break
            out.append(line[position:begin])
            position = begin + 4
            in_comment = True
    return "".join(out), in_comment


def blank_inline_code(line):
    return INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


# --- headings and anchors --------------------------------------------------

def headings(text):
    """Yield (line_number, level, heading_text) for ATX and Setext headings."""
    previous = None  # (number, text) of the last paragraph line
    for number, line in markdown_lines(text):
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


def slug(text):
    """GitHub (github-slugger) anchor: lowercase, drop everything except
    letters, digits, underscore, hyphen and space, then each space -> '-'."""
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


_anchor_cache = {}
REPO_ROOT = [os.sep]  # set in main(): the folder that holds SSOT/


def anchors(path):
    if path not in _anchor_cache:
        text = read_text(path)
        seen = {}
        found = set()
        for _, _, raw in headings(text):
            base = slug(heading_text(raw))
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f"{base}-{count}")
        for _, line in markdown_lines(text):
            found.update(re.findall(r"<a\s+(?:name|id)=\"([^\"]+)\"", line))
        _anchor_cache[path] = found
    return _anchor_cache[path]


# --- links -----------------------------------------------------------------

def parse_destination(line, start):
    """Parse an inline link destination starting right after '](' and return
    it, or None when the text is not a well-formed link."""
    position = start
    while position < len(line) and line[position] in " \t":
        position += 1
    if position < len(line) and line[position] == "<":
        end = line.find(">", position)
        if end == -1:
            return None
        destination, position = line[position + 1:end], end + 1
    else:
        depth = 0
        begin = position
        while position < len(line):
            char = line[position]
            if char == "\\" and position + 1 < len(line):
                position += 2
                continue
            if char in " \t":
                break
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            position += 1
        destination = line[begin:position]
    while position < len(line) and line[position] in " \t":
        position += 1
    if position < len(line) and line[position] in "\"'(":
        closer = ")" if line[position] == "(" else line[position]
        end = line.find(closer, position + 1)
        if end == -1:
            return None
        position = end + 1
        while position < len(line) and line[position] in " \t":
            position += 1
    if position < len(line) and line[position] == ")":
        return destination
    return None


def links_in(line):
    for match in LABEL_RE.finditer(line):
        destination = parse_destination(line, match.end())
        if destination is not None:
            yield destination


def link_targets(text):
    for number, line in markdown_lines(text):
        line = blank_inline_code(line)
        for destination in links_in(line):
            yield number, destination
        ref = REFDEF_RE.match(line)
        if ref:
            yield number, ref.group(2).strip("<>")


def resolve(doc, target):
    """Return (path or None, fragment) for a local link target."""
    target = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", target)  # CommonMark backslash escapes
    path_part, _, fragment = target.partition("#")
    path_part = unquote(path_part.partition("?")[0])
    if not path_part:
        return doc, fragment
    return os.path.normpath(os.path.join(os.path.dirname(doc), path_part)), fragment


def check_link(report, doc, number, target):
    target = target.strip()
    if not target or SCHEME_RE.match(target):
        return  # external URLs and mailto: are outside this checker's scope
    if unquote(target).startswith("/"):
        report.add("WARN", doc, number, f"absolute link path is machine-specific: {target}")
        return
    resolved, fragment = resolve(doc, target)
    if not inside(resolved, REPO_ROOT[0]):
        report.add("WARN", doc, number,
                   f"link leaves the repository and only works where the same folders sit beside it: {target}")
        return
    if not os.path.exists(resolved):
        report.add("ERROR", doc, number, f"broken link: {target}")
        return
    if not fragment or not os.path.isfile(resolved):
        return
    line_anchor = LINE_ANCHOR_RE.match(fragment)
    if line_anchor:
        with open(resolved, encoding="utf-8", errors="replace") as handle:
            length = sum(1 for _ in handle)
        if int(line_anchor.group(1)) > length:
            report.add("ERROR", doc, number, f"line anchor past end of file: {target}")
        else:
            report.add("WARN", doc, number, f"line anchors drift when the file changes; link a heading: {target}")
    elif resolved.endswith(".md") and unquote(fragment) not in anchors(resolved):
        report.add("ERROR", doc, number, f"missing heading anchor: {target}")


# --- hard-wrapped paragraphs --------------------------------------------------
# A paragraph written as several short lines reads as ragged text in an editor,
# and in Chinese or Japanese a line break inside a sentence can render as a
# stray space. Each paragraph and list item should be one line.

WRAP_MIN_RUN = 3        # consecutive lines of one paragraph
WRAP_MAX_WIDTH = 100    # every line of the run at most this wide (in characters)
BLOCK_START_RE = re.compile(r"^\s{0,3}(#|>|\||[-*+]\s|\d+[.)]\s|<|\[[^\]]+\]:|```|~~~)")


def hard_wrapped_paragraphs(text):
    """Yield the first line number of each paragraph or list item that runs
    over WRAP_MIN_RUN or more short source lines."""
    run_start, run_length, in_item = None, 0, False
    for number, line in markdown_lines(text):
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


# --- the invariants register -------------------------------------------------

def table_cells(line):
    """Split a pipe-table row into cells; outer pipes are optional in GFM."""
    stripped = line.strip()
    if not re.search(r"(?<!\\)\|", blank_inline_code(stripped)):
        return None
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|") and not stripped.endswith("\\|"):
        stripped = stripped[:-1]
    return [cell.strip() for cell in re.split(r"(?<!\\)\|", stripped)]


def inside(path, root):
    real_path, real_root = os.path.realpath(path), os.path.realpath(root)
    return os.path.commonpath([real_path, real_root]) == real_root


def check_invariants(report, readme, text, ssot_dir):
    lines = list(markdown_lines(text))
    section = None
    for number, level, raw in headings(text):
        if section is None:
            if re.sub(r"^[\d.)\s]+", "", raw).lower().startswith(INVARIANT_HEADINGS):
                section = [number, level, None]
        elif level <= section[1]:
            section[2] = number
            break
    if section is None:
        report.add("WARN", readme, None, "no Invariants section; add one (it may say there are none yet)")
        return
    body = [(n, line) for n, line in lines if n > section[0] and (section[2] is None or n < section[2])]
    refdefs = {m.group(1).lower(): m.group(2).strip("<>")
               for _, line in lines for m in [REFDEF_RE.match(line)] if m}

    tables, current = [], []
    for number, line in body:
        cells = table_cells(line)
        if cells is None:
            if current:
                tables.append(current)
            current = []
        else:
            current.append((number, cells))
    if current:
        tables.append(current)
    if not tables:
        for number, line in body:
            if re.search(r"\b[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+\b", blank_inline_code(line)):
                report.add("ERROR", readme, number,
                           f"invariants must be written as a table ({INVARIANT_COLUMNS}) so they can be checked")
                break
    seen = {}
    for table in tables:
        header_number, header = table[0]
        if len(header) != 6:
            report.add("ERROR", readme, header_number, f"invariants table needs 6 columns: {INVARIANT_COLUMNS}")
            continue
        if any(cell.strip("`* ").lower() not in names for cell, names in zip(header, INVARIANT_HEADERS)):
            report.add("ERROR", readme, header_number,
                       f"invariants table columns must be, in order: {INVARIANT_COLUMNS} "
                       "(or 类型 / 规则 / 解释位置 / 状态 / 来源)")
            continue
        if len(table) < 2 or len(table[1][1]) != len(header) \
                or not all(SEPARATOR_CELL_RE.match(cell) for cell in table[1][1]):
            report.add("ERROR", readme, header_number,
                       "invariants table needs a separator row (|---|---|...) under its header")
            continue
        for number, cells in table[2:]:
            if len(cells) != 6:
                report.add("ERROR", readme, number, "invariants row does not have 6 cells")
                continue
            ident, kind, rule, explained, status, source = cells
            ident, status = ident.strip("`* "), status.strip("`* ")
            if not INVARIANT_ID_RE.match(ident):
                report.add("ERROR", readme, number, f"invariant ID '{ident}' should look like INV-01")
            elif ident in seen:
                report.add("ERROR", readme, number, f"duplicate invariant ID {ident} (first on line {seen[ident]})")
            else:
                seen[ident] = number
            if not kind:
                report.add("ERROR", readme, number,
                           f"invariant {ident} needs a kind (product promise, architecture invariant, or process rule)")
            if not rule:
                report.add("ERROR", readme, number, f"invariant {ident} has an empty rule")
            targets = list(links_in(blank_inline_code(explained)))
            for label, alt in re.findall(r"\[([^\]]+)\]\[([^\]]*)\]", explained):
                target = refdefs.get((alt or label).lower())
                if target:
                    targets.append(target)
            if not targets:
                report.add("ERROR", readme, number, f"invariant {ident} needs a link to where it is explained")
            for target in targets:
                path = None if SCHEME_RE.match(target) else resolve(readme, target)[0]
                if path is None or not inside(path, ssot_dir):
                    report.add("ERROR", readme, number,
                               f"invariant {ident} is explained outside SSOT/ ({target}); "
                               "its explanation must live inside SSOT/")
            if status.lower() not in INVARIANT_STATUSES:
                report.add("ERROR", readme, number,
                           f"invariant {ident} status '{status}' must be confirmed, candidate, or retired")
            if not source:
                report.add("ERROR", readme, number,
                           f"invariant {ident} needs a source (user directive, decision, or date)")


# --- git -----------------------------------------------------------------------
# The checker never writes. These settings stop git from writing or running
# anything on its behalf: no optional index refresh, no filesystem-monitor hook,
# and no fetching of missing objects in a partial clone.
GIT_ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_NO_LAZY_FETCH="1")
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


def path_mentions(ssot_dir, doc, text):
    """Yield (line, path, line_text) for inline code spans that hold only a path.
    A link's own label is skipped: the link target is what the link check tests."""
    relative = os.path.relpath(doc, ssot_dir).split(os.sep)
    if HISTORY_DIRS & {part.lower() for part in relative[:-1]} or ".bootstrap" in relative \
            or relative[-1] in SKIP_FILES:
        return
    for number, line in markdown_lines(text):
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
        self.loose = {}
        for path, is_exact in mentions:
            if not is_exact:
                self.loose.setdefault(path.rsplit("/", 1)[-1], set()).add(path)

    def matching(self, path):
        """Yield (mention, exact) for every mention that `path` falls under."""
        parts = path.split("/")
        for end in range(1, len(parts) + 1):
            head = None
            if self.exact:
                head = "/".join(parts[:end])
                if head in self.exact:
                    yield head, True
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
    moves = {}
    for commit in {event[1] for events in found.values() for event in events} - {None}:
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
    order = {sha: at for at, sha in enumerate(git_output(top, "rev-list", "--topo-order", "HEAD").split())}
    for key, events in found.items():
        events.sort(key=lambda event: -1 if event[1] is None else order.get(event[1], len(order)))
        found[key] = [(old, c, d, n or moves.get((c, old))) for old, c, d, n in events]
    return found


def check_removed_paths(report, ssot_dir, mentions, since):
    if not mentions and not since:
        return
    try:
        top = git_output(ssot_dir, "rev-parse", "--show-toplevel").rstrip("\n")
    except FileNotFoundError:
        report.add("INFO", None, None, "git is not available, so mentions of removed files were not checked")
        return
    except GitError as error:
        if "not a git repository" in str(error):
            report.add("INFO", None, None, "not in a git work tree, so mentions of removed files were not checked")
        else:
            report.unchecked.append(f"mentions of removed files: git failed ({error})")
        return
    head, stderr = git(top, "rev-parse", "--verify", "--quiet", "HEAD")
    if head == GIT_NO:
        return  # no commits yet, so nothing has been removed
    if head != 0:
        report.unchecked.append(f"mentions of removed files: git failed ({stderr.strip() or head})")
        return
    if since and git(top, "rev-parse", "--verify", "--quiet", f"{since}^{{commit}}")[0] != 0:
        report.unchecked.append(f"--since {since} is not a commit in this repository")
        return
    if not mentions:
        return
    pending = {}  # (doc, (path, exact)) -> [(line, text)]
    for doc, number, written, text in mentions:
        if written.startswith(("./", "../")):
            full = os.path.normpath(os.path.join(os.path.dirname(doc), written))
            if os.path.lexists(full) or not inside(full, top):
                continue
            key = (os.path.relpath(full, top).replace(os.sep, "/"), True)
        elif os.path.lexists(os.path.join(top, written)):
            continue
        else:
            key = (written, False)
        pending.setdefault((doc, key), []).append((number, text))
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
        recent = set(git_output(top, "rev-list", f"{since}..HEAD").split()) if since else None
    except (GitError, FileNotFoundError) as error:
        report.unchecked.append(f"mentions of removed files: git failed ({error})")
        return
    found = older = unknown = 0
    for (doc, key), places in sorted(pending.items(), key=lambda item: (item[0][0], item[1][0][0])):
        matches = events.get(key)
        if not matches:
            unknown += 1  # never in the history we have: a runtime path, a planned file, or an abbreviation
            continue
        commits = {commit for _, commit, _, _ in matches} - {None}
        places = [(n, t) for n, t in places if not any(c.startswith(h) for h in HEX_RE.findall(t) for c in commits)]
        if not places:
            continue  # the line names the commit that removed the file: a deliberate mention of the past
        old, commit, date, new = matches[0]
        if recent is not None and commit is not None and commit not in recent:
            older += 1
            continue
        path = key[0]
        itself = [event for event in matches if event[0] == path or event[0].endswith("/" + path)]
        when = f"in {commit[:10]} ({date})" if commit else "in uncommitted changes"
        if not itself:
            name = f"`{path}` (a folder)"
        elif len({event[0] for event in itself}) > 1:
            name = f"`{path}` (matches {len({event[0] for event in itself})} removed files; the newest is `{old}`)"
        else:
            name = f"`{path}`" if old == path else f"`{path}` (`{old}`)"
        moved = itself and new and new in present
        what = f"was moved to `{new}` {when}" if moved else f"was removed {when}"
        also = f" (also line {', '.join(str(n) for n, _ in places[1:])})" if len(places) > 1 else ""
        report.add("WARN", doc, places[0][0], f"{name} {what}{also}")
        found += 1
    if found:
        report.add("INFO", None, None,
                   f"{found} mention(s) of files that no longer exist: correct the ones that describe current "
                   "code; a deliberate mention of the past may stay, and naming the removing commit on its line "
                   "silences this warning")
    if older:
        report.add("INFO", None, None, f"{older} mention(s) of files removed before {since} are not listed; "
                                       "run without --since to see them")
    if unknown and shallow:
        report.add("INFO", None, None, "this clone has shallow history, so files removed before its oldest "
                                       "commit are not recognised")


# --- reviewed_through ----------------------------------------------------------

def check_reviewed_through(report, readme, value):
    if not value:
        return
    if value.startswith("<"):
        report.add("WARN", readme, 1, "reviewed_through is still the template placeholder")
        return
    if not SHA_RE.match(value):
        report.add("ERROR", readme, 1,
                   f"reviewed_through '{value}' must be a commit SHA; a branch name or HEAD moves on its own")
        return
    directory = os.path.dirname(readme)
    try:
        code, stderr = git(directory, "rev-parse", "--is-inside-work-tree")
        if code != 0:
            if "not a git repository" in stderr:
                report.unchecked.append("reviewed_through: SSOT is not inside a git work tree")
            else:
                report.unchecked.append(f"reviewed_through: git failed ({stderr.strip() or f'exit code {code}'})")
            return
        exists, _ = git(directory, "rev-parse", "--verify", "--quiet", f"{value}^{{commit}}")
        if exists == GIT_NO:
            report.add("WARN", readme, 1,
                       f"reviewed_through {value} is not a commit in this repository (rebased or squashed?); "
                       "ask the user where catch-up should start")
            return
        ancestor = git(directory, "merge-base", "--is-ancestor", value, "HEAD")[0] if exists == 0 else exists
        if ancestor == GIT_NO:
            report.add("WARN", readme, 1,
                       f"reviewed_through {value} is not an ancestor of HEAD, so the commits since then "
                       "are not a simple range; ask the user where catch-up should start")
        elif ancestor != 0:
            report.unchecked.append(f"reviewed_through: git failed with exit code {ancestor}")
    except OSError:
        report.unchecked.append("reviewed_through: git is not available")


# --- main ----------------------------------------------------------------------

def markdown_files(ssot_dir, report):
    def unreadable(error):
        report.unchecked.append(f"{error.filename}: {error.strerror}")

    for directory, subdirs, files in os.walk(ssot_dir, onerror=unreadable):
        subdirs[:] = sorted(d for d in subdirs if d != ".git")
        for name in sorted(files):
            if name.endswith(".md"):
                yield os.path.join(directory, name)


def main(argv):
    args, since = list(argv[1:]), None
    if args in (["-h"], ["--help"]):
        print((__doc__ or "").strip())
        return 0
    if "--since" in args:
        at = args.index("--since")
        since = args[at + 1] if at + 1 < len(args) else ""
        del args[at:at + 2]
    if len(args) > 1 or since == "" or (since and since.startswith("-")) or any(a.startswith("-") for a in args):
        print((__doc__ or "").strip())
        return 2
    ssot_dir = os.path.abspath(args[0] if args else "SSOT")
    if not os.path.isdir(ssot_dir):
        print(f"ERROR no SSOT directory at {ssot_dir}")
        return 2
    report = Report(ssot_dir)
    REPO_ROOT[0] = os.path.dirname(ssot_dir)
    readme = os.path.join(ssot_dir, "README.md")

    is_v2 = any(os.path.exists(os.path.join(ssot_dir, name)) for name in V2_LEDGERS)
    legacy = False
    if not os.path.isfile(readme):
        report.add("ERROR", readme, None, "missing SSOT/README.md (the entry every task starts from)")
    else:
        text = read_text(readme)
        meta = front_matter(text)
        if meta.get("ssot_format") == FORMAT:
            if not meta.get("language"):
                report.add("ERROR", readme, 1, "front matter needs `language:` (for example en or zh-CN)")
            check_invariants(report, readme, text, ssot_dir)
            check_reviewed_through(report, readme, meta.get("reviewed_through"))
            for name in V2_LEDGERS:
                if os.path.exists(os.path.join(ssot_dir, name)):
                    report.add("WARN", os.path.join(ssot_dir, name), None,
                               "v2 ledger left after migration; extract anything still valid, then remove it")
        elif is_v2:
            legacy = True
            report.add("INFO", readme, None,
                       "v2 layout (no `ssot_format: 3`); readable as-is, see ssot-bootstrap for migration; "
                       "the invariants register is not checked until then")
        else:
            report.add("ERROR", readme, 1, "front matter needs `ssot_format: 3`")

    if os.path.isfile(os.path.join(ssot_dir, "BOOTSTRAP.md")):
        report.add("INFO", os.path.join(ssot_dir, "BOOTSTRAP.md"), None,
                   "bootstrap is unfinished; continue it with ssot-bootstrap")

    mentions = []
    for doc in markdown_files(ssot_dir, report):
        text = read_text(doc)
        mentions.extend((doc, number, path, line) for number, path, line in path_mentions(ssot_dir, doc, text))
        limit = README_WARN_CHARS if doc == readme else DOC_WARN_CHARS
        measured = text
        if doc == readme:  # the invariants register is meant to grow; budget the prose around it
            measured = "\n".join(line for line in text.splitlines()
                                  if not re.match(r"^\s*\|\s*`?[A-Z][A-Z0-9]*(?:-[A-Z][A-Z0-9]*)*-\d+", line))
        if len(measured) > limit and "/.bootstrap/" not in doc and not legacy:
            report.add("WARN", doc, None,
                       f"{len(measured)} characters is past the {limit}-character reading budget"
                       f"{' (invariant rows not counted)' if doc == readme else ''}; "
                       "split it by topic or move detail out")
        for number, target in link_targets(text):
            check_link(report, doc, number, target)
        wrapped = list(hard_wrapped_paragraphs(text))
        if wrapped and not legacy:
            lines = ", ".join(str(n) for n in wrapped[:5]) + (", ..." if len(wrapped) > 5 else "")
            report.add("WARN", doc, wrapped[0],
                       f"{len(wrapped)} paragraph(s) are broken across short lines (lines {lines}); "
                       "write each paragraph or list item as one line and let the editor wrap it")
    check_removed_paths(report, ssot_dir, mentions, since)
    for path in sorted(UNDECODABLE):
        report.add("WARN", path, None, "not valid UTF-8; undecodable bytes were replaced while checking")

    for line in report.lines:
        print(line)
    for item in report.unchecked:
        print(f"UNCHECKED {item}")
    verdict = "INCOMPLETE" if report.unchecked else "FAIL" if report.errors else "PASS"
    counts = f"{report.errors} error(s), {report.warnings} warning(s)"
    if report.unchecked:
        counts += f", {len(report.unchecked)} part(s) not checked"
    print(f"ssot-check: {verdict} - {counts} in {ssot_dir}")
    return {"INCOMPLETE": 3, "FAIL": 1, "PASS": 0}[verdict]


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except Exception:  # a checker bug must never look like a pass or a content error
        traceback.print_exc()
        print("ssot-check: INCOMPLETE - the checker crashed, so nothing was checked (TOOL FAILURE)")
        sys.exit(3)
