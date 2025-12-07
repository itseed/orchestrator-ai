"""
Agent Communication
Helper classes for agent-to-agent communication
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from monitoring import get_logger
from messaging.broker import MessageBroker
from messaging.message import Message, MessageFactory, MessageType
from agents.base import BaseAgent

logger = get_logger(__name__)


class AgentCommunicator:
    """
    Helper class for agent-to-agent communication
    
    Supports:
    - Direct communication (1-to-1)
    - Mediated communication (via orchestrator)
    - Broadcast communication (1-to-many)
    """
    
    def __init__(self, agent: BaseAgent, message_broker: MessageBroker):
        """
        Initialize agent communicator
        
        Args:
            agent: BaseAgent instance
            message_broker: MessageBroker instance
        """
        self.agent = agent
        self.broker = message_broker
        self.listening = False
        self.message_handlers: Dict[str, Callable] = {}
        logger.info("AgentCommunicator initialized", agent_id=agent.agent_id)
    
    async def connect(self):
        """Connect to message broker"""
        await self.broker.connect()
    
    async def send_to_agent(
        self,
        to_agent_id: str,
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.TASK
    ) -> bool:
        """
        Send message directly to another agent
        
        Args:
            to_agent_id: Target agent ID
            payload: Message payload
            message_type: Message type
            
        Returns:
            True if successful
        """
        if message_type == MessageType.TASK:
            message = MessageFactory.create_task_message(
                from_agent=self.agent.agent_id,
                to_agent=to_agent_id,
                payload=payload
            )
        elif message_type == MessageType.STATUS:
            message = MessageFactory.create_status_message(
                from_agent=self.agent.agent_id,
                to_agent=to_agent_id,
                payload=payload
            )
        else:
            message = Message(
                type=message_type,
                from_agent=self.agent.agent_id,
                to_agent=to_agent_id,
                payload=payload
            )
        
        return await self.broker.send_message(message)
    
    async def send_to_agents(
        self,
        to_agent_ids: list[str],
        payload: Dict[str, Any],
        message_type: MessageType = MessageType.TASK
    ) -> int:
        """
        Send message to multiple agents
        
        Args:
            to_agent_ids: List of target agent IDs
            payload: Message payload
            message_type: Message type
            
        Returns:
            Number of messages sent successfully
        """
        success_count = 0
        for agent_id in to_agent_ids:
            if await self.send_to_agent(agent_id, payload, message_type):
                success_count += 1
        
        return success_count
    
    async def broadcast(
        self,
        payload: Dict[str, Any],
        event_type: Optional[str] = None
    ) -> bool:
        """
        Broadcast message to all agents
        
        Args:
            payload: Message payload
            event_type: Optional event type (for EventMessage)
            
        Returns:
            True if successful
        """
        if event_type:
            message = MessageFactory.create_event_message(
                from_agent=self.agent.agent_id,
                event_type=event_type,
                payload=payload
            )
        else:
            message = MessageFactory.create_task_message(
                from_agent=self.agent.agent_id,
                to_agent="broadcast",
                payload=payload
            )
        
        return await self.broker.send_message(message)
    
    async def request_from_agent(
        self,
        to_agent_id: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Dict[str, Any]]:
        """
        Send request to agent and wait for response (Request-Response pattern)
        
        Args:
            to_agent_id: Target agent ID
            payload: Request payload
            timeout: Response timeout in seconds
            
        Returns:
            Response payload or None if timeout
        """
        response = await self.broker.request_response(
            from_agent=self.agent.agent_id,
            to_agent=to_agent_id,
            payload=payload,
            timeout=timeout
        )
        
        if response:
            return response.payload
        
        return None
    
    async def start_listening(self, handler: Optional[Callable] = None):
        """
        Start listening for messages
        
        Args:
            handler: Optional message handler function
        """
        if self.listening:
            logger.warning("Already listening", agent_id=self.agent.agent_id)
            return
        
        self.listening = True
        
        # Use provided handler or default
        if handler:
            self.message_handlers['default'] = handler
        else:
            self.message_handlers['default'] = self._default_message_handler
        
        logger.info("Started listening for messages", agent_id=self.agent.agent_id)
        
        # Start message loop in background
        asyncio.create_task(self._message_loop())
    
    async def stop_listening(self):
        """Stop listening for messages"""
        self.listening = False
        logger.info("Stopped listening for messages", agent_id=self.agent.agent_id)
    
    async def _message_loop(self):
        """Main message listening loop"""
        while self.listening:
            try:
                message = await self.broker.receive_message(
                    self.agent.agent_id,
                    timeout=1.0
                )
                
                if message:
                    await self._handle_message(message)
            except Exception as e:
                logger.error(
                    "Error in message loop",
                    agent_id=self.agent.agent_id,
                    error=str(e)
                )
                await asyncio.sleep(1)
    
    async def _handle_message(self, message: Message):
        """Handle received message"""
        handler = self.message_handlers.get('default')
        if handler:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                logger.error(
                    "Error handling message",
                    agent_id=self.agent.agent_id,
                    message_id=message.message_id,
                    error=str(e)
                )
    
    async def _default_message_handler(self, message: Message):
        """Default message handler"""
        logger.info(
            "Received message",
            agent_id=self.agent.agent_id,
            message_id=message.message_id,
            from_agent=message.from_agent,
            message_type=message.type
        )
        
        # Auto-respond to task messages if it's a request-response
        if message.type == MessageType.TASK:
            # Try to execute as a task
            try:
                result = await self.agent.execute(message.payload)
                
                # Send response if correlation_id exists
                if message.message_id:  # Use message_id as correlation_id
                    response = MessageFactory.create_response_message(
                        from_agent=self.agent.agent_id,
                        to_agent=message.from_agent,
                        payload=result,
                        correlation_id=message.message_id
                    )
                    await self.broker.send_message(response)
            except Exception as e:
                logger.error(
                    "Error executing task from message",
                    agent_id=self.agent.agent_id,
                    message_id=message.message_id,
                    error=str(e)
                )
    
    async def subscribe_event(
        self,
        event_type: str,
        handler: Callable[[Message], None]
    ):
        """
        Subscribe to event type
        
        Args:
            event_type: Event type to subscribe to
            handler: Handler function for events
        """
        self.message_handlers[event_type] = handler
        
        await self.broker.subscribe_event(
            event_type,
            handler
        )
        
        logger.info(
            "Subscribed to event",
            agent_id=self.agent.agent_id,
            event_type=event_type
        )
    
    async def publish_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> bool:
        """
        Publish event
        
        Args:
            event_type: Event type
            payload: Event payload
            
        Returns:
            True if successful
        """
        return await self.broker.publish_event(
            from_agent=self.agent.agent_id,
            event_type=event_type,
            payload=payload
        )

