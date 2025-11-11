#!/usr/bin/env python3
"""
Run /analyze-pr command using Claude Agent SDK
This will trigger the PR analysis workflow and output results to output/pr-{NUMBER}/ directory
"""

import asyncio
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, AssistantMessage, TextBlock


async def run_analyze_pr(repo: str, pr_number: int):
    """
    Execute /analyze-pr command via Claude Agent SDK

    Args:
        repo: Repository name (e.g., "spring-petclinic-microservices")
        pr_number: PR number to analyze (e.g., 495)
    """
    print(f"[START] Running /analyze-pr {repo} {pr_number}\n")
    print(f"Output will be written to: output/pr-{pr_number}/\n")
    print("=" * 70)

    # Configure SDK with working directory and project settings
    options = ClaudeAgentOptions(
        cwd=Path.cwd(),              # Current working directory
        setting_sources=["project", "local"]   # Load .claude/ configurations
    )

    async with ClaudeSDKClient(options=options) as client:
        # Execute the /analyze-pr command
        command = f"/analyze-pr {repo} {pr_number}"
        print(f"\n[COMMAND] {command}\n")

        await client.query(command)

        # Stream and display all response messages
        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)
                        print()  # Extra newline for readability

    print("=" * 70)
    print(f"\n[COMPLETE] Analysis finished!")
    print(f"Check output/pr-{pr_number}/ for results:")
    print(f"  - risk-analysis.json")
    print(f"  - final-report.md")
    print(f"  - metadata.json")


async def main():
    """Main entry point"""
    try:
        # Run the PR analysis
        await run_analyze_pr("spring-petclinic-microservices", 494)

    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
