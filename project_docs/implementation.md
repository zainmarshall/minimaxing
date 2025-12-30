# Implementation Plan: MiniMaxing

This document contains specific implementation ideas, technical plans, and design notes for the MiniMaxing project.

## Board Representation
- Use python-chess for board state and move validation.
- User-submitted functions must accept a parameter representing the board state (e.g., a python-chess Board object or FEN string).
- Store board state as FEN strings in the backend for easy serialization.
- Expose board state to frontend via API endpoints.

## Backend Structure
- FastAPI app with modular routers for different features (matches, users, bots).
- Use Pydantic models for request/response validation.
- Integrate Supabase for user authentication and match history storage.


## Engine Logic
- Custom Minimax implementation using python-chess for move generation.
- User-submitted heuristics run in a sandboxed environment (AST whitelisting, resource limits).

## Architecture Flow

1. Users write and submit their rules (boolean functions with weights) before matches. These are stored in the database.
2. When a match is created, each player is assigned their saved ruleset.
3. The backend initializes a ChessGame (python-chess) and alternates moves:
	- On each turn, the minimax engine runs using the current player's ruleset as the evaluation function.
	- The best move found by minimax is played for that side.
	- The process repeats, switching between white and black, until the game ends.
4. The full match history and result are saved to the database.

This architecture allows users to compete by designing better evaluation rules, while the backend ensures fair, secure, and automated matches.

## API Endpoints (Draft)
- /api/match/create
- /api/match/{id}/move
- /api/bot/submit
- /api/user/profile

## To Do
- Finalize board serialization format
- Design user bot submission API
- Implement match result storage

(Add more sections as needed)
