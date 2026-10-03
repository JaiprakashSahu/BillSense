import os
import json
import fitz  # PyMuPDF


def extract_text_from_pdf(pdf_path: str) -> dict:
    """Extract text from a PDF file with page-level metadata."""
    doc = fitz.open(pdf_path)
    pages = []
    full_text = ""

    for page_num, page in enumerate(doc):
        page_text = page.get_text()
        pages.append({
            'page_number': page_num + 1,
            'text': page_text,
            'char_count': len(page_text),
        })
        full_text += f"\n=== PAGE {page_num + 1} ===\n" + page_text

    result = {
        'file_name': os.path.basename(pdf_path),
        'total_pages': len(doc),
        'total_chars': len(full_text),
        'full_text': full_text,
        'pages': pages,
    }
    doc.close()
    return result


def extract_all_pdfs(pdf_dir: str, output_dir: str) -> list[dict]:
    """Extract text from all PDFs in a directory and save to output."""
    os.makedirs(output_dir, exist_ok=True)
    results = []

    for fname in sorted(os.listdir(pdf_dir)):
        if not fname.lower().endswith('.pdf'):
            continue

        pdf_path = os.path.join(pdf_dir, fname)
        print(f"  Extracting: {fname}")
        result = extract_text_from_pdf(pdf_path)

        # Save extracted text
        base_name = os.path.splitext(fname)[0]
        txt_path = os.path.join(output_dir, f"{base_name}.txt")
        with open(txt_path, 'w') as f:
            f.write(result['full_text'])

        # Save metadata
        meta_path = os.path.join(output_dir, f"{base_name}_meta.json")
        meta = {k: v for k, v in result.items() if k not in ('full_text', 'pages')}
        meta['pages_summary'] = [
            {'page': p['page_number'], 'chars': p['char_count']}
            for p in result['pages']
        ]
        with open(meta_path, 'w') as f:
            json.dump(meta, f, indent=2)

        print(f"    → {result['total_pages']} pages, {result['total_chars']} chars")
        results.append(result)

    return results
