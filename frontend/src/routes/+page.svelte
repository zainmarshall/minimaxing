<script lang="ts">
  import { onMount } from 'svelte';
  let bots = [];
  onMount(async () => {
    try {
      const res = await fetch('/api/bots');
      if (res.ok) bots = await res.json();
    } catch (e) { console.error(e); }
  });
</script>

<div class="p-6 max-w-4xl mx-auto">
  <h1 class="text-3xl font-bold mb-4">MiniMaxing</h1>
  <p class="mb-4">Welcome — quick links:</p>
  <ul class="list-disc ml-6">
    <li><a href="/dashboard" class="text-blue-600">Dashboard</a></li>
    <li><a href="/bot" class="text-blue-600">My Bots</a></li>
  </ul>
</div>
<div class="text-center py-20">
    <h1 class="text-5xl font-black mb-6">♟ MiniMaxing</h1>
    <p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
        Create immutable chess evaluation functions and watch them compete in
        deterministic match-ups.
    </p>
    <div class="flex justify-center gap-4">
        <a
            href="/dashboard"
            class="bg-gray-900 text-white px-8 py-3 rounded-lg font-bold hover:bg-black transition"
        >
            Go to Dashboard
        </a>
    </div>
</div>
