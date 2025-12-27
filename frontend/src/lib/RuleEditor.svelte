<script lang="ts">
  import { onMount } from 'svelte';
  import { writable } from 'svelte/store';

  export let initialCode = "len(board.pieces(chess.PAWN, chess.WHITE)) - len(board.pieces(chess.PAWN, chess.BLACK))";
  export let initialName = 'Material Advantage';
  export let initialWeight = 1.0;

  const code = writable(initialCode);
  const name = writable(initialName);
  const weight = writable(initialWeight);

  let result: { move?: string; score?: number } = {};

  async function testRun(fen: string) {
    const payload = {
      fen,
      rules: { rules: [ { name: $name, code: $code, weight: $weight } ] },
      depth: 2
    };
    const res = await fetch('/api/move', {
      method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
    });
    if (res.ok) {
      result = await res.json();
    } else {
      const err = await res.text();
      result = { move: 'error', score: 0 };
      console.error('Move error', err);
    }
  }
</script>

<div class="rule-editor">
  <label>Rule name<input bind:value={$name} /></label>
  <label>Weight<input type="number" step="0.1" bind:value={$weight} /></label>
  <label>Code<textarea bind:value={$code} rows="8"></textarea></label>
  <button on:click={() => testRun('startpos')}>Test on startpos</button>
  <div class="result">
    <strong>Move:</strong> {result.move} <strong>Score:</strong> {result.score}
  </div>
</div>

<style>
.rule-editor { padding: 1rem; border: 1px solid #ddd; border-radius: 6px; }
label { display:block; margin-bottom: 0.5rem }
input, textarea { width:100% }
button { margin-top: 0.5rem }
</style>
