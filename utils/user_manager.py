import streamlit as st
import uuid
from datetime import datetime, timedelta
import hashlib
import secrets
from utils.database_manager import DatabaseManager

class UserManager:
    """Multi-user session management and authentication"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        
        # Initialize session state for multi-user support
        if 'user_authenticated' not in st.session_state:
            st.session_state.user_authenticated = False
        if 'current_user' not in st.session_state:
            st.session_state.current_user = None
        if 'user_sessions' not in st.session_state:
            st.session_state.user_sessions = {}
        if 'current_session_id' not in st.session_state:
            st.session_state.current_session_id = None
    
    def hash_password(self, password):
        """Hash password for security (simplified for demo)"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate_user(self, username, email, full_name, institution=None):
        """Authenticate or create user"""
        try:
            # Check if user exists
            user = self.db_manager.get_user_by_username(username)
            
            if not user:
                # Create new user
                user_id = self.db_manager.create_user(username, email, full_name, institution)
                user = self.db_manager.get_user_by_username(username)
            
            # Update last active
            self.db_manager.update_user_activity(user.id)
            
            # Set session state
            st.session_state.user_authenticated = True
            st.session_state.current_user = {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'institution': user.institution,
                'role': user.role,
                'last_active': user.last_active
            }
            
            return True, "Authentication successful"
        
        except Exception as e:
            return False, f"Authentication failed: {str(e)}"
    
    def logout_user(self):
        """Logout current user"""
        st.session_state.user_authenticated = False
        st.session_state.current_user = None
        st.session_state.current_session_id = None
        st.session_state.user_sessions = {}
    
    def get_current_user(self):
        """Get current authenticated user"""
        return st.session_state.current_user
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        return st.session_state.user_authenticated
    
    def create_exam_session(self, session_name, exam_info, data_mode='single_sheet'):
        """Create a new exam session for the current user"""
        if not self.is_authenticated():
            return None, "User not authenticated"
        
        try:
            user_id = st.session_state.current_user['id']
            session_id = self.db_manager.create_exam_session(user_id, session_name, exam_info, data_mode)
            
            # Store in session state for quick access
            st.session_state.current_session_id = str(session_id)
            
            return str(session_id), "Exam session created successfully"
        
        except Exception as e:
            return None, f"Failed to create exam session: {str(e)}"
    
    def load_exam_session(self, session_id):
        """Load an existing exam session"""
        try:
            exam_session = self.db_manager.get_exam_session(session_id)
            if not exam_session:
                return False, "Exam session not found"
            
            # Verify user ownership
            if str(exam_session.user_id) != st.session_state.current_user['id']:
                return False, "Access denied"
            
            # Load session data
            st.session_state.current_session_id = str(session_id)
            
            # Load student data
            student_data = self.db_manager.get_student_data(session_id)
            if student_data:
                st.session_state.multi_sheet_data = student_data
                st.session_state.data_mode = exam_session.data_mode
            
            # Load student info
            st.session_state.student_info = {
                'exam_name': exam_session.exam_name,
                'class_name': exam_session.class_name,
                'grade': exam_session.grade,
                'stream': exam_session.stream,
                'teacher_name': exam_session.teacher_name,
                'exam_date': exam_session.exam_date,
                'timestamp': exam_session.created_at
            }
            
            return True, "Exam session loaded successfully"
        
        except Exception as e:
            return False, f"Failed to load exam session: {str(e)}"
    
    def save_current_session_data(self, student_data):
        """Save current session data to database"""
        if not st.session_state.current_session_id:
            return False, "No active session"
        
        try:
            session_id = st.session_state.current_session_id
            self.db_manager.save_student_data(session_id, student_data)
            return True, "Session data saved successfully"
        
        except Exception as e:
            return False, f"Failed to save session data: {str(e)}"
    
    def get_user_sessions(self):
        """Get all exam sessions for current user"""
        if not self.is_authenticated():
            return []
        
        try:
            user_id = st.session_state.current_user['id']
            sessions = self.db_manager.get_user_exam_sessions(user_id)
            return sessions
        
        except Exception as e:
            st.error(f"Failed to load user sessions: {str(e)}")
            return []
    
    def delete_exam_session(self, session_id):
        """Delete an exam session (soft delete)"""
        try:
            exam_session = self.db_manager.get_exam_session(session_id)
            if not exam_session:
                return False, "Session not found"
            
            # Verify user ownership
            if str(exam_session.user_id) != st.session_state.current_user['id']:
                return False, "Access denied"
            
            # Soft delete by marking as inactive
            session = self.db_manager.get_session()
            exam_session.is_active = False
            session.commit()
            session.close()
            
            return True, "Session deleted successfully"
        
        except Exception as e:
            return False, f"Failed to delete session: {str(e)}"
    
    def save_analysis_results(self, analysis_type, results):
        """Save analysis results for current session"""
        if not st.session_state.current_session_id:
            return False, "No active session"
        
        try:
            session_id = st.session_state.current_session_id
            result_id = self.db_manager.save_analysis_results(session_id, analysis_type, results)
            return True, f"Analysis results saved with ID: {result_id}"
        
        except Exception as e:
            return False, f"Failed to save analysis results: {str(e)}"
    
    def get_analysis_history(self, analysis_type=None):
        """Get analysis history for current session"""
        if not st.session_state.current_session_id:
            return []
        
        try:
            session_id = st.session_state.current_session_id
            results = self.db_manager.get_analysis_results(session_id, analysis_type)
            return results
        
        except Exception as e:
            st.error(f"Failed to load analysis history: {str(e)}")
            return []
    
    def export_user_data(self):
        """Export all user data"""
        if not self.is_authenticated():
            return None, "User not authenticated"
        
        try:
            user_id = st.session_state.current_user['id']
            export_data = self.db_manager.export_user_data(user_id)
            return export_data, "Data exported successfully"
        
        except Exception as e:
            return None, f"Failed to export data: {str(e)}"
    
    def get_session_analytics(self):
        """Get analytics for user sessions"""
        if not self.is_authenticated():
            return {}
        
        try:
            sessions = self.get_user_sessions()
            analytics = {
                'total_sessions': len(sessions),
                'active_sessions': len([s for s in sessions if s.is_active]),
                'data_modes': {},
                'recent_activity': []
            }
            
            for session in sessions:
                # Count data modes
                mode = session.data_mode
                analytics['data_modes'][mode] = analytics['data_modes'].get(mode, 0) + 1
                
                # Recent activity
                if session.updated_at:
                    analytics['recent_activity'].append({
                        'session_name': session.session_name,
                        'exam_name': session.exam_name,
                        'updated_at': session.updated_at,
                        'data_mode': session.data_mode
                    })
            
            # Sort recent activity
            analytics['recent_activity'].sort(key=lambda x: x['updated_at'], reverse=True)
            analytics['recent_activity'] = analytics['recent_activity'][:10]  # Top 10
            
            return analytics
        
        except Exception as e:
            st.error(f"Failed to get session analytics: {str(e)}")
            return {}

def display_user_authentication():
    """Display user authentication interface"""
    user_manager = UserManager()
    
    if not user_manager.is_authenticated():
        st.markdown("### 👤 User Authentication")
        st.info("Please provide your details to access the exam analysis system")
        
        with st.form("auth_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Username:", help="Unique identifier for your account")
                full_name = st.text_input("Full Name:", help="Your complete name")
            
            with col2:
                email = st.text_input("Email:", help="Your email address")
                institution = st.text_input("Institution (optional):", help="School, college, or organization")
            
            submit_button = st.form_submit_button("Login / Create Account", type="primary")
            
            if submit_button:
                if username and email and full_name:
                    success, message = user_manager.authenticate_user(username, email, full_name, institution)
                    
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please fill in all required fields")
        
        return False
    
    return True

def display_session_management():
    """Display session management interface"""
    user_manager = UserManager()
    
    if not user_manager.is_authenticated():
        return
    
    current_user = user_manager.get_current_user()
    
    # User info display
    st.sidebar.markdown(f"**Welcome, {current_user['full_name']}!**")
    st.sidebar.markdown(f"*{current_user['institution'] or 'No institution'}*")
    
    # Session management
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📂 Session Management")
    
    # Current session info
    if st.session_state.current_session_id:
        st.sidebar.success(f"Active Session: {st.session_state.student_info.get('exam_name', 'Unnamed')}")
        
        if st.sidebar.button("💾 Save Current Session"):
            if 'multi_sheet_data' in st.session_state:
                success, message = user_manager.save_current_session_data(st.session_state.multi_sheet_data)
                if success:
                    st.sidebar.success("Session saved!")
                else:
                    st.sidebar.error(message)
    
    # Load existing sessions
    sessions = user_manager.get_user_sessions()
    if sessions:
        st.sidebar.markdown("**Load Previous Sessions:**")
        
        session_options = {f"{s.exam_name} ({s.class_name}) - {s.created_at.strftime('%Y-%m-%d')}": str(s.id) 
                          for s in sessions if s.is_active}
        
        if session_options:
            selected_session = st.sidebar.selectbox("Choose session:", ["New Session"] + list(session_options.keys()))
            
            if selected_session != "New Session":
                session_id = session_options[selected_session]
                
                col1, col2 = st.sidebar.columns(2)
                with col1:
                    if st.button("📂 Load"):
                        success, message = user_manager.load_exam_session(session_id)
                        if success:
                            st.sidebar.success("Session loaded!")
                            st.rerun()
                        else:
                            st.sidebar.error(message)
                
                with col2:
                    if st.button("🗑️ Delete"):
                        success, message = user_manager.delete_exam_session(session_id)
                        if success:
                            st.sidebar.success("Session deleted!")
                            st.rerun()
                        else:
                            st.sidebar.error(message)
    
    # User analytics
    analytics = user_manager.get_session_analytics()
    if analytics:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 📊 Your Analytics")
        st.sidebar.metric("Total Sessions", analytics['total_sessions'])
        st.sidebar.metric("Active Sessions", analytics['active_sessions'])
    
    # Logout button
    st.sidebar.markdown("---")
    if st.sidebar.button("🚪 Logout"):
        user_manager.logout_user()
        st.rerun()
    
    return user_manager