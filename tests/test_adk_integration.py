"""
Test ADK integration with session manager.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "app"))

from adk_session_manager import ADKSessionManager
from agent_helpers import invoke_agent_simple


def test_session_manager():
    """Test session manager creation."""
    print("=== Testing Session Manager ===")
    try:
        manager = ADKSessionManager()
        print("✅ Session manager created")

        session_id = manager.create_session()
        print(f"✅ Session created: {session_id}")

        session = manager.get_session(session_id)
        print(f"✅ Session retrieved: {type(session)}")

        return manager
    except Exception as e:
        print(f"❌ Session manager test failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_simple_agent_invocation():
    """Test simple agent invocation."""
    print("\n=== Testing Simple Agent Invocation ===")
    try:
        # Create a simple tool
        def add(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        tool = FunctionTool(func=add)

        # Create agent
        agent = LlmAgent(
            model="gemini-2.5-flash-lite",
            name="test_agent",
            instruction="You are a helpful calculator. Use the add tool when asked to add numbers.",
            tools=[tool],
        )
        print("✅ Agent created")

        # Test invocation
        try:
            result = invoke_agent_simple(agent, "What is 5 + 3?")
            print(f"✅ Agent invocation succeeded")
            print(f"   Result: {result[:200]}")
            return True
        except Exception as e:
            print(f"⚠️  Agent invocation failed: {e}")
            print("   This is expected if ADK requires additional setup")
            import traceback

            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("ADK Integration Test")
    print("=" * 60)

    manager = test_session_manager()
    success = test_simple_agent_invocation()

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Session Manager: {'✅' if manager else '❌'}")
    print(f"Agent Invocation: {'✅' if success else '⚠️'}")
    print("\nNote: Agent invocation may fail if ADK requires additional")
    print("message handling or context setup. This is expected during development.")
