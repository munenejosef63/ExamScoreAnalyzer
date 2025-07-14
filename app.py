import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import json
from utils.data_processor import DataProcessor
from utils.analyzer import ExamAnalyzer
from utils.visualizer import ExamVisualizer

def main():
    st.set_page_config(
        page_title="Exam Analysis Tool",
        page_icon="📊",
        layout="wide"
    )
    
    st.title("📊 Exam Analysis Tool")
    st.markdown("---")
    
    # Initialize session state
    if 'analysis_data' not in st.session_state:
        st.session_state.analysis_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    
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
    
    # Analysis section
    if st.session_state.analysis_data is not None:
        st.markdown("---")
        perform_analysis()
        
        # Results section
        if st.session_state.analysis_results is not None:
            st.markdown("---")
            display_results()

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
        cols = st.columns(min(5, num_students))
        
        for i in range(num_students):
            col_idx = i % 5
            with cols[col_idx]:
                mark = st.number_input(
                    f"Student {i+1}:",
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
    
    # Detailed Statistics Table
    st.subheader("📋 Detailed Statistics")
    
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    percentile_values = [np.percentile(marks, p) for p in percentiles]
    
    stats_df = pd.DataFrame({
        'Statistic': ['Count', 'Mean', 'Median', 'Mode', 'Standard Deviation', 'Variance', 'Minimum', 'Maximum', 'Range'] + [f'{p}th Percentile' for p in percentiles],
        'Value': [
            results['count'],
            f"{results['mean']:.2f}",
            f"{results['median']:.2f}",
            f"{results['mode']:.2f}" if results['mode'] is not None else "No mode",
            f"{results['std_dev']:.2f}",
            f"{results['variance']:.2f}",
            f"{results['min']:.2f}",
            f"{results['max']:.2f}",
            f"{results['range']:.2f}"
        ] + [f"{val:.2f}" for val in percentile_values]
    })
    
    st.dataframe(stats_df, use_container_width=True)
    
    # Export functionality
    st.subheader("💾 Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export statistics as JSON
        export_data = {
            'statistics': results,
            'marks': marks,
            'pass_threshold': pass_threshold,
            'pass_rate': pass_rate,
            'grades': grades
        }
        
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="📄 Download JSON",
            data=json_str,
            file_name="exam_analysis.json",
            mime="application/json"
        )
    
    with col2:
        # Export as CSV
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
    
    with col3:
        # Export statistics table
        stats_csv = stats_df.to_csv(index=False)
        st.download_button(
            label="📈 Download Statistics",
            data=stats_csv,
            file_name="exam_statistics.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()
