<script lang="ts">
    /** @type {{ piece: string }} */
    let { piece } = $props();

    const pieceTypeMap: Record<string, string> = {
        k: "king",
        q: "queen",
        r: "rook",
        b: "bishop",
        n: "knight",
        p: "pawn",
    };

    const isWhite = $derived(piece === piece.toUpperCase());
    const type = $derived(pieceTypeMap[piece.toLowerCase()]);
    const color = $derived(isWhite ? "w" : "b");

    // In SvelteKit/Vite, we can import or use a path if it's in static
    // Since it's in src/lib/assets/pieces, we can use a dynamic import or just a relative URL if Vite handles it.
    // However, the cleanest way in a loop is often to just use a path if they were in static.
    // If they are in src/lib/assets, we might need to import them.
    // But for simplicity and to match common SvelteKit patterns for dynamic assets,
    // I'll assume they can be reached via a relative path if the dev server is set up.
    // Actually, I'll use a direct path relative to the component or just use the assets folder.

    const src = $derived(`/src/lib/assets/pieces/${type}-${color}.svg`);
</script>

<img
    {src}
    alt={piece}
    class="w-[85%] h-[85%] drop-shadow-md select-none pointer-events-none"
/>
