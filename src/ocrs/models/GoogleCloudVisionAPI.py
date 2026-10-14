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

_BREAK_WHITESPACE = {
    vision.TextAnnotation.DetectedBreak.BreakType.SPACE: " ",
    vision.TextAnnotation.DetectedBreak.BreakType.SURE_SPACE: " ",
    vision.TextAnnotation.DetectedBreak.BreakType.EOL_SURE_SPACE: "\n",
    vision.TextAnnotation.DetectedBreak.BreakType.LINE_BREAK: "\n",
    vision.TextAnnotation.DetectedBreak.BreakType.HYPHEN: "\n",
}

"""
GOOGLE VISION RESPONSE STRUCTURE — reference notes
==================================================
Verified against google-cloud-vision 3.11.0 (proto descriptors dumped 2026-09-22).
Field names below are the PYTHON names; the REST docs use camelCase (full_text_annotation
-> fullTextAnnotation). Re-verify if the package version changes.

Docs:
  https://docs.cloud.google.com/vision/docs/reference/rest/v1/AnnotateImageResponse
  https://docs.cloud.google.com/vision/deprecation/reference/rest/v1/files/annotate
  https://docs.cloud.google.com/vision/docs/pdf


1. PDF PATH — client.batch_annotate_files(requests=[AnnotateFileRequest])
--------------------------------------------------------------------------
BatchAnnotateFilesResponse
`-- responses[]: AnnotateFileResponse          one per FILE sent (we send 1)
    |-- input_config: InputConfig              echo of the request
    |   |-- gcs_source.uri: str
    |   |-- content: bytes
    |   `-- mime_type: str
    |-- responses[]: AnnotateImageResponse     one per PAGE (max 5)
    |   |-- full_text_annotation: TextAnnotation      <- the OCR result (see 3)
    |   |-- error: Status {code, message, details[]}  <- PER-PAGE failure
    |   |-- context: ImageAnnotationContext {uri, page_number}   page_number is 1-indexed
    |   `-- (12 unused siblings: face_annotations, label_annotations, web_detection,
    |        safe_search_annotation, image_properties_annotation, crop_hints_annotation,
    |        product_search_results, text_annotations, logo_annotations,
    |        landmark_annotations, localized_object_annotations)
    |-- total_pages: int                       REAL page count of the file
    `-- error: Status                          FILE-level failure (we do not check this)


2. IMAGE PATH — client.document_text_detection(image=vision.Image(content=...))
--------------------------------------------------------------------------
AnnotateImageResponse                          a single response, NOT wrapped in a file
|-- full_text_annotation: TextAnnotation       its pages[] always has exactly 1 entry
`-- error: Status

vision.Image has only two fields, content (raw bytes) and source (URI) — there is no
mime_type, which is why PDFs cannot use this path and need InputConfig instead.


3. TextAnnotation — the same hierarchy for both paths
--------------------------------------------------------------------------
TextAnnotation
|-- text: str                      whole document text, correctly spaced by Google
`-- pages[]: Page
    |-- property: TextProperty
    |-- width / height: int        POINTS for PDF, PIXELS for images (A4 PDF = 595x842)
    |-- confidence: float          [0, 1]
    `-- blocks[]: Block
        |-- property: TextProperty
        |-- bounding_box: BoundingPoly
        |-- block_type: enum  UNKNOWN | TEXT | TABLE | PICTURE | RULER | BARCODE
        |-- confidence: float
        `-- paragraphs[]: Paragraph
            |-- property / bounding_box / confidence
            `-- words[]: Word
                |-- property / bounding_box / confidence
                `-- symbols[]: Symbol
                    |-- property / bounding_box / confidence
                    `-- text: str          ONE character

TextProperty (present at every level above)
|-- detected_languages[]: DetectedLanguage {language_code (BCP-47), confidence}
`-- detected_break: DetectedBreak
    |-- type_: enum  UNKNOWN | SPACE | SURE_SPACE | EOL_SURE_SPACE | HYPHEN | LINE_BREAK
    `-- is_prefix: bool             break comes BEFORE the symbol instead of after

BoundingPoly  (order: top-left, top-right, bottom-right, bottom-left)
|-- vertices[]: Vertex                     {x: int, y: int}      IMAGES only (pixels)
`-- normalized_vertices[]: NormalizedVertex {x: float, y: float}  PDF/TIFF only ([0, 1])


4. LIMITS
--------------------------------------------------------------------------
- batch_annotate_files processes at most 5 pages/frames per file. AnnotateFileRequest.pages
  chooses WHICH 5 (we never set it, so pages 6+ of a long scan are silently dropped;
  file_response.total_pages still reports the true length).
- files.annotate accepts only application/pdf, image/tiff, image/gif.
- Over 5 pages needs async_batch_annotate_files, which writes JSON to a GCS bucket.
- Inline content (bytes) works for batch_annotate_files but NOT for the async variant.


5. WHAT _parse_annotation BELOW KEEPS / DROPS
--------------------------------------------------------------------------
Kept: page width/height/confidence, block confidence + block_type + bounding_box,
paragraph text + confidence, word text + confidence, symbol text + confidence +
break_type/break_is_prefix.

bounding_box is emitted in PAGE UNITS for both paths: images populate .vertices (pixels)
directly, PDFs populate .normalized_vertices ([0,1]) which _vertices() multiplies by
page width/height (points).

Spaces are NOT symbols — Vision emits one Symbol per visible glyph only. Whitespace is
carried by property.detected_break on the PRECEDING symbol (is_prefix flips it to the
following one), which _symbol_text() turns back into " " or "\n". That is how paragraph
text gets its spacing; full_text already arrives correctly spaced from Google.

Still dropped: bounding_box on paragraph/symbol (blocks and words keep one), and
detected_languages. Add them if per-symbol highlighting or language routing is needed.

Careful: total_pages in OUR return value counts only pages WITH text (blank pages are
skipped by the `continue` in _detect_pdf), which is NOT the document length.
AnnotateFileResponse.total_pages is the real count, and we do not surface it.
"""


class GoogleCloudVisionAPI:

    @staticmethod
    def _parse_annotation(annotation) -> List[Dict[str, Any]]:
        """Parse a full_text_annotation into the pages/blocks/paragraphs/words structure."""
        pages = []
        for page in annotation.pages:
            page_data = {
                "width": page.width, #whole page width
                "height": page.height, #whole page height
                "confidence": page.confidence, #average confidence for each block 
                "blocks": []
            }
            for block in page.blocks:
                block_data = {
                    "confidence": block.confidence,
                    "block_type": block.block_type.name,
                    "bounding_box": GoogleCloudVisionAPI._vertices(block.bounding_box, page.width, page.height),
                    "paragraphs": []
                }
                for paragraph in block.paragraphs:
                    para_text = "".join(
                        GoogleCloudVisionAPI._symbol_text(symbol)
                        for word in paragraph.words for symbol in word.symbols
                    ).rstrip()
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
                            "bounding_box": GoogleCloudVisionAPI._vertices(word.bounding_box, page.width, page.height),
                            "symbols": [
                                {
                                    "text": symbol.text,
                                    "confidence": symbol.confidence,
                                    "break_type": symbol.property.detected_break.type_.name
                                                  if symbol.property.detected_break.type_ else None,
                                    "break_is_prefix": symbol.property.detected_break.is_prefix,
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
    def _symbol_text(symbol) -> str:
        """The symbol plus the whitespace its detected_break stands for (Vision emits no space symbols)."""
        brk = symbol.property.detected_break
        whitespace = _BREAK_WHITESPACE.get(brk.type_, "")
        return whitespace + symbol.text if brk.is_prefix else symbol.text + whitespace

    @staticmethod
    def _vertices(bounding_box, width: int, height: int) -> List[List[int]]:
        """Box corners in page units. PDFs populate normalized_vertices ([0,1]) instead of vertices."""
        if bounding_box.vertices:
            return [[v.x, v.y] for v in bounding_box.vertices]
        return [[round(v.x * width), round(v.y * height)] for v in bounding_box.normalized_vertices]

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