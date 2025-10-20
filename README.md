# Resilience Agent

AI-powered Pull Request analysis system that detects production resilience risks including missing circuit breakers, timeout configurations, breaking API changes, and other failure modes that could cause production outages.

## Quick Start

```bash
# 1. Clone this repository
git clone <repo-url>
cd reselience-agent-prototype

# 2. Clone target repository to analyze
cd ..
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git

# 3. Start Claude Code in the resilience agent directory
cd reselience-agent-prototype

# 4. Run analysis
/analyze-pr microservices-demo 2876
```

**That's it!** Results will be in `output/pr-2876/`

For detailed setup instructions, see [Getting Started Guide](docs/GETTING-STARTED.md)

---

## What Gets Analyzed

The Resilience Agent detects production risks across multiple languages (Java, Go, Node.js, Python):

**New Failure Modes:**
- External API calls without circuit breakers
- Async operations without timeouts
- Database queries without resilience patterns
- Missing retry logic with exponential backoff

**Breaking API Changes:**
- Removed or renamed fields in responses
- Changed endpoint paths
- New required parameters
- Modified error response formats

**Git-Enhanced Risk Scoring:**
- Code hotspots (high churn files)
- Files with rollback history
- Authorship concentration risks

**Test Recommendations:**
- Integration tests for failure scenarios
- Contract tests for API changes
- Negative tests for scope validation
- Chaos tests for resilience verification

---

## Example Output

After running `/analyze-pr microservices-demo 2876`, you'll get:

```
output/pr-2876/
├── metadata.json          # PR context and timestamps
├── pr.diff                # The diff that was analyzed
├── risk-analysis.json     # Detailed findings with git metrics
└── final-report.md        # Executive summary with merge recommendation
```

**Sample Finding:**

```json
{
  "type": "new_failure_mode",
  "severity": "HIGH",
  "file": "src/services/OrderService.java",
  "line": 45,
  "pattern": "RestClient call without circuit breaker",
  "impact": "If payment service fails, cascading failures will affect all order processing",
  "recommendation": "Add @CircuitBreaker(name=\"paymentService\", fallbackMethod=\"paymentFallback\")",
  "test_needed": "Integration test simulating payment service timeout",
  "git_metrics": {
    "commits_last_month": 18,
    "rollback_history": true
  },
  "risk_adjustment": "+25 (hotspot + rollback history)"
}
```

---

## Architecture

The system uses a layered architecture with automatic skill discovery:

```
User: /analyze-pr microservices-demo 2876
         |
         v
[Command: analyze-pr.md]
    - Fetches PR from GitHub
    - Generates diff
    - Launches subagents
         |
         v
[Subagent: risk-analyzer]
    - Analyzes code changes
    - Auto-discovers git-risk-analysis skill
    - Detects resilience patterns
    - Outputs risk-analysis.json
         |
         v
[Subagent: critic-agent]
    - Validates findings
    - Filters false positives
    - Generates final-report.md
         |
         v
User: Reviews output/pr-2876/
```

**Key Components:**
- **Commands** - User-facing orchestration (`/analyze-pr`)
- **Subagents** - Specialized analysts (risk-analyzer, critic-agent)
- **Skills** - Auto-discovered capabilities (git-risk-analysis)

For architectural details, see [Architecture Guide](docs/ARCHITECTURE.md)

---

## Command Reference

### Analyze Pull Request

```bash
/analyze-pr <repo_name> <pr_number>
```

**Arguments:**
- `repo_name` - Repository directory name (e.g., "microservices-demo")
- `pr_number` - GitHub PR number (e.g., "2876")

**Example:**
```bash
/analyze-pr microservices-demo 2876
```

**What Happens:**
1. Navigates to repository directory
2. Fetches PR from GitHub origin
3. Generates diff between base branch and PR
4. Runs risk-analyzer with auto-discovered git skill
5. Validates findings with critic-agent
6. Outputs results to `output/pr-<number>/`

---

## Detection Examples

The agent learns from real-world patterns:

**Java (Spring Boot + Resilience4j):**
- Missing `@CircuitBreaker` on external API calls
- `@Async` methods without timeout configuration
- `@Retry` without `@CircuitBreaker` (retry storm anti-pattern)

**Node.js:**
- `axios`/`fetch` calls without timeout
- Promises without `.catch()` handlers
- Missing exponential backoff in retries

**All Languages:**
- Database queries without timeouts
- Message consumers without error handlers
- Breaking changes to REST/GraphQL APIs

For detailed examples, see `examples/change-risk/java-resilience4j/`

---

## Severity Levels

**CRITICAL (Production Outage Risk)**
- User-facing breaking changes
- Retry storms (retries without circuit breakers)
- Files with rollback history

**HIGH (Service Degradation)**
- Missing circuit breakers on external APIs
- Missing timeout configurations
- Code hotspots (high churn files)

**MEDIUM (Edge Case Failures)**
- Missing error handlers
- Coordination risks (5+ authors)

**LOW (Best Practice Improvements)**
- Minor code quality issues

---

## Merge Recommendations

Based on severity of findings:

**REQUEST_CHANGES**
- CRITICAL findings present
- Production outage risk
- Breaking changes without migration

**APPROVE_WITH_TESTS**
- HIGH findings requiring test coverage
- Missing resilience patterns
- Test recommendations provided

**APPROVE**
- Only LOW/MEDIUM findings
- No production risk
- Improvements can be post-merge

---

## Project Structure

```
reselience-agent-prototype/
├── .claude/
│   ├── commands/
│   │   └── analyze-pr.md           # Orchestrator (user-facing)
│   ├── agents/
│   │   ├── risk-analyzer.md        # Resilience risk detection
│   │   └── critic-agent.md         # Quality validation
│   └── skills/
│       └── git-risk-analysis/
│           └── SKILL.md            # Auto-discovered git analysis
├── examples/
│   └── change-risk/
│       └── java-resilience4j/      # Detection pattern examples
│           ├── missing-circuit-breaker.md
│           ├── missing-timeout.md
│           └── retry-without-circuit.md
├── output/                         # Analysis results (gitignored)
│   └── pr-<NUMBER>/
│       ├── metadata.json
│       ├── pr.diff
│       ├── risk-analysis.json
│       └── final-report.md
├── docs/
│   ├── ARCHITECTURE.md             # System architecture deep dive
│   └── GETTING-STARTED.md          # Step-by-step tutorial
└── README.md                       # This file
```

---

## Key Features

**Polyglot Analysis:**
- Single agent analyzes Java, Go, Node.js, Python, React
- Detects cross-language resilience issues
- No per-language agent needed

**Git-Enhanced Risk Scoring:**
- Code churn analysis (hotspot detection)
- Rollback history correlation
- Authorship concentration patterns
- 20-30% more accurate risk predictions

**Auto-Discovered Skills:**
- Skills loaded only when needed (progressive disclosure)
- No explicit skill references required
- Composable and reusable capabilities

**Agent-First Design:**
- High-level goals, not step-by-step scripts
- Agents autonomously decide how to accomplish tasks
- Flexible and adaptable to edge cases

**Quality Gate Pattern:**
- All findings validated by critic-agent
- False positives filtered automatically
- Only actionable recommendations reported

---

## Modern Patterns Detected (2025)

The agent focuses on current production standards:

**Java:**
- RestClient (Spring Boot 3+) - NOT deprecated RestTemplate
- Resilience4j - NOT Netflix Hystrix
- @CircuitBreaker + @Retry + @TimeLimiter layered pattern

**Node.js:**
- opossum (circuit breaker)
- axios-retry with exponential backoff
- AbortController for timeouts

**Anti-Patterns Flagged:**
- Retries without circuit breakers (retry storms)
- Unbounded thread pools
- Missing timeout configurations

---

## Documentation

- **[Getting Started](docs/GETTING-STARTED.md)** - Step-by-step tutorial
- **[Architecture](docs/ARCHITECTURE.md)** - System design and component interaction
- **Examples** - Detection pattern examples in `examples/change-risk/`

---

## Extending the System

### Add a New Skill

```bash
# 1. Create skill definition
.claude/skills/new-skill/SKILL.md

# 2. Write clear description with trigger keywords
---
name: new-skill
description: Use when analyzing <specific context>
---

# 3. Document step-by-step instructions
```

Skills are **automatically discovered** - no need to update agent prompts!

### Add a New Subagent

```bash
# 1. Create agent definition
.claude/agents/new-agent.md

# 2. Define detection patterns and output format

# 3. Update orchestrator to invoke new agent
.claude/commands/analyze-pr.md
```

### Add Detection Patterns

Update existing subagent with new patterns:
```bash
.claude/agents/risk-analyzer.md
```

Add example to help agent learn:
```bash
examples/change-risk/<category>/<pattern>.md
```

---

## Prerequisites

- **Claude Code** installed and configured
- **Git** for repository operations
- Access to GitHub repositories with Pull Requests

No Python, no API keys, no additional dependencies required for Claude Code usage.

---

## Troubleshooting

**Repository not found:**
- Ensure repository is cloned at same level as resilience-agent-prototype
- Check directory structure: `../microservices-demo/`

**PR not found:**
- Verify PR exists on GitHub
- Check network access to fetch from origin

**Empty diff:**
- Ensure PR branch is ahead of base branch
- Verify base branch detection (main vs master)

For detailed troubleshooting, see [Getting Started Guide](docs/GETTING-STARTED.md)

---

## Contributing

Contributions welcome! Areas for improvement:

- Additional detection patterns (security, performance)
- Language-specific examples (Go, Python, Rust)
- Enhanced git analysis metrics
- Integration with CI/CD pipelines

---

## License

MIT License
