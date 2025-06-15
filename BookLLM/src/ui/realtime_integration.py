"""
Real-time UI Integration System
Connects enhanced agents with existing UI components for live status tracking
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import websockets
from queue import Queue, Empty
import threading

from ..models.state import BookState
from ..models.agent_type import AgentType
from ..utils.logger import get_logger

class AgentStatus(Enum):
    """Agent execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

@dataclass
class EnhancedAgentStatus:
    """Enhanced agent status for UI integration"""
    agent_name: str
    agent_type: str
    current_step: str
    status: AgentStatus
    progress_percent: float
    iteration_count: int
    max_iterations: int
    quality_score: float
    start_time: str
    estimated_completion: str
    domain: str
    word_count: int
    tokens_used: int
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]

@dataclass
class QualityMetricsUpdate:
    """Real-time quality metrics update"""
    overall_score: float
    content_depth: float
    technical_accuracy: float
    expertise_level: float
    coherence_score: float
    factual_accuracy: float
    progression: List[Dict[str, float]]
    timestamp: str

@dataclass
class WorkflowProgress:
    """Complete workflow progress status"""
    total_agents: int
    completed_agents: int
    current_agent: str
    next_agent: Optional[str]
    overall_progress: float
    estimated_time_remaining: str
    quality_score: float
    book_title: str
    chapter_count: int
    word_count: int
    timestamp: str

class RealTimeStatusManager:
    """Manages real-time status updates for all agents and UI components"""
    
    def __init__(self):
        self.logger = get_logger(__name__)
        self.agent_statuses: Dict[str, EnhancedAgentStatus] = {}
        self.quality_metrics: Optional[QualityMetricsUpdate] = None
        self.workflow_progress: Optional[WorkflowProgress] = None
        
        # Event listeners and WebSocket connections
        self.listeners: List[Callable] = []
        self.websocket_clients: List[websockets.WebSocketServerProtocol] = []
        self.update_queue = Queue()
        self.is_running = False
        
        # Performance tracking
        self.agent_start_times: Dict[str, datetime] = {}
        self.quality_progression: List[Dict[str, float]] = []
        
    def start_status_manager(self):
        """Start the real-time status management system"""
        self.is_running = True
        
        # Start WebSocket server
        asyncio.create_task(self._start_websocket_server())
        
        # Start status update processor
        threading.Thread(target=self._process_status_updates, daemon=True).start()
        
        self.logger.info("Real-time status manager started")
    
    def stop_status_manager(self):
        """Stop the status management system"""
        self.is_running = False
        self.logger.info("Real-time status manager stopped")
    
    async def _start_websocket_server(self, host="localhost", port=8765):
        """Start WebSocket server for real-time communication"""
        try:
            async def handle_client(websocket, path):
                self.websocket_clients.append(websocket)
                self.logger.info(f"WebSocket client connected: {websocket.remote_address}")
                
                try:
                    # Send current status immediately
                    await self._send_complete_status(websocket)
                    
                    # Keep connection alive
                    await websocket.wait_closed()
                except websockets.exceptions.ConnectionClosed:
                    pass
                finally:
                    if websocket in self.websocket_clients:
                        self.websocket_clients.remove(websocket)
                    self.logger.info(f"WebSocket client disconnected")
            
            server = await websockets.serve(handle_client, host, port)
            self.logger.info(f"WebSocket server started on ws://{host}:{port}")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            self.logger.error(f"WebSocket server error: {e}")
    
    def update_agent_status(self, agent_name: str, **kwargs):
        """Update agent status and notify all listeners"""
        
        current_status = self.agent_statuses.get(agent_name)
        
        if current_status:
            # Update existing status
            for key, value in kwargs.items():
                if hasattr(current_status, key):
                    setattr(current_status, key, value)
        else:
            # Create new status
            default_status = EnhancedAgentStatus(
                agent_name=agent_name,
                agent_type=kwargs.get('agent_type', 'unknown'),
                current_step=kwargs.get('current_step', 'initializing'),
                status=AgentStatus.PENDING,
                progress_percent=0.0,
                iteration_count=0,
                max_iterations=1,
                quality_score=0.0,
                start_time=datetime.now().isoformat(),
                estimated_completion="",
                domain=kwargs.get('domain', 'general'),
                word_count=0,
                tokens_used=0,
                errors=[],
                warnings=[],
                metadata={}
            )
            
            # Apply provided updates
            for key, value in kwargs.items():
                if hasattr(default_status, key):
                    setattr(default_status, key, value)
            
            self.agent_statuses[agent_name] = default_status
        
        # Queue update for broadcast
        self.update_queue.put({
            'type': 'agent_status',
            'data': asdict(self.agent_statuses[agent_name])
        })
    
    def update_quality_metrics(self, metrics: Dict[str, float]):
        """Update quality metrics and notify listeners"""
        
        self.quality_metrics = QualityMetricsUpdate(
            overall_score=metrics.get('overall_score', 0.0),
            content_depth=metrics.get('content_depth', 0.0),
            technical_accuracy=metrics.get('technical_accuracy', 0.0),
            expertise_level=metrics.get('expertise_level', 0.0),
            coherence_score=metrics.get('coherence_score', 0.0),
            factual_accuracy=metrics.get('factual_accuracy', 0.0),
            progression=self.quality_progression.copy(),
            timestamp=datetime.now().isoformat()
        )
        
        # Add to progression history
        self.quality_progression.append({
            'timestamp': datetime.now().timestamp(),
            'overall_score': metrics.get('overall_score', 0.0),
            'content_depth': metrics.get('content_depth', 0.0),
            'technical_accuracy': metrics.get('technical_accuracy', 0.0)
        })
        
        # Keep only last 50 entries
        if len(self.quality_progression) > 50:
            self.quality_progression = self.quality_progression[-50:]
        
        # Queue update for broadcast
        self.update_queue.put({
            'type': 'quality_metrics',
            'data': asdict(self.quality_metrics)
        })
    
    def update_workflow_progress(self, state: BookState, current_agent: str, next_agent: Optional[str] = None):
        """Update overall workflow progress"""
        
        completed_count = len(state.completed_steps)
        total_count = len(state.chapters) + 10  # Estimate total steps
        
        overall_progress = (completed_count / total_count) * 100 if total_count > 0 else 0
        
        # Estimate time remaining based on current progress
        if overall_progress > 5:  # Avoid division by zero
            elapsed_time = datetime.now() - datetime.fromisoformat(state.generation_started)
            estimated_total = elapsed_time / (overall_progress / 100)
            time_remaining = estimated_total - elapsed_time
            estimated_completion = str(time_remaining).split('.')[0]  # Remove microseconds
        else:
            estimated_completion = "Calculating..."
        
        self.workflow_progress = WorkflowProgress(
            total_agents=total_count,
            completed_agents=completed_count,
            current_agent=current_agent,
            next_agent=next_agent,
            overall_progress=overall_progress,
            estimated_time_remaining=estimated_completion,
            quality_score=self.quality_metrics.overall_score if self.quality_metrics else 0.0,
            book_title=state.metadata.get('title', state.topic),
            chapter_count=len(state.chapters),
            word_count=sum(len(content.split()) for content in state.chapter_map.values()),
            timestamp=datetime.now().isoformat()
        )
        
        # Queue update for broadcast
        self.update_queue.put({
            'type': 'workflow_progress',
            'data': asdict(self.workflow_progress)
        })
    
    def _process_status_updates(self):
        """Process queued status updates and broadcast to clients"""
        
        while self.is_running:
            try:
                # Get update from queue (blocking with timeout)
                update = self.update_queue.get(timeout=1.0)
                
                # Broadcast to all WebSocket clients
                asyncio.create_task(self._broadcast_update(update))
                
                # Notify other listeners
                for listener in self.listeners:
                    try:
                        listener(update)
                    except Exception as e:
                        self.logger.warning(f"Listener error: {e}")
                
            except Empty:
                continue
            except Exception as e:
                self.logger.error(f"Status update processing error: {e}")
    
    async def _broadcast_update(self, update: Dict[str, Any]):
        """Broadcast update to all WebSocket clients"""
        
        if not self.websocket_clients:
            return
        
        message = json.dumps(update)
        disconnected_clients = []
        
        for client in self.websocket_clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
            except Exception as e:
                self.logger.warning(f"Failed to send to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            if client in self.websocket_clients:
                self.websocket_clients.remove(client)
    
    async def _send_complete_status(self, websocket):
        """Send complete current status to a client"""
        
        complete_status = {
            'type': 'complete_status',
            'data': {
                'agents': {name: asdict(status) for name, status in self.agent_statuses.items()},
                'quality_metrics': asdict(self.quality_metrics) if self.quality_metrics else None,
                'workflow_progress': asdict(self.workflow_progress) if self.workflow_progress else None,
                'timestamp': datetime.now().isoformat()
            }
        }
        
        try:
            await websocket.send(json.dumps(complete_status))
        except Exception as e:
            self.logger.warning(f"Failed to send complete status: {e}")
    
    def add_listener(self, listener: Callable):
        """Add a status update listener"""
        self.listeners.append(listener)
    
    def remove_listener(self, listener: Callable):
        """Remove a status update listener"""
        if listener in self.listeners:
            self.listeners.remove(listener)
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get complete current status for API endpoints"""
        
        return {
            'agents': {name: asdict(status) for name, status in self.agent_statuses.items()},
            'quality_metrics': asdict(self.quality_metrics) if self.quality_metrics else None,
            'workflow_progress': asdict(self.workflow_progress) if self.workflow_progress else None,
            'timestamp': datetime.now().isoformat()
        }

# Global status manager instance
status_manager = RealTimeStatusManager()

class AgentUIIntegration:
    """Mixin class for agents to integrate with UI status system"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.status_manager = status_manager
        self.agent_name = getattr(self, 'agent_type', type(self).__name__).replace('Agent', '').lower()
    
    def update_ui_status(self, **kwargs):
        """Update UI status for this agent"""
        self.status_manager.update_agent_status(self.agent_name, **kwargs)
    
    def start_agent_ui_tracking(self, domain: str = "general"):
        """Start UI tracking for this agent"""
        self.update_ui_status(
            agent_type=str(getattr(self, 'agent_type', 'unknown')),
            status=AgentStatus.RUNNING,
            current_step="initializing",
            domain=domain,
            start_time=datetime.now().isoformat()
        )
    
    def update_agent_progress(self, progress: float, step: str, **kwargs):
        """Update agent progress"""
        self.update_ui_status(
            progress_percent=progress,
            current_step=step,
            **kwargs
        )
    
    def complete_agent_ui_tracking(self, word_count: int = 0, quality_score: float = 0.0):
        """Complete UI tracking for this agent"""
        self.update_ui_status(
            status=AgentStatus.COMPLETED,
            progress_percent=100.0,
            current_step="completed",
            word_count=word_count,
            quality_score=quality_score
        )
    
    def fail_agent_ui_tracking(self, error: str):
        """Mark agent as failed in UI"""
        self.update_ui_status(
            status=AgentStatus.FAILED,
            current_step="failed",
            errors=[error]
        )

def integrate_status_with_state(state: BookState, current_agent: str, next_agent: Optional[str] = None):
    """Helper function to update workflow progress from BookState"""
    status_manager.update_workflow_progress(state, current_agent, next_agent)

def integrate_quality_metrics(metrics):
    """Helper function to update quality metrics"""
    if hasattr(metrics, '__dict__'):
        metrics_dict = metrics.__dict__
    else:
        metrics_dict = dict(metrics)
    
    status_manager.update_quality_metrics(metrics_dict)