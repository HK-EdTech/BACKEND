#Ref: https://docs.cloud.google.com/vision/docs/handwriting#vision-document-text-detection-python
import sys
import json
from pathlib import Path
from typing import Dict, Any
import pandas as pd
from datetime import datetime

from models.GoogleCloudVisionAPI import GoogleCloudVisionAPI
from models.EasyOCR import EasyOCRProcessor
from models.PyTesseract import PyTesseractOCR
from utils.logger import get_logger

logger = get_logger(name=__name__)


class OCRComparator:
    """
    Compare all three OCR models (Google Cloud Vision, EasyOCR, PyTesseract)
    on the same image and aggregate confidence scores.
    """
    
    def __init__(self, image_path: str, output_dir: str = "ocr_results"):
        """
        Initialize the comparator.
        
        Args:
            image_path: Path to the image to process
            output_dir: Directory to save results (will be created if not exists)
        """
        self.image_path = image_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
    
    def run_all(self, easy_ocr_langs: list = None, pytesseract_lang: str = "eng") -> Dict[str, Any]:
        """Run all three OCR models and collect confidence scores."""
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing: {self.image_path}")
        logger.info(f"{'='*60}\n")
        
        # Google Cloud Vision
        try:
            logger.info("Running Google Cloud Vision API...")
            result = GoogleCloudVisionAPI.detect_document(self.image_path)
            confidence = result.get("average_confidence", 0.0)
            self.results["GoogleCloudVision"] = {
                "confidence": confidence,
                "full_text": result.get("full_text", ""),
                "status": "success"
            }
            logger.info(f"✓ Google Cloud Vision: {confidence:.4f}")
        except Exception as e:
            logger.error(f"✗ Google Cloud Vision failed: {e}")
            self.results["GoogleCloudVision"] = {"confidence": 0.0, "status": f"error: {str(e)}"}
        
        # EasyOCR
        try:
            logger.info("Running EasyOCR...")
            processor = EasyOCRProcessor(languages=easy_ocr_langs or ["en"], gpu=False)
            avg_confidence, texts = processor.process_image(self.image_path)
            self.results["EasyOCR"] = {
                "confidence": avg_confidence,
                "full_text": " ".join(texts),
                "status": "success"
            }
            logger.info(f"✓ EasyOCR: {avg_confidence:.4f}")
        except Exception as e:
            logger.error(f"✗ EasyOCR failed: {e}")
            self.results["EasyOCR"] = {"confidence": 0.0, "status": f"error: {str(e)}"}
        
        # PyTesseract
        try:
            logger.info("Running PyTesseract...")
            processor = PyTesseractOCR(lang=pytesseract_lang)
            result = processor.process_image_with_confidence(self.image_path, min_confidence=0.0)
            
            if result is None:
                raise Exception("PyTesseract returned None")
            
            confidence = result.get("average_confidence", 0.0)
            full_text = " ".join([item["text"] for item in result.get("data", [])])
            
            self.results["PyTesseract"] = {
                "confidence": confidence,
                "full_text": full_text,
                "status": "success"
            }
            logger.info(f"✓ PyTesseract: {confidence:.4f}")
        except Exception as e:
            logger.error(f"✗ PyTesseract failed: {e}")
            self.results["PyTesseract"] = {"confidence": 0.0, "status": f"error: {str(e)}"}
        
        return self.results
    
    def export_to_csv(self, filename: str = None) -> str:
        """
        Export results to a pandas-readable CSV file.
        
        Args:
            filename: Output filename (default: ocr_comparison_TIMESTAMP.csv)
        
        Returns:
            Path to the generated CSV file
        """
        if not self.results:
            logger.warning("No results to export. Run run_all() first.")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ocr_comparison_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Prepare data for DataFrame
        data = []
        image_name = Path(self.image_path).name
        
        for model_name, model_data in self.results.items():
            data.append({
                "image_file": image_name,
                "ocr_model": model_name,
                "confidence_score": model_data.get("confidence", 0.0),
                "status": model_data.get("status", "unknown"),
                "extracted_text_preview": model_data.get("full_text", "")[:100],  # First 100 chars
                "timestamp": datetime.now().isoformat()
            })
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding="utf-8")
        logger.info(f"\n✓ Results exported to: {output_path}")
        
        return str(output_path)
    
    def export_to_json(self, filename: str = None) -> str:
        """
        Export full results to JSON for detailed inspection.
        
        Args:
            filename: Output filename (default: ocr_comparison_TIMESTAMP.json)
        
        Returns:
            Path to the generated JSON file
        """
        if not self.results:
            logger.warning("No results to export. Run run_all() first.")
            return None
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ocr_comparison_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        full_results = {
            "image_file": str(self.image_path),
            "timestamp": datetime.now().isoformat(),
            "models": self.results
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(full_results, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✓ Detailed results exported to: {output_path}")
        return str(output_path)
    
    def print_summary(self) -> None:
        """Print a summary table of all results."""
        if not self.results:
            logger.warning("No results. Run run_all() first.")
            return
        
        logger.info("\n" + "="*80)
        logger.info("OCR COMPARISON SUMMARY")
        logger.info("="*80)
        
        for model_name, model_data in self.results.items():
            confidence = model_data.get("confidence", 0.0)
            status = model_data.get("status", "unknown")
            logger.info(f"  {model_name:20} | Confidence: {confidence:8.4f} | Status: {status}")
        
        # Calculate average and best model
        successful_models = {k: v for k, v in self.results.items() if v.get("status") == "success"}
        if successful_models:
            avg_confidence = sum(v["confidence"] for v in successful_models.values()) / len(successful_models)
            best_model = max(successful_models.items(), key=lambda x: x[1]["confidence"])
            logger.info("="*80)
            logger.info(f"  Average Confidence: {avg_confidence:.4f}")
            logger.info(f"  Best Model: {best_model[0]} ({best_model[1]['confidence']:.4f})")
        logger.info("="*80 + "\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        logger.info("Usage: python BestOCR.py <path-to-image>")
        logger.info("Example: python BestOCR.py ./images/sample.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    # Initialize comparator
    comparator = OCRComparator(image_path, output_dir="ocr_results")
    
    # Run all models
    comparator.run_all()
    
    # Print summary
    comparator.print_summary()
    
    # Export results
    csv_path = comparator.export_to_csv()
    json_path = comparator.export_to_json()
    
    logger.info(f"CSV output: {csv_path}")
    logger.info(f"JSON output: {json_path}")