"""Regenerate the OCR baselines with the current parser.

    PYTHONPATH=.:src python src/tests/ocrs/regenerate_conf_scores.py

Reads every ocr_* asset, runs detect_document, writes <stem>.ocr.json into
conf_scores_updated/. Needs GOOGLE_APPLICATION_CREDENTIALS (billed per page).
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # GOOGLE_APPLICATION_CREDENTIALS lives in .env

from src.ocrs.models.GoogleCloudVisionAPI import GoogleCloudVisionAPI

ASSETS = Path(__file__).parent / "assets"
OUT = ASSETS / "conf_scores_updated"


def main() -> int:
    OUT.mkdir(exist_ok=True)
    assets = sorted(p for p in ASSETS.glob("ocr_*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".pdf"})
    if not assets:
        print(f"no assets found in {ASSETS}")
        return 1

    failures = 0
    for asset in assets:
        try:
            result = GoogleCloudVisionAPI.detect_document(str(asset))
        except Exception as e:
            print(f"FAIL {asset.name}: {type(e).__name__}: {e}")
            failures += 1
            continue

        target = OUT / f"{asset.stem}.ocr.json"
        with open(target, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        blocks = sum(len(p["blocks"]) for p in result["pages"])
        types = sorted({b["block_type"] for p in result["pages"] for b in p["blocks"]})
        print(f"OK   {asset.name:22} -> {target.name:24} pages={result['total_pages']} "
              f"blocks={blocks} conf={result['average_confidence']:.4f} types={types}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
