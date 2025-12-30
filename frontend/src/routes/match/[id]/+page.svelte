<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { page } from "$app/stores";
    import { supabase } from "$lib/supabaseClient";
    import { Chess } from "chess.js";
    import ChessBoard from "$lib/components/ChessBoard.svelte";

    const matchId = $page.params.id;

    interface SearchStep {
        move_idx: number;
        turn: "white" | "black";
        eval: number;
        top_moves: Record<string, number>;
    }

    interface MatchData {
        id: string;
        bot_a_version: string;
        bot_b_version: string;
        winner: "A" | "B" | "draw" | null;
        termination_reason: string;
        pgn: string;
        search_metadata: SearchStep[];
        status?: string;
        bot_a: { bot: { name: string } };
        bot_b: { bot: { name: string } };
    }

    interface MoveRecord {
        san: string;
        from: string;
        to: string;
        after: string;
        fen: string;
        eval: number;
    }

    let match = $state<MatchData | null>(null);
    let history = $state<MoveRecord[]>([]);
    let currentMoveIdx = $state(-1);
    let isPlaying = $state(false);
    let playbackSpeed = $state(1000);

    let activeTab = $state<"moves" | "thinking">("moves");

    let timer: ReturnType<typeof setInterval> | undefined;

    onMount(() => {
        fetchMatch();

        const channel = supabase
            .channel(`match_${matchId}`)
            .on(
                "postgres_changes",
                {
                    event: "UPDATE",
                    schema: "public",
                    table: "match_queue",
                    filter: `id=eq.${matchId}`,
                },
                (payload) => {
                    if (payload.new.status === "completed") {
                        fetchMatch();
                    } else if (payload.new.status === "failed") {
                        if (match) match = { ...match, status: "failed" };
                    }
                },
            )
            .subscribe();

        return () => {
            void channel.unsubscribe();
        };
    });

    onDestroy(() => {
        if (timer) clearInterval(timer);
    });

    async function fetchMatch() {
        const { data, error } = await supabase
            .from("matches")
            .select(
                "*, bot_a:bot_a_version(bot:bot_id(name)), bot_b:bot_b_version(bot:bot_id(name))",
            )
            .eq("id", matchId)
            .single();

        if (error) {
            const { data: queueData } = await supabase
                .from("match_queue")
                .select("*")
                .eq("id", matchId)
                .single();
            if (queueData) match = { status: queueData.status } as MatchData;
        } else {
            match = data as MatchData;
            parsePGN(data.pgn);
        }
    }

    function parsePGN(pgn: string) {
        const tempGame = new Chess();
        try {
            tempGame.loadPgn(pgn);
            const moves = tempGame.history({ verbose: true });
            const comments = tempGame.getComments();

            const evalRegex = /eval: (-?\d+\.?\d*)/;

            history = moves.map((move, i) => {
                const commentObj = comments.find((c) => c.fen === move.after);
                const comment = commentObj ? commentObj.comment : "";
                const evalMatch = comment.match(evalRegex);
                return {
                    san: move.san,
                    from: move.from,
                    to: move.to,
                    after: move.after,
                    fen: move.after,
                    eval: evalMatch ? parseFloat(evalMatch[1]) : 0,
                };
            });

            currentMoveIdx = history.length - 1;
        } catch (e) {
            console.error("PGN Parsing Error:", e);
        }
    }

    function step(delta: number) {
        currentMoveIdx = Math.max(
            -1,
            Math.min(history.length - 1, currentMoveIdx + delta),
        );
    }

    function togglePlay() {
        isPlaying = !isPlaying;
        if (isPlaying) {
            if (currentMoveIdx >= history.length - 1) currentMoveIdx = -1;
            timer = setInterval(() => {
                if (currentMoveIdx < history.length - 1) {
                    currentMoveIdx++;
                } else {
                    isPlaying = false;
                    if (timer) clearInterval(timer);
                }
            }, playbackSpeed);
        } else {
            if (timer) clearInterval(timer);
        }
    }

    const currentFen = $derived(
        currentMoveIdx === -1
            ? "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            : history[currentMoveIdx].fen,
    );
    const currentEval = $derived(
        currentMoveIdx === -1 ? 0 : history[currentMoveIdx].eval,
    );
    const lastMove = $derived(
        currentMoveIdx === -1
            ? undefined
            : {
                  from: history[currentMoveIdx].from,
                  to: history[currentMoveIdx].to,
              },
    );

    // thinking metadata for current position (which bot is moving NEXT)
    const currentThinking = $derived.by(() => {
        if (!match?.search_metadata) return null;
        // next move is currentMoveIdx + 1
        return match.search_metadata.find(
            (m) => m.move_idx === currentMoveIdx + 1,
        );
    });

    const thinkingColor = $derived(
        currentThinking?.turn === "white"
            ? "bg-white text-black"
            : "bg-black text-white",
    );
</script>

<div class="max-w-7xl mx-auto py-8 px-4">
    {#if match}
        {#if match.pgn && history.length > 0}
            <div class="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                <!-- Left Sidebar: Players & Eval -->
                <div class="lg:col-span-3 space-y-6">
                    <div
                        class="bg-white border-2 border-gray-100 p-6 rounded-2xl shadow-sm"
                    >
                        <div class="space-y-4">
                            <div class="flex items-center justify-between">
                                <span
                                    class="text-xs font-black uppercase tracking-widest text-gray-400"
                                    >White</span
                                >
                                <span
                                    class="text-xs bg-gray-100 px-2 py-0.5 rounded font-bold uppercase"
                                    >Bot A</span
                                >
                            </div>
                            <h3 class="text-xl font-black truncate">
                                {match.bot_a.bot.name}
                            </h3>

                            <hr class="border-gray-50" />

                            <div class="flex items-center justify-between">
                                <span
                                    class="text-xs font-black uppercase tracking-widest text-gray-400"
                                    >Black</span
                                >
                                <span
                                    class="text-xs bg-gray-900 text-white px-2 py-0.5 rounded font-bold uppercase"
                                    >Bot B</span
                                >
                            </div>
                            <h3 class="text-xl font-black truncate">
                                {match.bot_b.bot.name}
                            </h3>
                        </div>
                    </div>

                    <div
                        class="bg-gray-900 text-white p-6 rounded-2xl shadow-xl overflow-hidden relative"
                    >
                        <h4
                            class="text-xs font-black uppercase tracking-widest text-gray-500 mb-4"
                        >
                            Global Evaluation <span
                                class="text-[10px] ml-2 opacity-50"
                                >(White's Perspective)</span
                            >
                        </h4>
                        <div class="flex flex-col items-center">
                            <div
                                class="text-4xl font-black mb-2 transition-all duration-300"
                                class:text-green-400={currentEval > 0}
                                class:text-red-400={currentEval < 0}
                            >
                                {currentEval > 0
                                    ? "+"
                                    : ""}{currentEval.toFixed(2)}
                            </div>
                            <!-- Simple Eval Bar -->
                            <div
                                class="w-full h-4 bg-gray-800 rounded-full overflow-hidden flex"
                            >
                                <div
                                    class="h-full bg-white transition-all duration-500"
                                    style="width: {50 + currentEval * 5}%"
                                ></div>
                            </div>
                            <div
                                class="w-full flex justify-between mt-2 text-[10px] font-bold uppercase text-gray-600"
                            >
                                <span class="text-left w-1/2"
                                    >Black Advantage</span
                                >
                                <span class="text-right w-1/2"
                                    >White Advantage</span
                                >
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Center: Board -->
                <div class="lg:col-span-6 space-y-6">
                    <ChessBoard
                        fen={currentFen}
                        {lastMove}
                        turn={currentMoveIdx % 2 === 0 ? "b" : "w"}
                    />

                    <div
                        class="bg-white border-2 border-gray-100 p-4 rounded-2xl shadow-sm flex items-center justify-between gap-4"
                    >
                        <div class="flex items-center gap-2">
                            <button
                                onclick={() => (currentMoveIdx = -1)}
                                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="First Move"
                                aria-label="First Move"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    ><path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M11 19l-7-7 7-7m8 14l-7-7 7-7"
                                    /></svg
                                >
                            </button>
                            <button
                                onclick={() => step(-1)}
                                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Previous Move"
                                aria-label="Previous Move"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    ><path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M15 19l-7-7 7-7"
                                    /></svg
                                >
                            </button>

                            <button
                                onclick={togglePlay}
                                class="w-12 h-12 bg-black text-white rounded-full flex items-center justify-center hover:scale-105 active:scale-95 transition-all shadow-lg"
                                aria-label={isPlaying ? "Pause" : "Play"}
                            >
                                {#if isPlaying}
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        class="h-6 w-6"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                        ><path
                                            fill-rule="evenodd"
                                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zM7 8a1 1 0 012 0v4a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v4a1 1 0 102 0V8a1 1 0 00-1-1z"
                                            clip-rule="evenodd"
                                        /></svg
                                    >
                                {:else}
                                    <svg
                                        xmlns="http://www.w3.org/2000/svg"
                                        class="h-6 w-6 ml-1"
                                        fill="currentColor"
                                        viewBox="0 0 20 20"
                                        ><path
                                            fill-rule="evenodd"
                                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z"
                                            clip-rule="evenodd"
                                        /></svg
                                    >
                                {/if}
                            </button>

                            <button
                                onclick={() => step(1)}
                                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Next Move"
                                aria-label="Next Move"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    ><path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M9 5l7 7-7 7"
                                    /></svg
                                >
                            </button>
                            <button
                                onclick={() =>
                                    (currentMoveIdx = history.length - 1)}
                                class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Last Move"
                                aria-label="Last Move"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                    ><path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M13 5l7 7-7 7M5 5l7 7-7 7"
                                    /></svg
                                >
                            </button>
                        </div>

                        <div
                            class="flex items-center gap-2 text-sm font-bold text-gray-500"
                        >
                            Move {currentMoveIdx === -1
                                ? 0
                                : Math.floor(currentMoveIdx / 2) + 1} / {Math.floor(
                                history.length / 2,
                            )}
                        </div>
                    </div>
                </div>

                <!-- Right Sidebar: history & Thinking -->
                <div class="lg:col-span-3 space-y-6">
                    <div
                        class="bg-white border-2 border-gray-100 rounded-2xl shadow-sm overflow-hidden flex flex-col h-[600px]"
                    >
                        <div class="p-2 border-b bg-gray-50 flex gap-2">
                            <button
                                onclick={() => (activeTab = "moves")}
                                class="flex-grow py-2 px-4 rounded-lg text-xs font-black uppercase tracking-widest transition-all {activeTab ===
                                'moves'
                                    ? 'bg-black text-white shadow-lg'
                                    : 'text-gray-400 hover:bg-gray-200'}"
                                >History</button
                            >
                            <button
                                onclick={() => (activeTab = "thinking")}
                                class="flex-grow py-2 px-4 rounded-lg text-xs font-black uppercase tracking-widest transition-all {activeTab ===
                                'thinking'
                                    ? 'bg-black text-white shadow-lg'
                                    : 'text-gray-400 hover:bg-gray-200'}"
                                >Thinking</button
                            >
                        </div>

                        {#if activeTab === "moves"}
                            <div
                                class="p-4 overflow-y-auto grid grid-cols-2 gap-2 text-sm custom-scrollbar flex-grow"
                            >
                                {#each history as move, i}
                                    <button
                                        onclick={() => (currentMoveIdx = i)}
                                        class="p-2 rounded-lg text-left transition-all {currentMoveIdx ===
                                        i
                                            ? 'bg-black text-white font-bold'
                                            : 'hover:bg-gray-100'}"
                                        aria-label={`Go to move ${i + 1}`}
                                    >
                                        <span
                                            class="text-[10px] opacity-50 mr-1"
                                            >{i % 2 === 0
                                                ? Math.floor(i / 2) + 1 + "."
                                                : ""}</span
                                        >
                                        {move.san}
                                    </button>
                                {/each}
                            </div>
                        {:else}
                            <div
                                class="p-4 overflow-y-auto flex-grow custom-scrollbar space-y-4"
                            >
                                {#if currentThinking}
                                    <div
                                        class="flex items-center justify-between mb-4"
                                    >
                                        <span
                                            class="text-[10px] font-black uppercase tracking-widest text-gray-400"
                                            >Next to move:</span
                                        >
                                        <span
                                            class="text-[10px] font-black uppercase tracking-widest px-2 py-0.5 rounded {thinkingColor}"
                                            >{currentThinking.turn}</span
                                        >
                                    </div>

                                    <div class="space-y-2">
                                        {#each Object.entries(currentThinking.top_moves).sort((a, b) => b[1] - a[1]) as [move, val]}
                                            <div
                                                class="flex items-center justify-between p-3 bg-gray-50 rounded-xl group hover:bg-gray-100 transition-colors"
                                            >
                                                <span
                                                    class="font-mono font-bold text-gray-700"
                                                    >{move}</span
                                                >
                                                <div
                                                    class="flex items-center gap-2"
                                                >
                                                    {#if val === currentThinking.eval}
                                                        <span
                                                            class="text-[8px] bg-green-500 text-white px-1.5 py-0.5 rounded font-black uppercase"
                                                            >Best</span
                                                        >
                                                    {/if}
                                                    <span
                                                        class="text-sm font-black {val >
                                                        0
                                                            ? 'text-green-600'
                                                            : 'text-red-500'}"
                                                    >
                                                        {val > 0
                                                            ? "+"
                                                            : ""}{val.toFixed(
                                                            2,
                                                        )}
                                                    </span>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {:else}
                                    <div
                                        class="h-full flex flex-col items-center justify-center text-center p-8"
                                    >
                                        <div
                                            class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4 text-xl"
                                        >
                                            ⏳
                                        </div>
                                        <p
                                            class="text-xs font-bold text-gray-400 uppercase tracking-widest"
                                        >
                                            No thinking data available for this
                                            position.
                                        </p>
                                    </div>
                                {/if}
                            </div>
                        {/if}

                        <div class="p-6 bg-gray-900 text-white mt-auto">
                            <h4
                                class="text-xs font-black uppercase tracking-widest text-gray-500 mb-2"
                            >
                                Final Result
                            </h4>
                            <div class="text-lg font-bold mb-1">
                                {match.winner === "draw"
                                    ? "Draw"
                                    : `Winner: ${match.winner === "A" ? match.bot_a.bot.name : match.bot_b.bot.name}`}
                            </div>
                            <div
                                class="text-xs text-gray-400 font-medium lowercase"
                            >
                                Reason: {match.termination_reason}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        {:else if match.status === "failed"}
            <!-- ... same error state ... -->
            <div class="max-w-md mx-auto text-center py-20">
                <div
                    class="w-20 h-20 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto mb-6"
                >
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-10 w-10"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        ><path
                            stroke-linecap="round"
                            stroke-linejoin="round"
                            stroke-width="2"
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        /></svg
                    >
                </div>
                <h2 class="text-3xl font-black mb-4">Match Failed</h2>
                <p class="text-gray-500 mb-8 font-medium">
                    The deep blue circuitry encountered a fatal error during
                    evaluation. Check server logs for details.
                </p>
                <a
                    href="/dashboard"
                    class="inline-block bg-black text-white px-8 py-3 rounded-xl font-bold hover:scale-105 transition-all"
                    >Back to Dashboard</a
                >
            </div>
        {:else}
            <!-- ... same loading state ... -->
            <div
                class="flex flex-col items-center justify-center min-h-[500px]"
            >
                <div class="relative w-24 h-24 mb-6">
                    <div
                        class="absolute inset-0 border-8 border-gray-100 rounded-full"
                    ></div>
                    <div
                        class="absolute inset-0 border-8 border-t-black rounded-full animate-spin"
                    ></div>
                </div>
                <h2 class="text-2xl font-black mb-2 animate-pulse">
                    Bots Are Battling...
                </h2>
                <p class="text-gray-400 font-medium">
                    Computing millions of legal moves per second
                </p>
                <div class="mt-8 flex gap-4">
                    <div
                        class="bg-gray-100 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-widest text-gray-500"
                    >
                        Status: {match.status}
                    </div>
                </div>
            </div>
        {/if}
    {:else}
        <div class="flex flex-col items-center justify-center min-h-[500px]">
            <span
                class="w-12 h-12 border-4 border-gray-100 border-t-black rounded-full animate-spin"
            ></span>
        </div>
    {/if}
</div>

<style>
    :global(body) {
        background-color: #f9fafb;
    }

    .custom-scrollbar::-webkit-scrollbar {
        width: 4px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #e5e7eb;
        border-radius: 10px;
    }
</style>
