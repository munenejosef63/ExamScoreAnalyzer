import pandas as pd
import numpy as np

class RankingSystem:
    """Handle student ranking and subject-wise analysis"""
    
    def __init__(self):
        pass
    
    def calculate_rankings(self, marks, student_names=None, max_marks=100):
        """
        Calculate student rankings based on marks
        
        Args:
            marks: List of student marks
            student_names: Optional list of student names
            max_marks: Maximum possible marks
            
        Returns:
            list: List of dictionaries with ranking information
        """
        if not marks:
            return []
        
        # Create student data
        students = []
        for i, mark in enumerate(marks):
            name = student_names[i] if student_names and i < len(student_names) and student_names[i] else f"Student {i+1}"
            students.append({
                'name': name,
                'score': float(mark),
                'grade': self._get_letter_grade(mark, max_marks)
            })
        
        # Sort by score (descending)
        students.sort(key=lambda x: x['score'], reverse=True)
        
        # Assign ranks (handle ties)
        rankings = []
        current_rank = 1
        
        for i, student in enumerate(students):
            if i > 0 and students[i-1]['score'] != student['score']:
                current_rank = i + 1
            
            rankings.append({
                'rank': current_rank,
                'student_name': student['name'],
                'score': student['score'],
                'grade': student['grade'],
                'percentage': (student['score'] / max_marks) * 100
            })
        
        return rankings
    
    def calculate_subject_totals(self, subject_data):
        """
        Calculate subject-wise totals and statistics
        
        Args:
            subject_data: Dictionary with subject names as keys and lists of marks as values
            
        Returns:
            dict: Subject-wise analysis data
        """
        if not subject_data:
            return {}
        
        analysis = {}
        
        for subject, marks in subject_data.items():
            if marks:
                valid_marks = [float(mark) for mark in marks if mark is not None and str(mark).replace('.', '').isdigit()]
                
                if valid_marks:
                    analysis[subject] = {
                        'total': sum(valid_marks),
                        'average': np.mean(valid_marks),
                        'highest': max(valid_marks),
                        'lowest': min(valid_marks),
                        'count': len(valid_marks),
                        'std_dev': np.std(valid_marks) if len(valid_marks) > 1 else 0
                    }
        
        return analysis
    
    def create_overall_ranking(self, subject_data, student_names=None):
        """
        Create overall ranking based on total marks across subjects
        
        Args:
            subject_data: Dictionary with subject names as keys and lists of marks as values
            student_names: Optional list of student names
            
        Returns:
            list: Overall ranking based on total marks
        """
        if not subject_data:
            return []
        
        # Get number of students
        num_students = max(len(marks) for marks in subject_data.values()) if subject_data else 0
        
        if num_students == 0:
            return []
        
        # Calculate total marks for each student
        student_totals = []
        
        for i in range(num_students):
            name = student_names[i] if student_names and i < len(student_names) and student_names[i] else f"Student {i+1}"
            total_marks = 0
            subject_count = 0
            
            for subject, marks in subject_data.items():
                if i < len(marks) and marks[i] is not None:
                    try:
                        total_marks += float(marks[i])
                        subject_count += 1
                    except (ValueError, TypeError):
                        continue
            
            if subject_count > 0:
                student_totals.append({
                    'name': name,
                    'total_marks': total_marks,
                    'average': total_marks / subject_count,
                    'subjects_count': subject_count
                })
        
        # Sort by total marks (descending)
        student_totals.sort(key=lambda x: x['total_marks'], reverse=True)
        
        # Assign ranks
        rankings = []
        current_rank = 1
        
        for i, student in enumerate(student_totals):
            if i > 0 and student_totals[i-1]['total_marks'] != student['total_marks']:
                current_rank = i + 1
            
            rankings.append({
                'rank': current_rank,
                'student_name': student['name'],
                'total_marks': student['total_marks'],
                'average': student['average'],
                'subjects_count': student['subjects_count']
            })
        
        return rankings
    
    def create_subject_wise_ranking(self, subject_data, student_names=None, max_marks_per_subject=100):
        """
        Create subject-wise rankings
        
        Args:
            subject_data: Dictionary with subject names as keys and lists of marks as values
            student_names: Optional list of student names
            max_marks_per_subject: Maximum marks per subject
            
        Returns:
            dict: Subject-wise rankings
        """
        subject_rankings = {}
        
        for subject, marks in subject_data.items():
            if marks:
                subject_rankings[subject] = self.calculate_rankings(
                    marks, student_names, max_marks_per_subject
                )
        
        return subject_rankings
    
    def _get_letter_grade(self, mark, max_marks=100):
        """Convert numeric mark to letter grade"""
        percentage = (mark / max_marks) * 100
        
        if percentage >= 95:
            return 'A+'
        elif percentage >= 85:
            return 'A'
        elif percentage >= 75:
            return 'B+'
        elif percentage >= 65:
            return 'B'
        elif percentage >= 55:
            return 'C+'
        elif percentage >= 45:
            return 'C'
        elif percentage >= 35:
            return 'D'
        else:
            return 'F'
    
    def get_class_performance_summary(self, rankings):
        """
        Get class performance summary from rankings
        
        Args:
            rankings: List of ranking dictionaries
            
        Returns:
            dict: Performance summary
        """
        if not rankings:
            return {}
        
        scores = [r['score'] for r in rankings]
        
        return {
            'class_average': np.mean(scores),
            'highest_score': max(scores),
            'lowest_score': min(scores),
            'total_students': len(rankings),
            'top_performer': rankings[0]['student_name'] if rankings else None,
            'grade_distribution': self._calculate_grade_distribution(rankings)
        }
    
    def _calculate_grade_distribution(self, rankings):
        """Calculate grade distribution from rankings"""
        grade_counts = {}
        for ranking in rankings:
            grade = ranking['grade']
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        return grade_counts