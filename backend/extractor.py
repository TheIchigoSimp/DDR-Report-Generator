import fitz
import os


def extract_pdf_content(pdf_path: str, label: str) -> dict:
    result = {"text": "", "images": []}

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"[extractor] WARNING: Could not open PDF '{pdf_path}': {e}")
        return result

    # ── Text Extraction ──────────────────────────────────────────
    text_parts = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_text = page.get_text()
        text_parts.append(f"\n---Page {page_num + 1} --- \n{page_text}")

    result["text"] = "\n".join(text_parts).strip()

    # ── Image Extraction (with context) ──────────────────────────
    output_dir = os.path.join(
        os.path.dirname(pdf_path), "extracted_images", label
    )
    os.makedirs(output_dir, exist_ok=True)

    img_counter = 0
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        # Get all text blocks with positions on this page
        text_dict = page.get_text("dict")
        text_blocks = []
        for block in text_dict.get("blocks", []):
            if block.get("type") == 0:  # type 0 = text block
                block_text = ""
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        block_text += span.get("text", "") + " "
                block_text = block_text.strip()
                if block_text:
                    # y-position is top of the block
                    y_pos = block["bbox"][1]
                    text_blocks.append({"text": block_text, "y": y_pos})

        # Sort text blocks by vertical position
        text_blocks.sort(key=lambda b: b["y"])

        for img_index, img in enumerate(images):
            if img_index == 0:
                continue  # Skip first image per page (company logo)

            xref = img[0]

            try:
                base_image = doc.extract_image(xref)
            except Exception:
                continue

            image_bytes = base_image["image"]
            ext = base_image["ext"]

            if len(image_bytes) < 5000:
                continue

            # Find the image's position on the page
            context = ""
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    img_y = rects[0].y0  # top of image
                    # Find all text blocks ABOVE this image
                    above_texts = [b["text"] for b in text_blocks if b["y"] < img_y]
                    # Take the last 3 text blocks above the image as context
                    context = " | ".join(above_texts[-3:]) if above_texts else ""
            except Exception:
                pass

            filename = f"{label}_page{page_num + 1}_img{img_counter}.{ext}"
            filepath = os.path.join(output_dir, filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

            result["images"].append({
                "page": page_num + 1,
                "index": img_counter,
                "path": filepath,
                "ext": ext,
                "filename": filename,
                "context": context.lower(),
            })

            img_counter += 1

    doc.close()
    print(f"[extractor] {label}: {len(result['text'])} chars of text, "
          f"{len(result['images'])} images extracted.")
    return result


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python extractor.py <pdf_path> [label]")
        sys.exit(1)
    test_path = sys.argv[1]
    test_label = sys.argv[2] if len(sys.argv) > 2 else "test"
    data = extract_pdf_content(test_path, test_label)
    print(f"\nText preview (first 500 chars):\n{data['text'][:500]}")
    print(f"\nImages: {len(data['images'])}")
    for img in data["images"]:
        print(f"  - Page {img['page']}: {img['filename']}")
        print(f"    Context: {img['context'][:80]}")
