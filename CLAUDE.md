# CLAUDE.md — Resilience Agent

## Purpose

AI-powered PR analysis agent that identifies change risk and production readiness issues:
- **Change Risk & Test Recommendations:** Detects failure modes, breaking changes, recommends tests
- **Quality Gate:** Validates findings and filters false positives

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
    └─→ risk-analyzer.md → output/pr-1234/risk-analysis.json
    ↓
[Critic Agent: critic-agent.md]
    ├─ Reads risk-analysis.json
    ├─ Validates findings (quality gate)
    ├─ Filters false positives
    ├─ Synthesizes final report
    └─→ output/pr-1234/final-report.md
    ↓
[Orchestrator] Presents final report to user
```

## Components

- **Orchestrator:** `.claude/commands/analyze-pr.md` - Main command
- **Risk Analyzer:** `.claude/agents/risk-analyzer.md` - Change risk & test recommendations
- **Quality Gate:** `.claude/agents/critic-agent.md` - Validates findings

## Workflow

1. User invokes `/analyze-pr {PR_NUMBER}`
2. Orchestrator creates `output/pr-{NUMBER}/` directory
3. Orchestrator invokes risk-analyzer agent
4. Risk analyzer outputs JSON to `output/pr-{NUMBER}/risk-analysis.json`
5. Critic agent validates findings, filters false positives
6. Critic synthesizes final report as Markdown
7. Orchestrator presents report to user

## Analysis Focus

### Change Risk & Test Recommendations
- Detects new failure modes (missing circuit breakers, timeouts, retries)
- Identifies breaking API changes (removed fields, changed signatures)
- Recommends test strategies (integration, contract, negative tests)
- Validates scope (features applying to wrong user segments)
- Handles Java, Node.js, React, Android

### Quality Gate
- Validates finding quality (file:line references, actionable recommendations)
- Filters false positives (findings from unchanged files)
- Synthesizes final report with merge decision

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
- Critic agent validates findings before presentation
- Filters false positives
- Ensures actionable recommendations
- One of Andrew Ng's 4 fundamental agentic patterns

## Output Structure

```
output/
└── pr-1234/
    ├── risk-analysis.json       # Change risk findings
    ├── final-report.md          # Synthesized report from critic
    └── metadata.json            # Analysis metadata
```

## Extension Points

To add more analysis types (observability, configuration):
- Create new agent in `.claude/agents/`
- Update orchestrator to invoke new agent
- Update critic-agent.md to validate new findings
- Agents automatically loaded by Claude Agent SDK

## Quality Gates

- Every finding has file:line reference
- Recommendations are specific and actionable
- Severity levels justified by impact
- Test recommendations provided
- Structured JSON + Markdown output

## Current Implementation

✅ Working `/analyze-pr` command
✅ Risk analyzer agent (change risk & test recommendations)
✅ Critic quality gate
✅ Artifact-based workflow
✅ 2-agent architecture (risk-analyzer + critic)

## Future Enhancements

⏳ Add observability-reviewer agent (Use Case 2)
⏳ Add config-reviewer agent (Use Case 3)
⏳ GitHub/GitLab API integration (fetch PR diffs automatically)
⏳ Post findings as PR comments
⏳ Knowledge base / RAG for deeper pattern matching
⏳ Python automation script for CI/CD
⏳ Slack/email notifications
