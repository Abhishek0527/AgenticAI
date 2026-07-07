
from __future__ import annotations

import re
from dataclasses import dataclass
from collections import Counter
import pymupdf


@dataclass
class Heading:

    level: int
    text: str
    page: int
    font_size: float
    font_name: str
    y0: float


# Utilities

NUMBERING_REGEX = re.compile(
    r"^\d+(\.\d+)*[\)\.]?\s+"
)


def is_bold(font_name: str) -> bool:

    font_name = font_name.lower()

    return (
            "bold" in font_name
            or "black" in font_name
            or "heavy" in font_name
    )


def uppercase_ratio(text: str):

    letters = [c for c in text if c.isalpha()]

    if not letters:
        return 0

    upper = sum(c.isupper() for c in letters)

    return upper / len(letters)


def title_case_ratio(text: str):

    words = text.split()

    if not words:
        return 0

    title = 0

    for w in words:
        if len(w) > 1 and w[0].isupper():
            title += 1

    return title / len(words)


def looks_like_heading(text: str):

    text = text.strip()

    if len(text) < 3:
        return False

    if len(text) > 120:
        return False

    if text.endswith("."):
        return False

    return True


# Font Statistics
def compute_body_font(document):

    sizes = []

    for page in document:

        blocks = page.get_text("dict")["blocks"]

        for block in blocks:

            if "lines" not in block:
                continue

            for line in block["lines"]:

                for span in line["spans"]:

                    sizes.append(round(span["size"], 1))

    body_size = Counter(sizes).most_common(1)[0][0]

    return body_size


# Heading Detection

class HeadingDetector:

    def __init__(self):

        self.body_size = None

    def detect(self, pdf_path):
        print("Inside HeadingDetector")

        #doc = fitz.open(pdf_path)
        doc = pymupdf.open(pdf_path)

        self.body_size = compute_body_font(doc)

        headings = []

        for page_number, page in enumerate(doc):

            blocks = page.get_text("dict")["blocks"]

            for block in blocks:

                if "lines" not in block:
                    continue

                for line in block["lines"]:

                    text = ""

                    font_size = 0
                    font_name = ""
                    y0 = None

                    for span in line["spans"]:

                        text += span["text"]

                        font_size = max(
                            font_size,
                            span["size"]
                        )

                        font_name = span["font"]

                        y0 = span["bbox"][1]

                    text = text.strip()

                    if not looks_like_heading(text):
                        continue

                    level = self.classify(
                        text,
                        font_size,
                        font_name
                    )

                    if level is None:
                        continue

                    headings.append(

                        Heading(
                            level=level,
                            text=text,
                            page=page_number + 1,
                            font_size=font_size,
                            font_name=font_name,
                            y0=y0,
                        )

                    )

        return headings

    # -----------------------------------------------------

    def classify(
            self,
            text,
            font_size,
            font_name,
    ):

        score = 0

        if font_size >= self.body_size + 8:
            score += 5

        elif font_size >= self.body_size + 5:
            score += 4

        elif font_size >= self.body_size + 2:
            score += 2

        if is_bold(font_name):
            score += 2

        if NUMBERING_REGEX.match(text):
            score += 2

        if uppercase_ratio(text) > 0.7:
            score += 1

        if title_case_ratio(text) > 0.7:
            score += 1

        # -----------------------

        if score >= 7:
            return 1

        elif score >= 5:
            return 2

        elif score >= 3:
            return 3

        return None


# Document Title

def extract_document_title(pdf_path):

    doc = pymupdf.open(pdf_path)

    page = doc[0]

    blocks = page.get_text("dict")["blocks"]

    candidates = []

    for block in blocks:

        if "lines" not in block:
            continue

        for line in block["lines"]:

            text = ""

            font = 0

            y = None

            for span in line["spans"]:

                text += span["text"]

                font = max(font, span["size"])

                y = span["bbox"][1]

            candidates.append(

                (
                    font,
                    y,
                    text.strip()
                )

            )

    candidates.sort(
        key=lambda x: (-x[0], x[1])
    )

    return candidates[0][2]


# Example

if __name__ == "__main__":

    pdf = "sample.pdf"

    title = extract_document_title(pdf)

    print("\nDOCUMENT TITLE\n")
    print(title)

    detector = HeadingDetector()

    headings = detector.detect(pdf)

    print("\nHEADINGS\n")

    for h in headings:

        print(
            f"H{h.level}",
            h.page,
            h.text
        )