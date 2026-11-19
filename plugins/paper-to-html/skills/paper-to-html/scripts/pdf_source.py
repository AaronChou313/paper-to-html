#!/usr/bin/env python3
"""Inspect source PDF blocks or crop a figure, table, or equation."""
import argparse
import json
from pathlib import Path

try:
    import pymupdf
except ImportError:
    raise SystemExit("PDF extraction needs PyMuPDF. Use an existing environment or install pymupdf in a temporary virtual environment.")


def rounded(box):
    return [round(v, 2) for v in box]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="Write raw layout blocks to JSON")
    inspect.add_argument("pdf", type=Path)
    inspect.add_argument("--pages", type=int, nargs=2, metavar=("FIRST", "LAST"))
    crop = commands.add_parser("crop", help="Save a page or a cropped rectangle as PNG")
    crop.add_argument("pdf", type=Path)
    crop.add_argument("page", type=int, help="Physical PDF page, starting at 1")
    crop.add_argument("output", type=Path)
    crop.add_argument("--clip", type=float, nargs=4, metavar=("X0", "Y0", "X1", "Y1"))
    args = parser.parse_args()
    with pymupdf.open(args.pdf) as doc:
        if args.command == "inspect":
            first, last = args.pages or (1, len(doc))
            if not 1 <= first <= last <= len(doc):
                parser.error(f"Page range outside PDF (1–{len(doc)})")
            data = []
            for number in range(first, last + 1):
                page = doc[number - 1]
                blocks = page.get_text("blocks", sort=False)
                data.append({
                    "page": number, "printed_label": page.get_label(), "box": rounded(page.rect),
                    "blocks": [{"id": b[5], "box": rounded(b[:4]), "text": b[4]}
                               for b in blocks if b[6] == 0],
                })
            print(json.dumps({"page_count": len(doc), "pages": data}, ensure_ascii=False, indent=2))
        else:
            if not 1 <= args.page <= len(doc):
                parser.error(f"Page outside PDF (1–{len(doc)})")
            page = doc[args.page - 1]
            rect = pymupdf.Rect(*args.clip) if args.clip else page.rect
            if not page.rect.contains(rect) or rect.is_empty or rect.is_infinite:
                parser.error("Clip must be a nonempty rectangle inside the page.")
            if args.output.suffix.lower() != ".png":
                parser.error("Crop output must have a .png extension.")
            page.get_pixmap(matrix=pymupdf.Matrix(2, 2), clip=rect, alpha=False).save(args.output)


if __name__ == "__main__":
    main()
