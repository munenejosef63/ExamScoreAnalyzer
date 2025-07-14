import os
import uuid
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Text, Float, Integer, JSON, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.dialects.postgresql import UUID
import streamlit as st
import pandas as pd
import json

Base = declarative_base()

class User(Base):
    """User model for multi-user support"""
    __tablename__ = 'users'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    institution = Column(String(100))
    role = Column(String(20), default='teacher')  # teacher, admin, student
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class ExamSession(Base):
    """Exam session model for persistent storage"""
    __tablename__ = 'exam_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    session_name = Column(String(100), nullable=False)
    exam_name = Column(String(100), nullable=False)
    class_name = Column(String(100))
    grade = Column(String(20))
    stream = Column(String(50))
    teacher_name = Column(String(100))
    exam_date = Column(DateTime)
    data_mode = Column(String(20), default='single_sheet')  # single_sheet, multi_sheet
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)

class StudentData(Base):
    """Student data model"""
    __tablename__ = 'student_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_session_id = Column(UUID(as_uuid=True), nullable=False)
    student_name = Column(String(100), nullable=False)
    total_score = Column(Float)
    subject_scores = Column(JSON)  # {subject: score}
    rank = Column(Integer)
    grade_letter = Column(String(5))
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalysisResults(Base):
    """Analysis results model"""
    __tablename__ = 'analysis_results'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    exam_session_id = Column(UUID(as_uuid=True), nullable=False)
    analysis_type = Column(String(50))  # statistical, ranking, historical
    results_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class HistoricalComparison(Base):
    """Historical comparison data"""
    __tablename__ = 'historical_comparisons'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)
    current_exam_id = Column(UUID(as_uuid=True), nullable=False)
    previous_exam_id = Column(UUID(as_uuid=True), nullable=False)
    comparison_data = Column(JSON)
    insights = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class DatabaseManager:
    """Comprehensive database management for exam analysis"""
    
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(self.database_url)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))
        
        # Create tables
        Base.metadata.create_all(self.engine)
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self):
        """Close database session"""
        self.SessionLocal.remove()
    
    # User Management
    def create_user(self, username, email, full_name, institution=None, role='teacher'):
        """Create a new user"""
        session = self.get_session()
        try:
            user = User(
                username=username,
                email=email,
                full_name=full_name,
                institution=institution,
                role=role
            )
            session.add(user)
            session.commit()
            return user.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_by_username(self, username):
        """Get user by username"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.username == username).first()
            return user
        finally:
            session.close()
    
    def update_user_activity(self, user_id):
        """Update user's last active timestamp"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_active = datetime.utcnow()
                session.commit()
        except Exception as e:
            session.rollback()
        finally:
            session.close()
    
    # Exam Session Management
    def create_exam_session(self, user_id, session_name, exam_info, data_mode='single_sheet'):
        """Create a new exam session"""
        session = self.get_session()
        try:
            exam_session = ExamSession(
                user_id=user_id,
                session_name=session_name,
                exam_name=exam_info.get('exam_name', ''),
                class_name=exam_info.get('class_name', ''),
                grade=exam_info.get('grade', ''),
                stream=exam_info.get('stream', ''),
                teacher_name=exam_info.get('teacher_name', ''),
                exam_date=exam_info.get('exam_date'),
                data_mode=data_mode
            )
            session.add(exam_session)
            session.commit()
            return exam_session.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_exam_sessions(self, user_id):
        """Get all exam sessions for a user"""
        session = self.get_session()
        try:
            sessions = session.query(ExamSession).filter(
                ExamSession.user_id == user_id,
                ExamSession.is_active == True
            ).order_by(ExamSession.created_at.desc()).all()
            return sessions
        finally:
            session.close()
    
    def get_exam_session(self, session_id):
        """Get specific exam session"""
        session = self.get_session()
        try:
            exam_session = session.query(ExamSession).filter(ExamSession.id == session_id).first()
            return exam_session
        finally:
            session.close()
    
    # Student Data Management
    def save_student_data(self, exam_session_id, students_data):
        """Save student data for an exam session"""
        session = self.get_session()
        try:
            # Clear existing data for this session
            session.query(StudentData).filter(StudentData.exam_session_id == exam_session_id).delete()
            
            # Add new data
            for student_name, data in students_data.items():
                student_record = StudentData(
                    exam_session_id=exam_session_id,
                    student_name=student_name,
                    total_score=data.get('Total', 0),
                    subject_scores={k: v for k, v in data.items() if k != 'Total'}
                )
                session.add(student_record)
            
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_student_data(self, exam_session_id):
        """Get student data for an exam session"""
        session = self.get_session()
        try:
            students = session.query(StudentData).filter(
                StudentData.exam_session_id == exam_session_id
            ).all()
            
            student_data = {}
            for student in students:
                student_data[student.student_name] = {
                    'Total': student.total_score,
                    **student.subject_scores
                }
            
            return student_data
        finally:
            session.close()
    
    # Analysis Results Management
    def save_analysis_results(self, exam_session_id, analysis_type, results):
        """Save analysis results"""
        session = self.get_session()
        try:
            analysis_result = AnalysisResults(
                exam_session_id=exam_session_id,
                analysis_type=analysis_type,
                results_data=results
            )
            session.add(analysis_result)
            session.commit()
            return analysis_result.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_analysis_results(self, exam_session_id, analysis_type=None):
        """Get analysis results for an exam session"""
        session = self.get_session()
        try:
            query = session.query(AnalysisResults).filter(
                AnalysisResults.exam_session_id == exam_session_id
            )
            
            if analysis_type:
                query = query.filter(AnalysisResults.analysis_type == analysis_type)
            
            results = query.order_by(AnalysisResults.created_at.desc()).all()
            return results
        finally:
            session.close()
    
    # Historical Comparison Management
    def save_historical_comparison(self, user_id, current_exam_id, previous_exam_id, comparison_data, insights):
        """Save historical comparison data"""
        session = self.get_session()
        try:
            comparison = HistoricalComparison(
                user_id=user_id,
                current_exam_id=current_exam_id,
                previous_exam_id=previous_exam_id,
                comparison_data=comparison_data,
                insights=insights
            )
            session.add(comparison)
            session.commit()
            return comparison.id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_historical_comparisons(self, user_id):
        """Get historical comparisons for a user"""
        session = self.get_session()
        try:
            comparisons = session.query(HistoricalComparison).filter(
                HistoricalComparison.user_id == user_id
            ).order_by(HistoricalComparison.created_at.desc()).all()
            return comparisons
        finally:
            session.close()
    
    # Export and Backup
    def export_user_data(self, user_id):
        """Export all user data for backup"""
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            exam_sessions = session.query(ExamSession).filter(ExamSession.user_id == user_id).all()
            
            export_data = {
                'user': {
                    'username': user.username,
                    'email': user.email,
                    'full_name': user.full_name,
                    'institution': user.institution,
                    'role': user.role,
                    'created_at': user.created_at.isoformat()
                },
                'exam_sessions': []
            }
            
            for exam_session in exam_sessions:
                session_data = {
                    'session_name': exam_session.session_name,
                    'exam_name': exam_session.exam_name,
                    'class_name': exam_session.class_name,
                    'grade': exam_session.grade,
                    'stream': exam_session.stream,
                    'teacher_name': exam_session.teacher_name,
                    'exam_date': exam_session.exam_date.isoformat() if exam_session.exam_date else None,
                    'data_mode': exam_session.data_mode,
                    'created_at': exam_session.created_at.isoformat(),
                    'students': [],
                    'analysis_results': []
                }
                
                # Get student data
                students = session.query(StudentData).filter(
                    StudentData.exam_session_id == exam_session.id
                ).all()
                
                for student in students:
                    session_data['students'].append({
                        'name': student.student_name,
                        'total_score': student.total_score,
                        'subject_scores': student.subject_scores,
                        'rank': student.rank,
                        'grade_letter': student.grade_letter
                    })
                
                # Get analysis results
                analysis_results = session.query(AnalysisResults).filter(
                    AnalysisResults.exam_session_id == exam_session.id
                ).all()
                
                for result in analysis_results:
                    session_data['analysis_results'].append({
                        'analysis_type': result.analysis_type,
                        'results_data': result.results_data,
                        'created_at': result.created_at.isoformat()
                    })
                
                export_data['exam_sessions'].append(session_data)
            
            return export_data
        finally:
            session.close()
    
    # Utility Methods
    def get_database_stats(self):
        """Get database usage statistics"""
        session = self.get_session()
        try:
            stats = {
                'total_users': session.query(User).count(),
                'active_users': session.query(User).filter(User.is_active == True).count(),
                'total_exam_sessions': session.query(ExamSession).count(),
                'total_students': session.query(StudentData).count(),
                'total_analysis_results': session.query(AnalysisResults).count(),
                'total_historical_comparisons': session.query(HistoricalComparison).count()
            }
            return stats
        finally:
            session.close()
    
    def cleanup_old_data(self, days=90):
        """Clean up old inactive data"""
        session = self.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Deactivate old exam sessions
            old_sessions = session.query(ExamSession).filter(
                ExamSession.updated_at < cutoff_date,
                ExamSession.is_active == True
            ).update({'is_active': False})
            
            session.commit()
            return old_sessions
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()