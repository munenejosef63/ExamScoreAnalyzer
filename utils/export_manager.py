import pandas as pd
import json
import io
import zipfile
from datetime import datetime
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import base64

class ExportManager:
    """Comprehensive export functionality for exam analysis data"""
    
    def __init__(self):
        self.supported_formats = ['csv', 'excel', 'json', 'pdf', 'zip']
    
    def export_student_rankings(self, rankings_data, format_type='csv'):
        """Export student rankings in various formats"""
        try:
            if format_type == 'csv':
                return self._export_rankings_csv(rankings_data)
            elif format_type == 'excel':
                return self._export_rankings_excel(rankings_data)
            elif format_type == 'json':
                return self._export_rankings_json(rankings_data)
            elif format_type == 'pdf':
                return self._export_rankings_pdf(rankings_data)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
        
        except Exception as e:
            st.error(f"Export failed: {str(e)}")
            return None
    
    def _export_rankings_csv(self, rankings_data):
        """Export rankings as CSV"""
        df = pd.DataFrame([
            {
                'Rank': rank['rank'],
                'Student Name': rank['student_name'],
                'Total Score': rank['total_score'],
                'Average per Subject': rank['average_per_subject'],
                'Subject Count': rank['subject_count'],
                'Best Subject': f"{rank['best_subject'][0]}: {rank['best_subject'][1]:.1f}" if rank['best_subject'] else "N/A",
                'Worst Subject': f"{rank['worst_subject'][0]}: {rank['worst_subject'][1]:.1f}" if rank['worst_subject'] else "N/A"
            } for rank in rankings_data
        ])
        
        return df.to_csv(index=False).encode('utf-8')
    
    def _export_rankings_excel(self, rankings_data):
        """Export rankings as Excel with multiple sheets"""
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main rankings sheet
            rankings_df = pd.DataFrame([
                {
                    'Rank': rank['rank'],
                    'Student Name': rank['student_name'],
                    'Total Score': rank['total_score'],
                    'Average per Subject': rank['average_per_subject'],
                    'Subject Count': rank['subject_count']
                } for rank in rankings_data
            ])
            rankings_df.to_excel(writer, sheet_name='Rankings', index=False)
            
            # Subject-wise scores sheet
            if rankings_data and 'subject_scores' in rankings_data[0]:
                subject_data = []
                for rank in rankings_data:
                    for subject, score in rank['subject_scores'].items():
                        subject_data.append({
                            'Student Name': rank['student_name'],
                            'Subject': subject,
                            'Score': score,
                            'Rank': rank['rank']
                        })
                
                if subject_data:
                    subject_df = pd.DataFrame(subject_data)
                    subject_df.to_excel(writer, sheet_name='Subject Scores', index=False)
        
        return output.getvalue()
    
    def _export_rankings_json(self, rankings_data):
        """Export rankings as JSON"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'total_students': len(rankings_data),
            'rankings': rankings_data
        }
        
        return json.dumps(export_data, indent=2, default=str).encode('utf-8')
    
    def _export_rankings_pdf(self, rankings_data):
        """Export rankings as comprehensive PDF report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.darkblue,
            spaceAfter=30,
            alignment=1  # Center
        )
        
        story.append(Paragraph("Student Rankings Report", title_style))
        story.append(Spacer(1, 20))
        
        # Summary information
        summary_style = ParagraphStyle(
            'Summary',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=10
        )
        
        story.append(Paragraph(f"<b>Total Students:</b> {len(rankings_data)}", summary_style))
        story.append(Paragraph(f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", summary_style))
        story.append(Spacer(1, 20))
        
        # Rankings table
        table_data = [['Rank', 'Student Name', 'Total Score', 'Average', 'Best Subject']]
        
        for rank in rankings_data[:20]:  # Top 20 students
            best_subject = f"{rank['best_subject'][0]}: {rank['best_subject'][1]:.1f}" if rank['best_subject'] else "N/A"
            table_data.append([
                str(rank['rank']),
                rank['student_name'],
                f"{rank['total_score']:.1f}",
                f"{rank['average_per_subject']:.1f}",
                best_subject[:20] + "..." if len(best_subject) > 20 else best_subject
            ])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(table)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
    
    def export_comprehensive_analysis(self, student_data, analysis_results, rankings_data, student_info=None):
        """Export comprehensive analysis including all data"""
        try:
            # Create ZIP file with multiple components
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # 1. Student data CSV
                if student_data:
                    student_df = pd.DataFrame.from_dict(student_data, orient='index')
                    csv_data = student_df.to_csv().encode('utf-8')
                    zip_file.writestr('student_data.csv', csv_data)
                
                # 2. Rankings data
                if rankings_data:
                    rankings_csv = self._export_rankings_csv(rankings_data)
                    zip_file.writestr('student_rankings.csv', rankings_csv)
                    
                    rankings_json = self._export_rankings_json(rankings_data)
                    zip_file.writestr('rankings_detailed.json', rankings_json)
                
                # 3. Statistical analysis results
                if analysis_results:
                    analysis_json = json.dumps(analysis_results, indent=2, default=str).encode('utf-8')
                    zip_file.writestr('statistical_analysis.json', analysis_json)
                
                # 4. Class information
                if student_info:
                    info_json = json.dumps(student_info, indent=2, default=str).encode('utf-8')
                    zip_file.writestr('class_information.json', info_json)
                
                # 5. Summary report
                summary_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'total_students': len(student_data) if student_data else 0,
                    'total_rankings': len(rankings_data) if rankings_data else 0,
                    'class_info': student_info,
                    'export_includes': [
                        'student_data.csv - Individual student scores',
                        'student_rankings.csv - Student rankings table',
                        'rankings_detailed.json - Detailed ranking information',
                        'statistical_analysis.json - Statistical analysis results',
                        'class_information.json - Class and exam details'
                    ]
                }
                
                summary_json = json.dumps(summary_data, indent=2, default=str).encode('utf-8')
                zip_file.writestr('export_summary.json', summary_json)
            
            zip_buffer.seek(0)
            return zip_buffer.getvalue()
        
        except Exception as e:
            st.error(f"Comprehensive export failed: {str(e)}")
            return None
    
    def export_historical_comparison(self, comparison_data, format_type='json'):
        """Export historical comparison data"""
        try:
            if format_type == 'json':
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'comparison_type': 'historical_analysis',
                    'data': comparison_data
                }
                return json.dumps(export_data, indent=2, default=str).encode('utf-8')
            
            elif format_type == 'csv':
                # Flatten comparison data for CSV export
                csv_data = []
                for student, data in comparison_data.items():
                    row = {
                        'Student': student,
                        'Current_Total': data['subjects'].get('Total', {}).get('current', 0),
                        'Previous_Total': data['subjects'].get('Total', {}).get('previous', 0),
                        'Total_Change': data.get('total_change', 0),
                        'Overall_Trend': data.get('overall_trend', 'stable')
                    }
                    
                    # Add subject-wise changes
                    for subject, subject_data in data['subjects'].items():
                        if subject != 'Total':
                            row[f'{subject}_Current'] = subject_data.get('current', 0)
                            row[f'{subject}_Previous'] = subject_data.get('previous', 0)
                            row[f'{subject}_Change'] = subject_data.get('change', 0)
                    
                    csv_data.append(row)
                
                df = pd.DataFrame(csv_data)
                return df.to_csv(index=False).encode('utf-8')
            
            else:
                raise ValueError(f"Unsupported format for historical comparison: {format_type}")
        
        except Exception as e:
            st.error(f"Historical comparison export failed: {str(e)}")
            return None
    
    def create_comprehensive_pdf_report(self, student_data, rankings_data, analysis_results, student_info, historical_data=None):
        """Create a comprehensive PDF report with all analysis components"""
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*inch)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=28,
                textColor=colors.darkblue,
                spaceAfter=30,
                alignment=1
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                textColor=colors.darkblue,
                spaceAfter=15,
                spaceBefore=20
            )
            
            # Cover page
            story.append(Paragraph("Comprehensive Exam Analysis Report", title_style))
            story.append(Spacer(1, 50))
            
            # Class information
            if student_info:
                info_table_data = []
                if student_info.get('class_name'):
                    info_table_data.append(['Class:', student_info['class_name']])
                if student_info.get('exam_name'):
                    info_table_data.append(['Exam:', student_info['exam_name']])
                if student_info.get('grade'):
                    info_table_data.append(['Grade:', student_info['grade']])
                if student_info.get('stream'):
                    info_table_data.append(['Stream:', student_info['stream']])
                if student_info.get('teacher_name'):
                    info_table_data.append(['Teacher:', student_info['teacher_name']])
                if student_info.get('exam_date'):
                    info_table_data.append(['Date:', str(student_info['exam_date'])])
                
                if info_table_data:
                    info_table = Table(info_table_data, colWidths=[2*inch, 4*inch])
                    info_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 12),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
                    ]))
                    story.append(info_table)
            
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(PageBreak())
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            
            if student_data and analysis_results:
                total_students = len(student_data)
                avg_score = sum(data.get('Total', 0) for data in student_data.values()) / total_students if total_students > 0 else 0
                
                summary_text = f"""
                This report presents a comprehensive analysis of exam results for {total_students} students.
                The average total score across all students is {avg_score:.1f}.
                
                Key findings include detailed statistical analysis, student rankings, 
                and performance insights to support educational decision-making.
                """
                
                story.append(Paragraph(summary_text, styles['Normal']))
            
            story.append(PageBreak())
            
            # Statistical Analysis
            if analysis_results:
                story.append(Paragraph("Statistical Analysis", heading_style))
                
                stats_data = [
                    ['Metric', 'Value'],
                    ['Mean Score', f"{analysis_results.get('mean', 0):.2f}"],
                    ['Median Score', f"{analysis_results.get('median', 0):.2f}"],
                    ['Standard Deviation', f"{analysis_results.get('std_dev', 0):.2f}"],
                    ['Minimum Score', f"{analysis_results.get('min', 0):.2f}"],
                    ['Maximum Score', f"{analysis_results.get('max', 0):.2f}"]
                ]
                
                stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
                stats_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 12),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(stats_table)
                story.append(PageBreak())
            
            # Student Rankings
            if rankings_data:
                story.append(Paragraph("Student Rankings", heading_style))
                
                ranking_table_data = [['Rank', 'Student Name', 'Total Score', 'Average/Subject']]
                
                for rank in rankings_data[:30]:  # Top 30 students
                    ranking_table_data.append([
                        str(rank['rank']),
                        rank['student_name'],
                        f"{rank['total_score']:.1f}",
                        f"{rank['average_per_subject']:.1f}"
                    ])
                
                ranking_table = Table(ranking_table_data)
                ranking_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                
                story.append(ranking_table)
            
            # Historical comparison section
            if historical_data:
                story.append(PageBreak())
                story.append(Paragraph("Historical Comparison", heading_style))
                
                # Add historical analysis content
                story.append(Paragraph("This section contains comparison with previous exam results, showing student progress and improvement trends.", styles['Normal']))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
        
        except Exception as e:
            st.error(f"PDF report generation failed: {str(e)}")
            return None
    
    def create_download_link(self, data, filename, file_format):
        """Create a download link for the exported data"""
        if data is None:
            return None
        
        # Determine MIME type
        mime_types = {
            'csv': 'text/csv',
            'json': 'application/json',
            'pdf': 'application/pdf',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'zip': 'application/zip'
        }
        
        mime_type = mime_types.get(file_format, 'application/octet-stream')
        
        # Create download button
        return st.download_button(
            label=f"📄 Download {file_format.upper()}",
            data=data,
            file_name=f"{filename}.{file_format}",
            mime=mime_type,
            use_container_width=True
        )

def display_export_interface(student_data=None, rankings_data=None, analysis_results=None, student_info=None, historical_data=None):
    """Display comprehensive export interface"""
    st.subheader("📤 Export & Download")
    
    export_manager = ExportManager()
    
    # Export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Data Exports**")
        
        # Student rankings export
        if rankings_data:
            st.markdown("*Student Rankings:*")
            export_format = st.selectbox(
                "Choose format:",
                ['csv', 'excel', 'json', 'pdf'],
                key="rankings_format"
            )
            
            if st.button("Export Rankings", key="export_rankings"):
                with st.spinner("Generating export..."):
                    exported_data = export_manager.export_student_rankings(rankings_data, export_format)
                    
                    if exported_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"student_rankings_{timestamp}"
                        
                        export_manager.create_download_link(exported_data, filename, export_format)
                        st.success(f"Rankings exported as {export_format.upper()}")
        
        # Historical comparison export
        if historical_data:
            st.markdown("*Historical Comparison:*")
            hist_format = st.selectbox(
                "Choose format:",
                ['json', 'csv'],
                key="historical_format"
            )
            
            if st.button("Export Historical Data", key="export_historical"):
                with st.spinner("Generating export..."):
                    exported_data = export_manager.export_historical_comparison(historical_data, hist_format)
                    
                    if exported_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"historical_comparison_{timestamp}"
                        
                        export_manager.create_download_link(exported_data, filename, hist_format)
                        st.success(f"Historical data exported as {hist_format.upper()}")
    
    with col2:
        st.markdown("**📋 Comprehensive Reports**")
        
        # Comprehensive analysis export
        if student_data and rankings_data:
            if st.button("📦 Export Complete Analysis (ZIP)", key="export_comprehensive"):
                with st.spinner("Creating comprehensive export..."):
                    exported_data = export_manager.export_comprehensive_analysis(
                        student_data, analysis_results, rankings_data, student_info
                    )
                    
                    if exported_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"exam_analysis_complete_{timestamp}"
                        
                        export_manager.create_download_link(exported_data, filename, 'zip')
                        st.success("Complete analysis exported as ZIP package")
        
        # Comprehensive PDF report
        if student_data and rankings_data and analysis_results:
            if st.button("📄 Generate PDF Report", key="export_pdf_report"):
                with st.spinner("Generating comprehensive PDF report..."):
                    pdf_data = export_manager.create_comprehensive_pdf_report(
                        student_data, rankings_data, analysis_results, student_info, historical_data
                    )
                    
                    if pdf_data:
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"exam_analysis_report_{timestamp}"
                        
                        export_manager.create_download_link(pdf_data, filename, 'pdf')
                        st.success("Comprehensive PDF report generated successfully")