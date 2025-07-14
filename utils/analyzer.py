import numpy as np
import pandas as pd
from scipy import stats

class ExamAnalyzer:
    """Performs statistical analysis on exam marks."""
    
    def analyze(self, marks):
        """
        Perform comprehensive statistical analysis on marks.
        
        Args:
            marks: List or array of exam marks
            
        Returns:
            dict: Analysis results
        """
        if not marks:
            raise ValueError("No marks provided for analysis")
        
        marks_array = np.array(marks)
        
        # Remove any NaN values
        marks_clean = marks_array[~np.isnan(marks_array)]
        
        if len(marks_clean) == 0:
            raise ValueError("No valid marks found")
        
        results = {
            'count': len(marks_clean),
            'mean': np.mean(marks_clean),
            'median': np.median(marks_clean),
            'mode': self._calculate_mode(marks_clean),
            'std_dev': np.std(marks_clean, ddof=1) if len(marks_clean) > 1 else 0,
            'variance': np.var(marks_clean, ddof=1) if len(marks_clean) > 1 else 0,
            'min': np.min(marks_clean),
            'max': np.max(marks_clean),
            'range': np.max(marks_clean) - np.min(marks_clean),
            'q1': np.percentile(marks_clean, 25),
            'q3': np.percentile(marks_clean, 75),
            'iqr': np.percentile(marks_clean, 75) - np.percentile(marks_clean, 25),
            'skewness': stats.skew(marks_clean),
            'kurtosis': stats.kurtosis(marks_clean),
            'marks': marks_clean.tolist()
        }
        
        # Additional statistics
        results.update(self._calculate_percentiles(marks_clean))
        results.update(self._detect_outliers(marks_clean))
        
        return results
    
    def _calculate_mode(self, marks):
        """Calculate mode of marks."""
        try:
            mode_result = stats.mode(marks, keepdims=False)
            # Check if mode is meaningful (appears more than once)
            if hasattr(mode_result, 'count') and mode_result.count > 1:
                return float(mode_result.mode)
            else:
                return None
        except:
            return None
    
    def _calculate_percentiles(self, marks):
        """Calculate various percentiles."""
        percentiles = {}
        for p in [10, 20, 30, 40, 50, 60, 70, 80, 90, 95, 99]:
            percentiles[f'p{p}'] = np.percentile(marks, p)
        return percentiles
    
    def _detect_outliers(self, marks):
        """Detect outliers using IQR method."""
        q1 = np.percentile(marks, 25)
        q3 = np.percentile(marks, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = marks[(marks < lower_bound) | (marks > upper_bound)]
        
        return {
            'outliers': outliers.tolist(),
            'outlier_count': len(outliers),
            'outlier_percentage': (len(outliers) / len(marks)) * 100,
            'lower_bound': lower_bound,
            'upper_bound': upper_bound
        }
    
    def calculate_pass_fail_stats(self, marks, pass_threshold=50, max_marks=100):
        """
        Calculate pass/fail statistics.
        
        Args:
            marks: List of marks
            pass_threshold: Pass percentage threshold
            max_marks: Maximum possible marks
            
        Returns:
            dict: Pass/fail statistics
        """
        pass_mark = (pass_threshold / 100) * max_marks
        
        passed = sum(1 for mark in marks if mark >= pass_mark)
        failed = len(marks) - passed
        pass_rate = (passed / len(marks)) * 100 if marks else 0
        
        return {
            'pass_mark': pass_mark,
            'passed_count': passed,
            'failed_count': failed,
            'pass_rate': pass_rate,
            'fail_rate': 100 - pass_rate
        }
    
    def calculate_grade_distribution(self, marks, max_marks=100):
        """
        Calculate grade distribution.
        
        Args:
            marks: List of marks
            max_marks: Maximum possible marks
            
        Returns:
            dict: Grade distribution
        """
        grades = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for mark in marks:
            percentage = (mark / max_marks) * 100
            
            if percentage >= 95:
                grades['A+'] += 1
            elif percentage >= 85:
                grades['A'] += 1
            elif percentage >= 75:
                grades['B+'] += 1
            elif percentage >= 65:
                grades['B'] += 1
            elif percentage >= 55:
                grades['C+'] += 1
            elif percentage >= 45:
                grades['C'] += 1
            elif percentage >= 35:
                grades['D'] += 1
            else:
                grades['F'] += 1
        
        # Convert to percentages
        total = len(marks)
        grade_percentages = {grade: (count / total) * 100 for grade, count in grades.items()}
        
        return {
            'counts': grades,
            'percentages': grade_percentages
        }
    
    def performance_insights(self, marks, max_marks=100):
        """
        Generate performance insights.
        
        Args:
            marks: List of marks
            max_marks: Maximum possible marks
            
        Returns:
            list: List of insight strings
        """
        insights = []
        
        if not marks:
            return ["No data available for insights."]
        
        stats = self.analyze(marks)
        
        # Mean performance
        mean_percentage = (stats['mean'] / max_marks) * 100
        if mean_percentage >= 80:
            insights.append("📈 Excellent overall performance! Class average is above 80%.")
        elif mean_percentage >= 70:
            insights.append("👍 Good overall performance. Class average is above 70%.")
        elif mean_percentage >= 60:
            insights.append("📊 Average performance. Room for improvement.")
        else:
            insights.append("⚠️ Below average performance. Consider reviewing teaching methods.")
        
        # Distribution analysis
        if stats['std_dev'] > 15:
            insights.append("📊 High variability in scores. Consider differentiated instruction.")
        elif stats['std_dev'] < 5:
            insights.append("📊 Very consistent performance across students.")
        
        # Skewness analysis
        if abs(stats['skewness']) > 0.5:
            if stats['skewness'] > 0:
                insights.append("📉 Most students scored below average (right-skewed distribution).")
            else:
                insights.append("📈 Most students scored above average (left-skewed distribution).")
        
        # Outlier analysis
        if stats['outlier_percentage'] > 10:
            insights.append(f"⚡ {stats['outlier_percentage']:.1f}% of scores are outliers. Check for data entry errors.")
        
        return insights
