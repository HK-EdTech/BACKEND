import easyocr
import numpy as np
from utils.logger import get_logger
import sys

logger = get_logger(name=__name__)

class EasyOCRProcessor:
    def __init__(self, languages=['en'], gpu=False):
        """
        Initialize the EasyOCR reader.
        
        :param languages: List of languages to support (e.g., ['en', 'fr'] for English and French).
        :param gpu: Set to True to use GPU if available (requires CUDA).
        """
        self.reader = easyocr.Reader(languages, gpu=gpu)
    
    def process_image(self, image_path):
        """
        Process an image file to extract text using OCR.
        
        :param image_path: Path to the image file (e.g., 'path/to/image.jpg').
        :return: Tuple of (average_confidence, detected_texts)
            - average_confidence: Float representing the average confidence score (0 to 1).
            - detected_texts: List of strings, each being a detected text snippet.
        """
        # Run OCR on the image
        results = self.reader.readtext(image_path)
        
        if not results:
            return 0.0, []  # No detections
        
        # Extract confidences and texts
        confidences = [result[2] for result in results]  # Confidence is the 3rd element in each result tuple
        texts = [result[1] for result in results]       # Text is the 2nd element
        
        # Compute average confidence
        avg_confidence = np.mean(confidences)
        
        return avg_confidence, texts 

# Example usage (uncomment to test):
if __name__ == "__main__":
    processor = EasyOCRProcessor(languages=['en'], gpu=False)
    image_path = sys.argv[1]
    avg_conf, texts = processor.process_image(image_path=image_path)
    logger.info(f"Average Confidence: {avg_conf}")
    logger.info(f"Detected Texts: {texts}")