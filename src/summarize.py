import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-pro')

SECTION_PROMPT = """
You are a legal analyst. Summarize this section of an Indian bill in plain
language. Include:
- Purpose of this section
- Key obligations/rights created
- Any penalties or exceptions
- Preserve section numbers for citation

Section text:
{content}

Provide summary in Markdown format.
"""

BILL_PROMPT = """
You are a legal analyst. Below are section-level summaries of an Indian bill.
Create a hierarchical, plain-language document covering:

1. Executive Summary (2-3 paragraphs)
2. Key Provisions (bulleted list of major points)
3. Rights & Obligations (who gets what, who owes what)
4. Penalties & Enforcement
5. Notable Exceptions or Limitations

Section summaries:
{section_summaries}

Aim for ~15-20 pages of clear plain-language output.
"""


def summarize_section(chunk: dict) -> str:
    """Generate a plain-language summary of a single bill section."""
    response = model.generate_content(
        SECTION_PROMPT.format(content=chunk['content'])
    )
    return response.text


def summarize_bill(section_summaries: list[str]) -> str:
    """Generate a bill-level meta-summary from section summaries."""
    combined = "\n\n---\n\n".join(section_summaries)
    response = model.generate_content(
        BILL_PROMPT.format(section_summaries=combined)
    )
    return response.text
