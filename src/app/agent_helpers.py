"""
Helper functions for ADK agent invocation and result extraction.

This module provides utilities to work with Google ADK agents, including:
- Agent invocation helpers
- Result extraction utilities
- Context management (when needed)
"""

import os
import json
import asyncio
from typing import Optional, Dict, Any, List, Union
from dotenv import load_dotenv

load_dotenv()

try:
    from google.adk.agents import LlmAgent, InvocationContext
    from google.adk.tools import FunctionTool
except ImportError as e:
    raise ImportError(
        "google-adk package is required. Install it with: poetry add google-adk"
    ) from e


# ADK API Findings:
# - Agents have `run_live()` and `run_async()` methods
# - Both require InvocationContext (not simple string prompts)
# - InvocationContext requires: session_service, invocation_id, session, agent
# - This is more complex than expected - may need session management
# - For now, we'll use a hybrid approach: direct tool calls for reliability,
#   and document the ADK pattern for future use


def invoke_agent_simple(
    agent: LlmAgent,
    prompt: str,
    context: Optional[Dict[str, Any]] = None,
    session_id: Optional[str] = None,
) -> str:
    """
    Simplified agent invocation using session manager.

    Args:
        agent: The LlmAgent instance to invoke
        prompt: User prompt/message
        context: Optional context dictionary (for future use)
        session_id: Optional session ID for multi-turn conversations

    Returns:
        Agent response as string
    """
    from adk_session_manager import get_session_manager

    try:
        session_manager = get_session_manager()
        events = session_manager.run_agent_sync(agent, prompt, session_id)

        # Extract text from events
        # Events may contain various types - we'll look for text/message content
        result_text = ""
        for event in events:
            try:
                text = extract_text_from_agent_response(event)
                if text:
                    result_text += text + "\n"
            except (AttributeError, TypeError) as e:
                # Skip events that cause attribute errors (e.g., response_modalities on None)
                # This can happen when the agent framework processes tool responses
                continue

        return result_text.strip() if result_text else str(events[-1]) if events else ""
    except (AttributeError, TypeError) as e:
        # Handle attribute errors that might occur during agent invocation
        # (e.g., response_modalities on None)
        # Return empty string to trigger fallback to direct tool calls
        if "response_modalities" in str(e):
            return ""
        # Re-raise other attribute/type errors
        raise Exception(f"Agent invocation error: {str(e)}")
    except Exception as e:
        # Handle any other exceptions
        # Return empty string to trigger fallback to direct tool calls
        if "response_modalities" in str(e):
            return ""
        raise


def extract_text_from_agent_response(response: Any) -> str:
    """
    Extract text content from agent response.

    Args:
        response: Agent response object (format TBD)

    Returns:
        Extracted text content
    """
    # Handle None response
    if response is None:
        return ""

    if isinstance(response, str):
        return response

    # Try common attributes
    if hasattr(response, "text"):
        return response.text
    if hasattr(response, "content"):
        return str(response.content)
    if hasattr(response, "message"):
        return str(response.message)

    # Fallback to string representation
    return str(response)


def extract_json_from_agent_response(response: Any) -> Optional[Dict[str, Any]]:
    """
    Extract JSON data from agent response.

    Args:
        response: Agent response object

    Returns:
        Parsed JSON dictionary, or None if not found
    """
    text = extract_text_from_agent_response(response)

    # Try to find JSON in the text
    # Look for JSON code blocks
    import re

    json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

    # Try to find JSON object directly
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Try parsing entire text as JSON
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    return None


def extract_file_path_from_response(response: Any) -> Optional[str]:
    """
    Extract file path from agent response.

    Args:
        response: Agent response object

    Returns:
        File path string, or None if not found
    """
    text = extract_text_from_agent_response(response)

    # Look for file paths (common patterns)
    import re

    # Look for absolute paths
    path_match = re.search(r"(/[^\s]+\.(mp4|mp3|png|jpg|jpeg|json))", text)
    if path_match:
        path = path_match.group(1)
        if os.path.exists(path):
            return path

    # Look for relative paths in outputs directory
    outputs_match = re.search(r"(outputs/[^\s]+\.(mp4|mp3|png|jpg|jpeg))", text)
    if outputs_match:
        path = outputs_match.group(1)
        abs_path = os.path.abspath(path)
        if os.path.exists(abs_path):
            return abs_path

    return None


# For now, we'll use direct tool calls with agent-like orchestration
# This provides reliability while we work on proper ADK integration


def orchestrate_with_agent_instructions(
    agent_instruction: str,
    tools: Dict[str, FunctionTool],
    task_description: str,
) -> str:
    """
    Orchestrate task using agent instructions but with direct tool calls.

    This is a hybrid approach: use agent instructions to guide the workflow,
    but execute tools directly for reliability.

    Args:
        agent_instruction: The agent's instruction text (for reference)
        tools: Dictionary of available tools
        task_description: Description of the task to perform

    Returns:
        Result message
    """
    # This is a placeholder for future agent-driven execution
    # For now, return a message indicating direct tool calls should be used
    return (
        f"Task: {task_description}\n"
        f"Agent instruction: {agent_instruction}\n"
        f"Available tools: {list(tools.keys())}\n"
        f"Note: Using direct tool calls for reliability."
    )


# Documentation for future ADK integration:
"""
ADK Integration Notes:

1. InvocationContext Requirements:
   - session_service: SessionService instance
   - invocation_id: Unique ID for this invocation
   - session: Session object
   - agent: The agent being invoked

2. Session Management:
   - Need to create/obtain SessionService
   - Create sessions for user interactions
   - Manage session lifecycle

3. Agent Invocation Pattern (when implemented):
   ```python
   from google.adk.agents import LlmAgent, InvocationContext
   from google.adk.session import SessionService, Session
   
   # Setup (one-time)
   session_service = SessionService()
   session = session_service.create_session()
   
   # Invoke agent
   context = InvocationContext(
       session_service=session_service,
       invocation_id="unique-id",
       session=session,
       agent=agent
   )
   
   async for event in agent.run_live(context):
       # Process events
       pass
   ```

4. Current Approach:
   - Use direct tool calls for reliability
   - Keep agent instructions for guidance
   - Document ADK patterns for future use
"""
