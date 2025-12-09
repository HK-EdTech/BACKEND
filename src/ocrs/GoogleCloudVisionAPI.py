# $300 USD free credit
# Reference link: https://docs.cloud.google.com/vision/docs/handwriting#vision-document-text-detection-python
from google.cloud import vision

class GoogleCloudVisionAPI:
    def detect_document(path):
        client=vision.ImageAnnotatorCleint()