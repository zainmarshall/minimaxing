<script>
	import { onMount } from "svelte";
	import { supabase } from "$lib/supabaseClient";
	import "../app.css";

	/** @type {import('@supabase/supabase-js').Session | null} */
	let session = null;
	let email = "";
	let password = "";
	let isRegistering = false;
	let authError = "";
	let showAuthModal = false;

	onMount(() => {
		supabase.auth.getSession().then(({ data }) => {
			session = data.session;
		});

		supabase.auth.onAuthStateChange((_event, _session) => {
			session = _session;
		});
	});

	async function handleEmailAuth() {
		authError = "";
		const { data, error } = isRegistering
			? await supabase.auth.signUp({ email, password })
			: await supabase.auth.signInWithPassword({ email, password });

		if (error) {
			authError = error.message;
		} else {
			showAuthModal = false;
		}
	}

	async function signInWithGitHub() {
		authError = "";
		const { error } = await supabase.auth.signInWithOAuth({
			provider: "github",
			options: {
				redirectTo: window.location.origin,
			},
		});
		if (error) authError = error.message;
	}

	async function signOut() {
		const { error } = await supabase.auth.signOut();
		if (error) console.error("Error logging out:", error.message);
	}
</script>

<nav
	class="p-4 bg-gray-900 border-b border-gray-800 text-white flex justify-between items-center sticky top-0 z-50"
>
	<a
		href="/"
		class="text-2xl font-black tracking-tighter hover:text-gray-300 transition-colors"
		>♟ MINIMAXING</a
	>
	<div class="flex items-center gap-6">
		{#if session}
			<a
				href="/dashboard"
				class="font-medium hover:text-gray-300 transition-colors"
				>Dashboard</a
			>
			<button
				on:click={signOut}
				class="bg-red-500/10 text-red-400 border border-red-500/20 px-4 py-1.5 rounded-lg hover:bg-red-500 hover:text-white transition-all font-bold"
			>
				Sign Out
			</button>
		{:else}
			<button
				on:click={() => (showAuthModal = true)}
				class="bg-white text-black px-6 py-2 rounded-lg font-bold hover:bg-gray-200 transition-all shadow-lg"
			>
				Sign In
			</button>
		{/if}
	</div>
</nav>

{#if showAuthModal}
	<div
		class="fixed inset-0 bg-black/80 backdrop-blur-sm z-[100] flex items-center justify-center p-4"
	>
		<div
			class="bg-white text-black max-w-md w-full rounded-2xl shadow-2xl overflow-hidden"
		>
			<div class="p-8">
				<div class="flex justify-between items-center mb-8">
					<h2 class="text-3xl font-black">
						{isRegistering ? "Join" : "Welcome"}
					</h2>
					<button
						on:click={() => (showAuthModal = false)}
						class="text-gray-400 hover:text-black"
						aria-label="Close modal"
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
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				</div>

				{#if authError}
					<div
						class="bg-red-50 border-l-4 border-red-500 p-4 mb-6 text-red-700 text-sm"
					>
						{authError}
					</div>
				{/if}

				<button
					on:click={signInWithGitHub}
					class="w-full flex items-center justify-center gap-3 border-2 border-gray-100 py-3 rounded-xl font-bold hover:bg-gray-50 transition-all mb-6"
				>
					<svg class="h-5 w-5" viewBox="0 0 24 24"
						><path
							d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"
						/></svg
					>
					Continue with GitHub
				</button>

				<div class="relative mb-6">
					<div class="absolute inset-0 flex items-center">
						<div class="w-full border-t border-gray-100"></div>
					</div>
					<div class="relative flex justify-center text-sm">
						<span class="px-2 bg-white text-gray-500"
							>Or use email</span
						>
					</div>
				</div>

				<form
					on:submit|preventDefault={handleEmailAuth}
					class="space-y-4"
				>
					<input
						type="email"
						placeholder="Email"
						bind:value={email}
						class="w-full border-2 border-gray-100 p-3 rounded-xl focus:border-black transition-all outline-none"
						required
					/>
					<input
						type="password"
						placeholder="Password"
						bind:value={password}
						class="w-full border-2 border-gray-100 p-3 rounded-xl focus:border-black transition-all outline-none"
						required
					/>
					<button
						type="submit"
						class="w-full bg-black text-white py-3 rounded-xl font-bold hover:bg-gray-800 transition-all"
					>
						{isRegistering ? "Create Account" : "Sign In"}
					</button>
				</form>
			</div>
			<button
				on:click={() => (isRegistering = !isRegistering)}
				class="w-full bg-gray-50 py-4 text-sm font-bold text-gray-600 hover:text-black transition-all"
			>
				{isRegistering
					? "Already have an account? Sign in"
					: "Don't have an account? Create one"}
			</button>
		</div>
	</div>
{/if}

<main class="min-h-screen bg-gray-50">
	<slot />
</main>
