#!/usr/bin/env python3
"""Test Java query templates from MCP Tree-sitter server."""

import sys
import subprocess
import json

# Sample Java file for testing
JAVA_SAMPLE = """
package org.example;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class TestController {

    @GetMapping("/test")
    public String testMethod() {
        return "test";
    }
}
"""

# Java query templates from java.py
TEMPLATES = {
    "functions": """
        (method_declaration
            name: (identifier) @function.name
            parameters: (formal_parameters) @function.params
            body: (block) @function.body) @function.def

        (constructor_declaration
            name: (identifier) @constructor.name
            parameters: (formal_parameters) @constructor.params
            body: (block) @constructor.body) @constructor.def
    """,
    "classes": """
        (class_declaration
            name: (identifier) @class.name
            body: (class_body) @class.body) @class.def
    """,
    "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name
            body: (class_body) @interface.body) @interface.def
    """,
    "imports": """
        (import_declaration) @import

        (import_declaration
            name: (qualified_name) @import.name) @import.qualified

        (import_declaration
            name: (qualified_name
                name: (identifier) @import.class)) @import.class

        (import_declaration
            asterisk: "*") @import.wildcard
    """,
    "annotations": """
        (annotation
            name: (identifier) @annotation.name) @annotation

        (annotation_type_declaration
            name: (identifier) @annotation.type_name) @annotation.type
    """,
}


def write_sample_file(path="/tmp/TestController.java"):
    """Write sample Java file."""
    with open(path, 'w') as f:
        f.write(JAVA_SAMPLE)
    return path


def test_query_via_mcp(project_name, file_path, query_name, query_string):
    """Test a query using the MCP server's run_query tool."""
    # This would require invoking the MCP server
    # For now, let's use tree-sitter Python directly
    pass


def test_with_tree_sitter():
    """Test queries directly with tree-sitter Python."""
    try:
        from tree_sitter_language_pack import get_language, get_parser

        # Get Java language and parser
        language = get_language('java')
        parser = get_parser('java')

        # Write and parse sample file
        file_path = write_sample_file()
        with open(file_path, 'rb') as f:
            source = f.read()

        tree = parser.parse(source)

        print("=" * 80)
        print("Testing Java Query Templates")
        print("=" * 80)

        # Test each query
        for name, query_str in TEMPLATES.items():
            print(f"\n📋 Testing '{name}' query...")
            print(f"Query:\n{query_str}")

            try:
                query = language.query(query_str)
                captures = query.captures(tree.root_node)
                print(f"✅ SUCCESS - Found {len(captures)} captures")

                # Show first few captures
                for i, (node, capture_name) in enumerate(captures[:3]):
                    text = source[node.start_byte:node.end_byte].decode('utf-8')
                    print(f"  - {capture_name}: {text[:50]}...")

            except Exception as e:
                print(f"❌ FAILED - {type(e).__name__}: {e}")

        print("\n" + "=" * 80)

    except ImportError as e:
        print(f"❌ tree-sitter-language-pack not installed: {e}")
        print("Install with: pip install tree-sitter-language-pack")
        return False

    return True


if __name__ == "__main__":
    success = test_with_tree_sitter()
    sys.exit(0 if success else 1)
