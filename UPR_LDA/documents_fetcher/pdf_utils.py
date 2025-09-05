import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image
import asyncio

class PdfUtils:
    @staticmethod
    async def pdf_to_text(pdf_bytes: bytes) -> str:
        # Convert PDF bytes to images
        images = await asyncio.to_thread(convert_from_bytes, pdf_bytes)
        text = ''
        for img in images:
            # OCR each image (page)
            page_text = await asyncio.to_thread(pytesseract.image_to_string, img)
            text += page_text + '\n'
        return text