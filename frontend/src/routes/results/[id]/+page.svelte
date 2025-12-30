<script lang="ts">
  import { onMount } from 'svelte';
  export let params: { id: string };
  let pgn = '';
  let evals = [];
  onMount(async () => {
    try {
      const res = await fetch(`/api/results/${params.id}`);
      if (res.ok) {
        const data = await res.json();
        pgn = data.pgn || '';
        evals = data.evals || [];
      }
    } catch (e) { console.error(e); }
  });
</script>

<div class="p-6 max-w-4xl mx-auto">
  <h1 class="text-2xl font-bold mb-4">Match {params.id}</h1>
  <section class="mb-4">
    <h2 class="font-semibold">PGN</h2>
    <pre class="bg-gray-100 p-3 rounded">{pgn}</pre>
  </section>
  <section>
    <h2 class="font-semibold">Evaluations</h2>
    <pre class="bg-gray-50 p-3 rounded">{JSON.stringify(evals, null, 2)}</pre>
  </section>
</div>
