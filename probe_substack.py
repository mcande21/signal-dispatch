#!/usr/bin/env python3
"""
Probe Substack draft to inspect ProseMirror JSON structure.
Used to reverse-engineer footnote node format.

Usage:
    source .venv/bin/activate
    python probe_substack.py

Environment variables (optional, will prompt if not set):
    SUBSTACK_EMAIL
    SUBSTACK_PASSWORD
"""

import getpass
import json
import os
import sys
from collections import defaultdict

DRAFT_ID = 191196432
PUBLICATION_URL = "https://signaldsp.substack.com"
OUTPUT_FILE = "probe_output.json"

FOOTNOTE_KEYWORDS = {"footnote", "note", "sup", "superscript", "endnote", "fn"}


def get_credentials():
    email = os.environ.get("SUBSTACK_EMAIL")
    if not email:
        email = input("Substack email: ").strip()

    password = os.environ.get("SUBSTACK_PASSWORD")
    if not password:
        password = getpass.getpass("Substack password: ")

    return email, password


def collect_node_types(node, found_types, footnote_nodes, path="root"):
    """
    Recursively walk ProseMirror node tree.
    Collects all node types and flags any footnote-related nodes.
    """
    if not isinstance(node, dict):
        return

    node_type = node.get("type", "")
    if node_type:
        found_types[node_type] += 1

        # Check if this node looks footnote-related
        lower_type = node_type.lower()
        if any(kw in lower_type for kw in FOOTNOTE_KEYWORDS):
            footnote_nodes.append({"path": path, "node": node})

    # Also check marks array
    for mark in node.get("marks", []):
        if isinstance(mark, dict):
            mark_type = mark.get("type", "")
            if mark_type:
                found_types[f"mark:{mark_type}"] += 1
                lower_mark = mark_type.lower()
                if any(kw in lower_mark for kw in FOOTNOTE_KEYWORDS):
                    footnote_nodes.append({"path": f"{path}[mark:{mark_type}]", "node": mark})

    # Recurse into content array
    for i, child in enumerate(node.get("content", [])):
        collect_node_types(child, found_types, footnote_nodes, path=f"{path}.content[{i}]")


def main():
    try:
        from substack import Api
    except ImportError:
        print("ERROR: substack library not found. Run: source .venv/bin/activate")
        sys.exit(1)

    print(f"Authenticating to {PUBLICATION_URL}...")

    cookies_string = os.environ.get("SUBSTACK_COOKIES")
    if cookies_string:
        print("Using cookie authentication...")
        try:
            api = Api(
                cookies_string=cookies_string,
                publication_url=PUBLICATION_URL,
            )
        except Exception as e:
            print(f"ERROR: Cookie auth failed: {e}")
            sys.exit(1)
    else:
        email, password = get_credentials()
        try:
            api = Api(
                email=email,
                password=password,
                publication_url=PUBLICATION_URL,
            )
        except Exception as e:
            print(f"ERROR: Authentication failed: {e}")
            sys.exit(1)

    print(f"Fetching draft {DRAFT_ID}...")
    try:
        draft = api.get_draft(DRAFT_ID)
    except Exception as e:
        print(f"ERROR: Failed to fetch draft: {e}")
        sys.exit(1)

    # Save the full raw draft response
    with open(OUTPUT_FILE, "w") as f:
        json.dump(draft, f, indent=2)
    print(f"Full draft JSON saved to {OUTPUT_FILE}")

    # Extract and parse draft_body
    draft_body_raw = draft.get("draft_body")
    if not draft_body_raw:
        print("\nWARNING: No 'draft_body' field found in draft response.")
        print("Top-level keys:", list(draft.keys()))
        sys.exit(0)

    if isinstance(draft_body_raw, str):
        try:
            doc = json.loads(draft_body_raw)
        except json.JSONDecodeError as e:
            print(f"ERROR: draft_body is a string but not valid JSON: {e}")
            print("Raw value (first 500 chars):", draft_body_raw[:500])
            sys.exit(1)
    else:
        # Already a dict
        doc = draft_body_raw

    # Pretty-print the full ProseMirror document
    print("\n" + "=" * 60)
    print("PROSEMIRROR DOCUMENT STRUCTURE")
    print("=" * 60)
    print(json.dumps(doc, indent=2))

    # Collect node type statistics
    found_types = defaultdict(int)
    footnote_nodes = []
    collect_node_types(doc, found_types, footnote_nodes)

    # Print summary of unique node types
    print("\n" + "=" * 60)
    print("NODE TYPE SUMMARY")
    print("=" * 60)
    for node_type, count in sorted(found_types.items()):
        print(f"  {node_type}: {count}")

    # Highlight footnote-related nodes
    print("\n" + "=" * 60)
    print("FOOTNOTE-RELATED NODES")
    print("=" * 60)
    if footnote_nodes:
        for entry in footnote_nodes:
            print(f"\nPath: {entry['path']}")
            print(json.dumps(entry["node"], indent=2))
    else:
        print("None found.")
        print(f"(Searched for keywords: {sorted(FOOTNOTE_KEYWORDS)})")
        print("\nHint: Substack may use a different representation.")
        print("Check probe_output.json for the raw structure and look for:")
        print("  - Nodes with attrs containing 'href' pointing to '#footnote'")
        print("  - Inline nodes with numeric text content")
        print("  - Any 'anchor', 'link', or 'ref' node types")


if __name__ == "__main__":
    main()
