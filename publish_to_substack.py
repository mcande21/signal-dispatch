#!/usr/bin/env python3
"""
publish_to_substack.py -- Publish Signal Dispatch articles to Substack.

Converts markdown articles to ProseMirror JSON and posts them via the
Substack API. Handles footnotes, inline formatting, tables, and front matter.

Usage:
    python publish_to_substack.py [--dry-run] [--draft-only] [--publish] <markdown_file>

    --dry-run     Print ProseMirror JSON to stdout, do not hit the API (default if no mode given)
    --draft-only  Create as draft and print the draft URL (default API mode)
    --publish     Create draft and immediately publish it

Environment:
    SUBSTACK_COOKIES      Cookie string for auth (e.g. "substack.sid=VALUE")
    SUBSTACK_PUB_URL      Publication URL (e.g. "https://signaldsp.substack.com")
                          Defaults to https://signaldsp.substack.com if not set.

Example:
    SUBSTACK_COOKIES="substack.sid=..." \\
        python publish_to_substack.py --draft-only content/drafts/4-deep_dive.md
"""

import argparse
import json
import os
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# ProseMirror node constructors
# ---------------------------------------------------------------------------

def text_node(text: str, marks: Optional[List[Dict]] = None) -> Dict:
    node: Dict[str, Any] = {"type": "text", "text": text}
    if marks:
        node["marks"] = marks
    return node


def paragraph_node(content: List[Dict]) -> Dict:
    return {"type": "paragraph", "attrs": {"textAlign": None}, "content": content}


def heading_node(level: int, content: List[Dict]) -> Dict:
    return {"type": "heading", "attrs": {"level": level}, "content": content}


def horizontal_rule_node() -> Dict:
    return {"type": "horizontal_rule"}


def footnote_anchor_node(number: int) -> Dict:
    return {"type": "footnoteAnchor", "attrs": {"number": number}}


def footnote_body_node(number: int, content_nodes: List[Dict]) -> Dict:
    return {
        "type": "footnote",
        "attrs": {"number": number},
        "content": content_nodes,
    }


# ---------------------------------------------------------------------------
# Inline markdown parser
# ---------------------------------------------------------------------------

# Parses a string that may contain [^N] footnote references alongside the
# standard bold / italic / link patterns.  Returns a list of ProseMirror
# inline nodes (text nodes and footnoteAnchor nodes).

_INLINE_PATTERN = re.compile(
    r"(?P<footnote_ref>\[\^(?P<fn_num>\d+)\])"
    r"|(?P<link>\[(?P<link_text>[^\]]+)\]\((?P<link_url>[^)]+)\))"
    r"|(?P<bold>\*\*(?P<bold_text>[^*]+)\*\*)"
    r"|(?P<italic>(?<!\*)\*(?P<italic_text>[^*]+)\*(?!\*))"
)


def parse_inline(text: str, italic_all: bool = False) -> List[Dict]:
    """
    Convert inline markdown in *text* to a list of ProseMirror inline nodes.

    Handles:
      - [^N]           footnote anchor
      - [text](url)    link
      - **text**       bold
      - *text*         italic

    If italic_all is True, wrap all plain text nodes in an italic mark
    (used for italic paragraphs like the footer).
    """
    if not text:
        return []

    nodes: List[Dict] = []
    last = 0

    for m in _INLINE_PATTERN.finditer(text):
        start, end = m.start(), m.end()

        # Plain text before this match
        if start > last:
            plain = text[last:start]
            marks = [{"type": "em"}] if italic_all else None
            nodes.append(text_node(plain, marks))

        if m.group("footnote_ref"):
            nodes.append(footnote_anchor_node(int(m.group("fn_num"))))

        elif m.group("link"):
            link_marks = [{"type": "link", "attrs": {"href": m.group("link_url")}}]
            if italic_all:
                link_marks.append({"type": "em"})
            nodes.append(text_node(m.group("link_text"), link_marks))

        elif m.group("bold"):
            bold_marks: List[Dict] = [{"type": "strong"}]
            if italic_all:
                bold_marks.append({"type": "em"})
            nodes.append(text_node(m.group("bold_text"), bold_marks))

        elif m.group("italic"):
            nodes.append(text_node(m.group("italic_text"), [{"type": "em"}]))

        last = end

    # Trailing plain text
    if last < len(text):
        plain = text[last:]
        marks = [{"type": "em"}] if italic_all else None
        nodes.append(text_node(plain, marks))

    return [n for n in nodes if n.get("text") != "" or n.get("type") != "text"]


# ---------------------------------------------------------------------------
# Front matter / metadata stripping
# ---------------------------------------------------------------------------

_FRONT_MATTER_KEYS = re.compile(
    r"^\*\*(Classification|Topic|Analyst confidence):\*\*", re.IGNORECASE
)


def strip_front_matter(lines: List[str]) -> Tuple[str, str, List[str]]:
    """
    Remove the title, subtitle, and metadata block from the line list.

    Returns (title, subtitle, remaining_lines).

    Front matter structure expected:
        # Title line
        ## Subtitle line
        (blank line)
        **Key:** Value lines
        ...
        ---  <-- first horizontal rule ends the front matter
    """
    title = ""
    subtitle = ""
    body_lines: List[str] = []

    i = 0
    n = len(lines)

    # Title: first non-empty line starting with "# "
    while i < n and not lines[i].strip():
        i += 1
    if i < n and lines[i].startswith("# "):
        title = lines[i][2:].strip()
        i += 1

    # Subtitle: next non-empty line starting with "## "
    while i < n and not lines[i].strip():
        i += 1
    if i < n and lines[i].startswith("## "):
        subtitle = lines[i][3:].strip()
        i += 1

    # Skip metadata block: blank lines and **Key:** lines until first "---"
    while i < n:
        line = lines[i].strip()
        if line == "---":
            i += 1  # consume the horizontal rule
            break
        # Skip blank lines and metadata key lines
        if line == "" or _FRONT_MATTER_KEYS.match(line):
            i += 1
            continue
        # Anything else means we've overshot -- stop skipping
        break

    body_lines = lines[i:]
    return title, subtitle, body_lines


# ---------------------------------------------------------------------------
# Table parser
# ---------------------------------------------------------------------------

def is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and "|" in line.strip()[1:]


def is_separator_line(line: str) -> bool:
    """Detect markdown table separator rows like |---|---|"""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return False
    inner = stripped.strip("|")
    return bool(re.match(r"^[\s\-:|]+$", inner))


def parse_table_row(line: str) -> List[str]:
    """Split a markdown table row into cell values."""
    stripped = line.strip().strip("|")
    return [cell.strip() for cell in stripped.split("|")]


def table_to_prosemirror(table_lines: List[str]) -> List[Dict]:
    """
    Convert markdown table lines to a list of paragraph nodes.

    Each data row becomes a paragraph: **Event** -- Probability -- Resolution Date
    Header and separator rows are skipped.
    """
    nodes: List[Dict] = []
    header_seen = False
    separator_seen = False

    for line in table_lines:
        if is_separator_line(line):
            separator_seen = True
            continue

        cells = parse_table_row(line)
        if not cells:
            continue

        if not header_seen:
            header_seen = True
            continue  # skip header row

        if len(cells) >= 3:
            event, prob, date = cells[0], cells[1], cells[2]
            # Build: **Event** -- Probability -- Resolution Date
            inline: List[Dict] = [
                text_node(event, [{"type": "strong"}]),
                text_node(f" -- {prob} -- {date}"),
            ]
            nodes.append(paragraph_node(inline))
        elif len(cells) == 2:
            event, prob = cells[0], cells[1]
            inline = [
                text_node(event, [{"type": "strong"}]),
                text_node(f" -- {prob}"),
            ]
            nodes.append(paragraph_node(inline))

    return nodes


# ---------------------------------------------------------------------------
# Footnote definition parser
# ---------------------------------------------------------------------------

_FOOTNOTE_DEF = re.compile(r"^\[\^(\d+)\]:\s*(.*)")


def parse_footnote_definitions(lines: List[str]) -> Dict[int, str]:
    """
    First pass: collect all footnote definitions from the line list.

    Footnote definitions look like:
        [^1]: Some text that may span multiple lines (indented continuation)

    Returns a dict mapping footnote number -> full text.
    """
    defs: Dict[int, str] = {}
    current_num: Optional[int] = None
    current_text: List[str] = []

    for line in lines:
        m = _FOOTNOTE_DEF.match(line)
        if m:
            # Save previous if any
            if current_num is not None:
                defs[current_num] = " ".join(current_text).strip()
            current_num = int(m.group(1))
            current_text = [m.group(2).strip()]
        elif current_num is not None and line.startswith("    "):
            # Indented continuation
            current_text.append(line.strip())
        else:
            # Non-continuation line ends the current footnote def
            if current_num is not None:
                defs[current_num] = " ".join(current_text).strip()
                current_num = None
                current_text = []

    if current_num is not None:
        defs[current_num] = " ".join(current_text).strip()

    return defs


# ---------------------------------------------------------------------------
# Main markdown -> ProseMirror converter
# ---------------------------------------------------------------------------

def markdown_to_prosemirror(markdown: str) -> Tuple[str, str, Dict]:
    """
    Convert a markdown article to a ProseMirror document.

    Returns (title, subtitle, prosemirror_doc).
    """
    lines = markdown.splitlines()

    # First pass: collect all footnote definitions
    footnote_defs = parse_footnote_definitions(lines)

    # Strip front matter
    title, subtitle, body_lines = strip_front_matter(lines)

    doc_content: List[Dict] = []

    # Track which footnote bodies have been emitted so we don't double-emit
    emitted_footnotes: set = set()

    # Second pass: process body into blocks
    # We need to group lines into logical blocks before converting.
    # Strategy: iterate line by line, building up a "current paragraph" buffer.
    # Flush on blank lines. Handle headings, hrs, tables, and footnote defs inline.

    para_buffer: List[str] = []

    def flush_paragraph():
        """Emit buffered paragraph lines as a paragraph node (or nodes)."""
        if not para_buffer:
            return
        text = " ".join(para_buffer).strip()
        para_buffer.clear()
        if not text:
            return

        # Detect italic paragraph (starts and ends with *)
        # e.g. *I combine structured OSINT...*
        is_italic = text.startswith("*") and text.endswith("*") and not text.startswith("**")
        if is_italic:
            inner = text[1:-1]
            inline = parse_inline(inner, italic_all=True)
            if inline:
                doc_content.append(paragraph_node(inline))
            return

        # Normal paragraph -- may contain footnote anchors
        inline = parse_inline(text)
        if not inline:
            return

        para = paragraph_node(inline)
        doc_content.append(para)

        # Emit any footnote bodies anchored in this paragraph, in order
        fn_nums_in_para = [
            n["attrs"]["number"]
            for n in inline
            if n.get("type") == "footnoteAnchor"
        ]
        for fn_num in fn_nums_in_para:
            if fn_num not in emitted_footnotes and fn_num in footnote_defs:
                fn_text = footnote_defs[fn_num]
                fn_inline = parse_inline(fn_text)
                if not fn_inline:
                    fn_inline = [text_node(fn_text)]
                fn_para = {"type": "paragraph", "attrs": {"textAlign": None}, "content": fn_inline}
                fn_body = footnote_body_node(fn_num, [fn_para])
                doc_content.append(fn_body)
                emitted_footnotes.add(fn_num)

    # Collect consecutive table lines
    table_buffer: List[str] = []

    def flush_table():
        if not table_buffer:
            return
        nodes = table_to_prosemirror(table_buffer)
        doc_content.extend(nodes)
        table_buffer.clear()

    i = 0
    n_lines = len(body_lines)

    while i < n_lines:
        line = body_lines[i]
        stripped = line.strip()

        # Skip footnote definition lines entirely (already parsed in first pass)
        if _FOOTNOTE_DEF.match(stripped):
            # Also skip any indented continuation lines
            flush_paragraph()
            flush_table()
            i += 1
            while i < n_lines and body_lines[i].startswith("    "):
                i += 1
            continue

        # Horizontal rule
        if stripped == "---":
            flush_paragraph()
            flush_table()
            doc_content.append(horizontal_rule_node())
            i += 1
            continue

        # Table lines
        if is_table_line(stripped):
            flush_paragraph()
            table_buffer.append(line)
            i += 1
            continue
        else:
            flush_table()

        # Blank line: flush paragraph buffer
        if not stripped:
            flush_paragraph()
            i += 1
            continue

        # Heading
        if stripped.startswith("#"):
            flush_paragraph()
            level = len(stripped) - len(stripped.lstrip("#"))
            heading_text = stripped.lstrip("#").strip()
            if heading_text:
                inline = parse_inline(heading_text)
                if not inline:
                    inline = [text_node(heading_text)]
                doc_content.append(heading_node(min(level, 6), inline))
            i += 1
            continue

        # Regular line -- accumulate into paragraph buffer
        para_buffer.append(stripped)
        i += 1

    # Flush any remaining content
    flush_paragraph()
    flush_table()

    doc = {"type": "doc", "content": doc_content}
    return title, subtitle, doc


# ---------------------------------------------------------------------------
# API interaction
# ---------------------------------------------------------------------------

PUBLICATION_URL = os.environ.get("SUBSTACK_PUB_URL", "https://signaldsp.substack.com")


def get_api():
    """Initialize and return a substack.Api instance using cookie auth."""
    try:
        import substack
    except ImportError:
        print(
            "Error: substack package not found. "
            "Activate the venv: source .venv/bin/activate",
            file=sys.stderr,
        )
        sys.exit(1)

    cookies_string = os.environ.get("SUBSTACK_COOKIES")
    if not cookies_string:
        print(
            "Error: SUBSTACK_COOKIES environment variable not set.\n"
            "Set it to your cookie string, e.g.:\n"
            '  export SUBSTACK_COOKIES="substack.sid=VALUE; other=VALUE"',
            file=sys.stderr,
        )
        sys.exit(1)

    api = substack.Api(
        cookies_string=cookies_string,
        publication_url=PUBLICATION_URL,
    )
    return api


def build_post_body(title: str, subtitle: str, doc: Dict, api) -> Dict:
    """
    Construct the draft body dict expected by api.post_draft().

    Uses the substack Post class to get the bylines / audience structure,
    then injects our custom ProseMirror doc directly.
    """
    from substack.post import Post

    user_id = api.get_user_id()
    post = Post(
        title=title,
        subtitle=subtitle,
        user_id=user_id,
        audience="everyone",
    )

    # Override the draft_body with our custom ProseMirror doc
    post.draft_body = doc

    draft = post.get_draft()
    # get_draft() serializes draft_body to a JSON string -- we already have the dict
    # Re-set to the JSON string form
    draft["draft_body"] = json.dumps(doc)
    return draft


def draft_url(publication_url: str, draft_id: int) -> str:
    base = publication_url.rstrip("/")
    return f"{base}/publish/post/{draft_id}"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Publish a Signal Dispatch markdown article to Substack.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("markdown_file", help="Path to the markdown article file")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        help="Print ProseMirror JSON to stdout, do not hit the API",
    )
    mode_group.add_argument(
        "--draft-only",
        action="store_true",
        help="Create as Substack draft and print the draft URL",
    )
    mode_group.add_argument(
        "--publish",
        action="store_true",
        help="Create draft and immediately publish it",
    )

    args = parser.parse_args()

    # Default to dry-run if no mode specified
    if not args.draft_only and not args.publish:
        args.dry_run = True

    # Read markdown
    try:
        with open(args.markdown_file, "r", encoding="utf-8") as f:
            markdown = f.read()
    except FileNotFoundError:
        print(f"Error: file not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    # Convert
    title, subtitle, doc = markdown_to_prosemirror(markdown)

    print(f"Title:    {title}", file=sys.stderr)
    print(f"Subtitle: {subtitle}", file=sys.stderr)
    print(f"Nodes:    {len(doc['content'])}", file=sys.stderr)

    if args.dry_run:
        print(json.dumps(doc, indent=2, ensure_ascii=False))
        return

    # API mode
    api = get_api()
    body = build_post_body(title, subtitle, doc, api)

    print("Creating draft...", file=sys.stderr)
    result = api.post_draft(body)
    draft_id = result.get("id")
    if not draft_id:
        print(f"Error: unexpected API response: {result}", file=sys.stderr)
        sys.exit(1)

    url = draft_url(PUBLICATION_URL, draft_id)
    print(f"Draft created: {url}", file=sys.stderr)

    if args.draft_only:
        print(url)
        return

    # --publish
    print("Pre-publishing...", file=sys.stderr)
    api.prepublish_draft(draft_id)

    print("Publishing...", file=sys.stderr)
    api.publish_draft(draft_id, send=True, share_automatically=False)

    print(f"Published: {url}")


if __name__ == "__main__":
    main()
