---
name: Git Risk Analysis
description: Analyze git history to enhance risk assessment for PR reviews. Use when analyzing file changes to detect code hotspots (high churn files), authorship patterns, historical failure correlation, and change complexity. Provides additional context beyond static code analysis to improve production risk scoring.
allowed-tools: [Bash]
---

# Git Risk Analysis Skill

## When to Use This Skill

- ✅ Analyzing file changes in Pull Request reviews
- ✅ Assessing risk of modifications to existing files
- ✅ Need historical context for code stability
- ✅ Enhancing risk scores with churn/hotspot data
- ✅ Identifying files with deployment failure history

## Git Metrics Commands

### 1. Detect Code Hotspots (High Churn Rate)

**Purpose:** Identify files changed frequently (instability indicator)

```bash
# Count commits touching this file in last 30 days
git log --since="1 month ago" --oneline -- {FILE_PATH} | wc -l
```

**Interpretation:**
- **0-3 commits** = Stable file (LOW risk)
- **4-10 commits** = Moderate churn (baseline risk)
- **10-15 commits** = High churn → **+10 risk score**
- **15+ commits** = HOTSPOT → **+20 risk score, flag as CRITICAL**

**Rationale:** Research shows high churn correlates with poor implementation, missing abstractions, or inadequate tests. Hotspot files (20% of code) contain 80% of bugs.

---

### 2. Check Authorship Concentration

**Purpose:** Detect coordination risk from multiple contributors

```bash
# List authors who touched this file in last 3 months
git shortlog -sn --since="3 months ago" -- {FILE_PATH}
```

**Interpretation:**
- **1-2 authors** = Good ownership (LOW risk)
- **3-4 authors** = Coordination needed → **Note in findings**
- **5+ authors** = High coordination risk → **+10 risk score**

**Rationale:** Multiple authors increase merge conflicts, inconsistent patterns, and knowledge fragmentation. Coordination overhead grows exponentially with team size.

---

### 3. Find Historical Deployment Failures

**Purpose:** Identify files involved in production rollbacks/hotfixes

```bash
# Search for rollback/revert/hotfix commits affecting this file
git log --all --grep="revert\|rollback\|hotfix\|emergency" --oneline -- {FILE_PATH}
```

**Interpretation:**
- **0 matches** = No rollback history
- **1+ matches** = File has deployment failure history → **Upgrade severity to CRITICAL**
- **3+ matches** = Chronic production issues → **Recommend architectural review**

**Rationale:** Files with rollback history are statistically more likely to cause future production issues. Past failures predict future failures.

---

### 4. Measure Change Complexity

**Purpose:** Calculate lines changed (churn magnitude)

```bash
# Total lines added + deleted in last 30 days
git log --since="1 month ago" --numstat -- {FILE_PATH} | \
  awk 'NF==3 {added+=$1; deleted+=$2} END {print added+deleted}'
```

**Interpretation:**
- **0-100 lines** = Small changes (LOW risk)
- **100-300 lines** = Moderate refactoring (baseline)
- **300-500 lines** = Large changes → **+5 risk score**
- **500+ lines** = Massive churn → **+15 risk score, recommend incremental approach**

**Rationale:** Large line changes increase bug probability. Smaller, incremental changes are safer for production.

---

### 5. Check Recent Bug Fix Rate

**Purpose:** Measure code quality via bug fix frequency

```bash
# Count bug fix commits in last 60 days
git log --since="2 months ago" --grep="fix\|bug\|issue\|defect" --oneline -- {FILE_PATH} | wc -l
```

**Interpretation:**
- **0-1 fixes** = Stable code quality
- **2-3 fixes** = Some quality concerns → **Note in findings**
- **4+ fixes** = Quality red flag → **+10 risk score, recommend tests**

**Rationale:** High bug fix rate indicates underlying quality issues. Files requiring frequent fixes often lack test coverage or have design flaws.

---

### 6. Detect Merge Conflict Frequency

**Purpose:** Identify files with complex merge history

```bash
# Count merge commits affecting this file
git log --oneline --merges --since="2 months ago" -- {FILE_PATH} | wc -l
```

**Interpretation:**
- **0-2 merges** = Normal collaboration
- **3-5 merges** = Active development area
- **6+ merges** = High conflict risk → **+5 risk score**

**Rationale:** Frequent merges suggest parallel development streams, increasing conflict probability and integration issues.

---

## Integration with Risk Analysis

### Add Git Metrics to Findings

Include git context in your JSON output:

```json
{
  "file": "src/services/PaymentService.java",
  "line": 45,
  "severity": "CRITICAL",
  "git_metrics": {
    "commits_last_month": 18,
    "unique_authors_3mo": 7,
    "lines_changed_30d": 750,
    "bug_fixes_60d": 5,
    "rollback_history": true,
    "merge_conflicts_60d": 8
  },
  "risk_adjustment": "+35 (hotspot + rollback history + high bug rate)",
  "original_severity": "HIGH",
  "adjusted_severity": "CRITICAL",
  "recommendation": "This file is a production hotspot with rollback history. Consider: 1) Architectural review before adding complexity, 2) Increase test coverage (5 bugs in 60 days), 3) Limit concurrent modifications (7 authors)"
}
```

### Risk Score Adjustment Formula

```
Base Risk Score (from static analysis)
+ Churn Adjustment (0-20 points)
+ Authorship Adjustment (0-10 points)
+ Bug Fix Rate Adjustment (0-10 points)
+ Rollback History (upgrade to CRITICAL if present)
= Final Risk Score
```

---

## Best Practices

### ✅ Do:
- Run git commands from repository root
- Handle missing files gracefully (new files have no git history)
- Cache results to avoid redundant git calls
- Use --oneline to reduce output size
- Check if file exists before running git log

### ❌ Don't:
- Fail entire analysis if git commands error
- Run git commands on files outside the repository
- Make assumptions about git configuration
- Ignore context (1 commit from 1 author in a 5-year-old file is stable!)

---

## Error Handling

```bash
# Example: Safe git command with error handling
if git rev-parse --git-dir > /dev/null 2>&1; then
  CHURN=$(git log --since="1 month ago" --oneline -- "$FILE" 2>/dev/null | wc -l)
  echo "Churn: $CHURN"
else
  echo "Not a git repository, skipping git analysis"
fi
```

---

## Example Usage

**Scenario:** Analyzing PaymentService.java in PR #1234

```bash
# 1. Check churn
git log --since="1 month ago" --oneline -- src/services/PaymentService.java | wc -l
# Output: 15  → HOTSPOT (+20 risk)

# 2. Check authors
git shortlog -sn --since="3 months ago" -- src/services/PaymentService.java
# Output:
#    8  Alice
#    4  Bob
#    2  Charlie
#    1  Dave
# → 4 authors (+5 risk for coordination)

# 3. Check rollbacks
git log --all --grep="revert\|rollback" --oneline -- src/services/PaymentService.java
# Output: 2 commits found
# → Rollback history (UPGRADE TO CRITICAL)

# 4. Final assessment
# Base severity: HIGH
# + Hotspot: +20
# + Authors: +5
# + Rollback history: UPGRADE TO CRITICAL
# Final: CRITICAL with git context
```

---

## Success Criteria

Git analysis enhances risk scoring when:

- ✅ Hotspot files get higher risk scores
- ✅ Files with rollback history flagged as CRITICAL
- ✅ Coordination risks identified for multi-author files
- ✅ Bug-prone files get test coverage recommendations
- ✅ Agent provides stability context in recommendations
- ✅ 20-30% more accurate risk predictions

---

## When NOT to Use

- ❌ New files (no git history exists)
- ❌ Non-git repositories
- ❌ Files outside repository boundaries
- ❌ When git commands timeout (very large repos)

In these cases, gracefully skip git analysis and rely on static code analysis only.
