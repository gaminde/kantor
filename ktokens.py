from enum import Enum, auto

class TokenType(Enum):
    # Existing Literals and Identifiers
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()

    # Existing Keywords
    KEYWORD_LET = auto()
    KEYWORD_FILTER = auto() # May be removed/repurposed if 'if' is used for predicates
    KEYWORD_OF = auto()
    KEYWORD_TYPE = auto()
    KEYWORD_RECORD = auto()
    # KEYWORD_IF = auto() # Add if you decide to use 'if' keyword for predicates

    # Existing Operators and Punctuation
    EQUALS = auto()          # Assignment =
    PIPE = auto()            # Set union |
    AMPERSAND = auto()       # Set intersection &
    CROSS = auto()           # Set product * (or X if you kept that)
    SET_OPEN = auto()        # {
    SET_CLOSE = auto()       # }
    LPAREN = auto()          # (
    RPAREN = auto()          # )
    COMMA = auto()           # ,
    COLON = auto()           # :

    # --- New Tokens for Phase 2: Predicates ---
    DOT = auto()             # For attribute access, e.g., record.field

    # Comparison Operators
    GREATER = auto()         # >
    LESS = auto()            # <
    GREATER_EQUAL = auto()   # >=
    LESS_EQUAL = auto()      # <=
    EQUALS_EQUALS = auto()   # == (for comparison, distinct from assignment =)
    NOT_EQUAL = auto()       # != (or <>)
    # --- End of New Tokens for Phase 2 ---

    # Special
    EOF = auto()
    ILLEGAL = auto()

class Token:
    def __init__(self, token_type, lexeme, line=None, column=None): # Added line/column for future
        self.token_type = token_type
        self.lexeme = lexeme
        self.line = line
        self.column = column

    def __repr__(self):
        return f"Token({self.token_type.name}, {self.lexeme!r})"