import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.database_manager import DatabaseManager
from utils.user_manager import UserManager
import plotly.express as px
import plotly.graph_objects as go

class AdminDashboard:
    """Administrative dashboard for system management"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.user_manager = UserManager()
    
    def display_dashboard(self):
        """Display the main admin dashboard"""
        if not self._check_admin_access():
            st.error("Access denied. Admin privileges required.")
            return
        
        st.header("🔧 Administrative Dashboard")
        
        # Dashboard tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "👥 Users", "📁 Sessions", "🗄️ Database"])
        
        with tab1:
            self._display_overview()
        
        with tab2:
            self._display_user_management()
        
        with tab3:
            self._display_session_management()
        
        with tab4:
            self._display_database_management()
    
    def _check_admin_access(self):
        """Check if current user has admin access"""
        current_user = self.user_manager.get_current_user()
        return current_user and current_user.get('role') == 'admin'
    
    def _display_overview(self):
        """Display system overview and statistics"""
        st.subheader("📊 System Overview")
        
        # Get database statistics
        stats = self.db_manager.get_database_stats()
        
        # Display key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", stats.get('total_users', 0))
        
        with col2:
            st.metric("Active Users", stats.get('active_users', 0))
        
        with col3:
            st.metric("Total Sessions", stats.get('total_exam_sessions', 0))
        
        with col4:
            st.metric("Total Students", stats.get('total_students', 0))
        
        # Usage trends
        st.subheader("📈 Usage Trends")
        
        try:
            # Get recent activity data
            session = self.db_manager.get_session()
            
            # Users created over time
            from utils.database_manager import User, ExamSession
            users_df = pd.read_sql(
                session.query(User.created_at).statement,
                session.bind
            )
            
            if not users_df.empty:
                users_df['created_at'] = pd.to_datetime(users_df['created_at'])
                users_df['date'] = users_df['created_at'].dt.date
                daily_users = users_df.groupby('date').size().reset_index(name='new_users')
                
                fig_users = px.line(daily_users, x='date', y='new_users', 
                                  title='New Users Per Day')
                st.plotly_chart(fig_users, use_container_width=True)
            
            # Exam sessions over time
            sessions_df = pd.read_sql(
                session.query(ExamSession.created_at, ExamSession.data_mode).statement,
                session.bind
            )
            
            if not sessions_df.empty:
                sessions_df['created_at'] = pd.to_datetime(sessions_df['created_at'])
                sessions_df['date'] = sessions_df['created_at'].dt.date
                daily_sessions = sessions_df.groupby(['date', 'data_mode']).size().reset_index(name='sessions')
                
                fig_sessions = px.bar(daily_sessions, x='date', y='sessions', 
                                    color='data_mode', title='Exam Sessions Per Day')
                st.plotly_chart(fig_sessions, use_container_width=True)
            
            session.close()
            
        except Exception as e:
            st.warning(f"Could not load trend data: {str(e)}")
    
    def _display_user_management(self):
        """Display user management interface"""
        st.subheader("👥 User Management")
        
        try:
            # Get all users
            session = self.db_manager.get_session()
            from utils.database_manager import User
            
            users_query = session.query(User).all()
            
            if users_query:
                users_data = []
                for user in users_query:
                    users_data.append({
                        'ID': str(user.id),
                        'Username': user.username,
                        'Full Name': user.full_name,
                        'Email': user.email,
                        'Institution': user.institution or 'N/A',
                        'Role': user.role,
                        'Created': user.created_at.strftime('%Y-%m-%d'),
                        'Last Active': user.last_active.strftime('%Y-%m-%d %H:%M') if user.last_active else 'Never',
                        'Status': 'Active' if user.is_active else 'Inactive'
                    })
                
                users_df = pd.DataFrame(users_data)
                st.dataframe(users_df, use_container_width=True)
                
                # User actions
                st.subheader("User Actions")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Deactivate user
                    user_to_deactivate = st.selectbox(
                        "Deactivate User:",
                        options=['Select user...'] + [f"{u.username} ({u.full_name})" for u in users_query if u.is_active]
                    )
                    
                    if st.button("Deactivate User") and user_to_deactivate != 'Select user...':
                        username = user_to_deactivate.split(' (')[0]
                        user = session.query(User).filter(User.username == username).first()
                        if user:
                            user.is_active = False
                            session.commit()
                            st.success(f"User {username} deactivated")
                            st.rerun()
                
                with col2:
                    # Promote to admin
                    user_to_promote = st.selectbox(
                        "Promote to Admin:",
                        options=['Select user...'] + [f"{u.username} ({u.full_name})" for u in users_query if u.role != 'admin']
                    )
                    
                    if st.button("Promote to Admin") and user_to_promote != 'Select user...':
                        username = user_to_promote.split(' (')[0]
                        user = session.query(User).filter(User.username == username).first()
                        if user:
                            user.role = 'admin'
                            session.commit()
                            st.success(f"User {username} promoted to admin")
                            st.rerun()
            
            else:
                st.info("No users found in the system")
            
            session.close()
            
        except Exception as e:
            st.error(f"Error loading users: {str(e)}")
    
    def _display_session_management(self):
        """Display exam session management"""
        st.subheader("📁 Session Management")
        
        try:
            session = self.db_manager.get_session()
            from utils.database_manager import ExamSession, User
            
            # Get all exam sessions with user info
            sessions_query = session.query(ExamSession, User).join(
                User, ExamSession.user_id == User.id
            ).order_by(ExamSession.created_at.desc()).all()
            
            if sessions_query:
                sessions_data = []
                for exam_session, user in sessions_query:
                    sessions_data.append({
                        'Session ID': str(exam_session.id)[:8] + '...',
                        'Session Name': exam_session.session_name,
                        'Exam Name': exam_session.exam_name,
                        'Class': exam_session.class_name or 'N/A',
                        'User': user.full_name,
                        'Data Mode': exam_session.data_mode,
                        'Created': exam_session.created_at.strftime('%Y-%m-%d %H:%M'),
                        'Updated': exam_session.updated_at.strftime('%Y-%m-%d %H:%M'),
                        'Status': 'Active' if exam_session.is_active else 'Inactive'
                    })
                
                sessions_df = pd.DataFrame(sessions_data)
                st.dataframe(sessions_df, use_container_width=True)
                
                # Session statistics
                st.subheader("Session Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    active_sessions = sum(1 for s, u in sessions_query if s.is_active)
                    st.metric("Active Sessions", active_sessions)
                
                with col2:
                    multi_sheet_sessions = sum(1 for s, u in sessions_query if s.data_mode == 'multi_sheet')
                    st.metric("Multi-Sheet Sessions", multi_sheet_sessions)
                
                with col3:
                    recent_sessions = sum(1 for s, u in sessions_query 
                                        if s.updated_at > datetime.utcnow() - timedelta(days=7))
                    st.metric("Recent Activity (7 days)", recent_sessions)
            
            else:
                st.info("No exam sessions found")
            
            session.close()
            
        except Exception as e:
            st.error(f"Error loading sessions: {str(e)}")
    
    def _display_database_management(self):
        """Display database management tools"""
        st.subheader("🗄️ Database Management")
        
        # Database statistics
        stats = self.db_manager.get_database_stats()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Analysis Results", stats.get('total_analysis_results', 0))
            st.metric("Historical Comparisons", stats.get('total_historical_comparisons', 0))
        
        with col2:
            # Database cleanup
            st.subheader("🧹 Cleanup Tools")
            
            cleanup_days = st.number_input(
                "Cleanup data older than (days):",
                min_value=30,
                max_value=365,
                value=90,
                help="Mark exam sessions as inactive if not updated for this many days"
            )
            
            if st.button("🗑️ Cleanup Old Data"):
                try:
                    cleaned_count = self.db_manager.cleanup_old_data(cleanup_days)
                    st.success(f"Cleaned up {cleaned_count} old sessions")
                except Exception as e:
                    st.error(f"Cleanup failed: {str(e)}")
        
        # Data export
        st.subheader("📤 System Data Export")
        
        if st.button("📄 Export System Data"):
            try:
                # Get all users and export their data
                session = self.db_manager.get_session()
                from utils.database_manager import User
                
                users = session.query(User).all()
                export_data = {
                    'export_timestamp': datetime.now().isoformat(),
                    'system_stats': stats,
                    'users': []
                }
                
                for user in users:
                    user_data = self.db_manager.export_user_data(user.id)
                    if user_data:
                        export_data['users'].append(user_data)
                
                session.close()
                
                # Create download
                import json
                json_data = json.dumps(export_data, indent=2, default=str).encode('utf-8')
                
                st.download_button(
                    label="📄 Download System Export",
                    data=json_data,
                    file_name=f"system_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                st.success("System data exported successfully")
                
            except Exception as e:
                st.error(f"Export failed: {str(e)}")

def display_admin_interface():
    """Display admin interface if user has admin privileges"""
    user_manager = UserManager()
    
    if not user_manager.is_authenticated():
        return False
    
    current_user = user_manager.get_current_user()
    if current_user and current_user.get('role') == 'admin':
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔧 Admin Panel")
        
        if st.sidebar.button("📊 Admin Dashboard"):
            st.session_state.show_admin_dashboard = True
        
        if getattr(st.session_state, 'show_admin_dashboard', False):
            admin_dashboard = AdminDashboard()
            admin_dashboard.display_dashboard()
            
            if st.button("← Back to Main App"):
                st.session_state.show_admin_dashboard = False
                st.rerun()
            
            return True
    
    return False