#!/usr/bin/env python3
"""Test fixed Java query templates."""

from tree_sitter_language_pack import get_language, get_parser

# Sample Java with more test cases
JAVA_SAMPLE = """
package org.example;

import java.util.List;
import org.springframework.web.bind.annotation.*;

@RestController
public class TestController {

    public TestController() {
        // Constructor
    }

    @GetMapping("/test")
    public String testMethod() {
        return "test";
    }
}

public interface TestInterface {
    void method();
}
"""

# ORIGINAL (BROKEN) templates from java.py
ORIGINAL_TEMPLATES = {
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
    "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name
            body: (class_body) @interface.body) @interface.def
    """,
}

# FIXED templates based on AST inspection
FIXED_TEMPLATES = {
    "functions": """
        (method_declaration
            name: (identifier) @function.name) @function

        (constructor_declaration
            name: (identifier) @constructor.name) @constructor
    """,
    "classes": """
        (class_declaration
            name: (identifier) @class.name) @class
    """,
    "interfaces": """
        (interface_declaration
            name: (identifier) @interface.name) @interface
    """,
    "imports": """
        (import_declaration) @import
    """,
    "annotations": """
        (marker_annotation
            name: (identifier) @annotation.name) @annotation

        (annotation
            name: (identifier) @annotation.name) @annotation
    """,
}


def test_templates(templates, label):
    """Test a set of templates."""
    language = get_language('java')
    parser = get_parser('java')

    source = JAVA_SAMPLE.encode('utf-8')
    tree = parser.parse(source)

    print("=" * 80)
    print(f"{label}")
    print("=" * 80)

    for name, query_str in templates.items():
        print(f"\n📋 {name}:")
        try:
            query = language.query(query_str)
            captures = query.captures(tree.root_node)

            if isinstance(captures, dict):
                total = sum(len(nodes) for nodes in captures.values())
                print(f"  ✅ SUCCESS - {total} total captures")

                for capture_name, nodes in captures.items():
                    print(f"    '{capture_name}': {len(nodes)} nodes")
                    for node in nodes[:2]:  # First 2
                        text = source[node.start_byte:node.end_byte].decode('utf-8')
                        # Clean up text for display
                        text = text.split('\n')[0][:60]
                        print(f"      - {text}")
            else:
                print(f"  ℹ️ Captures: {type(captures)}")

        except Exception as e:
            print(f"  ❌ FAILED - {type(e).__name__}: {e}")


def main():
    print("\n\n")
    test_templates(ORIGINAL_TEMPLATES, "ORIGINAL (BROKEN) TEMPLATES")
    print("\n\n")
    test_templates(FIXED_TEMPLATES, "FIXED TEMPLATES")


if __name__ == "__main__":
    main()
