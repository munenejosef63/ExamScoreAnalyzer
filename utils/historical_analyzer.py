import pandas as pd
import numpy as np
from datetime import datetime
import streamlit as st

class HistoricalAnalyzer:
    """Handle historical exam comparisons and student progress tracking"""
    
    def __init__(self):
        self.historical_data = {}
        if 'historical_exams' not in st.session_state:
            st.session_state.historical_exams = {}
    
    def store_exam_data(self, exam_name, student_data, exam_date=None):
        """
        Store exam data for historical comparison
        
        Args:
            exam_name: Name/identifier for the exam
            student_data: Dictionary of student -> {subject: score, Total: score}
            exam_date: Date of the exam (defaults to current date)
        """
        if exam_date is None:
            exam_date = datetime.now().strftime('%Y-%m-%d')
        
        exam_record = {
            'date': exam_date,
            'student_data': student_data,
            'stored_at': datetime.now().isoformat()
        }
        
        st.session_state.historical_exams[exam_name] = exam_record
        return True
    
    def get_stored_exams(self):
        """Get list of stored exam names"""
        return list(st.session_state.historical_exams.keys())
    
    def compare_student_progress(self, current_student_data, previous_exam_name):
        """
        Compare current exam with previous exam for individual students
        
        Args:
            current_student_data: Current exam data
            previous_exam_name: Name of previous exam to compare with
            
        Returns:
            dict: Student progress comparison data
        """
        if previous_exam_name not in st.session_state.historical_exams:
            return None
        
        previous_data = st.session_state.historical_exams[previous_exam_name]['student_data']
        progress_data = {}
        
        for student, current_scores in current_student_data.items():
            if student in previous_data:
                student_progress = {
                    'student_name': student,
                    'subjects': {},
                    'total_change': 0,
                    'improved_subjects': [],
                    'declined_subjects': [],
                    'overall_trend': 'stable'
                }
                
                # Compare subject-wise
                for subject, current_score in current_scores.items():
                    if subject in previous_data[student]:
                        previous_score = previous_data[student][subject]
                        change = current_score - previous_score
                        percentage_change = (change / previous_score) * 100 if previous_score > 0 else 0
                        
                        student_progress['subjects'][subject] = {
                            'current': current_score,
                            'previous': previous_score,
                            'change': change,
                            'percentage_change': percentage_change
                        }
                        
                        if subject == 'Total':
                            student_progress['total_change'] = change
                            student_progress['total_percentage_change'] = percentage_change
                        elif change > 0:
                            student_progress['improved_subjects'].append(subject)
                        elif change < 0:
                            student_progress['declined_subjects'].append(subject)
                
                # Determine overall trend
                if student_progress['total_change'] > 5:
                    student_progress['overall_trend'] = 'improved'
                elif student_progress['total_change'] < -5:
                    student_progress['overall_trend'] = 'declined'
                
                progress_data[student] = student_progress
        
        return progress_data
    
    def calculate_subject_averages_comparison(self, current_student_data, previous_exam_name):
        """
        Compare subject averages between current and previous exam
        
        Returns:
            dict: Subject-wise average comparisons
        """
        if previous_exam_name not in st.session_state.historical_exams:
            return None
        
        previous_data = st.session_state.historical_exams[previous_exam_name]['student_data']
        
        # Calculate current averages
        current_subjects = {}
        for student, scores in current_student_data.items():
            for subject, score in scores.items():
                if subject not in current_subjects:
                    current_subjects[subject] = []
                current_subjects[subject].append(score)
        
        current_averages = {subject: np.mean(scores) for subject, scores in current_subjects.items()}
        
        # Calculate previous averages
        previous_subjects = {}
        for student, scores in previous_data.items():
            for subject, score in scores.items():
                if subject not in previous_subjects:
                    previous_subjects[subject] = []
                previous_subjects[subject].append(score)
        
        previous_averages = {subject: np.mean(scores) for subject, scores in previous_subjects.items()}
        
        # Compare averages
        comparison = {}
        for subject in current_averages:
            if subject in previous_averages:
                current_avg = current_averages[subject]
                previous_avg = previous_averages[subject]
                change = current_avg - previous_avg
                percentage_change = (change / previous_avg) * 100 if previous_avg > 0 else 0
                
                comparison[subject] = {
                    'current_average': current_avg,
                    'previous_average': previous_avg,
                    'change': change,
                    'percentage_change': percentage_change,
                    'trend': 'improved' if change > 0 else 'declined' if change < 0 else 'stable'
                }
        
        return comparison
    
    def get_subject_leaders(self, student_data, exclude_total=True):
        """
        Find students leading in each subject
        
        Returns:
            dict: Subject -> list of top 3 students
        """
        subject_leaders = {}
        
        # Collect all subjects
        all_subjects = set()
        for student_scores in student_data.values():
            all_subjects.update(student_scores.keys())
        
        if exclude_total:
            all_subjects.discard('Total')
        
        # Find leaders for each subject
        for subject in all_subjects:
            subject_scores = []
            for student, scores in student_data.items():
                if subject in scores:
                    subject_scores.append((student, scores[subject]))
            
            # Sort by score (highest first) and get top 3
            subject_scores.sort(key=lambda x: x[1], reverse=True)
            subject_leaders[subject] = subject_scores[:3]
        
        return subject_leaders
    
    def get_overall_top_students(self, student_data, top_n=3):
        """
        Get top N students based on total marks
        
        Returns:
            list: Top students with their scores
        """
        total_scores = []
        for student, scores in student_data.items():
            if 'Total' in scores:
                total_scores.append((student, scores['Total']))
        
        total_scores.sort(key=lambda x: x[1], reverse=True)
        return total_scores[:top_n]
    
    def create_comprehensive_ranking(self, student_data):
        """
        Create comprehensive ranking with detailed metrics
        
        Returns:
            list: Ranked students with detailed information
        """
        rankings = []
        
        # Calculate additional metrics for each student
        for student, scores in student_data.items():
            if 'Total' in scores:
                total_score = scores['Total']
                subject_scores = {k: v for k, v in scores.items() if k != 'Total'}
                
                ranking_data = {
                    'student_name': student,
                    'total_score': total_score,
                    'subject_count': len(subject_scores),
                    'average_per_subject': total_score / len(subject_scores) if subject_scores else 0,
                    'best_subject': max(subject_scores.items(), key=lambda x: x[1]) if subject_scores else None,
                    'worst_subject': min(subject_scores.items(), key=lambda x: x[1]) if subject_scores else None,
                    'subject_scores': subject_scores
                }
                
                rankings.append(ranking_data)
        
        # Sort by total score
        rankings.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Add rank numbers
        for i, ranking in enumerate(rankings):
            ranking['rank'] = i + 1
        
        return rankings
    
    def get_improvement_insights(self, progress_data):
        """
        Generate insights about student improvements
        
        Returns:
            dict: Various improvement insights
        """
        if not progress_data:
            return {}
        
        insights = {
            'most_improved': None,
            'most_declined': None,
            'consistent_performers': [],
            'subject_improvements': {},
            'overall_class_trend': 'stable'
        }
        
        # Find most improved and declined
        max_improvement = float('-inf')
        max_decline = float('inf')
        
        total_changes = []
        
        for student, data in progress_data.items():
            total_change = data.get('total_change', 0)
            total_changes.append(total_change)
            
            if total_change > max_improvement:
                max_improvement = total_change
                insights['most_improved'] = (student, total_change)
            
            if total_change < max_decline:
                max_decline = total_change
                insights['most_declined'] = (student, total_change)
            
            # Consistent performers (small change)
            if abs(total_change) <= 5:
                insights['consistent_performers'].append(student)
        
        # Overall class trend
        if total_changes:
            avg_change = np.mean(total_changes)
            if avg_change > 2:
                insights['overall_class_trend'] = 'improving'
            elif avg_change < -2:
                insights['overall_class_trend'] = 'declining'
        
        return insights