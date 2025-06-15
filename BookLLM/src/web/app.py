"""
Production-Grade BookLLM Web Application
Advanced features for professional book generation with real-time collaboration
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import asyncio
import threading
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import redis
import celery
from celery import Celery
import stripe
import logging

from ..api_enhanced import ui_orchestrator, health_checker
from ..ui.orchestrator_integration import create_ui_integrated_book_generator
from ..utils.logger import get_logger

# Initialize Flask app with production configuration
app = Flask(__name__)
app.config.update(
    SECRET_KEY='your-secret-key-change-in-production',
    SQLALCHEMY_DATABASE_URI='postgresql://user:password@localhost/booklm_prod',
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    JWT_SECRET_KEY='jwt-secret-change-in-production',
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(hours=24),
    REDIS_URL='redis://localhost:6379/0',
    CELERY_BROKER_URL='redis://localhost:6379/0',
    CELERY_RESULT_BACKEND='redis://localhost:6379/0',
    STRIPE_PUBLISHABLE_KEY='pk_test_your_stripe_key',
    STRIPE_SECRET_KEY='sk_test_your_stripe_key',
    UPLOAD_FOLDER='uploads/',
    MAX_CONTENT_LENGTH=16 * 1024 * 1024  # 16MB max file size
)

# Initialize extensions
CORS(app, origins=["http://localhost:3000", "https://yourdomain.com"])
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = JWTManager(app)
logger = get_logger(__name__)

# Initialize Redis for caching and real-time features
redis_client = redis.Redis.from_url(app.config['REDIS_URL'])

# Initialize Celery for background tasks
celery_app = Celery(
    app.import_name,
    broker=app.config['CELERY_BROKER_URL'],
    backend=app.config['CELERY_RESULT_BACKEND']
)

# Initialize Stripe for payments
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# Database Models
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    subscription_tier = db.Column(db.String(50), default='free')  # free, pro, enterprise
    subscription_status = db.Column(db.String(50), default='active')
    stripe_customer_id = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Usage tracking
    books_generated = db.Column(db.Integer, default=0)
    words_generated = db.Column(db.Integer, default=0)
    api_calls_today = db.Column(db.Integer, default=0)
    last_api_reset = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    projects = db.relationship('BookProject', backref='author', lazy=True, cascade='all, delete-orphan')
    collaborations = db.relationship('ProjectCollaborator', backref='user', lazy=True)

class BookProject(db.Model):
    __tablename__ = 'book_projects'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)
    target_audience = db.Column(db.String(100), default='professional')
    book_style = db.Column(db.String(100), default='authoritative')
    estimated_pages = db.Column(db.Integer, default=200)
    
    # Status and progress
    status = db.Column(db.String(50), default='draft')  # draft, generating, completed, published
    progress_percentage = db.Column(db.Float, default=0.0)
    quality_score = db.Column(db.Float, default=0.0)
    word_count = db.Column(db.Integer, default=0)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Content storage
    outline_json = db.Column(db.Text, nullable=True)  # JSON outline
    chapters_json = db.Column(db.Text, nullable=True)  # JSON chapters
    metadata_json = db.Column(db.Text, nullable=True)  # Generation metadata
    
    # Publishing
    pdf_path = db.Column(db.String(500), nullable=True)
    epub_path = db.Column(db.String(500), nullable=True)
    docx_path = db.Column(db.String(500), nullable=True)
    
    # Foreign keys
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False, index=True)
    template_id = db.Column(db.String(36), db.ForeignKey('book_templates.id'), nullable=True)
    
    # Relationships
    collaborators = db.relationship('ProjectCollaborator', backref='project', lazy=True, cascade='all, delete-orphan')
    generation_logs = db.relationship('GenerationLog', backref='project', lazy=True, cascade='all, delete-orphan')
    analytics = db.relationship('ProjectAnalytics', backref='project', lazy=True, cascade='all, delete-orphan')

class ProjectCollaborator(db.Model):
    __tablename__ = 'project_collaborators'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('book_projects.id'), nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(50), default='editor')  # owner, editor, reviewer, viewer
    permissions = db.Column(db.Text, nullable=True)  # JSON permissions
    invited_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime, nullable=True)
    
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id'),)

class BookTemplate(db.Model):
    __tablename__ = 'book_templates'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=False)  # academic, business, technical, etc.
    template_json = db.Column(db.Text, nullable=False)  # JSON template structure
    preview_image = db.Column(db.String(500), nullable=True)
    is_premium = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    usage_count = db.Column(db.Integer, default=0)

class GenerationLog(db.Model):
    __tablename__ = 'generation_logs'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('book_projects.id'), nullable=False)
    agent_name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # running, completed, failed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    progress_percentage = db.Column(db.Float, default=0.0)
    quality_score = db.Column(db.Float, nullable=True)
    tokens_used = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Float, default=0.0)
    error_message = db.Column(db.Text, nullable=True)
    metadata_json = db.Column(db.Text, nullable=True)

class ProjectAnalytics(db.Model):
    __tablename__ = 'project_analytics'
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = db.Column(db.String(36), db.ForeignKey('book_projects.id'), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    metadata_json = db.Column(db.Text, nullable=True)

# User Management Endpoints
@app.route('/api/auth/register', methods=['POST'])
def register():
    """Advanced user registration with validation"""
    try:
        data = request.get_json()
        
        # Validation
        if not data.get('email') or not data.get('password') or not data.get('full_name'):
            return jsonify({'error': 'Missing required fields'}), 400
        
        if len(data['password']) < 8:
            return jsonify({'error': 'Password must be at least 8 characters'}), 400
        
        # Check if user already exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 409
        
        # Create Stripe customer
        stripe_customer = stripe.Customer.create(
            email=data['email'],
            name=data['full_name'],
            metadata={'source': 'booklm_registration'}
        )
        
        # Create user
        user = User(
            email=data['email'],
            password_hash=generate_password_hash(data['password']),
            full_name=data['full_name'],
            stripe_customer_id=stripe_customer.id
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        # Track registration analytics
        redis_client.incr('analytics:registrations:today')
        redis_client.incr(f"analytics:registrations:{datetime.now().strftime('%Y-%m')}")
        
        return jsonify({
            'message': 'User registered successfully',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'subscription_tier': user.subscription_tier
            }
        }), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Secure user login with rate limiting"""
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'error': 'Email and password required'}), 400
        
        # Rate limiting check
        rate_limit_key = f"login_attempts:{request.remote_addr}"
        attempts = redis_client.get(rate_limit_key)
        if attempts and int(attempts) >= 5:
            return jsonify({'error': 'Too many login attempts. Try again later.'}), 429
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not check_password_hash(user.password_hash, password):
            # Increment failed attempts
            redis_client.incr(rate_limit_key)
            redis_client.expire(rate_limit_key, 300)  # 5 minutes
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Reset failed attempts on successful login
        redis_client.delete(rate_limit_key)
        
        # Update last active
        user.last_active = datetime.utcnow()
        db.session.commit()
        
        # Create access token
        access_token = create_access_token(identity=user.id)
        
        # Track login analytics
        redis_client.incr('analytics:logins:today')
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name,
                'subscription_tier': user.subscription_tier,
                'books_generated': user.books_generated,
                'words_generated': user.words_generated
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

# Dashboard and Analytics Endpoints
@app.route('/api/dashboard/overview', methods=['GET'])
@jwt_required()
def dashboard_overview():
    """Comprehensive dashboard overview with analytics"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        # Get user's projects
        projects = BookProject.query.filter_by(user_id=user_id).order_by(BookProject.updated_at.desc()).limit(10).all()
        
        # Calculate statistics
        total_projects = BookProject.query.filter_by(user_id=user_id).count()
        completed_projects = BookProject.query.filter_by(user_id=user_id, status='completed').count()
        
        # Recent activity
        recent_logs = GenerationLog.query.join(BookProject).filter(
            BookProject.user_id == user_id
        ).order_by(GenerationLog.start_time.desc()).limit(20).all()
        
        # Usage analytics
        this_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = db.session.query(
            db.func.sum(GenerationLog.tokens_used).label('tokens'),
            db.func.sum(GenerationLog.cost_usd).label('cost')
        ).join(BookProject).filter(
            BookProject.user_id == user_id,
            GenerationLog.start_time >= this_month
        ).first()
        
        # Quality metrics
        avg_quality = db.session.query(db.func.avg(BookProject.quality_score)).filter(
            BookProject.user_id == user_id,
            BookProject.quality_score.isnot(None)
        ).scalar() or 0.0
        
        return jsonify({
            'user_stats': {
                'total_projects': total_projects,
                'completed_projects': completed_projects,
                'books_generated': user.books_generated,
                'words_generated': user.words_generated,
                'average_quality': round(avg_quality, 2),
                'subscription_tier': user.subscription_tier
            },
            'recent_projects': [{
                'id': p.id,
                'title': p.title,
                'status': p.status,
                'progress': p.progress_percentage,
                'quality_score': p.quality_score,
                'updated_at': p.updated_at.isoformat(),
                'word_count': p.word_count
            } for p in projects],
            'monthly_usage': {
                'tokens_used': int(monthly_usage.tokens or 0),
                'cost_usd': float(monthly_usage.cost or 0.0),
                'api_calls_today': user.api_calls_today
            },
            'recent_activity': [{
                'id': log.id,
                'project_title': log.project.title,
                'agent_name': log.agent_name,
                'status': log.status,
                'start_time': log.start_time.isoformat(),
                'end_time': log.end_time.isoformat() if log.end_time else None,
                'quality_score': log.quality_score
            } for log in recent_logs]
        }), 200
        
    except Exception as e:
        logger.error(f"Dashboard overview error: {e}")
        return jsonify({'error': 'Failed to load dashboard'}), 500

# Real-time WebSocket Events
@socketio.on('connect')
@jwt_required()
def handle_connect():
    """Handle WebSocket connection with authentication"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return False
        
        join_room(f"user_{user_id}")
        emit('connected', {
            'message': 'Connected to BookLLM real-time updates',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        logger.info(f"User {user_id} connected to WebSocket")
        
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        return False

@socketio.on('join_project')
@jwt_required()
def handle_join_project(data):
    """Join project room for real-time collaboration"""
    try:
        user_id = get_jwt_identity()
        project_id = data.get('project_id')
        
        # Verify user has access to project
        project = BookProject.query.filter(
            (BookProject.id == project_id) & 
            ((BookProject.user_id == user_id) | 
             (BookProject.collaborators.any(ProjectCollaborator.user_id == user_id)))
        ).first()
        
        if not project:
            emit('error', {'message': 'Access denied to project'})
            return
        
        join_room(f"project_{project_id}")
        emit('project_joined', {
            'project_id': project_id,
            'project_title': project.title,
            'current_status': project.status,
            'progress': project.progress_percentage
        })
        
        # Notify other users in project
        emit('user_joined_project', {
            'user_id': user_id,
            'project_id': project_id,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"project_{project_id}", include_self=False)
        
    except Exception as e:
        logger.error(f"Join project error: {e}")
        emit('error', {'message': 'Failed to join project'})

# Advanced Project Management
@app.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    """Get user's projects with advanced filtering and sorting"""
    try:
        user_id = get_jwt_identity()
        
        # Query parameters
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        status = request.args.get('status')
        sort_by = request.args.get('sort_by', 'updated_at')
        sort_order = request.args.get('sort_order', 'desc')
        search = request.args.get('search')
        
        # Base query
        query = BookProject.query.filter(
            (BookProject.user_id == user_id) |
            (BookProject.collaborators.any(ProjectCollaborator.user_id == user_id))
        )
        
        # Apply filters
        if status:
            query = query.filter(BookProject.status == status)
        
        if search:
            query = query.filter(
                (BookProject.title.ilike(f"%{search}%")) |
                (BookProject.topic.ilike(f"%{search}%"))
            )
        
        # Apply sorting
        if hasattr(BookProject, sort_by):
            order_column = getattr(BookProject, sort_by)
            if sort_order == 'desc':
                query = query.order_by(order_column.desc())
            else:
                query = query.order_by(order_column.asc())
        
        # Paginate
        projects = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'projects': [{
                'id': p.id,
                'title': p.title,
                'topic': p.topic,
                'description': p.description,
                'status': p.status,
                'progress_percentage': p.progress_percentage,
                'quality_score': p.quality_score,
                'word_count': p.word_count,
                'target_audience': p.target_audience,
                'book_style': p.book_style,
                'estimated_pages': p.estimated_pages,
                'created_at': p.created_at.isoformat(),
                'updated_at': p.updated_at.isoformat(),
                'completed_at': p.completed_at.isoformat() if p.completed_at else None,
                'is_owner': p.user_id == user_id,
                'collaborators_count': len(p.collaborators)
            } for p in projects.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': projects.total,
                'pages': projects.pages,
                'has_prev': projects.has_prev,
                'has_next': projects.has_next
            },
            'filters': {
                'status': status,
                'sort_by': sort_by,
                'sort_order': sort_order,
                'search': search
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Get projects error: {e}")
        return jsonify({'error': 'Failed to load projects'}), 500

# Celery Background Tasks
@celery_app.task(bind=True)
def generate_book_async(self, project_id: str, user_id: str):
    """Asynchronous book generation with progress updates"""
    try:
        project = BookProject.query.get(project_id)
        if not project:
            raise Exception(f"Project {project_id} not found")
        
        # Update project status
        project.status = 'generating'
        project.progress_percentage = 0.0
        db.session.commit()
        
        # Emit real-time update
        socketio.emit('project_status_update', {
            'project_id': project_id,
            'status': 'generating',
            'progress': 0.0,
            'message': 'Starting book generation...'
        }, room=f"project_{project_id}")
        
        # Create UI-integrated orchestrator
        orchestrator = create_ui_integrated_book_generator()
        
        # Generate book with progress tracking
        result = asyncio.run(orchestrator.generate_book_with_ui(
            topic=project.topic,
            target_audience=project.target_audience,
            book_style=project.book_style,
            estimated_pages=project.estimated_pages
        ))
        
        # Update project with results
        project.status = 'completed'
        project.progress_percentage = 100.0
        project.quality_score = result.get('final_score', 0) / 10  # Convert to 0-100 scale
        project.completed_at = datetime.utcnow()
        
        # Store generated content
        if 'state' in result:
            state = result['state']
            project.outline_json = json.dumps(getattr(state, 'outline', []))
            project.chapters_json = json.dumps(getattr(state, 'chapter_map', {}))
            project.word_count = sum(len(chapter.split()) for chapter in getattr(state, 'chapter_map', {}).values())
        
        project.metadata_json = json.dumps({
            'generation_time': datetime.utcnow().isoformat(),
            'quality_metrics': result.get('quality_metrics', {}),
            'final_score': result.get('final_score', 0)
        })
        
        db.session.commit()
        
        # Update user statistics
        user = User.query.get(user_id)
        user.books_generated += 1
        user.words_generated += project.word_count
        db.session.commit()
        
        # Emit completion update
        socketio.emit('project_completed', {
            'project_id': project_id,
            'final_score': project.quality_score,
            'word_count': project.word_count,
            'completion_time': project.completed_at.isoformat()
        }, room=f"project_{project_id}")
        
        return {
            'status': 'completed',
            'project_id': project_id,
            'final_score': project.quality_score,
            'word_count': project.word_count
        }
        
    except Exception as e:
        logger.error(f"Book generation task error: {e}")
        
        # Update project with error status
        project = BookProject.query.get(project_id)
        if project:
            project.status = 'failed'
            db.session.commit()
        
        # Emit error update
        socketio.emit('project_error', {
            'project_id': project_id,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"project_{project_id}")
        
        raise

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    socketio.run(
        app, 
        host='0.0.0.0', 
        port=5000, 
        debug=False,
        use_reloader=False
    )