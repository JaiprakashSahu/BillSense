import re


def chunk_bill(text: str) -> list[dict]:
    """Split bill text into section-aware chunks."""
    section_pattern = re.compile(
        r'^(?:Chapter\s+[IVX\d]+|Section\s+\d+|\d+\.\s+[A-Z])',
        re.MULTILINE
    )

    sections = section_pattern.split(text)
    chunks = []

    for i, section in enumerate(sections):
        if section.strip():
            chunks.append({
                'section_id': i,
                'content': section.strip(),
                'char_count': len(section),
                'word_count': len(section.split()),
            })

    return chunks


def split_oversized_chunk(chunk: dict, max_tokens: int = 4000) -> list[dict]:
    """Split chunks that exceed max_tokens at paragraph boundaries."""
    if chunk['word_count'] < max_tokens:
        return [chunk]

    paragraphs = chunk['content'].split('\n\n')
    sub_chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) > max_tokens * 4:
            sub_chunks.append({
                **chunk,
                'content': current,
                'char_count': len(current),
                'word_count': len(current.split()),
            })
            current = para
        else:
            current += "\n\n" + para

    if current:
        sub_chunks.append({
            **chunk,
            'content': current,
            'char_count': len(current),
            'word_count': len(current.split()),
        })

    return sub_chunks
