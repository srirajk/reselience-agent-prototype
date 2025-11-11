"""Query templates for Java language."""

TEMPLATES = {
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
    "enums": """
        (enum_declaration
            name: (identifier) @enum.name) @enum
    """,
}
