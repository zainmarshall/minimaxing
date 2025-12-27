<script lang="ts">
  import RuleEditor from '$lib/RuleEditor.svelte';
  import ChessBoard from '$lib/ChessBoard.svelte';
  import { onMount } from 'svelte';

  let fen = 'startpos';
  let lastMove = '';

  async function runTest(rule) {
    const payload = { fen: fen === 'startpos' ? new (await import('chess.js')).Chess().fen() : fen, rules: { rules: [rule] }, depth: 2 };
    // For simplicity call backend relative path
    const res = await fetch('/api/move', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
    if (res.ok) {
      const data = await res.json();
      lastMove = data.move;
    } else {
      lastMove = 'error';
    }
  }
</script>

<h1>Workshop</h1>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem">
  <div>
    <RuleEditor bind:initialCode initialName="Material" initialWeight={1.0} />
  </div>
  <div>
    <ChessBoard {fen} />
    <div>Last move: {lastMove}</div>
  </div>
</div>

<style>
h1 { margin-bottom: 1rem }
</style>
