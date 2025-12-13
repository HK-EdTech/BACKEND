# $300 USD free credit
# Reference link: https://docs.cloud.google.com/vision/docs/handwriting#vision-document-text-detection-python

'''
Docstring for src.ocrs.GoogleCloudVisionAPI
----------------------------------------------------------------

Google Cloud Products Page for CloudVision API (for content analysis):
https://console.cloud.google.com/marketplace/product/google/vision.googleapis.com?q=search&referrer=search&authuser=1&project=fluid-axe-424414-t7
1. Enable
2. Create Credentials, select API "Cloud Vision API"
3. Select "Application Data"
4. Create service account
    - Service Account Name: svc_hkedtech
    - (Auto Generated) Service Account id: svc_hkedtech
        - Auto Generated email address:  svc-hkedtech@fluid-axe-424414-t7.iam.gserviceaccount.com
    - Service Account Description: Service account is used for OCR purposes
5. Permissions: Quick Access - Basic - Owner
6. Principles with access: Just skip it

7. Google console: Credentaials -> Final your email under service account -> Keys -> Add Key -> Create New Key -> JSON

8. I have a json for the API key called: fluid-axe-424414-t7-e36e36754744.json, pass it in as env vars

9. Head over to "https://console.developers.google.com/billing/enable?project=227145770745", enable billing
    - Manaing billing accounts
    - Create a new billing account
        - Name: My Billing Account
    - Submit and enabling billing

10. Set billing account

11. Track cost here: https://console.cloud.google.com/billing/0189E8-7E15D9-F3C37A?authuser=1
'''
from google.cloud import vision
from typing import Dict, Any
import json
import sys
from utils.logger import get_logger

logger = get_logger(name=__name__)

class GoogleCloudVisionAPI:

    @staticmethod
    def detect_document(path:str) -> Dict[str, Any]:
        '''
        result["full_text"]: Extracted text
        result["average_confidence"]: average_confidence text score
        result["pages"][0]["blocks"][0]["paragraphs"][0]["words"][0]["confidence"]:First word confidence score
        '''

        client=vision.ImageAnnotatorClient()
        with open(path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

        # Use document_text_detection for dense text (forms, books, PDFs)
        response = client.document_text_detection(
            image=image,
            image_context={"language_hints": []}  # Empty = auto-detect all languages
        )

        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")

        # Extract full text
        full_text = response.full_text_annotation.text if response.full_text_annotation else ""

        # Build detailed structured output
        result = {
            "full_text": full_text,
            "pages": []
        }

        for page in response.full_text_annotation.pages:
            page_data = {
                "width": page.width,
                "height": page.height,
                "confidence": page.confidence,  # Page-level confidence
                "blocks": []
            }

            for block in page.blocks:
                block_data = {
                    "confidence": block.confidence,
                    "bounding_box": [[v.x, v.y] for v in block.bounding_box.vertices],
                    "paragraphs": []
                }

                for paragraph in block.paragraphs:
                    para_text = "".join([symbol.text for word in paragraph.words for symbol in word.symbols])
                    paragraph_data = {
                        "text": para_text,
                        "confidence": paragraph.confidence,
                        "words": []
                    }

                    for word in paragraph.words:
                        word_text = "".join([symbol.text for symbol in word.symbols])
                        word_data = {
                            "text": word_text,
                            "confidence": word.confidence,
                            "symbols": [
                                {
                                    "text": symbol.text,
                                    "confidence": symbol.confidence,
                                    "is_break": hasattr(symbol.property, 'detected_break')
                                }
                                for symbol in word.symbols
                            ]
                        }
                        paragraph_data["words"].append(word_data)

                    block_data["paragraphs"].append(paragraph_data)
                page_data["blocks"].append(block_data)
            result["pages"].append(page_data)

        # Optional: Add overall average confidence
        all_confidences = []
        def collect_confidences(obj):
            if hasattr(obj, 'confidence') and obj.confidence is not None:
                all_confidences.append(obj.confidence)
            for child in obj.__dict__.values():
                if isinstance(child, list):
                    for item in child:
                        if hasattr(item, '__dict__'):
                            collect_confidences(item)
                elif hasattr(child, '__dict__'):
                    collect_confidences(child)

        collect_confidences(response.full_text_annotation)
        result["average_confidence"] = sum(all_confidences) / len(all_confidences) if all_confidences else None

        return result
        

    # Simple version if you just want text + average confidence
    @staticmethod
    def detect_document_simple(path: str) -> tuple[str, float]:
        """Returns (extracted_text, average_confidence)"""
        data = GoogleCloudVisionAPI.detect_document_full(path)
        return data["full_text"], data.get("average_confidence", 0.0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("Usage: python vision_ocr.py <path-to-image.jpg>")
        logger.info("Example: python vision_ocr.py ./images/menu_chinese.jpg")
        sys.exit(1)

    image_path = sys.argv[1]

    logger.info(f"Processing: {image_path}")

    try:
        result = GoogleCloudVisionAPI.detect_document(image_path)

        # logger.info("EXTRACTED TEXT:")
        # logger.info(result["full_text"])

        logger.info(f"AVERAGE CONFIDENCE: {result["pages"][0]["confidence"]*100}")

        # Optional: Save full JSON output
        output_json = image_path.split(".")[0] + ".ocr.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\nFull detailed result saved to: {output_json}")

    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure:")
        print("   • GOOGLE_APPLICATION_CREDENTIALS env var is set")
        print("   • Vision API is enabled in your Google Cloud project")
        print("   • The image file exists and is readable")