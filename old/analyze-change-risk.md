---
name: analyze-change-risk
description: Analyze a repository or code change for production risks and get test recommendations
example: analyze-change-risk /path/to/repo
---

# Change Risk Analysis Command

This command analyzes code changes for production risks and provides specific test recommendations.

## Usage

```bash
analyze-change-risk [repository_path]
```

**Arguments:**
- `repository_path` (optional): Path to the repository to analyze. Defaults to current directory.

## What it does

1. **Invokes the change-risk subagent** to analyze the repository
2. **Loads few-shot examples** to understand analysis patterns
3. **Scans for risk patterns**:
   - API breaking changes
   - Missing resilience patterns (timeouts, retries, circuit breakers)
   - Dependency risks
   - Configuration changes
4. **Generates a risk report** with:
   - Overall risk score (0-100)
   - Detailed findings with file:line references
   - Specific test recommendations
   - Actionable remediation steps

## Output

The analysis produces a JSON report containing:
- Risk score and level (LOW/MEDIUM/HIGH/CRITICAL)
- Confidence level
- Detailed findings for each issue
- Test recommendations
- Analysis metadata

## Examples

**Analyze current directory:**
```bash
analyze-change-risk
```

**Analyze specific repository:**
```bash
analyze-change-risk /path/to/my-service
```

## When to use

Use this command when:
- ✅ Before merging a pull request
- ✅ Before deploying to production
- ✅ After adding new dependencies
- ✅ After changing API contracts
- ✅ After modifying configuration
- ✅ During code review
- ✅ As part of CI/CD pipeline

## Delegation to Subagent

When you run this command, Claude will:

1. Detect the repository path
2. Delegate to the `change-risk` subagent using:
   ```
   > @change-risk analyze this repository for production risks
   ```
3. The subagent will load examples and perform the analysis
4. Results are returned to you in structured JSON format

## Tips

- Run this **before** manual testing to prioritize what to test
- Use findings to **write targeted tests** that address specific risks
- Share the report with your **code reviewers**
- Use risk score to determine **deployment strategy**:
  - LOW (0-30): Standard deployment
  - MEDIUM (31-60): Canary deployment
  - HIGH (61-80): Blue/Green deployment with rollback plan
  - CRITICAL (81-100): Phased rollout with kill switch
