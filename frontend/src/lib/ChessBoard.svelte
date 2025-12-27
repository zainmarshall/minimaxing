<script lang="ts">
  import { onMount } from 'svelte';
  export let fen: string = 'startpos';
  let display = '';
  onMount(() => {
    display = fen === 'startpos' ? 'Initial position' : fen;
  });
</script>

<div class="chess-board">
  <div>{display}</div>
</div>

<style>
.chess-board { padding: 1rem; border: 1px solid #eee; border-radius:6px }
</style>
