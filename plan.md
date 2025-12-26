♟️ Project: MiniMaxing
A distributed AI Chess Platform where users design heuristic algorithms to battle for ELO.
🛠 The Tech Stack
Frontend: SvelteKit (Node.js) + TailwindCSS + Monaco Editor.
Backend: Python FastAPI (High performance, Async).
Database: Supabase (PostgreSQL + Auth).
Engine Logic: python-chess + Custom Minimax Implementation.
🔐 1. The Security Architecture (The "Anti-Jailbreak" System)
You are right: raw eval() is dangerous even with __builtins__ removed because of Python's introspection (e.g., ().__class__.__base__...).
To run user rules safely without the slowness of Docker (which would kill Minimax performance), we use Static Analysis (AST Whitelisting).
The 3-Layer Defense:
Layer 1: AST Validation (The Gatekeeper)
Before the code even touches eval(), we parse it into an Abstract Syntax Tree. We reject the code if it contains:
Attributes starting with _ (Prevents accessing __class__, __bases__, __import__).
Function calls NOT in our whitelist (Allows len, abs, board.*; Bans open, eval, exec).
Control flow (loops/imports).
Layer 2: Scope Isolation
We execute eval() with globals={"__builtins__": None} and locals={"board": board, "chess": chess}.
Layer 3: Resource Limits
We enforce a strict 1.0s timeout on the total move calculation.
📂 2. File Structure (Setup this first)
Create a monorepo. This structure separates concerns and looks professional.
code
Text
/gambit-zero
│
├── /frontend               # SvelteKit Application
│   ├── /src
│   │   ├── /lib
│   │   │   ├── /components
│   │   │   │   ├── ChessBoard.svelte
│   │   │   │   ├── RuleEditor.svelte  <-- The "Deck" UI
│   │   │   │   └── MatchGraph.svelte
│   │   └── /routes
│   │       ├── +page.svelte           # Landing
│   │       ├── /workshop              # Where users build bots
│   │       └── /arena                 # Watch matches
│
├── /backend                # FastAPI Application
│   ├── main.py             # Entry Point
│   ├── /api
│   │   ├── routers.py      # Endpoints
│   │   └── schemas.py      # Pydantic Models (Input validation)
│   ├── /core
│   │   ├── security.py     # AST Validator Logic (CRITICAL)
│   │   └── config.py
│   └── /engine
│       ├── minimax.py      # Your AI algorithm
│       └── evaluator.py    # The Rule Engine
│
└── docker-compose.yml      # For spinning up DB locally
🚀 3. Implementation Plan (The Work Order)
Phase 1: The Secure Engine (Backend)
Goal: Send a board FEN + a list of rules, receive a move.
Setup FastAPI: basic POST /move endpoint.
Implement security.py: Write the AST walker that scans user strings.
Constraint: Must reject (1).__class__.
Constraint: Must accept len(board.pieces(chess.PAWN, chess.WHITE)).
Implement evaluator.py:
Class Bot that takes a list of rule strings.
compile() the strings once during __init__.
evaluate(board) method that loops through compiled rules, runs eval(), and sums the weights.
Implement minimax.py: Standard Alpha-Beta pruning that calls Bot.evaluate() at leaf nodes.
Phase 2: The Workshop (Frontend)
Goal: A UI to create, test, and save rules.
Rule Editor UI: A list view where users can "Add Rule".
Input: Rule Name (String).
Input: Code Snippet (Monaco Editor, Python syntax).
Input: Weight (Slider -10 to +10).
"Test Run" Button:
Sends current board state + rules to Backend.
Backend runs Minimax (Depth 2).
Frontend displays the move and the calculated score.
Visual Debugger:
Show which rules triggered. (e.g., "⚠️ King Safety Triggered: -5.0 pts").
Phase 3: The Arena (Persistence)
Goal: Save bots and play them.
Supabase Integration:
Table bots: id, user_id, rules_json, elo.
Matchmaking Logic:
Endpoint POST /match: User selects two saved bots.
Server simulates the game (Bot A vs Bot B).
Server returns the PGN (Move history).
Replay Viewer:
Frontend takes the PGN and animates the board move-by-move.
📝 Code Snippet: The Security Core (backend/core/security.py)
This is the code you should write first. It is the foundation of the project.
code
Python
import ast

SAFE_FUNCTIONS = {'len', 'abs', 'max', 'min', 'sum'}

class SecurityVisitor(ast.NodeVisitor):
    def __init__(self):
        self.is_safe = True
        self.error_msg = ""

    def visit_Attribute(self, node):
        # BAN: Accessing private/magic attributes (e.g., __class__, _private)
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
✅ Ready to start?
Initialize the Repo.
Setup FastAPI.
Paste the SecurityVisitor into backend/core/security.py.
Start coding.