import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import json
import base64
from datetime import datetime
from utils.data_processor import DataProcessor
from utils.analyzer import ExamAnalyzer
from utils.visualizer import ExamVisualizer
from utils.email_handler import EmailHandler
from utils.ranking_system import RankingSystem
from utils.pdf_generator import PDFGenerator

def main():
    st.set_page_config(
        page_title="Exam Analysis Tool",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 10px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: #f8f9fa;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            margin: 0.5rem 0;
        }
        .info-box {
            background: #e3f2fd;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #2196f3;
            margin: 1rem 0;
        }
        .success-box {
            background: #e8f5e8;
            padding: 1rem;
            border-radius: 8px;
            border-left: 4px solid #4caf50;
            margin: 1rem 0;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Exam Analysis Tool</h1>
        <p>Comprehensive statistical analysis for exam results with student information management</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'student_info' not in st.session_state:
        st.session_state.student_info = None
    
    # Sidebar for student information
    with st.sidebar:
        st.header("👨‍🎓 Student Information")
        student_info = handle_student_info()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Data input section
        st.header("📥 Data Input")
        
        input_method = st.radio(
            "Choose your input method:",
            ["Upload Document", "Manual Entry"],
            horizontal=True
        )
        
        data_processor = DataProcessor()
        
        if input_method == "Upload Document":
            handle_file_upload(data_processor)
        else:
            handle_manual_entry()
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 📋 Quick Guide")
        st.markdown("""
        **Upload Document:**
        - Support CSV, Excel, PDF files
        - Automatic mark extraction
        
        **Manual Entry:**
        - Individual input for each student
        - Bulk text input option
        
        **Features:**
        - Statistical analysis
        - Visual charts
        - Export results
        - Email sharing
        """)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Analysis section
    if st.session_state.analysis_data is not None:
        st.markdown("---")
        perform_analysis()
        
        # Results section
        if st.session_state.analysis_results is not None:
            st.markdown("---")
            display_results()

def handle_student_info():
    """Handle student information input in sidebar"""
    st.markdown("Enter details for class or individual students:")
    
    # Class information
    st.subheader("📚 Class Details")
    class_name = st.text_input("Class/Subject Name:", placeholder="e.g., Mathematics 101")
    grade = st.selectbox("Grade/Year:", ["Select Grade", "Grade 9", "Grade 10", "Grade 11", "Grade 12", "Year 1", "Year 2", "Year 3", "Year 4", "Other"])
    stream = st.selectbox("Stream/Section:", ["Select Stream", "Science", "Commerce", "Arts", "A", "B", "C", "D", "Other"])
    
    if stream == "Other":
        stream = st.text_input("Enter Stream/Section:", placeholder="Enter custom stream")
    
    # Exam details
    st.subheader("📝 Exam Information")
    exam_name = st.text_input("Exam Name:", placeholder="e.g., Mid-term Exam")
    exam_date = st.date_input("Exam Date:")
    teacher_name = st.text_input("Teacher Name:", placeholder="Your name")
    
    # Individual student names (optional)
    st.subheader("👥 Student Names (Optional)")
    enable_names = st.checkbox("Add individual student names")
    student_names = []
    
    if enable_names:
        num_students = st.number_input("Number of students:", min_value=1, max_value=50, value=5)
        
        if st.button("📝 Enter Student Names"):
            st.session_state.show_name_inputs = True
        
        if hasattr(st.session_state, 'show_name_inputs') and st.session_state.show_name_inputs:
            for i in range(num_students):
                name = st.text_input(f"Student {i+1}:", key=f"student_name_{i}", placeholder=f"Student {i+1} name")
                if name:
                    student_names.append(name)
    
    # Subject Information
    st.subheader("📚 Subject Details")
    enable_subjects = st.checkbox("Enable multi-subject analysis")
    subjects_data = {}
    
    if enable_subjects:
        num_subjects = st.number_input("Number of subjects:", min_value=1, max_value=10, value=1)
        
        for i in range(num_subjects):
            subject_name = st.text_input(f"Subject {i+1} name:", key=f"subject_{i}", placeholder=f"e.g., Mathematics")
            if subject_name:
                subjects_data[subject_name] = []
    
    # Save to session state
    student_info = {
        'class_name': class_name,
        'grade': grade if grade != "Select Grade" else "",
        'stream': stream if stream != "Select Stream" else "",
        'exam_name': exam_name,
        'exam_date': exam_date,
        'teacher_name': teacher_name,
        'student_names': student_names,
        'subjects_data': subjects_data,
        'timestamp': datetime.now()
    }
    
    st.session_state.student_info = student_info
    
    # Display summary
    if any([class_name, grade != "Select Grade", stream != "Select Stream", exam_name]):
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("### ✅ Information Summary")
        if class_name:
            st.write(f"**Class:** {class_name}")
        if grade != "Select Grade":
            st.write(f"**Grade:** {grade}")
        if stream != "Select Stream":
            st.write(f"**Stream:** {stream}")
        if exam_name:
            st.write(f"**Exam:** {exam_name}")
        if teacher_name:
            st.write(f"**Teacher:** {teacher_name}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    return student_info

def handle_file_upload(data_processor):
    st.subheader("📁 Upload Exam Results")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls', 'pdf'],
        help="Supported formats: CSV, Excel (.xlsx, .xls), PDF"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner("Processing file..."):
                df = data_processor.process_file(uploaded_file)
                
            if df is not None and not df.empty:
                st.success(f"✅ File processed successfully! Found {len(df)} records.")
                
                # Display preview
                st.subheader("📋 Data Preview")
                st.dataframe(df.head(10))
                
                # Column selection for marks
                numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
                
                if numeric_columns:
                    selected_column = st.selectbox(
                        "Select the column containing marks:",
                        numeric_columns,
                        help="Choose the column that contains the exam marks/scores"
                    )
                    
                    if st.button("Analyze Data", type="primary"):
                        marks = df[selected_column].dropna()
                        if len(marks) > 0:
                            st.session_state.analysis_data = marks.tolist()
                            st.rerun()
                        else:
                            st.error("No valid marks found in the selected column.")
                else:
                    st.error("No numeric columns found in the uploaded file.")
            else:
                st.error("Could not process the file or file is empty.")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

def handle_manual_entry():
    st.subheader("✏️ Manual Mark Entry")
    
    col1, col2 = st.columns(2)
    
    with col1:
        num_students = st.number_input(
            "Number of students:",
            min_value=1,
            max_value=1000,
            value=10,
            help="Enter the total number of students"
        )
    
    with col2:
        max_marks = st.number_input(
            "Maximum marks:",
            min_value=1,
            value=100,
            help="Enter the maximum possible marks for the exam"
        )
    
    st.subheader("📝 Enter Marks")
    
    # Create input method selection
    entry_method = st.radio(
        "Choose entry method:",
        ["Individual Input", "Bulk Text Input"],
        horizontal=True
    )
    
    if entry_method == "Individual Input":
        marks = []
        student_info = st.session_state.student_info
        student_names = student_info.get('student_names', []) if student_info else []
        
        # Create a more organized layout for individual input
        if num_students <= 10:
            cols = st.columns(min(2, num_students))
            for i in range(num_students):
                col_idx = i % 2
                with cols[col_idx]:
                    # Use student name if available, otherwise use generic label
                    if i < len(student_names) and student_names[i]:
                        label = f"{student_names[i]}:"
                    else:
                        label = f"Student {i+1}:"
                    
                    mark = st.number_input(
                        label,
                        min_value=0.0,
                        max_value=float(max_marks),
                        value=0.0,
                        step=0.5,
                        key=f"mark_{i}",
                        help=f"Enter marks for student (0-{max_marks})"
                    )
                    marks.append(mark)
        else:
            # For larger classes, use a more compact layout
            st.info("💡 For large classes, consider using the 'Bulk Text Input' method for faster entry.")
            for i in range(num_students):
                if i < len(student_names) and student_names[i]:
                    label = f"{student_names[i]}:"
                else:
                    label = f"Student {i+1}:"
                
                mark = st.number_input(
                    label,
                    min_value=0.0,
                    max_value=float(max_marks),
                    value=0.0,
                    step=0.5,
                    key=f"mark_{i}"
                )
                marks.append(mark)
    
    else:  # Bulk Text Input
        st.info("Enter marks separated by commas, spaces, or new lines")
        bulk_input = st.text_area(
            "Paste marks here:",
            height=150,
            placeholder="85, 92, 78, 88, 95\n72, 84, 90, 77, 83\n..."
        )
        
        marks = []
        if bulk_input.strip():
            try:
                # Parse bulk input
                import re
                # Split by comma, space, or newline
                raw_marks = re.split('[,\s\n]+', bulk_input.strip())
                marks = [float(mark) for mark in raw_marks if mark.strip()]
                
                # Validate marks
                invalid_marks = [mark for mark in marks if mark < 0 or mark > max_marks]
                if invalid_marks:
                    st.warning(f"Found {len(invalid_marks)} marks outside valid range (0-{max_marks})")
                
                st.info(f"Parsed {len(marks)} marks from input")
                
            except ValueError:
                st.error("Invalid format. Please enter numeric values only.")
                marks = []
    
    if st.button("Analyze Marks", type="primary"):
        if marks and any(mark > 0 for mark in marks):
            st.session_state.analysis_data = marks
            st.rerun()
        else:
            st.error("Please enter at least one valid mark greater than 0.")

def perform_analysis():
    st.header("🔍 Statistical Analysis")
    
    analyzer = ExamAnalyzer()
    marks = st.session_state.analysis_data
    
    with st.spinner("Performing analysis..."):
        results = analyzer.analyze(marks)
        st.session_state.analysis_results = results
    
    st.success("✅ Analysis completed!")

def display_results():
    st.header("📈 Analysis Results")
    results = st.session_state.analysis_results
    student_info = st.session_state.student_info
    
    # Display class information if available
    if student_info and any([student_info.get('class_name'), student_info.get('grade'), student_info.get('stream')]):
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            if student_info.get('class_name'):
                st.write(f"**Class:** {student_info['class_name']}")
            if student_info.get('grade'):
                st.write(f"**Grade:** {student_info['grade']}")
        with col2:
            if student_info.get('stream'):
                st.write(f"**Stream:** {student_info['stream']}")
            if student_info.get('exam_name'):
                st.write(f"**Exam:** {student_info['exam_name']}")
        with col3:
            if student_info.get('teacher_name'):
                st.write(f"**Teacher:** {student_info['teacher_name']}")
            if student_info.get('exam_date'):
                st.write(f"**Date:** {student_info['exam_date']}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Mean Score",
            f"{results['mean']:.2f}",
            help="Average score of all students"
        )
    
    with col2:
        st.metric(
            "Median Score",
            f"{results['median']:.2f}",
            help="Middle value when scores are arranged in order"
        )
    
    with col3:
        st.metric(
            "Standard Deviation",
            f"{results['std_dev']:.2f}",
            help="Measure of score variability"
        )
    
    with col4:
        st.metric(
            "Total Students",
            results['count'],
            help="Total number of students"
        )
    
    # Additional statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Highest Score",
            f"{results['max']:.2f}",
            help="Best performance in the exam"
        )
    
    with col2:
        st.metric(
            "Lowest Score",
            f"{results['min']:.2f}",
            help="Lowest score in the exam"
        )
    
    with col3:
        if results['mode'] is not None:
            st.metric(
                "Mode",
                f"{results['mode']:.2f}",
                help="Most frequently occurring score"
            )
        else:
            st.metric(
                "Mode",
                "No mode",
                help="No frequently occurring score"
            )
    
    with col4:
        st.metric(
            "Range",
            f"{results['range']:.2f}",
            help="Difference between highest and lowest scores"
        )
    
    # Pass/Fail Analysis
    st.subheader("✅ Pass/Fail Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        pass_threshold = st.slider(
            "Pass Threshold (%):",
            min_value=0,
            max_value=100,
            value=50,
            help="Set the minimum percentage required to pass"
        )
    
    with col2:
        max_marks = st.number_input(
            "Maximum Marks:",
            min_value=1,
            value=100,
            help="Total marks for the exam"
        )
    
    # Calculate pass/fail rates
    marks = st.session_state.analysis_data
    pass_mark = (pass_threshold / 100) * max_marks
    passed = sum(1 for mark in marks if mark >= pass_mark)
    failed = len(marks) - passed
    pass_rate = (passed / len(marks)) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Students Passed", passed)
    
    with col2:
        st.metric("Students Failed", failed)
    
    with col3:
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    # Visualizations
    st.subheader("📊 Visualizations")
    
    visualizer = ExamVisualizer()
    
    # Distribution histogram
    fig_hist = visualizer.create_histogram(marks, pass_mark)
    st.plotly_chart(fig_hist, use_container_width=True)
    
    # Box plot
    fig_box = visualizer.create_box_plot(marks)
    st.plotly_chart(fig_box, use_container_width=True)
    
    # Grade distribution
    grades = visualizer.calculate_grades(marks, max_marks)
    fig_grades = visualizer.create_grade_distribution(grades)
    st.plotly_chart(fig_grades, use_container_width=True)
    
    # Student Rankings
    st.subheader("🏆 Student Rankings")
    
    ranking_system = RankingSystem()
    student_info = st.session_state.student_info
    student_names = student_info.get('student_names', []) if student_info else []
    
    # Calculate rankings
    rankings = ranking_system.calculate_rankings(marks, student_names, max_marks)
    
    if rankings:
        # Create rankings dataframe
        rankings_df = pd.DataFrame(rankings)
        
        # Display top performers
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🥇 Top 5 Performers")
            top_5 = rankings_df.head(5)
            for _, row in top_5.iterrows():
                st.markdown(f"**{row['rank']}.** {row['student_name']} - {row['score']:.1f} ({row['grade']})")
        
        with col2:
            st.markdown("### 📊 Class Performance")
            class_summary = ranking_system.get_class_performance_summary(rankings)
            st.metric("Class Average", f"{class_summary['class_average']:.1f}")
            st.metric("Top Score", f"{class_summary['highest_score']:.1f}")
            st.metric("Total Students", class_summary['total_students'])
        
        # Full rankings table
        st.markdown("### 📋 Complete Rankings")
        display_df = rankings_df[['rank', 'student_name', 'score', 'grade', 'percentage']].copy()
        display_df.columns = ['Rank', 'Student Name', 'Score', 'Grade', 'Percentage']
        display_df['Percentage'] = display_df['Percentage'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Store rankings in session state
        st.session_state.rankings = rankings
    else:
        st.warning("No rankings available. Please ensure student data is properly entered.")
    
    # Export and Share functionality
    st.subheader("💾 Export & Share Results")
    
    # Email sharing section
    with st.expander("📧 Share via Email", expanded=False):
        handle_email_sharing(results, marks, pass_threshold, max_marks, grades)
    
    st.subheader("📥 Download Options")
    col1, col2, col3, col4 = st.columns(4)
    
    # Prepare data for exports
    rankings = getattr(st.session_state, 'rankings', [])
    subject_totals = {}  # This would be populated if multi-subject analysis is implemented
    
    with col1:
        # Export as PDF
        if st.button("📄 Generate PDF Report", type="primary"):
            pdf_generator = PDFGenerator()
            pdf_content = pdf_generator.generate_analysis_report(
                results=results,
                marks=marks,
                student_info=student_info,
                rankings=rankings,
                subject_totals=subject_totals,
                pass_threshold=pass_threshold,
                max_marks=max_marks
            )
            
            st.download_button(
                label="📄 Download PDF",
                data=pdf_content,
                file_name=f"exam_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
    
    with col2:
        # Export rankings as CSV
        if rankings:
            rankings_df = pd.DataFrame(rankings)
            rankings_csv = rankings_df.to_csv(index=False)
            st.download_button(
                label="🏆 Download Rankings",
                data=rankings_csv,
                file_name="student_rankings.csv",
                mime="text/csv"
            )
        else:
            st.button("🏆 Rankings (N/A)", disabled=True)
    
    with col3:
        # Export as CSV
        if rankings:
            export_df = pd.DataFrame({
                'Rank': [r['rank'] for r in rankings],
                'Student_Name': [r['student_name'] for r in rankings],
                'Marks': [r['score'] for r in rankings],
                'Grade': [r['grade'] for r in rankings],
                'Percentage': [f"{r['percentage']:.1f}%" for r in rankings],
                'Status': ['Pass' if r['score'] >= pass_mark else 'Fail' for r in rankings]
            })
        else:
            export_df = pd.DataFrame({
                'Student_ID': range(1, len(marks) + 1),
                'Marks': marks,
                'Grade': [visualizer.get_letter_grade(mark, max_marks) for mark in marks],
                'Status': ['Pass' if mark >= pass_mark else 'Fail' for mark in marks]
            })
        
        csv = export_df.to_csv(index=False)
        st.download_button(
            label="📊 Download CSV",
            data=csv,
            file_name="exam_results.csv",
            mime="text/csv"
        )
    
    with col4:
        # Export statistics as JSON
        export_data = {
            'statistics': results,
            'marks': marks,
            'rankings': rankings,
            'pass_threshold': pass_threshold,
            'pass_rate': pass_rate,
            'grades': grades,
            'student_info': student_info,
            'export_timestamp': datetime.now().isoformat()
        }
        
        json_str = json.dumps(export_data, indent=2, default=str)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name="exam_analysis.json",
            mime="application/json"
        )

def handle_email_sharing(results, marks, pass_threshold, max_marks, grades):
    """Handle email sharing functionality"""
    st.markdown("Send analysis results via email to students, parents, or administrators.")
    
    email_handler = EmailHandler()
    
    # Check if SendGrid is configured
    if not email_handler.is_configured():
        st.warning("⚠️ Email functionality requires SendGrid API key. Please configure SENDGRID_API_KEY environment variable to enable sending.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        recipient_email = st.text_input("Recipient Email:", placeholder="recipient@example.com")
        email_subject = st.text_input("Subject:", value="Exam Analysis Results")
    
    with col2:
        sender_email = st.text_input("Your Email:", placeholder="teacher@school.com")
        cc_emails = st.text_input("CC (optional):", placeholder="admin@school.com, parent@email.com")
    
    # Email format selection
    email_format = st.radio("Email Format:", ["Plain Text", "HTML"], horizontal=True)
    
    # Email content preview
    st.subheader("📝 Email Content Preview")
    
    student_info = st.session_state.student_info
    rankings = getattr(st.session_state, 'rankings', [])
    custom_message = st.text_area("Add Personal Message (optional):", placeholder="Additional notes or comments...")
    
    if email_format == "Plain Text":
        email_content = generate_email_content(results, marks, pass_threshold, max_marks, grades, student_info, custom_message, rankings)
        st.text_area("Email Content:", value=email_content, height=300, disabled=True)
    else:
        html_content = email_handler.generate_html_content(results, marks, pass_threshold, max_marks, grades, student_info, custom_message)
        st.markdown("**HTML Preview:**")
        st.components.v1.html(html_content, height=400, scrolling=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Send Email", type="primary"):
            if recipient_email and sender_email:
                if email_handler.is_configured():
                    with st.spinner("Sending email..."):
                        if email_format == "HTML":
                            content = html_content
                        else:
                            content = email_content
                        
                        success, message = email_handler.send_analysis_email(
                            to_email=recipient_email,
                            from_email=sender_email,
                            subject=email_subject,
                            content=content,
                            cc_emails=cc_emails if cc_emails else None
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.error("❌ SendGrid API key not configured. Please set SENDGRID_API_KEY environment variable.")
            else:
                st.error("❌ Please fill in both recipient and sender email addresses.")
    
    with col2:
        if st.button("📋 Copy Content"):
            content_to_copy = html_content if email_format == "HTML" else email_content
            st.info("📋 Copy the email content above to send manually through your email client.")
    
    with col3:
        if st.button("💾 Download Content"):
            content_to_download = html_content if email_format == "HTML" else email_content
            file_extension = "html" if email_format == "HTML" else "txt"
            st.download_button(
                label=f"📄 Download {email_format}",
                data=content_to_download,
                file_name=f"exam_analysis_email.{file_extension}",
                mime="text/html" if email_format == "HTML" else "text/plain"
            )

def generate_email_content(results, marks, pass_threshold, max_marks, grades, student_info, custom_message="", rankings=[]):
    """Generate formatted email content"""
    content = []
    
    # Header
    if student_info:
        if student_info.get('exam_name'):
            content.append(f"Subject: {student_info['exam_name']} - Analysis Results")
        if student_info.get('class_name'):
            content.append(f"Class: {student_info['class_name']}")
        if student_info.get('grade') and student_info.get('stream'):
            content.append(f"Grade: {student_info['grade']} | Stream: {student_info['stream']}")
        if student_info.get('teacher_name'):
            content.append(f"Teacher: {student_info['teacher_name']}")
        content.append("")
    
    # Add custom message if provided
    if custom_message:
        content.append("PERSONAL MESSAGE:")
        content.append("-" * 30)
        content.append(custom_message)
        content.append("")
    
    # Analysis summary
    content.append("EXAM ANALYSIS SUMMARY")
    content.append("=" * 50)
    content.append("")
    
    # Key statistics
    content.append("📊 Key Statistics:")
    content.append(f"• Total Students: {results['count']}")
    content.append(f"• Average Score: {results['mean']:.2f}")
    content.append(f"• Median Score: {results['median']:.2f}")
    content.append(f"• Highest Score: {results['max']:.2f}")
    content.append(f"• Lowest Score: {results['min']:.2f}")
    content.append(f"• Standard Deviation: {results['std_dev']:.2f}")
    content.append("")
    
    # Pass/Fail analysis
    pass_mark = (pass_threshold / 100) * max_marks
    passed = sum(1 for mark in marks if mark >= pass_mark)
    failed = len(marks) - passed
    pass_rate = (passed / len(marks)) * 100
    
    content.append("✅ Pass/Fail Analysis:")
    content.append(f"• Pass Threshold: {pass_threshold}% ({pass_mark:.1f} marks)")
    content.append(f"• Students Passed: {passed}")
    content.append(f"• Students Failed: {failed}")
    content.append(f"• Pass Rate: {pass_rate:.1f}%")
    content.append("")
    
    # Grade distribution
    content.append("📊 Grade Distribution:")
    for grade, count in grades.items():
        if count > 0:
            percentage = (count / len(marks)) * 100
            content.append(f"• {grade}: {count} students ({percentage:.1f}%)")
    content.append("")
    
    # Student Rankings (top 10)
    if rankings:
        content.append("🏆 Top 10 Student Rankings:")
        top_10 = rankings[:10]
        for rank_info in top_10:
            content.append(f"• {rank_info['rank']}. {rank_info['student_name']}: {rank_info['score']:.1f} ({rank_info['grade']})")
        content.append("")
    
    # Quartile analysis
    content.append("📈 Performance Quartiles:")
    content.append(f"• 25th Percentile (Q1): {results['q1']:.2f}")
    content.append(f"• 50th Percentile (Q2/Median): {results['median']:.2f}")
    content.append(f"• 75th Percentile (Q3): {results['q3']:.2f}")
    content.append("")
    
    # Additional insights
    if results.get('outlier_count', 0) > 0:
        content.append(f"⚠️ Outliers Detected: {results['outlier_count']} students")
        content.append("")
    
    content.append("📋 This analysis was generated using the Exam Analysis Tool.")
    content.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return "\n".join(content)

if __name__ == "__main__":
    main()
