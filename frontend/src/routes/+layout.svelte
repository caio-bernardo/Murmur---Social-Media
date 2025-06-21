<script lang="ts">
	import '../app.css';

	let { children } = $props();

	let theme = $state("mona")
</script>

<div data-theme={theme} class="h-screen grid">
    {@render children()}
</div>
