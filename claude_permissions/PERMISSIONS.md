# Permissions Configuration for Autonomous Agent Runs

This directory contains the permissions template for running `/analyze-pr` autonomously without manual approval prompts.

## Quick Setup

**Copy the template to your local Claude settings:**

```bash
# macOS/Linux
cp claude_permissions/settings.local.json ~/.claude/settings.local.json

# Windows
copy claude_permissions\settings.local.json.tmpl %USERPROFILE%\.claude\settings.local.json
```

**Result:** Run `/analyze-pr {PR_NUMBER}` without any permission prompts!

---

## What Gets Pre-Approved

The template pre-approves the following tool categories:

### 1. Git Operations

**Patterns:**
```json
"Bash(git fetch:*)"
"Bash(git checkout:*)"
"Bash(git diff:*)"
"Bash(git log:*)"
"Bash(git show:*)"
"Bash(git branch:*)"
"Bash(git merge-base:*)"
"Bash(git show-ref:*)"
"Bash(git shortlog:*)"
```

**What they do:**
- Fetch PR branches from remote
- Checkout branches for analysis
- View diffs between branches
- Examine commit history
- Find merge bases
- Check branch references
- Generate author statistics for git-risk-analysis

**Safety:** Read-only operations, no destructive actions (no push, no force, no delete)

---

### 2. GitHub CLI

**Pattern:**
```json
"Bash(gh pr view:*)"
```

**What it does:**
- Fetches PR metadata (title, body, files changed, additions/deletions)
- Used by orchestrator to get PR context

**Safety:** Read-only, no modifications to GitHub

---

### 3. Directory Operations

**Pattern:**
```json
"Bash(mkdir:*)"
```

**What it does:**
- Creates `output/pr-{NUMBER}/` directory structure
- Creates `output/pr-{NUMBER}/facts/` for AST extractions

**Safety:** Only creates directories, doesn't delete anything

---

### 4. File Operations

**Patterns:**
```json
"Bash(cat:*)"
"Bash(grep:*)"
"Bash(wc:*)"
```

**What they do:**
- `cat`: Read JSON files, diffs, and analysis outputs
- `grep`: Search through files (used by fact-extractor)
- `wc`: Count lines (used by git-risk-analysis)

**Safety:** Read-only file operations

---

### 5. Read Permissions

**Patterns:**
```json
"Read(output/**)"
"Read(.claude/**)"
"Read(templates/**)"
"Read(workspace/**)"
```

**What they do:**
- `output/**`: Read analysis results (risk-analysis.json, metadata.json)
- `.claude/**`: Read agent configurations and templates
- `templates/**`: Read report templates (template-final-report.md)
- `workspace/**`: Read repository source code for analysis

**Safety:** Read-only, no file modifications

---

### 6. Write Permissions

**Pattern:**
```json
"Write(output/**)"
```

**What it does:**
- Write analysis outputs to `output/pr-{NUMBER}/` directory
- Examples: metadata.json, pr.diff, risk-analysis.json, final-report.md, facts/*.json

**Safety:** Sandboxed to `output/` directory only, cannot write to source code or system files

---

### 7. MCP Tree-sitter Tools

**Patterns:**
```json
"mcp__tree_sitter__register_project_tool"
"mcp__tree_sitter__get_symbols"
"mcp__tree_sitter__get_dependencies"
"mcp__tree_sitter__run_query"
"mcp__tree_sitter__list_languages"
"mcp__tree_sitter__get_file"
"mcp__tree_sitter__find_usage"
"mcp__tree_sitter__list_projects_tool"
```

**What they do:**
- Register project for AST analysis
- Extract symbols (functions, classes, methods)
- Extract dependencies (imports, includes)
- Run tree-sitter queries for pattern detection
- Find symbol usage (fan-in analysis)
- List supported languages

**Safety:** Read-only AST parsing, no code modification

---

### 8. Skills and Slash Commands

**Patterns:**
```json
"Skill(git-risk-analysis)"
"SlashCommand(/analyze-pr:*)"
```

**What they do:**
- `Skill(git-risk-analysis)`: Analyze git history for code hotspots, churn rates, authorship patterns
- `SlashCommand(/analyze-pr:*)`: Main command for PR analysis

**Safety:** Coordinated workflow execution, read-only operations

---

## MCP Server Configuration

**Patterns:**
```json
"enableAllProjectMcpServers": true
"enabledMcpjsonServers": ["tree_sitter"]
```

**What they do:**
- Enable all MCP servers defined in project settings
- Specifically enable the tree-sitter MCP server for AST parsing

**Safety:** Project-scoped MCP servers only

---

## What Gets Blocked (Deny List)

The template includes a `deny` list that explicitly blocks dangerous operations. These provide safety guardrails and will **never execute**, even if accidentally added to the `allow` list.

### File Deletion
```json
"Bash(rm:*)"
"Bash(rm -rf:*)"
```
**Why blocked:** Prevents accidental deletion of files or directories.

### Destructive Git Operations
```json
"Bash(git push:*)"
"Bash(git push --force:*)"
"Bash(git reset --hard:*)"
"Bash(git clean:*)"
"Bash(git rebase:*)"
```
**Why blocked:**
- `git push`: Prevents pushing code to remote (analysis should be local-only)
- `git push --force`: Prevents force-pushing and overwriting remote history
- `git reset --hard`: Prevents discarding uncommitted changes
- `git clean`: Prevents deleting untracked files
- `git rebase`: Prevents history manipulation during analysis

### System-Level Operations
```json
"Bash(sudo:*)"
"Bash(chmod:*)"
"Bash(chown:*)"
```
**Why blocked:**
- `sudo`: Prevents privilege escalation
- `chmod`/`chown`: Prevents permission and ownership changes

### Source Code Writes
```json
"Write(src/**)"
"Write(.git/**)"
"Write(.claude/**)"
"Write(../**)"
```
**Why blocked:**
- `src/**`: Prevents modifying source code (analysis should be read-only)
- `.git/**`: Prevents corrupting git repository
- `.claude/**`: Prevents modifying agent configurations
- `../**`: Prevents writing outside project directory

**These blocks ensure the agent cannot:**
- Modify your source code
- Push changes to remote repositories
- Delete files or directories
- Corrupt your git history
- Escalate privileges
- Escape the project sandbox

---

## Permission Categories

Claude Code has three permission categories:

### 1. `allow` (Pre-approved)
- Tools execute immediately without prompts
- Used for safe, read-only operations
- This template pre-approves all analyze-pr workflow tools

### 2. `deny` (Blocked)
- Tools are explicitly blocked and will never execute
- Pre-populated with dangerous operations for safety
- Provides guardrails against accidental destructive actions

### 3. `ask` (Prompt user)
- Tools prompt for approval before execution
- Empty by default (everything goes to `allow`)
- Default fallback if a tool isn't in `allow` or `deny`

---

## Security Considerations

### What's Safe

**All pre-approved operations are read-only except for:**
- Writing to `output/` directory (sandboxed analysis outputs)
- Creating directories in `output/` (non-destructive)

**Destructive operations are explicitly blocked in the `deny` list:**
- ❌ `rm` and `rm -rf` (file deletion)
- ❌ `git push` and `git push --force` (prevents pushing code)
- ❌ `git reset --hard` (prevents history rewriting)
- ❌ `git clean` (prevents untracked file deletion)
- ❌ `git rebase` (prevents history manipulation)
- ❌ `sudo` (prevents privilege escalation)
- ❌ `chmod` and `chown` (prevents permission changes)
- ❌ Writing to `src/**`, `.git/**`, `.claude/**` (prevents source modification)
- ❌ Writing to parent directories `../**` (prevents escaping project)

### Wildcard Patterns

The template uses wildcards (`*`) for flexibility:
- `git fetch:*` matches any PR number or branch
- `Read(output/**)` matches any path under `output/`
- `SlashCommand(/analyze-pr:*)` matches any PR number

This ensures the template works for all PRs without hardcoding specific numbers.

---

## Platform Compatibility

### Windows Users

**Requirements:**
- Git for Windows (https://git-scm.com/download/win)
- Claude Code's Bash tool uses Git Bash automatically on Windows

**All patterns work identically on:**
- ✅ Windows (with Git for Windows)
- ✅ macOS
- ✅ Linux
- ✅ WSL (Windows Subsystem for Linux)

**Why it works:**
- Claude Code uses tool abstractions (Bash, Read, Write, Grep, Glob)
- Git commands work cross-platform
- Forward slashes in paths work on all platforms

---

## Customization

### Adding More Permissions

Edit your `~/.claude/settings.local.json` and add patterns to the `allow` array:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm install:*)",
      "Bash(pytest:*)",
      "Read(src/**)"
    ]
  }
}
```

### Blocking Operations

Add patterns to the `deny` array:

```json
{
  "permissions": {
    "deny": [
      "Bash(rm:*)",
      "Bash(git push:*)"
    ]
  }
}
```

### Requiring Approval

Add patterns to the `ask` array:

```json
{
  "permissions": {
    "ask": [
      "Write(src/**)",
      "Bash(git commit:*)"
    ]
  }
}
```

---

## Troubleshooting

### Still Getting Permission Prompts?

1. **Check file location:** Settings must be at `~/.claude/settings.local.json` (not in project directory)

2. **Validate JSON syntax:** Use a JSON validator or `python3 -m json.tool ~/.claude/settings.local.json`

3. **Check pattern match:** Ensure the tool call matches your pattern exactly
   - Example: If Claude Code calls `Bash(git fetch origin pull/123/head:pr-123)`, it should match `Bash(git fetch:*)`

4. **Restart Claude Code:** Changes to settings require a restart

### Pattern Not Matching?

Claude Code permission patterns use exact tool names:
- ✅ `Bash(git fetch:*)` - Correct
- ❌ `bash(git fetch:*)` - Incorrect (lowercase)
- ❌ `Git(fetch:*)` - Incorrect (wrong tool name)

---

## What Each Agent Uses

### Orchestrator (analyze-pr.md)
- Git operations (fetch, checkout, diff)
- GitHub CLI (gh pr view)
- Directory creation (mkdir)
- Read/Write (metadata, pr.diff)

### Fact Extractor (fact-extractor.md)
- MCP tree-sitter tools (AST parsing)
- Read (source code files)
- Write (facts/*.json)
- Bash (grep for file filtering)

### Risk Analyzer (risk-analyzer.md)
- Read (facts/*.json, fact-schema.json)
- Write (risk-analysis.json)
- MCP tree-sitter (fan-in analysis)
- Skill (git-risk-analysis for code hotspots)

### Critic Agent (critic-agent.md)
- Read (risk-analysis.json, template-final-report.md)
- Write (final-report.md)

---

## Complete Workflow Permissions

When you run `/analyze-pr 123`, the workflow uses:

1. **Git fetch** → `Bash(git fetch:*)`
2. **Git checkout** → `Bash(git checkout:*)`
3. **Create output directory** → `Bash(mkdir:*)`, `Write(output/**)`
4. **Fetch PR metadata** → `Bash(gh pr view:*)`
5. **Generate PR diff** → `Bash(git diff:*)`, `Write(output/**)`
6. **Register project** → `mcp__tree_sitter__register_project_tool`
7. **Extract AST facts** → `mcp__tree_sitter__get_symbols`, `mcp__tree_sitter__get_dependencies`, etc.
8. **Analyze git history** → `Skill(git-risk-analysis)`, `Bash(git log:*)`, `Bash(git shortlog:*)`
9. **Generate risk analysis** → `Read(output/**)`, `Write(output/**)`
10. **Synthesize final report** → `Read(templates/**)`, `Read(output/**)`, `Write(output/**)`

All of these are pre-approved by the template, enabling fully autonomous execution.

---

## Support

If you encounter issues with permissions:
1. Check the troubleshooting section above
2. Review the pattern syntax in your settings file
3. Open an issue with the specific permission prompt you're seeing
