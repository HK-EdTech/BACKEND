import sys
from pathlib import Path
from typing import Optional, List, Dict

import pytesseract
from PIL import Image
from pytesseract import Output
from utils.logger import get_logger

logger = get_logger(name=__name__)

class PyTesseractOCR:
    """
    A class for performing OCR using PyTesseract.
    
    This class encapsulates OCR functionality, allowing customization of language,
    Tesseract configuration, and more. Now includes support for confidence scores.
    """
    
    def __init__(self, lang: str = 'eng', config: str = '--psm 3') -> None:
        """
        Initialize the OCR processor.
        
        Args:
            lang (str): Language code for Tesseract (default: 'eng' for English).
            config (str): Tesseract configuration string (default: '--psm 3' for auto page segmentation).
        """
        self.lang = lang
        self.config = config
        logger.info(f"Initialized PyTesseractOCR with lang='{self.lang}' and config='{self.config}'")
    
    def process_image(self, image_path: str) -> Optional[str]:
        """
        Perform basic OCR on the given image file (text only, no confidence).
        
        Args:
            image_path (str): Path to the image file.
        
        Returns:
            Optional[str]: Extracted text, or None if an error occurs.
        """
        try:
            path = Path(image_path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}. Use it to fix the script and re-run.")

            logger.info("Running OCR with PyTesseract...")
            text = pytesseract.image_to_string(image_path, lang=self.lang, config=self.config)
            return text.strip()
        
        except pytesseract.pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found. Ensure it's installed and in PATH.")
            return None
        except Exception as e:
            logger.error(f"Error during OCR: {str(e)}")
            return None
    
    def process_image_with_confidence(
        self, 
        image_path: str, 
        min_confidence: float = 0.0
    ) -> Optional[Dict[str, any]]:
        """
        Perform OCR with detailed output, including confidence scores per word.
        
        Args:
            image_path (str): Path to the image file.
            min_confidence (float): Minimum confidence threshold (0-100) to filter results (default: 0, include all).
        
        Returns:
            Optional[Dict[str, any]]: A dictionary with:
                - 'data': List of dicts (one per word/line) with keys like 'text', 'conf', 'left', 'top', etc.
                - 'average_confidence': Float average of all confidence scores (after filtering).
                - Or None if an error occurs.
        """
        try:
            path = Path(image_path)
            if not path.exists() or not path.is_file():
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            logger.info(f"Loading image: {image_path}")
            image = Image.open(path)
            
            # Optional: Preprocess (uncomment if needed)
            # image = image.convert('L')  # Grayscale
            # image = image.resize((image.width * 2, image.height * 2))  # Upscale
            
            logger.info("Running OCR with PyTesseract (detailed mode)...")
            data = pytesseract.image_to_data(
                image, 
                lang=self.lang, 
                config=self.config, 
                output_type=Output.DICT
            )
            
            # Parse and filter the data
            parsed_data: List[Dict[str, any]] = []
            conf_scores = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if text:  # Skip empty entries
                    conf = float(data['conf'][i])  # Confidence as float
                    if conf >= min_confidence:
                        parsed_data.append({
                            'level': data['level'][i],
                            'page_num': data['page_num'][i],
                            'block_num': data['block_num'][i],
                            'par_num': data['par_num'][i],
                            'line_num': data['line_num'][i],
                            'word_num': data['word_num'][i],
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i],
                            'conf': conf,
                            'text': text
                        })
                        conf_scores.append(conf)
            
            if not conf_scores:
                logger.warning("No text detected with confidence above threshold.")
                return {'data': [], 'average_confidence': 0.0}
            
            avg_conf = sum(conf_scores) / len(conf_scores)
            return {'data': parsed_data, 'average_confidence': avg_conf}
        
        except pytesseract.pytesseract.TesseractNotFoundError:
            logger.error("Tesseract not found. Ensure it's installed and in PATH.")
            return None
        except Exception as e:
            logger.error(f"Error during OCR: {str(e)}")
            return None

    def get_average_confidence(
        self, 
        image_path: str, 
        min_confidence: float = 0.0
    ) -> float:
        """
        Compute and return only the average confidence score for the image.
        
        This is a convenience method that runs OCR and calculates the average
        without returning the full detailed data.
        
        Args:
            image_path (str): Path to the image file.
            min_confidence (float): Minimum confidence threshold for filtering (default: 0).
        
        Returns:
            float: Average confidence score (0-100), or 0.0 if no data or on error.
        """
        result = self.process_image_with_confidence(image_path, min_confidence)
        if result is not None:
            return result['average_confidence']
        return 0.0

if __name__ == "__main__":
    if len(sys.argv) != 2:
        logger.error("Usage: python PyTesseract.py <image_path>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    logger.info(f"Processing: {image_path}\n{'-' * 60}")
    
    # Instantiate the class
    ocr_processor = PyTesseractOCR(lang='eng', config='--psm 3')
    
    # Get detailed results with confidence (e.g., filter below 60 confidence)
    result = ocr_processor.process_image_with_confidence(image_path, min_confidence=60.0)
    
    if result is not None:
        avg_conf = result['average_confidence']
        logger.info(f"Average Confidence: {avg_conf:.2f}")
        
        # Build full text from detailed data
        full_text = " ".join(item['text'] for item in result['data'])
        
        # Log detailed results (optional; comment out if you only want average)
        logger.info("Detailed Results (filtered):")
        for item in result['data']:
            logger.info(f"Text: '{item['text']}' | Conf: {item['conf']:.2f} | Box: ({item['left']}, {item['top']}, {item['width']}, {item['height']})")
        
        logger.info(f"Full Extracted Text:\n{'-' * 60}\n{full_text.strip()}\n{'-' * 60}")
        
        # Print to stdout: Average confidence and full text (easy for scripting)
        print(f"Average Confidence: {avg_conf:.2f}")
    else:
        logger.error("OCR failed. Check logs for details.")
        sys.exit(1)