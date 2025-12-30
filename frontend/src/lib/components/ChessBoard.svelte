<script lang="ts">
    import ChessPiece from "./ChessPiece.svelte";

    /** @type {{ fen: string, lastMove?: { from: string, to: string }, turn?: 'w' | 'b' }} */
    let { fen, lastMove = undefined, turn = "w" } = $props();

    const files = ["a", "b", "c", "d", "e", "f", "g", "h"];
    const ranks = ["8", "7", "6", "5", "4", "3", "2", "1"];

    /** @type {any[][]} */
    let board = $derived(parseFen(fen));

    function parseFen(fenString: string) {
        const [position] = fenString.split(" ");
        const rows = position.split("/");
        return rows.map((row) => {
            const cells = [];
            for (const char of row) {
                if (isNaN(parseInt(char))) {
                    cells.push(char);
                } else {
                    for (let i = 0; i < parseInt(char); i++) cells.push(null);
                }
            }
            return cells;
        });
    }

    function isSquareLastMove(fileIdx: number, rankIdx: number) {
        if (!lastMove) return false;
        const currentSquare = files[fileIdx] + ranks[rankIdx];
        return currentSquare === lastMove.from || currentSquare === lastMove.to;
    }
</script>

<div
    class="aspect-square bg-[#ebecd0] rounded-xl shadow-2xl overflow-hidden border-8 border-gray-900 grid grid-cols-8 grid-rows-8 relative"
>
    {#each ranks as rank, rIdx}
        {#each files as file, fIdx}
            {@const isDark = (rIdx + fIdx) % 2 === 1}
            {@const isHighlighted = isSquareLastMove(fIdx, rIdx)}
            <div
                class="relative flex items-center justify-center select-none transition-all duration-300 {isHighlighted
                    ? isDark
                        ? 'bg-yellow-500/60'
                        : 'bg-yellow-200/80'
                    : isDark
                      ? 'bg-[#779556]'
                      : 'bg-[#ebecd0]'}"
            >
                {#if board[rIdx][fIdx]}
                    <ChessPiece piece={board[rIdx][fIdx]} />
                {/if}

                {#if fIdx === 0}
                    <span
                        class="absolute top-1 left-1.5 text-[11px] font-black uppercase {isDark
                            ? 'text-[#ebecd0] opacity-50'
                            : 'text-[#779556] opacity-50'}">{rank}</span
                    >
                {/if}
                {#if rIdx === 7}
                    <span
                        class="absolute bottom-1 right-1.5 text-[11px] font-black uppercase {isDark
                            ? 'text-[#ebecd0] opacity-50'
                            : 'text-[#779556] opacity-50'}">{file}</span
                    >
                {/if}
            </div>
        {/each}
    {/each}

    {#if turn}
        <div
            class="absolute inset-0 pointer-events-none border-4 {turn === 'w'
                ? 'border-white/20'
                : 'border-black/20'} animate-pulse"
        ></div>
    {/if}
</div>

<style>
    :global(.drop-shadow-md) {
        filter: drop-shadow(0 4px 3px rgb(0 0 0 / 0.07))
            drop-shadow(0 2px 2px rgb(0 0 0 / 0.06));
    }
</style>
