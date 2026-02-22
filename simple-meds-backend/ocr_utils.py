# ocr_utils.py
from PIL import Image, ImageFilter, ImageOps
import pytesseract
import os

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}

def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def preprocess_image_for_ocr(path: str):
    """
    Basic preprocessing for OCR: convert to grayscale, increase contrast, maybe resize.
    """
    im = Image.open(path)
    im = ImageOps.grayscale(im)
    im = im.filter(ImageFilter.MedianFilter())
    w, h = im.size
    # enlarge small images for better OCR
    if max(w, h) < 1500:
        im = im.resize((int(w*1.5), int(h*1.5)))
    return im

def extract_text_from_image(path: str) -> str:
    """
    Using Tesseract to extract text from image at `path`.
    On Windows, you may need to set pytesseract.pytesseract.tesseract_cmd.
    """
    im = preprocess_image_for_ocr(path)
    text = pytesseract.image_to_string(im)
    # basic cleaning
    text = "\n".join([line.strip() for line in text.splitlines() if line.strip()])
    return text