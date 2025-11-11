#!/usr/bin/env python3
"""Inspect Java AST structure to find correct node types."""

from tree_sitter_language_pack import get_language, get_parser

# Sample Java file
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


def print_ast(node, source, depth=0, max_depth=8):
    """Recursively print AST structure."""
    if depth > max_depth:
        return

    indent = "  " * depth
    node_text = source[node.start_byte:node.end_byte].decode('utf-8')
    # Only show first 50 chars
    node_text = node_text.replace('\n', '\\n')[:50]

    print(f"{indent}{node.type} [{node.start_point[0]}:{node.start_point[1]}] {node_text!r}")

    for child in node.children:
        print_ast(child, source, depth + 1, max_depth)


def main():
    language = get_language('java')
    parser = get_parser('java')

    # Parse sample
    source = JAVA_SAMPLE.encode('utf-8')
    tree = parser.parse(source)

    print("=" * 80)
    print("Java AST Structure")
    print("=" * 80)
    print_ast(tree.root_node, source)

    print("\n" + "=" * 80)
    print("Looking for specific patterns:")
    print("=" * 80)

    # Test specific queries
    queries = {
        "imports (scoped_identifier)": "(import_declaration (scoped_identifier) @import)",
        "imports (all)": "(import_declaration) @import",
        "method_declaration": "(method_declaration) @method",
        "constructor_declaration": "(constructor_declaration) @constructor",
    }

    for name, query_str in queries.items():
        print(f"\n{name}:")
        try:
            query = language.query(query_str)
            captures = query.captures(tree.root_node)
            print(f"  ✅ Query parsed, captures type: {type(captures)}")

            # Handle dict format: {capture_name: [nodes]}
            if isinstance(captures, dict):
                total = sum(len(nodes) for nodes in captures.values())
                print(f"  ✅ Found {total} total captures across {len(captures)} capture names")
                for capture_name, nodes in list(captures.items())[:2]:  # First 2 capture types
                    print(f"    Capture '{capture_name}': {len(nodes)} nodes")
                    for node in nodes[:1]:  # First node of each type
                        text = source[node.start_byte:node.end_byte].decode('utf-8').replace('\n', ' ')[:60]
                        print(f"      - {text}")
            else:
                print(f"  ℹ️ Unexpected captures format: {type(captures)}")

        except Exception as e:
            print(f"  ❌ {type(e).__name__}: {e}")


if __name__ == "__main__":
    main()
