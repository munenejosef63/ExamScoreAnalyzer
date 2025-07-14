import os
import sys
from datetime import datetime
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False

class EmailHandler:
    """Handle email sending functionality using SendGrid"""
    
    def __init__(self):
        self.api_key = os.environ.get('SENDGRID_API_KEY')
        self.sendgrid_available = SENDGRID_AVAILABLE and self.api_key
    
    def is_configured(self):
        """Check if SendGrid is properly configured"""
        return self.sendgrid_available
    
    def send_analysis_email(self, to_email, from_email, subject, content, cc_emails=None):
        """
        Send analysis results via email
        
        Args:
            to_email: Recipient email address
            from_email: Sender email address
            subject: Email subject
            content: Email content (plain text)
            cc_emails: Optional CC email addresses (comma-separated string)
            
        Returns:
            tuple: (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "SendGrid is not configured. Please set SENDGRID_API_KEY environment variable."
        
        try:
            sg = SendGridAPIClient(self.api_key)
            
            # Create email message
            message = Mail(
                from_email=Email(from_email),
                to_emails=To(to_email),
                subject=subject,
                plain_text_content=Content("text/plain", content)
            )
            
            # Add CC recipients if provided
            if cc_emails:
                cc_list = [email.strip() for email in cc_emails.split(',') if email.strip()]
                for cc_email in cc_list:
                    message.add_cc(cc_email)
            
            # Send email
            response = sg.send(message)
            
            if response.status_code == 202:
                return True, "Email sent successfully!"
            else:
                return False, f"Failed to send email. Status code: {response.status_code}"
                
        except Exception as e:
            return False, f"Error sending email: {str(e)}"
    
    def generate_html_content(self, results, marks, pass_threshold, max_marks, grades, student_info, custom_message=""):
        """
        Generate HTML formatted email content for better presentation
        
        Args:
            results: Analysis results dictionary
            marks: List of student marks
            pass_threshold: Pass percentage threshold
            max_marks: Maximum possible marks
            grades: Grade distribution dictionary
            student_info: Student information dictionary
            custom_message: Optional custom message from sender
            
        Returns:
            str: HTML formatted email content
        """
        
        # Calculate pass/fail statistics
        pass_mark = (pass_threshold / 100) * max_marks
        passed = sum(1 for mark in marks if mark >= pass_mark)
        failed = len(marks) - passed
        pass_rate = (passed / len(marks)) * 100
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .info-box {{ background: #f8f9fa; padding: 15px; border-left: 4px solid #667eea; margin: 15px 0; }}
                .stats-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
                .stats-table th, .stats-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .stats-table th {{ background-color: #f2f2f2; }}
                .grade-item {{ display: inline-block; margin: 5px; padding: 5px 10px; background: #e3f2fd; border-radius: 5px; }}
                .footer {{ background: #f8f9fa; padding: 15px; text-align: center; color: #666; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 Exam Analysis Results</h1>
        """
        
        # Add class information if available
        if student_info:
            if student_info.get('exam_name'):
                html_content += f"<h2>{student_info['exam_name']}</h2>"
            
            class_info = []
            if student_info.get('class_name'):
                class_info.append(f"Class: {student_info['class_name']}")
            if student_info.get('grade'):
                class_info.append(f"Grade: {student_info['grade']}")
            if student_info.get('stream'):
                class_info.append(f"Stream: {student_info['stream']}")
            
            if class_info:
                html_content += f"<p>{' | '.join(class_info)}</p>"
        
        html_content += """
            </div>
            <div class="content">
        """
        
        # Add custom message if provided
        if custom_message:
            html_content += f"""
                <div class="info-box">
                    <h3>Personal Message</h3>
                    <p>{custom_message}</p>
                </div>
            """
        
        # Key statistics table
        html_content += f"""
            <h2>📊 Key Statistics</h2>
            <table class="stats-table">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Total Students</td><td>{results['count']}</td></tr>
                <tr><td>Average Score</td><td>{results['mean']:.2f}</td></tr>
                <tr><td>Median Score</td><td>{results['median']:.2f}</td></tr>
                <tr><td>Highest Score</td><td>{results['max']:.2f}</td></tr>
                <tr><td>Lowest Score</td><td>{results['min']:.2f}</td></tr>
                <tr><td>Standard Deviation</td><td>{results['std_dev']:.2f}</td></tr>
            </table>
            
            <h2>✅ Pass/Fail Analysis</h2>
            <table class="stats-table">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Pass Threshold</td><td>{pass_threshold}% ({pass_mark:.1f} marks)</td></tr>
                <tr><td>Students Passed</td><td>{passed}</td></tr>
                <tr><td>Students Failed</td><td>{failed}</td></tr>
                <tr><td>Pass Rate</td><td>{pass_rate:.1f}%</td></tr>
            </table>
            
            <h2>📊 Grade Distribution</h2>
            <div>
        """
        
        # Grade distribution
        for grade, count in grades.items():
            if count > 0:
                percentage = (count / len(marks)) * 100
                html_content += f'<span class="grade-item">{grade}: {count} ({percentage:.1f}%)</span>'
        
        html_content += f"""
            </div>
            
            <h2>📈 Performance Quartiles</h2>
            <table class="stats-table">
                <tr><th>Quartile</th><th>Score</th></tr>
                <tr><td>25th Percentile (Q1)</td><td>{results['q1']:.2f}</td></tr>
                <tr><td>50th Percentile (Q2/Median)</td><td>{results['median']:.2f}</td></tr>
                <tr><td>75th Percentile (Q3)</td><td>{results['q3']:.2f}</td></tr>
            </table>
        """
        
        # Additional insights
        if results.get('outlier_count', 0) > 0:
            html_content += f"""
                <div class="info-box">
                    <h3>⚠️ Additional Insights</h3>
                    <p>Outliers Detected: {results['outlier_count']} students have scores that are significantly different from the rest of the class.</p>
                </div>
            """
        
        # Footer
        html_content += f"""
            </div>
            <div class="footer">
                <p>📋 This analysis was generated using the Exam Analysis Tool</p>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        """
        
        if student_info and student_info.get('teacher_name'):
            html_content += f"<p>Teacher: {student_info['teacher_name']}</p>"
        
        html_content += """
            </div>
        </body>
        </html>
        """
        
        return html_content