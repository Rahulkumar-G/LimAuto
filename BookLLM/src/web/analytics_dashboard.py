"""
Advanced Analytics and Reporting Dashboard
Enterprise-grade analytics with real-time insights and business intelligence
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
from sqlalchemy import func, and_, or_, text
import pandas as pd
import numpy as np

from .app import db, User, BookProject, GenerationLog, ProjectAnalytics, redis_client
from .subscription_manager import subscription_manager, SUBSCRIPTION_PLANS
from ..utils.logger import get_logger

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')
logger = get_logger(__name__)

class AnalyticsEngine:
    """Advanced analytics engine with real-time processing"""
    
    def __init__(self):
        self.redis = redis_client
        self.logger = logger
    
    def get_user_analytics(self, user_id: str, date_range: int = 30) -> Dict[str, Any]:
        """Comprehensive user analytics"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=date_range)
            
            # Basic project statistics
            projects_stats = self._get_projects_stats(user_id, start_date, end_date)
            
            # Quality analytics
            quality_stats = self._get_quality_analytics(user_id, start_date, end_date)
            
            # Performance analytics
            performance_stats = self._get_performance_analytics(user_id, start_date, end_date)
            
            # Usage patterns
            usage_patterns = self._get_usage_patterns(user_id, date_range)
            
            # Productivity insights
            productivity_insights = self._get_productivity_insights(user_id, start_date, end_date)
            
            return {
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat(),
                    'days': date_range
                },
                'projects': projects_stats,
                'quality': quality_stats,
                'performance': performance_stats,
                'usage_patterns': usage_patterns,
                'productivity': productivity_insights,
                'generated_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"User analytics error: {e}")
            return {}
    
    def _get_projects_stats(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get project-related statistics"""
        
        # Total projects created in period
        projects_created = BookProject.query.filter(
            BookProject.user_id == user_id,
            BookProject.created_at.between(start_date, end_date)
        ).count()
        
        # Projects completed in period
        projects_completed = BookProject.query.filter(
            BookProject.user_id == user_id,
            BookProject.status == 'completed',
            BookProject.completed_at.between(start_date, end_date)
        ).count()
        
        # Total word count
        total_words = db.session.query(func.sum(BookProject.word_count)).filter(
            BookProject.user_id == user_id,
            BookProject.completed_at.between(start_date, end_date)
        ).scalar() or 0
        
        # Average completion time
        avg_completion_time = db.session.query(
            func.avg(
                func.extract('epoch', BookProject.completed_at - BookProject.created_at) / 3600
            )
        ).filter(
            BookProject.user_id == user_id,
            BookProject.status == 'completed',
            BookProject.completed_at.between(start_date, end_date)
        ).scalar() or 0
        
        # Projects by status
        status_breakdown = db.session.query(
            BookProject.status,
            func.count(BookProject.id)
        ).filter(
            BookProject.user_id == user_id,
            BookProject.created_at.between(start_date, end_date)
        ).group_by(BookProject.status).all()
        
        # Daily project creation trend
        daily_trend = db.session.query(
            func.date(BookProject.created_at).label('date'),
            func.count(BookProject.id).label('count')
        ).filter(
            BookProject.user_id == user_id,
            BookProject.created_at.between(start_date, end_date)
        ).group_by(func.date(BookProject.created_at)).order_by('date').all()
        
        return {
            'total_created': projects_created,
            'total_completed': projects_completed,
            'completion_rate': (projects_completed / max(projects_created, 1)) * 100,
            'total_words': int(total_words),
            'average_completion_hours': round(avg_completion_time, 2),
            'status_breakdown': {status: count for status, count in status_breakdown},
            'daily_trend': [
                {'date': date.isoformat(), 'projects': count}
                for date, count in daily_trend
            ]
        }
    
    def _get_quality_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get quality-related analytics"""
        
        # Average quality score
        avg_quality = db.session.query(func.avg(BookProject.quality_score)).filter(
            BookProject.user_id == user_id,
            BookProject.quality_score.isnot(None),
            BookProject.completed_at.between(start_date, end_date)
        ).scalar() or 0
        
        # Quality distribution
        quality_ranges = [
            ('Excellent (90-100)', 90, 100),
            ('Good (80-89)', 80, 89),
            ('Average (70-79)', 70, 79),
            ('Below Average (60-69)', 60, 69),
            ('Poor (<60)', 0, 59)
        ]
        
        quality_distribution = {}
        for label, min_score, max_score in quality_ranges:
            count = BookProject.query.filter(
                BookProject.user_id == user_id,
                BookProject.quality_score.between(min_score, max_score),
                BookProject.completed_at.between(start_date, end_date)
            ).count()
            quality_distribution[label] = count
        
        # Quality trend over time
        quality_trend = db.session.query(
            func.date(BookProject.completed_at).label('date'),
            func.avg(BookProject.quality_score).label('avg_quality')
        ).filter(
            BookProject.user_id == user_id,
            BookProject.quality_score.isnot(None),
            BookProject.completed_at.between(start_date, end_date)
        ).group_by(func.date(BookProject.completed_at)).order_by('date').all()
        
        # Quality improvement rate
        if len(quality_trend) >= 2:
            first_week_avg = sum(q.avg_quality for q in quality_trend[:7]) / min(7, len(quality_trend))
            last_week_avg = sum(q.avg_quality for q in quality_trend[-7:]) / min(7, len(quality_trend))
            improvement_rate = ((last_week_avg - first_week_avg) / max(first_week_avg, 1)) * 100
        else:
            improvement_rate = 0
        
        return {
            'average_score': round(avg_quality, 2),
            'grade': self._get_quality_grade(avg_quality),
            'distribution': quality_distribution,
            'improvement_rate': round(improvement_rate, 2),
            'trend': [
                {'date': date.isoformat(), 'quality': round(float(avg_qual), 2)}
                for date, avg_qual in quality_trend
            ]
        }
    
    def _get_performance_analytics(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get performance-related analytics"""
        
        # Generation speed (words per hour)
        generation_logs = GenerationLog.query.join(BookProject).filter(
            BookProject.user_id == user_id,
            GenerationLog.status == 'completed',
            GenerationLog.start_time.between(start_date, end_date)
        ).all()
        
        speeds = []
        costs = []
        token_usage = []
        
        for log in generation_logs:
            if log.end_time and log.start_time:
                duration_hours = (log.end_time - log.start_time).total_seconds() / 3600
                if duration_hours > 0 and log.project.word_count:
                    speed = log.project.word_count / duration_hours
                    speeds.append(speed)
            
            if log.cost_usd:
                costs.append(log.cost_usd)
            
            if log.tokens_used:
                token_usage.append(log.tokens_used)
        
        avg_speed = sum(speeds) / len(speeds) if speeds else 0
        total_cost = sum(costs)
        total_tokens = sum(token_usage)
        
        # Agent performance breakdown
        agent_performance = db.session.query(
            GenerationLog.agent_name,
            func.avg(GenerationLog.quality_score).label('avg_quality'),
            func.avg(
                func.extract('epoch', GenerationLog.end_time - GenerationLog.start_time) / 60
            ).label('avg_duration_minutes'),
            func.count(GenerationLog.id).label('runs')
        ).join(BookProject).filter(
            BookProject.user_id == user_id,
            GenerationLog.status == 'completed',
            GenerationLog.start_time.between(start_date, end_date)
        ).group_by(GenerationLog.agent_name).all()
        
        # Peak usage hours
        hourly_usage = db.session.query(
            func.extract('hour', GenerationLog.start_time).label('hour'),
            func.count(GenerationLog.id).label('count')
        ).join(BookProject).filter(
            BookProject.user_id == user_id,
            GenerationLog.start_time.between(start_date, end_date)
        ).group_by(func.extract('hour', GenerationLog.start_time)).all()
        
        return {
            'average_speed_wph': round(avg_speed, 2),
            'total_cost_usd': round(total_cost, 2),
            'total_tokens': total_tokens,
            'average_cost_per_word': round(total_cost / max(sum(p.word_count for p in BookProject.query.filter_by(user_id=user_id).all()), 1), 4),
            'agent_performance': [
                {
                    'agent': agent,
                    'avg_quality': round(float(avg_qual or 0), 2),
                    'avg_duration_minutes': round(float(avg_dur or 0), 2),
                    'total_runs': runs
                }
                for agent, avg_qual, avg_dur, runs in agent_performance
            ],
            'peak_hours': [
                {'hour': int(hour), 'usage_count': count}
                for hour, count in hourly_usage
            ]
        }
    
    def _get_usage_patterns(self, user_id: str, date_range: int) -> Dict[str, Any]:
        """Analyze usage patterns and habits"""
        
        # Get hourly usage pattern
        hourly_pattern = {}
        for hour in range(24):
            cache_key = f"usage_pattern:{user_id}:hour:{hour}"
            count = self.redis.get(cache_key) or 0
            hourly_pattern[str(hour)] = int(count)
        
        # Get weekly pattern
        weekly_pattern = {}
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        for i, day in enumerate(days):
            cache_key = f"usage_pattern:{user_id}:day:{i}"
            count = self.redis.get(cache_key) or 0
            weekly_pattern[day] = int(count)
        
        # Most productive day and hour
        most_productive_hour = max(hourly_pattern.items(), key=lambda x: x[1])
        most_productive_day = max(weekly_pattern.items(), key=lambda x: x[1])
        
        # Session analysis
        sessions = self._analyze_user_sessions(user_id, date_range)
        
        return {
            'hourly_pattern': hourly_pattern,
            'weekly_pattern': weekly_pattern,
            'most_productive_hour': f"{most_productive_hour[0]}:00",
            'most_productive_day': most_productive_day[0],
            'sessions': sessions,
            'usage_consistency': self._calculate_usage_consistency(hourly_pattern, weekly_pattern)
        }
    
    def _get_productivity_insights(self, user_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Generate productivity insights and recommendations"""
        
        user = User.query.get(user_id)
        plan_limits = SUBSCRIPTION_PLANS[user.subscription_tier]['features']
        
        # Current utilization
        current_usage = subscription_manager._get_current_usage(user)
        
        book_utilization = 0
        if plan_limits['books_per_month'] > 0:
            book_utilization = (current_usage['books_this_month'] / plan_limits['books_per_month']) * 100
        
        word_utilization = 0
        if plan_limits['words_per_month'] > 0:
            word_utilization = (current_usage['words_this_month'] / plan_limits['words_per_month']) * 100
        
        # Efficiency metrics
        projects_this_period = BookProject.query.filter(
            BookProject.user_id == user_id,
            BookProject.created_at.between(start_date, end_date)
        ).all()
        
        if projects_this_period:
            avg_project_size = sum(p.word_count or 0 for p in projects_this_period) / len(projects_this_period)
            completion_rate = len([p for p in projects_this_period if p.status == 'completed']) / len(projects_this_period) * 100
        else:
            avg_project_size = 0
            completion_rate = 0
        
        # Generate recommendations
        recommendations = self._generate_productivity_recommendations(
            user, current_usage, book_utilization, word_utilization, completion_rate
        )
        
        return {
            'plan_utilization': {
                'books': round(book_utilization, 1),
                'words': round(word_utilization, 1),
                'api_calls': (current_usage['api_calls_today'] / max(plan_limits['api_calls_per_day'], 1)) * 100
            },
            'efficiency_metrics': {
                'average_project_size': round(avg_project_size, 0),
                'completion_rate': round(completion_rate, 1),
                'projects_this_period': len(projects_this_period)
            },
            'recommendations': recommendations,
            'productivity_score': self._calculate_productivity_score(
                completion_rate, avg_project_size, book_utilization
            )
        }
    
    def _analyze_user_sessions(self, user_id: str, date_range: int) -> Dict[str, Any]:
        """Analyze user session patterns"""
        # This would analyze login patterns, session durations, etc.
        # For now, return mock data structure
        return {
            'average_session_duration': 45,  # minutes
            'total_sessions': 12,
            'sessions_per_day': 1.2,
            'longest_session': 120,  # minutes
            'shortest_session': 15   # minutes
        }
    
    def _calculate_usage_consistency(self, hourly_pattern: Dict, weekly_pattern: Dict) -> float:
        """Calculate how consistent the user's usage patterns are"""
        hourly_values = list(hourly_pattern.values())
        weekly_values = list(weekly_pattern.values())
        
        # Calculate coefficient of variation
        if hourly_values and weekly_values:
            hourly_cv = np.std(hourly_values) / (np.mean(hourly_values) + 1)
            weekly_cv = np.std(weekly_values) / (np.mean(weekly_values) + 1)
            consistency = max(0, 100 - ((hourly_cv + weekly_cv) * 50))
        else:
            consistency = 0
        
        return round(consistency, 1)
    
    def _generate_productivity_recommendations(self, user: User, usage: Dict, 
                                            book_util: float, word_util: float, 
                                            completion_rate: float) -> List[str]:
        """Generate personalized productivity recommendations"""
        recommendations = []
        
        if completion_rate < 50:
            recommendations.append("Consider breaking large projects into smaller, manageable chunks to improve completion rates.")
        
        if book_util > 80:
            recommendations.append("You're approaching your monthly book limit. Consider upgrading to continue generating books.")
        
        if word_util > 80:
            recommendations.append("You're approaching your monthly word limit. Optimize your content or consider upgrading.")
        
        if user.subscription_tier == 'free':
            recommendations.append("Upgrade to Pro for unlimited books, advanced templates, and collaboration features.")
        
        if completion_rate > 80:
            recommendations.append("Great completion rate! Consider taking on more ambitious projects.")
        
        return recommendations[:3]  # Limit to top 3 recommendations
    
    def _calculate_productivity_score(self, completion_rate: float, 
                                    avg_project_size: float, 
                                    utilization: float) -> int:
        """Calculate overall productivity score (0-100)"""
        score = (
            completion_rate * 0.4 +
            min(utilization, 100) * 0.3 +
            min(avg_project_size / 1000, 100) * 0.3
        )
        return round(score, 0)
    
    def _get_quality_grade(self, score: float) -> str:
        """Convert quality score to letter grade"""
        if score >= 95:
            return 'A+'
        elif score >= 90:
            return 'A'
        elif score >= 85:
            return 'B+'
        elif score >= 80:
            return 'B'
        elif score >= 75:
            return 'C+'
        elif score >= 70:
            return 'C'
        else:
            return 'D'

# Initialize analytics engine
analytics_engine = AnalyticsEngine()

@analytics_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard"""
    try:
        user_id = get_jwt_identity()
        date_range = request.args.get('date_range', 30, type=int)
        
        # Validate date range
        if date_range not in [7, 30, 90, 365]:
            date_range = 30
        
        analytics_data = analytics_engine.get_user_analytics(user_id, date_range)
        
        return jsonify({
            'status': 'success',
            'data': analytics_data
        }), 200
        
    except Exception as e:
        logger.error(f"Analytics dashboard error: {e}")
        return jsonify({'error': 'Failed to load analytics dashboard'}), 500

@analytics_bp.route('/export', methods=['POST'])
@jwt_required()
def export_analytics():
    """Export analytics data in various formats"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        export_format = data.get('format', 'json')  # json, csv, pdf
        date_range = data.get('date_range', 30)
        sections = data.get('sections', ['all'])  # projects, quality, performance, etc.
        
        if export_format not in ['json', 'csv', 'pdf']:
            return jsonify({'error': 'Invalid export format'}), 400
        
        # Get analytics data
        analytics_data = analytics_engine.get_user_analytics(user_id, date_range)
        
        if export_format == 'json':
            return jsonify(analytics_data), 200
        
        elif export_format == 'csv':
            # Convert to CSV format
            csv_data = analytics_engine.export_to_csv(analytics_data, sections)
            return csv_data, 200, {
                'Content-Type': 'text/csv',
                'Content-Disposition': f'attachment; filename=analytics_{user_id}_{date_range}days.csv'
            }
        
        elif export_format == 'pdf':
            # Generate PDF report
            pdf_data = analytics_engine.export_to_pdf(analytics_data, sections)
            return pdf_data, 200, {
                'Content-Type': 'application/pdf',
                'Content-Disposition': f'attachment; filename=analytics_report_{user_id}.pdf'
            }
        
    except Exception as e:
        logger.error(f"Analytics export error: {e}")
        return jsonify({'error': 'Failed to export analytics'}), 500

@analytics_bp.route('/realtime', methods=['GET'])
@jwt_required()
def get_realtime_metrics():
    """Get real-time metrics for live dashboard"""
    try:
        user_id = get_jwt_identity()
        
        # Get real-time metrics from Redis
        current_sessions = analytics_engine.redis.scard(f"active_sessions:{user_id}")
        projects_generating = BookProject.query.filter_by(
            user_id=user_id,
            status='generating'
        ).count()
        
        # API calls in last hour
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_activity = GenerationLog.query.join(BookProject).filter(
            BookProject.user_id == user_id,
            GenerationLog.start_time >= hour_ago
        ).count()
        
        # Current usage
        user = User.query.get(user_id)
        current_usage = subscription_manager._get_current_usage(user)
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat(),
            'live_metrics': {
                'active_sessions': current_sessions,
                'projects_generating': projects_generating,
                'recent_activity_hour': recent_activity,
                'api_calls_today': current_usage['api_calls_today'],
                'books_this_month': current_usage['books_this_month'],
                'words_this_month': current_usage['words_this_month']
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Real-time metrics error: {e}")
        return jsonify({'error': 'Failed to load real-time metrics'}), 500

@analytics_bp.route('/insights', methods=['GET'])
@jwt_required()
def get_ai_insights():
    """Get AI-powered insights and recommendations"""
    try:
        user_id = get_jwt_identity()
        
        # Get comprehensive analytics
        analytics_data = analytics_engine.get_user_analytics(user_id, 30)
        
        # Generate AI insights
        insights = {
            'performance_trends': analytics_engine._analyze_performance_trends(analytics_data),
            'optimization_opportunities': analytics_engine._identify_optimization_opportunities(analytics_data),
            'growth_predictions': analytics_engine._predict_growth_trajectory(analytics_data),
            'benchmarking': analytics_engine._benchmark_against_peers(user_id, analytics_data)
        }
        
        return jsonify({
            'insights': insights,
            'confidence_score': 85,  # AI confidence in insights
            'generated_at': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"AI insights error: {e}")
        return jsonify({'error': 'Failed to generate insights'}), 500