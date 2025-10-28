# Agent Tools Configuration Strategy

## Understanding the `tools:` Field in Subagents

According to [Claude Code documentation](https://docs.claude.com/en/docs/claude-code/sub-agents), the `tools:` field in agent YAML frontmatter controls tool access:

### When `tools:` Field is OMITTED
- ✅ Agent inherits **ALL tools** from main thread
- ✅ Includes **ALL MCP server tools** (e.g., Tree-sitter, filesystem, etc.)
- ✅ Maximum flexibility
- ⚠️ Less security isolation (agent has broad tool access)

### When `tools:` Field is SPECIFIED
```yaml
tools: Read, Bash, Glob
```
- ✅ Agent gets **ONLY** the listed tools
- ❌ **NO MCP tool inheritance** (even if MCP servers are configured)
- ✅ More granular control
- ✅ Better security isolation (principle of least privilege)

---

## Our Configuration Strategy

### Agents WITHOUT `tools:` Field (Inherit MCP Tools)

**1. fact-extractor** (`/.claude/agents/fact-extractor.md`)
- **Why**: Needs MCP Tree-sitter tools for AST parsing
- **MCP tools required**:
  - `mcp__tree_sitter__register_project_tool`
  - `mcp__tree_sitter__get_symbols`
  - `mcp__tree_sitter__get_dependencies`
  - `mcp__tree_sitter__run_query`
  - ~50+ other Tree-sitter tools
- **Security trade-off**: Acceptable - fact extraction is core functionality

**2. risk-analyzer** (`/.claude/agents/risk-analyzer.md`)
- **Why**: May need MCP Tree-sitter tools for deep analysis
- **Use case**: If fact files are incomplete, can query AST directly
- **Security trade-off**: Acceptable - risk analysis is core functionality

---

### Agents WITH Explicit `tools:` Field (No MCP Inheritance)

**1. critic-agent** (`/.claude/agents/critic-agent.md`)
```yaml
tools: Read, Write
```
- **Why**: Only validates JSON and writes reports - no MCP tools needed
- **Security benefit**: Limited tool access reduces attack surface

**2. change-risk** (`/.claude/agents/change-risk.md`)
```yaml
tools: Read, Grep, Glob
```
- **Why**: Grep-based pattern matching - no AST parsing needed
- **Note**: This is v1.0 grep-based agent (legacy)

**3. config-reviewer** (`/.claude/agents/config-reviewer.md`)
```yaml
tools: Read, Grep, Glob, Bash
```
- **Why**: Reviews configuration files via text search - no AST needed

**4. observability-reviewer** (`/.claude/agents/observability-reviewer.md`)
```yaml
tools: Read, Grep, Glob, Bash
```
- **Why**: Reviews observability configs via text search - no AST needed

---

## Best Practices

### When to OMIT `tools:` Field
✅ Agent needs MCP server tools (e.g., Tree-sitter, database, API clients)
✅ Agent's core functionality depends on external integrations
✅ You want agent to adapt to newly added MCP servers automatically

### When to SPECIFY `tools:` Field
✅ Agent only needs basic Claude Code tools (Read, Write, Bash, Grep)
✅ Security isolation is important (principle of least privilege)
✅ Agent's tool requirements are well-defined and won't change

### Warning Signs You Need to Remove `tools:`
- ❌ Agent instructions mention using MCP tools but they're not available
- ❌ Error messages like "Tree-sitter MCP tools not found"
- ❌ Agent can't perform its core function due to missing tools

---

## Migration Guide: Adding MCP Support to Existing Agent

**Before** (Blocked from MCP):
```yaml
---
name: my-agent
description: Does something with AST parsing
tools: Read, Bash, Glob
model: sonnet
---
```

**After** (Inherits MCP):
```yaml
---
name: my-agent
description: Does something with AST parsing
# tools field omitted to inherit ALL tools including MCP Tree-sitter tools
model: sonnet
---
```

**Result**: Agent can now access all MCP tools configured in `.mcp.json`

---

## Debugging Tool Access Issues

### Check if agent has MCP tools:
1. Look at agent's YAML frontmatter
2. If `tools:` field exists → Agent ONLY has those tools (no MCP)
3. If `tools:` field is missing → Agent inherits all tools + MCP

### Verify MCP server is configured:
```bash
# Check .mcp.json in project root
cat .mcp.json

# Expected: tree_sitter server configured
{
  "mcpServers": {
    "tree_sitter": {
      "command": "python",
      "args": ["-m", "mcp_server_tree_sitter.server"]
    }
  }
}
```

### Test MCP tool access in main thread:
If the orchestrator (main thread) can see MCP tools, subagents with omitted `tools:` field will inherit them.

---

## Related Documentation

- [Claude Code Subagents Documentation](https://docs.claude.com/en/docs/claude-code/sub-agents)
- [MCP Server Configuration](../.mcp.json)
- [Project Architecture](ARCHITECTURE.md)
