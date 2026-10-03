import os
import json
import re


# Filler patterns to skip (TOC entries, page markers, blank headers)
FILLER_PATTERNS = re.compile(
    r'^(=== PAGE \d+ ===\s*$'
    r'|TABLE OF CONTENTS'
    r'|ARRANGEMENT OF CLAUSES'
    r'|\s*——+\s*$'
    r'|\s*\d+\s*$'           # Just a page number
    r'|\s*$)',
    re.MULTILINE | re.IGNORECASE
)


def is_filler_chunk(chunk: dict) -> bool:
    """Check if a chunk is just filler (TOC, page markers, etc.)."""
    content = chunk['content'].strip()
    # Too short to be meaningful
    if chunk['word_count'] < 15:
        return True
    # Mostly page markers or dashes
    cleaned = FILLER_PATTERNS.sub('', content).strip()
    if len(cleaned) < 30:
        return True
    return False


def chunk_bill(text: str, bill_name: str) -> list[dict]:
    """Split bill text into section-aware chunks, preserving section headers."""
    section_pattern = re.compile(
        r'((?:CHAPTER|Chapter)\s+[IVXivx\d]+[.\s]*[^\n]*'
        r'|\d+\.\s+[A-Z][^\n]*'
        r'|(?:SECTION|Section)\s+\d+[^\n]*'
        r'|SCHEDULE[^\n]*'
        r'|PART\s+[IVX\d]+[^\n]*)',
        re.MULTILINE
    )

    matches = list(section_pattern.finditer(text))
    chunks = []

    if not matches:
        chunks.append({
            'chunk_id': 0,
            'section_header': 'Full Text',
            'content': text.strip(),
            'bill_name': bill_name,
            'char_count': len(text),
            'word_count': len(text.split()),
        })
        return chunks

    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        section_text = text[start:end].strip()
        header = match.group().strip()

        if len(section_text) < 20:
            continue

        chunks.append({
            'chunk_id': i,
            'section_header': header,
            'content': section_text,
            'bill_name': bill_name,
            'char_count': len(section_text),
            'word_count': len(section_text.split()),
        })

    # Split oversized chunks
    final_chunks = []
    for chunk in chunks:
        final_chunks.extend(split_oversized_chunk(chunk))

    for i, chunk in enumerate(final_chunks):
        chunk['chunk_id'] = i

    return final_chunks


def split_oversized_chunk(chunk: dict, max_words: int = 3000) -> list[dict]:
    """Split chunks that exceed max_words at paragraph boundaries."""
    if chunk['word_count'] <= max_words:
        return [chunk]

    paragraphs = chunk['content'].split('\n\n')
    sub_chunks = []
    current = ""
    part = 1

    for para in paragraphs:
        if len(current.split()) + len(para.split()) > max_words and current:
            sub_chunks.append({
                **chunk,
                'section_header': f"{chunk['section_header']} (Part {part})",
                'content': current.strip(),
                'char_count': len(current),
                'word_count': len(current.split()),
            })
            current = para
            part += 1
        else:
            current += "\n\n" + para if current else para

    if current.strip():
        sub_chunks.append({
            **chunk,
            'section_header': f"{chunk['section_header']} (Part {part})" if part > 1 else chunk['section_header'],
            'content': current.strip(),
            'char_count': len(current),
            'word_count': len(current.split()),
        })

    return sub_chunks


def merge_small_chunks(chunks: list[dict], min_words: int = 500) -> list[dict]:
    """Merge consecutive small chunks to reduce API calls while keeping context."""
    if not chunks:
        return chunks

    merged = []
    current = dict(chunks[0])

    for chunk in chunks[1:]:
        if current['word_count'] < min_words:
            current['content'] += "\n\n" + chunk['content']
            current['section_header'] += " | " + chunk.get('section_header', '')
            current['word_count'] = len(current['content'].split())
            current['char_count'] = len(current['content'])
        else:
            merged.append(current)
            current = dict(chunk)

    merged.append(current)

    for i, chunk in enumerate(merged):
        chunk['chunk_id'] = i

    return merged


def chunk_all_bills(extracted_dir: str, chunks_dir: str) -> dict[str, list[dict]]:
    """Chunk all extracted bill texts and save results."""
    os.makedirs(chunks_dir, exist_ok=True)
    all_chunks = {}

    for fname in sorted(os.listdir(extracted_dir)):
        if not fname.endswith('.txt'):
            continue

        bill_name = fname.replace('.txt', '')
        txt_path = os.path.join(extracted_dir, fname)

        with open(txt_path, 'r') as f:
            text = f.read()

        print(f"  Chunking: {bill_name}")
        chunks = chunk_bill(text, bill_name)
        raw_count = len(chunks)

        # Filter out filler chunks
        chunks = [c for c in chunks if not is_filler_chunk(c)]
        filtered_count = len(chunks)

        # Merge small chunks aggressively
        chunks = merge_small_chunks(chunks, min_words=500)
        print(f"    Raw: {raw_count} → Filtered: {filtered_count} → Merged: {len(chunks)}")
        all_chunks[bill_name] = chunks

        out_path = os.path.join(chunks_dir, f"{bill_name}_chunks.json")
        with open(out_path, 'w') as f:
            json.dump(chunks, f, indent=2)

        avg_words = sum(c['word_count'] for c in chunks) // max(len(chunks), 1)
        print(f"    → {len(chunks)} chunks (avg {avg_words} words/chunk)")

    return all_chunks
