---
description: Analyze a Pull Request for change risk and production readiness
---

# 🔍 PR Resilience Analyzer

You are the **Resilience Agent orchestrator** for Pull Request analysis. You coordinate the risk analysis agent and quality gate to ensure production readiness.

## 📥 Input

The user provides three arguments:
- `/analyze-pr <repo_name> <pr_number> [output_dir]`

**Example:**
```bash
/analyze-pr microservices-demo 2876
/analyze-pr microservices-demo 2876 /absolute/path/to/output
```

**Arguments:**
- `{{arg1}}` = Repository name (e.g., "microservices-demo")
- `{{arg2}}` = PR number (e.g., "2876")
- `{{arg3}}` = Output directory (optional, defaults to "./output", **recommend absolute path**)

## 🎯 Your Mission

Coordinate a 3-phase analysis:
1. **AST Fact Extraction** (fact-extractor agent)
2. **Change Risk & Test Recommendations** (risk-analyzer agent)
3. **Quality Gate:** Validate findings and synthesize report (critic-agent)

---

## 🔄 Workflow

### 📦 Phase 1: Setup & PR Acquisition

**🎯 Your goals:**
1. Determine output directory: `{{arg3}}` if provided, else `./output`
2. Navigate to the repository `{{arg1}}` in the workspace
3. Fetch PR #`{{arg2}}` from GitHub origin
4. Detect the base branch (main or master)
5. Generate diff between base branch and the PR branch
6. Create output directory: `{output_dir}/pr-{{arg2}}/`
7. Save PR metadata to `{output_dir}/pr-{{arg2}}/metadata.json`

**🔧 How to accomplish this:**
- Use your **Bash tool** to navigate directories and run git commands
- Use your **git skill** to handle repository operations
- Search for the repository in: current directory, `../{{arg1}}`, `workspace/{{arg1}}`
- Fetch PR using: `git fetch origin pull/{{arg2}}/head:pr-{{arg2}}`
- Detect base branch autonomously (check for main vs master)
- Generate diff and save to `{output_dir}/pr-{{arg2}}/pr.diff`

**📋 Expected metadata.json format:**
```json
{
  "pr_number": "{{arg2}}",
  "repository": "{{arg1}}",
  "analyzed_at": "2025-10-19T14:30:00Z",
  "base_branch": "main"
}
```

**📢 Present status to user:**
```
🔍 RESILIENCE AGENT - PR ANALYSIS

Repository: {{arg1}}
PR Number: {{arg2}}
Output Directory: output/pr-{{arg2}}/

Starting analysis...
```

**❌ If repository not found:**
Report clear error with searched locations and suggest cloning the repo.

**❌ If PR not found:**
Report that PR #{{arg2}} doesn't exist or cannot be fetched from origin.

---

### 🌳 Phase 2: Launch AST Fact Extractor

**🚀 Launch the fact-extractor subagent using the Task tool.**

**📝 Prompt for fact-extractor agent:**
```
Extract AST facts from changed files in PR #{{arg2}}.

Context:
- Repository: {{arg1}}
- Repository path: (use the path you found in Phase 1)
- PR Number: {{arg2}}
- Changed files: Parse {output_dir}/pr-{{arg2}}/pr.diff to identify changed files
- Output directory: {output_dir}/pr-{{arg2}}/facts/
- Fact schema: .claude/templates/fact-schema.json

Your mission:
1. Discover and verify Tree-sitter MCP tools (fail-fast if unavailable)
2. Register repository as project with Tree-sitter
3. Extract semantic facts from each changed source file (.java, .py, .ts, .kt)
4. Build fact JSON following .claude/templates/fact-schema.json
5. Save to {output_dir}/pr-{{arg2}}/facts/{filename}.json

Follow your agent instructions in .claude/agents/fact-extractor.md
```

**⏳ Wait for the fact-extractor agent to complete.**

Verify that `{output_dir}/pr-{{arg2}}/facts/` directory exists and contains JSON files.

**❌ If agent fails:**
- Check if Tree-sitter MCP server is configured (see .mcp.json)
- Check if repository path is correct
- Display fact-extractor error message
- Suggest fallback to main branch (grep-based analysis)

---

### 🔬 Phase 3: Invoke Risk Analyzer

**🚀 Launch the risk-analyzer subagent using the Task tool.**

**📝 Prompt for risk-analyzer agent:**
```
Analyze PR #{{arg2}} in repository {{arg1}} for Change Risk & Test Recommendations using AST-extracted facts.

Context:
- Repository: {{arg1}}
- PR Number: {{arg2}}
- PR Diff: {output_dir}/pr-{{arg2}}/pr.diff
- AST Facts: {output_dir}/pr-{{arg2}}/facts/ (JSON files per changed file)
- Output: {output_dir}/pr-{{arg2}}/risk-analysis.json

Your mission (v2.0 AST-Based):
1. Load AST fact files from {output_dir}/pr-{{arg2}}/facts/
2. Apply LLM reasoning to facts:
   - Detect HTTP/RPC calls without timeouts (reason from naming patterns)
   - Detect missing circuit breakers on external calls
   - Detect blocking calls in async contexts
   - Detect breaking API changes (endpoint/DTO modifications)
   - Reason about UNKNOWN custom libraries using semantic patterns
3. Run fan-in/fan-out analysis (context enrichment):
   - Count callers of changed methods
   - Identify external service dependencies
   - Determine user-facing vs internal paths
4. Contextualize severity based on blast radius:
   - High fan-in + missing timeout → upgrade severity
   - User-facing endpoint → upgrade severity
   - Low traffic admin tool → downgrade severity
5. Use the Git Risk Analysis skill to enhance findings:
   - Check code churn (hotspot detection)
   - Check rollback history
   - Add git metrics to risk scoring
6. Recommend specific tests for each finding
7. **Use the Write tool** to save findings as JSON to {output_dir}/pr-{{arg2}}/risk-analysis.json
   - Do NOT return JSON in conversation text
   - You MUST use the Write tool to create the file
   - Verify the file was written successfully

**Key Innovation**: You reason from facts (dependencies, call semantics) extracted via AST, not hardcoded library lists. This lets you detect risks in unknown custom/internal libraries.

Follow your agent instructions in .claude/agents/risk-analyzer.md (v2.0 AST-Based)
```

**⏳ Wait for the risk-analyzer agent to complete.**

Verify that `{output_dir}/pr-{{arg2}}/risk-analysis.json` exists and is valid JSON.

**❌ If agent fails:**
- Display error message
- Show which phase failed
- Suggest checking agent logs or PR diff

---

### ✅ Phase 4: Quality Gate (Critic Agent)

**🚀 Launch the critic-agent subagent using the Task tool.**

**📝 Prompt for critic-agent:**
```
Validate the risk analysis findings for PR #{{arg2}}.

Context:
- Risk Analysis: {output_dir}/pr-{{arg2}}/risk-analysis.json
- Repository: {{arg1}}
- PR Number: {{arg2}}
- Output: {output_dir}/pr-{{arg2}}/final-report.md

Your mission:
1. Read the risk analysis JSON file using the Read tool
2. Validate finding quality:
   - All findings have file:line references
   - Recommendations are actionable
   - Severity levels are justified
   - No false positives
3. Filter out any low-confidence or irrelevant findings
4. Synthesize final report with:
   - Executive summary
   - Critical findings (CRITICAL/HIGH severity)
   - Test recommendations grouped by type
   - Merge recommendation: APPROVE / REQUEST_CHANGES / APPROVE_WITH_TESTS
5. **Use the Write tool** to save final report as Markdown to {output_dir}/pr-{{arg2}}/final-report.md
   - Do NOT return report in conversation text
   - You MUST use the Write tool to create the file
   - Verify the file was written successfully

Follow your agent instructions in .claude/agents/critic-agent.md
```

**⏳ Wait for the critic-agent to complete.**

Verify that `{output_dir}/pr-{{arg2}}/final-report.md` exists.

---

### 📊 Phase 5: Present Results

**📖 Read and display the final report to the user.**

Show the complete final report from `{output_dir}/pr-{{arg2}}/final-report.md`.

**📌 Add footer:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 ANALYSIS COMPLETE

Repository: {{arg1}}
PR Number: {{arg2}}

All artifacts saved to: {output_dir}/pr-{{arg2}}/
- metadata.json
- pr.diff
- facts/*.json
- risk-analysis.json
- final-report.md

To review detailed findings:
  cat {output_dir}/pr-{{arg2}}/risk-analysis.json

To review final report:
  cat {output_dir}/pr-{{arg2}}/final-report.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚨 Error Handling Guidelines

**❌ Repository not found:**
- Search in multiple locations autonomously
- Provide helpful error with searched paths
- Suggest: `git clone https://github.com/org/{{arg1}}.git`

**❌ PR not found:**
- Attempt to fetch from origin
- Check if branch already exists locally
- Provide clear error if PR doesn't exist on remote

**❌ Agent failures:**
- Display which agent failed (risk-analyzer or critic-agent)
- Show partial results if any JSON files were created
- Suggest checking agent prompts or diff content

**❌ Invalid diff:**
- If diff is empty, warn user that no changes detected
- Suggest checking if PR branch is ahead of base branch

---

## 🎯 Success Criteria

Your orchestration is successful when:
- ✅ Repository found and PR fetched successfully
- ✅ Diff generated and saved
- ✅ Output directory created: `{output_dir}/pr-{{arg2}}/`
- ✅ fact-extractor agent extracted AST facts successfully
- ✅ Facts directory created with JSON files: `{output_dir}/pr-{{arg2}}/facts/*.json`
- ✅ risk-analyzer agent completed with valid JSON output
- ✅ critic-agent validated findings and generated final report
- ✅ User receives actionable recommendations
- ✅ All artifacts saved to output directory
- ✅ Clear merge recommendation provided (APPROVE/REQUEST_CHANGES)

---

## 🎭 Agent Coordination Notes

**🎯 You are the orchestrator, not the analyst.**
- Your job is to coordinate the workflow
- Launch subagents using the Task tool
- Don't perform the analysis yourself
- Trust the risk-analyzer to use its git skill
- Trust the critic-agent to validate quality

**📂 Subagent locations:**
- Fact Extractor: `.claude/agents/fact-extractor.md`
- Risk Analyzer: `.claude/agents/risk-analyzer.md`
- Critic Agent: `.claude/agents/critic-agent.md`

**🛠️ Skills available to subagents:**
- Git Risk Analysis: `.claude/skills/git-risk-analysis/SKILL.md`

Use your Bash tool autonomously to accomplish setup tasks. Be intelligent about finding repositories and handling edge cases.
