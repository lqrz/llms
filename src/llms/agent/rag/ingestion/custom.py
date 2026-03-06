"""Custom adhoc ingestion."""

import pymupdf
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from llama_index.core.schema import TextNode
import os
from typing import Literal
from langchain_core.callbacks import UsageMetadataCallbackHandler
import joblib
import re
from pathlib import Path
import base64


# =========================
# Pydantic schema for page parsing
# =========================

BlockType = Literal["header", "text", "table"]


class PageBlock(BaseModel):
    type: BlockType
    level: int | None = None  # only for headers
    text: str | None = None  # for headers and body text
    title: str | None = None  # optional for tables
    markdown: str | None = None  # required for tables


class ParsedPage(BaseModel):
    page_number: int
    blocks: list[PageBlock] = Field(default_factory=list)


# =========================
# PDF page rendering
# =========================


def render_pdf_page_to_png_bytes(
    pdf_path: str,
    page_number: int,
    dpi: int = 200,
) -> bytes:
    doc = pymupdf.open(str(pdf_path))
    page = doc.load_page(page_number - 1)

    zoom = dpi / 72.0
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    return pix.tobytes("png")


def png_bytes_to_base64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("utf-8")


# =========================
# Vision page parser
# =========================


def parse_page_with_vision_llm(
    png_bytes: bytes,
    page_number: int,
    model: str = "gpt-4.1-mini",
) -> ParsedPage:

    b64 = png_bytes_to_base64(png_bytes)

    prompt_table: str = """Extract the table from the image.
Return ONLY markdown.
Check if the table has a double header. If the table has a double header, merge it into 1.
Remove currency signs in front of numbers (e.g. "$ 30,177" should be "30,177").
Parse values that appear between parenthesis as negative values (e.g. "(2,693)" should be "-2,693").
Replace uninformed values as None (i.e. "-" should be "None").
"""
    prompt = f"""
Parse this SEC filing page into structured JSON.

Return JSON only.
Do not include markdown fences.
Do not add commentary.

Schema:
{{
  "page_number": {page_number},
  "blocks": [
    {{
      "type": "header" | "text" | "table",
      "level": 1 | 2,         // only for headers
      "text": "...",          // for header/text
      "title": "...",         // optional for table
      "markdown": "..."       // required for table
    }}
  ]
}}

Rules:
- Preserve reading order from top to bottom.
- Use "header" for section titles / subheaders.
- Use "text" for prose paragraphs.
- Use "table" for tabular content.
- Do not summarize or rewrite content.
- Do not hallucinate values that are not visible.
- Merge consecutive prose lines into coherent paragraph blocks.
- For tables, follow this guides: {prompt_table}
"""

    msg = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {
                "type": "image",
                "base64": b64,
                "mime_type": "image/png",
            },
        ]
    )

    callback = UsageMetadataCallbackHandler()

    llm = ChatOpenAI(
        model=model,
        temperature=0,
        api_key=os.getenv("OPENAI_API_KEY"),
    ).with_structured_output(ParsedPage)

    response = llm.invoke([msg], config={"callbacks": [callback]})
    # print(callback.usage_metadata.values())

    usage = callback.usage_metadata[list(callback.usage_metadata.keys())[0]]
    usage_info = {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
    }

    return response, usage_info


# =========================
# Markdown table -> row nodes
# =========================

MISSING = {"", "None", "—", "-", "–", None}


def is_missing(x) -> bool:
    return str(x).strip() in {str(m).strip() for m in MISSING}


def parse_number(cell: str):
    s = str(cell).strip()
    if is_missing(s):
        return None

    s = s.replace("$", "").strip()
    neg = s.startswith("(") and s.endswith(")")
    if neg:
        s = s[1:-1].strip()

    s = s.replace(",", "")
    try:
        v = float(s)
        return -v if neg else v
    except ValueError:
        return None


def parse_markdown_table(md: str) -> tuple[list[str], list[list[str]]]:
    rows = []

    for line in md.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue

        no_pipes = line.replace("|", "").strip()
        if no_pipes and set(no_pipes) <= {"-", ":", " "}:
            continue

        rows.append([c.strip() for c in line.strip("|").split("|")])

    if len(rows) < 2:
        raise ValueError("Markdown table too short")

    return rows[0], rows[1:]


def table_markdown_to_row_nodes(
    table_md: str,
    *,
    page_number: int,
    header_path: list[str],
    base_metadata: dict,
) -> list[TextNode]:
    header, body = parse_markdown_table(table_md)
    if len(header) < 2:
        return []

    value_cols = header[1:]
    local_header_stack: list[str] = []
    row_nodes: list[TextNode] = []

    for row in body:
        if len(row) < len(header):
            row = row + [""] * (len(header) - len(row))

        row_label = row[0].strip()
        value_cells = row[1:]

        if not row_label:
            continue

        # generic rule requested earlier:
        # if row has no values, treat it as a header inside the table
        if all(is_missing(v) for v in value_cells):
            cleaned = row_label.rstrip(":").strip()

            # light generic reset heuristic so stack does not grow forever
            letters = [c for c in cleaned if c.isalpha()]
            upper_ratio = (
                sum(c.isupper() for c in letters) / len(letters) if letters else 0.0
            )
            short = len(cleaned.split()) <= 8

            if upper_ratio > 0.8 and short:
                local_header_stack = [cleaned]
            elif not local_header_stack:
                local_header_stack = [cleaned]
            elif len(local_header_stack) == 1:
                local_header_stack = [local_header_stack[0], cleaned]
            else:
                local_header_stack = [local_header_stack[0], cleaned]
            continue

        values = {col: parse_number(val) for col, val in zip(value_cols, value_cells)}

        vals_str = "; ".join(
            f"{k}={'' if v is None else int(v) if float(v).is_integer() else v}"
            for k, v in values.items()
        )

        effective_path = header_path + local_header_stack
        row_text = (
            f"{' > '.join(effective_path) if effective_path else 'ROOT'} | {row_label}\n"
            f"{vals_str}"
        )

        row_nodes.append(
            TextNode(
                text=row_text,
                metadata={
                    **base_metadata,
                    "page_number": page_number,
                    "content_type": "table_row",
                    "header_path": effective_path,
                    "header_1": effective_path[0] if len(effective_path) > 0 else None,
                    "header_2": effective_path[1] if len(effective_path) > 1 else None,
                    "row_label": row_label,
                },
            )
        )

    return row_nodes


# =========================
# Parsed pages -> LlamaIndex nodes
# =========================


def parsed_pages_to_nodes(
    parsed_pages: list[ParsedPage],
    text_template: str,
    *,
    base_metadata: dict | None = None,
) -> list[TextNode]:
    base_metadata = base_metadata or {}
    nodes: list[TextNode] = []

    # document-level header state
    header_stack: list[str] = []

    for parsed_page in parsed_pages:
        page_meta = {
            **base_metadata,
            "page_number": parsed_page.page_number,
        }

        for block in parsed_page.blocks:
            if block.type == "header":
                text = (block.text or "").strip()
                if not text:
                    continue

                level = block.level or 1
                if level == 1:
                    header_stack = [text]
                elif level == 2:
                    if len(header_stack) == 0:
                        header_stack = [text]
                    elif len(header_stack) == 1:
                        header_stack = [header_stack[0], text]
                    else:
                        header_stack = [header_stack[0], text]
                else:
                    # fallback
                    if not header_stack:
                        header_stack = [text]
                    else:
                        header_stack = [header_stack[0], text]
                continue

            if block.type == "text":
                text = (block.text or "").strip()
                if not text:
                    continue

                nodes.append(
                    TextNode(
                        text=text,
                        metadata={
                            **page_meta,
                            "content_type": "text",
                            "header_path": list(header_stack),
                            "header_1": (
                                header_stack[0] if len(header_stack) > 0 else None
                            ),
                            "header_2": (
                                header_stack[1] if len(header_stack) > 1 else None
                            ),
                        },
                    )
                )
                continue

            if block.type == "table":
                table_md = (block.markdown or "").strip()
                if not table_md:
                    continue

                # full-table node
                nodes.append(
                    TextNode(
                        text=table_md,
                        metadata={
                            **page_meta,
                            "content_type": "table_full",
                            "header_path": list(header_stack),
                            "header_1": (
                                header_stack[0] if len(header_stack) > 0 else None
                            ),
                            "header_2": (
                                header_stack[1] if len(header_stack) > 1 else None
                            ),
                            "table_title": block.title,
                        },
                    )
                )

                # row nodes
                nodes.extend(
                    table_markdown_to_row_nodes(
                        table_md,
                        page_number=parsed_page.page_number,
                        header_path=list(header_stack),
                        base_metadata=page_meta,
                    )
                )

    # modify text template
    for n in nodes:
        n.text_template = text_template

    return nodes


# =========================
# Cost helpers
# =========================


def estimate_cost_usd(
    *,
    input_tokens: int,
    output_tokens: int,
    input_price_per_1m: float,
    output_price_per_1m: float,
) -> float:
    in_cost = (input_tokens / 1_000_000) * input_price_per_1m
    out_cost = (output_tokens / 1_000_000) * output_price_per_1m
    return in_cost + out_cost


# =========================
# End-to-end PDF -> parsed pages -> nodes
# =========================


def get_base_metadata(file_path: str):

    filename_re = re.compile(
        r"^\s*(?P<year>\d{4})\s+(?P<quarter>Q[1-4])\s+(?P<ticker>.+?)\s*$",
        re.IGNORECASE,
    )

    ticker2company = {
        "AMZN": "Amazon",
        "MSFT": "Microsoft",
        "INTC": "Intel",
        "NVDA": "Nvidia",
    }

    filename = Path(file_path).stem
    m = filename_re.match(filename)
    year = m.group("year")
    quarter = m.group("quarter")
    ticker = m.group("ticker")
    company = ticker2company[ticker]

    base_metadata = {
        "filename": filename,
        "ticker": ticker,
        "company": company,
        "year": year,
        "quarter": quarter,
    }

    return base_metadata


def parse_pdf_with_vision_to_nodes(
    pdf_path: str,
    page_idxs: list[int],
    input_price_per_1m: float,
    output_price_per_1m: float,
    text_template: str,
    pages_to_filter: list[int],
    *,
    model: str,
    path_output: str,
    dpi: int = 200,
) -> tuple[list[ParsedPage], list[TextNode]]:

    base_metadata = get_base_metadata(file_path=pdf_path)

    doc = pymupdf.open(pdf_path)

    parsed_pages: list[ParsedPage] = []

    total_input_tokens = 0
    total_output_tokens = 0
    total_tokens = 0
    total_cost = 0.0
    per_page_usage = []

    for page_idx in range(len(doc)):
        if page_idxs is not None and page_idx not in page_idxs:
            continue

        page_number = page_idx + 1
        if pages_to_filter is not None and page_number in pages_to_filter:
            continue

        png_bytes = render_pdf_page_to_png_bytes(pdf_path, page_number, dpi=dpi)
        response, usage_info = parse_page_with_vision_llm(
            png_bytes, page_number, model=model
        )
        parsed_pages.append(response)

        input_tokens = usage_info["input_tokens"]
        output_tokens = usage_info["output_tokens"]
        page_total_tokens = usage_info["total_tokens"]

        total_input_tokens += input_tokens
        total_output_tokens += output_tokens
        total_tokens += page_total_tokens

        page_cost = None
        if input_price_per_1m is not None and output_price_per_1m is not None:
            page_cost = estimate_cost_usd(
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_price_per_1m=input_price_per_1m,
                output_price_per_1m=output_price_per_1m,
            )
            total_cost += page_cost

        per_page_usage.append(
            {
                "page_number": page_number,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": page_total_tokens,
                "estimated_cost_usd": page_cost,
            }
        )

    nodes = parsed_pages_to_nodes(
        parsed_pages,
        text_template=text_template,
        base_metadata={
            **base_metadata,
            "source_file": pdf_path,
        },
    )

    usage_summary = {
        "model": model,
        "pages": len(parsed_pages),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_tokens": total_tokens,
        "estimated_total_cost_usd": (
            total_cost
            if (input_price_per_1m is not None and output_price_per_1m is not None)
            else None
        ),
        "per_page_usage": per_page_usage,
    }

    # joblib dump
    if path_output is not None:
        year, quarter, ticker = (
            base_metadata["year"],
            base_metadata["quarter"],
            base_metadata["ticker"],
        )
        joblib.dump(parsed_pages, f"{year}_{quarter}_{ticker}_parsed_pages.joblib")
        joblib.dump(nodes, f"{year}_{quarter}_{ticker}_nodes.joblib")
        joblib.dump(usage_summary, f"{year}_{quarter}_{ticker}_usage_summary.joblib")

    return parsed_pages, nodes, usage_summary


if __name__ == "__main__":

    year, quarter, ticker = "2023", "Q1", "AMZN"
    path_input_data = "../../data/tmp"
    file_path = f"{path_input_data}/{year} {quarter} {ticker}.pdf"
    page_idxs = None
    input_price_per_1m = 0.40
    output_price_per_1m = 1.60
    model: str = "gpt-4.1-mini"
    pages_to_filter = [1, 2, 45, 46, 47, 48, 49, 50]
    text_template: str = (
        "<metadata>\n{metadata_str}\n</metadata>\n\n<content>\n{content}\n</content>"
    )
    parsed_pages, nodes, usage_summary = parse_pdf_with_vision_to_nodes(
        file_path,
        page_idxs,
        input_price_per_1m,
        output_price_per_1m,
        model=model,
        text_template=text_template,
        pages_to_filter=pages_to_filter,
        path_output=None,
    )

    # usage cost
    usage_summary["estimated_total_cost_usd"]
