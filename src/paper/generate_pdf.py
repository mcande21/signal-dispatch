#!/usr/bin/env python3
"""
Signal Dispatch PDF Generator

Converts markdown drafts to professionally-styled PDFs using pandoc → HTML → weasyprint.
Design aesthetic: The Economist / Foreign Affairs / Stratfor -- authoritative, clean, minimal.
"""

import argparse
import subprocess
import sys
from pathlib import Path


CSS_STYLE = """
/* Professional typography for geopolitical intelligence newsletter */

@page {
    size: letter;
    margin: 1in;

    @top-left {
        content: "Signal Dispatch";
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-size: 9pt;
        color: #666;
    }

    @top-right {
        content: "Issue #1 • March 6, 2026";
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-size: 9pt;
        color: #666;
    }

    @bottom-center {
        content: counter(page);
        font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
        font-size: 9pt;
        color: #666;
    }
}

/* Remove default margins from first page */
@page :first {
    @top-left { content: none; }
    @top-right { content: none; }
}

/* Typography */
body {
    font-family: 'Palatino', 'Palatino Linotype', 'Georgia', 'Times New Roman', serif;
    font-size: 11pt;
    line-height: 1.5;
    color: #1a1a1a;
}

/* Headers - sans-serif, navy blue */
h1 {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-size: 28pt;
    font-weight: bold;
    color: #003366;
    page-break-after: avoid;
    margin-top: 2em;
    margin-bottom: 0.8em;
    padding-bottom: 0.4em;
    border-bottom: 2px solid #003366;
}

h2 {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-size: 18pt;
    font-weight: bold;
    color: #003366;
    page-break-after: avoid;
    margin-top: 1.8em;
    margin-bottom: 0.6em;
    padding-bottom: 0.3em;
    border-bottom: 1px solid #ccc;
}

h3 {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-size: 14pt;
    font-weight: bold;
    color: #333;
    page-break-after: avoid;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h4 {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-size: 12pt;
    font-weight: bold;
    color: #333;
    page-break-after: avoid;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
}

/* First h1 should not have top margin */
h1:first-of-type {
    margin-top: 0;
}

/* Paragraphs */
p {
    margin-bottom: 1em;
    text-align: justify;
    hyphens: auto;
}

/* Links */
a {
    color: #0066cc;
    text-decoration: none;
}

/* Lists */
ul, ol {
    margin-left: 2em;
    margin-bottom: 1em;
}

li {
    margin-bottom: 0.4em;
}

/* Blockquotes - primarily for executive summary */
blockquote {
    background-color: #f2f2f2;
    padding: 1.2em 1.5em;
    margin: 1.5em 0;
    border-left: 4px solid #003366;
    page-break-inside: avoid;
}

blockquote p {
    margin-bottom: 0.8em;
}

blockquote p:last-child {
    margin-bottom: 0;
}

/* Tables */
table {
    border-collapse: collapse;
    width: 100%;
    margin: 1.5em 0;
    page-break-inside: avoid;
}

thead {
    background-color: #003366;
    color: white;
}

th {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-weight: bold;
    padding: 0.6em 0.8em;
    text-align: left;
    border-bottom: 2px solid #003366;
}

td {
    padding: 0.5em 0.8em;
    border-bottom: 1px solid #ddd;
}

tbody tr:nth-child(even) {
    background-color: #f9f9f9;
}

/* Code */
code {
    font-family: 'Courier New', 'Courier', monospace;
    background-color: #f5f5f5;
    padding: 0.15em 0.3em;
    border-radius: 2px;
    font-size: 10pt;
}

pre {
    background-color: #f5f5f5;
    padding: 1em;
    border-left: 3px solid #999;
    margin: 1em 0;
    page-break-inside: avoid;
}

pre code {
    background-color: transparent;
    padding: 0;
}

/* Strong emphasis */
strong {
    font-weight: bold;
    color: #000;
}

/* Em emphasis */
em {
    font-style: italic;
}

/* Horizontal rules */
hr {
    border: none;
    border-top: 1px solid #999;
    margin: 2em 0;
}

/* Table of contents */
nav#TOC {
    background-color: #f8f8f8;
    padding: 1.5em;
    margin: 2em 0;
    border: 1px solid #ddd;
}

nav#TOC ul {
    list-style: none;
    margin-left: 0;
}

nav#TOC li {
    margin-bottom: 0.5em;
}

nav#TOC a {
    color: #003366;
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
}

/* Prevent orphans and widows */
p, li {
    orphans: 3;
    widows: 3;
}

/* Page breaks */
h1, h2 {
    page-break-after: avoid;
}

/* Specific section styling */

/* Executive Summary gets distinct background */
#executive-summary + p,
#executive-summary + blockquote {
    background-color: #f8f8f8;
    padding: 1em;
    border-left: 4px solid #003366;
}

/* Probability sections stand out */
.probability,
[id*="probability"] {
    background-color: #f8f8f8;
    padding: 0.8em;
    margin: 1em 0;
    border-left: 3px solid #0066cc;
}

/* Sources section - smaller font */
#sources {
    font-size: 9pt;
    line-height: 1.4;
}

#sources ul {
    margin-left: 1.5em;
}

#sources li {
    margin-bottom: 0.3em;
}

/* Footnotes */
.footnotes {
    margin-top: 3em;
    padding-top: 1em;
    border-top: 1px solid #ccc;
    font-size: 9pt;
}

.footnotes ol {
    margin-left: 1.5em;
}

/* Classification and metadata */
.metadata {
    font-family: 'Helvetica Neue', 'Helvetica', 'Arial', sans-serif;
    font-size: 10pt;
    color: #666;
    margin: 1em 0;
}
"""


def generate_pdf(markdown_file: Path, output_file: Path, verbose: bool = False):
    """
    Generate PDF from markdown using pandoc → HTML → weasyprint.

    Args:
        markdown_file: Path to input markdown file
        output_file: Path to output PDF file
        verbose: Print detailed output
    """

    # Create temporary HTML file
    html_file = output_file.parent / f"{output_file.stem}_temp.html"

    try:
        # Step 1: Convert markdown to HTML with pandoc
        pandoc_cmd = [
            "pandoc",
            str(markdown_file),
            "-o", str(html_file),
            "--standalone",
            "--toc",
            "--toc-depth", "2",
            "--metadata", "title=Signal Dispatch",
            "-H", "/dev/stdin"  # Read custom header from stdin
        ]

        if verbose:
            print(f"Step 1: Converting markdown to HTML")
            print(f"Running: {' '.join(pandoc_cmd[:-2])}")  # Don't show stdin part

        # Create HTML header with embedded CSS
        html_header = f"<style>\n{CSS_STYLE}\n</style>"

        result = subprocess.run(
            pandoc_cmd,
            input=html_header,
            capture_output=True,
            text=True,
            check=True
        )

        if verbose and result.stderr:
            print("Pandoc output:", result.stderr)

        # Step 2: Convert HTML to PDF with weasyprint
        weasyprint_cmd = [
            "weasyprint",
            str(html_file),
            str(output_file)
        ]

        if verbose:
            print(f"\nStep 2: Converting HTML to PDF")
            print(f"Running: {' '.join(weasyprint_cmd)}")

        result = subprocess.run(
            weasyprint_cmd,
            capture_output=True,
            text=True,
            check=True
        )

        if verbose and result.stderr:
            # Filter out common non-critical warnings
            stderr_lines = result.stderr.split('\n')
            important_lines = [
                line for line in stderr_lines
                if line and not any(skip in line for skip in [
                    'unknown property',
                    'invalid value',
                    'Ignored `gap',
                    'Ignored `overflow-x'
                ])
            ]
            if important_lines:
                print("Weasyprint output:", '\n'.join(important_lines))

        print(f"✓ PDF generated: {output_file}")
        print(f"  Size: {output_file.stat().st_size / 1024:.1f} KB")
        print(f"  Pages: ~{output_file.stat().st_size // 3000}")  # Rough estimate

    except subprocess.CalledProcessError as e:
        print(f"Error generating PDF:", file=sys.stderr)
        print(f"  Command: {' '.join(e.cmd)}", file=sys.stderr)
        print(f"  Return code: {e.returncode}", file=sys.stderr)
        if e.stdout:
            print(f"  STDOUT: {e.stdout}", file=sys.stderr)
        if e.stderr:
            print(f"  STDERR: {e.stderr}", file=sys.stderr)
        sys.exit(1)

    finally:
        # Clean up temporary files
        if html_file.exists():
            html_file.unlink()
            if verbose:
                print(f"\nCleaned up: {html_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate professional PDF from Signal Dispatch markdown draft",
        epilog="Example: python generate_pdf.py content/drafts/1-deep_dive.md"
    )
    parser.add_argument(
        "markdown_file",
        type=Path,
        help="Path to markdown draft file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output PDF path (default: same as input with .pdf extension)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    args = parser.parse_args()

    # Validate input
    if not args.markdown_file.exists():
        print(f"Error: Input file not found: {args.markdown_file}", file=sys.stderr)
        sys.exit(1)

    # Determine output path
    if args.output:
        output_file = args.output
    else:
        output_file = args.markdown_file.with_suffix('.pdf')

    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Generate PDF
    generate_pdf(args.markdown_file, output_file, args.verbose)


if __name__ == "__main__":
    main()
