import ast

SAFE_FUNCTIONS = {'len', 'abs', 'max', 'min', 'sum'}

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.is_safe = True
        self.error_msg = ""

    def visit_Attribute(self, node):
        # BAN: Accessing private/magic attributes (e.g., __class__, __bases__, __import__)
        if node.attr.startswith('_'):
            self.is_safe = False
            self.error_msg = f"Security Error: Accessing private attribute '{node.attr}' is forbidden."
        self.generic_visit(node)

    def visit_Call(self, node):
        # BAN: Calling functions that aren't whitelisted or board methods
        if isinstance(node.func, ast.Name):
            if node.func.id not in SAFE_FUNCTIONS:
                self.is_safe = False
                self.error_msg = f"Security Error: Function '{node.func.id}' is not allowed."
        self.generic_visit(node)

    def visit_Import(self, node):
        self.is_safe = False
        self.error_msg = "Security Error: Imports are forbidden."

    def visit_ImportFrom(self, node):
        self.is_safe = False
        self.error_msg = "Security Error: Imports are forbidden."

def validate_rule(rule_code: str) -> tuple[bool, str]:
    """
    Parses string into AST and checks for malicious patterns.
    Returns (is_valid, error_message).
    """
    try:
        tree = ast.parse(rule_code, mode='eval')
    except SyntaxError:
        return False, "Syntax Error in rule."

    validator = SecurityVisitor()
    validator.visit(tree)
    
    return validator.is_safe, validator.error_msg