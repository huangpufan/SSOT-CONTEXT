#!/usr/bin/env python3
"""Deterministic working-tree reverse-link lookup for explicitly selected Markdown sources.

Lives outside skills/ (zero protocol words, zero model tokens at idle).
Does not crawl directories, stat/read target files, invoke Git hooks, or call models.

Supported Markdown subset:
- YAML frontmatter delimited by `---` (UTF-8 BOM and CRLF supported)
- ATX and Setext headings (ignoring fenced blocks, indented code blocks, blockquoted fences, and HTML comments)
- Inline links `[text](dest "title")`, linked images `[![alt](img)](dest)`, nested brackets,
  angle-bracket destinations, balanced parentheses, backslash escapes, and single/multi-line code spans
- Reference link definitions `[id]: dest` (labeled `reference_definition`; footnotes `[^id]:` excluded)

Exit codes:
- 0: Complete scan of all selected sources (including zero matches)
- 2: Usage or invalid-argument error (invalid `--root` or escaping/invalid source/target arguments)
- 3: Incomplete coverage (one or more sources could not be safely opened/read/decoded or exceeded size cap)
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
from urllib.parse import unquote

FENCE_RE = re.compile(r"^[ ]{0,3}(`{3,}|~{3,})(.*)$")
BQ_FENCE_RE = re.compile(r"^[ ]{0,3}>[ \t]*(`{3,}|~{3,})(.*)$")
ATX_RE = re.compile(r"^[ ]{0,3}(#{1,6})(?:[ \t]+(.*?))?(?:[ \t]+#+)?[ \t]*$")
SETEXT_RE = re.compile(r"^[ ]{0,3}(=+|-+)[ \t]*$")
REFDEF_RE = re.compile(r"^[ ]{0,3}\[(?!\^)([^\]]+)\]:[ \t]*(<[^>\n]+>|[^\s]+)")
SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")
CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")
MAX_SOURCE_BYTES = 16 * 1024 * 1024  # 16 MiB safety cap per caller-declared source


def sanitize_terminal(text: str) -> str:
    """Escape control characters for safe terminal rendering."""
    return CTRL_RE.sub(lambda m: f"\\x{ord(m.group(0)):02x}", text)


def clean_heading(raw: str) -> str:
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", raw)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"(\*\*|\*)(\S(?:.*?\S)?)\1", r"\2", text)
    text = re.sub(r"(?<!\w)(__|_)(\S(?:.*?\S)?)\1(?!\w)", r"\2", text)
    return re.sub(r"<[^>]+>", "", text).strip()


def _find_matching_ticks_in_line(line: str, pos: int, run_len: int) -> int:
    """Return index of an exact run_len backtick run at or after pos, or -1."""
    n = len(line)
    k = pos
    while k < n:
        if line[k] == "`":
            m = k
            while m < n and line[m] == "`":
                m += 1
            if (m - k) == run_len:
                return k
            k = m
        else:
            k += 1
    return -1


def strip_html_comments_line(line: str, in_comment: bool):
    """Strip HTML comments outside inline backtick spans, replacing them with a space so adjacent tokens never merge."""
    out = []
    i = 0
    n = len(line)
    while i < n:
        if in_comment:
            end = line.find("-->", i)
            if end == -1:
                return "".join(out), True
            out.append(" ")
            i = end + 3
            in_comment = False
            continue
        if line[i] == "\\":
            out.append(line[i:i + 2])
            i += 2
            continue
        if line[i] == "`":
            j = i
            while j < n and line[j] == "`":
                j += 1
            run_len = j - i
            close = _find_matching_ticks_in_line(line, j, run_len)
            if close != -1:
                out.append(line[i:close + run_len])
                i = close + run_len
                continue
            out.append(line[i:j])
            i = j
            continue
        if line.startswith("<!--", i):
            out.append(" ")
            i += 4
            in_comment = True
            continue
        out.append(line[i])
        i += 1
    return "".join(out), in_comment


def iter_visible_lines(text: str):
    """Yield (1-based line_number, line, interrupted_by_block) skipping YAML frontmatter,
    HTML comments, fenced code blocks, blockquoted fences, and indented code blocks."""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines = text.splitlines()
    start_idx = 0
    if lines and lines[0].strip() == "---":
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                start_idx = i + 1
                break

    fence_char = None
    fence_len = 0
    bq_fence_char = None
    bq_fence_len = 0
    in_comment = False
    prev_was_blank_or_block = True
    in_indented_code = False

    for idx in range(start_idx, len(lines)):
        raw_line = lines[idx]
        number = idx + 1

        # Inside an active fenced code block, literal `<!--` never opens an HTML comment.
        if fence_char is not None:
            m = FENCE_RE.match(raw_line)
            if m and m.group(1)[0] == fence_char and len(m.group(1)) >= fence_len and not m.group(2).strip():
                fence_char, fence_len = None, 0
            prev_was_blank_or_block = True
            in_indented_code = False
            continue

        if bq_fence_char is not None:
            m = BQ_FENCE_RE.match(raw_line)
            if m and m.group(1)[0] == bq_fence_char and len(m.group(1)) >= bq_fence_len and not m.group(2).strip():
                bq_fence_char, bq_fence_len = None, 0
                prev_was_blank_or_block = True
                continue
            if not raw_line.lstrip().startswith(">"):
                bq_fence_char, bq_fence_len = None, 0
                prev_was_blank_or_block = True
            else:
                prev_was_blank_or_block = True
                continue

        # Outside fences, strip HTML comments BEFORE fence detection so a fence inside a comment cannot open a fence.
        was_in_comment = in_comment
        line, in_comment = strip_html_comments_line(raw_line, in_comment)
        if was_in_comment and not line.strip():
            prev_was_blank_or_block = True
            in_indented_code = False
            continue

        m = FENCE_RE.match(line)
        if m:
            ch = m.group(1)[0]
            if ch == "~" or "`" not in m.group(2):
                fence_char, fence_len = ch, len(m.group(1))
                prev_was_blank_or_block = True
                in_indented_code = False
                continue

        bm = BQ_FENCE_RE.match(line)
        if bm:
            ch = bm.group(1)[0]
            if ch == "~" or "`" not in bm.group(2):
                bq_fence_char, bq_fence_len = ch, len(bm.group(1))
                prev_was_blank_or_block = True
                in_indented_code = False
                continue

        stripped = line.strip()
        if not stripped:
            prev_was_blank_or_block = True
            in_indented_code = False
            yield number, "", True
            continue

        is_indented = line.startswith("    ") or line.startswith("\t")
        if is_indented and (prev_was_blank_or_block or in_indented_code):
            in_indented_code = True
            prev_was_blank_or_block = False
            yield number, "", True
            continue

        in_indented_code = False
        yield number, line, prev_was_blank_or_block
        prev_was_blank_or_block = False


def parse_destination(line: str, start: int):
    """Parse an inline Markdown link destination + optional title starting right after ']('.
    Returns (destination, end_pos_after_closing_paren) or (None, start)."""
    pos, n = start, len(line)
    while pos < n and line[pos] in " \t":
        pos += 1
    if pos >= n:
        return None, start
    if line[pos] == "<":
        pos += 1
        begin = pos
        while pos < n:
            if line[pos] == "\\" and pos + 1 < n:
                pos += 2
                continue
            if line[pos] == ">":
                break
            pos += 1
        if pos >= n or line[pos] != ">":
            return None, start
        dest = line[begin:pos]
        pos += 1
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

    # Optional link title ("...", '...', or (...)) with backslash-escape handling
    if pos < n and line[pos] in "\"'(":
        close_ch = ")" if line[pos] == "(" else line[pos]
        pos += 1
        while pos < n:
            if line[pos] == "\\" and pos + 1 < n:
                pos += 2
                continue
            if line[pos] == close_ch:
                pos += 1
                break
            pos += 1
        else:
            return None, start
        while pos < n and line[pos] in " \t":
            pos += 1

    if pos < n and line[pos] == ")":
        return dest, pos + 1
    return None, start


def _has_matching_ticks_in_block(vis_lines: list, vis_idx: int, char_pos: int, run_len: int) -> bool:
    """Check whether an exact run_len backtick closer exists in the current paragraph/block (CommonMark §6.1)."""
    if _find_matching_ticks_in_line(vis_lines[vis_idx][1], char_pos, run_len) != -1:
        return True
    for k in range(vis_idx + 1, len(vis_lines)):
        _, nxt_line, nxt_interrupted = vis_lines[k]
        if nxt_interrupted or not nxt_line.strip():
            break
        if _find_matching_ticks_in_line(nxt_line, 0, run_len) != -1:
            return True
    return False


def scan_inline_links(line: str, open_code_ticks: int, vis_lines: list = None, vis_idx: int = 0):
    """Single-pass scanner over a Markdown line that tracks inline code spans (including multiline),
    CommonMark §6.1 unmatched backticks, backslash escapes, nested brackets (e.g. linked images), and link titles.
    Returns (list_of_destinations, remaining_open_code_ticks)."""
    dests = []
    bracket_stack = []
    i = 0
    n = len(line)
    while i < n:
        if open_code_ticks > 0:
            if line[i] == "`":
                j = i
                while j < n and line[j] == "`":
                    j += 1
                if (j - i) == open_code_ticks:
                    open_code_ticks = 0
                i = j
            else:
                i += 1
            continue

        ch = line[i]
        if ch == "\\" and i + 1 < n:
            i += 2
            continue
        if ch == "`":
            j = i
            while j < n and line[j] == "`":
                j += 1
            run_len = j - i
            if vis_lines is not None:
                has_closer = _has_matching_ticks_in_block(vis_lines, vis_idx, j, run_len)
            else:
                has_closer = _find_matching_ticks_in_line(line, j, run_len) != -1
            if has_closer:
                open_code_ticks = run_len
            i = j
            continue
        if ch == "[":
            bracket_stack.append(i)
            i += 1
            continue
        if ch == "]" and bracket_stack:
            bracket_stack.pop()
            if i + 1 < n and line[i + 1] == "(":
                dest, end_pos = parse_destination(line, i + 2)
                if dest is not None:
                    dests.append(dest)
                    i = end_pos
                    continue
            i += 1
            continue
        i += 1
    return dests, open_code_ticks


def has_surrogates(text: str) -> bool:
    """Return True if text contains lone UTF-16 surrogates (e.g. non-UTF-8 POSIX argv bytes)."""
    return any(0xD800 <= ord(ch) <= 0xDFFF for ch in text)


def normalize_lexical_path(root_given: Path, root_real: Path, raw_path: str) -> str:
    """Normalize a repo-relative (or root-prefixed absolute) path lexically without touching target files.
    Preserves literal POSIX backslashes and rejects escapes outside root, surrogates, or bare '.'."""
    if not raw_path or "\x00" in raw_path or has_surrogates(raw_path):
        raise ValueError(f"invalid path: {raw_path!r}")
    p = Path(raw_path)
    if p.is_absolute():
        rel = None
        for base in (root_given, root_real):
            try:
                rel = p.relative_to(base)
                break
            except ValueError:
                continue
        if rel is None:
            raise ValueError(f"path escapes root {root_given}: {raw_path}")
        raw_rel = rel.as_posix()
    else:
        raw_rel = raw_path

    parts = []
    for seg in raw_rel.split("/"):
        if seg in ("", "."):
            continue
        if seg == "..":
            if not parts:
                raise ValueError(f"path escapes root: {raw_path}")
            parts.pop()
        else:
            parts.append(seg)
    if not parts:
        raise ValueError(f"path must name an entry inside root, not '.': {raw_path}")
    return "/".join(parts)


def validate_source_arg(root_given: Path, root_real: Path, raw_source: str) -> str:
    """Validate caller-supplied source path without erasing intermediate '..' before open."""
    if not raw_source or "\x00" in raw_source or has_surrogates(raw_source):
        raise ValueError(f"invalid source path: {raw_source!r}")
    p = Path(raw_source)
    if p.is_absolute():
        rel = None
        for base in (root_given, root_real):
            try:
                rel = p.relative_to(base)
                break
            except ValueError:
                continue
        if rel is None:
            raise ValueError(f"source path escapes root {root_given}: {raw_source}")
        raw_rel = rel.as_posix()
    else:
        raw_rel = raw_source

    segs = [s for s in raw_rel.split("/") if s not in ("", ".")]
    if not segs:
        raise ValueError(f"source path must name a file inside root: {raw_source}")
    if any(s == ".." for s in segs):
        raise ValueError(f"source path must not contain '..': {raw_source}")
    return "/".join(segs)


def open_source_confined(root_fd: int, source_rel: str) -> str:
    """Open source_rel component-by-component from root_fd using O_NOFOLLOW + O_NONBLOCK
    (TOCTOU-safe, no symlink traversal, no FIFO blocking stall)."""
    if not (hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")):
        raise OSError("platform lacks required O_NOFOLLOW/O_DIRECTORY confinement primitives")
    segs = source_rel.split("/")
    cur_fd = root_fd
    opened_fds = []
    flags_dir = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    flags_file = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0)
    try:
        for seg in segs[:-1]:
            nxt = os.open(seg, flags_dir, dir_fd=cur_fd)
            opened_fds.append(nxt)
            cur_fd = nxt
        leaf_fd = os.open(segs[-1], flags_file, dir_fd=cur_fd)
        opened_fds.append(leaf_fd)
        st = os.fstat(leaf_fd)
        if not stat.S_ISREG(st.st_mode):
            raise OSError(f"source is not a regular file: {source_rel}")
        if st.st_size > MAX_SOURCE_BYTES:
            raise OSError(f"source exceeds {MAX_SOURCE_BYTES}-byte safety limit: {source_rel}")
        # Read bounded bytes from the verified file descriptor
        with os.fdopen(os.dup(leaf_fd), "rb") as fh:
            raw = fh.read(MAX_SOURCE_BYTES + 1)
        if len(raw) > MAX_SOURCE_BYTES:
            raise OSError(f"source exceeds {MAX_SOURCE_BYTES}-byte safety limit: {source_rel}")
        try:
            return raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise UnicodeDecodeError(
                exc.encoding, exc.object, exc.start, exc.end,
                f"UTF-8 decode error in {source_rel}: {exc.reason}"
            ) from exc
    except OSError as exc:
        raise OSError(f"unreadable or confined-rejected source {source_rel}: {exc.strerror or exc}") from exc
    finally:
        for fd in reversed(opened_fds):
            try:
                os.close(fd)
            except OSError:
                pass


def resolve_local_target(source_rel: str, raw_target: str):
    """Resolve a Markdown local link destination relative to source_rel (pure lexical, no disk I/O)."""
    target = raw_target.strip()
    if not target or SCHEME_RE.match(target):
        return None, None
    target_unescaped = re.sub(r"\\([!-/:-@\[-`{-~])", r"\1", target)
    path_part, _, fragment = target_unescaped.partition("#")
    path_part = unquote(path_part.partition("?")[0])
    if path_part.startswith("/"):
        return None, None
    if not path_part:
        resolved = source_rel
    else:
        base_dir = os.path.dirname(source_rel)
        joined = f"{base_dir}/{path_part}" if base_dir else path_part
        parts = []
        for seg in joined.split("/"):
            if seg in ("", "."):
                continue
            if seg == "..":
                if not parts:
                    return None, None
                parts.pop()
            else:
                parts.append(seg)
        if not parts:
            return None, None
        resolved = "/".join(parts)
    return resolved, fragment


def scan_source_text(source_rel: str, text: str, target_set: set[str]):
    """Parse headings and explicit local links matching target_set."""
    vis = list(iter_visible_lines(text))

    # First pass: locate ATX and Setext headings without crossing blank/block interrupts.
    heading_at = {}
    para_lines = []
    para_start = None
    for number, line, interrupted in vis:
        if interrupted or not line.strip():
            para_lines, para_start = [], None
            if not line.strip():
                continue
        atx = ATX_RE.match(line)
        if atx:
            heading_at[number] = clean_heading(atx.group(2) or "")
            para_lines, para_start = [], None
            continue
        setext = SETEXT_RE.match(line)
        if setext and para_lines and para_start is not None:
            heading_at[para_start] = clean_heading(" ".join(p.strip() for p in para_lines))
            para_lines, para_start = [], None
            continue
        stripped = line.strip()
        is_para = (
            bool(stripped)
            and not stripped.startswith(("|", ">", "- ", "* ", "+ "))
            and not re.match(r"^\d+[.)] ", stripped)
            and not line.startswith(("    ", "\t"))
        )
        if is_para:
            if para_start is None:
                para_start = number
            para_lines.append(line)
        else:
            para_lines, para_start = [], None

    # Second pass: track active heading and multiline inline code spans, filtering immediately to target_set.
    current_heading = "(top)"
    open_code_ticks = 0
    hits = []
    for vis_idx, (number, line, interrupted) in enumerate(vis):
        if interrupted or not line.strip():
            open_code_ticks = 0
            if not line.strip():
                continue
        if number in heading_at:
            current_heading = heading_at[number] or "(top)"

        ticks_before = open_code_ticks
        inline_dests, open_code_ticks = scan_inline_links(line, open_code_ticks, vis, vis_idx)
        for raw_target in inline_dests:
            resolved, fragment = resolve_local_target(source_rel, raw_target)
            if resolved in target_set:
                hits.append({
                    "source": source_rel,
                    "line": number,
                    "heading": current_heading,
                    "kind": "inline_link",
                    "resolved": resolved,
                    "raw_target": raw_target.strip(),
                    "fragment": fragment or "",
                })

        if ticks_before == 0:
            ref = REFDEF_RE.match(line)
            if ref:
                raw_target = ref.group(2).strip("<>").strip()
                resolved, fragment = resolve_local_target(source_rel, raw_target)
                if resolved in target_set:
                    hits.append({
                        "source": source_rel,
                        "line": number,
                        "heading": current_heading,
                        "kind": "reference_definition",
                        "resolved": resolved,
                        "raw_target": raw_target,
                        "fragment": fragment or "",
                    })
    return hits


def find_backlinks(root: Path, sources: list[str], targets: list[str]):
    if has_surrogates(str(root)):
        return None, 2, [f"invalid --root (non-UTF-8 bytes): {root!r}"]
    root_given = Path(os.path.abspath(str(root)))
    try:
        root_real = root.resolve(strict=True)
    except OSError as exc:
        return None, 2, [f"invalid --root {root}: {exc}"]
    if has_surrogates(str(root_real)):
        return None, 2, [f"invalid --root (non-UTF-8 realpath): {root_real!r}"]
    if not root_real.is_dir():
        return None, 2, [f"--root is not a directory: {root}"]

    invalid_targets = []
    norm_targets = []
    seen_targets = set()
    for t in targets:
        try:
            nt = normalize_lexical_path(root_given, root_real, t)
            if nt not in seen_targets:
                seen_targets.add(nt)
                norm_targets.append(nt)
        except ValueError as exc:
            invalid_targets.append({"input": t.encode("utf-8", "backslashreplace").decode("ascii"), "error": str(exc).encode("utf-8", "backslashreplace").decode("ascii")})

    invalid_sources = []
    norm_sources = []
    seen_sources = set()
    for s in sources:
        try:
            ns = validate_source_arg(root_given, root_real, s)
            if ns not in seen_sources:
                seen_sources.add(ns)
                norm_sources.append(ns)
        except ValueError as exc:
            invalid_sources.append({"input": s.encode("utf-8", "backslashreplace").decode("ascii"), "error": str(exc).encode("utf-8", "backslashreplace").decode("ascii")})

    by_target = {t: [] for t in norm_targets}
    scanned_sources = []
    failed_sources = []

    if norm_targets and norm_sources:
        if not (hasattr(os, "O_NOFOLLOW") and hasattr(os, "O_DIRECTORY")):
            return None, 2, ["platform lacks required O_NOFOLLOW/O_DIRECTORY confinement primitives"]
        try:
            root_fd = os.open(str(root_real), os.O_RDONLY | os.O_DIRECTORY)
        except OSError as exc:
            return None, 2, [f"cannot open --root {root}: {exc}"]
        try:
            for ns in norm_sources:
                try:
                    text = open_source_confined(root_fd, ns)
                    scanned_sources.append(ns)
                except (OSError, UnicodeDecodeError) as exc:
                    failed_sources.append({"source": ns, "error": str(exc)})
                    continue
                for hit in scan_source_text(ns, text, seen_targets):
                    by_target[hit["resolved"]].append({
                        "source": hit["source"],
                        "line": hit["line"],
                        "heading": hit["heading"],
                        "kind": hit["kind"],
                        "raw_target": hit["raw_target"],
                        "fragment": hit["fragment"],
                    })
        finally:
            os.close(root_fd)

    has_arg_error = bool(invalid_targets or invalid_sources)
    incomplete = bool(failed_sources or invalid_sources)
    if has_arg_error and not failed_sources:
        exit_code = 2
    elif incomplete:
        exit_code = 3
    else:
        exit_code = 0

    data = {
        "scope": "working-tree explicit-link lookup (selected sources only)",
        "root": str(root_real),
        "sources_scanned": scanned_sources,
        "incomplete_coverage": incomplete,
        "invalid_targets": invalid_targets,
        "invalid_sources": invalid_sources,
        "failed_sources": failed_sources,
        "results": by_target,
    }
    return data, exit_code, []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="Deterministic working-tree reverse-link lookup across explicitly authorized Markdown sources."
    )
    ap.add_argument("--root", type=Path, default=Path.cwd(), help="Repository/space root directory (default: cwd)")
    ap.add_argument("--source", action="append", required=True, help="Authorized Markdown file relative to root (repeatable)")
    ap.add_argument("--json", action="store_true", help="Emit structured JSON output")
    ap.add_argument("targets", nargs="+", help="Repo-relative target path(s) to look up")
    args = ap.parse_args(argv)

    data, exit_code, fatal_errors = find_backlinks(args.root, args.source, args.targets)
    if data is None:
        if args.json:
            print(json.dumps({"fatal_errors": fatal_errors}, indent=2, ensure_ascii=False))
        else:
            for err in fatal_errors:
                print(f"ERROR: {sanitize_terminal(err)}", file=sys.stderr)
        return exit_code

    if args.json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(f"Scope: {data['scope']}")
        for item in data["invalid_targets"]:
            print(f"ERROR (invalid target): {sanitize_terminal(item['error'])}", file=sys.stderr)
        for item in data["invalid_sources"]:
            print(f"ERROR (invalid source): {sanitize_terminal(item['error'])}", file=sys.stderr)
        for item in data["failed_sources"]:
            print(f"ERROR (incomplete coverage): {sanitize_terminal(item['error'])}", file=sys.stderr)

        empty_msg = (
            "no match in successfully scanned sources (incomplete coverage; see stderr)"
            if data["incomplete_coverage"]
            else "no explicit link in the selected sources"
        )
        for target, hits in data["results"].items():
            print(f"\nTarget: {sanitize_terminal(target)}")
            if not hits:
                print(f"  {empty_msg}")
            else:
                for h in hits:
                    kind_tag = " (reference definition)" if h["kind"] == "reference_definition" else ""
                    src = sanitize_terminal(h["source"])
                    hdg = sanitize_terminal(h["heading"])
                    raw = sanitize_terminal(h["raw_target"])
                    print(f"  {src}:{h['line']} [{hdg}]{kind_tag} -> {raw}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
