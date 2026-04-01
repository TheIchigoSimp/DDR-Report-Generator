import os

def match_images_to_sections(observations: list, inspection_images: list, thermal_images: list) -> list:
    """
    Match images to observations using context text extracted from the PDF.
    Scores images by how many keywords from the observation area appear in the image's context.
    """
    used_paths = set()

    for obs in observations:
        obs["matched_images"] = []
        source = obs.get("source", "both").lower()
        source_pages = obs.get("source_pages", [])
        area = obs.get("area", "").lower()
        hint = obs.get("image_hint", "").lower()

        # Build keywords from area name and image hint
        keywords = set(area.split() + hint.split())
        # Remove generic words
        keywords -= {"the", "a", "an", "of", "in", "on", "at", "-", "and", "or", "side"}

        pools = []
        if source in ("inspection", "both"):
            pools.extend(inspection_images)
        if source in ("thermal", "both"):
            pools.extend(thermal_images)

        # Score each unused image by keyword matches in its context
        scored = []
        for img in pools:
            if img.get("path") in used_paths:
                continue
            context = img.get("context", "")
            if not context:
                continue
            score = sum(1 for kw in keywords if kw in context)
            if score > 0:
                scored.append((score, img))

        # Sort by score descending, take top 3
        scored.sort(key=lambda x: x[0], reverse=True)
        for score, img in scored[:3]:
            obs["matched_images"].append(img)
            used_paths.add(img.get("path"))

    matched_count = sum(1 for obs in observations if obs["matched_images"])
    print(f"[image_matcher] {matched_count}/{len(observations)} observations matched with images.")
    return observations


if __name__ == "__main__":
    test_obs = [
        {"area": "Hall Skirting level", "observation": "Dampness", "image_hint": "hall skirting dampness", "source": "inspection", "source_pages": [3]},
        {"area": "Common Bathroom", "observation": "Tile hollowness", "image_hint": "bathroom tile", "source": "inspection", "source_pages": [3]},
    ]
    test_inspection = [
        {"page": 3, "path": "a.jpeg", "filename": "a.jpeg", "context": "hall skirting level dampness | negative side photographs"},
        {"page": 3, "path": "b.jpeg", "filename": "b.jpeg", "context": "common bathroom tile hollowness | positive side photographs"},
    ]
    result = match_images_to_sections(test_obs, test_inspection, [])
    for obs in result:
        print(f"\n{obs['area']}: {len(obs['matched_images'])} images matched")
