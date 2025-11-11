# Analysis Phases: Step-by-Step Breakdown

This document provides a detailed breakdown of each phase in the AST-based PR analysis workflow.

---

## Overview

The analysis consists of 5 phases:

1. **Setup & PR Acquisition** (Orchestrator)
2. **AST Fact Extraction** (fact-extractor sub-agent)
3. **Change Risk Analysis** (risk-analyzer sub-agent)
4. **Quality Gate** (critic sub-agent)
5. **Present Results** (Orchestrator)

```
┌─────────────────────────────────────────────────────────────┐
│  Phase 1: Setup & PR Acquisition                            │
│  Who: Orchestrator (analyze-pr.md)                          │
│  Output: pr.diff, metadata.json                             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 2: AST Fact Extraction                               │
│  Who: fact-extractor sub-agent                              │
│  Output: facts/*.json (one per changed file)                │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 3: Change Risk Analysis                              │
│  Who: risk-analyzer sub-agent                               │
│  Output: risk-analysis.json                                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 4: Quality Gate                                      │
│  Who: critic sub-agent                                      │
│  Output: final-report.md                                    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  Phase 5: Present Results                                   │
│  Who: Orchestrator (analyze-pr.md)                          │
│  Output: User-facing final report                           │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Setup & PR Acquisition

**Responsible Agent:** Orchestrator (`.claude/commands/analyze-pr.md`)

**Duration:** ~10-30 seconds

**Purpose:** Fetch PR from GitHub, generate diff, create output directory structure.

### Steps

#### 1.1. Parse User Input

User command format:
```bash
/analyze-pr <repo_name> <pr_number> [output_dir]
```

**Example:**
```bash
/analyze-pr booking-microservices-java-spring-boot 27
```

**Arguments:**
- `{{arg1}}` = Repository name
- `{{arg2}}` = PR number
- `{{arg3}}` = Output directory (optional, defaults to `./output`)

#### 1.2. Locate Repository

Orchestrator searches for repository in multiple locations:
1. Current directory: `./<repo_name>`
2. Parent directory: `../<repo_name>`
3. Workspace subdirectory: `workspace/<repo_name>`

**Git Commands:**
```bash
# Check if directory exists and is a git repo
if [ -d "booking-microservices-java-spring-boot" ]; then
  cd booking-microservices-java-spring-boot
  git status  # Verify it's a git repo
fi
```

#### 1.3. Fetch PR from GitHub

```bash
# Fetch PR branch from origin
git fetch origin pull/27/head:pr-27

# Checkout PR branch
git checkout pr-27
```

#### 1.4. Detect Base Branch

Orchestrator autonomously detects whether the base branch is `main` or `master`:

```bash
# Check which branch exists
git show-ref --verify --quiet refs/heads/main && echo "main" || echo "master"
```

#### 1.5. Generate PR Diff

```bash
# Generate diff between base branch and PR branch
git diff main...pr-27 > output/pr-27/pr.diff
```

**Diff Format:**
```diff
diff --git a/src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqConfiguration.java b/src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqConfiguration.java
index 1234567..abcdefg 100644
--- a/src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqConfiguration.java
+++ b/src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqConfiguration.java
@@ -70,6 +70,8 @@ public class RabbitmqConfiguration {
+    container.setAcknowledgeMode(AcknowledgeMode.AUTO);
```

#### 1.6. Create Output Directory Structure

```bash
mkdir -p output/pr-27/facts/
```

**Directory Structure:**
```
output/
└── pr-27/
    ├── metadata.json       (created in this phase)
    ├── pr.diff             (created in this phase)
    ├── facts/              (populated in Phase 2)
    │   ├── File1.java.json
    │   └── File2.java.json
    ├── risk-analysis.json  (created in Phase 3)
    └── final-report.md     (created in Phase 4)
```

#### 1.7. Save Metadata

**File:** `output/pr-27/metadata.json`

```json
{
  "pr_number": "27",
  "repository": "booking-microservices-java-spring-boot",
  "analyzed_at": "2025-10-28T14:30:00Z",
  "base_branch": "main"
}
```

#### 1.8. Present Status to User

```
🔍 RESILIENCE AGENT - PR ANALYSIS

Repository: booking-microservices-java-spring-boot
PR Number: 27
Output Directory: output/pr-27/

Starting analysis...
```

### Error Handling

**Repository Not Found:**
```
❌ ERROR: Repository 'booking-microservices-java-spring-boot' not found

Searched locations:
  • ./booking-microservices-java-spring-boot
  • ../booking-microservices-java-spring-boot
  • workspace/booking-microservices-java-spring-boot

Suggestion: Clone the repository first:
  git clone https://github.com/org/booking-microservices-java-spring-boot.git
```

**PR Not Found:**
```
❌ ERROR: PR #27 not found on remote origin

Suggestion: Verify PR number exists on GitHub
```

---

## Phase 2: AST Fact Extraction

**Responsible Agent:** fact-extractor (`.claude/agents/fact-extractor.md`)

**Duration:** ~30-60 seconds (depends on PR size)

**Purpose:** Extract semantic facts from changed source files using Tree-sitter AST parsing.

### What Makes Fact-Extractor a Specialist

- **Tree-sitter MCP Expert:** Direct access to tree-sitter AST parsers
- **Multi-language Support:** Java, Python, TypeScript, Kotlin, Go, Rust, C++
- **Semantic Understanding:** Parses code structure, not just text
- **Pattern Recognition:** Detects async patterns (RabbitMQ, Kafka, HTTP, gRPC)

### Steps

#### 2.1. Discover & Verify Tree-sitter MCP Tools

**Goal:** Fail-fast if MCP server is not available.

**Tools Used:**
```
mcp__tree_sitter__list_languages
mcp__tree_sitter__list_projects_tool
```

**Example Output:**
```json
{
  "languages": ["java", "python", "typescript", "kotlin", "go", "rust"],
  "projects": []
}
```

**Error Handling:**
If tools are not available, agent reports:
```
❌ Tree-sitter MCP tools not available
Falling back to grep-based analysis (limited accuracy)
```

#### 2.2. Register Repository with Tree-sitter

**Goal:** Register repository as a project so Tree-sitter can parse files.

**Tool Used:**
```
mcp__tree_sitter__register_project_tool(
  project_name="booking-microservices",
  root_path="/absolute/path/to/booking-microservices-java-spring-boot"
)
```

**Why Important:**
- Tree-sitter needs project context to resolve imports
- Enables cross-file analysis (find_usage for fan-in analysis)

#### 2.3. Parse PR Diff to Identify Changed Files

**Goal:** Extract list of changed source files from pr.diff.

**Method:**
```bash
# Read pr.diff
cat output/pr-27/pr.diff | grep "^diff --git" | awk '{print $3}' | sed 's|^a/||'
```

**Example Output:**
```
src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqConfiguration.java
src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqMessageHandler.java (DELETED)
src/buildingblocks/src/main/java/buildingblocks/outboxprocessor/PersistMessageProcessorImpl.java
src/services/passenger/src/main/java/io/bookingmicroservices/passenger/listeners/FlightUpdatedListener.java (NEW)
...
```

**Filter Criteria:**
- ✅ Include: `.java`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.kt`, `.go`, `.rs` files
- ❌ Exclude: `.md`, `.txt`, `.yml`, `.json`, `.xml` (non-source files)

#### 2.4. 🚨 Step 1.5: CRITICAL RULE - Extract Facts for EVERY Changed File

**MANDATORY RULE:**

> **Create a fact file for EVERY file identified in Step 2.3.**
>
> **NO EXCEPTIONS - Even if the file appears to be:**
> - "Just an annotation definition" (`@interface` in Java, decorator in Python)
> - "Just an interface with no implementation"
> - "Just a DTO/model with no business logic"
> - "Just constants or enums"
> - "Just a type definition" (TypeScript `interface` or `type`)

**WHY This Rule Exists:**

The risk-analyzer uses LLM reasoning to analyze changes across multiple files. It needs to see ALL changed files to:

1. **Detect coordinated refactorings:** Annotation definition changes + usage site changes
2. **Identify breaking API changes:** Removed methods/fields from public contracts
3. **Assess migration completeness:** Are all usage sites updated consistently?
4. **Reason about cross-file impacts:** Interface changes affecting implementations

**Key Principle:**

> **Fact-extractor extracts facts. Risk-analyzer reasons about facts.**
>
> Don't filter upfront based on "importance" - let the LLM decide what matters.

**Example:** RabbitmqMessageHandler.java

In PR #27, this file is an annotation definition with a removed method `queueName()`:

```java
@interface RabbitmqMessageHandler {
  // String queueName();  ← REMOVED
}
```

If skipped, risk-analyzer can't detect:
- Breaking change (removed method)
- Migration pattern (usage sites removing `queueName="..."`)
- Completeness check (are all implementations updated?)

**Fact File Created:**
```json
{
  "file": "src/buildingblocks/src/main/java/buildingblocks/rabbitmq/RabbitmqMessageHandler.java",
  "language": "java",
  "parse_error": true,
  "error_message": "File was deleted in this PR",
  "public_api_changes": [
    {
      "type": "endpoint_removed",
      "old_signature": "RabbitmqMessageHandler interface",
      "new_signature": null,
      "breaking": true
    }
  ],
  "external_review_flags": [
    {
      "type": "api_gateway_check",
      "resource_name": "RabbitmqMessageHandler",
      "reason": "File was deleted. Check if any code depends on this interface.",
      "recommendation": "Verify all implementations have been migrated to MessageHandler interface"
    }
  ]
}
```

#### 2.5. Extract AST Facts from Each File

**For Each Changed File:**

##### Step 2.5.1: Get Symbols

**Tool Used:**
```
mcp__tree_sitter__get_symbols(
  project="booking-microservices",
  file_path="src/.../RabbitmqConfiguration.java",
  language="java"
)
```

**Example Output:**
```json
{
  "classes": [
    {
      "name": "RabbitmqConfiguration",
      "line": 27,
      "methods": [
        {"name": "connectionFactory", "line": 46},
        {"name": "addListeners", "line": 70}
      ]
    }
  ],
  "interfaces": [],
  "functions": []
}
```

##### Step 2.5.2: Get Dependencies

**Tool Used:**
```
mcp__tree_sitter__get_dependencies(
  project="booking-microservices",
  file_path="src/.../RabbitmqConfiguration.java",
  language="java"
)
```

**Example Output:**
```json
{
  "imports": [
    "org.springframework.amqp.rabbit.connection.ConnectionFactory",
    "org.springframework.amqp.rabbit.core.RabbitTemplate",
    "buildingblocks.outboxprocessor.PersistMessageProcessor"
  ]
}
```

**Pattern Matching:**

The agent classifies dependencies:
- `org.springframework.amqp` → External service (RabbitMQ)
- `com.fasterxml.jackson` → External library (JSON serialization)
- `buildingblocks.*` → Internal module

##### Step 2.5.3: Analyze Method Calls

**Tool Used:**
```
mcp__tree_sitter__run_query(
  project="booking-microservices",
  query="(method_invocation) @call",
  file_path="src/.../RabbitmqConfiguration.java",
  language="java"
)
```

**Example AST Node:**
```json
{
  "type": "method_invocation",
  "receiver": "RabbitTemplate",
  "method": "convertSendAndReceive",
  "arguments": ["exchange", "routingKey", "message", "messagePostProcessor"],
  "line": 154
}
```

**Semantic Analysis:**

Agent infers metadata:
- `receiver_type: "RabbitTemplate"` → Pattern: ends with "Template"
- `method: "convertSendAndReceive"` → Blocking send-receive pattern
- `has_timeout: false` → No timeout parameter detected
- `category: "mq_publish"` → Message queue publish operation
- `is_external: false` BUT `external_service: true` (RabbitMQ broker is external)

**Result:**
```json
{
  "line": 154,
  "receiver_type": "RabbitTemplate",
  "method": "convertSendAndReceive",
  "is_blocking": true,
  "has_timeout": false,
  "has_circuit_breaker_annotation": false,
  "has_retry_annotation": false,
  "category": "mq_publish",
  "resource": "rabbitmq_exchange",
  "timeout_value_ms": null
}
```

##### Step 2.5.4: Detect Async Communication Patterns

**Pattern Recognition:**

Agent searches for:
- **RabbitMQ:** `@RabbitListener`, `RabbitTemplate`, `SimpleMessageListenerContainer`
- **Kafka:** `@KafkaListener`, `KafkaTemplate`, `ConsumerFactory`
- **HTTP:** `RestTemplate`, `WebClient`, `*Client` classes
- **gRPC:** `*Stub`, `*BlockingStub`

**Example: RabbitMQ Consumer Detection**

**Code:**
```java
@Bean
public SimpleMessageListenerContainer addListeners(...) {
    SimpleMessageListenerContainer container = new SimpleMessageListenerContainer();
    container.setAcknowledgeMode(AcknowledgeMode.AUTO);
    // ...
}
```

**AST Pattern Detected:**
- Bean method returns `SimpleMessageListenerContainer`
- Method call: `setAcknowledgeMode(AcknowledgeMode.AUTO)`

**Fact Generated:**
```json
{
  "type": "rabbitmq",
  "operation": "consume",
  "ack_mode": "auto",
  "delivery_guarantee": "at_least_once",
  "error_handling": {
    "has_dead_letter": false,
    "has_circuit_breaker": false
  },
  "retry_policy": {
    "enabled": false
  }
}
```

##### Step 2.5.5: Detect Breaking API Changes

**What Qualifies as Breaking:**
- Removed methods from public classes/interfaces
- Removed fields from DTOs/events
- Changed method signatures (return type, parameters)
- Deleted files (entire public API removed)

**Example: Deleted Interface**

```json
{
  "file": "RabbitmqMessageHandler.java",
  "parse_error": true,
  "error_message": "File was deleted in this PR",
  "public_api_changes": [
    {
      "type": "endpoint_removed",
      "old_signature": "RabbitmqMessageHandler interface",
      "breaking": true
    }
  ]
}
```

##### Step 2.5.6: Generate External Review Flags

**Purpose:** Mark changes that need validation outside the PR scope.

**Examples:**
- Schema registry check (message schema changes)
- API gateway check (REST endpoint changes)
- Contract test needed (new message consumers)

**Example:**
```json
{
  "external_review_flags": [
    {
      "type": "contract_test_needed",
      "resource_name": "FlightUpdated",
      "resource_type": "rabbitmq",
      "reason": "New listener for FlightUpdated messages. No error handling or retry logic.",
      "recommendation": "Add contract tests to verify FlightUpdated message schema compatibility."
    }
  ]
}
```

#### 2.6. Save Fact Files

**For Each Changed File:**

**File:** `output/pr-27/facts/RabbitmqConfiguration.java.json`

**Schema:** Follows `.claude/templates/fact-schema.json` (v2.0)

**Content Sections:**
- `dependencies` - Imports and external libraries
- `calls` - Method invocations with resilience metadata
- `async_communication` - Message queue patterns
- `message_schema_changes` - Field additions/removals
- `public_api_changes` - Breaking changes
- `config_changes` - Configuration modifications
- `annotations` - Framework annotations
- `external_review_flags` - Changes needing external validation

#### 2.7. Generate Extraction Summary

**File:** `output/pr-27/facts/extraction-summary.md`

**Purpose:** Human-readable summary of fact extraction results.

**Content:**
- Overview (PR number, files analyzed, extraction date)
- Files analyzed (categorized by type)
- Key findings (async patterns, breaking changes)
- Resilience gaps identified
- External review flags
- Statistics (fact files created, patterns detected)

**Example Snippet:**
```markdown
## Key Findings

### Async Communication Patterns Detected

#### 1. RabbitMQ Consumer (RabbitmqConfiguration.java:70)
- **Type:** rabbitmq
- **Operation:** consume
- **Ack Mode:** AUTO
- **Risk:** No DLQ, no retry policy, no circuit breaker

#### 2. RabbitMQ Publisher (PersistMessageProcessorImpl.java:154)
- **Type:** rabbitmq
- **Operation:** publish
- **Method:** convertSendAndReceive
- **Risk:** No timeout configured on RabbitTemplate call
```

### Output

**Files Created:**
```
output/pr-27/facts/
├── extraction-summary.md
├── RabbitmqConfiguration.java.json
├── RabbitmqMessageHandler.java.json
├── PersistMessageProcessorImpl.java.json
├── FlightUpdatedListener.java.json
└── ... (16 total)
```

**Success Metrics:**
- ✅ 16/16 files analyzed (100% coverage)
- ✅ All changed source files have fact files
- ✅ Breaking changes detected
- ✅ Async patterns identified

---

## Phase 3: Change Risk Analysis

**Responsible Agent:** risk-analyzer (`.claude/agents/risk-analyzer.md`)

**Duration:** ~60-120 seconds (depends on complexity)

**Purpose:** Reason about extracted facts to detect failure modes, blast radius, and recommend tests.

### What Makes Risk-Analyzer a Specialist

- **Resilience Pattern Expert:** Deep knowledge of circuit breakers, timeouts, retries, bulkheads
- **Semantic Pattern Matching:** Recognize risks in unknown/custom libraries via naming patterns
- **Blast Radius Analysis:** Fan-in/fan-out analysis to assess change impact
- **Severity Contextualization:** Adjust severity based on user-facing paths and traffic

**Model:** claude-opus (complex reasoning required)

### Steps

#### 3.1. Load AST Fact Files

**Tool Used:** `Read`

```bash
# Read all fact files
for file in output/pr-27/facts/*.json; do
  # Parse JSON and extract semantic facts
done
```

#### 3.2. Apply LLM Reasoning to Facts

**Goal:** Detect failure modes using semantic patterns.

##### Pattern 1: HTTP/RPC Calls Without Timeouts

**Detection Logic:**
```
IF receiver_type ends with "Client" OR "Stub"
   AND (method contains "get", "fetch", "call", "execute")
   AND is_blocking == true
   AND has_timeout == false
   AND (category == "http" OR category == "grpc")
THEN: HTTP/RPC client without timeout (failure mode)
```

**Example Fact:**
```json
{
  "receiver_type": "RabbitTemplate",
  "method": "convertSendAndReceive",
  "is_blocking": true,
  "has_timeout": false,
  "category": "mq_publish"
}
```

**Reasoning:**
- "Template" suffix → Spring template pattern
- "convertSendAndReceive" → Blocking send-receive
- `has_timeout: false` → No timeout configured
- `category: "mq_publish"` → Message queue operation

**Finding:**
```json
{
  "type": "new_failure_mode",
  "severity": "HIGH",
  "file": "PersistMessageProcessorImpl.java",
  "line": 154,
  "pattern": "rabbitmq_publish_without_timeout",
  "impact": "RabbitTemplate.convertSendAndReceive() call without timeout. If RabbitMQ broker is slow, publisher threads will block indefinitely.",
  "recommendation": "Add timeout configuration to RabbitTemplate using setReplyTimeout() method."
}
```

##### Pattern 2: Consumer Without Dead Letter Queue

**Detection Logic:**
```
IF async_communication.operation == "consume"
   AND async_communication.error_handling.has_dead_letter == false
   AND async_communication.is_new == true
THEN: New consumer without DLQ (critical failure mode)
```

**Example Fact:**
```json
{
  "type": "rabbitmq",
  "operation": "consume",
  "is_new": true,
  "error_handling": {
    "has_dead_letter": false
  },
  "ack_mode": "auto"
}
```

**Reasoning:**
- New consumer (`is_new: true`)
- No DLQ configured
- AUTO ack mode → Failed messages are lost OR infinite redelivery

**Finding:**
```json
{
  "type": "new_failure_mode",
  "severity": "CRITICAL",
  "file": "FlightUpdatedListener.java",
  "line": 11,
  "pattern": "consumer_without_dlq",
  "impact": "NEW RabbitMQ consumer has no dead letter queue. Poison messages will block the queue indefinitely.",
  "recommendation": "Configure dead letter exchange (DLX) and dead letter queue (DLQ) in RabbitmqConfiguration."
}
```

##### Pattern 3: Breaking API Changes

**Detection Logic:**
```
IF public_api_changes.breaking == true
THEN: Breaking change detected
```

**Example Fact:**
```json
{
  "public_api_changes": [
    {
      "type": "endpoint_removed",
      "old_signature": "RabbitmqMessageHandler interface",
      "breaking": true
    }
  ]
}
```

**Finding:**
```json
{
  "type": "breaking_change",
  "severity": "HIGH",
  "file": "RabbitmqMessageHandler.java",
  "pattern": "interface_removed",
  "impact": "RabbitmqMessageHandler interface deleted. All implementations must migrate to MessageHandler<T>.",
  "recommendation": "Verify all usage sites have been migrated. Search codebase for 'implements RabbitmqMessageHandler'."
}
```

#### 3.3. Fan-In/Fan-Out Analysis (Blast Radius)

**Goal:** Determine impact scope of each finding.

##### Fan-In Analysis (Who Calls This?)

**Tool Used:** `mcp__tree_sitter__find_usage`

```
mcp__tree_sitter__find_usage(
  project="booking-microservices",
  symbol="convertSendAndReceive",
  language="java"
)
```

**Example Output:**
```json
{
  "usages": [
    {"file": "PersistMessageProcessorImpl.java", "line": 154},
    {"file": "EventDispatcherImpl.java", "line": 89}
  ]
}
```

**Trace Call Chain:**
```
convertSendAndReceive (Line 154)
    ← publishMessage (PersistMessageProcessorImpl)
        ← dispatch (EventDispatcherImpl)
            ← TransactionPipelineBehavior
                ← CreateFlightController (user-facing!)
                ← UpdateFlightController (user-facing!)
                ← CreateBookingController (user-facing!)
```

**Blast Radius Calculation:**
```json
{
  "blast_radius": {
    "fan_in": {
      "direct_callers": 1,
      "indirect_callers": "13+ REST controllers via TransactionPipelineBehavior",
      "user_facing": true
    },
    "impact_scope": "All domain events published through outbox pattern"
  }
}
```

##### Severity Contextualization

**Rules:**
```
IF fan_in.user_facing == true
   AND fan_in.indirect_callers > 10
   THEN: Upgrade severity (MEDIUM → HIGH, HIGH → CRITICAL)

IF fan_in.user_facing == false
   AND fan_in.direct_callers < 3
   THEN: Downgrade severity (HIGH → MEDIUM, CRITICAL → HIGH)
```

**Example:**
```
Original Severity: HIGH
User-facing: true (13+ REST controllers)
Final Severity: HIGH (confirmed, justifies high severity)
```

#### 3.4. Use Git Risk Analysis Skill

**Goal:** Enhance findings with git history metrics.

**Skill:** `git-risk-analysis` (`.claude/skills/git-risk-analysis/SKILL.md`)

**What It Does:**
- Check code churn (hotspot detection)
- Check rollback history (has this file been rolled back before?)
- Identify high-risk files (frequent changes + frequent failures)

**Example Usage:**
```
Skill(git-risk-analysis)
```

**Output:**
```json
{
  "file": "RabbitmqConfiguration.java",
  "churn_score": 8.5,
  "rollback_count": 2,
  "recent_failures": [
    {"date": "2025-09-15", "reason": "RabbitMQ connection timeout"}
  ]
}
```

**Integration with Findings:**
```json
{
  "type": "new_failure_mode",
  "severity": "HIGH → CRITICAL (upgraded due to git history)",
  "git_metrics": {
    "churn_score": 8.5,
    "rollback_count": 2,
    "risk_reason": "File has been rolled back twice. High churn indicates instability."
  }
}
```

#### 3.5. Recommend Specific Tests

**Goal:** Provide concrete test recommendations for each finding.

**Test Categories:**
- **Unit Tests:** Test individual components in isolation
- **Integration Tests:** Test component interactions (e.g., RabbitMQ, database)
- **Contract Tests:** Verify message schemas match producer/consumer contracts
- **Timeout Tests:** Verify timeout behavior (slow responses, broker downtime)
- **Circuit Breaker Tests:** Verify circuit breaker opens after failures
- **Negative Tests:** Test error scenarios (poison messages, invalid data)

**Example:**
```json
{
  "type": "new_failure_mode",
  "pattern": "rabbitmq_publish_without_timeout",
  "test_needed": [
    "integration_timeout_test",
    "rabbitmq_broker_slow_response_test",
    "circuit_breaker_test",
    "thread_pool_exhaustion_test"
  ],
  "test_details": {
    "integration_timeout_test": {
      "description": "Start RabbitMQ broker with simulated 10-second delay. Verify timeout occurs.",
      "expected": "Timeout exception after 5 seconds"
    },
    "circuit_breaker_test": {
      "description": "Simulate 5 consecutive RabbitMQ failures. Verify circuit opens.",
      "expected": "Circuit breaker opens, subsequent calls fail fast"
    }
  }
}
```

#### 3.6. Write Risk Analysis JSON

**Tool Used:** `Write`

**File:** `output/pr-27/risk-analysis.json`

**Schema:**
```json
{
  "pr": {
    "number": 27,
    "repo": "booking-microservices-java-spring-boot",
    "base": "main",
    "head": "refactor/refactor-rabbitmq"
  },
  "summary": {
    "failure_modes": 5,
    "breaking_changes": 2,
    "test_recipes": 12,
    "resiliency_gaps": 6
  },
  "failure_modes": [
    {
      "type": "new_failure_mode",
      "severity": "HIGH",
      "file": "PersistMessageProcessorImpl.java",
      "line": 154,
      "pattern": "rabbitmq_publish_without_timeout",
      "impact": "...",
      "recommendation": "...",
      "test_needed": [...],
      "reasoning": "...",
      "blast_radius": {...}
    }
  ],
  "breaking_changes": [...],
  "test_recommendations": [...]
}
```

### Output

**Files Created:**
```
output/pr-27/risk-analysis.json
```

**Success Metrics:**
- ✅ 5 failure modes detected
- ✅ 2 breaking changes identified
- ✅ 12 test recommendations provided
- ✅ All findings have file:line references
- ✅ Blast radius analyzed for each finding

---

## Phase 4: Quality Gate

**Responsible Agent:** critic (`.claude/agents/critic-agent.md`)

**Duration:** ~30-45 seconds

**Purpose:** Validate findings, filter false positives, synthesize final report.

### What Makes Critic a Specialist

- **Meta-Reasoning:** Reason about the quality of other agent's findings
- **False Positive Filtering:** Remove low-confidence findings
- **Synthesis Skills:** Convert technical findings into executive summaries
- **Quality Validation:** Ensure actionable recommendations

### Steps

#### 4.1. Read Risk Analysis JSON

**Tool Used:** `Read`

```bash
cat output/pr-27/risk-analysis.json
```

#### 4.2. Validate Finding Quality

**Quality Checks:**

##### Check 1: File:Line References

**Rule:** Every finding MUST reference a specific file and line number.

❌ **Invalid:**
```json
{
  "file": "unknown",
  "line": null,
  "impact": "Some classes have missing timeouts"
}
```

✅ **Valid:**
```json
{
  "file": "PersistMessageProcessorImpl.java",
  "line": 154,
  "impact": "RabbitTemplate.convertSendAndReceive() at line 154 has no timeout"
}
```

##### Check 2: Actionable Recommendations

**Rule:** Recommendations must be specific and actionable, not vague advice.

❌ **Vague:**
```json
{
  "recommendation": "Add better error handling"
}
```

✅ **Actionable:**
```json
{
  "recommendation": "1. Add timeout to RabbitTemplate using setReplyTimeout(5000). 2. Add circuit breaker using @CircuitBreaker annotation. 3. Implement fallback strategy to store messages in local DB."
}
```

##### Check 3: Severity Justification

**Rule:** Severity levels must be justified by blast radius and impact.

**Verification:**
```
IF severity == "CRITICAL"
   THEN: blast_radius.user_facing == true OR blast_radius.fan_in > 20

IF severity == "HIGH"
   THEN: blast_radius.user_facing == true OR blast_radius.fan_in > 10
```

##### Check 4: No False Positives

**Rule:** No findings should reference unchanged files.

**Check:**
```bash
# Get list of changed files from pr.diff
changed_files=$(cat output/pr-27/pr.diff | grep "^diff --git" | awk '{print $3}' | sed 's|^a/||')

# Verify each finding references a changed file
for finding in findings; do
  if ! grep -q "$finding.file" <<< "$changed_files"; then
    echo "FALSE POSITIVE: $finding.file not in changed files"
  fi
done
```

#### 4.3. Filter False Positives

**Example False Positive:**
```json
{
  "file": "BaseController.java",
  "line": 45,
  "impact": "Missing error handling"
}
```

**Check:**
```bash
grep "BaseController.java" output/pr-27/pr.diff
# No results → file not changed in this PR → FALSE POSITIVE
```

**Action:** Remove this finding from final report.

#### 4.4. Synthesize Final Report

**Goal:** Convert technical JSON findings into user-friendly Markdown report.

##### Section 1: Executive Summary

```markdown
# PR #27 Risk Analysis - Executive Summary

**Repository:** booking-microservices-java-spring-boot
**PR Title:** Refactor/refactor rabbitmq
**Analysis Date:** 2025-10-28

## Overview

This PR refactors RabbitMQ configuration to use Spring Boot's native RabbitProperties.

**Risk Level:** 🔴 HIGH

**Summary:**
- ✅ **Positive:** Migrated to standard Spring Boot configuration
- ⚠️  **Concerns:** 5 new failure modes detected, 2 breaking changes
- 🧪 **Testing:** 12 integration tests recommended

**Recommendation:** ⚠️  REQUEST_CHANGES - Address critical resiliency gaps before merge
```

##### Section 2: Critical Findings

```markdown
## 🚨 Critical Findings

### 1. RabbitMQ Consumer Without Dead Letter Queue (CRITICAL)

**File:** FlightUpdatedListener.java:11
**Pattern:** consumer_without_dlq

**Impact:**
NEW RabbitMQ consumer for FlightUpdated messages has no dead letter queue configured. If message processing fails or message is malformed (poison message), it will be redelivered indefinitely, blocking consumption of subsequent messages.

**Recommendation:**
1. Configure dead letter exchange (DLX) in RabbitmqConfiguration
2. Set max retry attempts (x-max-retries header)
3. Add error handling in listener with try-catch
4. Implement alerting for DLQ depth

**Tests Needed:**
- poison_message_test
- dlq_routing_test
- message_retry_limit_test
```

##### Section 3: Test Recommendations

```markdown
## 🧪 Test Recommendations

### Integration Tests (6)
1. **rabbitmq_broker_timeout_test**
   - Simulate slow RabbitMQ broker (10s delay)
   - Verify timeout occurs after 5 seconds
   - Verify error is logged

2. **poison_message_test**
   - Send malformed JSON message
   - Verify message routed to DLQ
   - Verify subsequent messages processed
```

##### Section 4: Merge Recommendation

```markdown
## 📊 Merge Recommendation

**Decision:** ⚠️  REQUEST_CHANGES

**Rationale:**
- 1 CRITICAL finding (consumer without DLQ)
- 2 HIGH findings (publish without timeout, AUTO ack mode risk)
- 2 breaking changes (interface removal)

**Before Merge:**
1. ✅ Add DLQ configuration for FlightUpdatedListener
2. ✅ Add timeout to RabbitTemplate
3. ✅ Verify all RabbitmqMessageHandler implementations migrated
4. ✅ Add integration tests for timeout and DLQ scenarios

**After Merge:**
- Monitor RabbitMQ queue depth
- Monitor DLQ message count
- Alert on message processing failures
```

#### 4.5. Write Final Report

**Tool Used:** `Write`

**File:** `output/pr-27/final-report.md`

### Output

**Files Created:**
```
output/pr-27/final-report.md
```

**Success Metrics:**
- ✅ All findings validated
- ✅ False positives filtered
- ✅ Executive summary synthesized
- ✅ Merge recommendation provided

---

## Phase 5: Present Results

**Responsible Agent:** Orchestrator (`.claude/commands/analyze-pr.md`)

**Duration:** ~5 seconds

**Purpose:** Display final report to user.

### Steps

#### 5.1. Read Final Report

**Tool Used:** `Read`

```bash
cat output/pr-27/final-report.md
```

#### 5.2. Display to User

```markdown
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# PR #27 Risk Analysis - Executive Summary

[Full report content displayed...]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ANALYSIS COMPLETE

Repository: booking-microservices-java-spring-boot
PR Number: 27

All artifacts saved to: output/pr-27/
- metadata.json
- pr.diff
- facts/*.json (16 files)
- risk-analysis.json
- final-report.md

To review detailed findings:
  cat output/pr-27/risk-analysis.json

To review final report:
  cat output/pr-27/final-report.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Summary: Phase Comparison

| Phase | Agent | Duration | Input | Output | Key Tool |
|-------|-------|----------|-------|--------|----------|
| 1. Setup | Orchestrator | 10-30s | PR number | pr.diff, metadata.json | git, bash |
| 2. Fact Extraction | fact-extractor | 30-60s | pr.diff | facts/*.json | mcp__tree_sitter__* |
| 3. Risk Analysis | risk-analyzer | 60-120s | facts/*.json | risk-analysis.json | Read, find_usage, Skill |
| 4. Quality Gate | critic | 30-45s | risk-analysis.json | final-report.md | Read, Write |
| 5. Present | Orchestrator | 5s | final-report.md | User-facing report | Read |

**Total Duration:** ~2-4 minutes (depends on PR size)

---

## Next Steps

- Read [architecture-flow.md](./architecture-flow.md) for visual architecture diagram
- Read [end-to-end-example.md](./end-to-end-example.md) for PR #27 walkthrough
- Read [getting-started.md](./getting-started.md) for quick start guide
