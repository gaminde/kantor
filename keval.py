from kast import (
    TypeDefinition, SetDefinition, Identifier, TupleLiteral, LiteralSet,
    SetOperation, SetComprehension, RecordInstanceLiteral, NumberLiteralNode, StringLiteralNode,
    AttributeAccess, Comparison 
)
import klexer
import ktokens
from kparser import Parser

# HELPER FUNCTION
def format_kantor_value(value, defined_types=None, type_name_hint=None):
    """
    Formats a Python value (representing a Kantor value) into a Kantor-like string.
    defined_types is the evaluator.types dictionary.
    type_name_hint is the declared type of the set containing this value, if known.
    """
    if isinstance(value, frozenset):
        is_record_format = True 
        if not value: # If the frozenset is empty
            is_record_format = False # An empty frozenset is an empty set, not an empty record
        elif value: 
            all_items_are_kv_pairs_for_record = True
            for item_in_frozenset in value:
                if not (isinstance(item_in_frozenset, tuple) and \
                        len(item_in_frozenset) == 2 and \
                        isinstance(item_in_frozenset[0], str)):
                    all_items_are_kv_pairs_for_record = False
                    break
            if not all_items_are_kv_pairs_for_record:
                is_record_format = False 
        
        if is_record_format:
            # Format as a record (e.g., (name: "Alice", age: 30))
            fields_order = []
            if defined_types and type_name_hint and type_name_hint in defined_types:
                type_info = defined_types[type_name_hint]
                if type_info and isinstance(type_info, list) and type_info and isinstance(type_info[0], tuple):
                    fields_order = [f[0] for f in type_info]
            
            record_dict = dict(value) 
            if not fields_order: # Fallback to sorted keys if no type hint or type hint is positional
                fields_order = sorted(record_dict.keys())

            parts = []
            for key in fields_order:
                if key in record_dict: # Ensure key exists, especially if fields_order comes from type
                    val_str = format_kantor_value(record_dict[key], defined_types)
                    parts.append(f"{key}: {val_str}")
            return f"({', '.join(parts)})"
        else:
            # Format as a set (e.g., {"item1", "item2"})
            return format_kantor_set(value, defined_types, None) 

    elif isinstance(value, set): 
        return format_kantor_set(value, defined_types, type_name_hint)
    elif isinstance(value, tuple):
        return f"({', '.join(format_kantor_value(v, defined_types) for v in value)})"
    elif isinstance(value, str):
        return f'"{value}"' 
    # Handle list type for defined types formatting
    elif isinstance(value, list): # Specifically for formatting type fields
        return str(value) # Or a more specific list formatting if needed
    
    return str(value)

def format_kantor_set(s, defined_types=None, type_name_hint=None):
    """ Formats a Python set or frozenset of Kantor values. """
    if not isinstance(s, (set, frozenset)): 
        return str(s)
    if not s:
        return "{}"
    
    try:
        # Attempt to sort for consistent output, will fail if elements are unorderable
        sorted_elements_str = sorted([format_kantor_value(e, defined_types, type_name_hint) for e in s])
        return f"{{{', '.join(sorted_elements_str)}}}"
    except TypeError: 
        # Fallback if sorting fails
        return f"{{{', '.join(format_kantor_value(e, defined_types, type_name_hint) for e in s)}}}"


class Evaluator:
    def __init__(self):
        self.env = {}  
        self.types = {} 

    def eval_program(self, program_nodes):
        results = []
        if not program_nodes:
            return results

        for node in program_nodes:
            try:
                result = self.eval(node) 
                results.append(result)
            except Exception:
                # Let errors propagate to the main try-except in __main__
                # Or handle them more gracefully here if needed (e.g., skip faulty node)
                raise 
        return results

    def eval(self, node, env=None): 
        if env is None:
            env = self.env 
        
        if isinstance(node, (int, float, str, frozenset)):
            return node
        if isinstance(node, tuple) and (not hasattr(node, '__class__') or type(node).__name__ != 'TupleLiteral'):
             if hasattr(node, 'elements') and isinstance(getattr(node, 'elements', None), list):
                 pass 
             else: 
                 return node

        node_type_name = type(node).__name__
        eval_method_name = f"eval_{node_type_name}"

        if hasattr(self, eval_method_name):
            try:
                return getattr(self, eval_method_name)(node, env)
            except Exception: # Catch errors from specific eval_ methods
                raise # Re-raise to be caught by eval_program's try-except or __main__
        else:
            raise NotImplementedError(f"Cannot evaluate AST node or unexpected type: {node_type_name} ({node})")

    def eval_TypeDefinition(self, node, env): 
        if not hasattr(node, 'name') or not hasattr(node, 'fields'):
            # This case should ideally be caught by parser or be an internal error
            raise ValueError("Malformed TypeDefinition node: missing 'name' or 'fields'")
        self.types[node.name] = node.fields
        return f"Type '{node.name}' defined with fields: {node.fields}"

    def eval_SetDefinition(self, node, env): 
        if not hasattr(node, 'name') or not hasattr(node, 'expr'):
            raise ValueError("Malformed SetDefinition node: missing 'name' or 'expr'")

        value = self.eval(node.expr, env)

        if node.type_name:
            if node.type_name not in self.types:
                raise TypeError(f"Type '{node.type_name}' not defined for set '{node.name}'.")
            
            type_fields_info = self.types[node.type_name]
            if not isinstance(value, (set, frozenset)):
                 raise TypeError(f"Set definition for '{node.name}' of type '{node.type_name}' evaluated to non-set type: {type(value)}")

            for item in value:
                is_named_field_type = isinstance(type_fields_info, list) and type_fields_info and isinstance(type_fields_info[0], tuple)

                if is_named_field_type: 
                    if not isinstance(item, frozenset): 
                        raise TypeError(f"Expected hashable record (frozenset of items) for type '{node.type_name}', got {type(item)}: {item}")
                    
                    item_as_dict = dict(item) 
                    defined_field_names = {f[0] for f in type_fields_info}
                    
                    missing_fields = defined_field_names - item_as_dict.keys()
                    if missing_fields:
                         raise TypeError(f"Item {format_kantor_value(item, self.types, node.type_name)} missing fields for type '{node.type_name}'. Expected: {missing_fields}")
                    # Optional: Check for extra fields
                    # extra_fields = item_as_dict.keys() - defined_field_names
                    # if extra_fields:
                    #     raise TypeError(f"Item {format_kantor_value(item, self.types, node.type_name)} has extra fields for type '{node.type_name}'. Extra: {extra_fields}")
                else: 
                    if not isinstance(item, tuple):
                        raise TypeError(f"Expected tuple for type '{node.type_name}', got {type(item)}: {item}")
                    if len(item) != len(type_fields_info):
                        raise TypeError(f"Item {item} has wrong number of fields for type '{node.type_name}'. Expected {len(type_fields_info)}, got {len(item)}")
        
        self.env[node.name] = value 
        return value

    def eval_Identifier(self, node, env): 
        if node.name in env: 
            return env[node.name]
        if node.name in self.types:
            raise NameError(f"'{node.name}' is a type, not a value variable in this context.")
        raise NameError(f"Identifier '{node.name}' not found in the current scope.")

    def eval_TupleLiteral(self, node, env):
        evaluated_elements = []
        for element_node in node.elements:
            val = self.eval(element_node, env)
            if isinstance(val, set): 
                evaluated_elements.append(frozenset(val)) 
            else:
                evaluated_elements.append(val)
        return tuple(evaluated_elements)

    def eval_RecordInstanceLiteral(self, node, env):
        record_dict = {}
        for field_name, value_node in node.field_assignments:
            val = self.eval(value_node, env)
            if isinstance(val, set): 
                record_dict[field_name] = frozenset(val) 
            else:
                record_dict[field_name] = val
        return frozenset(record_dict.items())
        
    def eval_NumberLiteralNode(self, node, env): 
        return node.value

    def eval_StringLiteralNode(self, node, env): 
        return node.value

    def eval_LiteralSet(self, node, env): 
        evaluated_elements = set()
        for element_node in node.elements:
            evaluated_elements.add(self.eval(element_node, env))
        return evaluated_elements

    def eval_SetOperation(self, node, env): 
        left_val = self.eval(node.left, env)
        right_val = self.eval(node.right, env)

        if not isinstance(left_val, (set, frozenset)):
            raise TypeError(f"Left operand for set operation '{node.op}' must be a set. Got {type(left_val)}")
        if not isinstance(right_val, (set, frozenset)):
            raise TypeError(f"Right operand for set operation '{node.op}' must be a set. Got {type(right_val)}")

        left_set = set(left_val) if isinstance(left_val, frozenset) else left_val
        right_set = set(right_val) if isinstance(right_val, frozenset) else right_val

        if node.op == '|':
            return left_set.union(right_set)
        elif node.op == '&':
            return left_set.intersection(right_set)
        elif node.op == '*': 
            product = set()
            if not left_set or not right_set:
                return set()
            for l_item in left_set:
                for r_item in right_set:
                    product.add((l_item, r_item)) 
            return product
        else:
            raise ValueError(f"Unknown set operator: {node.op}")

    def eval_SetComprehension(self, node, env):
        source_val = self.eval(node.source, env)
        if not isinstance(source_val, (set, frozenset)): 
            raise TypeError(f"Set comprehension source must be a set or frozenset. Got {type(source_val)}")
        
        source_set = set(source_val) if isinstance(source_val, frozenset) else source_val

        result_set = set()
        for elem in source_set: 
            iter_env = {} 
            
            successful_bind = False
            if len(node.in_vars) == 1:
                iter_env[node.in_vars[0]] = elem 
                successful_bind = True
            elif isinstance(elem, tuple) and len(node.in_vars) == len(elem):
                for i, var_name in enumerate(node.in_vars):
                    iter_env[var_name] = elem[i]
                successful_bind = True
            # No direct record field destructuring in `in_vars` for now

            if not successful_bind and not (len(node.in_vars) == 1): 
                continue 
            
            current_scope_env = {**env, **iter_env}

            if node.predicate:
                predicate_result = self.eval(node.predicate, current_scope_env)
                if not predicate_result: 
                    continue
            
            if len(node.out_vars) == 1:
                output_item = self.eval(node.out_vars[0], current_scope_env) 
            else: 
                output_tuple_elements = []
                for out_expr_node in node.out_vars:
                    output_tuple_elements.append(self.eval(out_expr_node, current_scope_env)) 
                output_item = tuple(output_tuple_elements)
            
            result_set.add(output_item)
            
        return result_set

    def eval_AttributeAccess(self, node, env): 
        obj_value = self.eval(node.obj_expr, env)

        if isinstance(obj_value, frozenset): 
            record_dict = dict(obj_value)
            if node.attribute_name in record_dict:
                return record_dict[node.attribute_name]
            else:
                raise AttributeError(f"Record {format_kantor_value(obj_value, self.types)} has no attribute '{node.attribute_name}'")
        else:
            raise TypeError(f"Cannot access attribute '{node.attribute_name}' on non-record type: {type(obj_value)}")

    def eval_Comparison(self, node, env): 
        left_val = self.eval(node.left_expr, env)
        right_val = self.eval(node.right_expr, env)

        op = node.operator
        if op == '==': return left_val == right_val
        elif op == '!=': return left_val != right_val
        elif op == '<': return left_val < right_val
        elif op == '<=': return left_val <= right_val
        elif op == '>': return left_val > right_val
        elif op == '>=': return left_val >= right_val
        else:
            raise ValueError(f"Unknown comparison operator: {op}")

if __name__ == "__main__":
    source_code_phase2 = """
        // --- Kantor Phase 2: Comprehensive Test Suite ---

        // 1. Type Definitions
        type Person: Record(name: string, age: int, city: string)
        type Item: Record(id: int, category: string, price: float)

        // 2. Data Structures & Literals / Set Definitions

        // Basic Literals & Sets
        let Numbers1 = {1, 2, 3, 4, 3} // Test uniqueness
        let Numbers2 = {3, 4, 5, 6}
        let Strings1 = {"apple", "banana", "cherry"}
        let Strings2 = {"banana", "date", "apple"}
        let EmptySetTest = {}

        // Record Instances & Sets of Records
        let Users: Person = {
            (name: "Alice", age: 30, city: "New York"),
            (name: "Bob", age: 25, city: "London"),
            (name: "Charlie", age: 35, city: "Paris"),
            (name: "David", age: 25, city: "London")
        }
        let ExtraUserSet: Person = {(name: "Eve", age: 22, city: "Berlin")}
        
        let Inventory: Item = {
            (id: 101, category: "Fruit", price: 0.5),
            (id: 102, category: "Fruit", price: 0.75),
            (id: 201, category: "Dairy", price: 2.5)
        }

        // Tuple Instances & Sets of Tuples
        let Coordinates = {(1, 2), (3, 4), (1, 2), (5, 6)} // Test uniqueness
        // MixedTuples will test if a set (Users) inside a tuple becomes a frozenset for hashability
        let MixedTuples = { (1, "one"), (2, "two", Users) } 

        // Records with Set-valued fields
        let UserGroups = { 
            (groupName: "All Users", members: Users),
            (groupName: "Empty Group", members: {})
        }

        // 3. Set Operations
        let UnionNumbers = Numbers1 | Numbers2
        let IntersectionStrings = Strings1 & Strings2
        let CrossProductTest = {1,2} * {"a"} // Test cross product
        let CombinedUsers: Person = Users | ExtraUserSet

        // 4. Set Comprehensions

        // Basic Comprehensions (Identity, Attribute Access)
        let AllUserRecordsCopy: Person = { p | p of Users } 
        let UserNames = { p.name | p of Users }
        let UserAges = { p.age | p of Users }

        // Comprehensions with Predicates
        let Adults: Person = { p | p of Users, p.age >= 30 }
        let SpecificUserBob: Person = { p | p of Users, p.name == "Bob" }
        let Fruits: Item = { item | item of Inventory, item.category == "Fruit" }
        let ExpensiveFruits: Item = { item | item of Fruits, item.price > 0.6 } // Chained: Comprehension over a derived set

        // Comprehensions with Tuple Output
        let NameAndCity = { (p.name, p.city) | p of Users }
        let AdultNameAndAge = { (p.name, p.age) | p of Users, p.age >= 30 }

        // Comprehension over a derived set (another example)
        let NamesOfAdults = { person.name | person of Adults }

        // Comprehension with more complex output structure (tuple of attributes)
        let UserInfoTuples = { (p.name, p.age, p.city) | p of Users, p.age < 30 }

        // Comprehension over an empty set
        let NamesFromEmpty = { p.name | p of EmptySetTest }

        // Comprehension deconstructing tuples from a set of tuples
        let FirstCoordValues = { c1 | (c1, c2) of Coordinates }
        let SecondCoordValues = { c2 | (c1, c2) of Coordinates }
        let FilteredCoords = { (x,y) | (x,y) of Coordinates, x > 1 }

        // Comprehension over a set of basic types
        // let DoubledNumbers = { n*2 | n of Numbers1 } // COMMENTED OUT: Arithmetic not yet supported
        let CopiedNumbers = { n | n of Numbers1 } 
        // let NumbersPlusOne = { n + 1 | n of {10,20} } // COMMENTED OUT: Arithmetic not yet supported
        // 5. Expression Evaluation (implicitly tested throughout)
    """

    print(f"--- Testing Kantor Phase 2: Interactive Evaluation ---")

    # Prepare source lines for display
    all_source_lines = source_code_phase2.splitlines()
    code_statement_lines = []
    for line in all_source_lines:
        stripped_line = line.strip()
        if stripped_line and not stripped_line.startswith("//"):
            code_statement_lines.append(line) # Store the original line to preserve indentation for display if desired, or use stripped_line

    lexer = klexer.Lexer(source_code_phase2)
    tokens = []
    while True:
        token = lexer.next_token()
        if token.token_type == ktokens.TokenType.EOF:
            tokens.append(token)
            break
        tokens.append(token)

    parser = Parser(tokens)
    try:
        ast_nodes = parser.parse()
        evaluator = Evaluator()

        if not ast_nodes:
            print("No statements found to process.")
        else:
            for i, node in enumerate(ast_nodes):
                source_line_display = "N/A"
                if i < len(code_statement_lines):
                    source_line_display = code_statement_lines[i].strip() # Use the stripped version for cleaner output
                
                print(f"\nProcessing Statement {i+1}/{len(ast_nodes)}: {source_line_display}")

                try:
                    result = evaluator.eval(node) # Evaluate one statement

                    if isinstance(node, TypeDefinition):
                        print(f"Output: {result}")
                    elif isinstance(node, SetDefinition):
                        print(f"Output: Set '{node.name}' defined. Current value: {format_kantor_value(result, evaluator.types, node.type_name)}")
                    else:
                        print(f"Output: {format_kantor_value(result, evaluator.types)}")
                    
                except Exception as e_node:
                    print(f"Error evaluating statement '{source_line_display}': {e_node}")
                
        # Final summary of the environment
        print("\n\n--- Final State After All Statements ---")
        print("Evaluation Results (Final Environment - Sets):") 
        if not evaluator.env:
            print("  (No sets defined or environment is empty)")
        for name, value in evaluator.env.items():
            type_name_hint = None
            if ast_nodes: 
                for n_ in ast_nodes:
                    if isinstance(n_, SetDefinition) and n_.name == name:
                        type_name_hint = n_.type_name 
                        break
            print(f"  {name}: {format_kantor_value(value, evaluator.types, type_name_hint)}")
        
        print("\nDefined Types:")
        if not evaluator.types:
            print("  (No types defined)")
        for name, fields in evaluator.types.items(): 
            print(f"  {name}: {format_kantor_value(fields, evaluator.types)}")

    except SyntaxError as e:
        print(f"Syntax Error: {e}")
    except TypeError as e:
        print(f"Type Error: {e}")
    except ValueError as e:
        print(f"Value Error: {e}")
    except NameError as e:
        print(f"Name Error: {e}")
    except NotImplementedError as e: 
        print(f"Not Implemented Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred in __main__: {e}")
        import traceback
        traceback.print_exc()

    print("------------------------------")