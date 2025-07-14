import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd

class ExamVisualizer:
    """Creates visualizations for exam analysis."""
    
    def __init__(self):
        self.colors = {
            'primary': '#1f77b4',
            'secondary': '#ff7f0e',
            'success': '#2ca02c',
            'danger': '#d62728',
            'warning': '#ff8c00',
            'info': '#17a2b8'
        }
    
    def create_histogram(self, marks, pass_mark=None):
        """
        Create histogram of marks distribution.
        
        Args:
            marks: List of marks
            pass_mark: Pass threshold line
            
        Returns:
            plotly.graph_objects.Figure
        """
        fig = go.Figure()
        
        # Create histogram
        fig.add_trace(go.Histogram(
            x=marks,
            nbinsx=20,
            name='Score Distribution',
            marker_color=self.colors['primary'],
            opacity=0.7
        ))
        
        # Add pass mark line if provided
        if pass_mark is not None:
            fig.add_vline(
                x=pass_mark,
                line_dash="dash",
                line_color=self.colors['danger'],
                annotation_text=f"Pass Mark: {pass_mark}",
                annotation_position="top"
            )
        
        # Add mean line
        mean_mark = np.mean(marks)
        fig.add_vline(
            x=mean_mark,
            line_dash="dot",
            line_color=self.colors['success'],
            annotation_text=f"Mean: {mean_mark:.1f}",
            annotation_position="bottom"
        )
        
        fig.update_layout(
            title="Score Distribution",
            xaxis_title="Marks",
            yaxis_title="Frequency",
            showlegend=False,
            height=400
        )
        
        return fig
    
    def create_box_plot(self, marks):
        """
        Create box plot for marks.
        
        Args:
            marks: List of marks
            
        Returns:
            plotly.graph_objects.Figure
        """
        fig = go.Figure()
        
        fig.add_trace(go.Box(
            y=marks,
            name='Marks',
            boxpoints='outliers',
            marker_color=self.colors['primary'],
            line_color=self.colors['primary']
        ))
        
        fig.update_layout(
            title="Box Plot - Score Distribution & Outliers",
            yaxis_title="Marks",
            height=400,
            showlegend=False
        )
        
        return fig
    
    def create_grade_distribution(self, grades):
        """
        Create pie chart for grade distribution.
        
        Args:
            grades: Dictionary of grade counts
            
        Returns:
            plotly.graph_objects.Figure
        """
        # Filter out grades with zero counts
        filtered_grades = {k: v for k, v in grades.items() if v > 0}
        
        if not filtered_grades:
            # Create empty chart
            fig = go.Figure()
            fig.add_annotation(
                text="No data available",
                xref="paper", yref="paper",
                x=0.5, y=0.5, xanchor='center', yanchor='middle',
                showarrow=False, font=dict(size=16)
            )
            fig.update_layout(title="Grade Distribution", height=400)
            return fig
        
        fig = go.Figure(data=[go.Pie(
            labels=list(filtered_grades.keys()),
            values=list(filtered_grades.values()),
            hole=0.3,
            marker_colors=px.colors.qualitative.Set3
        )])
        
        fig.update_traces(
            textposition='inside',
            textinfo='percent+label'
        )
        
        fig.update_layout(
            title="Grade Distribution",
            height=400,
            showlegend=True
        )
        
        return fig
    
    def create_performance_summary(self, stats):
        """
        Create summary statistics visualization.
        
        Args:
            stats: Dictionary of statistics
            
        Returns:
            plotly.graph_objects.Figure
        """
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Central Tendency', 'Spread', 'Percentiles', 'Distribution Shape'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "bar"}]]
        )
        
        # Central tendency
        fig.add_trace(
            go.Bar(
                x=['Mean', 'Median', 'Mode'],
                y=[stats['mean'], stats['median'], stats.get('mode', 0) or 0],
                name='Central Tendency',
                marker_color=self.colors['primary']
            ),
            row=1, col=1
        )
        
        # Spread
        fig.add_trace(
            go.Bar(
                x=['Std Dev', 'Variance', 'Range'],
                y=[stats['std_dev'], stats['variance'], stats['range']],
                name='Spread',
                marker_color=self.colors['secondary']
            ),
            row=1, col=2
        )
        
        # Percentiles
        percentiles = ['25th', '50th', '75th', '90th']
        percentile_values = [stats['q1'], stats['median'], stats['q3'], stats.get('p90', 0)]
        fig.add_trace(
            go.Bar(
                x=percentiles,
                y=percentile_values,
                name='Percentiles',
                marker_color=self.colors['success']
            ),
            row=2, col=1
        )
        
        # Distribution shape
        fig.add_trace(
            go.Bar(
                x=['Skewness', 'Kurtosis'],
                y=[stats.get('skewness', 0), stats.get('kurtosis', 0)],
                name='Shape',
                marker_color=self.colors['warning']
            ),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            showlegend=False,
            title_text="Performance Summary Dashboard"
        )
        
        return fig
    
    def calculate_grades(self, marks, max_marks=100):
        """
        Calculate grade distribution from marks.
        
        Args:
            marks: List of marks
            max_marks: Maximum possible marks
            
        Returns:
            dict: Grade counts
        """
        grades = {'A+': 0, 'A': 0, 'B+': 0, 'B': 0, 'C+': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for mark in marks:
            grade = self.get_letter_grade(mark, max_marks)
            grades[grade] += 1
        
        return grades
    
    def get_letter_grade(self, mark, max_marks=100):
        """
        Convert numeric mark to letter grade.
        
        Args:
            mark: Numeric mark
            max_marks: Maximum possible marks
            
        Returns:
            str: Letter grade
        """
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
    
    def create_comparative_analysis(self, marks, benchmarks=None):
        """
        Create comparative analysis chart.
        
        Args:
            marks: List of marks
            benchmarks: Dictionary of benchmark values
            
        Returns:
            plotly.graph_objects.Figure
        """
        if benchmarks is None:
            benchmarks = {
                'National Average': 70,
                'School Target': 75,
                'Previous Year': 68
            }
        
        current_avg = np.mean(marks)
        
        categories = ['Current Class'] + list(benchmarks.keys())
        values = [current_avg] + list(benchmarks.values())
        colors = [self.colors['primary']] + [self.colors['secondary']] * len(benchmarks)
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                marker_color=colors,
                text=[f'{v:.1f}' for v in values],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title="Performance Comparison",
            xaxis_title="Category",
            yaxis_title="Average Score",
            height=400
        )
        
        return fig
