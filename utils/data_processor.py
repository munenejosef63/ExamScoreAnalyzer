import pandas as pd
import PyPDF2
import io
import re
import streamlit as st
from difflib import SequenceMatcher
import numpy as np

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
        """Process Excel file with multi-sheet support."""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(uploaded_file)
            all_sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name, engine='openpyxl')
                all_sheets[sheet_name] = self._clean_dataframe(df)
            
            # If only one sheet, return it directly
            if len(all_sheets) == 1:
                return list(all_sheets.values())[0]
            
            # Return all sheets for multi-sheet handling
            return all_sheets
            
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
        
        # Convert numeric columns more carefully
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric
                numeric_col = pd.to_numeric(df[col], errors='coerce')
                if not numeric_col.isna().all():
                    # Ensure proper float conversion to avoid Arrow issues
                    df[col] = numeric_col.astype('float64')
        
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
    
    def consolidate_student_data(self, sheets_data, similarity_threshold=0.8):
        """
        Consolidate data from multiple sheets, matching similar student names.
        
        Args:
            sheets_data: Dictionary of sheet_name -> DataFrame
            similarity_threshold: Minimum similarity score for name matching
            
        Returns:
            dict: Consolidated student data with subjects and total scores
        """
        consolidated_data = {}
        all_students = {}
        
        # First pass: collect all unique student names
        for sheet_name, df in sheets_data.items():
            if 'student_name' in df.columns or 'name' in df.columns:
                name_col = 'student_name' if 'student_name' in df.columns else 'name'
                for name in df[name_col].dropna():
                    name = str(name).strip()
                    if name:
                        all_students[name] = name
        
        # Create consolidated student list with name matching
        consolidated_names = {}
        used_names = set()
        
        for name in all_students.keys():
            if name in used_names:
                continue
                
            # Find similar names
            similar_names = [name]
            for other_name in all_students.keys():
                if other_name != name and other_name not in used_names:
                    similarity = self._calculate_name_similarity(name, other_name)
                    if similarity >= similarity_threshold:
                        similar_names.append(other_name)
            
            # Use the most common/longest name as canonical
            canonical_name = max(similar_names, key=len)
            for similar_name in similar_names:
                consolidated_names[similar_name] = canonical_name
                used_names.add(similar_name)
        
        # Second pass: consolidate data by canonical names
        student_data = {}
        
        for sheet_name, df in sheets_data.items():
            subject_name = sheet_name.replace('_', ' ').title()
            
            if 'student_name' in df.columns or 'name' in df.columns:
                name_col = 'student_name' if 'student_name' in df.columns else 'name'
                score_col = None
                
                # Find score column
                for col in df.columns:
                    if col.lower() in ['marks', 'score', 'grade', 'total', 'points']:
                        score_col = col
                        break
                
                if score_col:
                    for _, row in df.iterrows():
                        original_name = str(row[name_col]).strip()
                        canonical_name = consolidated_names.get(original_name, original_name)
                        score = row[score_col]
                        
                        if pd.notna(score) and canonical_name:
                            if canonical_name not in student_data:
                                student_data[canonical_name] = {}
                            student_data[canonical_name][subject_name] = float(score)
        
        # Calculate total scores
        for student, subjects in student_data.items():
            student_data[student]['Total'] = sum(subjects.values())
        
        return student_data
    
    def _calculate_name_similarity(self, name1, name2):
        """Calculate similarity between two names."""
        name1 = name1.lower().strip()
        name2 = name2.lower().strip()
        
        # Direct match
        if name1 == name2:
            return 1.0
        
        # Check if one is substring of another
        if name1 in name2 or name2 in name1:
            return 0.9
        
        # Use sequence matcher for overall similarity
        return SequenceMatcher(None, name1, name2).ratio()
    
    def process_multi_sheet_data(self, uploaded_file):
        """
        Process multi-sheet Excel file and return consolidated data.
        
        Returns:
            tuple: (consolidated_student_data, sheet_names, raw_sheets_data)
        """
        try:
            sheets_data = self._process_excel(uploaded_file)
            
            if isinstance(sheets_data, pd.DataFrame):
                # Single sheet
                return None, ['Single Sheet'], {'Single Sheet': sheets_data}
            
            # Multi-sheet processing
            consolidated_data = self.consolidate_student_data(sheets_data)
            sheet_names = list(sheets_data.keys())
            
            return consolidated_data, sheet_names, sheets_data
            
        except Exception as e:
            st.error(f"Error processing multi-sheet data: {str(e)}")
            return None, [], {}
