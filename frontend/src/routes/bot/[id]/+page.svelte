<script lang="ts">
    import { onMount } from "svelte";
    import { page } from "$app/stores";
    import { supabase } from "$lib/supabaseClient";

    interface Bot {
        id: string;
        name: string;
        active_version_id: string | null;
        status: string;
    }

    interface Rule {
        id?: string;
        name: string;
        code: string;
        weight: number;
    }

    interface Version {
        id: string;
        search_depth: number;
        rules_json: Rule[];
        created_at: string;
    }

    const botId = $page.params.id;
    let bot = $state<Bot | null>(null);
    let versions = $state<Version[]>([]);
    let newRule = $state<Rule>({ name: "", code: "", weight: 1.0 });
    let rules = $state<Rule[]>([]);
    let searchDepth = $state(3);

    let isSaving = $state(false);
    let showSuccess = $state(false);
    let errorMessage = $state("");
    let isScriptMode = $state(false);
    let loadedVersionId = $state<string | null>(null);

    onMount(async () => {
        fetchBot();
        fetchVersions();
    });

    async function fetchBot() {
        const { data, error } = await supabase
            .from("bots")
            .select("*")
            .eq("id", botId)
            .single();
        if (error) {
            console.error("Error fetching bot:", error.message);
            errorMessage = "Failed to load bot details.";
        } else {
            bot = data;
        }
    }

    async function fetchVersions() {
        const { data, error } = await supabase
            .from("bot_versions")
            .select("*")
            .eq("bot_id", botId)
            .order("created_at", { ascending: false });
        if (error) console.error("Error fetching versions:", error.message);
        else versions = data;
    }

    async function loadVersion(v: Version) {
        // If script-based, put into single-script staged rule
        try {
            const rj = v.rules_json || [];
            if (rj.length > 0 && typeof rj[0] === 'object' && 'script' in rj[0]) {
                isScriptMode = true;
                rules = [{ name: 'script', code: rj[0].script, weight: 1 }];
            } else {
                isScriptMode = false;
                rules = (rj as Rule[]).map((r: any) => ({ name: r.name || 'unnamed', code: r.code || '', weight: r.weight || 1 }));
            }
            searchDepth = v.search_depth || 3;
            loadedVersionId = v.id;
            errorMessage = '';
            window.scrollTo({ top: 0, behavior: 'smooth' });
        } catch (e) {
            console.error(e);
            errorMessage = 'Failed to load version into editor.';
        }
    }

    async function cloneVersion(v: Version) {
        try {
            const resp = await fetch(`http://localhost:8000/api/bots/versions/${v.id}/clone`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ bot_id: botId })
            });
            if (!resp.ok) {
                const err = await resp.json();
                errorMessage = 'Clone failed: ' + (err.detail || resp.statusText);
                return;
            }
            await fetchVersions();
            await fetchBot();
        } catch (e) {
            console.error(e);
            errorMessage = 'Unexpected error cloning version.';
        }
    }

    async function deleteVersionById(v: Version) {
        if (!confirm('Delete this version? This action cannot be undone.')) return;
        try {
            const resp = await fetch(`http://localhost:8000/api/bots/versions/${v.id}`, { method: 'DELETE' });
            if (!resp.ok) {
                const err = await resp.json();
                errorMessage = 'Delete failed: ' + (err.detail || resp.statusText);
                return;
            }
            await fetchVersions();
            await fetchBot();
        } catch (e) {
            console.error(e);
            errorMessage = 'Unexpected error deleting version.';
        }
    }

    async function downloadVersion(v: Version) {
        try {
            const resp = await fetch(`http://localhost:8000/api/bots/versions/${v.id}`);
            if (!resp.ok) { errorMessage = 'Failed to fetch version'; return; }
            const data = await resp.json();
            const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${bot?.name || 'bot'}-${v.id}.json`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(url);
        } catch (e) {
            console.error(e);
            errorMessage = 'Download failed.';
        }
    }

    async function deleteBot() {
        if (!confirm('Delete this bot and all its versions?')) return;
        try {
            const resp = await fetch(`http://localhost:8000/api/bots/${botId}`, { method: 'DELETE' });
            if (!resp.ok) { const err = await resp.json(); errorMessage = 'Failed to delete bot: ' + (err.detail || resp.statusText); return; }
            window.location.href = '/dashboard';
        } catch (e) {
            console.error(e);
            errorMessage = 'Unexpected error deleting bot.';
        }
    }

    function addRule() {
        if (!newRule.name || !newRule.code) {
            errorMessage = "Rule name and code are required.";
            return;
        }
        rules = [...rules, { ...newRule, id: crypto.randomUUID() }];
        newRule = { name: "", code: "", weight: 1.0 };
        errorMessage = "";
    }

    function removeRule(id: string) {
        rules = rules.filter((r) => r.id !== id);
    }

    async function saveVersion() {
        if (rules.length === 0) {
            errorMessage = "Add at least one rule before saving.";
            return;
        }

        isSaving = true;
        errorMessage = "";
        showSuccess = false;

        try {
            let resp;

            if (isScriptMode) {
                const scriptCode = rules[0].code;
                if (loadedVersionId) {
                    // Update existing version
                    resp = await fetch(`http://localhost:8000/api/bots/versions/${loadedVersionId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rules: [{ script: scriptCode }], search_depth: searchDepth })
                    });
                } else {
                    // Create new script version
                    resp = await fetch(`http://localhost:8000/api/bots/upload-script`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bot_id: botId, code: scriptCode, search_depth: searchDepth })
                    });
                }
            } else {
                const payload = { bot_id: botId, rules: rules.map(({ name, code, weight }) => ({ name, code, weight })), search_depth: searchDepth };
                if (loadedVersionId) {
                    // update existing (legacy)
                    resp = await fetch(`http://localhost:8000/api/bots/versions/${loadedVersionId}`, {
                        method: 'PATCH',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ rules: payload.rules, search_depth: payload.search_depth })
                    });
                } else {
                    resp = await fetch('http://localhost:8000/api/bots/versions', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(payload)
                    });
                }
            }

            if (resp && resp.ok) {
                rules = [];
                loadedVersionId = null;
                isScriptMode = false;
                showSuccess = true;
                await fetchVersions();
                await fetchBot();
                setTimeout(() => { showSuccess = false; }, 5000);
            } else {
                const err = resp ? await resp.json().catch(() => ({})) : { detail: 'No response' };
                errorMessage = `Error saving version: ${err.detail || 'Unknown error'}`;
            }
        } catch (e) {
            console.error("Unexpected error:", e);
            errorMessage =
                "An unexpected error occurred while connecting to the backend.";
        } finally {
            isSaving = false;
        }
    }
</script>

<div class="max-w-6xl mx-auto py-8 px-4">
    {#if bot}
        <div
            class="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4 border-b pb-6"
        >
            <div>
                <a
                    href="/dashboard"
                    class="text-sm font-bold text-gray-500 hover:text-black mb-2 inline-block transition-colors"
                    >← Back to Dashboard</a
                >
                <h1 class="text-4xl font-black">{bot.name}</h1>
                <p class="text-gray-500 font-medium">
                    Configure evaluation rules and search parameters
                </p>
            </div>

            <div
                class="bg-gray-100 px-4 py-2 rounded-lg flex items-center gap-2"
            >
                <span class="w-3 h-3 rounded-full bg-green-500 animate-pulse"
                ></span>
                <span
                    class="text-sm font-bold uppercase tracking-widest text-gray-700"
                    >Live: {bot.active_version_id
                        ? bot.active_version_id.slice(0, 8)
                        : "None"}</span
                >
            </div>
        </div>

        {#if errorMessage}
            <div
                class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-red-700 flex justify-between items-center shadow-sm rounded-r-lg"
            >
                <div class="flex items-center gap-3">
                    <svg
                        xmlns="http://www.w3.org/2000/svg"
                        class="h-5 w-5"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                    >
                        <path
                            fill-rule="evenodd"
                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                            clip-rule="evenodd"
                        />
                    </svg>
                    <span class="font-medium">{errorMessage}</span>
                </div>
                <button
                    onclick={() => (errorMessage = "")}
                    class="hover:text-red-900"
                    aria-label="Close error message"
                >
                    &times;
                </button>
            </div>
        {/if}

        {#if showSuccess}
            <div
                class="bg-green-50 border-l-4 border-green-500 p-4 mb-6 text-green-700 flex items-center gap-3 shadow-sm rounded-r-lg animate-in fade-in slide-in-from-top-2 duration-300"
            >
                <svg
                    xmlns="http://www.w3.org/2000/svg"
                    class="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                >
                    <path
                        fill-rule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clip-rule="evenodd"
                    />
                </svg>
                <span class="font-bold"
                    >New version successfully deployed and activated!</span
                >
            </div>
        {/if}

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div class="lg:col-span-2 space-y-8">
                <section
                    class="bg-white border-2 border-gray-100 p-8 rounded-2xl shadow-sm"
                >
                    <h2 class="text-2xl font-bold mb-6 flex items-center gap-2">
                        <span class="p-2 bg-gray-100 rounded-lg">🛠️</span>
                        New Version Construction
                    </h2>

                    <div class="space-y-6">
                        <div
                            class="bg-gray-50 p-6 rounded-xl border border-gray-100"
                        >
                            <h3
                                class="font-bold text-lg mb-4 flex items-center gap-2 text-gray-700"
                            >
                                <span>1. Search Parameters</span>
                            </h3>
                            <label class="flex flex-col gap-2 max-w-xs">
                                <span
                                    class="text-sm font-bold text-gray-500 uppercase tracking-wider"
                                    >Computation Depth</span
                                >
                                <div class="flex items-center gap-4">
                                    <input
                                        type="range"
                                        bind:value={searchDepth}
                                        min="1"
                                        max="5"
                                        step="1"
                                        class="flex-grow accent-black"
                                    />
                                    <span
                                        class="w-12 h-12 bg-black text-white rounded-xl flex items-center justify-center font-black text-xl shadow-lg"
                                        >{searchDepth}</span
                                    >
                                </div>
                                <p class="text-xs text-gray-400 mt-1">
                                    Deeper search increases strength but takes
                                    longer to compute.
                                </p>
                            </label>
                        </div>

                        <div
                            class="bg-white p-6 rounded-xl border-2 border-dashed border-gray-200"
                        >
                            <h3
                                class="font-bold text-lg mb-4 flex items-center gap-2 text-gray-700"
                            >
                                <span>2. Evaluation Rules</span>
                            </h3>

                            <div
                                class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4"
                            >
                                <input
                                    type="text"
                                    placeholder="Rule Display Name (e.g. Center Control)"
                                    bind:value={newRule.name}
                                    class="border-2 border-gray-100 p-3 rounded-xl focus:border-black outline-none transition-all font-medium"
                                />
                                <input
                                    type="number"
                                    step="0.1"
                                    placeholder="Importance Weight"
                                    bind:value={newRule.weight}
                                    class="border-2 border-gray-100 p-3 rounded-xl focus:border-black outline-none transition-all font-medium"
                                />
                            </div>
                            <textarea
                                placeholder="Python Evaluation Code (e.g. len(board.pieces(chess.PAWN, chess.WHITE)))"
                                bind:value={newRule.code}
                                class="w-full border-2 border-gray-100 p-4 rounded-xl focus:border-black outline-none transition-all font-mono text-sm mb-4 min-h-[100px]"
                            ></textarea>

                            <button
                                onclick={addRule}
                                class="w-full py-3 bg-gray-100 hover:bg-gray-200 text-gray-900 rounded-xl font-bold transition-all flex items-center justify-center gap-2"
                            >
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-5 w-5"
                                    viewBox="0 0 20 20"
                                    fill="currentColor"
                                >
                                    <path
                                        fill-rule="evenodd"
                                        d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z"
                                        clip-rule="evenodd"
                                    />
                                </svg>
                                Add Rule to Set
                            </button>
                        </div>

                        {#if rules.length > 0}
                            <div class="space-y-3">
                                <h3
                                    class="text-sm font-bold text-gray-500 uppercase tracking-wider px-2"
                                >
                                    Staged Rules ({rules.length})
                                </h3>
                                {#each rules as rule}
                                    <div
                                        class="group bg-white border-2 border-gray-100 p-4 rounded-xl flex justify-between items-center hover:border-gray-300 transition-all shadow-sm"
                                    >
                                        <div class="flex-grow">
                                            <div
                                                class="flex items-center gap-2 mb-1"
                                            >
                                                <span class="font-bold"
                                                    >{rule.name}</span
                                                >
                                                <span
                                                    class="text-xs bg-black text-white px-2 py-0.5 rounded-full"
                                                    >Weight: {rule.weight}</span
                                                >
                                            </div>
                                            <code
                                                class="text-xs text-blue-600 font-bold block bg-blue-50 p-2 rounded-lg"
                                                >{rule.code}</code
                                            >
                                        </div>
                                        <button
                                            onclick={() =>
                                                rule.id && removeRule(rule.id)}
                                            class="p-2 text-gray-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                                            aria-label="Remove rule"
                                        >
                                            <svg
                                                xmlns="http://www.w3.org/2000/svg"
                                                class="h-6 w-6"
                                                fill="none"
                                                viewBox="0 0 24 24"
                                                stroke="currentColor"
                                            >
                                                <path
                                                    stroke-linecap="round"
                                                    stroke-linejoin="round"
                                                    stroke-width="2"
                                                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                                                />
                                            </svg>
                                        </button>
                                    </div>
                                {/each}
                            </div>
                        {/if}

                        <button
                            onclick={saveVersion}
                            disabled={isSaving || rules.length === 0}
                            class="w-full py-4 bg-gray-900 text-white rounded-2xl font-black text-xl hover:bg-black active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-xl hover:shadow-2xl flex items-center justify-center gap-3 mt-8"
                        >
                            {#if isSaving}
                                <span
                                    class="w-6 h-6 border-4 border-white/30 border-t-white rounded-full animate-spin"
                                ></span>
                                Processing Rule Security...
                            {:else}
                                <svg
                                    xmlns="http://www.w3.org/2000/svg"
                                    class="h-6 w-6"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                    stroke="currentColor"
                                >
                                    <path
                                        stroke-linecap="round"
                                        stroke-linejoin="round"
                                        stroke-width="2"
                                        d="M13 10V3L4 14h7v7l9-11h-7z"
                                    />
                                </svg>
                                Save & Activate Version
                            {/if}
                        </button>
                    </div>
                </section>
            </div>

            <div class="space-y-8">
                <section
                    class="bg-gray-900 text-white p-8 rounded-2xl shadow-xl"
                >
                    <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
                        <span class="p-2 bg-gray-800 rounded-lg">📜</span>
                        Version History
                    </h2>

                    {#if versions.length === 0}
                        <div
                            class="text-center py-12 text-gray-500 border-2 border-dashed border-gray-800 rounded-xl"
                        >
                            No versions deployed yet.
                        </div>
                    {:else}
                        <div
                            class="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar"
                        >
                            {#each versions as v}
                                <div
                                    class="bg-gray-800/50 border border-gray-700/50 p-4 rounded-xl hover:bg-gray-800 transition-colors relative group"
                                >
                                    {#if v.id === bot.active_version_id}
                                        <div
                                            class="absolute -top-2 -right-2 bg-green-500 text-[10px] font-black uppercase px-2 py-1 rounded-md shadow-lg border-2 border-gray-900"
                                        >
                                            Active
                                        </div>
                                    {/if}

                                    <div
                                        class="flex justify-between items-start mb-3"
                                    >
                                        <span
                                            class="text-xs font-mono text-gray-400 bg-gray-900 px-2 py-1 rounded"
                                            >#{v.id.slice(0, 8)}</span
                                        >
                                        <span
                                            class="text-[10px] text-gray-500 font-bold uppercase"
                                            >{new Date(
                                                v.created_at,
                                            ).toLocaleDateString()}</span
                                        >
                                    </div>

                                    <div class="grid grid-cols-2 gap-2">
                                        <div
                                            class="bg-gray-900/50 p-2 rounded flex flex-col items-center"
                                        >
                                            <span
                                                class="text-[10px] text-gray-500 font-bold uppercase"
                                                >Depth</span
                                            >
                                            <span class="font-black text-lg"
                                                >{v.search_depth}</span
                                            >
                                        </div>
                                        <div
                                            class="bg-gray-900/50 p-2 rounded flex flex-col items-center"
                                        >
                                            <span
                                                class="text-[10px] text-gray-500 font-bold uppercase"
                                                >Rules</span
                                            >
                                            <span class="font-black text-lg"
                                                >{v.rules_json.length}</span
                                            >
                                        </div>
                                    </div>
                                </div>
                                    <div class="mt-3 flex gap-2 flex-wrap">
                                        {#each versions as v}
                                            <div class="bg-gray-700/40 p-3 rounded-lg w-full group-hover:w-auto">
                                                <div class="flex items-start justify-between gap-3">
                                                    <div class="flex-1">
                                                        <div class="flex items-center gap-2">
                                                            <span class="font-mono text-xs">#{v.id.slice(0,8)}</span>
                                                            <span class="text-xs text-gray-400">{new Date(v.created_at).toLocaleString()}</span>
                                                        </div>
                                                        <div class="text-xs text-gray-300">Depth: {v.search_depth} • Rules: {v.rules_json.length}</div>
                                                    </div>
                                                    <div class="flex gap-2">
                                                        <button onclick={() => loadVersion(v)} class="px-2 py-1 rounded bg-gray-600 text-xs">Load</button>
                                                        <button onclick={() => downloadVersion(v)} class="px-2 py-1 rounded bg-gray-600 text-xs">Download</button>
                                                        <button onclick={() => cloneVersion(v)} class="px-2 py-1 rounded bg-green-600 text-xs">Clone</button>
                                                        <button onclick={() => deleteVersionById(v)} class="px-2 py-1 rounded bg-red-600 text-xs">Delete</button>
                                                    </div>
                                                </div>
                                            </div>
                                        {/each}
                                    </div>
                                {/each}
                        </div>
                    {/if}
                </section>
                    <div class="mt-4">
                        <button onclick={deleteBot} class="bg-red-600 text-white px-4 py-2 rounded-lg">Delete Bot</button>
                    </div>
            </div>
        </div>
    {:else}
        <div class="flex flex-col items-center justify-center min-h-[400px]">
            <span
                class="w-12 h-12 border-4 border-gray-200 border-t-black rounded-full animate-spin mb-4"
            ></span>
            <p class="font-bold text-gray-400">Loading neural pathways...</p>
        </div>
    {/if}
</div>

<style>
    .custom-scrollbar::-webkit-scrollbar {
        width: 6px;
    }
    .custom-scrollbar::-webkit-scrollbar-track {
        background: transparent;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb {
        background: #374151;
        border-radius: 10px;
    }
    .custom-scrollbar::-webkit-scrollbar-thumb:hover {
        background: #4b5563;
    }
</style>
