# CLAUDE.md — Resilience Agent

## Purpose

AI-powered PR analysis agent that identifies production readiness issues:
- **Use Case 1:** Change Risk & Test Recommendations
- **Use Case 2:** Observability Review
- **Use Case 3:** Production Configuration Review

## Usage

### Claude Code (Demo)
```
/analyze-pr 1234
```

### Claude Agent SDK (Automation)
```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

options = ClaudeAgentOptions(
    setting_sources=["project"],
    agents_dir=".claude/agents"
)

async with ClaudeSDKClient(options=options) as client:
    await client.query("/analyze-pr 1234")
```

## Architecture

```
User: /analyze-pr 1234
    ↓
[Orchestrator: analyze-pr.md]
    ↓
    ├─→ risk-analyzer.md → output/pr-1234/risk-analysis.json
    ├─→ observability-reviewer.md → output/pr-1234/observability-analysis.json
    ├─→ config-reviewer.md → output/pr-1234/config-analysis.json
    ↓
[Critic Agent: critic-agent.md]
    ├─ Reads all 3 JSON artifacts
    ├─ Validates findings (quality gate)
    ├─ Filters false positives
    ├─ Synthesizes final report
    └─→ output/pr-1234/final-report.md
    ↓
[Orchestrator] Presents final report to user
```

## Components

- **Orchestrator:** `.claude/commands/analyze-pr.md` - Main command
- **Use Case 1:** `.claude/agents/risk-analyzer.md` - Change risk & test recommendations
- **Use Case 2:** `.claude/agents/observability-reviewer.md` - Logging, metrics, tracing
- **Use Case 3:** `.claude/agents/config-reviewer.md` - Production configuration
- **Quality Gate:** `.claude/agents/critic-agent.md` - Validates all findings

## Workflow

1. User invokes `/analyze-pr {PR_NUMBER}`
2. Orchestrator creates `output/pr-{NUMBER}/` directory
3. Orchestrator invokes 3 specialized agents sequentially:
   - Risk Analyzer (Use Case 1)
   - Observability Reviewer (Use Case 2)
   - Config Reviewer (Use Case 3)
4. Each agent outputs JSON to `output/pr-{NUMBER}/`
5. Critic agent validates all findings, filters false positives
6. Critic synthesizes final report as Markdown
7. Orchestrator presents report to user

## Use Cases

### Use Case 1: Change Risk & Test Recommendations
- Detects new failure modes (missing circuit breakers, timeouts)
- Identifies breaking API changes
- Recommends test strategies (integration, contract, negative tests)
- Handles Java, Node.js, React, Android

### Use Case 2: Observability Review
- Checks error logging quality (structured, queryable)
- Validates metrics and monitoring
- Verifies distributed tracing
- Ensures alerts for anomalous conditions

### Use Case 3: Production Configuration Review
- Validates configuration changes
- Checks for missing production config values
- Identifies invalid configurations
- Recommends production config test scripts

## Key Design Decisions

**Function-Based Agents (Not Language-Based):**
- ONE risk-analyzer handles all languages (Java, Node, React, Android)
- 4× more efficient than separate language agents
- Catches cross-language issues (React → Node → Java flows)

**High-Level Instructions (Not Prescriptive):**
- Agents told WHAT to find, not HOW to find it
- Claude uses tools intelligently (Grep, Read, Bash)
- More flexible and adaptable

**Artifact Pattern:**
- Agents output JSON to `output/pr-{NUMBER}/`
- Minimizes "game of telephone" between agents
- Persistent storage for audit trail

**Quality Gate Pattern:**
- Critic agent validates all findings before presentation
- Filters false positives
- Resolves contradictions
- Ensures actionable recommendations

## Output Structure

```
output/
└── pr-1234/
    ├── risk-analysis.json
    ├── observability-analysis.json
    ├── config-analysis.json
    ├── final-report.md
    └── metadata.json
```

## Extension Points

- Add new subagents in `.claude/agents/`
- Update orchestrator to invoke new agents
- Agents automatically loaded by Claude Agent SDK

## Quality Gates

- Every finding has file:line reference
- Recommendations are specific and actionable
- Severity levels justified by impact
- Test recommendations provided
- Structured JSON + Markdown output

## Day 1 Scope

✅ Working `/analyze-pr` command
✅ 3 specialized agents (Use Cases 1, 2, 3)
✅ Critic quality gate
✅ Artifact-based workflow
✅ Live demo in Claude Code

## Future (Day 2+)

⏳ GitHub/GitLab API integration (fetch PR diffs automatically)
⏳ Post findings as PR comments
⏳ Knowledge base / RAG for deeper pattern matching
⏳ Python automation script for CI/CD
⏳ Slack/email notifications
