from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from datetime import datetime
import io

class PDFGenerator:
    """Generate PDF reports for exam analysis"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # Center alignment
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='BodyText',
            parent=self.styles['BodyText'],
            fontSize=11,
            spaceAfter=6
        ))
    
    def generate_analysis_report(self, results, marks, student_info, rankings, subject_totals, pass_threshold=50, max_marks=100):
        """
        Generate comprehensive PDF analysis report
        
        Args:
            results: Analysis results dictionary
            marks: List of student marks
            student_info: Student information dictionary
            rankings: Student rankings data
            subject_totals: Subject-wise totals if available
            pass_threshold: Pass percentage threshold
            max_marks: Maximum possible marks
            
        Returns:
            bytes: PDF content as bytes
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        story = []
        
        # Title and header information
        story.append(Paragraph("Exam Analysis Report", self.styles['CustomTitle']))
        story.append(Spacer(1, 12))
        
        # Class information
        if student_info:
            class_data = []
            if student_info.get('exam_name'):
                class_data.append(['Exam:', student_info['exam_name']])
            if student_info.get('class_name'):
                class_data.append(['Class:', student_info['class_name']])
            if student_info.get('grade'):
                class_data.append(['Grade:', student_info['grade']])
            if student_info.get('stream'):
                class_data.append(['Stream:', student_info['stream']])
            if student_info.get('teacher_name'):
                class_data.append(['Teacher:', student_info['teacher_name']])
            if student_info.get('exam_date'):
                class_data.append(['Date:', str(student_info['exam_date'])])
            
            if class_data:
                class_table = Table(class_data, colWidths=[1.5*inch, 3*inch])
                class_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(class_table)
                story.append(Spacer(1, 20))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", self.styles['SectionHeader']))
        
        stats_data = [
            ['Metric', 'Value'],
            ['Total Students', str(results['count'])],
            ['Average Score', f"{results['mean']:.2f}"],
            ['Median Score', f"{results['median']:.2f}"],
            ['Highest Score', f"{results['max']:.2f}"],
            ['Lowest Score', f"{results['min']:.2f}"],
            ['Standard Deviation', f"{results['std_dev']:.2f}"],
            ['Pass Rate', f"{self._calculate_pass_rate(marks, pass_threshold, max_marks):.1f}%"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 2*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(stats_table)
        story.append(Spacer(1, 20))
        
        # Student Rankings
        if rankings:
            story.append(Paragraph("Student Rankings", self.styles['SectionHeader']))
            self._add_rankings_table(story, rankings)
            story.append(Spacer(1, 20))
        
        # Subject-wise Analysis
        if subject_totals:
            story.append(Paragraph("Subject-wise Analysis", self.styles['SectionHeader']))
            self._add_subject_analysis(story, subject_totals)
            story.append(Spacer(1, 20))
        
        # Grade Distribution
        story.append(Paragraph("Grade Distribution", self.styles['SectionHeader']))
        grades = self._calculate_grades(marks, max_marks)
        self._add_grade_distribution_table(story, grades, len(marks))
        
        # Footer
        story.append(Spacer(1, 30))
        story.append(Paragraph(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 
                              self.styles['BodyText']))
        story.append(Paragraph("Generated by Exam Analysis Tool", self.styles['BodyText']))
        
        doc.build(story)
        pdf_content = buffer.getvalue()
        buffer.close()
        
        return pdf_content
    
    def _add_rankings_table(self, story, rankings):
        """Add student rankings table to the story"""
        ranking_data = [['Rank', 'Student Name', 'Score', 'Grade']]
        
        for rank_info in rankings:
            ranking_data.append([
                str(rank_info['rank']),
                rank_info['student_name'],
                f"{rank_info['score']:.1f}",
                rank_info['grade']
            ])
        
        ranking_table = Table(ranking_data, colWidths=[0.8*inch, 2.5*inch, 1*inch, 0.8*inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        story.append(ranking_table)
    
    def _add_subject_analysis(self, story, subject_totals):
        """Add subject-wise analysis table"""
        subject_data = [['Subject', 'Total Marks', 'Average', 'Highest', 'Lowest']]
        
        for subject, data in subject_totals.items():
            subject_data.append([
                subject,
                f"{data['total']:.1f}",
                f"{data['average']:.1f}",
                f"{data['highest']:.1f}",
                f"{data['lowest']:.1f}"
            ])
        
        subject_table = Table(subject_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1*inch, 1*inch])
        subject_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9)
        ]))
        story.append(subject_table)
    
    def _add_grade_distribution_table(self, story, grades, total_students):
        """Add grade distribution table"""
        grade_data = [['Grade', 'Count', 'Percentage']]
        
        for grade, count in grades.items():
            if count > 0:
                percentage = (count / total_students) * 100
                grade_data.append([grade, str(count), f"{percentage:.1f}%"])
        
        grade_table = Table(grade_data, colWidths=[1*inch, 1*inch, 1.5*inch])
        grade_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(grade_table)
    
    def _calculate_pass_rate(self, marks, pass_threshold, max_marks):
        """Calculate pass rate"""
        pass_mark = (pass_threshold / 100) * max_marks
        passed = sum(1 for mark in marks if mark >= pass_mark)
        return (passed / len(marks)) * 100 if marks else 0
    
    def _calculate_grades(self, marks, max_marks=100):
        """Calculate grade distribution"""
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
        
        return grades