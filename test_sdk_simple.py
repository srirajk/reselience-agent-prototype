#!/usr/bin/env python3
"""
Simple test of Claude Agent SDK with local filesystem
Tests basic query functionality using project settings and working directory
"""

import asyncio
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock


async def test_filesystem_access():
    """Test basic filesystem access - read files and list directory"""
    print("[TEST 1] Testing Claude Agent SDK with Local Filesystem\n")

    # Configure SDK with working directory and project settings
    options = ClaudeAgentOptions(
        cwd=Path.cwd(),              # Set working directory to current directory
        setting_sources=["project"]   # Load .claude/ configurations (agents, commands, settings)
    )

    async with ClaudeSDKClient(options=options) as client:
        print("Query: List files and read CLAUDE.md\n")

        await client.query("List the files in the current directory, then read CLAUDE.md and summarize what this project does in 2-3 sentences")

        # Process response messages
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print("Response:")
                        print("-" * 60)
                        print(block.text)
                        print("-" * 60)


async def test_main_py():
    """Test reading main.py file"""
    print("\n[TEST 2] Testing Reading main.py\n")

    options = ClaudeAgentOptions(
        cwd=Path.cwd(),
        setting_sources=["project"]
    )

    async with ClaudeSDKClient(options=options) as client:
        print("Query: What is in main.py?\n")

        await client.query("Read main.py and tell me what it contains")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print("Response:")
                        print("-" * 60)
                        print(block.text)
                        print("-" * 60)


async def test_agents_discovery():
    """Test if agents are discovered from .claude/agents/"""
    print("\n[TEST 3] Testing Agent Discovery\n")

    options = ClaudeAgentOptions(
        cwd=Path.cwd(),
        setting_sources=["project"]
    )

    async with ClaudeSDKClient(options=options) as client:
        print("Query: What agents are available in .claude/agents/?\n")

        await client.query("List the agent files in .claude/agents/ directory and tell me what each one does")

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print("Response:")
                        print("-" * 60)
                        print(block.text)
                        print("-" * 60)


async def main():
    """Main test runner"""
    try:
        # Test 1: Basic filesystem access
        await test_filesystem_access()

        # Test 2: Read main.py
        await test_main_py()

        # Test 3: Agent discovery
        await test_agents_discovery()

        print("\n[SUCCESS] All tests completed successfully!")

    except Exception as e:
        print(f"\n[ERROR] Error occurred: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
