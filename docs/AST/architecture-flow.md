# AST-Based Analysis Architecture Flow

## Overview

The Resilience Agent uses a **multi-agent architecture** with specialized sub-agents that work together to analyze Pull Requests for production risks. This document explains the complete flow from user request to final report.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                            USER                                      │
│                    /analyze-pr <repo> <pr_number>                    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                    │
│              (.claude/commands/analyze-pr.md)                        │
│                                                                       │
│  Responsibilities:                                                   │
│  • Fetch PR from GitHub (git fetch origin pull/X/head:pr-X)        │
│  • Generate diff between base and PR branch                         │
│  • Create output directory structure                                │
│  • Launch specialized sub-agents via Task tool                      │
│  • Present final report to user                                     │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         │
┌─────────────────────────────────────┐      │
│   PHASE 1: AST FACT EXTRACTION      │      │
│   Sub-Agent: fact-extractor         │      │
│   (.claude/agents/fact-extractor.md)│      │
│                                      │      │
│   Specialist Role:                  │      │
│   🌳 AST Parsing Expert             │      │
│   • Tree-sitter MCP tool master     │      │
│   • Semantic code analysis          │      │
│   • Multi-language support          │      │
│                                      │      │
│   What it does:                     │      │
│   1. Discover & verify Tree-sitter  │      │
│      MCP tools                      │      │
│   2. Register repository as project │      │
│   3. Parse PR diff to find changed  │      │
│      source files                   │      │
│   4. Extract AST facts from EVERY   │      │
│      changed file (Step 1.5 rule)   │      │
│   5. Detect async patterns          │      │
│      (RabbitMQ, Kafka, HTTP, gRPC)  │      │
│   6. Identify breaking API changes  │      │
│                                      │      │
│   Tools Used:                       │      │
│   • mcp__tree_sitter__register_     │      │
│     project_tool                    │      │
│   • mcp__tree_sitter__get_symbols   │      │
│   • mcp__tree_sitter__get_          │      │
│     dependencies                    │      │
│   • mcp__tree_sitter__run_query     │      │
│   • Read, Write, Bash               │      │
│                                      │      │
│   Output: facts/*.json              │      │
│   Schema: .claude/templates/        │      │
│           fact-schema.json          │      │
└──────────────┬──────────────────────┘      │
               │                              │
               │ facts/*.json                 │
               │                              │
               ▼                              │
┌─────────────────────────────────────┐      │
│   PHASE 2: CHANGE RISK ANALYSIS     │      │
│   Sub-Agent: risk-analyzer          │      │
│   (.claude/agents/risk-analyzer.md) │      │
│                                      │      │
│   Specialist Role:                  │      │
│   🛡️ Resilience Pattern Expert      │      │
│   • Failure mode detection          │      │
│   • Blast radius analysis           │      │
│   • Unknown library reasoning       │      │
│                                      │      │
│   What it does:                     │      │
│   1. Load AST fact files            │      │
│   2. Apply LLM reasoning to facts:  │      │
│      • HTTP/RPC calls without       │      │
│        timeouts                     │      │
│      • Missing circuit breakers     │      │
│      • Blocking calls in async      │      │
│        contexts                     │      │
│      • Breaking API changes         │      │
│      • Unknown custom libraries     │      │
│        (via semantic patterns)      │      │
│   3. Fan-in/fan-out analysis:       │      │
│      • Count callers of changed     │      │
│        methods                      │      │
│      • Identify external service    │      │
│        dependencies                 │      │
│      • Determine user-facing paths  │      │
│   4. Contextualize severity:        │      │
│      • High fan-in + missing        │      │
│        timeout → upgrade severity   │      │
│      • User-facing endpoint →       │      │
│        upgrade severity             │      │
│   5. Use Git Risk Analysis skill    │      │
│      for code churn metrics         │      │
│   6. Recommend specific tests       │      │
│                                      │      │
│   Model: claude-opus (complex       │      │
│          reasoning required)        │      │
│                                      │      │
│   Output: risk-analysis.json        │      │
└──────────────┬──────────────────────┘      │
               │                              │
               │ risk-analysis.json           │
               │                              │
               ▼                              │
┌─────────────────────────────────────┐      │
│   PHASE 3: QUALITY GATE             │      │
│   Sub-Agent: critic-agent           │      │
│   (.claude/agents/critic-agent.md)  │      │
│                                      │      │
│   Specialist Role:                  │      │
│   ✅ Quality Validation Expert      │      │
│   • Meta-reasoning about findings   │      │
│   • False positive filtering        │      │
│   • User-facing communication       │      │
│                                      │      │
│   What it does:                     │      │
│   1. Validate finding quality:      │      │
│      • All findings have file:line  │      │
│        references                   │      │
│      • Recommendations are          │      │
│        actionable                   │      │
│      • Severity levels justified    │      │
│      • No findings from unchanged   │      │
│        files                        │      │
│   2. Filter false positives         │      │
│   3. Synthesize final report:       │      │
│      • Executive summary            │      │
│      • Critical findings grouped    │      │
│      • Test recommendations         │      │
│      • Merge recommendation:        │      │
│        APPROVE / REQUEST_CHANGES    │      │
│                                      │      │
│   Output: final-report.md           │      │
└──────────────┬──────────────────────┘      │
               │                              │
               │ final-report.md              │
               │                              │
               └──────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR                                    │
│              (reads and displays final report)                       │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                            USER                                      │
│                    (receives final report)                           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Sub-Agent Specializations

### Why 3 Specialists > 1 Generalist?

The architecture uses **separation of concerns** - each agent is an expert in its domain:

| Agent | Specialization | Key Strength | When It Runs |
|-------|----------------|--------------|--------------|
| **fact-extractor** | AST Parsing | Semantic code understanding via Tree-sitter | Phase 1 (after PR fetch) |
| **risk-analyzer** | Resilience Patterns | Deep knowledge of failure modes, blast radius reasoning | Phase 2 (after facts extracted) |
| **critic** | Quality Validation | Meta-reasoning, false positive filtering, synthesis | Phase 3 (after risk analysis) |

---

### 1. Fact-Extractor: The AST Parsing Specialist

**Role:** Extract semantic facts from code using Abstract Syntax Tree (AST) analysis.

**Expertise:**
- **Tree-sitter MCP Integration:** Direct access to tree-sitter AST parsers via MCP protocol
- **Multi-language Support:** Java, Python, TypeScript, Kotlin, Go, Rust, C++
- **Semantic Analysis:** Understands code structure, not just text patterns
- **Pattern Recognition:** Detects async communication patterns (RabbitMQ, Kafka, HTTP, gRPC)

**Why Specialist:**
- Requires deep understanding of AST node types and query syntax
- Needs to handle language-specific parsing nuances
- Must follow strict fact schema (v2.0) for downstream reasoning
- Critical Step 1.5 rule: Extract facts for ALL changed files (no filtering)

**Tools:**
- `mcp__tree_sitter__register_project_tool` - Register repo with Tree-sitter
- `mcp__tree_sitter__get_symbols` - Extract classes, methods, interfaces
- `mcp__tree_sitter__get_dependencies` - Find imports and external dependencies
- `mcp__tree_sitter__run_query` - Run custom AST queries
- `Read`, `Write`, `Bash` - File operations

**Output Format:** JSON fact files following `.claude/templates/fact-schema.json`

---

### 2. Risk-Analyzer: The Resilience Pattern Specialist

**Role:** Reason about extracted facts to detect failure modes and production risks.

**Expertise:**
- **Resilience Patterns:** Circuit breakers, timeouts, retries, bulkheads, fallbacks
- **Semantic Pattern Matching:** Recognize HTTP clients by naming patterns (`*Client`, `*Stub`) + method semantics
- **Blast Radius Analysis:** Fan-in/fan-out analysis to assess change impact
- **Unknown Library Reasoning:** Detect risks in custom/internal libraries never seen before
- **Severity Contextualization:** Adjust severity based on user-facing paths and traffic patterns

**Why Specialist:**
- Requires complex reasoning about code behavior (uses Opus model)
- Must correlate facts across multiple files
- Needs deep knowledge of production failure modes
- Performs graph analysis (caller/callee relationships)

**Key Innovation:** Pattern-based detection works on ANY library (not hardcoded lists):

```json
// Example: Unknown library detection
{
  "receiver_type": "InternalLegacyServiceClient",  // Never seen before!
  "method": "fetchData",
  "is_blocking": true,
  "has_timeout": false,
  "category": "http"  // AST-determined category
}
```

**Reasoning:** "Ends with 'Client' + fetchData method + blocking + no timeout + HTTP category = HTTP client without resilience (HIGH severity)"

**Tools:**
- `Read` - Load fact files from Phase 1
- `mcp__tree_sitter__find_usage` - Fan-in analysis (who calls this?)
- `Grep` - Context enrichment (find configuration)
- `Skill(git-risk-analysis)` - Git history analysis for code churn
- `Write` - Output risk-analysis.json

**Output Format:** JSON with failure modes, breaking changes, test recommendations

---

### 3. Critic: The Quality Gate Specialist

**Role:** Validate findings and synthesize user-facing final report.

**Expertise:**
- **Meta-Reasoning:** Reason about the quality of other agent's findings
- **False Positive Filtering:** Remove findings from unchanged files or low-confidence detections
- **Synthesis Skills:** Convert technical findings into executive-friendly summaries
- **Quality Validation:** Ensure all findings have file:line references and actionable recommendations

**Why Specialist:**
- Implements one of Andrew Ng's 4 fundamental agentic patterns (Quality Gate)
- Requires different skill set than technical analysis
- Must balance technical accuracy with readability
- Acts as final checkpoint before user sees results

**Validation Checks:**
- ✅ All findings reference specific file:line locations
- ✅ Recommendations are specific and actionable
- ✅ Severity levels are justified by impact
- ✅ No false positives (findings in unchanged files)
- ✅ Test recommendations are concrete

**Tools:**
- `Read` - Load risk-analysis.json
- `Write` - Output final-report.md
- `Grep`, `Read` - Verify file references are valid

**Output Format:** Markdown report with executive summary and merge recommendation

---

## Data Flow & Artifacts

```
User Input
   ↓
┌─────────────────────────┐
│  output/pr-{NUMBER}/    │
│  ├── metadata.json      │  ← Phase 1: Orchestrator
│  ├── pr.diff            │  ← Phase 1: Orchestrator
│  ├── facts/             │  ← Phase 2a: Fact-Extractor
│  │   ├── File1.java.json
│  │   ├── File2.java.json
│  │   └── ...
│  ├── risk-analysis.json │  ← Phase 2b: Risk-Analyzer
│  └── final-report.md    │  ← Phase 3: Critic
└─────────────────────────┘
```

### Artifact Descriptions

**metadata.json** - PR context (repository, PR number, base branch)

**pr.diff** - Git diff between base branch and PR branch

**facts/*.json** - One JSON file per changed source file, containing:
- Dependencies (imports, external libraries)
- Method calls with resilience metadata (has_timeout, has_circuit_breaker, etc.)
- Async communication patterns (RabbitMQ, Kafka, HTTP)
- Message schema changes (field additions/removals)
- Public API changes (breaking changes)
- Configuration changes

**risk-analysis.json** - Structured findings:
- Failure modes (new risks introduced by PR)
- Breaking API changes
- Blast radius analysis
- Test recommendations
- Resiliency gaps

**final-report.md** - User-facing Markdown report with executive summary and merge recommendation

---

## MCP Tree-sitter Integration

### What is MCP (Model Context Protocol)?

MCP is a protocol for connecting Claude Code to external tools and servers. The Tree-sitter MCP server provides AST parsing capabilities.

### Configuration

**File:** `.mcp.json` (project root)

```json
{
  "mcpServers": {
    "tree_sitter": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/mcp-server-tree-sitter",
        "run",
        "-m",
        "mcp_server_tree_sitter.server"
      ],
      "description": "Tree-sitter AST parser for multi-language code analysis"
    }
  }
}
```

**File:** `.claude/settings.local.json`

```json
{
  "permissions": {
    "allowedMcpTools": [
      "mcp__tree_sitter__register_project_tool",
      "mcp__tree_sitter__get_symbols",
      "mcp__tree_sitter__get_dependencies",
      "mcp__tree_sitter__run_query",
      "mcp__tree_sitter__list_languages",
      "mcp__tree_sitter__get_file",
      "mcp__tree_sitter__find_usage",
      "mcp__tree_sitter__list_projects_tool"
    ]
  },
  "enableAllProjectMcpServers": true,
  "enabledMcpjsonServers": ["tree_sitter"]
}
```

### Tool Granting to Sub-Agents

**CRITICAL:** Tools must be comma-separated in agent frontmatter (not YAML list format):

✅ **Correct:**
```yaml
---
tools: mcp__tree_sitter__register_project_tool, mcp__tree_sitter__get_symbols, Read, Write
---
```

❌ **Incorrect:**
```yaml
---
tools:
  - mcp__tree_sitter__register_project_tool
  - Read
---
```

**Best Practice:** Omit `tools` field entirely to inherit ALL tools (recommended for risk-analyzer and critic).

---

## Key Design Decisions

### 1. Function-Based Agents (Not Language-Based)

**Decision:** ONE risk-analyzer handles all languages (Java, Node, React, Android)

**Rationale:**
- 4× more efficient than separate language agents
- Catches cross-language issues (React → Node → Java flows)
- Consistent analysis quality across languages

### 2. High-Level Instructions (Not Prescriptive)

**Decision:** Agents told WHAT to find, not HOW to find it

**Rationale:**
- Claude uses tools intelligently (Grep, Read, Bash)
- More flexible and adaptable
- Agents can discover optimal strategies

### 3. Artifact Pattern

**Decision:** Agents output JSON to `output/pr-{NUMBER}/`

**Rationale:**
- Minimizes "game of telephone" between agents
- Persistent storage for audit trail
- Enables parallel agent development

### 4. Quality Gate Pattern

**Decision:** Critic agent validates findings before presentation

**Rationale:**
- Filters false positives
- Ensures actionable recommendations
- One of Andrew Ng's 4 fundamental agentic patterns

### 5. Step 1.5 CRITICAL RULE

**Decision:** Fact-extractor MUST create fact files for ALL changed files (no filtering)

**Rationale:**
- Risk-analyzer uses LLM reasoning to correlate changes
- Need complete facts to detect coordinated refactorings
- Breaking changes in annotations/interfaces require fact files
- Example: RabbitmqMessageHandler.java (annotation with removed method)

---

## Semantic AST vs Text-Based Analysis

### Why AST?

| Approach | Grep/Regex (Old) | AST-Based (New) |
|----------|------------------|-----------------|
| **Accuracy** | High false positives | Precise semantic understanding |
| **Context** | No code structure understanding | Full syntax tree context |
| **Languages** | Language-agnostic (too general) | Language-aware (Java, Python, etc.) |
| **Unknown Libraries** | Requires hardcoded lists | Pattern-based detection |
| **Comments/Strings** | Finds matches in comments | Ignores non-code |

### Example: Detecting HTTP Client Without Timeout

**❌ Text-Based (grep):**
```bash
grep -r "HttpClient" src/
grep -r "timeout" src/
```
- Finds comments, strings, unrelated code
- Can't determine if timeout is actually configured
- Can't handle custom client libraries

**✅ AST-Based (semantic):**
```json
{
  "receiver_type": "CustomApiClient",  // Pattern: ends with "Client"
  "method": "fetchData",               // Semantics: data fetching
  "category": "http",                  // AST determined this is HTTP
  "has_timeout": false,                // AST checked for timeout config
  "is_blocking": true                  // AST analyzed control flow
}
```
- Understands code structure
- Works on unknown libraries via patterns
- No false positives from comments

---

## Error Handling

### Common Issues

**1. "Tree-sitter MCP tools not available"**

**Cause:** MCP server not running or not configured

**Fix:** Check `.mcp.json` and `.claude/settings.local.json` configuration

**2. "Impossible pattern" or "Invalid node type" errors**

**Cause:** Tree-sitter query templates have syntax errors

**Fix:** Simplify query templates in `/mcp-server-tree-sitter/src/mcp_server_tree_sitter/language/templates/{language}.py`

**3. Files being skipped (N-1 files analyzed instead of N)**

**Cause:** Agent filtering out "unimportant" files (annotations, interfaces)

**Fix:** Step 1.5 CRITICAL RULE ensures ALL files get fact files

---

## Success Criteria

Analysis is successful when:
- ✅ All changed source files have fact files in `facts/` directory
- ✅ `risk-analysis.json` contains structured findings with severity levels
- ✅ All findings have specific file:line references
- ✅ Test recommendations are concrete and actionable
- ✅ `final-report.md` contains executive summary and merge recommendation
- ✅ No false positives (findings in unchanged files)

---

## Next Steps

- Read [analysis-phases.md](./analysis-phases.md) for detailed phase-by-phase breakdown
- Read [end-to-end-example.md](./end-to-end-example.md) for PR #27 walkthrough
- Read [getting-started.md](./getting-started.md) for quick start guide
