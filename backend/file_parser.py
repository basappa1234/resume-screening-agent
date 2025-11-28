"""
File parsing utilities for resume and job description files
Supports PDF, DOCX, and TXT formats
"""

import os
from typing import Optional
import PyPDF2
from docx import Document


class FileParser:
    """Parse various file formats to extract text content"""
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error parsing PDF: {str(e)}")
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """
        Extract text from DOCX file
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            doc = Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text.strip()
        except Exception as e:
            raise ValueError(f"Error parsing DOCX: {str(e)}")
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """
        Read text from TXT file
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read().strip()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read().strip()
        except Exception as e:
            raise ValueError(f"Error parsing TXT: {str(e)}")
    
    @staticmethod
    def parse_file(file_path: str) -> str:
        """
        Parse file based on extension
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file format is not supported
        """
        if not os.path.exists(file_path):
            raise ValueError(f"File not found: {file_path}")
        
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        if ext == '.pdf':
            return FileParser.parse_pdf(file_path)
        elif ext in ['.docx', '.doc']:
            return FileParser.parse_docx(file_path)
        elif ext == '.txt':
            return FileParser.parse_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}. Supported formats: PDF, DOCX, TXT")


def extract_resume_info_from_text(text: str, filename: str) -> dict:
    """
    Extract basic resume information from text
    Returns a dictionary with resume data
    
    Args:
        text: Resume text content
        filename: Original filename
        
    Returns:
        Dictionary with resume information
    """
    # For now, we'll return the text as-is
    # The AI will parse the structure
    return {
        "id": filename.replace('.', '_'),
        "name": "Candidate",  # Will be extracted by AI
        "email": "",
        "phone": "",
        "skills": [],
        "experience": [],
        "education": [],
        "summary": text[:500] if len(text) > 500 else text,  # First 500 chars
        "full_text": text
    }


def extract_job_description_from_text(text: str) -> dict:
    """
    Extract job description information from text
    
    Args:
        text: Job description text content
        
    Returns:
        Dictionary with job description information
    """
    return {
        "title": "Position",  # Will be extracted by AI
        "company": "Company",
        "required_skills": [],
        "preferred_skills": [],
        "experience_years": 0,
        "responsibilities": [],
        "qualifications": [],
        "description": text,
        "full_text": text
    }
