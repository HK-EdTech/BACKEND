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
from typing import Dict, Any, List
import json
import os
import sys
from utils.logger import get_logger

logger = get_logger(name=__name__)

class GoogleCloudVisionAPI:

    @staticmethod
    def _parse_annotation(annotation) -> List[Dict[str, Any]]:
        """Parse a full_text_annotation into the pages/blocks/paragraphs/words structure."""
        pages = []
        for page in annotation.pages:
            page_data = {
                "width": page.width,
                "height": page.height,
                "confidence": page.confidence,
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
            pages.append(page_data)
        return pages

    @staticmethod
    def detect_document(path: str) -> Dict[str, Any]:
        '''
        Supports images (.jpg, .jpeg, .png) and PDFs (.pdf).

        result["full_text"]: Extracted text (all pages joined for PDFs)
        result["average_confidence"]: Average confidence score
        result["pages"][i]["blocks"][j]["paragraphs"][k]["words"][l]["confidence"]: Word confidence
        PDF pages additionally include result["pages"][i]["page_number"] (1-indexed)

        Note: Synchronous PDF processing supports up to 5 pages. Use GCS +
        async_batch_annotate_files for larger documents.
        '''
        client = vision.ImageAnnotatorClient()

        with open(path, "rb") as f:
            content = f.read()

        ext = os.path.splitext(path)[1].lower()
        print(f"[GoogleCloudVisionAPI] File extension: {ext}")

        if ext == ".pdf":
            print("[GoogleCloudVisionAPI] Routing to: _detect_pdf (annotate_file, mime_type=application/pdf)")
            return GoogleCloudVisionAPI._detect_pdf(client, content)
        else:
            print("[GoogleCloudVisionAPI] Routing to: _detect_image (document_text_detection)")
            return GoogleCloudVisionAPI._detect_image(client, content)

    @staticmethod
    def _detect_image(client, content) -> Dict[str, Any]:
        image = vision.Image(content=content)
        print(f"What is this image content type? {type(image.content)}")  # Should be bytes

        response = client.document_text_detection(
            image=image,
            image_context={"language_hints": []}  # Empty = auto-detect all languages
        )

        if response.error.message:
            raise Exception(f"Google Vision API Error: {response.error.message}")

        full_text = response.full_text_annotation.text if response.full_text_annotation else ""

        pages = GoogleCloudVisionAPI._parse_annotation(response.full_text_annotation)
        page_confidences = [p["confidence"] for p in pages if p.get("confidence") is not None]
        average_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else None

        return {
            "average_confidence": average_confidence,
            "full_text": full_text,
            "total_pages": len(pages),
            "pages": pages
        }

    @staticmethod
    def _detect_pdf(client, content) -> Dict[str, Any]:
        '''
        PDF processing via annotate_file (synchronous, up to 5 pages).
        Each page entry in result["pages"] includes a "page_number" key (1-indexed).
        '''
        request = vision.AnnotateFileRequest(
            features=[vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)],
            input_config=vision.InputConfig(
                content=content,
                mime_type="application/pdf"
            )
        )

        batch_response = client.batch_annotate_files(requests=[request])
        # batch_response.responses[0] is AnnotateFileResponse
        # .responses on that is a list of AnnotateImageResponse, one per PDF page
        file_response = batch_response.responses[0]

        full_text_parts = []
        all_pages = []

        for page_response in file_response.responses:
            if page_response.error.message:
                raise Exception(f"Google Vision API Error (PDF page): {page_response.error.message}")

            if not page_response.full_text_annotation:
                continue

            # context.page_number is 1-indexed
            page_number = page_response.context.page_number
            full_text_parts.append(page_response.full_text_annotation.text)

            pages = GoogleCloudVisionAPI._parse_annotation(page_response.full_text_annotation)
            all_pages.extend({"page_number": page_number, **page} for page in pages)

        page_confidences = [p["confidence"] for p in all_pages if p.get("confidence") is not None]
        average_confidence = sum(page_confidences) / len(page_confidences) if page_confidences else None

        return {
            "average_confidence": average_confidence,
            "full_text": "\n".join(full_text_parts),
            "total_pages": len(all_pages),
            "pages": all_pages
        }
        

    # Simple version if you just want text + average confidence
    @staticmethod
    def detect_document_simple(path: str) -> tuple[str, float]:
        """Returns (extracted_text, average_confidence)"""
        data = GoogleCloudVisionAPI.detect_document(path)
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

        logger.info("EXTRACTED TEXT:")
        logger.info(f"\n {result['full_text']}")

        logger.info(f"AVERAGE CONFIDENCE: {result['pages'][0]['confidence']*100}")

        # Optional: Save full JSON output
        output_json = f"{image_path.split('ocr_')[0]}conf_scores/{image_path.split('/')[-1].split('.')[0]}.ocr.json" 
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"\nFull detailed result saved to: {output_json}")

    except Exception as e:
        logger.error(f"\nError: {e}. \n Please Make sure:\
                        • GOOGLE_APPLICATION_CREDENTIALS env var is set\
                        • Vision API is enabled in your Google Cloud project\
                        • The image file exists and is readable")