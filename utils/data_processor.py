import pandas as pd
import PyPDF2
import io
import re
import streamlit as st

class DataProcessor:
    """Handles processing of uploaded files and extracting exam marks."""
    
    def process_file(self, uploaded_file):
        """
        Process uploaded file and extract marks data.
        
        Args:
            uploaded_file: Streamlit uploaded file object
            
        Returns:
            pandas.DataFrame: Processed data
        """
        file_type = uploaded_file.type
        
        try:
            if file_type == "text/csv":
                return self._process_csv(uploaded_file)
            elif file_type in ["application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                              "application/vnd.ms-excel"]:
                return self._process_excel(uploaded_file)
            elif file_type == "application/pdf":
                return self._process_pdf(uploaded_file)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def _process_csv(self, uploaded_file):
        """Process CSV file."""
        try:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding)
                    return self._clean_dataframe(df)
                except UnicodeDecodeError:
                    continue
            
            raise ValueError("Could not decode CSV file with any supported encoding")
            
        except Exception as e:
            raise Exception(f"Error reading CSV: {str(e)}")
    
    def _process_excel(self, uploaded_file):
        """Process Excel file."""
        try:
            # Read Excel file
            df = pd.read_excel(uploaded_file, engine='openpyxl')
            return self._clean_dataframe(df)
            
        except Exception as e:
            raise Exception(f"Error reading Excel file: {str(e)}")
    
    def _process_pdf(self, uploaded_file):
        """Process PDF file and extract numeric data."""
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            text = ""
            
            # Extract text from all pages
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            if not text.strip():
                raise Exception("Could not extract text from PDF")
            
            # Extract numbers from text
            numbers = self._extract_numbers_from_text(text)
            
            if not numbers:
                raise Exception("No numeric data found in PDF")
            
            # Create DataFrame
            df = pd.DataFrame({'marks': numbers})
            return df
            
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    def _extract_numbers_from_text(self, text):
        """Extract numeric values from text."""
        # Find all numbers (including decimals)
        number_pattern = r'\b\d+(?:\.\d+)?\b'
        numbers = re.findall(number_pattern, text)
        
        # Convert to float and filter reasonable exam scores (0-100 range typically)
        numeric_values = []
        for num in numbers:
            try:
                val = float(num)
                # Filter values that could be exam scores (adjust range as needed)
                if 0 <= val <= 200:  # Allowing up to 200 for bonus marks
                    numeric_values.append(val)
            except ValueError:
                continue
        
        return numeric_values
    
    def _clean_dataframe(self, df):
        """Clean and validate DataFrame."""
        if df.empty:
            raise Exception("File is empty")
        
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        # Convert numeric columns
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if not numeric_col.isna().all():
                    df[col] = numeric_col
        
        return df
    
    def validate_marks_data(self, marks, min_val=0, max_val=100):
        """
        Validate marks data.
        
        Args:
            marks: List or Series of marks
            min_val: Minimum valid mark
            max_val: Maximum valid mark
            
        Returns:
            tuple: (valid_marks, invalid_count)
        """
        if not marks:
            return [], 0
        
        valid_marks = []
        invalid_count = 0
        
        for mark in marks:
            try:
                mark_val = float(mark)
                if min_val <= mark_val <= max_val:
                    valid_marks.append(mark_val)
                else:
                    invalid_count += 1
            except (ValueError, TypeError):
                invalid_count += 1
        
        return valid_marks, invalid_count
