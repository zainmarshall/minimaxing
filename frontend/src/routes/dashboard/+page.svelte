<script lang="ts">
    import { onMount } from "svelte";
    import { supabase } from "$lib/supabaseClient";

    interface Bot {
        id: string;
        name: string;
        user_id: string;
        status: string;
        active_version_id: string | null;
    }

    /** @type {any[]} */
    let bots = $state<Bot[]>([]);
    /** @type {import('@supabase/supabase-js').User | null} */
    let user = $state<any>(null);
    let newBotName = $state("");
    let isCreating = $state(false);
    let errorMessage = $state("");
    let selectedBotA = $state("");
    let selectedBotB = $state("");
    let uploadFileInput: HTMLInputElement | null = null;
    let selectedBotForUpload = $state("");
    let isUploading = $state(false);

    onMount(async () => {
        const {
            data: { session },
        } = await supabase.auth.getSession();
        if (session) {
            user = session.user;
            await fetchBots();
        } else {
            errorMessage = "Please sign in to manage bots.";
        }
    });

    async function fetchBots() {
        if (!user) return;
        const { data, error } = await supabase
            .from("bots")
            .select("*")
            .eq("user_id", user.id);
        if (error) {
            console.error("Error fetching bots:", error.message);
            errorMessage = "Failed to load bots: " + error.message;
        } else {
            bots = data as Bot[];
        }
    }

    async function createBot() {
        if (!user) {
            errorMessage = "You must be logged in to create a bot.";
            return;
        }
        if (!newBotName.trim()) {
            errorMessage = "Please enter a bot name.";
            return;
        }

        isCreating = true;
        errorMessage = "";

        try {
            const { data, error } = await supabase
                .from("bots")
                .insert([{ name: newBotName.trim(), user_id: user.id }])
                .select();

            if (error) {
                console.error("Error creating bot:", error);
                errorMessage = "Error: " + error.message;
            } else {
                newBotName = "";
                await fetchBots();
            }
        } catch (e) {
            console.error("Unexpected error:", e);
            errorMessage = "An unexpected error occurred.";
        } finally {
            isCreating = false;
        }
    }

    async function startMatch() {
        if (!selectedBotA || !selectedBotB) return;

        const response = await fetch(
            "http://localhost:8000/api/matches/trigger",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    bot_a_version: selectedBotA,
                    bot_b_version: selectedBotB,
                }),
            },
        );

        if (response.ok) {
            const data = await response.json();
            window.location.href = `/match/${data.match_id}`;
        } else {
            const err = await response.json();
            errorMessage = "Failed to start match: " + err.detail;
        }
    }

    async function uploadBotFile() {
        if (!selectedBotForUpload) {
            errorMessage = "Select a bot to attach the uploaded version to.";
            return;
        }
        if (!uploadFileInput || !uploadFileInput.files || uploadFileInput.files.length === 0) {
            errorMessage = "Please choose a JSON file to upload.";
            return;
        }

        isUploading = true;
        errorMessage = "";

        try {
            const file = uploadFileInput.files[0];
            const form = new FormData();
            form.append("file", file);

            const url = `http://localhost:8000/api/bots/upload?bot_id=${encodeURIComponent(
                selectedBotForUpload,
            )}&search_depth=3`;

            const resp = await fetch(url, {
                method: "POST",
                body: form,
            });

            if (!resp.ok) {
                const err = await resp.json().catch(() => ({ detail: "Unknown error" }));
                errorMessage = "Upload failed: " + (err.detail || resp.statusText);
            } else {
                await fetchBots();
            }
        } catch (e) {
            console.error(e);
            errorMessage = "Unexpected error during upload.";
        } finally {
            isUploading = false;
            if (uploadFileInput) uploadFileInput.value = "";
        }
    }
</script>

<div class="max-w-4xl mx-auto py-8 px-4">
    <h1 class="text-4xl font-black mb-8 border-b pb-4">Dashboard</h1>

    {#if errorMessage}
        <div class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-red-700">
            {errorMessage}
        </div>
    {/if}

    <div class="mb-12">
        <h2 class="text-2xl font-bold mb-6 flex items-center gap-2">
            <span>My Bots</span>
            <span
                class="text-sm bg-gray-200 px-2 py-0.5 rounded-full text-gray-600"
                >{bots.length}</span
            >
        </h2>

        {#if bots.length === 0}
            <div
                class="bg-gray-50 border-2 border-dashed rounded-xl p-12 text-center text-gray-500"
            >
                You haven't created any bots yet.
            </div>
        {:else}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {#each bots as bot}
                    <div
                        class="group border-2 border-transparent bg-white shadow-sm hover:shadow-md hover:border-gray-200 p-6 rounded-xl transition-all"
                    >
                        <h3 class="font-bold text-xl mb-1">{bot.name}</h3>
                        <div class="flex items-center gap-2 mb-4">
                            <span class="w-2 h-2 rounded-full bg-green-500"
                            ></span>
                            <span
                                class="text-sm font-medium uppercase tracking-wider text-gray-500"
                                >{bot.status}</span
                            >
                        </div>
                        <a
                            href="/bot/{bot.id}"
                            class="inline-block w-full py-2 text-center bg-gray-50 group-hover:bg-gray-900 group-hover:text-white rounded-lg font-bold transition-colors"
                        >
                            Configure Bot
                        </a>
                    </div>
                {/each}
            </div>
        {/if}
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-12">
        <div
            class="bg-white border-2 border-gray-100 p-8 rounded-2xl shadow-sm"
        >
            <h2 class="text-2xl font-bold mb-4">Create New Bot</h2>
            <div class="flex flex-col gap-3">
                <input
                    type="text"
                    bind:value={newBotName}
                    placeholder="Ex: DeepBlue 2025"
                    class="flex-grow border-2 border-gray-100 p-3 rounded-xl focus:border-gray-900 focus:outline-none transition-colors"
                    disabled={isCreating}
                />
                <button
                    onclick={createBot}
                    class="bg-gray-900 text-white px-8 py-3 rounded-xl font-bold hover:bg-black active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg hover:shadow-xl flex items-center justify-center gap-2"
                    aria-label="Create Bot"
                    disabled={isCreating}
                >
                    {#if isCreating}
                        <span
                            class="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"
                        ></span>
                        Creating...
                    {:else}
                        Create Bot
                    {/if}
                </button>
            </div>
        </div>

        <div class="bg-gray-900 text-white p-8 rounded-2xl shadow-xl">
            <h2 class="text-2xl font-bold mb-4">Match Maker</h2>
            <div class="space-y-4">
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label
                            class="block text-xs font-bold uppercase tracking-widest text-gray-400 mb-1"
                            for="bot-a-select">Bot A</label
                        >
                        <select
                            id="bot-a-select"
                            bind:value={selectedBotA}
                            class="w-full bg-gray-800 border border-gray-700 p-2 rounded-lg text-sm outline-none focus:border-white transition-colors"
                        >
                            {#each bots as bot}
                                {#if bot.active_version_id}
                                    <option value={bot.active_version_id}
                                        >{bot.name}</option
                                    >
                                {/if}
                            {/each}
                        </select>
                    </div>
                    <div>
                        <label
                            class="block text-xs font-bold uppercase tracking-widest text-gray-400 mb-1"
                            for="bot-b-select">Bot B</label
                        >
                        <select
                            id="bot-b-select"
                            bind:value={selectedBotB}
                            class="w-full bg-gray-800 border border-gray-700 p-2 rounded-lg text-sm outline-none focus:border-white transition-colors"
                        >
                            {#each bots as bot}
                                {#if bot.active_version_id}
                                    <option value={bot.active_version_id}
                                        >{bot.name}</option
                                    >
                                {/if}
                            {/each}
                        </select>
                    </div>
                </div>
                <button
                    onclick={startMatch}
                    disabled={!selectedBotA || !selectedBotB}
                    class="w-full bg-white text-black py-3 rounded-xl font-bold hover:bg-gray-200 active:scale-95 transition-all disabled:opacity-50"
                    aria-label="Start Battle"
                >
                    Start Battle
                </button>
            </div>
        </div>
    </div>

    <div class="bg-white border-2 border-gray-100 p-8 rounded-2xl shadow-sm">
        <h2 class="text-2xl font-bold mb-4">Upload Bot Version</h2>
        <div class="flex flex-col gap-3">
            <label class="text-sm font-medium">Attach to Bot</label>
            <select bind:value={selectedBotForUpload} class="p-2 border rounded-lg">
                <option value="">-- select bot --</option>
                {#each bots as bot}
                    <option value={bot.id}>{bot.name}</option>
                {/each}
            </select>

            <label class="text-sm font-medium">Bot JSON File</label>
            <input bind:this={uploadFileInput} type="file" accept="application/json" class="p-2" />

            <div class="flex gap-3">
                <button
                    onclick={uploadBotFile}
                    disabled={isUploading}
                    class="bg-gray-900 text-white px-4 py-2 rounded-lg font-bold disabled:opacity-50"
                >
                    {#if isUploading}
                        Uploading...
                    {:else}
                        Upload
                    {/if}
                </button>
                <button
                    onclick={() => { selectedBotForUpload = ""; if (uploadFileInput) uploadFileInput.value = "" }}
                    class="bg-gray-100 text-black px-4 py-2 rounded-lg"
                >
                    Clear
                </button>
            </div>
        </div>
    </div>
</div>
