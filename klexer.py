import re
import ktokens

class Lexer:
    def __init__(self, source):
        self.source = source
        self.position = 0
        # Add line and column tracking if you want better error messages later
        # self.line = 1
        # self.column = 1 
        self.keywords = {
            "let": ktokens.TokenType.KEYWORD_LET,
            "filter": ktokens.TokenType.KEYWORD_FILTER,
            "of": ktokens.TokenType.KEYWORD_OF,
            "type": ktokens.TokenType.KEYWORD_TYPE,
            "Record": ktokens.TokenType.KEYWORD_RECORD,
            # "if": ktokens.TokenType.KEYWORD_IF, # If using 'if' keyword for predicates
        }

    def peek(self):
        if self.position + 1 < len(self.source):
            return self.source[self.position + 1]
        return None

    def advance(self):
        # Add logic to update line/column if tracking
        self.position += 1

    def skip_whitespace_and_comments(self):
        while self.position < len(self.source):
            char = self.source[self.position]
            if char.isspace():
                # Add line/column update logic if tracking newlines
                self.advance()
            elif self.source[self.position:].startswith("//"):
                while self.position < len(self.source) and self.source[self.position] != '\n':
                    self.advance()
                if self.position < len(self.source) and self.source[self.position] == '\n':
                    self.advance() # Consume the newline
                    # Update line/column tracking
            else:
                break

    def next_token(self):
        self.skip_whitespace_and_comments()

        if self.position >= len(self.source):
            return ktokens.Token(ktokens.TokenType.EOF, "")

        char = self.source[self.position]
        current_pos = self.position # For multi-char tokens

        # Single-character tokens that are not part of multi-character ones
        simple_tokens = {
            '{': ktokens.TokenType.SET_OPEN,
            '}': ktokens.TokenType.SET_CLOSE,
            '(': ktokens.TokenType.LPAREN,
            ')': ktokens.TokenType.RPAREN,
            ',': ktokens.TokenType.COMMA,
            ':': ktokens.TokenType.COLON,
            '|': ktokens.TokenType.PIPE,
            '&': ktokens.TokenType.AMPERSAND,
            '*': ktokens.TokenType.CROSS, # Or whatever you use for product
            '.': ktokens.TokenType.DOT,   # New
        }

        if char in simple_tokens:
            self.advance()
            return ktokens.Token(simple_tokens[char], char)

        # Potentially multi-character tokens (comparison, assignment)
        if char == '=':
            if self.peek() == '=':
                self.advance()
                self.advance()
                return ktokens.Token(ktokens.TokenType.EQUALS_EQUALS, "==")
            else:
                self.advance()
                return ktokens.Token(ktokens.TokenType.EQUALS, "=")
        elif char == '>':
            if self.peek() == '=':
                self.advance()
                self.advance()
                return ktokens.Token(ktokens.TokenType.GREATER_EQUAL, ">=")
            else:
                self.advance()
                return ktokens.Token(ktokens.TokenType.GREATER, ">")
        elif char == '<':
            if self.peek() == '=':
                self.advance()
                self.advance()
                return ktokens.Token(ktokens.TokenType.LESS_EQUAL, "<=")
            # elif self.peek() == '>': # For <> if you prefer that for not-equal
            #     self.advance()
            #     self.advance()
            #     return ktokens.Token(ktokens.TokenType.NOT_EQUAL, "<>")
            else:
                self.advance()
                return ktokens.Token(ktokens.TokenType.LESS, "<")
        elif char == '!':
            if self.peek() == '=':
                self.advance()
                self.advance()
                return ktokens.Token(ktokens.TokenType.NOT_EQUAL, "!=")
            # else: # Handle single '!' if it's a valid operator, or error
            #    pass

        # Handle Numbers (integers and potentially floats)
        # Using a more specific regex to avoid consuming a dot meant for attribute access
        num_match = re.match(r"\d+(\.\d+)?(?![.a-zA-Z_])", self.source[self.position:])
        if num_match:
            lexeme = num_match.group(0)
            self.position += len(lexeme)
            return ktokens.Token(ktokens.TokenType.NUMBER, lexeme)

        # Handle Strings
        if char == '"':
            start_pos = self.position
            self.advance() # Consume opening quote
            str_content = []
            while self.position < len(self.source) and self.source[self.position] != '"':
                # Handle escape sequences if you want them, e.g., \"
                str_content.append(self.source[self.position])
                self.advance()
            if self.position < len(self.source) and self.source[self.position] == '"':
                self.advance() # Consume closing quote
                return ktokens.Token(ktokens.TokenType.STRING, "".join(str_content))
            else:
                # Unterminated string - revert position and error or handle differently
                self.position = start_pos # Backtrack
                # Fall through to ILLEGAL or raise specific error

        # Handle keywords and identifiers
        # Ensure dot is not part of an identifier if it's a separate token
        ident_match = re.match(r"[a-zA-Z_][a-zA-Z0-9_]*", self.source[self.position:])
        if ident_match:
            lexeme = ident_match.group(0)
            token_type = self.keywords.get(lexeme, ktokens.TokenType.IDENTIFIER)
            self.position += len(lexeme)
            return ktokens.Token(token_type, lexeme)
        
        # If no token is matched
        self.advance() # Consume the character to avoid infinite loop
        return ktokens.Token(ktokens.TokenType.ILLEGAL, char)

# Test Lexer
source_code = "let A = {x | x of Users} // Ignore this"
lexer = Lexer(source_code)

tokens = []
while (token := lexer.next_token()).token_type != ktokens.TokenType.EOF:
    tokens.append(token)

def pretty_print_tokens(tokens):
    for token in tokens:
        print(f"{token.token_type.name:20} | {repr(token.lexeme)}")

pretty_print_tokens(tokens)
