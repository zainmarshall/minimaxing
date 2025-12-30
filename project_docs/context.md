# Project Context & Progress

This file tracks what has been completed, current tasks, and overall project state for MiniMaxing.


## Completed
- Project plan written (plan.md)
- SvelteKit frontend started
- FastAPI backend structure created
- .venv set up in backend
- Board logic endpoints implemented
- Supabase integration for users, bots, matches
- User authentication via Supabase
- Modular backend API: matches, bots, versions
- Chess engine: Negamax with alpha-beta, helpers, repetition penalty
- User bots: rule-based and script-based (Python, helpers injected)
- Example bots: tactical_aggressor ("the butcher"), positional_strategist ("grandmaster")
- Batch evaluation endpoint for scripts
- Full version management: create, clone, delete, download, edit (with safety checks)
- Bot management: create, delete (with FK safety), upload JSON/script
- Dashboard and bot UI: upload, edit, view, clone, delete, download, version history
- Helper library for bot scripts: material, mobility, king_attackers, pawn_structure, center_control, repetition_count, etc.

## In Progress
- Implementation plan (implementation.md)
- API design
- Harden script execution (sandboxing, resource limits)
- Add more helpers and script templates
- Improve UI for error/success, preview, and batch match tools

## Next Steps
- Harden backend script execution (sandboxing)
- Add tournament/ladder logic
- Add ELO/rating system and stats
- Add more bot upload/preview/test features
- Add more example bots and helper docs

(Update this file as you make progress!)
