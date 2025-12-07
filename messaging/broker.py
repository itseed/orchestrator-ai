"""
Message Broker
Redis-based message broker for agent communication
"""

import json
import asyncio
from typing import Dict, Any, Optional, Callable, List, Set
from datetime import datetime
import redis.asyncio as aioredis
from monitoring import get_logger
from config.settings import get_settings
from messaging.message import Message, MessageFactory, MessageType

logger = get_logger(__name__)


class MessageBroker:
    """
    Redis-based message broker for agent communication
    
    Features:
    - Message queue management
    - Message routing (direct, broadcast)
    - Request-Response pattern support
    - Event-driven pattern support
    - Pub-Sub pattern support
    """
    
    def __init__(
        self,
        redis_url: Optional[str] = None,
        queue_prefix: str = "orchestrator:queue:",
        pubsub_prefix: str = "orchestrator:pubsub:",
        response_prefix: str = "orchestrator:response:"
    ):
        """
        Initialize message broker
        
        Args:
            redis_url: Redis connection URL (uses settings if not provided)
            queue_prefix: Prefix for queue keys
            pubsub_prefix: Prefix for pubsub channels
            response_prefix: Prefix for response keys
        """
        settings = get_settings()
        self.redis_url = redis_url or settings.redis_url
        self.queue_prefix = queue_prefix
        self.pubsub_prefix = pubsub_prefix
        self.response_prefix = response_prefix
        
        self.redis: Optional[aioredis.Redis] = None
        self.pubsub: Optional[aioredis.client.PubSub] = None
        
        # Subscriptions tracking
        self.subscriptions: Dict[str, Set[Callable]] = {}
        
        # Response handlers for request-response pattern
        self.response_handlers: Dict[str, asyncio.Future] = {}
        
        logger.info("MessageBroker initialized", redis_url=self.redis_url)
    
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
            # Test connection
            await self.redis.ping()
            
            logger.info("Connected to Redis")
        except Exception as e:
            logger.error("Failed to connect to Redis", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.close()
            self.pubsub = None
        
        if self.redis:
            await self.redis.close()
            self.redis = None
        
        logger.info("Disconnected from Redis")
    
    async def _ensure_connected(self):
        """Ensure Redis connection is active"""
        if not self.redis:
            await self.connect()
        
        try:
            await self.redis.ping()
        except Exception:
            await self.connect()
    
    def _get_queue_key(self, agent_id: str) -> str:
        """Get queue key for agent"""
        return f"{self.queue_prefix}{agent_id}"
    
    def _get_broadcast_queue_key(self) -> str:
        """Get broadcast queue key"""
        return f"{self.queue_prefix}broadcast"
    
    def _get_pubsub_channel(self, topic: str) -> str:
        """Get pubsub channel key"""
        return f"{self.pubsub_prefix}{topic}"
    
    def _get_response_key(self, correlation_id: str) -> str:
        """Get response key for correlation_id"""
        return f"{self.response_prefix}{correlation_id}"
    
    async def send_message(self, message: Message) -> bool:
        """
        Send message to agent queue
        
        Args:
            message: Message instance
            
        Returns:
            True if successful
        """
        await self._ensure_connected()
        
        try:
            message_json = message.to_json()
            
            if message.is_broadcast():
                # Add to broadcast queue
                queue_key = self._get_broadcast_queue_key()
            else:
                # Add to specific agent queue
                queue_key = self._get_queue_key(message.to_agent)
            
            # Add message to queue (right push)
            await self.redis.rpush(queue_key, message_json)
            
            logger.debug(
                "Message sent",
                message_id=message.message_id,
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                message_type=message.type
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to send message",
                message_id=message.message_id,
                error=str(e)
            )
            return False
    
    async def receive_message(
        self,
        agent_id: str,
        timeout: Optional[float] = None,
        include_broadcast: bool = True
    ) -> Optional[Message]:
        """
        Receive message from agent queue
        
        Args:
            agent_id: Agent ID to receive messages for
            timeout: Timeout in seconds (None = blocking)
            include_broadcast: Whether to include broadcast messages
            
        Returns:
            Message instance or None
        """
        await self._ensure_connected()
        
        try:
            queue_key = self._get_queue_key(agent_id)
            
            # Blocking pop from queue (left pop)
            if timeout:
                result = await self.redis.blpop([queue_key], timeout=timeout)
            else:
                result = await self.redis.blpop([queue_key])
            
            if result:
                _, message_json = result
                message = MessageFactory.from_dict(json.loads(message_json))
                
                # Auto-handle response messages for request-response pattern
                if message.type == MessageType.RESPONSE:
                    await self.handle_response(message)
                
                return message
            
            # Check broadcast queue if enabled
            if include_broadcast:
                broadcast_key = self._get_broadcast_queue_key()
                if timeout:
                    result = await self.redis.blpop([broadcast_key], timeout=0.1)
                else:
                    result = await self.redis.blpop([broadcast_key], timeout=0.1)
                
                if result:
                    _, message_json = result
                    message = MessageFactory.from_dict(json.loads(message_json))
                    if message.is_broadcast():
                        # Auto-handle response messages
                        if message.type == MessageType.RESPONSE:
                            await self.handle_response(message)
                        return message
            
            return None
            
        except Exception as e:
            logger.error(
                "Failed to receive message",
                agent_id=agent_id,
                error=str(e)
            )
            return None
    
    async def request_response(
        self,
        from_agent: str,
        to_agent: str,
        payload: Dict[str, Any],
        timeout: float = 30.0
    ) -> Optional[Message]:
        """
        Send request and wait for response (Request-Response pattern)
        
        Args:
            from_agent: Source agent ID
            to_agent: Target agent ID
            payload: Request payload
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None if timeout
        """
        await self._ensure_connected()
        
        # Create request message (message_id will be auto-generated)
        request = MessageFactory.create_task_message(
            from_agent=from_agent,
            to_agent=to_agent,
            payload=payload
        )
        
        # Create future for response (use message_id as correlation_id)
        # The response should have correlation_id = request.message_id
        future = asyncio.Future()
        self.response_handlers[request.message_id] = future
        
        try:
            # Send request
            await self.send_message(request)
            
            # Wait for response with timeout
            try:
                response = await asyncio.wait_for(future, timeout=timeout)
                return response
            except asyncio.TimeoutError:
                logger.warning(
                    "Request timeout",
                    request_id=request.message_id,
                    timeout=timeout
                )
                return None
                
        finally:
            # Cleanup
            self.response_handlers.pop(request.message_id, None)
    
    async def handle_response(self, response: Message):
        """
        Handle response message (internal use)
        
        Args:
            response: Response message
        """
        if response.correlation_id and response.correlation_id in self.response_handlers:
            future = self.response_handlers[response.correlation_id]
            if not future.done():
                future.set_result(response)
    
    async def publish_event(
        self,
        from_agent: str,
        event_type: str,
        payload: Dict[str, Any],
        topic: Optional[str] = None
    ) -> bool:
        """
        Publish event (Event-Driven pattern)
        
        Args:
            from_agent: Source agent ID
            event_type: Event type
            payload: Event payload
            topic: Optional topic name (uses event_type if not provided)
            
        Returns:
            True if successful
        """
        await self._ensure_connected()
        
        try:
            topic = topic or event_type
            event = MessageFactory.create_event_message(
                from_agent=from_agent,
                event_type=event_type,
                payload=payload
            )
            
            channel = self._get_pubsub_channel(topic)
            await self.redis.publish(channel, event.to_json())
            
            logger.debug(
                "Event published",
                event_type=event_type,
                topic=topic,
                from_agent=from_agent
            )
            
            return True
            
        except Exception as e:
            logger.error(
                "Failed to publish event",
                event_type=event_type,
                error=str(e)
            )
            return False
    
    async def subscribe_event(
        self,
        topic: str,
        callback: Callable[[Message], None]
    ):
        """
        Subscribe to event topic (Pub-Sub pattern)
        
        Args:
            topic: Topic name
            callback: Callback function to handle messages
        """
        await self._ensure_connected()
        
        if topic not in self.subscriptions:
            self.subscriptions[topic] = set()
        
        self.subscriptions[topic].add(callback)
        
        # Initialize pubsub if not exists
        if not self.pubsub:
            self.pubsub = self.redis.pubsub()
        
        channel = self._get_pubsub_channel(topic)
        await self.pubsub.subscribe(channel)
        
        logger.info("Subscribed to topic", topic=topic)
        
        # Start listening in background
        asyncio.create_task(self._listen_pubsub())
    
    async def unsubscribe_event(self, topic: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from event topic
        
        Args:
            topic: Topic name
            callback: Optional callback to remove (removes all if not provided)
        """
        if topic not in self.subscriptions:
            return
        
        if callback:
            self.subscriptions[topic].discard(callback)
        else:
            self.subscriptions[topic].clear()
        
        if not self.subscriptions[topic] and self.pubsub:
            channel = self._get_pubsub_channel(topic)
            await self.pubsub.unsubscribe(channel)
        
        logger.info("Unsubscribed from topic", topic=topic)
    
    async def _listen_pubsub(self):
        """Listen to pubsub messages and call callbacks"""
        if not self.pubsub:
            return
        
        try:
            while True:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message:
                    await self._handle_pubsub_message(message)
        except Exception as e:
            logger.error("Error in pubsub listener", error=str(e))
    
    async def _handle_pubsub_message(self, message: Dict[str, Any]):
        """Handle pubsub message and call callbacks"""
        try:
            channel = message.get("channel", "")
            data = message.get("data", "")
            
            # Extract topic from channel
            topic = channel.replace(self.pubsub_prefix, "")
            
            if topic in self.subscriptions:
                msg = MessageFactory.from_dict(json.loads(data))
                
                # Call all callbacks
                for callback in self.subscriptions[topic]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(msg)
                        else:
                            callback(msg)
                    except Exception as e:
                        logger.error(
                            "Error in subscription callback",
                            topic=topic,
                            error=str(e)
                        )
                        
        except Exception as e:
            logger.error("Error handling pubsub message", error=str(e))
    
    async def get_queue_length(self, agent_id: str) -> int:
        """Get queue length for agent"""
        await self._ensure_connected()
        queue_key = self._get_queue_key(agent_id)
        return await self.redis.llen(queue_key)
    
    async def clear_queue(self, agent_id: str):
        """Clear queue for agent"""
        await self._ensure_connected()
        queue_key = self._get_queue_key(agent_id)
        await self.redis.delete(queue_key)
        logger.info("Queue cleared", agent_id=agent_id)
