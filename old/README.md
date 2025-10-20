# Resilience Agent

AI-powered Pull Request analysis for production readiness across 3 use cases.

## Quick Start

### Prerequisites
- Python 3.10+
- Anthropic API key
- Git repository cloned in `workspace/`

### Installation

1. Clone this repository
```bash
git clone <repo-url>
cd resilience-agent
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Set up environment
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

4. Clone target repository for analysis
```bash
cd workspace/
git clone https://github.com/your-org/your-repo.git
cd your-repo
# Checkout PR branch or create test PR
```

### Usage (Claude Code)

Open this project in Claude Code and run:

```
/analyze-pr 1234
```

The agent will:
1. Analyze PR #1234 for production risks
2. Check observability completeness
3. Validate production configuration
4. Filter false positives via critic agent
5. Generate comprehensive report in `output/pr-1234/`

### Usage (Python SDK)

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        setting_sources=["project"],
        agents_dir=".claude/agents"
    )

    async with ClaudeSDKClient(options=options) as client:
        result = await client.query("/analyze-pr 1234")
        print(result)
```

## What It Checks

### Use Case 1: Change Risk & Test Recommendations
- **New Failure Modes:** Missing circuit breakers, timeouts, retries
- **Breaking API Changes:** Removed fields, changed signatures
- **Test Strategy:** Integration tests, contract tests, negative tests
- **Scope Validation:** Features applying to wrong user segments

### Use Case 2: Observability Review
- **Error Logging:** Structured logging, correlation IDs, no PII
- **Metrics:** Performance tracking, business metrics, SLI/SLO
- **Distributed Tracing:** Trace propagation across services
- **Monitoring & Alerts:** Health checks, anomaly detection

### Use Case 3: Production Configuration Review
- **Configuration Changes:** New values, changed settings
- **Missing Config:** Values in dev/staging but not prod
- **Invalid Config:** Pool sizes, timeouts, placeholder values
- **Security:** Hardcoded secrets detection

## Architecture

```
/analyze-pr 1234
     ↓
[Orchestrator]
     ├─→ Risk Analyzer (Use Case 1)
     ├─→ Observability Reviewer (Use Case 2)
     ├─→ Config Reviewer (Use Case 3)
     ↓
[Critic Agent - Quality Gate]
     ├─ Validates findings
     ├─ Filters false positives
     ├─ Resolves contradictions
     └─→ Final Report
```

## Output Structure

```
output/
└── pr-1234/
    ├── risk-analysis.json              # Use Case 1 findings
    ├── observability-analysis.json     # Use Case 2 findings
    ├── config-analysis.json            # Use Case 3 findings
    ├── final-report.md                 # Synthesized report
    └── metadata.json                   # Analysis metadata
```

## Key Features

**Function-Based Architecture:**
- ONE agent handles ALL languages (Java, Node.js, React, Android)
- 4× more efficient than language-specific agents
- Catches cross-language issues

**High-Level Instructions:**
- Agents told WHAT to find, not HOW
- Claude uses tools intelligently
- More flexible and adaptable

**Quality Gate Pattern:**
- Critic agent validates all findings
- Filters false positives
- Ensures actionable recommendations

**Artifact-Based Workflow:**
- Persistent JSON outputs
- Audit trail for all analyses
- Easy debugging and review

## Merge Decision Criteria

### 🔴 REQUEST_CHANGES
- CRITICAL findings (production outage risk)
- Breaking changes without migration
- Security vulnerabilities

### 🟡 APPROVE_WITH_TESTS
- HIGH findings mitigatable with tests
- Missing observability
- Configuration validation needed

### 🟢 APPROVE
- Only LOW/MEDIUM findings
- Improvements can be post-merge
- No production risk

## Project Structure

```
.claude/
├── commands/
│   └── analyze-pr.md          # Orchestrator
└── agents/
    ├── risk-analyzer.md        # Use Case 1
    ├── observability-reviewer.md  # Use Case 2
    ├── config-reviewer.md      # Use Case 3
    └── critic-agent.md         # Quality Gate

workspace/                      # Cloned repos (gitignored)
output/                         # Analysis results (gitignored)
examples/                       # Few-shot examples
```

## Extending the Agent

### Add New Use Case

1. Create agent: `.claude/agents/new-use-case.md`
2. Update orchestrator in `.claude/commands/analyze-pr.md`
3. Add critic validation for new findings

### Add Language Support

Agents already handle Java, Node.js, React, Android. To add more:
- Update detection patterns in existing agents
- No new agents needed (function-based design)

## Demo Setup

```bash
# 1. Clone target repo
cd workspace/
git clone https://github.com/your-org/repo.git
cd repo

# 2. Create test PR with failure modes
git checkout -b test-pr
# Add @FeignClient without @CircuitBreaker
# Remove field from API response
# Add config without production value
git commit -am "Test PR with issues"

# 3. Analyze
/analyze-pr test-pr

# 4. Review output
cat output/pr-test-pr/final-report.md
```

## License

MIT License
