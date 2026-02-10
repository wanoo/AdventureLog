<script lang="ts">
	import StarRating from '../../StarRating.svelte';

	export let averageRating: number | null | undefined = null;
	export let fallbackRating: number | null | undefined = null;
	export let size: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl' = 'sm';
	export let showValue: boolean = true;
</script>

{#if averageRating !== null && averageRating !== undefined}
	<div class="flex items-center gap-1">
		<StarRating rating={averageRating} {size} readonly />
		{#if showValue}
			<span class="text-xs text-base-content/60">({averageRating})</span>
		{/if}
	</div>
{:else if fallbackRating !== null && fallbackRating !== undefined}
	<div class="flex items-center gap-1">
		<StarRating rating={fallbackRating} {size} readonly />
		{#if showValue}
			<span class="text-xs text-base-content/60">({fallbackRating}/5)</span>
		{/if}
	</div>
{/if}
