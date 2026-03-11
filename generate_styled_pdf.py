#!/usr/bin/env python3
"""
Generate clean PDF from markdown - simple blog post style.
Uses weasyprint for HTML-to-PDF conversion with minimal CSS.
"""

import subprocess
import sys
from pathlib import Path

# File paths
MD_PATH = Path("/Users/cooperanderson/work/personal/code/research/signal-dispatch/content/drafts/3-deep_dive.md")
PDF_PATH = Path("/Users/cooperanderson/work/personal/code/research/signal-dispatch/content/drafts/3-deep_dive.pdf")
INTERMEDIATE_HTML_PATH = Path("/tmp/signal_dispatch_styled.html")

# HTML template with clean blog post styling
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Signal Dispatch -- Deep Dive</title>
    <style>
        @page {
            margin: 1in;
            @bottom-center {
                content: counter(page);
                font-size: 9pt;
                color: #666;
            }
        }

        body {
            font-family: "Helvetica Neue", Helvetica, Arial, sans-serif;
            font-size: 12pt;
            line-height: 1.7;
            color: #333;
            margin: 0;
            padding: 0;
            background: #ffffff;
        }

        h1 {
            font-size: 28pt;
            font-weight: 700;
            margin: 0 0 0.5rem 0;
            color: #000;
            line-height: 1.2;
        }

        h2 {
            font-size: 18pt;
            font-weight: 600;
            color: #000;
            margin: 1.5rem 0 0.75rem 0;
            line-height: 1.3;
        }

        h3 {
            font-size: 14pt;
            font-weight: 600;
            color: #222;
            margin: 1.25rem 0 0.5rem 0;
            line-height: 1.3;
        }

        p {
            margin: 0 0 1rem 0;
            orphans: 3;
            widows: 3;
        }

        strong {
            font-weight: 700;
            color: #000;
        }

        em {
            font-style: italic;
        }

        ul, ol {
            margin: 0 0 1rem 0;
            padding-left: 1.5rem;
        }

        li {
            margin: 0.3rem 0;
        }

        sup {
            font-size: 0.75em;
            vertical-align: super;
        }

        .footnotes {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #ddd;
            font-size: 10pt;
            color: #666;
            line-height: 1.5;
        }

        .footnotes p {
            margin-bottom: 0.5rem;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 11pt;
        }

        th {
            font-weight: 600;
            padding: 0.5rem;
            text-align: left;
            border-bottom: 2px solid #ddd;
        }

        td {
            padding: 0.5rem;
            border-bottom: 1px solid #eee;
            vertical-align: top;
        }

        hr {
            border: none;
            border-top: 1px solid #ddd;
            margin: 2rem 0;
        }
    </style>
</head>
<body>
{{CONTENT}}
</body>
</html>
"""

def convert_md_to_html():
    """Convert markdown to HTML using pandoc."""
    try:
        result = subprocess.run(
            [
                "pandoc",
                str(MD_PATH),
                "-f", "markdown",
                "-t", "html",
                "--standalone"
            ],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"✗ Error converting markdown to HTML: {e}")
        print(f"  stderr: {e.stderr}")
        sys.exit(1)

def wrap_in_template(html_content):
    """Wrap pandoc HTML in styled template."""
    # Extract body content from pandoc output
    if "<body>" in html_content:
        body_start = html_content.find("<body>") + 6
        body_end = html_content.find("</body>")
        body_content = html_content[body_start:body_end].strip()
    else:
        body_content = html_content

    return HTML_TEMPLATE.replace("{{CONTENT}}", body_content)

def generate_pdf_from_html():
    """Generate PDF from HTML using weasyprint CLI."""
    try:
        subprocess.run(
            [
                "/opt/homebrew/bin/weasyprint",
                str(INTERMEDIATE_HTML_PATH),
                str(PDF_PATH),
                "-p",  # Enable PDF forms
                "--dpi", "300"  # Higher DPI for better quality
            ],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✓ PDF generated: {PDF_PATH}")

        # Get file size
        size_bytes = PDF_PATH.stat().st_size
        size_kb = size_bytes / 1024
        print(f"  Size: {size_kb:.1f} KB ({size_bytes:,} bytes)")

    except subprocess.CalledProcessError as e:
        print(f"✗ Error generating PDF: {e}")
        print(f"  stderr: {e.stderr}")
        sys.exit(1)

def main():
    print("Converting markdown to HTML...")
    html_content = convert_md_to_html()
    print("  ✓ Markdown converted")

    print("Wrapping in styled template...")
    styled_html = wrap_in_template(html_content)
    print("  ✓ Template applied")

    print("Writing intermediate HTML...")
    INTERMEDIATE_HTML_PATH.write_text(styled_html, encoding='utf-8')
    print(f"  ✓ HTML written: {INTERMEDIATE_HTML_PATH}")

    print("Generating PDF with weasyprint...")
    generate_pdf_from_html()

    print("\n✓ Done.")

if __name__ == "__main__":
    main()
