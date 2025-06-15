"""
Enhanced API with Real-time UI Integration
Extends the existing API with WebSocket support and enhanced status endpoints
"""

import asyncio
import json
import threading
import time
from datetime import datetime
from typing import Dict, Any, List

from flask import Flask, jsonify, request, Response
from flask_cors import CORS

from .ui.orchestrator_integration import create_ui_integrated_book_generator, UIHealthChecker
from .ui.realtime_integration import status_manager
from .utils.logger import get_logger

app = Flask(__name__)
CORS(app)
logger = get_logger(__name__)

# Global orchestrator instance
ui_orchestrator = None
health_checker = None


@app.before_first_request
def initialize_orchestrator():
    """Initialize the UI-integrated orchestrator"""
    global ui_orchestrator, health_checker
    
    try:
        ui_orchestrator = create_ui_integrated_book_generator()
        health_checker = UIHealthChecker(ui_orchestrator)
        logger.info("UI-integrated orchestrator initialized")
    except Exception as e:
        logger.error(f"Failed to initialize orchestrator: {e}")


# Enhanced Status Endpoints

@app.route('/api/enhanced-status', methods=['GET'])
def get_enhanced_status():
    """Get comprehensive enhanced status including quality metrics"""
    try:
        if not ui_orchestrator:
            return jsonify({'error': 'Orchestrator not initialized'}), 500
        
        status = ui_orchestrator.get_current_status()
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'status': status,
            'health': health_checker.get_system_health() if health_checker else None
        })
        
    except Exception as e:
        logger.error(f"Enhanced status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/agents/detailed', methods=['GET'])
def get_detailed_agent_status():
    """Get detailed agent status with quality metrics and progress"""
    try:
        if not ui_orchestrator:
            return jsonify({'error': 'Orchestrator not initialized'}), 500
        
        status = ui_orchestrator.get_current_status()
        agents = status.get('agents', {})
        
        # Enhance agent data with additional details
        enhanced_agents = {}
        for agent_name, agent_data in agents.items():
            enhanced_agents[agent_name] = {
                **agent_data,
                'performance_score': _calculate_agent_performance(agent_data),
                'efficiency_rating': _calculate_efficiency_rating(agent_data),
                'estimated_completion': _estimate_completion_time(agent_data)
            }
        
        return jsonify({
            'agents': enhanced_agents,
            'summary': {
                'total_agents': len(enhanced_agents),
                'running_agents': len([a for a in enhanced_agents.values() if a.get('status') == 'running']),
                'completed_agents': len([a for a in enhanced_agents.values() if a.get('status') == 'completed']),
                'failed_agents': len([a for a in enhanced_agents.values() if a.get('status') == 'failed']),
                'average_quality': sum(a.get('quality_score', 0) for a in enhanced_agents.values()) / max(len(enhanced_agents), 1)
            }
        })
        
    except Exception as e:
        logger.error(f"Detailed agent status error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/quality-metrics', methods=['GET'])
def get_quality_metrics():
    """Get comprehensive quality metrics with historical data"""
    try:
        if not ui_orchestrator:
            return jsonify({'error': 'Orchestrator not initialized'}), 500
        
        status = ui_orchestrator.get_current_status()
        quality_metrics = status.get('quality_metrics')
        
        if not quality_metrics:
            return jsonify({'message': 'No quality metrics available yet'}), 404
        
        # Calculate additional metrics
        final_score = _calculate_final_score(quality_metrics)
        
        return jsonify({
            'current_metrics': quality_metrics,
            'calculated_scores': {
                'final_score': final_score,
                'grade': _get_quality_grade(final_score),
                'improvement_areas': _identify_improvement_areas(quality_metrics),
                'strengths': _identify_strengths(quality_metrics)
            },
            'progression': quality_metrics.get('progression', []),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Quality metrics error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/workflow-progress', methods=['GET'])
def get_workflow_progress():
    """Get detailed workflow progress information"""
    try:
        if not ui_orchestrator:
            return jsonify({'error': 'Orchestrator not initialized'}), 500
        
        status = ui_orchestrator.get_current_status()
        workflow_progress = status.get('workflow_progress')
        
        if not workflow_progress:
            return jsonify({'message': 'No workflow progress available yet'}), 404
        
        # Add calculated fields
        progress_percentage = workflow_progress.get('overall_progress', 0)
        estimated_time = workflow_progress.get('estimated_time_remaining', 'Unknown')
        
        return jsonify({
            'progress': workflow_progress,
            'analytics': {
                'completion_rate': f"{progress_percentage:.1f}%",
                'estimated_completion': estimated_time,
                'current_phase': _determine_current_phase(workflow_progress),
                'next_milestone': _get_next_milestone(workflow_progress),
                'performance_rating': _calculate_workflow_performance(workflow_progress)
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Workflow progress error: {e}")
        return jsonify({'error': str(e)}), 500


# Book Generation Endpoints

@app.route('/api/generate-book', methods=['POST'])
def generate_book_enhanced():
    """Generate book with enhanced UI integration"""
    try:
        if not ui_orchestrator:
            return jsonify({'error': 'Orchestrator not initialized'}), 500
        
        data = request.get_json()
        topic = data.get('topic')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Extract optional parameters
        kwargs = {
            'audience': data.get('audience', 'professional'),
            'style': data.get('style', 'authoritative'),
            'pages': data.get('pages', 200),
            'quality_threshold': data.get('quality_threshold', 0.90)
        }
        
        # Start generation in background thread
        def run_generation():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    ui_orchestrator.generate_book_with_ui(topic, **kwargs)
                )
                logger.info(f"Book generation completed with score: {result.get('final_score', 0)}")
            except Exception as e:
                logger.error(f"Background generation failed: {e}")
        
        thread = threading.Thread(target=run_generation, daemon=True)
        thread.start()
        
        return jsonify({
            'message': 'Book generation started',
            'topic': topic,
            'parameters': kwargs,
            'status_endpoint': '/api/enhanced-status',
            'websocket_url': 'ws://localhost:8765',
            'estimated_duration': '30-60 minutes'
        })
        
    except Exception as e:
        logger.error(f"Book generation error: {e}")
        return jsonify({'error': str(e)}), 500


# Server-Sent Events for Real-time Updates

@app.route('/events/enhanced-status')
def enhanced_status_stream():
    """Server-sent events for enhanced status updates"""
    
    def event_stream():
        """Generate server-sent events"""
        last_update = None
        
        while True:
            try:
                if ui_orchestrator:
                    current_status = ui_orchestrator.get_current_status()
                    
                    # Only send updates when status changes
                    if current_status != last_update:
                        yield f"data: {json.dumps(current_status)}\n\n"
                        last_update = current_status
                
                # Wait before next check
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"SSE stream error: {e}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
    
    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Access-Control-Allow-Origin': '*'
        }
    )


# Health Check Endpoints

@app.route('/api/health', methods=['GET'])
def health_check():
    """Comprehensive health check"""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'version': '2.0.0-enhanced',
            'components': {
                'orchestrator': ui_orchestrator is not None,
                'status_manager': status_manager.is_running if status_manager else False,
                'health_checker': health_checker is not None
            }
        }
        
        if health_checker:
            health_data['detailed_health'] = health_checker.get_system_health()
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500


@app.route('/api/system-info', methods=['GET'])
def get_system_info():
    """Get system information and capabilities"""
    try:
        return jsonify({
            'name': 'BookLLM Enhanced API',
            'version': '2.0.0',
            'features': [
                'Real-time WebSocket updates',
                'Enhanced quality metrics',
                'Advanced agent monitoring',
                'Professional PDF generation',
                'Expert-level content generation',
                'Iterative quality refinement'
            ],
            'endpoints': {
                'status': '/api/enhanced-status',
                'agents': '/api/agents/detailed',
                'quality': '/api/quality-metrics',
                'workflow': '/api/workflow-progress',
                'generation': '/api/generate-book',
                'health': '/api/health',
                'sse': '/events/enhanced-status',
                'websocket': 'ws://localhost:8765'
            },
            'ui_components': {
                'dashboard': '/frontend/components/EnhancedDashboard.tsx',
                'progress': '/frontend/components/AgentProgress.tsx',
                'websocket_hook': '/frontend/src/hooks/useEnhancedWebSocket.ts'
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"System info error: {e}")
        return jsonify({'error': str(e)}), 500


# Utility Functions

def _calculate_agent_performance(agent_data: Dict[str, Any]) -> float:
    """Calculate agent performance score"""
    try:
        quality_score = agent_data.get('quality_score', 0)
        progress = agent_data.get('progress_percent', 0) / 100
        
        # Factor in iteration efficiency
        iteration_count = agent_data.get('iteration_count', 1)
        max_iterations = agent_data.get('max_iterations', 1)
        iteration_efficiency = 1 - (iteration_count - 1) / max(max_iterations, 1)
        
        return (quality_score * 0.6 + progress * 0.3 + iteration_efficiency * 0.1)
    except Exception:
        return 0.0


def _calculate_efficiency_rating(agent_data: Dict[str, Any]) -> str:
    """Calculate efficiency rating"""
    performance = _calculate_agent_performance(agent_data)
    
    if performance >= 0.9:
        return 'Excellent'
    elif performance >= 0.8:
        return 'Good'
    elif performance >= 0.7:
        return 'Average'
    else:
        return 'Needs Improvement'


def _estimate_completion_time(agent_data: Dict[str, Any]) -> str:
    """Estimate completion time for agent"""
    try:
        status = agent_data.get('status')
        if status == 'completed':
            return 'Completed'
        elif status == 'failed':
            return 'Failed'
        
        progress = agent_data.get('progress_percent', 0)
        if progress <= 0:
            return 'Starting...'
        
        # Simple estimation based on progress
        estimated_minutes = max(1, int((100 - progress) / progress * 5))
        return f"~{estimated_minutes} minutes"
    except Exception:
        return 'Unknown'


def _calculate_final_score(quality_metrics: Dict[str, Any]) -> int:
    """Calculate final quality score out of 1000"""
    try:
        overall_score = quality_metrics.get('overall_score', 0)
        base_score = overall_score * 800
        
        # Bonus points
        bonus = 0
        if quality_metrics.get('content_depth', 0) > 0.95:
            bonus += 40
        if quality_metrics.get('technical_accuracy', 0) > 0.98:
            bonus += 40
        if quality_metrics.get('factual_accuracy', 0) > 0.95:
            bonus += 30
        
        return min(int(base_score + bonus), 1500)
    except Exception:
        return 0


def _get_quality_grade(score: int) -> str:
    """Get quality grade based on score"""
    if score >= 1200:
        return 'World-Class (A+)'
    elif score >= 1000:
        return 'Professional (A)'
    elif score >= 800:
        return 'Advanced (B+)'
    elif score >= 600:
        return 'Intermediate (B)'
    else:
        return 'Developing (C)'


def _identify_improvement_areas(quality_metrics: Dict[str, Any]) -> List[str]:
    """Identify areas needing improvement"""
    areas = []
    threshold = 0.8
    
    if quality_metrics.get('content_depth', 1) < threshold:
        areas.append('Content Depth')
    if quality_metrics.get('technical_accuracy', 1) < threshold:
        areas.append('Technical Accuracy')
    if quality_metrics.get('expertise_level', 1) < threshold:
        areas.append('Expertise Level')
    if quality_metrics.get('coherence_score', 1) < threshold:
        areas.append('Coherence')
    
    return areas


def _identify_strengths(quality_metrics: Dict[str, Any]) -> List[str]:
    """Identify quality strengths"""
    strengths = []
    threshold = 0.9
    
    if quality_metrics.get('content_depth', 0) >= threshold:
        strengths.append('Excellent Content Depth')
    if quality_metrics.get('technical_accuracy', 0) >= threshold:
        strengths.append('High Technical Accuracy')
    if quality_metrics.get('expertise_level', 0) >= threshold:
        strengths.append('Expert-Level Content')
    if quality_metrics.get('coherence_score', 0) >= threshold:
        strengths.append('Strong Coherence')
    
    return strengths


def _determine_current_phase(workflow_progress: Dict[str, Any]) -> str:
    """Determine current workflow phase"""
    current_agent = workflow_progress.get('current_agent', '')
    
    if 'outline' in current_agent:
        return 'Planning & Structure'
    elif any(x in current_agent for x in ['writer', 'chapter']):
        return 'Content Generation'
    elif any(x in current_agent for x in ['review', 'quality', 'proofreader']):
        return 'Quality Assurance'
    elif 'final' in current_agent:
        return 'Finalization'
    else:
        return 'Processing'


def _get_next_milestone(workflow_progress: Dict[str, Any]) -> str:
    """Get next workflow milestone"""
    progress = workflow_progress.get('overall_progress', 0)
    
    if progress < 25:
        return 'Complete Outline'
    elif progress < 75:
        return 'Finish Content Generation'
    elif progress < 95:
        return 'Quality Review Complete'
    else:
        return 'Final Book Ready'


def _calculate_workflow_performance(workflow_progress: Dict[str, Any]) -> str:
    """Calculate overall workflow performance"""
    try:
        quality_score = workflow_progress.get('quality_score', 0)
        progress = workflow_progress.get('overall_progress', 0) / 100
        
        performance = (quality_score * 0.7 + progress * 0.3)
        
        if performance >= 0.9:
            return 'Excellent'
        elif performance >= 0.8:
            return 'Good'
        elif performance >= 0.7:
            return 'Satisfactory'
        else:
            return 'Needs Improvement'
    except Exception:
        return 'Unknown'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)