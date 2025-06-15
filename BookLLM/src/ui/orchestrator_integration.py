"""
Unified UI Orchestration System
Integrates all UI components with the BookLLM orchestrator for seamless real-time updates
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from ..core.orchestrator import BookOrchestrator
from ..agents.enhanced_agents import QualityEnhancedOrchestrator
from ..ui.realtime_integration import status_manager, RealTimeStatusManager
from ..utils.logger import get_logger

class UIIntegratedOrchestrator:
    """Orchestrator with full UI integration and real-time status updates"""
    
    def __init__(self, base_orchestrator: BookOrchestrator):
        self.base_orchestrator = base_orchestrator
        self.quality_orchestrator = QualityEnhancedOrchestrator(base_orchestrator)
        self.status_manager = status_manager
        self.logger = get_logger(__name__)
        
        # Start real-time status management
        self.status_manager.start_status_manager()
        
        # Hook into all agent executions
        self._integrate_agent_monitoring()
    
    def _integrate_agent_monitoring(self):
        """Integrate monitoring into all agents"""
        
        # Get original graph execution method
        original_invoke = self.base_orchestrator.graph.invoke
        
        def monitored_invoke(state):
            """Monitored version of graph invoke with UI updates"""
            
            # Start overall workflow tracking
            self.status_manager.update_workflow_progress(
                state, 
                current_agent='initializing',
                next_agent='outline'
            )
            
            # Track each step in the workflow
            workflow_steps = self.base_orchestrator.graph._define_workflow()
            
            for i, step_name in enumerate(workflow_steps):
                current_agent = step_name.replace('_node', '')
                next_agent = workflow_steps[i + 1].replace('_node', '') if i + 1 < len(workflow_steps) else None
                
                # Update status before agent execution
                self.status_manager.update_agent_status(
                    current_agent,
                    status='running',
                    current_step='executing',
                    agent_type=current_agent,
                    domain=self._extract_domain(state.topic)
                )
                
                # Update workflow progress
                self.status_manager.update_workflow_progress(
                    state,
                    current_agent=current_agent,
                    next_agent=next_agent
                )
            
            # Execute original invoke
            result = original_invoke(state)
            
            # Final status update
            self.status_manager.update_workflow_progress(
                result,
                current_agent='completed',
                next_agent=None
            )
            
            return result
        
        # Replace the invoke method
        self.base_orchestrator.graph.invoke = monitored_invoke
    
    async def generate_book_with_ui(self, topic: str, **kwargs) -> Dict[str, Any]:
        """Generate book with full UI integration and real-time updates"""
        
        self.logger.info(f"Starting UI-integrated book generation for: {topic}")
        
        try:
            # Start generation with quality enhancements
            result = await self.quality_orchestrator.generate_professional_book(topic, **kwargs)
            
            # Final status updates
            self.status_manager.update_quality_metrics(result['quality_metrics'].__dict__)
            
            # Mark all agents as completed
            for agent_name in self.base_orchestrator.agents.keys():
                self.status_manager.update_agent_status(
                    agent_name,
                    status='completed',
                    progress_percent=100.0,
                    current_step='finished'
                )
            
            self.logger.info(f"Book generation completed with score: {result['final_score']}/1000")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Book generation failed: {e}")
            
            # Update UI with failure status
            self.status_manager.update_agent_status(
                'system',
                status='failed',
                errors=[str(e)],
                current_step='error'
            )
            
            raise
    
    def _extract_domain(self, topic: str) -> str:
        """Extract domain from topic for UI display"""
        topic_lower = topic.lower()
        
        domain_keywords = {
            'machine_learning': ['machine learning', 'ml', 'ai', 'neural', 'deep learning'],
            'software_engineering': ['software', 'programming', 'development', 'coding'],
            'data_science': ['data science', 'analytics', 'statistics', 'data analysis'],
            'cybersecurity': ['security', 'cybersecurity', 'hacking', 'encryption'],
            'cloud_computing': ['cloud', 'aws', 'azure', 'kubernetes', 'docker'],
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in topic_lower for keyword in keywords):
                return domain
        
        return 'general_technology'
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current status for API endpoints"""
        return self.status_manager.get_current_status()
    
    def add_status_listener(self, listener_func):
        """Add a custom status listener"""
        self.status_manager.add_listener(listener_func)
    
    def stop_ui_integration(self):
        """Stop UI integration and clean up resources"""
        self.status_manager.stop_status_manager()
        self.logger.info("UI integration stopped")

class WebSocketStatusServer:
    """Dedicated WebSocket server for status updates"""
    
    def __init__(self, orchestrator: UIIntegratedOrchestrator, host="localhost", port=8765):
        self.orchestrator = orchestrator
        self.host = host
        self.port = port
        self.server = None
        self.logger = get_logger(__name__)
    
    async def start_server(self):
        """Start the WebSocket server"""
        import websockets
        
        async def handle_client(websocket, path):
            self.logger.info(f"WebSocket client connected: {websocket.remote_address}")
            
            try:
                # Send initial status
                initial_status = self.orchestrator.get_current_status()
                await websocket.send(json.dumps({
                    'type': 'complete_status',
                    'data': initial_status
                }))
                
                # Add client to status manager
                self.orchestrator.status_manager.websocket_clients.append(websocket)
                
                # Keep connection alive
                await websocket.wait_closed()
                
            except websockets.exceptions.ConnectionClosed:
                pass
            finally:
                if websocket in self.orchestrator.status_manager.websocket_clients:
                    self.orchestrator.status_manager.websocket_clients.remove(websocket)
                self.logger.info("WebSocket client disconnected")
        
        self.server = await websockets.serve(handle_client, self.host, self.port)
        self.logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
        return self.server
    
    async def stop_server(self):
        """Stop the WebSocket server"""
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.logger.info("WebSocket server stopped")

def create_ui_integrated_book_generator(config_path: Optional[str] = None) -> UIIntegratedOrchestrator:
    """Create a fully UI-integrated book generator"""
    
    # Create base orchestrator
    base_orchestrator = BookOrchestrator(config_path)
    
    # Create UI-integrated orchestrator
    ui_orchestrator = UIIntegratedOrchestrator(base_orchestrator)
    
    return ui_orchestrator

async def run_ui_integrated_generation(topic: str, **kwargs) -> Dict[str, Any]:
    """Complete UI-integrated book generation workflow"""
    
    # Create UI-integrated orchestrator
    orchestrator = create_ui_integrated_book_generator()
    
    try:
        # Start WebSocket server for real-time updates
        websocket_server = WebSocketStatusServer(orchestrator)
        server = await websocket_server.start_server()
        
        # Generate book with full UI integration
        result = await orchestrator.generate_book_with_ui(topic, **kwargs)
        
        return result
        
    finally:
        # Clean up
        orchestrator.stop_ui_integration()
        if 'server' in locals():
            await websocket_server.stop_server()

class UIHealthChecker:
    """Health checker for UI integration system"""
    
    def __init__(self, orchestrator: UIIntegratedOrchestrator):
        self.orchestrator = orchestrator
        self.logger = get_logger(__name__)
    
    def check_status_manager(self) -> Dict[str, Any]:
        """Check status manager health"""
        return {
            'running': self.orchestrator.status_manager.is_running,
            'websocket_clients': len(self.orchestrator.status_manager.websocket_clients),
            'active_agents': len(self.orchestrator.status_manager.agent_statuses),
            'quality_metrics_available': self.orchestrator.status_manager.quality_metrics is not None,
            'workflow_progress_available': self.orchestrator.status_manager.workflow_progress is not None
        }
    
    def check_websocket_connectivity(self) -> Dict[str, Any]:
        """Check WebSocket connectivity"""
        try:
            import websockets
            return {
                'websockets_available': True,
                'active_connections': len(self.orchestrator.status_manager.websocket_clients)
            }
        except ImportError:
            return {
                'websockets_available': False,
                'error': 'websockets package not installed'
            }
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get complete system health status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'status_manager': self.check_status_manager(),
            'websocket': self.check_websocket_connectivity(),
            'orchestrator_healthy': hasattr(self.orchestrator, 'base_orchestrator'),
            'quality_system_healthy': hasattr(self.orchestrator, 'quality_orchestrator')
        }