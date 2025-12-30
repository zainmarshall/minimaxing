import ast
import chess

class SecurityValidator:
    """
    Validates user-supplied Python rule code for security.
    """
    
    # Whitelist of safe function calls and names
    NAME_WHITELIST = {
        # Core objects
        'board', 'chess', 'True', 'False', 'None',
        
        # Built-in functions (Safe ones)
        'len', 'range', 'abs', 'min', 'max', 'sum', 'list', 'dict', 'set', 'tuple',
        'int', 'float', 'str', 'bool', 'all', 'any', 'enumerate', 'filter', 'map',
        'sorted', 'reversed', 'pow', 'round', 'divmod',
        
        # Chess constants
        'WHITE', 'BLACK', 'PAWN', 'KNIGHT', 'BISHOP', 'ROOK', 'QUEEN', 'KING',
        'SQUARES', 'FILE_NAMES', 'RANK_NAMES',
    }

    def __init__(self):
        pass

    def validate(self, code: str) -> bool:
        """
        Parses code into AST and checks against security rules.
        """
        try:
            tree = ast.parse(code, mode='eval')
        except SyntaxError:
            return False

        for node in ast.walk(tree):
            # Block imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False
            
            # Block attribute access to private/internal stuff
            if isinstance(node, ast.Attribute):
                if node.attr.startswith('_'):
                    return False
            
            # Block control flow (loops, etc.) - although mode='eval' mostly handles this
            if isinstance(node, (ast.For, ast.While, ast.If, ast.With, ast.Try)):
                return False
            
            # Block assignment and deletes
            if isinstance(node, (ast.Assign, ast.Delete, ast.AugAssign)):
                return False

            # Check names against whitelist
            if isinstance(node, ast.Name):
                if node.id not in self.NAME_WHITELIST and not node.id.isupper():
                    # Allow uppercase constants (likely chess module constants)
                    if node.id not in self.NAME_WHITELIST:
                        return False

        return True
