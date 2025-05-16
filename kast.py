class ASTNode:
    pass

class TypeDefinition(ASTNode):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields
    def __repr__(self):
        return f"TypeDefinition(name={self.name!r}, fields={self.fields!r})"

class SetDefinition(ASTNode):
    def __init__(self, name, expr, type_name=None):
        self.name = name
        self.expr = expr
        self.type_name = type_name
    def __repr__(self):
        return f"SetDefinition(name={self.name!r}, type={self.type_name!r}, expr={self.expr!r})"

class SetOperation(ASTNode):
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self):
        return f"SetOperation(left={self.left!r}, op={self.op!r}, right={self.right!r})"

class Identifier(ASTNode):
    def __init__(self, name):
        self.name = name
    def __repr__(self):
        return f"Identifier({self.name!r})"

class LiteralSet(ASTNode):
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return f"LiteralSet({self.elements!r})"

class TupleLiteral(ASTNode):
    def __init__(self, elements):
        self.elements = elements
    def __repr__(self):
        return f"TupleLiteral({self.elements!r})"

class RecordInstanceLiteral(ASTNode):
    def __init__(self, field_assignments):
        # field_assignments is a list of (field_name_str, value_node)
        self.field_assignments = field_assignments
    def __repr__(self):
        return f"RecordInstanceLiteral(fields={self.field_assignments!r})"

class NumberLiteralNode(ASTNode):
    def __init__(self, lexeme_value):
        # Try to convert to int, then float
        try:
            self.value = int(lexeme_value)
        except ValueError:
            try:
                self.value = float(lexeme_value)
            except ValueError:
                # This should ideally not happen if the lexer correctly identifies numbers
                raise ValueError(f"Invalid number literal: {lexeme_value}")
        # self.type = 'number' # You can add more specific type info if needed, e.g., 'int' or 'float'

    def __repr__(self):
        return f"NumberLiteralNode({self.value})"

class StringLiteralNode(ASTNode):
    def __init__(self, value):
        self.value = value
    def __repr__(self):
        return f"StringLiteralNode({self.value!r})"

class SetComprehension(ASTNode):
    def __init__(self, out_vars, in_vars, source, predicate=None): # MODIFIED: Added predicate
        self.out_vars = out_vars
        self.in_vars = in_vars
        self.source = source
        self.predicate = predicate # NEW: AST node for the predicate expression (or None)
    def __repr__(self):
        return f"SetComprehension(out_vars={self.out_vars!r}, in_vars={self.in_vars!r}, source={self.source!r}, predicate={self.predicate!r})"

# --- New AST Nodes for Phase 2: Predicate Expressions ---

class AttributeAccess(ASTNode):
    """Represents accessing an attribute of an object, e.g., record.field"""
    def __init__(self, obj_expr, attribute_name_token):
        self.obj_expr = obj_expr  # The expression for the object (e.g., Identifier('person'))
        self.attribute_name = attribute_name_token.lexeme # The name of the attribute (string)
        # Store token for potential error reporting (line/column)
        self.attribute_name_token = attribute_name_token 
    def __repr__(self):
        return f"AttributeAccess(obj={self.obj_expr!r}, attr={self.attribute_name!r})"

class Comparison(ASTNode):
    """Represents a comparison operation, e.g., left_expr > right_expr"""
    def __init__(self, left_expr, operator_token, right_expr):
        self.left_expr = left_expr
        self.operator = operator_token.lexeme # The operator as a string (e.g., ">", "==")
        self.right_expr = right_expr
        # Store token for potential error reporting or specific operator type
        self.operator_token = operator_token 
    def __repr__(self):
        return f"Comparison(left={self.left_expr!r}, op={self.operator!r}, right={self.right_expr!r})"

# --- End of New AST Nodes for Phase 2 ---