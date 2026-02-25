"""
PDF text extraction and cleaning.
"""
import hashlib
import re
from typing import List, Tuple
import pdfplumber


class PDFExtractor:
    """Extracts and cleans text from PDF files."""
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
    
    def extract_text(self) -> Tuple[str, str]:
        """
        Extract and clean text from PDF.
        
        Returns:
            Tuple of (cleaned_text, content_hash)
        """
        raw_pages = self._extract_raw_text()
        cleaned_text = self._clean_text(raw_pages)
        content_hash = self._compute_hash(cleaned_text)
        return cleaned_text, content_hash
    
    def _extract_raw_text(self) -> List[str]:
        """Extract raw text from each page."""
        pages = []
        with pdfplumber.open(self.pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
        return pages
    
    def _clean_text(self, pages: List[str]) -> str:
        """
        Clean text by removing headers, footers, page numbers, and merging broken lines.
        
        Heuristics:
        - Remove lines with only numbers (page numbers)
        - Remove repeated lines across all pages (headers/footers)
        - Merge lines that don't end with punctuation (broken lines)
        """
        if not pages:
            return ""
        
        # Split each page into lines
        page_lines = [page.split('\n') for page in pages]
        
        # Find repeated lines across pages (headers/footers)
        repeated_lines = self._find_repeated_lines(page_lines)
        
        # Clean each page
        cleaned_lines = []
        for lines in page_lines:
            for line in lines:
                line = line.strip()
                
                # Skip empty lines
                if not line:
                    continue
                
                # Skip lines with only numbers (page numbers)
                if re.match(r'^\d+$', line):
                    continue
                
                # Skip repeated lines (headers/footers)
                if line in repeated_lines:
                    continue
                
                cleaned_lines.append(line)
        
        # Merge broken lines
        merged_text = self._merge_broken_lines(cleaned_lines)
        
        return merged_text
    
    def _find_repeated_lines(self, page_lines: List[List[str]]) -> set:
        """Find lines that appear in multiple pages (likely headers/footers)."""
        if len(page_lines) < 2:
            return set()
        
        # Count occurrences of each line
        line_counts = {}
        for lines in page_lines:
            unique_lines = set(line.strip() for line in lines if line.strip())
            for line in unique_lines:
                line_counts[line] = line_counts.get(line, 0) + 1
        
        # Lines appearing in at least half of the pages are considered repeated
        threshold = max(2, len(page_lines) // 2)
        repeated = {line for line, count in line_counts.items() if count >= threshold}
        
        return repeated
    
    def _merge_broken_lines(self, lines: List[str]) -> str:
        """Merge lines that don't end with sentence-ending punctuation."""
        if not lines:
            return ""
        
        merged = []
        current = lines[0]
        
        for i in range(1, len(lines)):
            # Check if current line ends with sentence-ending punctuation
            if re.search(r'[.!?:;]$', current):
                merged.append(current)
                current = lines[i]
            else:
                # Merge with next line
                current = current + " " + lines[i]
        
        # Add the last accumulated line
        merged.append(current)
        
        return "\n".join(merged)
    
    def _compute_hash(self, text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
