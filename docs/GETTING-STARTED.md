# Getting Started with Resilience Agent

This guide walks you through analyzing your first Pull Request for production resilience risks using the Resilience Agent.

---

## Prerequisites

Before starting, ensure you have:

- **Claude Code** installed and configured
- **Git** installed on your system
- Access to a **GitHub repository** with Pull Requests
- Basic familiarity with command-line operations

---

## Overview: What You'll Do

1. Clone the resilience-agent-prototype repository
2. Clone the target repository you want to analyze
3. Start a Claude Code session
4. Run the analysis command
5. Grant necessary permissions
6. Review the generated results

**Time Required:** 10-15 minutes for first-time setup, 5 minutes for subsequent analyses

---

## Step 1: Clone and Setup Repositories

### 1.1 Clone the Resilience Agent

```bash
# Navigate to your projects directory
cd ~/projects

# Clone the resilience agent repository
git clone https://github.com/your-org/reselience-agent-prototype.git
cd reselience-agent-prototype
```

### 1.2 Clone the Target Repository

The repository you want to analyze should be in your workspace. For this tutorial, we'll use Google's microservices-demo as an example.

```bash
# From the reselience-agent-prototype directory
cd ..

# Clone the target repository
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git
```

### Expected Directory Structure

After setup, your directory structure should look like:

```
~/projects/
├── reselience-agent-prototype/    # The analysis agent
│   ├── .claude/
│   ├── docs/
│   ├── examples/
│   └── README.md
└── microservices-demo/             # Target repo to analyze
    ├── src/
    ├── .git/
    └── README.md
```

**Important:** Both repositories should be at the same directory level (siblings).

---

## Step 2: Start Claude Code Session

### 2.1 Navigate to Resilience Agent Directory

```bash
cd ~/projects/reselience-agent-prototype
```

### 2.2 Open Claude Code

Open Claude Code and ensure it recognizes the `.claude/` directory structure:

- Commands available in `.claude/commands/`
- Agents available in `.claude/agents/`
- Skills available in `.claude/skills/`

You should see the `/analyze-pr` command available in the command palette.

---

## Step 3: Trigger PR Analysis

### 3.1 Command Format

```bash
/analyze-pr <repo_name> <pr_number>
```

**Arguments:**
- `<repo_name>` - Name of the repository directory (e.g., "microservices-demo")
- `<pr_number>` - GitHub PR number to analyze (e.g., "2876")

### 3.2 Example Command

```bash
/analyze-pr microservices-demo 2876
```

### 3.3 What Happens Behind the Scenes

When you run this command, the orchestrator:

1. Searches for the `microservices-demo` repository in:
   - Current directory
   - Parent directory (`../microservices-demo`)
   - Workspace subdirectory

2. Fetches PR #2876 from GitHub:
   ```bash
   git fetch origin pull/2876/head:pr-2876
   git checkout pr-2876
   ```

3. Detects the base branch (main or master)

4. Generates the diff:
   ```bash
   git diff <base-branch>...pr-2876 > output/pr-2876/pr.diff
   ```

5. Creates output directory and metadata file

6. Launches the `risk-analyzer` subagent

7. Launches the `critic-agent` for quality validation

8. Presents final report

---

## Step 4: Grant Necessary Permissions

During execution, Claude will request permissions for various operations. Understanding why these are needed helps you make informed decisions.

### 4.1 Bash Tool Permission

**Request:**
```
Claude is requesting permission to use Bash tool
```

**Why Needed:**
- Navigate to repository directory
- Run git commands (fetch, checkout, diff)
- Create output directories
- Save analysis results

**Safe to Grant:** Yes - The agent only runs read operations and writes to the `output/` directory within the project.

### 4.2 Read Permission

**Request:**
```
Claude is requesting permission to read files in:
/path/to/microservices-demo/
```

**Why Needed:**
- Read PR diff to analyze code changes
- Examine changed files for resilience patterns
- Check git history for risk metrics

**Safe to Grant:** Yes - Read-only operations on the target repository.

### 4.3 Write Permission

**Request:**
```
Claude is requesting permission to write to:
output/pr-2876/
```

**Why Needed:**
- Save analysis results (JSON, Markdown)
- Store PR diff for reference
- Create metadata file

**Safe to Grant:** Yes - Writes are limited to the `output/` directory.

### Permission Summary

| Permission | Purpose | Risk Level |
|-----------|---------|------------|
| Bash | Git operations, directory navigation | Low (read-only git ops) |
| Read | Analyze code changes, git history | Low (read-only) |
| Write | Save results to output/ | Low (isolated directory) |

---

## Step 5: Review Results

### 5.1 Output Location

All analysis artifacts are saved in:

```
output/pr-2876/
├── metadata.json          # PR context and timestamps
├── pr.diff                # The PR diff that was analyzed
├── risk-analysis.json     # Detailed findings from risk-analyzer
└── final-report.md        # Executive summary from critic-agent
```

### 5.2 Understanding Output Files

#### metadata.json

Contains PR context:

```json
{
  "pr_number": "2876",
  "repository": "microservices-demo",
  "analyzed_at": "2025-10-19T14:30:00Z",
  "base_branch": "main"
}
```

#### pr.diff

The actual diff that was analyzed. Useful for understanding context of findings.

#### risk-analysis.json

Detailed findings from the risk-analyzer agent:

```json
{
  "use_case": "Change Risk & Test Recommendations",
  "analyzed_at": "2025-10-19T14:30:45Z",
  "findings": [
    {
      "type": "new_failure_mode",
      "severity": "HIGH",
      "file": "src/services/OrderService.java",
      "line": 45,
      "pattern": "RestClient call without circuit breaker",
      "impact": "If payment service fails, this will cause cascading failures",
      "recommendation": "Add @CircuitBreaker annotation with fallback method",
      "test_needed": "Integration test simulating payment service timeout",
      "git_metrics": {
        "commits_last_month": 12,
        "rollback_history": false
      }
    }
  ],
  "summary": {
    "total_findings": 3,
    "critical": 0,
    "high": 2,
    "medium": 1,
    "low": 0,
    "recommendation": "REQUEST_CHANGES"
  }
}
```

#### final-report.md

Executive summary suitable for PR comments:

```markdown
# PR #2876 Resilience Analysis

## Summary

Analyzed 3 files with 2 HIGH severity findings requiring attention before merge.

## Critical Findings

### 1. Missing Circuit Breaker (HIGH)

**File:** src/services/OrderService.java:45
**Issue:** RestClient call to payment service without circuit breaker protection

**Impact:** If payment service becomes slow or unavailable, this will cause cascading failures affecting all order processing.

**Recommendation:** Add Resilience4j circuit breaker:
- Add @CircuitBreaker annotation
- Implement fallback method
- Configure timeout in application.yml

**Test Required:** Integration test simulating payment service timeout and verifying fallback is called

## Recommendation

REQUEST_CHANGES - Address HIGH severity findings before merge
```

### 5.3 Reviewing Findings

#### Severity Levels

- **CRITICAL** - Production outage risk, breaking changes, or files with rollback history
- **HIGH** - Service degradation, missing resilience patterns, hotspot files
- **MEDIUM** - Potential edge case failures, coordination risks
- **LOW** - Best practice improvements

#### Git Metrics Context

Findings may include git history metrics:

```json
"git_metrics": {
  "commits_last_month": 18,
  "rollback_history": true,
  "unique_authors_3mo": 5
}
```

**Interpretation:**
- **commits_last_month > 15** - Hotspot file (high churn), +20 risk score
- **rollback_history: true** - File has production failure history, upgrade to CRITICAL
- **unique_authors > 5** - Coordination risk, +10 risk score

#### Taking Action

For each finding:

1. **Review file:line reference** - Navigate to the exact location
2. **Read the impact statement** - Understand what breaks
3. **Follow the recommendation** - Actionable fix provided
4. **Implement test** - Specific test scenario described
5. **Consider git context** - Assess based on file history

---

## Common Scenarios

### Scenario 1: Repository Not Found

**Error:**
```
ERROR: Repository 'microservices-demo' not found
Searched locations:
  - ./microservices-demo
  - ../microservices-demo
  - workspace/microservices-demo
```

**Solution:**
```bash
# Clone the repository at the correct location
cd ~/projects
git clone https://github.com/GoogleCloudPlatform/microservices-demo.git
```

### Scenario 2: PR Not Found

**Error:**
```
ERROR: PR #2876 not found in origin
```

**Solution:**
- Verify the PR number exists on GitHub
- Check you have network access to fetch from origin
- Ensure the repository remote is correctly configured

### Scenario 3: Empty Diff

**Warning:**
```
No changes detected in PR diff
```

**Solution:**
- Verify the PR branch is ahead of the base branch
- Check if the PR has already been merged
- Ensure you're comparing against the correct base branch

### Scenario 4: Agent Failure

**Error:**
```
risk-analyzer agent failed at Phase 2
```

**Solution:**
- Check if the diff file was created in `output/pr-<number>/pr.diff`
- Review the error message for specific issues
- Verify repository has readable code files

---

## Next Steps

### Analyze Another PR

```bash
/analyze-pr microservices-demo 3001
```

### Analyze Different Repository

```bash
# Clone another repository
cd ~/projects
git clone https://github.com/org/another-repo.git

# Analyze it
cd reselience-agent-prototype
/analyze-pr another-repo 42
```

### Understanding Detection Patterns

Review example patterns in:
```
examples/change-risk/java-resilience4j/
├── missing-circuit-breaker.md    # What gets detected
├── missing-timeout.md             # Detection examples
└── retry-without-circuit.md       # Anti-patterns
```

### Deep Dive into Architecture

Read the architecture documentation:
```
docs/ARCHITECTURE.md
```

Understand:
- Why subagents are used
- How skills are auto-discovered
- How components work together

---

## Tips for Best Results

### 1. Analyze PRs Early

Run analysis when PR is first created, not just before merge. Catches issues earlier in development cycle.

### 2. Focus on High Severity

Prioritize CRITICAL and HIGH findings. These have the highest production risk.

### 3. Review Git Metrics

Files with high churn or rollback history deserve extra attention. The git skill provides valuable historical context.

### 4. Use Findings as Learning

The recommendations show modern resilience patterns (Resilience4j, circuit breakers, timeouts). Use them to improve your team's patterns.

### 5. Validate Test Recommendations

The agent suggests specific tests. Implement these to prevent regressions.

---

## Troubleshooting

### Permission Denied Errors

If you get permission errors when fetching PRs:

```bash
# Ensure you have git credentials configured
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# For private repos, ensure SSH keys are set up
ssh -T git@github.com
```

### Claude Code Not Recognizing Commands

If `/analyze-pr` command not available:

1. Verify you're in the `reselience-agent-prototype` directory
2. Check `.claude/commands/analyze-pr.md` exists
3. Restart Claude Code session

### Output Directory Already Exists

If analyzing the same PR multiple times:

```bash
# Remove old results
rm -rf output/pr-2876/

# Re-run analysis
/analyze-pr microservices-demo 2876
```

---

## Summary

You've successfully:

1. Set up the Resilience Agent environment
2. Analyzed a Pull Request for resilience risks
3. Reviewed detailed findings with git context
4. Understood severity levels and recommendations

**Next:** Try analyzing a PR from your own project to see the agent in action on familiar code.

---

## Getting Help

- **Architecture Questions:** See `docs/ARCHITECTURE.md`
- **Issues:** Check the troubleshooting section above
- **Examples:** Review `examples/change-risk/` for detection patterns
- **GitHub Issues:** Report bugs or request features

---

## Appendix: Command Reference

### Analyze PR

```bash
/analyze-pr <repo_name> <pr_number>
```

**Example:**
```bash
/analyze-pr microservices-demo 2876
```

### Review Results

```bash
# View detailed findings
cat output/pr-2876/risk-analysis.json

# View executive summary
cat output/pr-2876/final-report.md

# View the analyzed diff
cat output/pr-2876/pr.diff
```

### Clean Up

```bash
# Remove analysis results
rm -rf output/pr-2876/

# Remove all results
rm -rf output/
```
