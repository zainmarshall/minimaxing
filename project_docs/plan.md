# ♟ MiniMaxing — Full Core Architecture & Execution Pipeline

This document defines the COMPLETE foundational system required to run MiniMaxing.
It specifies how bots are defined, stored, matched, executed, secured, and persisted.
Game modes, ladders, tournaments, and UI layers are intentionally excluded.

---

## 1. Core Concept

MiniMaxing is a deterministic competitive system where users create immutable chess
evaluation functions (“bots”) that compete by playing full chess games against each other
using a fixed-depth search algorithm.

Players do NOT make moves.
Bots play entire games autonomously.

---

## 2. Bot Definition (Fundamental Unit)

A bot is a versioned, immutable evaluation function.

A bot version contains:
- A list of rules
- Each rule is a pure Python expression
- Each rule has a numeric weight
- No state, memory, or learning
- Fixed search depth

### Bot Version Schema (Logical)

bot_versions
- id (uuid, primary key)
- bot_id (uuid, foreign key)
- rules_json (jsonb)
- rules_hash (sha256)
- search_depth (int)
- created_at (timestamp)

rules_json format:
[
  {
    "rule_id": "uuid",
    "name": "King Safety",
    "code": "len(board.attackers(chess.WHITE, board.king(chess.BLACK)))",
    "weight": -5.0
  }
]

A bot version is immutable once created.

---

## 3. Database Models (Complete)

### users (Supabase Auth)
Managed externally by Supabase.

---

### profiles
Public identity and moderation state.

profiles
- id (uuid, pk, same as auth.users.id)
- username (unique)
- rating_global (float)
- matches_played (int)
- is_banned (bool)
- created_at (timestamp)

---

### bots
Logical container owned by a user.

bots
- id (uuid)
- user_id (uuid)
- name (string)
- description (string)
- active_version_id (uuid)
- status (draft | active | retired)
- created_at (timestamp)

---

### bot_versions
Immutable competitive units.

bot_versions
- id (uuid)
- bot_id (uuid)
- rules_json (jsonb)
- rules_hash (string)
- search_depth (int)
- created_at (timestamp)

---

### matches
Immutable match records.

matches
- id (uuid)
- bot_a_version (uuid)
- bot_b_version (uuid)
- winner (A | B | draw)
- termination_reason (checkmate | timeout | illegal | draw)
- pgn (text)
- elo_delta_a (float)
- elo_delta_b (float)
- created_at (timestamp)

---

### match_queue
Asynchronous execution control.

match_queue
- id (uuid)
- bot_a_version (uuid)
- bot_b_version (uuid)
- status (queued | running | completed | failed)
- priority (int)
- created_at (timestamp)

---

### elo_history
Rating audit trail.

elo_history
- bot_version_id (uuid)
- match_id (uuid)
- elo_before (float)
- elo_after (float)
- created_at (timestamp)

---

## 4. Match Execution Pipeline (End-to-End)

1. A match request is created
2. Bot versions are validated and locked
3. Match is inserted into match_queue
4. A worker claims the job
5. Engine initializes a standard chess board
6. Bots alternate turns until termination
7. Game ends via checkmate, draw, timeout, or illegal eval
8. PGN is generated
9. ELO is calculated
10. Match and ratings are persisted atomically

All matches are deterministic and reproducible.

---

## 5. Engine Model

### Search Algorithm
- Negamax with alpha-beta pruning
- Fixed depth per bot version
- Deterministic move ordering
- No randomness

### Turn Flow
For each move:
1. Generate legal moves
2. For each move:
   - Apply move
   - Run Negamax to remaining depth
   - At leaf nodes, call evaluate(board)
3. Select move with highest score
4. Enforce time limits
5. Execute chosen move

---

## 6. Evaluation Function

Each bot defines a single evaluation function:

evaluate(board):
- Iterates through rules
- Executes each rule expression
- Multiplies result by weight
- Returns summed score

Only the final scalar score is used by the engine.

Optional per-rule breakdowns may be logged for debugging.

---

## 7. Security Model (Mandatory)

User-supplied rule code is treated as hostile.

### Layer 1: AST Validation
Rules are parsed into an AST and rejected if they contain:
- Imports
- Attribute access starting with "_"
- Loops or control flow
- Function calls outside a whitelist

### Layer 2: Compile Once
Rules are compiled once at bot version creation.
Compilation time is capped.

### Layer 3: Runtime Sandbox
eval() is executed with:
- globals = {"__builtins__": None}
- locals = {"board": board, "chess": chess}

### Layer 4: Resource Limits
- Per-rule time limit
- Per-evaluation time limit
- Per-move time limit
- Per-game ply limit

Any violation results in immediate loss.

---

## 8. Determinism Guarantees

To ensure fairness and replayability:
- No randomness
- No system time access
- Stable move ordering
- Fixed engine configuration

The same bot versions will always produce the same game.

---

## 9. Match Result Object

matches are immutable once written.

Logical match result:
{
  "match_id": "uuid",
  "bot_a_version": "uuid",
  "bot_b_version": "uuid",
  "winner": "A | B | draw",
  "termination_reason": "checkmate | timeout | illegal | draw",
  "pgn": "string",
  "created_at": "timestamp"
}

---

## 10. Minimal System Requirements

The system is considered complete if it can:
- Create and store bot versions
- Validate rule code securely
- Execute full bot-vs-bot matches
- Enforce fairness and limits
- Persist and replay results

No ladders, tournaments, or UI are required for the core system.

---

## 11. Foundational Principle

Bots compete, not players.
Versions are immutable.
Security and determinism override performance.

Everything else is a layer on top of this core.
