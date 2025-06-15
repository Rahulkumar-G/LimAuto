"""
Advanced Collaboration System
Real-time collaborative editing and team management for book projects
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_socketio import emit, join_room, leave_room
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import json
import uuid

from .app import db, User, BookProject, ProjectCollaborator, socketio, redis_client
from .subscription_manager import subscription_manager
from ..utils.logger import get_logger

collaboration_bp = Blueprint('collaboration', __name__, url_prefix='/api/collaboration')
logger = get_logger(__name__)

class CollaborationManager:
    """Advanced collaboration management system"""
    
    def __init__(self):
        self.redis = redis_client
        self.logger = logger
    
    def get_project_collaborators(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all collaborators for a project"""
        collaborators = db.session.query(
            ProjectCollaborator, User
        ).join(User).filter(
            ProjectCollaborator.project_id == project_id
        ).all()
        
        return [{
            'id': collab.id,
            'user_id': collab.user_id,
            'email': user.email,
            'full_name': user.full_name,
            'role': collab.role,
            'permissions': json.loads(collab.permissions) if collab.permissions else {},
            'invited_at': collab.invited_at.isoformat(),
            'accepted_at': collab.accepted_at.isoformat() if collab.accepted_at else None,
            'status': 'accepted' if collab.accepted_at else 'pending',
            'last_active': user.last_active.isoformat()
        } for collab, user in collaborators]
    
    def can_user_access_project(self, user_id: str, project_id: str, required_permission: str = 'read') -> tuple[bool, str]:
        """Check if user can access project with specific permission"""
        project = BookProject.query.get(project_id)
        if not project:
            return False, "Project not found"
        
        # Owner has full access
        if project.user_id == user_id:
            return True, ""
        
        # Check collaboration
        collaboration = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=user_id
        ).first()
        
        if not collaboration or not collaboration.accepted_at:
            return False, "Access denied"
        
        # Check permissions
        permissions = json.loads(collaboration.permissions) if collaboration.permissions else {}
        role_permissions = self._get_role_permissions(collaboration.role)
        
        # Merge role permissions with custom permissions
        all_permissions = {**role_permissions, **permissions}
        
        if required_permission not in all_permissions or not all_permissions[required_permission]:
            return False, f"Insufficient permissions for {required_permission}"
        
        return True, ""
    
    def _get_role_permissions(self, role: str) -> Dict[str, bool]:
        """Get default permissions for role"""
        role_permissions = {
            'owner': {
                'read': True, 'write': True, 'delete': True, 'manage_collaborators': True,
                'export': True, 'publish': True, 'manage_settings': True
            },
            'editor': {
                'read': True, 'write': True, 'delete': False, 'manage_collaborators': False,
                'export': True, 'publish': False, 'manage_settings': False
            },
            'reviewer': {
                'read': True, 'write': False, 'delete': False, 'manage_collaborators': False,
                'export': True, 'publish': False, 'manage_settings': False
            },
            'viewer': {
                'read': True, 'write': False, 'delete': False, 'manage_collaborators': False,
                'export': False, 'publish': False, 'manage_settings': False
            }
        }
        
        return role_permissions.get(role, role_permissions['viewer'])
    
    def track_collaborative_activity(self, user_id: str, project_id: str, action: str, details: Dict = None):
        """Track collaborative activities for analytics"""
        activity = {
            'user_id': user_id,
            'project_id': project_id,
            'action': action,
            'details': details or {},
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store in Redis for real-time activity feed
        activity_key = f"project_activity:{project_id}"
        self.redis.lpush(activity_key, json.dumps(activity))
        self.redis.ltrim(activity_key, 0, 99)  # Keep last 100 activities
        self.redis.expire(activity_key, 86400 * 7)  # Keep for 7 days
        
        # Emit to all project collaborators
        socketio.emit('project_activity', activity, room=f"project_{project_id}")

# Initialize collaboration manager
collaboration_manager = CollaborationManager()

@collaboration_bp.route('/projects/<project_id>/collaborators', methods=['GET'])
@jwt_required()
def get_collaborators(project_id: str):
    """Get project collaborators"""
    try:
        user_id = get_jwt_identity()
        
        # Check access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return jsonify({'error': message}), 403
        
        collaborators = collaboration_manager.get_project_collaborators(project_id)
        
        return jsonify({
            'collaborators': collaborators,
            'total_count': len(collaborators)
        }), 200
        
    except Exception as e:
        logger.error(f"Get collaborators error: {e}")
        return jsonify({'error': 'Failed to load collaborators'}), 500

@collaboration_bp.route('/projects/<project_id>/collaborators', methods=['POST'])
@jwt_required()
def invite_collaborator(project_id: str):
    """Invite new collaborator to project"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check if user can manage collaborators
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'manage_collaborators')
        if not can_access:
            return jsonify({'error': message}), 403
        
        email = data.get('email')
        role = data.get('role', 'viewer')
        custom_permissions = data.get('permissions', {})
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        if role not in ['editor', 'reviewer', 'viewer']:
            return jsonify({'error': 'Invalid role'}), 400
        
        # Check subscription limits
        project = BookProject.query.get(project_id)
        current_collaborators = len(collaboration_manager.get_project_collaborators(project_id))
        
        owner = User.query.get(project.user_id)
        can_add, limit_message = subscription_manager.can_perform_action(
            owner, 'add_collaborator', current_count=current_collaborators
        )
        if not can_add:
            return jsonify({'error': limit_message}), 402
        
        # Find user by email
        invitee = User.query.filter_by(email=email).first()
        if not invitee:
            return jsonify({'error': 'User not found with this email'}), 404
        
        # Check if already collaborated
        existing = ProjectCollaborator.query.filter_by(
            project_id=project_id,
            user_id=invitee.id
        ).first()
        
        if existing:
            return jsonify({'error': 'User is already a collaborator'}), 409
        
        # Create collaboration
        collaboration = ProjectCollaborator(
            project_id=project_id,
            user_id=invitee.id,
            role=role,
            permissions=json.dumps(custom_permissions) if custom_permissions else None
        )
        
        db.session.add(collaboration)
        db.session.commit()
        
        # Track activity
        collaboration_manager.track_collaborative_activity(
            user_id, project_id, 'collaborator_invited',
            {'invitee_email': email, 'role': role}
        )
        
        # Send real-time notification to invitee
        socketio.emit('collaboration_invite', {
            'project_id': project_id,
            'project_title': project.title,
            'inviter_name': User.query.get(user_id).full_name,
            'role': role,
            'invitation_id': collaboration.id
        }, room=f"user_{invitee.id}")
        
        return jsonify({
            'message': 'Collaborator invited successfully',
            'collaboration_id': collaboration.id
        }), 201
        
    except Exception as e:
        logger.error(f"Invite collaborator error: {e}")
        return jsonify({'error': 'Failed to invite collaborator'}), 500

@collaboration_bp.route('/invitations/<invitation_id>/accept', methods=['POST'])
@jwt_required()
def accept_invitation(invitation_id: str):
    """Accept collaboration invitation"""
    try:
        user_id = get_jwt_identity()
        
        collaboration = ProjectCollaborator.query.filter_by(
            id=invitation_id,
            user_id=user_id
        ).first()
        
        if not collaboration:
            return jsonify({'error': 'Invitation not found'}), 404
        
        if collaboration.accepted_at:
            return jsonify({'error': 'Invitation already accepted'}), 409
        
        # Accept invitation
        collaboration.accepted_at = datetime.utcnow()
        db.session.commit()
        
        # Track activity
        collaboration_manager.track_collaborative_activity(
            user_id, collaboration.project_id, 'invitation_accepted'
        )
        
        # Notify project owner and other collaborators
        socketio.emit('collaborator_joined', {
            'project_id': collaboration.project_id,
            'user_id': user_id,
            'user_name': User.query.get(user_id).full_name,
            'role': collaboration.role
        }, room=f"project_{collaboration.project_id}")
        
        return jsonify({
            'message': 'Invitation accepted successfully',
            'project_id': collaboration.project_id
        }), 200
        
    except Exception as e:
        logger.error(f"Accept invitation error: {e}")
        return jsonify({'error': 'Failed to accept invitation'}), 500

@collaboration_bp.route('/projects/<project_id>/activity', methods=['GET'])
@jwt_required()
def get_project_activity(project_id: str):
    """Get project activity feed"""
    try:
        user_id = get_jwt_identity()
        
        # Check access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return jsonify({'error': message}), 403
        
        # Get activity from Redis
        activity_key = f"project_activity:{project_id}"
        activities = collaboration_manager.redis.lrange(activity_key, 0, 49)  # Last 50 activities
        
        activity_list = []
        for activity_json in activities:
            try:
                activity = json.loads(activity_json)
                # Enrich with user info
                user = User.query.get(activity['user_id'])
                if user:
                    activity['user_name'] = user.full_name
                    activity['user_email'] = user.email
                activity_list.append(activity)
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            'activities': activity_list,
            'total_count': len(activity_list)
        }), 200
        
    except Exception as e:
        logger.error(f"Get project activity error: {e}")
        return jsonify({'error': 'Failed to load project activity'}), 500

@collaboration_bp.route('/projects/<project_id>/realtime-status', methods=['GET'])
@jwt_required()
def get_realtime_status(project_id: str):
    """Get real-time collaboration status"""
    try:
        user_id = get_jwt_identity()
        
        # Check access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return jsonify({'error': message}), 403
        
        # Get online collaborators
        online_users = []
        collaborators = collaboration_manager.get_project_collaborators(project_id)
        
        for collab in collaborators:
            # Check if user is online (last seen < 5 minutes ago)
            last_seen_key = f"user_last_seen:{collab['user_id']}"
            last_seen = collaboration_manager.redis.get(last_seen_key)
            
            if last_seen:
                last_seen_time = datetime.fromisoformat(last_seen.decode())
                if datetime.utcnow() - last_seen_time < timedelta(minutes=5):
                    online_users.append({
                        'user_id': collab['user_id'],
                        'full_name': collab['full_name'],
                        'role': collab['role'],
                        'last_seen': last_seen_time.isoformat()
                    })
        
        # Get current editing status
        editing_status = {}
        for collab in collaborators:
            editing_key = f"editing:{project_id}:{collab['user_id']}"
            editing_info = collaboration_manager.redis.get(editing_key)
            if editing_info:
                editing_status[collab['user_id']] = json.loads(editing_info)
        
        return jsonify({
            'online_collaborators': online_users,
            'total_collaborators': len(collaborators),
            'editing_status': editing_status,
            'last_updated': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Get realtime status error: {e}")
        return jsonify({'error': 'Failed to load realtime status'}), 500

# WebSocket Events for Real-time Collaboration
@socketio.on('join_collaborative_editing')
@jwt_required()
def handle_join_editing(data):
    """Join collaborative editing session"""
    try:
        user_id = get_jwt_identity()
        project_id = data.get('project_id')
        section = data.get('section', 'outline')  # outline, chapter, etc.
        
        # Verify access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            emit('error', {'message': message})
            return
        
        # Join editing room
        room = f"editing_{project_id}_{section}"
        join_room(room)
        
        # Update editing status
        editing_key = f"editing:{project_id}:{user_id}"
        editing_info = {
            'section': section,
            'started_at': datetime.utcnow().isoformat(),
            'user_name': User.query.get(user_id).full_name
        }
        collaboration_manager.redis.setex(editing_key, 300, json.dumps(editing_info))  # 5 minute expiry
        
        # Notify other users
        user = User.query.get(user_id)
        emit('user_started_editing', {
            'user_id': user_id,
            'user_name': user.full_name,
            'section': section,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"project_{project_id}", include_self=False)
        
        emit('editing_session_joined', {
            'project_id': project_id,
            'section': section,
            'room': room
        })
        
    except Exception as e:
        logger.error(f"Join collaborative editing error: {e}")
        emit('error', {'message': 'Failed to join editing session'})

@socketio.on('content_change')
@jwt_required()
def handle_content_change(data):
    """Handle real-time content changes"""
    try:
        user_id = get_jwt_identity()
        project_id = data.get('project_id')
        section = data.get('section')
        changes = data.get('changes')
        cursor_position = data.get('cursor_position')
        
        # Verify write access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'write')
        if not can_access:
            emit('error', {'message': message})
            return
        
        # Broadcast changes to other editors
        user = User.query.get(user_id)
        emit('content_updated', {
            'user_id': user_id,
            'user_name': user.full_name,
            'project_id': project_id,
            'section': section,
            'changes': changes,
            'cursor_position': cursor_position,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"editing_{project_id}_{section}", include_self=False)
        
        # Track activity
        collaboration_manager.track_collaborative_activity(
            user_id, project_id, 'content_edited',
            {'section': section, 'changes_count': len(changes)}
        )
        
    except Exception as e:
        logger.error(f"Content change error: {e}")
        emit('error', {'message': 'Failed to process content change'})

@socketio.on('cursor_movement')
@jwt_required()
def handle_cursor_movement(data):
    """Handle real-time cursor movements"""
    try:
        user_id = get_jwt_identity()
        project_id = data.get('project_id')
        section = data.get('section')
        cursor_position = data.get('cursor_position')
        selection = data.get('selection')
        
        # Verify access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return
        
        # Broadcast cursor position to other editors
        user = User.query.get(user_id)
        emit('cursor_updated', {
            'user_id': user_id,
            'user_name': user.full_name,
            'cursor_position': cursor_position,
            'selection': selection,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"editing_{project_id}_{section}", include_self=False)
        
    except Exception as e:
        logger.error(f"Cursor movement error: {e}")

@socketio.on('leave_editing')
@jwt_required()
def handle_leave_editing(data):
    """Handle user leaving editing session"""
    try:
        user_id = get_jwt_identity()
        project_id = data.get('project_id')
        section = data.get('section')
        
        # Leave editing room
        room = f"editing_{project_id}_{section}"
        leave_room(room)
        
        # Clear editing status
        editing_key = f"editing:{project_id}:{user_id}"
        collaboration_manager.redis.delete(editing_key)
        
        # Notify other users
        user = User.query.get(user_id)
        emit('user_stopped_editing', {
            'user_id': user_id,
            'user_name': user.full_name,
            'section': section,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f"project_{project_id}", include_self=False)
        
    except Exception as e:
        logger.error(f"Leave editing error: {e}")

@collaboration_bp.route('/projects/<project_id>/comments', methods=['GET'])
@jwt_required()
def get_comments(project_id: str):
    """Get comments for project section"""
    try:
        user_id = get_jwt_identity()
        section = request.args.get('section', 'general')
        
        # Check access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return jsonify({'error': message}), 403
        
        # Get comments from Redis (in production, use database)
        comments_key = f"comments:{project_id}:{section}"
        comments_data = collaboration_manager.redis.lrange(comments_key, 0, -1)
        
        comments = []
        for comment_json in comments_data:
            try:
                comment = json.loads(comment_json)
                # Enrich with user info
                user = User.query.get(comment['user_id'])
                if user:
                    comment['user_name'] = user.full_name
                    comment['user_email'] = user.email
                comments.append(comment)
            except json.JSONDecodeError:
                continue
        
        return jsonify({
            'comments': comments,
            'section': section,
            'total_count': len(comments)
        }), 200
        
    except Exception as e:
        logger.error(f"Get comments error: {e}")
        return jsonify({'error': 'Failed to load comments'}), 500

@collaboration_bp.route('/projects/<project_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(project_id: str):
    """Add comment to project section"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Check access
        can_access, message = collaboration_manager.can_user_access_project(user_id, project_id, 'read')
        if not can_access:
            return jsonify({'error': message}), 403
        
        section = data.get('section', 'general')
        content = data.get('content')
        position = data.get('position')  # For inline comments
        
        if not content:
            return jsonify({'error': 'Comment content is required'}), 400
        
        # Create comment
        comment = {
            'id': str(uuid.uuid4()),
            'user_id': user_id,
            'content': content,
            'section': section,
            'position': position,
            'created_at': datetime.utcnow().isoformat(),
            'replies': []
        }
        
        # Store comment
        comments_key = f"comments:{project_id}:{section}"
        collaboration_manager.redis.lpush(comments_key, json.dumps(comment))
        collaboration_manager.redis.expire(comments_key, 86400 * 30)  # Keep for 30 days
        
        # Track activity
        collaboration_manager.track_collaborative_activity(
            user_id, project_id, 'comment_added',
            {'section': section, 'comment_id': comment['id']}
        )
        
        # Notify collaborators
        user = User.query.get(user_id)
        socketio.emit('new_comment', {
            'comment': {**comment, 'user_name': user.full_name},
            'project_id': project_id
        }, room=f"project_{project_id}")
        
        return jsonify({
            'message': 'Comment added successfully',
            'comment_id': comment['id']
        }), 201
        
    except Exception as e:
        logger.error(f"Add comment error: {e}")
        return jsonify({'error': 'Failed to add comment'}), 500