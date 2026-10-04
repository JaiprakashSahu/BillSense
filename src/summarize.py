import os
import time
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from tqdm import tqdm
from src.llm import get_client, MODEL

load_dotenv()

# Max concurrent requests — Groq free tier allows 30 RPM,
# so 5 concurrent with ~1s each ≈ 25-30 RPM (safe margin)
MAX_WORKERS = 5

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

BATCH_PROMPT = """You are a legal analyst specializing in Indian legislation.
Summarize each of the following sections of an Indian bill in plain language.
For EACH section, provide 3-6 bullet points covering purpose, obligations, rights, penalties.
Preserve section/clause numbers. Separate each section summary with "---".

{sections}

Do not include any thinking or reasoning tags - just provide the summaries directly."""

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
    client = get_client()
    response = client.chat(
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


CONDENSE_PROMPT = """You are a legal analyst. Condense these section summaries of an Indian bill into a shorter combined summary, preserving all key points and section numbers.

{summaries}

Provide a condensed version covering all major points. Do not include any thinking or reasoning tags."""


def summarize_bill(section_summaries: list[str], bill_name: str) -> str:
    """Generate a bill-level meta-summary from section summaries.

    If the combined summaries exceed the input token limit (~5K words),
    splits into chunks, condenses each, then generates the final summary.
    """
    combined = "\n\n---\n\n".join(section_summaries)
    word_count = len(combined.split())
    client = get_client()

    # Groq free tier: 7K input tokens/min (~5K words).
    # Condense in small batches of 3 sections to stay under limit.
    import time

    if word_count > 3000:
        print(f"    Condensing {word_count} words in small batches...")
        batch_size = 3
        condensed_parts = []

        for i in range(0, len(section_summaries), batch_size):
            batch = section_summaries[i:i + batch_size]
            batch_text = "\n\n---\n\n".join(batch)

            # Skip if batch is too short
            if len(batch_text.split()) < 20:
                condensed_parts.append(batch_text)
                continue

            time.sleep(3)
            response = client.chat(
                messages=[{
                    "role": "user",
                    "content": CONDENSE_PROMPT.format(summaries=batch_text)
                }],
                max_tokens=512,
            )
            condensed_parts.append(response.choices[0].message.content)
            print(f"      Batch {i//batch_size + 1}/{(len(section_summaries) + batch_size - 1)//batch_size} done")

        combined = "\n\n---\n\n".join(condensed_parts)
        print(f"    Condensed to {len(combined.split())} words")

        # Keep condensing until under 3000 words
        pass_num = 2
        while len(combined.split()) > 3000:
            print(f"    Condensing pass {pass_num} ({len(combined.split())} words)...")
            parts2 = combined.split("\n\n---\n\n")
            condensed2 = []
            for i in range(0, len(parts2), 5):
                batch = "\n\n".join(parts2[i:i + 5])
                time.sleep(3)
                response = client.chat(
                    messages=[{
                        "role": "user",
                        "content": CONDENSE_PROMPT.format(summaries=batch)
                    }],
                    max_tokens=256,
                )
                condensed2.append(response.choices[0].message.content)
            combined = "\n\n---\n\n".join(condensed2)
            print(f"    → {len(combined.split())} words")
            pass_num += 1
            if pass_num > 5:
                # Safety: truncate if still too large after 5 passes
                words = combined.split()
                combined = " ".join(words[:2500])
                print(f"    Truncated to 2500 words")
                break

    time.sleep(3)
    response = client.chat(
        messages=[{
            "role": "user",
            "content": BILL_PROMPT.format(section_summaries=combined, bill_name=bill_name)
        }],
        max_tokens=4096,
    )
    return response.choices[0].message.content


def _worker_summarize(idx, chunk):
    """Worker function for concurrent summarization."""
    try:
        summary = summarize_section(chunk)
        return (idx, {
            'chunk_id': chunk['chunk_id'],
            'section_header': chunk.get('section_header', ''),
            'summary': summary,
        }, None)
    except Exception as e:
        return (idx, None, str(e))


def summarize_all_bills(chunks_dir: str, summaries_dir: str, rate_delay: float = 0.5):
    """Run optimized summarization pipeline on all chunked bills.

    Optimizations:
    - Concurrent API calls (5 workers)
    - Batching short sections
    - Filler chunk skipping
    - Resumable progress saving
    """
    os.makedirs(summaries_dir, exist_ok=True)

    for fname in sorted(os.listdir(chunks_dir)):
        if not fname.endswith('_chunks.json'):
            continue

        bill_name = fname.replace('_chunks.json', '')
        chunks_path = os.path.join(chunks_dir, fname)

        # Skip bills that already have a final summary
        summary_md_path = os.path.join(summaries_dir, f"{bill_name}.md")
        if os.path.exists(summary_md_path):
            print(f"\n  Skipping: {bill_name} (summary already exists)")
            continue

        with open(chunks_path, 'r') as f:
            chunks = json.load(f)

        print(f"\n  Summarizing: {bill_name} ({len(chunks)} chunks, {MAX_WORKERS} workers)")

        # Load saved progress
        section_summaries = {}  # idx -> summary_dict
        section_summary_path = os.path.join(summaries_dir, f"{bill_name}_sections.json")

        if os.path.exists(section_summary_path):
            with open(section_summary_path, 'r') as f:
                saved = json.load(f)
            # Convert list to dict keyed by index for easy lookup
            for i, s in enumerate(saved):
                section_summaries[i] = s
            print(f"    Resuming: {len(section_summaries)}/{len(chunks)} already done")

        # Find remaining chunks to process
        remaining = [(i, chunks[i]) for i in range(len(chunks)) if i not in section_summaries]

        if remaining:
            pbar = tqdm(total=len(chunks), initial=len(section_summaries), desc="    Sections")

            # Process in batches of MAX_WORKERS
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                batch_start = 0
                while batch_start < len(remaining):
                    batch = remaining[batch_start:batch_start + MAX_WORKERS]
                    futures = {}

                    for idx, chunk in batch:
                        future = executor.submit(_worker_summarize, idx, chunk)
                        futures[future] = idx
                        time.sleep(rate_delay)  # Small stagger to avoid burst

                    for future in as_completed(futures):
                        idx, result, error = future.result()

                        if error:
                            print(f"\n    Error on chunk {idx}: {error}")
                            # Retry once after delay
                            time.sleep(10)
                            try:
                                _, result, error2 = _worker_summarize(idx, chunks[idx])
                                if error2:
                                    print(f"    Retry failed: {error2}. Skipping chunk {idx}.")
                                    pbar.update(1)
                                    continue
                            except Exception:
                                pbar.update(1)
                                continue

                        section_summaries[idx] = result
                        pbar.update(1)

                    # Save progress after each batch
                    ordered = [section_summaries[i] for i in sorted(section_summaries.keys())]
                    with open(section_summary_path, 'w') as f:
                        json.dump(ordered, f, indent=2)

                    batch_start += MAX_WORKERS

            pbar.close()

        # Step 2: Bill-level meta-summary
        print(f"    Generating bill-level summary...")
        ordered = [section_summaries[i] for i in sorted(section_summaries.keys())]
        summary_texts = [s['summary'] for s in ordered]

        try:
            bill_summary = summarize_bill(summary_texts, bill_name)
        except Exception as e:
            print(f"    Error: {e}. Waiting 30s and retrying...")
            time.sleep(30)
            bill_summary = summarize_bill(summary_texts, bill_name)

        summary_md_path = os.path.join(summaries_dir, f"{bill_name}.md")
        with open(summary_md_path, 'w') as f:
            f.write(f"# Summary: {bill_name.replace('_', ' ')}\n\n")
            f.write(bill_summary)

        print(f"    → Saved: {summary_md_path}")
