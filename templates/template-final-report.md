# PR #{pr_number} - Risk Analysis

**Repository:** {repository_name}
**Branch:** {head_branch} → {base_branch}
**Analyzed:** {timestamp}

---

## Analysis Quality Metrics

**Analysis Confidence:** {confidence_score}%
**Files Analyzed:** {files_analyzed} / {files_changed} ({coverage_percentage}%)
**AST Extraction Success:** {ast_success_rate}%
**Analysis Duration:** {duration}

**Detection Coverage:**
- Failure Modes: {failure_modes_count} detected
- Breaking Changes: {breaking_changes_count} detected
- Async Patterns: {async_patterns_count} detected
- Test Recommendations: {test_recommendations_count} generated

---

## Findings Summary

| # | Severity | Pattern | File:Line | Brief Description |
|---|----------|---------|-----------|-------------------|
{findings_table_rows}

**Breaking Changes:** {breaking_changes_count}
{breaking_changes_summary_list}

---

## Breaking Changes

{breaking_changes_section}

---

## External Review Flags

**Items Requiring Validation Outside This PR:**

{external_review_flags_section}

---

## Merge Recommendation

### {merge_decision_icon} {merge_decision}

**Decision Reasoning:**
{decision_reasoning}

**Required Before Merge:**
{required_actions_checklist}

**Estimated Fix Time:** {estimated_fix_time}

**After Merge - Monitoring Required:**
{post_merge_monitoring_checklist}

---

## Detailed Findings

{detailed_findings_section}

---

## Appendix: AST Facts Analysis

**Extraction Summary:**
- **Total Files Changed:** {total_files_changed}
- **Source Files Analyzed:** {source_files_analyzed}
- **AST Extraction Success Rate:** {ast_success_rate}%
- **Async Patterns Detected:** {async_patterns_count}
- **Breaking Changes Detected:** {breaking_changes_count}

**Fact Extraction Coverage:**
- Dependencies extracted: {dependencies_count}
- Method calls analyzed: {method_calls_count}
- Async communication patterns: {async_patterns_count}
- Message schema changes: {message_schema_changes_count}
- Configuration changes: {config_changes_count}

**AST Analysis Artifacts:**
All detailed AST facts available at: `output/pr-{pr_number}/facts/*.json`

**Analysis Methodology:**
- **Semantic Analysis:** Tree-sitter AST parsing
- **Pattern Detection:** Language-agnostic pattern matching
- **Risk Reasoning:** LLM-based semantic reasoning (Claude Opus)
- **Blast Radius:** Fan-in/fan-out analysis using symbol usage

**Confidence Factors:**
- High confidence: Findings backed by explicit AST facts
- Medium confidence: Findings based on pattern inference
- Low confidence: Findings requiring manual verification

---

## Appendix: File Analysis Coverage

### Files Analyzed ({files_analyzed})

| File | Language | AST Extraction | Findings Count |
|------|----------|----------------|----------------|
{analyzed_files_table}

### Files Reviewed for Context ({files_reviewed_for_context})

The following files were part of the PR but do not require resilience analysis:

| File | Type | Reason |
|------|------|--------|
{context_files_table}

{file_exclusion_explanations}

### Coverage Summary by Type

| File Type | Total | Analyzed | Reviewed for Context | Source Coverage % |
|-----------|-------|----------|----------------------|-------------------|
{coverage_by_type_table}

**Total PR Files:** {total_pr_files}
**Source Files Analyzed:** {files_analyzed} / {source_files_total} ({source_coverage_percentage}%)
**Context Files Reviewed:** {files_reviewed_for_context}

---

**Analysis Powered By:**
Resilience Agent v2.0 - AST-Based Production Risk Analysis
**Generated:** {timestamp}
**Analysis Duration:** {duration}

---

## Template Instructions for Critic Agent

### How to Fill This Template

**Section: Findings Summary Table**
For each finding, add a row:
```
| {number} | {severity} | {pattern} | {file}:{line} | {brief_description} |
```

Example:
```
| 1 | CRITICAL | consumer_without_dlq | FlightUpdatedListener.java:11 | New RabbitMQ consumer has no dead letter queue |
```

**Section: Detailed Findings**
For each finding, create a subsection:
```markdown
### {severity}: Finding #{number} - {title}

**File:** `{file}:{line}`
**Pattern:** `{pattern}`
**Severity:** {severity}

**Impact:**
{impact_description}

**Blast Radius:**
- **Direct Impact:** {direct_impact}
- **User-Facing:** {user_facing}
- **Fan-In:** {fan_in_description}
- **Affected Services:** {affected_services}

**Recommendation:**
{numbered_recommendation_list}

**Test Recommendations:**
{test_checklist}

**Code Examples:**

<details>
<summary>Click to expand configuration code</summary>

\`\`\`{language}
{code_example}
\`\`\`

</details>
```

**Section: Breaking Changes**
For each breaking change:
```markdown
### {number}. {title}

**File:** `{file}`
**Type:** `{change_type}`
**Severity:** {severity}
**Impact:** {impact_description}

**Description:**
{detailed_description}

**Migration Required:**
{migration_instructions}

**Verification Checklist:**
{verification_checklist}

**Test Recommendations:**
{test_checklist}
```

**Section: File Analysis Coverage**

For the "Files Analyzed" table, add a row for each source file that was successfully analyzed:
```
| {file_path} | {language} | {ast_status} | {findings_count} |
```
Example: `| src/services/PaymentService.java | Java | Success | 3 |`

For the "Files Reviewed for Context" table, add a row for each non-source file (dynamically categorized using pattern matching):
```
| {file_path} | {category} | {reason} |
```
- `{category}` determined by pattern matching (Configuration, Documentation, Build file, Test file, Binary/Media, etc.)
- `{reason}` from the categorization table in critic-agent.md
- Only include files that were actually present in this PR

For the "Coverage Summary by Type" table, dynamically discover all file extensions from pr.diff and add a row for each:
```
| {extension} | {total_count} | {analyzed_count} | {context_count} | {source_coverage} |
```
- `{extension}` discovered from actual PR files (e.g., .java, .py, .md, .yml, .xml, .properties)
- `{source_coverage}` = Percentage if analyzed_count > 0, otherwise "N/A"
- Sort: source extensions first (analyzed > 0), then context extensions (analyzed = 0)

For aggregate metrics, calculate dynamically from PR data:
```
{total_pr_files} = Count of ALL files in pr.diff
{source_files_total} = Count of files successfully analyzed
{files_analyzed} = Same as source_files_total
{source_coverage_percentage} = (files_analyzed / source_files_total) * 100, or "N/A" if no source files
{files_reviewed_for_context} = total_pr_files - files_analyzed
```

**Section: External Review Flags**
For each flag:
```markdown
### {number}. {title}

**Resource:** `{resource_name}`
**Type:** {resource_type}
**Reason:** {reason}

**Action Required:**
{action_description}

**Recommendation:**
{numbered_recommendation_list}
```

**Merge Decision Options:**
- `APPROVE` - No blocking issues
- `APPROVE WITH TESTS` - Non-blocking issues, tests required
- `REQUEST CHANGES` - Blocking issues must be fixed

**Severity Levels:**
- `CRITICAL` - Must fix before merge
- `HIGH` - Should fix before merge
- `MEDIUM` - Can fix after merge
- `LOW` - Nice to have
