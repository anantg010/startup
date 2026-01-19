from pathlib import Path
from io import BytesIO
import pypdf
import pdfplumber
import logging
import base64
import os
from typing import Dict, List, Optional
try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from ..config import Config

# Suppress pdfminer warning logs (invalid float values, etc.)
logging.getLogger("pdfminer").setLevel(logging.ERROR)


class PDFParser:
    def __init__(self):
        self.max_text_length = 50000  # Max characters to extract
        self.vision_model = "gpt-4o-mini" # Use smaller, effective model as requested
    
    async def extract_text_from_path(self, pdf_file_path: str) -> Dict:
        try:
            # Check if file exists
            file_path = Path(pdf_file_path)
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {pdf_file_path}",
                    "full_text": "",
                    "slides_count": 0,
                    "pages": []
                }
            
            # Use Hybrid Approach
            return await self._extract_hybrid(pdf_path=pdf_file_path)
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading PDF file: {str(e)}",
                "full_text": "",
                "slides_count": 0,
                "pages": []
            }
    
    
    async def extract_text_from_bytes(self, pdf_bytes: bytes) -> Dict:
        try:
           return await self._extract_hybrid(pdf_bytes=pdf_bytes)
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error reading PDF bytes: {str(e)}",
                "full_text": "",
                "slides_count": 0,
                "pages": []
            }

    async def _extract_hybrid(self, pdf_path: str = None, pdf_bytes: bytes = None) -> Dict:
        """
        Hybrid extraction: Iterates through pages.
        If a page has sufficient text -> Use text.
        If a page is mostly image (low text) -> Use OCR (GPT-4o-mini).
        """
        full_text = ""
        pages_data = []
        metadata = {}
        
        try:
            # We need two handles: one for text (pdfplumber) and one for images (fitz)
            # 1. Setup pdfplumber
            plumber_pdf = None
            if pdf_path:
                plumber_pdf = pdfplumber.open(pdf_path)
            else:
                plumber_pdf = pdfplumber.open(BytesIO(pdf_bytes))
                
            # 2. Setup fitz (PyMuPDF)
            fitz_doc = None
            if fitz:
                if pdf_path:
                    fitz_doc = fitz.open(pdf_path)
                else:
                    fitz_doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            # Extract metadata from plumber
            if plumber_pdf.metadata:
                metadata = {
                    "title": plumber_pdf.metadata.get("Title", ""),
                    "author": plumber_pdf.metadata.get("Author", ""),
                    "subject": plumber_pdf.metadata.get("Subject", ""),
                    "creator": plumber_pdf.metadata.get("Creator", "")
                }

            total_pages = len(plumber_pdf.pages)
            print(f"📖 Processing {total_pages} pages (Hybrid Mode: Text + Vision)...")
            
            # Limit pages for Vision to avoid excessive API usage/time
            VISION_PAGE_LIMIT = 15
            vision_pages_count = 0

            for i, page in enumerate(plumber_pdf.pages):
                page_num = i + 1
                page_text = ""
                source = "text"
                
                # 1. Try Text Extraction
                try:
                    page_text = page.extract_text() or ""
                except Exception as e:
                    print(f"⚠️ Page {page_num} text extraction failed: {e}")
                
                # 2. Check density
                # Heuristic: If text is < 80 chars, assume it's an image slide or title only
                if len(page_text.strip()) < 80:
                    if fitz_doc and vision_pages_count < VISION_PAGE_LIMIT:
                        print(f"  Page {page_num} has minimal text ({len(page_text.strip())} chars). Using Vision ({self.vision_model})...")
                        try:
                            ocr_text = await self._ocr_page(fitz_doc, i)
                            if ocr_text:
                                page_text = ocr_text
                                source = "vision"
                                vision_pages_count += 1
                        except Exception as ve:
                             print(f" Vision failed for page {page_num}: {ve}")
                    else:
                        if not fitz:
                             print(f" Page {page_num} has minimal text, but pymupdf is not installed.")
                        elif vision_pages_count >= VISION_PAGE_LIMIT:
                             print(f" Page {page_num} skipped Vision (limit reached).")
                
                # Append result
                full_text += f"\n--- Page {page_num} ({source}) ---\n{page_text}"
                pages_data.append({
                    "page_number": page_num,
                    "text": page_text,
                    "source": source
                })

            # Cleanup
            plumber_pdf.close()
            if fitz_doc:
                fitz_doc.close()
                
            # Limit total text length
            if len(full_text) > self.max_text_length:
                full_text = full_text[:self.max_text_length]
                print(f"⚠️ Text truncated to {self.max_text_length} characters")

            return {
                "success": True,
                "total_pages": len(pages_data),
                "full_text": full_text,
                "metadata": metadata,
                "pages": pages_data
            }

        except Exception as e:
            print(f"❌ Hybrid Extraction Failed: {e}")
            import traceback
            traceback.print_exc()
            return {
                "success": False,
                "error": f"Hybrid Extraction Failed: {str(e)}",
                "full_text": "",
                "slides_count": 0,
                "pages": []
            }

    async def _ocr_page(self, doc, page_index):
        """Helper to OCR a single page from a fitz document"""
        try:
            page = doc[page_index]
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img_data = pix.tobytes("png")
            base64_image = base64.b64encode(img_data).decode('utf-8')
            
            llm = ChatOpenAI(model=self.vision_model, max_tokens=1000, api_key=Config.OPENAI_API_KEY)
            
            messages = [
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Extract all text from this slide. Preserve layout structure like bullet points and headers."},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{base64_image}"
                            }
                        }
                    ]
                )
            ]
            response = await llm.ainvoke(messages)
            return response.content
        except Exception as e:
            print(f"OCR Error: {e}")
            return None

    # Keeping legacy methods as fallbacks or utilities if needed, but not used by main flow anymore
    async def _extract_text_with_vision(self, pdf_file_path: str = None, pdf_bytes: bytes = None) -> Dict:
        """Deprecated: Use _extract_hybrid instead"""
        return await self._extract_hybrid(pdf_path=pdf_file_path, pdf_bytes=pdf_bytes)
    
    
    async def extract_page_text(self, pdf_file_path: str, page_number: int) -> Dict:
        """
        Extract text from a specific page
        
        Args:
            pdf_file_path: Path to PDF file
            page_number: Page number (1-indexed)
            
        Returns:
            Dict with page text
            
        Example:
            result = await parser.extract_page_text("./pitch.pdf", 1)
            print(result["text"])  # Text from page 1
        """
        try:
            with pdfplumber.open(pdf_file_path) as pdf:
                if page_number < 1 or page_number > len(pdf.pages):
                    return {
                        "success": False,
                        "error": f"Page {page_number} out of range (1-{len(pdf.pages)})",
                        "text": ""
                    }
                
                page = pdf.pages[page_number - 1]
                page_text = page.extract_text()
                
                return {
                    "success": True,
                    "page_number": page_number,
                    "text": page_text
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error extracting page: {str(e)}",
                "text": ""
            }
    
    
    async def get_pdf_info(self, pdf_file_path: str) -> Dict:
        """
        Get information about PDF without extracting all text
        
        Args:
            pdf_file_path: Path to PDF file
            
        Returns:
            Dict with PDF info
            
        Example:
            info = await parser.get_pdf_info("./pitch.pdf")
            print(info["total_pages"])
        """
        try:
            with pdfplumber.open(pdf_file_path) as pdf:
                return {
                    "success": True,
                    "total_pages": len(pdf.pages),
                    "metadata": pdf.metadata,
                    "has_text": True
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Error getting PDF info: {str(e)}",
                "total_pages": 0
            }
    
    
    def extract_key_phrases(self, text: str, num_phrases: int = 10) -> List[str]:
        """
        Extract potential key phrases from PDF text
        Simple extraction based on line breaks and capitalization
        
        Args:
            text: Extracted PDF text
            num_phrases: Number of phrases to extract
            
        Returns:
            List of key phrases
        """
        try:
            # Split by line breaks
            lines = text.split('\n')
            
            # Filter potential key phrases
            # (lines that are not too long and have capital letters)
            key_phrases = []
            for line in lines:
                line = line.strip()
                # Check if line looks like a key phrase
                if (2 < len(line) < 100 and 
                    line[0].isupper() and 
                    not line.endswith(':') and
                    line not in key_phrases):
                    key_phrases.append(line)
                
                if len(key_phrases) >= num_phrases:
                    break
            
            return key_phrases
        
        except Exception as e:
            print(f"Error extracting key phrases: {str(e)}")
            return []
    
    
    def split_text_into_chunks(self, text: str, chunk_size: int = 2000, overlap: int = 200) -> List[str]:
        """
        Split extracted text into chunks for processing
        Useful for sending to LLM in smaller pieces
        
        Args:
            text: Full extracted text
            chunk_size: Size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
            
        Example:
            chunks = parser.split_text_into_chunks(full_text, chunk_size=2000)
            for chunk in chunks:
                # Process each chunk
        """
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
        
        return chunks