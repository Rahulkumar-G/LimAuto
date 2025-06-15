"""
Advanced Subscription Management and Billing Integration
Enterprise-grade subscription handling with Stripe integration
"""

import stripe
import json
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import redis
from sqlalchemy import and_, or_

from .app import db, User, redis_client, socketio
from ..utils.logger import get_logger

subscription_bp = Blueprint('subscription', __name__, url_prefix='/api/subscription')
logger = get_logger(__name__)

# Subscription Plans Configuration
SUBSCRIPTION_PLANS = {
    'free': {
        'name': 'Free',
        'price': 0,
        'currency': 'usd',
        'interval': 'month',
        'features': {
            'books_per_month': 2,
            'words_per_month': 20000,
            'api_calls_per_day': 50,
            'collaborators': 0,
            'export_formats': ['pdf'],
            'templates': ['basic'],
            'priority_support': False,
            'advanced_analytics': False,
            'white_label': False,
            'api_access': False
        }
    },
    'pro': {
        'name': 'Professional',
        'price': 2900,  # $29.00 in cents
        'currency': 'usd',
        'interval': 'month',
        'stripe_price_id': 'price_pro_monthly',
        'features': {
            'books_per_month': 20,
            'words_per_month': 500000,
            'api_calls_per_day': 1000,
            'collaborators': 5,
            'export_formats': ['pdf', 'epub', 'docx', 'html'],
            'templates': ['basic', 'professional', 'academic'],
            'priority_support': True,
            'advanced_analytics': True,
            'white_label': False,
            'api_access': True,
            'ai_suggestions': True,
            'bulk_generation': True
        }
    },
    'enterprise': {
        'name': 'Enterprise',
        'price': 9900,  # $99.00 in cents
        'currency': 'usd',
        'interval': 'month',
        'stripe_price_id': 'price_enterprise_monthly',
        'features': {
            'books_per_month': -1,  # Unlimited
            'words_per_month': -1,  # Unlimited
            'api_calls_per_day': -1,  # Unlimited
            'collaborators': -1,  # Unlimited
            'export_formats': ['pdf', 'epub', 'docx', 'html', 'latex', 'markdown'],
            'templates': ['basic', 'professional', 'academic', 'enterprise', 'custom'],
            'priority_support': True,
            'advanced_analytics': True,
            'white_label': True,
            'api_access': True,
            'ai_suggestions': True,
            'bulk_generation': True,
            'custom_integrations': True,
            'dedicated_support': True,
            'sla_guarantee': True
        }
    }
}

class SubscriptionManager:
    """Advanced subscription management with usage tracking"""
    
    def __init__(self):
        self.stripe = stripe
        self.redis = redis_client
        self.logger = logger
    
    def get_user_limits(self, user: User) -> Dict[str, Any]:
        """Get current usage limits for user based on subscription"""
        plan = SUBSCRIPTION_PLANS.get(user.subscription_tier, SUBSCRIPTION_PLANS['free'])
        
        # Get current usage
        current_usage = self._get_current_usage(user)
        
        return {
            'plan': plan,
            'current_usage': current_usage,
            'limits_exceeded': self._check_limits_exceeded(user, plan, current_usage)
        }
    
    def _get_current_usage(self, user: User) -> Dict[str, int]:
        """Get current month's usage for user"""
        # Reset daily API calls if needed
        if user.last_api_reset.date() < datetime.utcnow().date():
            user.api_calls_today = 0
            user.last_api_reset = datetime.utcnow()
            db.session.commit()
        
        # Get monthly usage from cache/database
        month_key = datetime.utcnow().strftime('%Y-%m')
        cache_key = f"usage:{user.id}:{month_key}"
        
        cached_usage = self.redis.hgetall(cache_key)
        if cached_usage:
            return {
                'books_this_month': int(cached_usage.get(b'books', 0)),
                'words_this_month': int(cached_usage.get(b'words', 0)),
                'api_calls_today': user.api_calls_today
            }
        
        # Calculate from database if not cached
        from .app import BookProject, GenerationLog
        
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        books_this_month = BookProject.query.filter(
            BookProject.user_id == user.id,
            BookProject.created_at >= month_start
        ).count()
        
        words_this_month = db.session.query(
            db.func.sum(BookProject.word_count)
        ).filter(
            BookProject.user_id == user.id,
            BookProject.created_at >= month_start
        ).scalar() or 0
        
        usage = {
            'books_this_month': books_this_month,
            'words_this_month': int(words_this_month),
            'api_calls_today': user.api_calls_today
        }
        
        # Cache for 1 hour
        self.redis.hset(cache_key, mapping={
            'books': usage['books_this_month'],
            'words': usage['words_this_month']
        })
        self.redis.expire(cache_key, 3600)
        
        return usage
    
    def _check_limits_exceeded(self, user: User, plan: Dict, usage: Dict) -> Dict[str, bool]:
        """Check if user has exceeded any limits"""
        limits = plan['features']
        
        return {
            'books': limits['books_per_month'] != -1 and usage['books_this_month'] >= limits['books_per_month'],
            'words': limits['words_per_month'] != -1 and usage['words_this_month'] >= limits['words_per_month'],
            'api_calls': limits['api_calls_per_day'] != -1 and usage['api_calls_today'] >= limits['api_calls_per_day']
        }
    
    def can_perform_action(self, user: User, action: str, **kwargs) -> tuple[bool, str]:
        """Check if user can perform specific action based on subscription"""
        limits_info = self.get_user_limits(user)
        plan = limits_info['plan']
        exceeded = limits_info['limits_exceeded']
        
        if action == 'create_book':
            if exceeded['books']:
                return False, f"Monthly book limit reached ({plan['features']['books_per_month']}). Upgrade for more books."
            return True, ""
        
        elif action == 'generate_words':
            words_needed = kwargs.get('estimated_words', 1000)
            if exceeded['words'] or (
                plan['features']['words_per_month'] != -1 and 
                limits_info['current_usage']['words_this_month'] + words_needed > plan['features']['words_per_month']
            ):
                return False, f"Monthly word limit reached ({plan['features']['words_per_month']}). Upgrade for more words."
            return True, ""
        
        elif action == 'api_call':
            if exceeded['api_calls']:
                return False, f"Daily API limit reached ({plan['features']['api_calls_per_day']}). Upgrade or try tomorrow."
            return True, ""
        
        elif action == 'add_collaborator':
            current_collaborators = kwargs.get('current_count', 0)
            if plan['features']['collaborators'] != -1 and current_collaborators >= plan['features']['collaborators']:
                return False, f"Collaborator limit reached ({plan['features']['collaborators']}). Upgrade for more collaborators."
            return True, ""
        
        elif action == 'export_format':
            format_type = kwargs.get('format')
            if format_type not in plan['features']['export_formats']:
                return False, f"Export format '{format_type}' not available in your plan. Upgrade to access."
            return True, ""
        
        elif action == 'use_template':
            template_category = kwargs.get('category')
            if template_category not in plan['features']['templates']:
                return False, f"Template category '{template_category}' not available in your plan. Upgrade to access."
            return True, ""
        
        return True, ""
    
    def track_usage(self, user: User, action: str, **kwargs):
        """Track user action for billing and analytics"""
        month_key = datetime.utcnow().strftime('%Y-%m')
        cache_key = f"usage:{user.id}:{month_key}"
        
        if action == 'book_created':
            self.redis.hincrby(cache_key, 'books', 1)
            self.redis.expire(cache_key, 86400 * 32)  # Expire after month ends
            
        elif action == 'words_generated':
            word_count = kwargs.get('word_count', 0)
            self.redis.hincrby(cache_key, 'words', word_count)
            self.redis.expire(cache_key, 86400 * 32)
            
        elif action == 'api_call':
            user.api_calls_today += 1
            db.session.commit()
        
        # Track for analytics
        analytics_key = f"analytics:usage:{action}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        self.redis.incr(analytics_key)
        self.redis.expire(analytics_key, 86400 * 90)  # Keep for 90 days

# Initialize subscription manager
subscription_manager = SubscriptionManager()

@subscription_bp.route('/plans', methods=['GET'])
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        # Add pricing from Stripe if needed
        plans_with_pricing = {}
        for plan_id, plan in SUBSCRIPTION_PLANS.items():
            plan_data = plan.copy()
            
            # Get real-time pricing from Stripe for paid plans
            if plan.get('stripe_price_id'):
                try:
                    stripe_price = stripe.Price.retrieve(plan['stripe_price_id'])
                    plan_data['stripe_price'] = {
                        'id': stripe_price.id,
                        'amount': stripe_price.unit_amount,
                        'currency': stripe_price.currency,
                        'interval': stripe_price.recurring.interval
                    }
                except Exception as e:
                    logger.warning(f"Failed to get Stripe pricing for {plan_id}: {e}")
            
            plans_with_pricing[plan_id] = plan_data
        
        return jsonify({
            'plans': plans_with_pricing,
            'currency_symbol': '$',
            'billing_cycles': ['monthly', 'yearly']
        }), 200
        
    except Exception as e:
        logger.error(f"Get subscription plans error: {e}")
        return jsonify({'error': 'Failed to load subscription plans'}), 500

@subscription_bp.route('/current', methods=['GET'])
@jwt_required()
def get_current_subscription():
    """Get user's current subscription details and usage"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get subscription limits and usage
        limits_info = subscription_manager.get_user_limits(user)
        
        # Get Stripe subscription if exists
        stripe_subscription = None
        if user.stripe_customer_id and user.subscription_tier != 'free':
            try:
                subscriptions = stripe.Subscription.list(
                    customer=user.stripe_customer_id,
                    status='active',
                    limit=1
                )
                if subscriptions.data:
                    stripe_subscription = subscriptions.data[0]
            except Exception as e:
                logger.warning(f"Failed to get Stripe subscription: {e}")
        
        return jsonify({
            'current_plan': user.subscription_tier,
            'subscription_status': user.subscription_status,
            'plan_details': limits_info['plan'],
            'current_usage': limits_info['current_usage'],
            'limits_exceeded': limits_info['limits_exceeded'],
            'stripe_subscription': {
                'id': stripe_subscription.id if stripe_subscription else None,
                'current_period_end': stripe_subscription.current_period_end if stripe_subscription else None,
                'cancel_at_period_end': stripe_subscription.cancel_at_period_end if stripe_subscription else None
            } if stripe_subscription else None,
            'upgrade_available': user.subscription_tier != 'enterprise'
        }), 200
        
    except Exception as e:
        logger.error(f"Get current subscription error: {e}")
        return jsonify({'error': 'Failed to load subscription details'}), 500

@subscription_bp.route('/checkout', methods=['POST'])
@jwt_required()
def create_checkout_session():
    """Create Stripe checkout session for subscription upgrade"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        data = request.get_json()
        
        plan_id = data.get('plan_id')
        billing_cycle = data.get('billing_cycle', 'monthly')
        
        if not user or plan_id not in SUBSCRIPTION_PLANS:
            return jsonify({'error': 'Invalid user or plan'}), 400
        
        plan = SUBSCRIPTION_PLANS[plan_id]
        
        if plan_id == 'free':
            return jsonify({'error': 'Cannot checkout for free plan'}), 400
        
        # Determine price ID based on billing cycle
        price_id = plan.get('stripe_price_id')
        if billing_cycle == 'yearly':
            price_id = plan.get('stripe_price_id_yearly', price_id)
        
        # Create checkout session
        checkout_session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=f"{request.host_url}subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{request.host_url}subscription/cancel",
            metadata={
                'user_id': user.id,
                'plan_id': plan_id,
                'billing_cycle': billing_cycle
            },
            allow_promotion_codes=True,
            subscription_data={
                'metadata': {
                    'user_id': user.id,
                    'plan_id': plan_id
                }
            }
        )
        
        return jsonify({
            'checkout_url': checkout_session.url,
            'session_id': checkout_session.id
        }), 200
        
    except Exception as e:
        logger.error(f"Create checkout session error: {e}")
        return jsonify({'error': 'Failed to create checkout session'}), 500

@subscription_bp.route('/portal', methods=['POST'])
@jwt_required()
def create_customer_portal():
    """Create Stripe customer portal for subscription management"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user or not user.stripe_customer_id:
            return jsonify({'error': 'No Stripe customer found'}), 404
        
        portal_session = stripe.billing_portal.Session.create(
            customer=user.stripe_customer_id,
            return_url=f"{request.host_url}dashboard"
        )
        
        return jsonify({
            'portal_url': portal_session.url
        }), 200
        
    except Exception as e:
        logger.error(f"Create customer portal error: {e}")
        return jsonify({'error': 'Failed to create customer portal'}), 500

@subscription_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = current_app.config.get('STRIPE_WEBHOOK_SECRET')
        
        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            handle_successful_payment(session)
            
        elif event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            handle_subscription_updated(subscription)
            
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            handle_subscription_cancelled(subscription)
            
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            handle_payment_succeeded(invoice)
            
        elif event['type'] == 'invoice.payment_failed':
            invoice = event['data']['object']
            handle_payment_failed(invoice)
        
        return jsonify({'status': 'success'}), 200
        
    except ValueError as e:
        logger.error(f"Invalid payload: {e}")
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid signature: {e}")
        return jsonify({'error': 'Invalid signature'}), 400
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

def handle_successful_payment(session):
    """Handle successful payment from checkout"""
    user_id = session['metadata']['user_id']
    plan_id = session['metadata']['plan_id']
    
    user = User.query.get(user_id)
    if user:
        user.subscription_tier = plan_id
        user.subscription_status = 'active'
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('subscription_updated', {
            'user_id': user_id,
            'new_plan': plan_id,
            'status': 'active',
            'message': f'Successfully upgraded to {SUBSCRIPTION_PLANS[plan_id]["name"]} plan!'
        }, room=f"user_{user_id}")
        
        logger.info(f"User {user_id} upgraded to {plan_id}")

def handle_subscription_updated(subscription):
    """Handle subscription updates"""
    user_id = subscription['metadata']['user_id']
    
    user = User.query.get(user_id)
    if user:
        # Update subscription status based on Stripe subscription
        if subscription['status'] in ['active', 'trialing']:
            user.subscription_status = 'active'
        elif subscription['status'] in ['past_due', 'incomplete']:
            user.subscription_status = 'past_due'
        elif subscription['status'] in ['canceled', 'incomplete_expired']:
            user.subscription_status = 'cancelled'
            user.subscription_tier = 'free'
        
        db.session.commit()
        
        logger.info(f"User {user_id} subscription updated: {subscription['status']}")

def handle_subscription_cancelled(subscription):
    """Handle subscription cancellation"""
    user_id = subscription['metadata']['user_id']
    
    user = User.query.get(user_id)
    if user:
        user.subscription_tier = 'free'
        user.subscription_status = 'cancelled'
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('subscription_cancelled', {
            'user_id': user_id,
            'message': 'Your subscription has been cancelled. You now have access to the free plan.'
        }, room=f"user_{user_id}")
        
        logger.info(f"User {user_id} subscription cancelled")

def handle_payment_succeeded(invoice):
    """Handle successful payment"""
    customer_id = invoice['customer']
    
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user:
        # Update payment status, extend subscription, etc.
        user.subscription_status = 'active'
        db.session.commit()
        
        logger.info(f"Payment succeeded for user {user.id}")

def handle_payment_failed(invoice):
    """Handle failed payment"""
    customer_id = invoice['customer']
    
    user = User.query.filter_by(stripe_customer_id=customer_id).first()
    if user:
        user.subscription_status = 'past_due'
        db.session.commit()
        
        # Emit real-time notification
        socketio.emit('payment_failed', {
            'user_id': user.id,
            'message': 'Payment failed. Please update your payment method to continue using premium features.'
        }, room=f"user_{user.id}")
        
        logger.warning(f"Payment failed for user {user.id}")

# Usage verification decorator
def check_subscription_limit(action: str, **kwargs):
    """Decorator to check subscription limits before performing actions"""
    def decorator(f):
        def wrapper(*args, **kwargs_inner):
            try:
                user_id = get_jwt_identity()
                user = User.query.get(user_id)
                
                can_perform, message = subscription_manager.can_perform_action(user, action, **kwargs)
                if not can_perform:
                    return jsonify({
                        'error': 'Subscription limit exceeded',
                        'message': message,
                        'upgrade_required': True
                    }), 402  # Payment Required
                
                # Track usage
                result = f(*args, **kwargs_inner)
                
                # Track successful action
                if hasattr(result, 'status_code') and result.status_code < 300:
                    subscription_manager.track_usage(user, action, **kwargs)
                
                return result
                
            except Exception as e:
                logger.error(f"Subscription check error: {e}")
                return f(*args, **kwargs_inner)
        
        wrapper.__name__ = f.__name__
        return wrapper
    return decorator