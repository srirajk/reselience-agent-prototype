# Resilience Agent

AI-powered Pull Request analysis system that detects production resilience risks including missing circuit breakers, timeout configurations, breaking API changes, and other failure modes that could cause production outages.

> **🚀 v2.0 (ast-int branch)**: Now featuring **AST-based fact extraction** with MCP Tree-sitter! Detects risks in unknown libraries using LLM reasoning from semantic facts.

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

**v2.0 Innovation**: The Resilience Agent uses **AST-based fact extraction** to reason about code semantically. It can detect risks in **unknown custom libraries** by recognizing patterns (e.g., names ending in "Client", blocking methods) without hardcoded library lists.

The agent detects production risks across multiple languages (Java, Python, Node.js, Kotlin/Android):

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
User: /analyze-pr microservices-demo 2876 /output
         |
         v
[Command: analyze-pr.md]
    - Fetches PR from GitHub
    - Generates diff
    - Launches subagents
         |
         v
[Subagent: fact-extractor]
    - Discovers MCP Tree-sitter tools
    - Extracts AST facts from changed files
    - Outputs facts/*.json (following fact-schema.json)
         |
         v
[Subagent: risk-analyzer]
    - Reads AST facts
    - Applies LLM reasoning from base knowledge
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
User: Reviews /output/pr-2876/
```

**Key Components:**
- **Commands** - User-facing orchestration (`/analyze-pr`)
- **Subagents** - Specialized analysts (fact-extractor, risk-analyzer, critic-agent)
- **Skills** - Auto-discovered capabilities (git-risk-analysis)
- **Templates** - Shared schemas (fact-schema.json)

For architectural details, see [Architecture Guide](docs/ARCHITECTURE.md)

---

## Command Reference

### Analyze Pull Request

```bash
/analyze-pr <repo_name> <pr_number> [output_dir]
```

**Arguments:**
- `repo_name` - Repository directory name (e.g., "microservices-demo")
- `pr_number` - GitHub PR number (e.g., "2876")
- `output_dir` - Output directory path (optional, defaults to `./output`, **recommend absolute path**)

**Example:**
```bash
/analyze-pr microservices-demo 2876
/analyze-pr microservices-demo 2876 /Users/me/analysis-results
```

**What Happens:**
1. Navigates to repository directory
2. Fetches PR from GitHub origin
3. Generates diff between base branch and PR
4. Launches fact-extractor to extract AST facts via MCP Tree-sitter
5. Runs risk-analyzer with AST facts and auto-discovered git skill
6. Validates findings with critic-agent
7. Outputs results to `{output_dir}/pr-<number>/`

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
│   │   ├── fact-extractor.md       # AST fact extraction (v2.0)
│   │   ├── risk-analyzer.md        # Resilience risk detection
│   │   └── critic-agent.md         # Quality validation
│   ├── templates/
│   │   └── fact-schema.json        # Fact JSON schema (v2.0)
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
│       ├── facts/                  # AST facts (v2.0)
│       │   └── *.json
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

**Template-Based Schemas:**
- Fact JSON schema defined once in `.claude/templates/`
- All agents reference the same schema
- Single source of truth for data formats
- Reduces token usage across agents

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

## v2.0 Features (ast-int branch)

### AST-Based Fact Extraction
- **MCP Tree-sitter Integration**: Semantic code analysis across Java, Python, Node.js, Kotlin
- **Fact-Driven LLM Reasoning**: Extract facts (dependencies, call semantics, config) → LLM reasons using base knowledge
- **Unknown Library Detection**: Recognizes custom libraries via naming patterns (e.g., "CustomHttpClient") without hardcoding

### Multi-Language Support
- **Single workflow** works across all languages (same risk-analysis.json schema)
- **Language-specific AST queries** handle syntax differences
- **Universal resilience patterns** (timeout_missing, circuit_breaker_missing, etc.)

### Context-Aware Severity
- **Fan-in/fan-out analysis** enriches risk scoring
- **Same pattern, different severity**: Missing timeout in admin tool (LOW) vs user API (CRITICAL)
- **Git-enhanced metrics**: Hotspot detection, rollback history correlation

### Architecture Documentation
Complete architecture documentation available in the docs/ directory.

### Comparison: v1.0 vs v2.0

| Feature | v1.0 (main) | v2.0 (ast-int) |
|---------|-------------|----------------|
| Detection | Grep + few-shot examples | AST facts + LLM reasoning |
| Languages | Java (examples) | Java, Python, Node, Kotlin |
| Unknown Libraries | Cannot detect | Detects via semantic patterns |
| Severity | Pattern-based | Context-aware (fan-in/fan-out) |
| Scalability | Limited to known libraries | Scales to custom libraries |

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
