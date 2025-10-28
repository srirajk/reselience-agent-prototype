# MCP Tree-sitter Java Template Fix

## File Location

**Replace this file in your MCP Tree-sitter server:**

```
src/mcp_server_tree_sitter/language/templates/java.py
```

## What This Fixes

This fixes the "Impossible pattern" and "Invalid node type" errors when the fact-extractor agent tries to use Tree-sitter to parse Java code.

**Problems Fixed:**
1. Removed field syntax (`name:`, `body:`, `parameters:`) that caused "Impossible pattern" errors
2. Changed `qualified_name` to `scoped_identifier` (correct Java grammar node type)
3. Added support for `marker_annotation` (annotations without parameters like `@Component`)

## Instructions

**Prerequisites:** You must have the MCP Tree-sitter server installed. If not installed yet:

```bash
# Clone the MCP Tree-sitter server
git clone https://github.com/your-org/mcp-server-tree-sitter.git
cd mcp-server-tree-sitter

# Install dependencies (requires Python 3.10+)
pip install -e .
```

See [Getting Started Guide](../docs/AST/getting-started.md#2-mcp-tree-sitter-server) for full installation instructions.

**Apply the Fix:**

1. Locate your MCP Tree-sitter server installation directory (where you cloned it above)
2. Navigate to: `src/mcp_server_tree_sitter/language/templates/`
3. Replace `java.py` with the version in this directory
4. Restart Claude Code to reload the MCP server

## Verification

After replacing, the fact-extractor should successfully parse Java files without errors:

```
 Tree-sitter MCP tools available
 Project registered successfully
 All Java files analyzed (no "Impossible pattern" errors)
```
