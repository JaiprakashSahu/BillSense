import os
import time
import json
from groq import Groq
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "qwen/qwen3.8-27b"

SECTION_PROMPT = """You are a legal analyst specializing in Indian legislation.
Summarize this section of an Indian bill in plain language.

Include:
- Purpose of this section
- Key obligations or rights created
- Any penalties or exceptions mentioned
- Preserve section/clause numbers for citation

Section Header: {header}

Section Text:
{content}

Provide a clear, concise summary in Markdown format (3-8 bullet points). Do not include any thinking or reasoning tags - just provide the summary directly."""

BILL_PROMPT = """You are a legal analyst specializing in Indian legislation.
Below are section-level summaries of an Indian bill called "{bill_name}".

Create a comprehensive, plain-language summary covering:

1. **Executive Summary** (2-3 paragraphs explaining what this bill does and why it matters)
2. **Key Provisions** (bulleted list of the major points)
3. **Rights & Obligations** (who gets what rights, who has what duties)
4. **Penalties & Enforcement** (what happens if someone violates the law)
5. **Notable Exceptions or Limitations** (any carve-outs or special cases)
6. **Key Definitions** (important terms defined in the bill)

Section summaries:
{section_summaries}

Write in clear, plain language that a non-lawyer can understand.
Use section/clause numbers for reference where available. Do not include any thinking or reasoning tags - just provide the summary directly."""


def summarize_section(chunk: dict) -> str:
    """Generate a plain-language summary of a single bill section."""
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": SECTION_PROMPT.format(
                header=chunk.get('section_header', 'Unknown'),
                content=chunk['content'][:6000]
            )
        }],
        max_tokens=1024,
    )
    return response.choices[0].message.content


def summarize_bill(section_summaries: list[str], bill_name: str) -> str:
    """Generate a bill-level meta-summary from section summaries."""
    combined = "\n\n---\n\n".join(section_summaries)
    if len(combined) > 25000:
        combined = combined[:25000] + "\n\n[... remaining sections truncated for length]"

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{
            "role": "user",
            "content": BILL_PROMPT.format(section_summaries=combined, bill_name=bill_name)
        }],
        max_tokens=4096,
    )
    return response.choices[0].message.content


def summarize_all_bills(chunks_dir: str, summaries_dir: str, rate_delay: float = 2.0):
    """Run summarization pipeline on all chunked bills.

    Args:
        rate_delay: Seconds to wait between API calls (Groq free tier = 30 RPM).
    """
    os.makedirs(summaries_dir, exist_ok=True)

    for fname in sorted(os.listdir(chunks_dir)):
        if not fname.endswith('_chunks.json'):
            continue

        bill_name = fname.replace('_chunks.json', '')
        chunks_path = os.path.join(chunks_dir, fname)

        with open(chunks_path, 'r') as f:
            chunks = json.load(f)

        print(f"\n  Summarizing: {bill_name} ({len(chunks)} chunks)")

        # Step 1: Section-level summaries
        section_summaries = []
        section_summary_path = os.path.join(summaries_dir, f"{bill_name}_sections.json")

        # Resume from saved progress if available
        if os.path.exists(section_summary_path):
            with open(section_summary_path, 'r') as f:
                section_summaries = json.load(f)
            print(f"    Resuming from chunk {len(section_summaries)}/{len(chunks)}")

        for i in tqdm(range(len(section_summaries), len(chunks)),
                      desc="    Sections", initial=len(section_summaries), total=len(chunks)):
            chunk = chunks[i]
            try:
                summary = summarize_section(chunk)
                section_summaries.append({
                    'chunk_id': chunk['chunk_id'],
                    'section_header': chunk.get('section_header', ''),
                    'summary': summary,
                })
                # Save progress after each section
                with open(section_summary_path, 'w') as f:
                    json.dump(section_summaries, f, indent=2)
                time.sleep(rate_delay)
            except Exception as e:
                print(f"\n    Error on chunk {i}: {e}")
                print(f"    Saving progress and waiting 60s before retry...")
                with open(section_summary_path, 'w') as f:
                    json.dump(section_summaries, f, indent=2)
                time.sleep(60)
                try:
                    summary = summarize_section(chunk)
                    section_summaries.append({
                        'chunk_id': chunk['chunk_id'],
                        'section_header': chunk.get('section_header', ''),
                        'summary': summary,
                    })
                    with open(section_summary_path, 'w') as f:
                        json.dump(section_summaries, f, indent=2)
                except Exception as e2:
                    print(f"    Retry failed: {e2}. Skipping chunk {i}.")

        # Step 2: Bill-level meta-summary
        print(f"    Generating bill-level summary...")
        summary_texts = [s['summary'] for s in section_summaries]
        try:
            bill_summary = summarize_bill(summary_texts, bill_name)
        except Exception as e:
            print(f"    Error generating bill summary: {e}")
            print(f"    Waiting 60s and retrying...")
            time.sleep(60)
            bill_summary = summarize_bill(summary_texts, bill_name)

        # Save bill-level summary as markdown
        summary_md_path = os.path.join(summaries_dir, f"{bill_name}.md")
        with open(summary_md_path, 'w') as f:
            f.write(f"# Summary: {bill_name.replace('_', ' ')}\n\n")
            f.write(bill_summary)

        print(f"    → Saved: {summary_md_path}")
