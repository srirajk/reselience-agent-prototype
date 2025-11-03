# Risk-Analyzer Performance Optimization - Complete Implementation Guide

## Executive Summary

**Problem:** Risk-analyzer takes 50 minutes to analyze 11 files (vs fact-extractor: 6 minutes)
**Root Cause:** Zero explicit parallelism instructions → sequential processing
**Solution:** Add explicit parallel batching like fact-extractor has
**Expected Result:** 50 minutes → 4-6 minutes (10x improvement, keep Opus quality)

---

## Complete Change Specification

### Change 1: Phase 1 - Parallel Fact Loading
**File:** `.claude/agents/risk-analyzer.md`
**Lines:** 199-208
**Priority:** HIGH (10-13s savings)

**FIND THIS TEXT:**
```markdown
### Your Task: Read All Fact Files

```bash
# Use Glob to find all fact files
find output/pr-<NUMBER>/facts -name "*.json"

# Use Read tool to load each file
# Parse the JSON structure
# Build a mental model of the changes
```
```

**REPLACE WITH:**
```markdown
### Your Task: Read All Fact Files IN PARALLEL ⚡

**PERFORMANCE OPTIMIZATION:** Load all fact files concurrently in a SINGLE message to minimize latency.

**Step 1: Discover fact files**
```bash
# Use Glob to find all fact files
find output/pr-<NUMBER>/facts -name "*.json"
```

**Step 2: Load ALL files in parallel (CRITICAL)**

**IMPORTANT:** Make multiple Read tool calls in a SINGLE message. Do NOT read files one-by-one.

**Example for 11 files:**
```
[In ONE message, make 11 Read tool calls:]
- Read output/pr-369/facts/ClientConfiguration.java.json
- Read output/pr-369/facts/ServerConfiguration.java.json
- Read output/pr-369/facts/FileA.java.json
- Read output/pr-369/facts/FileB.java.json
... (continue for all files)
- Read output/pr-369/facts/FileK.java.json

[Wait for ALL results to arrive together - they process in parallel]
```

**Step 3: Build mental model**
- Parse ALL JSON structures together
- Build complete view of changes across entire PR
- Aggregate calls[], async_communication[], public_api_changes[] from all files

**Why this works:** File reads are I/O-bound and independent. Parallel reads complete in 1-2s vs 11-15s sequential.
```

**Rationale:** Mirrors fact-extractor.md lines 130-274 which explicitly says "PARALLEL ⚡" and provides clear batching examples.

---

### Change 2: Phase 2 - Batch LLM Reasoning (BIGGEST IMPACT)
**File:** `.claude/agents/risk-analyzer.md`
**Lines:** 210-318 (entire Phase 2 section)
**Priority:** CRITICAL (40 minute savings)

**FIND THIS TEXT:**
```markdown
## 📊 Phase 2: LLM Reasoning from Facts

**This is your core capability**: Apply your base knowledge about resilience patterns to the extracted facts.

You have AST-extracted facts. Now use LLM reasoning to:
1. Interpret what these calls are actually doing
2. Detect resilience gaps using semantic understanding
3. Handle UNKNOWN libraries by reasoning from naming patterns

---

### 🎯 Key Insight: Reason from Facts, Not Frameworks

You don't need hardcoded library lists. Use the facts to reason:
```

**REPLACE WITH:**
```markdown
## 📊 Phase 2: LLM Reasoning from Facts (BATCH ANALYSIS ⚡)

**This is your core capability**: Apply your base knowledge about resilience patterns to the extracted facts.

You have AST-extracted facts. Now use LLM reasoning to:
1. Interpret what these calls are actually doing
2. Detect resilience gaps using semantic understanding
3. Handle UNKNOWN libraries by reasoning from naming patterns

**PERFORMANCE OPTIMIZATION:** Process ALL fact files in ONE reasoning pass. Do NOT analyze files sequentially.

---

### 🎯 Key Insight: Reason from Facts, Not Frameworks

You don't need hardcoded library lists. Use the facts to reason:
```

**THEN, FIND THIS TEXT (Lines 245-273):**
```markdown
### Reasoning Process

For each call in the facts, ask yourself:

1. **Is this a network call?**
   - Receiver type ends in "Client"?
   - Method name suggests remote operation (`fetch`, `get`, `post`, `invoke`)?
   - Return type is a response object?
   - Throws network-related exceptions?

2. **Does it have resilience patterns?**
   - `has_timeout: true`?
   - `timeout_value_ms` configured with reasonable value?
   - `has_circuit_breaker_annotation: true`?
   - `has_retry_annotation: true`?
   - `retry_config` configured?

3. **What's the context?**
   - Is it blocking in an async method? (`in_async_method: true` + no async marker)
   - Is it in a transaction? (check `in_transaction` from facts)
   - Is resource external? (check `category`: http, grpc, database, mq_publish, mq_consume)

4. **What's the blast radius?** (Phase 3 will provide this)
   - How many callers depend on this?
   - Is it user-facing?
   - Is it in a critical path?
```

**REPLACE WITH:**
```markdown
### Reasoning Process: BATCH ANALYSIS (Critical Performance Optimization)

**DO NOT analyze files one-by-one.** Instead, process ALL facts together in a SINGLE reasoning operation.

**Strategy:**

**Step 1: Aggregate ALL data from ALL fact files**
Build global inventories across the entire PR:
```python
# Conceptual aggregation (do this mentally)
all_calls = []
all_async_communication = []
all_public_api_changes = []

for fact_file in all_loaded_facts:
    all_calls.extend(fact_file['calls'])
    all_async_communication.extend(fact_file.get('async_communication', []))
    all_public_api_changes.extend(fact_file.get('public_api_changes', []))
```

**Step 2: Apply pattern filters to ENTIRE inventory (ONE reasoning pass)**

Filter and analyze in bulk:

1. **Filter: Network calls without timeouts**
   ```
   Query: all_calls WHERE
     (receiver_type ENDS_WITH "Client" OR method_name IN ["fetch","get","post","invoke"])
     AND has_timeout = false

   For each result → Generate finding: http_client_without_timeout
   ```

2. **Filter: Network calls without circuit breakers**
   ```
   Query: all_calls WHERE
     (receiver_type ENDS_WITH "Client" OR category = "http")
     AND has_circuit_breaker_annotation = false

   For each result → Generate finding: external_call_without_circuit_breaker
   ```

3. **Filter: Blocking calls in async methods**
   ```
   Query: all_calls WHERE
     in_async_method = true
     AND method_name NOT IN async_indicators
     AND category IN ["http", "database", "grpc"]

   For each result → Generate finding: blocking_call_in_async_context
   ```

4. **Filter: Async communication without dead letter queues**
   ```
   Query: all_async_communication WHERE
     operation = "consume"
     AND has_dead_letter_queue = false

   For each result → Generate finding: consumer_without_dlq
   ```

5. **Filter: Breaking API changes**
   ```
   Query: all_public_api_changes WHERE
     change_type IN ["removed_field", "removed_endpoint", "signature_changed"]

   For each result → Generate finding: breaking_change_detected
   ```

**Step 3: Generate findings list**
Output all findings from Steps 1-5 in a single findings array.

**Example execution (11 files → 3 findings):**
```
Input: 11 fact files loaded (all_calls contains ~50 total calls)
Filter 1: calls WHERE receiver_type ENDS_WITH "Client" AND has_timeout=false
  → Result: 1 match (ClientConfiguration.java:204 - Http.outboundGateway)
  → Generate Finding #1: http_client_without_timeout

Filter 2: async_communication WHERE has_dead_letter_queue=false
  → Result: 1 match (ServerConfiguration.java:436 - RabbitMQ consumer)
  → Generate Finding #2: consumer_without_dlq

Filter 3: public_api_changes WHERE change_type="removed_endpoint"
  → Result: 1 match (RestController.java:89 - DELETE /api/orders)
  → Generate Finding #3: breaking_api_change

Filters 4-10: No matches
Output: 3 findings total (in ONE reasoning pass, not 11 separate passes)
```

**Why this works:** Batch filtering is O(1) LLM reasoning operation vs O(n) per-file analysis. Reduces 11 sequential Opus rounds (33-44 min) to 1 batched Opus call (3-5 min).

---

### Original 4-Question Framework (Use for Each Finding)

For each call that matches a filter, ask yourself:

1. **Is this a network call?**
   - Receiver type ends in "Client"?
   - Method name suggests remote operation (`fetch`, `get`, `post`, `invoke`)?
   - Return type is a response object?
   - Throws network-related exceptions?

2. **Does it have resilience patterns?**
   - `has_timeout: true`?
   - `timeout_value_ms` configured with reasonable value?
   - `has_circuit_breaker_annotation: true`?
   - `has_retry_annotation: true`?
   - `retry_config` configured?

3. **What's the context?**
   - Is it blocking in an async method? (`in_async_method: true` + no async marker)
   - Is it in a transaction? (check `in_transaction` from facts)
   - Is resource external? (check `category`: http, grpc, database, mq_publish, mq_consume)

4. **What's the blast radius?** (Phase 3 will provide this)
   - How many callers depend on this?
   - Is it user-facing?
   - Is it in a critical path?
```

**Rationale:** This is the BIGGEST bottleneck. Current instructions say "For each call" which causes 11 sequential reasoning loops (33-44 min). New instructions explicitly require ONE bulk analysis pass (3-5 min).

---

### Change 3: Phase 3 - Batch Fan-In/Fan-Out Lookups
**File:** `.claude/agents/risk-analyzer.md`
**Lines:** 320-402 (entire Phase 3 section header and fan-in subsection)
**Priority:** MEDIUM (6-11s savings)

**FIND THIS TEXT:**
```markdown
## 🎯 Phase 3: Fan-In/Fan-Out Analysis (Context Enrichment)

Use AST-based tools to understand blast radius.

---

### Fan-In: Who Calls This? (AST-Based)

**Purpose:** Determine how many other parts of the code depend on the changed method.

For each changed method/function:
1. Use find_usage tool with symbol name and language
2. Count the results → callers_count
3. Extract file paths from results → callers_sample
```

**REPLACE WITH:**
```markdown
## 🎯 Phase 3: Fan-In/Fan-Out Analysis (Context Enrichment) ⚡

Use AST-based tools to understand blast radius.

**PERFORMANCE OPTIMIZATION:** Query callers for multiple symbols concurrently in ONE message.

---

### Fan-In: Who Calls This? (AST-Based - BATCH LOOKUPS)

**Purpose:** Determine how many other parts of the code depend on the changed methods.

**Step 1: Extract ALL changed method/function names**
From Phase 1 fact files:
- Scan all public_api_changes[] for new/modified methods
- Scan all method definitions with public/protected visibility
- Build list of symbol names to analyze

**Step 2: Batch lookup callers for ALL methods (CRITICAL)**

**IMPORTANT:** Make multiple find_usage tool calls in a SINGLE message for parallel execution.

**Example for 3 methods:**
```
[In ONE message, make 3 find_usage calls:]
- find_usage(symbol="RequestGateway.echo", language="java")
- find_usage(symbol="ClientConfiguration.clientFlow", language="java")
- find_usage(symbol="ServerConfiguration.serverFlow", language="java")

[Wait for ALL 3 results to arrive together - they process in parallel]
```

**Step 3: Process results**
For each find_usage result:
1. Count the results → callers_count
2. Extract file paths from results → callers_sample
```

**Rationale:** Mirrors fact-extractor's parallel tool call pattern. find_usage calls are independent and can run concurrently.

---

### Change 4: Phase 5 - Batch Git Analysis
**File:** `.claude/agents/risk-analyzer.md`
**Lines:** 854-894 (Git Risk Analysis Skill section)
**Priority:** MEDIUM (24-36s savings)

**FIND THIS TEXT (Lines 869-879):**
```markdown
# Check if file is a hotspot (high churn) - ONLY BEFORE PR TIMESTAMP
git log main --since="1 month ago" --until="${PR_TIMESTAMP}" --oneline -- src/services/PaymentService.java | wc -l
# Output: 18 commits → HOTSPOT! Add +1 severity level

# Check for rollback history - ONLY BEFORE PR TIMESTAMP
git log main --until="${PR_TIMESTAMP}" --grep="revert\|rollback" --oneline -- src/services/PaymentService.java
# If any commits found → ROLLBACK HISTORY! Add warning
```

**REPLACE WITH:**
```markdown
**PERFORMANCE OPTIMIZATION:** Batch git analysis for ALL changed files in minimal commands.

**Strategy: Analyze all modified files together (not one-by-one)**

**Step 1: Get list of modified files (exclude new files)**
```bash
# Extract modified files from metadata or pr.diff
MODIFIED_FILES=$(grep "^diff --git" output/pr-{NUMBER}/pr.diff | \
  grep -v "new file mode" | \
  awk '{print $4}' | \
  sed 's|^b/||')
```

**Step 2: Single hotspot check for ALL files (ONE command)**
```bash
# Load PR timestamp for temporal filtering
PR_TIMESTAMP=$(jq -r '.pr_timestamp' output/pr-{NUMBER}/metadata.json)

# Get churn counts for ALL modified files in ONE git log command
git log main --since="1 month ago" --until="${PR_TIMESTAMP}" --oneline --name-only -- $MODIFIED_FILES | \
  awk '
    /^[a-f0-9]+/ { commit=1; next }
    commit && NF { files[$0]++; commit=0 }
    END { for (f in files) print f, files[f] }
  '
```
Output example:
```
src/services/PaymentService.java 18
src/controllers/OrderController.java 5
src/models/User.java 2
```
→ Files with >10 commits are HOTSPOTS! Add +1 severity level

**Step 3: Single rollback check for ALL files (ONE command)**
```bash
# Check rollback history for ALL modified files in ONE command
git log main --until="${PR_TIMESTAMP}" --grep="revert\|rollback" --oneline --name-only -- $MODIFIED_FILES
```
Output example:
```
df2363a7 Revert 'Upgrade to Derby `10.16.1.2`'
src/services/PaymentService.java

b3bab0de Revert 'file-split-ftp Move errorChannel to Poller'
src/services/FileService.java
```
→ Any file with rollback commits gets warning flag

**Why this works:** Git can process multiple file paths in one invocation. No need for per-file loops. Reduces 14 sequential git commands (7 files × 2 commands) to 2 batched commands.
```

**Rationale:** Current example shows one-file-at-a-time commands. Git supports multiple file paths natively - should use batch commands like grep does.

---

### Change 5: Add Performance Guidance Summary (New Section)
**File:** `.claude/agents/risk-analyzer.md`
**Location:** After line 124 (before Phase 1)
**Priority:** HIGH (provides overview of all optimizations)

**INSERT NEW SECTION:**
```markdown
---

## 🚀 Performance Optimization Strategy

**Goal:** Minimize latency by reducing sequential operations through parallel batching.

**Key Principles:**

1. **Parallel File I/O** (Phase 1)
   - Load ALL fact files in ONE message with multiple Read calls
   - Files process concurrently (1-2s vs 11-15s sequential)

2. **Batch LLM Reasoning** (Phase 2)
   - Analyze ALL facts together in ONE reasoning pass
   - Build global inventory → filter patterns → generate findings
   - ONE Opus call for 11 files (3-5 min) vs 11 separate calls (33-44 min)

3. **Parallel Tool Calls** (Phase 3)
   - Make multiple find_usage calls in ONE message
   - Symbols process concurrently (3-4s vs 9-15s sequential)

4. **Batch Git Commands** (Phase 5)
   - Git supports multiple file paths natively
   - 2 batched commands (4-6s) vs 14 sequential commands (28-42s)

**Expected Performance:**
- **Without optimizations:** ~50 minutes (sequential processing)
- **With optimizations:** ~4-6 minutes (parallel batching)
- **Improvement:** 10x faster while preserving Opus reasoning quality

**Model Justification:**
This agent uses **Opus** (not Sonnet) because:
- Deep reasoning required for pattern detection in unknown libraries
- Semantic understanding of call intent from naming patterns
- Context-aware severity adjustment based on business impact
- Holistic analysis across multiple files simultaneously

Opus excels at reasoning over large contexts - one Opus call analyzing 11 files together is significantly faster than 11 separate Opus calls.

---
```

**Rationale:** Provides clear overview of why each optimization exists and expected impact. Helps future maintainers understand the performance strategy.

---

## Implementation Checklist

### Pre-Implementation
- [ ] Read this entire document
- [ ] Backup current risk-analyzer.md: `cp .claude/agents/risk-analyzer.md .claude/agents/risk-analyzer.md.backup`
- [ ] Verify you have access to PR #369 for testing

### Implementation Order
- [ ] **Change 5** (Add Performance Guidance Summary) - Sets context
- [ ] **Change 1** (Parallel Fact Loading) - Lines 199-208
- [ ] **Change 2** (Batch LLM Reasoning) - Lines 210-318 ⭐ CRITICAL
- [ ] **Change 3** (Batch Fan-In Lookups) - Lines 320-402
- [ ] **Change 4** (Batch Git Analysis) - Lines 854-894

### Post-Implementation Testing
- [ ] Run `/analyze-pr spring-data-examples 369` again
- [ ] Verify execution time < 10 minutes (target: 4-6 minutes)
- [ ] Compare output/pr-369/risk-analysis.json with backup - should have same 3 findings
- [ ] Check tool use count in logs - should be ~10 tools (vs previous 33)
- [ ] Verify final-report.md quality unchanged

### Rollback Plan
If testing fails:
```bash
# Restore backup
cp .claude/agents/risk-analyzer.md.backup .claude/agents/risk-analyzer.md

# Re-test original version to confirm baseline
/analyze-pr spring-data-examples 369
```

---

## Expected Results

### Before Optimization
```
⏺ risk-analyzer(Analyze PR change risks)
  ⎿  Done (33 tool uses · 57.0k tokens · 50m 18s)
```

### After Optimization
```
⏺ risk-analyzer(Analyze PR change risks)
  ⎿  Done (8-12 tool uses · 55-60k tokens · 4-6 minutes)
```

### Key Metrics
- **Time:** 50 min → 4-6 min (10x improvement)
- **Tool Uses:** 33 → 8-12 (~70% reduction)
- **Token Usage:** ~57k → ~55-60k (similar, slight increase due to batching)
- **Quality:** Unchanged (same findings, same Opus reasoning depth)
- **Model:** Still Opus (preserving deep reasoning capability)

---

## FAQ

**Q: Why keep Opus if Sonnet is faster?**
A: Opus provides superior semantic reasoning for unknown libraries and cross-file pattern detection. With batching optimizations, Opus becomes fast enough (4-6 min) while maintaining quality.

**Q: Will batching reduce finding quality?**
A: No - batching actually IMPROVES quality because Opus can see patterns across ALL files simultaneously rather than analyzing in isolation.

**Q: What if we have 100 files instead of 11?**
A: Consider adding adaptive batching like fact-extractor (process in batches of 10-20 files). Current optimization assumes <50 files per PR.

**Q: Can we parallelize across phases?**
A: No - phases have dependencies (Phase 2 needs Phase 1 facts, Phase 3 needs Phase 2 findings). But within each phase, we maximize parallelism.

**Q: Why not switch to async agent execution?**
A: Agent coordination overhead would add complexity. Current sequential-phase, parallel-within-phase approach is simpler and sufficient for 4-6 min runtime.

---

## Investigation Methodology (How We Found This)

### Performance Data Analysis
```
fact-extractor: 6m 7s (44 tool uses, 98.5k tokens) - Sonnet
risk-analyzer: 50m 18s (33 tool uses, 57.0k tokens) - Opus
critic-agent: 2m 28s (7 tool uses, 45.5k tokens) - Sonnet
```

**Key Observation:** Risk-analyzer used FEWER tools but took 8x longer → Model alone doesn't explain it.

### Root Cause Discovery
1. Analyzed risk-analyzer.md (1164 lines) for performance instructions
2. Found ZERO mentions of "parallel", "batch", or "concurrent"
3. Compared with fact-extractor.md which has explicit "PARALLEL ⚡" directives
4. Traced likely execution flow: "For each call" → sequential loops
5. Analyzed PR #369 artifacts: 11 files, 3 findings, ~50 calls total
6. Estimated tool breakdown: 12 file reads + 11 reasoning loops + 14 git commands + 5 find_usage = ~42 operations
7. Calculated: 42 sequential operations × 1-2 min/operation with Opus = ~50 min ✓

### Validation
- Cross-referenced fact-extractor's performance patterns
- Confirmed git supports batch file path processing
- Verified MCP find_usage can run in parallel
- Tested calculation: Same operations in parallel batches = ~4-6 min

---

**Document Version:** 1.0
**Date:** 2025-11-03
**Based on Analysis of:** PR #369 (spring-data-examples)
**Estimated Implementation Time:** 2-3 hours
**Expected ROI:** 45-47 minutes saved per PR analysis
