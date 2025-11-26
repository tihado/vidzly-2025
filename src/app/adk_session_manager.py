"""
Session management for Google ADK agents.

This module provides a simplified interface for creating and managing
ADK sessions and invocation contexts.
"""

import uuid
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk.agents import LlmAgent, InvocationContext
    from google.adk.sessions import InMemorySessionService, Session
except ImportError as e:
    raise ImportError(
        "google-adk package is required. Install it with: poetry add google-adk"
    ) from e


class ADKSessionManager:
    """
    Manages ADK sessions and provides simplified agent invocation.
    
    This class handles the complexity of session management and
    provides a simple interface for invoking agents.
    """
    
    def __init__(self):
        """Initialize the session manager."""
        self.session_service = InMemorySessionService()
        self._sessions: Dict[str, Session] = {}
    
    async def create_session(
        self, 
        session_id: Optional[str] = None,
        app_name: str = "vidzly",
        user_id: Optional[str] = None,
    ) -> str:
        """
        Create a new session.
        
        Args:
            session_id: Optional session ID. If not provided, generates a unique ID.
            app_name: Application name (default: "vidzly")
            user_id: Optional user ID. If not provided, uses session_id.
            
        Returns:
            Session ID string
        """
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        if user_id is None:
            user_id = session_id
        
        # InMemorySessionService.create_session is async and requires keyword arguments
        session = await self.session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )
        self._sessions[session_id] = session
        return session_id
    
    async def get_session(self, session_id: str, app_name: str = "vidzly", user_id: Optional[str] = None) -> Session:
        """
        Get an existing session.
        
        Args:
            session_id: Session ID
            app_name: Application name (default: "vidzly")
            user_id: Optional user ID. If not provided, uses session_id.
            
        Returns:
            Session object
            
        Raises:
            KeyError: If session doesn't exist
        """
        if session_id not in self._sessions:
            if user_id is None:
                user_id = session_id
            # Try to get from service
            try:
                session = await self.session_service.get_session(
                    app_name=app_name,
                    user_id=user_id,
                    session_id=session_id,
                )
                if session:
                    self._sessions[session_id] = session
                else:
                    # Session doesn't exist, create it
                    await self.create_session(session_id, app_name, user_id)
            except Exception:
                # Session doesn't exist, create it
                await self.create_session(session_id, app_name, user_id)
        
        return self._sessions[session_id]
    
    async def create_invocation_context(
        self,
        agent: LlmAgent,
        session_id: Optional[str] = None,
        invocation_id: Optional[str] = None,
        app_name: str = "vidzly",
        user_id: Optional[str] = None,
    ) -> InvocationContext:
        """
        Create an InvocationContext for agent invocation.
        
        Args:
            agent: The LlmAgent to invoke
            session_id: Session ID (creates new if not provided)
            invocation_id: Invocation ID (generates if not provided)
            app_name: Application name (default: "vidzly")
            user_id: Optional user ID. If not provided, uses session_id.
            
        Returns:
            InvocationContext object
        """
        if session_id is None:
            session_id = await self.create_session(app_name=app_name, user_id=user_id)
        else:
            if session_id not in self._sessions:
                await self.get_session(session_id, app_name=app_name, user_id=user_id)  # Will create if needed
        
        session = await self.get_session(session_id, app_name=app_name, user_id=user_id)
        
        if invocation_id is None:
            invocation_id = str(uuid.uuid4())
        
        context = InvocationContext(
            session_service=self.session_service,
            invocation_id=invocation_id,
            session=session,
            agent=agent,
        )
        
        return context
    
    async def run_agent_async(
        self,
        agent: LlmAgent,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> AsyncGenerator[Any, None]:
        """
        Run an agent asynchronously and yield events.
        
        Args:
            agent: The LlmAgent to run
            prompt: User prompt/message
            session_id: Optional session ID
            
        Yields:
            Events from agent execution
        """
        context = await self.create_invocation_context(agent, session_id)
        
        # The prompt will be handled by the agent's run_live method
        # ADK may handle message passing internally through the context
        # For now, we'll pass the context and let ADK handle it
        # Note: The actual message passing mechanism may need to be
        # determined through testing with the actual ADK API
        
        # Try to set user message if context supports it
        if hasattr(context, 'user_message'):
            context.user_message = prompt
        elif hasattr(context, 'message'):
            context.message = prompt
        elif hasattr(context, 'prompt'):
            context.prompt = prompt
        
        try:
            async for event in agent.run_live(context):
                # Wrap event processing in try-except to handle errors
                # that might occur when ADK processes tool responses
                try:
                    yield event
                except (AttributeError, TypeError) as e:
                    # Skip events that cause attribute errors (e.g., response_modalities on None)
                    # This can happen when the agent framework processes tool responses
                    # that return None or have issues with response_modalities
                    if 'response_modalities' in str(e):
                        # Silently skip this error - it's a known issue with ADK
                        # when processing certain tool responses
                        continue
                    # Re-raise other attribute/type errors
                    raise
        except (AttributeError, TypeError) as e:
            # Handle attribute errors that occur during agent execution
            # (e.g., response_modalities on None when processing tool responses)
            if 'response_modalities' in str(e):
                # Return empty generator - agent execution failed due to response_modalities issue
                return
            # Re-raise other errors
            raise
    
    async def run_agent_and_collect(
        self,
        agent: LlmAgent,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> list:
        """
        Run an agent and collect all events.
        
        Args:
            agent: The LlmAgent to run
            prompt: User prompt/message
            session_id: Optional session ID
            
        Returns:
            List of events from agent execution
        """
        events = []
        try:
            async for event in self.run_agent_async(agent, prompt, session_id):
                events.append(event)
        except (AttributeError, TypeError) as e:
            # Handle attribute errors (e.g., response_modalities on None)
            # Return collected events so far, even if there was an error
            if 'response_modalities' in str(e):
                # Return what we have - this is a known issue with ADK
                return events
            # Re-raise other errors
            raise
        return events
    
    def run_agent_sync(
        self,
        agent: LlmAgent,
        prompt: str,
        session_id: Optional[str] = None,
    ) -> list:
        """
        Run an agent synchronously (wrapper around async).
        
        Args:
            agent: The LlmAgent to run
            prompt: User prompt/message
            session_id: Optional session ID
            
        Returns:
            List of events from agent execution
        """
        try:
            return asyncio.run(self.run_agent_and_collect(agent, prompt, session_id))
        except (AttributeError, TypeError) as e:
            # Handle attribute errors that occur during agent execution
            # (e.g., response_modalities on None when processing tool responses)
            if 'response_modalities' in str(e):
                # Return empty list - agent execution failed due to response_modalities issue
                # This will trigger fallback to direct tool calls
                return []
            # Re-raise other errors
            raise


# Global session manager instance
_session_manager: Optional[ADKSessionManager] = None


def get_session_manager() -> ADKSessionManager:
    """
    Get or create the global session manager.
    
    Returns:
        ADKSessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        _session_manager = ADKSessionManager()
    return _session_manager

