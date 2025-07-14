# Exam Analysis Tool

## Overview

This is a Streamlit-based web application for analyzing exam marks and scores. The tool provides comprehensive statistical analysis and visualizations to help educators and administrators understand exam performance patterns. Users can upload data in various formats (CSV, Excel, PDF) or manually enter exam marks for analysis.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit web application framework
- **Layout**: Wide layout configuration for better data visualization
- **State Management**: Streamlit session state for maintaining analysis data and results across user interactions
- **Input Methods**: Dual input system supporting both file uploads and manual data entry

### Backend Architecture
- **Modular Design**: Utility-based architecture with separate modules for data processing, analysis, and visualization
- **Processing Pipeline**: Three-stage pipeline consisting of data ingestion, statistical analysis, and visualization generation
- **Error Handling**: Comprehensive error handling for file processing and data validation

## Key Components

### 1. Main Application (app.py)
- **Purpose**: Entry point and UI orchestration
- **Responsibilities**: 
  - UI layout and user interaction handling
  - Session state management
  - Coordination between utility modules
- **Features**: File upload interface, manual entry forms, analysis triggers

### 2. Data Processor (utils/data_processor.py)
- **Purpose**: Handle multiple file formats and data extraction
- **Supported Formats**: CSV, Excel (XLSX/XLS), PDF
- **Features**:
  - Multiple encoding support for CSV files
  - Automatic data cleaning and validation
  - Mark extraction from various data structures

### 3. Statistical Analyzer (utils/analyzer.py)
- **Purpose**: Comprehensive statistical analysis of exam marks
- **Analysis Types**:
  - Descriptive statistics (mean, median, mode, standard deviation)
  - Distribution analysis (skewness, kurtosis)
  - Quartile analysis and outlier detection
  - Percentile calculations
- **Dependencies**: NumPy for numerical operations, SciPy for advanced statistics

### 4. Visualization Engine (utils/visualizer.py)
- **Purpose**: Generate interactive charts and graphs
- **Technology**: Plotly for interactive visualizations
- **Chart Types**: Histograms, distribution plots, statistical summaries
- **Features**: Customizable color schemes, pass mark indicators

## Data Flow

1. **Data Input**: Users upload files or manually enter marks
2. **Data Processing**: Raw data is cleaned, validated, and standardized
3. **Statistical Analysis**: Comprehensive statistical calculations performed
4. **Visualization Generation**: Interactive charts and graphs created
5. **Results Display**: Analysis results and visualizations presented to user

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for rapid development
- **Pandas**: Data manipulation and analysis
- **NumPy**: Numerical computing and array operations
- **Plotly**: Interactive visualization library
- **SciPy**: Scientific computing for statistical functions

### File Processing
- **PyPDF2**: PDF text extraction and processing
- **Built-in CSV/Excel**: Pandas handles CSV and Excel file formats

### Statistical Computing
- **SciPy.stats**: Advanced statistical functions (skewness, kurtosis)
- **NumPy.stats**: Basic statistical operations

## Deployment Strategy

### Development Environment
- **Platform**: Designed for Replit deployment
- **Configuration**: Streamlit configuration optimized for web deployment
- **Dependencies**: All dependencies managed through standard Python package management

### Production Considerations
- **Scalability**: Single-user focused design suitable for small to medium datasets
- **Performance**: In-memory processing suitable for typical exam datasets
- **Security**: File upload validation and error handling for safe operation

### Future Enhancements
- **Database Integration**: Potential for adding persistent data storage
- **Multi-user Support**: Session management for concurrent users
- **Export Functionality**: PDF report generation and data export capabilities