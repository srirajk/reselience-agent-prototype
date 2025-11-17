# Resilience Agent - Sub-Agent Walkthrough

## High-Level Flow

```
User: /analyze-pr 1234
    ↓
Orchestrator Agent → Launches Sub-Agents → Critic Agent → Final Report
```

---

## Sub-Agent Breakdown

### 1. **Orchestrator Agent** (.claude/commands/analyze-pr.md)
**One-liner:** Entry point that coordinates all sub-agents and manages the end-to-end workflow.

**What it does:**
- Fetches PR diff from Git
- Creates output directory: `output/pr-{NUMBER}/`
- Launches sub-agents in sequence
- Presents final report to user

**Input:** PR number
**Output:** Orchestrates the entire analysis

---

### 2. **AST Fact Extraction Agent** (.claude/agents/fact-extractor.md)
**One-liner:** Extracts structured semantic facts from code using Tree-sitter AST parsing.

**What it does:**
- Parses changed files via Tree-sitter MCP Server
- Extracts functions, classes, imports, API calls
- Detects patterns: circuit breakers, timeouts, retries, auth checks
- Outputs structured JSON with code metadata

**Input:** PR changed files
**Output:** `fact-tree.json` - Structured semantic facts

**Example fact:**
```json
{
  "function": "processPayment",
  "has_timeout": false,
  "calls_external_api": true,
  "has_error_handling": false
}
```

---

### 3. **Change Risk Analysis Agent** (.claude/agents/risk-analyzer.md)
**One-liner:** Analyzes PR changes for production risks and recommends test strategies.

**What it does:**
- Reads `fact-tree.json` + PR diff
- Detects failure modes: missing circuit breakers, timeouts, retries
- Identifies breaking API changes: removed fields, signature changes
- Assesses severity: Critical, High, Medium, Low
- Recommends specific test strategies

**Input:** `fact-tree.json` + `pr.diff`
**Output:** `risk-analysis.json` - Risk findings with file:line references

**Example finding:**
```json
{
  "severity": "High",
  "type": "Missing Timeout",
  "file": "src/payment.py",
  "line": 45,
  "description": "Function processPayment calls external API without timeout",
  "recommendation": "Add timeout of 5s, implement retry with exponential backoff"
}
```

---

### 4. **Observability Reviewer Agent** (.claude/agents/observability-reviewer.md) 🔄 FUTURE
**One-liner:** Validates observability completeness - logging, metrics, tracing, alerts.

**What it does:**
- Checks for log statements (info, warn, error levels)
- Validates metrics instrumentation
- Verifies distributed tracing context propagation
- Ensures alert/monitoring coverage

**Input:** `fact-tree.json` + `pr.diff`
**Output:** `observability-report.json` - Observability gaps

---

### 5. **Configuration Reviewer Agent** (.claude/agents/config-reviewer.md) 🔄 FUTURE
**One-liner:** Validates production configuration safety - secrets, limits, feature flags.

**What it does:**
- Validates credential/secret handling
- Checks resource limits (memory, CPU, connections)
- Verifies environment-specific configuration
- Reviews feature flag settings

**Input:** Configuration changes + values
**Output:** `config-report.json` - Config safety issues

---

### 6. **Quality Gate & Synthesis Agent** (.claude/agents/critic-agent.md)
**One-liner:** Validates all findings, filters false positives, synthesizes final report.

**What it does:**
- Reads all sub-agent JSON outputs
- Verifies file:line references exist in PR diff
- Filters findings from unchanged files
- Removes duplicates and contradictions
- Validates severity justifications
- Synthesizes executive summary with merge decision

**Input:** All sub-agent JSON outputs (risk-analysis.json, etc.)
**Output:** `final-report.md` - Validated synthesis with merge decision

**Example output:**
```markdown
## Executive Summary
⚠️ Merge with Improvements

## Critical Findings
1. [High] Missing timeout in payment API call (src/payment.py:45)

## Recommended Tests
- Integration test: Payment timeout handling
- Contract test: Payment API schema validation

## Merge Decision: Merge with Improvements (Confidence: 85%)
```

---

## Complete Workflow Example

```
User: /analyze-pr 1234
    ↓
Orchestrator: Fetch PR diff from Git
    ↓
Fact Extractor: Parse files → fact-tree.json
    ↓
Risk Analyzer: Analyze risks → risk-analysis.json
    ↓
Critic Agent: Validate findings → final-report.md
    ↓
User: Receives final report
```

---

## Key Design Principles

### 1. **Artifact-Based Communication**
Sub-agents write JSON outputs to `output/pr-{NUMBER}/` directory. This eliminates "game of telephone" between agents.

### 2. **Function-Based (Not Language-Based)**
One risk-analyzer handles Java, Python, JS, Go, Rust - enables cross-language flow analysis.

### 3. **Quality Gate Pattern**
Critic agent validates ALL findings before user sees them - filters false positives, ensures actionable recommendations.

### 4. **Declarative Instructions**
Agents told WHAT to find (missing timeouts), not HOW to find it (Claude chooses tools: Grep, AST, Read).

---

## Agent Status

| Agent | Status | Output |
|-------|--------|--------|
| Orchestrator | 🔄 IN PROGRESS | Coordinates workflow |
| Fact Extractor | 🔄 IN PROGRESS | fact-tree.json |
| Risk Analyzer | 🔄 IN PROGRESS | risk-analysis.json |
| Observability Reviewer | 🔄 FUTURE | observability-report.json |
| Config Reviewer | 🔄 FUTURE | config-report.json |
| Critic Agent | 🔄 IN PROGRESS | final-report.md |

---

## MCP Server Integration

### Tree-sitter MCP Server
**What it does:** Provides AST parsing across multiple languages (Java, Python, JS/TS, Kotlin, Go, Rust)

**How agents use it:**
- Fact Extractor: "Parse this file and give me structured facts about functions, classes, imports"
- Returns JSON with semantic information (not just raw AST)

**Example request:**
```
Agent → MCP: "Parse src/payment.py and extract all functions with their error handling status"
MCP → Agent: { "functions": [{"name": "processPayment", "has_error_handling": false, ...}] }
```

### Knowledge Base MCP Server (Future)
**What it does:** Pattern matching database with historical failure modes and best practices

**How agents use it:**
- Risk Analyzer: "Is missing timeout a known failure pattern?"
- Critic Agent: "Validate this finding against known rules"

---

## Output Structure

```
output/
└── pr-1234/
    ├── pr.diff                  # PR diff from Git
    ├── fact-tree.json           # Semantic facts from AST
    ├── risk-analysis.json       # Risk findings
    ├── final-report.md          # Validated synthesis
    └── metadata.json            # Analysis metadata
```
