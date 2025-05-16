import ktokens
from kast import (
    TypeDefinition, SetDefinition, Identifier, TupleLiteral, LiteralSet,
    SetOperation, SetComprehension, RecordInstanceLiteral, NumberLiteralNode, StringLiteralNode,
    AttributeAccess, Comparison # Ensure all AST nodes used are imported
)

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        if not self.tokens or self.tokens[-1].token_type != ktokens.TokenType.EOF:
            # Assuming lexer might not always append EOF or list could be empty.
            # A robust lexer should always give a clear EOF.
            # If tokens can be truly empty, current() needs to handle it.
            pass


    def current(self):
        if self.current_token_index < len(self.tokens):
            return self.tokens[self.current_token_index]
        # This case should ideally be prevented by checking for EOF in loops.
        # If lexer guarantees an EOF token, this might return it.
        # Fallback to a dummy EOF if absolutely necessary, but better to ensure tokens list is valid.
        if self.tokens and self.tokens[-1].token_type == ktokens.TokenType.EOF:
            return self.tokens[-1]
        # This indicates a problem if reached when not expecting EOF.
        raise IndexError("Attempted to read past the end of token stream or token stream is empty without EOF.")


    def advance(self):
        token = self.current()
        if token.token_type != ktokens.TokenType.EOF: # Don't advance past EOF
            self.current_token_index += 1
        return token

    def expect(self, expected_type):
        token = self.current()
        if token.token_type == expected_type:
            self.advance()
            return token
        else:
            line = token.line if hasattr(token, 'line') and token.line is not None else "Unknown"
            col = token.column if hasattr(token, 'column') and token.column is not None else "Unknown"
            raise SyntaxError(
                f"Expected token {expected_type.name} but got {token.token_type.name} ('{token.lexeme}') "
                f"at line {line}, column {col}"
            )

    def parse(self):
        statements = []
        while self.current().token_type != ktokens.TokenType.EOF:
            current_tok_type = self.current().token_type
            if current_tok_type == ktokens.TokenType.KEYWORD_TYPE:
                statements.append(self.parse_type_definition())
            elif current_tok_type == ktokens.TokenType.KEYWORD_LET:
                statements.append(self.parse_set_definition())
            else:
                token = self.current()
                line = token.line if hasattr(token, 'line') and token.line is not None else "Unknown"
                col = token.column if hasattr(token, 'column') and token.column is not None else "Unknown"
                raise SyntaxError(
                    f"Unexpected token at top level: '{token.lexeme}' ({token.token_type.name}) "
                    f"at line {line}, column {col}"
                )
        return statements

    def parse_type_definition(self):
        self.expect(ktokens.TokenType.KEYWORD_TYPE)
        name_token = self.expect(ktokens.TokenType.IDENTIFIER)
        self.expect(ktokens.TokenType.COLON)
        
        fields = []
        # Example: type Person: Record(name: string, age: int)
        # Example: type MyTuple: Tuple(string, int)
        # For simplicity, assuming Record for now, extend as needed
        if self.current().token_type == ktokens.TokenType.KEYWORD_RECORD:
            self.advance() # Consume RECORD
            self.expect(ktokens.TokenType.LPAREN)
            if self.current().token_type != ktokens.TokenType.RPAREN:
                while True:
                    field_name = self.expect(ktokens.TokenType.IDENTIFIER).lexeme
                    self.expect(ktokens.TokenType.COLON)
                    field_type_name = self.expect(ktokens.TokenType.IDENTIFIER).lexeme # Assuming type is an identifier
                    fields.append((field_name, field_type_name))
                    if self.current().token_type == ktokens.TokenType.COMMA:
                        self.advance()
                    else:
                        break
            self.expect(ktokens.TokenType.RPAREN)
        # Add parsing for Tuple type definitions if needed
        # elif self.current().token_type == ktokens.TokenType.KEYWORD_TUPLE: ...
        else:
            raise SyntaxError(f"Expected 'Record' or 'Tuple' in type definition, got {self.current().token_type}")
            
        return TypeDefinition(name_token.lexeme, fields)

    def parse_set_definition(self):
        self.expect(ktokens.TokenType.KEYWORD_LET)
        name_token = self.expect(ktokens.TokenType.IDENTIFIER)
        type_name = None
        if self.current().token_type == ktokens.TokenType.COLON:
            self.advance() # Consume COLON
            type_name = self.expect(ktokens.TokenType.IDENTIFIER).lexeme
        self.expect(ktokens.TokenType.EQUALS)
        
        # This is the crucial change: parse the actual set expression
        set_expr_node = self.parse_set_expr() 
        
        return SetDefinition(name_token.lexeme, set_expr_node, type_name)

    def parse_set_expr(self):
        """ Parses a set expression, which can be a literal set, a comprehension, or an identifier,
            potentially followed by set operations.
        """
        # For now, assume a set expression starts with '{' (LiteralSet/Comprehension) or an Identifier
        # This needs to be expanded to handle full expression hierarchy (e.g. A | B where A, B are identifiers)
        
        # Simplified: directly parse literal set or comprehension if '{'
        # Or parse an identifier if it's a set name.
        # A full expression parser would handle A | B, A * C etc. here.
        
        # Let's start with the most common case for definitions: { ... }
        if self.current().token_type == ktokens.TokenType.SET_OPEN:
            node = self.parse_literal_set_or_comprehension()
        elif self.current().token_type == ktokens.TokenType.IDENTIFIER:
            node = Identifier(self.expect(ktokens.TokenType.IDENTIFIER).lexeme)
        else:
            raise SyntaxError(f"Expected set expression (starting with '{{' or identifier), got {self.current().token_type}")

        # Now, check for binary set operations like UNION, INTERSECTION, CROSS_PRODUCT
        while self.current().token_type in (ktokens.TokenType.PIPE, ktokens.TokenType.AMPERSAND, ktokens.TokenType.CROSS):
            op_token = self.advance() # Consume the operator
            # Recursively parse the right-hand side.
            # This simple recursion works for left-associative operators.
            # For precedence, a more structured approach (e.g., Pratt parser or precedence climbing) is needed
            # if mixing with other arithmetic/logical operators. For now, this is okay for set ops.
            
            right_node = None
            if self.current().token_type == ktokens.TokenType.SET_OPEN:
                 right_node = self.parse_literal_set_or_comprehension()
            elif self.current().token_type == ktokens.TokenType.IDENTIFIER:
                 right_node = Identifier(self.expect(ktokens.TokenType.IDENTIFIER).lexeme)
            else:
                raise SyntaxError(f"Expected set expression after operator '{op_token.lexeme}', got {self.current().token_type}")

            node = SetOperation(node, op_token.lexeme, right_node)
        return node


    def parse_literal_set_or_comprehension(self):
        self.expect(ktokens.TokenType.SET_OPEN)
        
        if self.current().token_type == ktokens.TokenType.SET_CLOSE: # Empty set {}
            self.advance()
            return LiteralSet([])

        # This is the first expression: could be an element, or the output_expr of a comprehension
        first_expr_node = self.parse_predicate_expression()

        if self.current().token_type == ktokens.TokenType.PIPE: # It's a comprehension
            self.advance() # Consume PIPE
            
            in_vars_tokens = []
            if self.current().token_type == ktokens.TokenType.LPAREN: # Destructuring like (c1, c2)
                self.advance()
                while True:
                    in_vars_tokens.append(self.expect(ktokens.TokenType.IDENTIFIER))
                    if self.current().token_type == ktokens.TokenType.COMMA:
                        self.advance()
                    elif self.current().token_type == ktokens.TokenType.RPAREN:
                        self.advance()
                        break
                    else:
                        raise SyntaxError("Expected COMMA or RPAREN in comprehension input variables")
            else: # Single variable like p
                in_vars_tokens.append(self.expect(ktokens.TokenType.IDENTIFIER))
            
            in_vars_lexemes = [t.lexeme for t in in_vars_tokens]

            self.expect(ktokens.TokenType.KEYWORD_OF)
            source_node = self.parse_identifier() # Source set must be an identifier for now

            predicate_node = None
            if self.current().token_type == ktokens.TokenType.COMMA: # Optional predicate
                self.advance()
                predicate_node = self.parse_predicate_expression()
            
            self.expect(ktokens.TokenType.SET_CLOSE)

            # The first_expr_node is the output expression. If it was a TupleLiteral, its elements are the output.
            # Otherwise, it's a single output expression.
            out_expr_nodes = []
            if isinstance(first_expr_node, TupleLiteral):
                 out_expr_nodes.extend(first_expr_node.elements)
            else:
                 out_expr_nodes.append(first_expr_node)

            return SetComprehension(out_expr_nodes, in_vars_lexemes, source_node, predicate_node)
        
        else: # It's a literal set
            elements = [first_expr_node]
            while self.current().token_type == ktokens.TokenType.COMMA:
                self.advance()
                if self.current().token_type == ktokens.TokenType.SET_CLOSE: # Trailing comma {}
                    break
                elements.append(self.parse_predicate_expression())
            self.expect(ktokens.TokenType.SET_CLOSE)
            return LiteralSet(elements)

    def parse_identifier(self): # Helper for parsing just an identifier expression
        token = self.expect(ktokens.TokenType.IDENTIFIER)
        return Identifier(token.lexeme)

    # --- Expression Parsing (Predicate Logic) ---
    # This needs to be built out for full Kantor predicate expressions.
    # For now, a simplified version to support literals, identifiers, and basic structures.

    def parse_predicate_expression(self):
        # This will eventually be the entry point for full expression parsing (e.g., with precedence)
        # For now, delegate to comparison or a simpler form.
        return self.parse_comparison()

    def parse_comparison(self):
        # Simplified: parse a term, then optionally a comparison op and another term
        # Does not handle chained comparisons like a < b < c correctly without more structure.
        node = self.parse_term() # parse_term will handle attribute access
        
        while self.current().token_type in (
                ktokens.TokenType.EQUALS_EQUALS, ktokens.TokenType.NOT_EQUAL,
                ktokens.TokenType.LESS, ktokens.TokenType.LESS_EQUAL,
                ktokens.TokenType.GREATER, ktokens.TokenType.GREATER_EQUAL):
            op_token = self.advance()
            right_node = self.parse_term()
            node = Comparison(node, op_token, right_node)
        return node

    def parse_term(self):
        # Handles primary expressions and attribute access, e.g., p or p.name
        # Will need to be expanded for arithmetic terms (+, *) if those are added.
        node = self.parse_primary_predicate_expr()
        
        while self.current().token_type == ktokens.TokenType.DOT:
            dot_token = self.advance()
            attribute_name_token = self.expect(ktokens.TokenType.IDENTIFIER)
            node = AttributeAccess(node, attribute_name_token)
        return node

    def parse_primary_predicate_expr(self):
        token = self.current()

        if token.token_type == ktokens.TokenType.NUMBER:
            self.advance()
            return NumberLiteralNode(token.lexeme) # Assumes NumberLiteralNode handles conversion
        elif token.token_type == ktokens.TokenType.STRING:
            self.advance()
            return StringLiteralNode(token.lexeme)
        elif token.token_type == ktokens.TokenType.IDENTIFIER:
            return self.parse_identifier() # Use the helper
        elif token.token_type == ktokens.TokenType.LPAREN:
            # This needs to distinguish between (expr), tuple literal, and record literal
            # Look ahead to distinguish RecordInstanceLiteral from TupleLiteral/Parenthesized Expr
            is_record_candidate = False
            # A simple check: if next is IDENTIFIER and then COLON, it's likely a record field
            if (self.current_token_index + 2 < len(self.tokens) and
                self.tokens[self.current_token_index + 1].token_type == ktokens.TokenType.IDENTIFIER and
                self.tokens[self.current_token_index + 2].token_type == ktokens.TokenType.COLON):
                is_record_candidate = True
            
            if is_record_candidate:
                return self.parse_record_instance_literal() # Needs to be implemented
            else: # Parenthesized expression or Tuple literal
                self.expect(ktokens.TokenType.LPAREN)
                # Check for empty tuple ()
                if self.current().token_type == ktokens.TokenType.RPAREN:
                    self.advance() # Consume RPAREN
                    return TupleLiteral([])

                # Parse first element
                expr_node = self.parse_predicate_expression()

                if self.current().token_type == ktokens.TokenType.COMMA: # It's a tuple
                    elements = [expr_node]
                    while self.current().token_type == ktokens.TokenType.COMMA:
                        self.advance()
                        if self.current().token_type == ktokens.TokenType.RPAREN: # Trailing comma in tuple
                            break
                        elements.append(self.parse_predicate_expression())
                    self.expect(ktokens.TokenType.RPAREN)
                    return TupleLiteral(elements)
                else: # It was a parenthesized expression
                    self.expect(ktokens.TokenType.RPAREN)
                    return expr_node # Return the inner expression directly
        elif token.token_type == ktokens.TokenType.SET_OPEN: # Literal set as an expression
             return self.parse_literal_set_or_comprehension() # Allows sets within expressions/tuples
        else:
            line = token.line if hasattr(token, 'line') and token.line is not None else "Unknown"
            col = token.column if hasattr(token, 'column') and token.column is not None else "Unknown"
            raise SyntaxError(
                f"Unexpected token in expression: {token.token_type.name} ('{token.lexeme}') "
                f"at line {line}, column {col}"
            )

    def parse_record_instance_literal(self):
        # Parses (name: "Alice", age: 30)
        self.expect(ktokens.TokenType.LPAREN)
        assignments = []
        if self.current().token_type != ktokens.TokenType.RPAREN:
            while True:
                field_name_token = self.expect(ktokens.TokenType.IDENTIFIER)
                self.expect(ktokens.TokenType.COLON)
                value_node = self.parse_predicate_expression()
                assignments.append((field_name_token.lexeme, value_node))
                if self.current().token_type == ktokens.TokenType.COMMA:
                    self.advance()
                else:
                    break
        self.expect(ktokens.TokenType.RPAREN)
        return RecordInstanceLiteral(assignments)

# ... (ensure all other necessary parsing methods are present and correct)