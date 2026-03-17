#!/usr/bin/env python3
"""
Probe Substack Notes API endpoints.
Try to discover how Notes work under the hood.
"""

import json
import os
import sys
from urllib.parse import unquote

import requests

PUBLICATION_URL = "https://signaldsp.substack.com"
COOKIE_SID = os.environ.get("SUBSTACK_SID", "")

def make_session():
    s = requests.Session()
    s.cookies.set("substack.sid", unquote(COOKIE_SID), domain=".substack.com")
    s.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    return s

def probe(session, method, url, data=None, label=""):
    try:
        if method == "GET":
            r = session.get(url, params=data)
        else:
            r = session.post(url, json=data)
        print(f"\n{'='*60}")
        print(f"{label}")
        print(f"{method} {url}")
        print(f"Status: {r.status_code}")
        if r.status_code < 400:
            try:
                body = r.json()
                # Truncate large responses
                text = json.dumps(body, indent=2)
                if len(text) > 2000:
                    print(text[:2000] + "\n... [truncated]")
                else:
                    print(text)
            except:
                print(r.text[:500])
        else:
            print(r.text[:500])
        return r
    except Exception as e:
        print(f"ERROR: {e}")
        return None

def main():
    if not COOKIE_SID:
        print("Set SUBSTACK_SID env var to your substack.sid cookie value")
        sys.exit(1)

    s = make_session()

    # First verify auth works
    probe(s, "GET", "https://substack.com/api/v1/user/profile/self", label="1. Verify auth")

    # Probe Notes-related endpoints
    base = "https://substack.com/api/v1"
    pub_base = f"{PUBLICATION_URL}/api/v1"

    # Try various Notes endpoint patterns
    probe(s, "GET", f"{base}/reader/notes", label="2. GET /reader/notes")
    probe(s, "GET", f"{base}/notes/feed", label="3. GET /notes/feed")
    probe(s, "GET", f"{base}/notes", label="4. GET /notes")
    probe(s, "GET", f"{pub_base}/notes", label="5. GET pub/notes")
    probe(s, "GET", f"{base}/reader/feed", label="6. GET /reader/feed")

    # Try to create a note (don't worry, we can delete)
    # Common patterns: POST with body containing text/content
    test_note = {
        "body": json.dumps({
            "type": "doc",
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {"type": "text", "text": "Test note - will delete"}
                    ]
                }
            ]
        })
    }

    probe(s, "POST", f"{base}/notes", data=test_note, label="7. POST /notes (create)")
    probe(s, "POST", f"{pub_base}/notes", data=test_note, label="8. POST pub/notes (create)")

    # Try comment/note hybrid endpoints
    probe(s, "GET", f"{base}/reader/notes/feed", label="9. GET /reader/notes/feed")
    probe(s, "POST", f"{base}/comment", data=test_note, label="10. POST /comment")

    print("\n\nDone probing. Check output for 200s -- those are the live endpoints.")


if __name__ == "__main__":
    main()
