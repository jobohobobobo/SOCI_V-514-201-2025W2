#!/usr/bin/env python3
"""Summarize a PDF and embed annotated notes into a new PDF.

This script:
- Extracts text per page from a PDF.
- Builds a structured summary (overall summary + key points + per-page notes).
- Creates an annotated PDF with per-page note boxes.
- Writes a Markdown summary file and optional JSON output.

Dependencies: pypdf, reportlab
"""

from __future__ import annotations

import argparse
import io
import json
import re
from collections import Counter
from pathlib import Path
from textwrap import fill

from pypdf import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.pdfgen import canvas

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "has",
    "have",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "no",
    "not",
    "of",
    "on",
    "or",
    "such",
    "that",
    "the",
    "their",
    "then",
    "there",
    "these",
    "they",
    "this",
    "to",
    "was",
    "were",
    "will",
    "with",
    "we",
    "you",
    "your",
}


def split_sentences(text: str) -> list[str]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    if not cleaned:
        return []
    return re.split(r"(?<=[.!?])\s+", cleaned)


def tokenize_words(text: str) -> list[str]:
    return [
        word
        for word in re.findall(r"[A-Za-z']{2,}", text.lower())
        if word not in STOPWORDS
    ]


def score_sentences(sentences: list[str], word_scores: Counter) -> list[tuple[str, float]]:
    scored: list[tuple[str, float]] = []
    for sentence in sentences:
        words = tokenize_words(sentence)
        if not words:
            scored.append((sentence, 0.0))
            continue
        score = sum(word_scores[word] for word in words) / len(words)
        scored.append((sentence, score))
    return scored


def top_sentences(sentences: list[str], word_scores: Counter, limit: int) -> list[str]:
    scored = score_sentences(sentences, word_scores)
    scored.sort(key=lambda item: item[1], reverse=True)
    return [sentence for sentence, _ in scored[:limit]]


def top_keywords(words: list[str], limit: int) -> list[str]:
    counts = Counter(words)
    return [word for word, _ in counts.most_common(limit)]


def build_summary(page_texts: list[str], summary_sentences: int, keyword_count: int):
    full_text = "\n".join(page_texts)
    sentences = split_sentences(full_text)
    full_words = tokenize_words(full_text)
    word_scores = Counter(full_words)

    overall_summary = top_sentences(sentences, word_scores, summary_sentences)
    key_points = top_keywords(full_words, keyword_count)

    page_notes = []
    for index, text in enumerate(page_texts, start=1):
        page_sentences = split_sentences(text)
        page_words = tokenize_words(text)
        page_scores = Counter(page_words)
        page_summary = top_sentences(page_sentences, page_scores, 1)
        page_keywords = top_keywords(page_words, min(4, keyword_count))
        page_notes.append(
            {
                "page": index,
                "summary": page_summary[0] if page_summary else "(No extractable text)",
                "keywords": page_keywords,
            }
        )

    return {
        "overall_summary": overall_summary,
        "key_points": key_points,
        "page_notes": page_notes,
    }


def calculate_note_box(
    page_width: float,
    page_height: float,
    box_width: float,
    box_height: float,
    margin: float,
    position: str,
) -> tuple[float, float]:
    if position == "top-left":
        return margin, page_height - box_height - margin
    if position == "top-right":
        return page_width - box_width - margin, page_height - box_height - margin
    if position == "bottom-left":
        return margin, margin
    if position == "bottom-right":
        return page_width - box_width - margin, margin
    return page_width - box_width - margin, page_height - box_height - margin


def render_annotation_overlay(
    page_width: float,
    page_height: float,
    note_title: str,
    note_body: str,
    *,
    position: str,
    box_width: float,
    box_height: float,
) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    margin = 18
    x, y = calculate_note_box(
        page_width,
        page_height,
        box_width,
        box_height,
        margin,
        position,
    )

    c.setFillColor(colors.lightgrey)
    c.rect(x, y, box_width, box_height, fill=1, stroke=0)

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x + 6, y + box_height - 14, note_title)

    c.setFont("Helvetica", 7.5)
    wrapped = fill(note_body, width=32)
    text = c.beginText(x + 6, y + box_height - 28)
    for line in wrapped.splitlines():
        if text.getY() < y + 6:
            break
        text.textLine(line)
    c.drawText(text)

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def render_summary_page(summary: dict, page_width: float, page_height: float) -> io.BytesIO:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(page_width, page_height))

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, page_height - 60, "Document Summary")

    y = page_height - 90
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Overall Summary")
    y -= 16
    c.setFont("Helvetica", 10)
    for sentence in summary["overall_summary"]:
        for line in fill(f"• {sentence}", width=90).splitlines():
            c.drawString(48, y, line)
            y -= 12
        y -= 4

    y -= 8
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, y, "Key Points")
    y -= 16
    c.setFont("Helvetica", 10)
    for keyword in summary["key_points"]:
        c.drawString(48, y, f"• {keyword}")
        y -= 12

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def write_markdown(summary: dict, output_path: Path) -> None:
    lines = ["# Document Summary", "", "## Overall Summary"]
    lines.extend([f"- {sentence}" for sentence in summary["overall_summary"]])
    lines.extend(["", "## Key Points"])
    lines.extend([f"- {keyword}" for keyword in summary["key_points"]])
    lines.extend(["", "## Page Notes"])
    for note in summary["page_notes"]:
        keywords = ", ".join(note["keywords"]) if note["keywords"] else "(none)"
        lines.append(f"- **Page {note['page']}**: {note['summary']} (Keywords: {keywords})")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(summary: dict, output_path: Path | None) -> None:
    if output_path is None:
        return
    output_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


def annotate_pdf(
    input_path: Path,
    output_pdf: Path,
    summary_path: Path,
    summary_json_path: Path | None,
    summary_sentences: int,
    keyword_count: int,
    note_position: str,
    note_width: float,
    note_height: float,
) -> None:
    reader = PdfReader(str(input_path))
    page_texts = [page.extract_text() or "" for page in reader.pages]

    summary = build_summary(page_texts, summary_sentences, keyword_count)
    write_markdown(summary, summary_path)
    write_json(summary, summary_json_path)

    writer = PdfWriter()
    for page_index, page in enumerate(reader.pages, start=1):
        note = summary["page_notes"][page_index - 1]
        note_title = f"Notes (Page {page_index})"
        keyword_text = ", ".join(note["keywords"]) if note["keywords"] else "No keywords"
        note_body = f"{note['summary']}\nKeywords: {keyword_text}"

        page_width = float(page.mediabox.width)
        page_height = float(page.mediabox.height)
        box_width = min(note_width, page_width * 0.4)
        box_height = min(note_height, page_height * 0.3)
        overlay_buffer = render_annotation_overlay(
            page_width,
            page_height,
            note_title,
            note_body,
            position=note_position,
            box_width=box_width,
            box_height=box_height,
        )
        overlay = PdfReader(overlay_buffer).pages[0]
        page.merge_page(overlay)
        writer.add_page(page)

    if reader.pages:
        first_page = reader.pages[0]
        summary_buffer = render_summary_page(
            summary,
            float(first_page.mediabox.width),
            float(first_page.mediabox.height),
        )
        summary_page = PdfReader(summary_buffer).pages[0]
        writer.add_page(summary_page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with output_pdf.open("wb") as handle:
        writer.write(handle)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create structured summaries and annotated notes for a PDF.",
    )
    parser.add_argument("input_pdf", type=Path, help="Path to the source PDF.")
    parser.add_argument(
        "--output-pdf",
        type=Path,
        default=Path("annotated_output.pdf"),
        help="Where to write the annotated PDF.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("summary.md"),
        help="Where to write the Markdown summary.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        default=None,
        help="Optional JSON summary output path.",
    )
    parser.add_argument(
        "--summary-sentences",
        type=int,
        default=5,
        help="Number of sentences to include in the overall summary.",
    )
    parser.add_argument(
        "--keywords",
        type=int,
        default=10,
        help="Number of keywords to include in the key points list.",
    )
    parser.add_argument(
        "--note-position",
        choices=["top-right", "top-left", "bottom-right", "bottom-left"],
        default="top-right",
        help="Where to place the per-page note box.",
    )
    parser.add_argument(
        "--note-width",
        type=float,
        default=180,
        help="Width of the note box in points.",
    )
    parser.add_argument(
        "--note-height",
        type=float,
        default=140,
        help="Height of the note box in points.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    annotate_pdf(
        input_path=args.input_pdf,
        output_pdf=args.output_pdf,
        summary_path=args.summary,
        summary_json_path=args.summary_json,
        summary_sentences=args.summary_sentences,
        keyword_count=args.keywords,
        note_position=args.note_position,
        note_width=args.note_width,
        note_height=args.note_height,
    )


if __name__ == "__main__":
    main()
