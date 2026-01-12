"""
PDF text extraction using PyPDF2 and pdfplumber.
Falls back to alternative methods if primary extraction fails.
"""

from typing import List, Dict, Optional
from pathlib import Path
import PyPDF2
import pdfplumber
from utils.logger import get_logger

logger = get_logger(__name__)


class PDFExtractor:
    """Extract text from PDF files with fallback mechanisms."""
    
    def extract_text(self, pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF with page-level metadata.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of dicts with 'page_number' and 'text' keys
        """
        logger.info("extracting_pdf", path=pdf_path)
        
        # Try pdfplumber first (better text extraction)
        try:
            pages = self._extract_with_pdfplumber(pdf_path)
            if pages and any(p['text'].strip() for p in pages):
                logger.info("extraction_successful", method="pdfplumber", pages=len(pages))
                return pages
        except Exception as e:
            logger.warning("pdfplumber_failed", error=str(e))
        
        # Fallback to PyPDF2
        try:
            pages = self._extract_with_pypdf2(pdf_path)
            if pages and any(p['text'].strip() for p in pages):
                logger.info("extraction_successful", method="pypdf2", pages=len(pages))
                return pages
        except Exception as e:
            logger.error("pypdf2_failed", error=str(e))
            raise RuntimeError(f"Failed to extract text from PDF: {e}")
        
        raise RuntimeError("No text extracted from PDF")
    
    def _extract_with_pdfplumber(self, pdf_path: str) -> List[Dict[str, any]]:
        """Extract text using pdfplumber."""
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                pages.append({
                    'page_number': i + 1,
                    'text': text,
                })
        return pages
    
    def _extract_with_pypdf2(self, pdf_path: str) -> List[Dict[str, any]]:
        """Extract text using PyPDF2."""
        pages = []
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                pages.append({
                    'page_number': i + 1,
                    'text': text,
                })
        return pages
