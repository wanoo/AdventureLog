<script lang="ts">
	/**
	 * RatingFilter - Star rating filter with interactive selector
	 */
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';
	import Star from '~icons/mdi/star';

	export let minRating: string = 'all';

	const dispatch = createEventDispatcher<{ change: string }>();

	let ratingHover: number | null = null;

	function handleRatingChange(rating: number) {
		if (minRating === rating.toString()) {
			minRating = 'all';
		} else {
			minRating = rating.toString();
		}
		dispatch('change', minRating);
	}

	function clearRating() {
		minRating = 'all';
		dispatch('change', minRating);
	}
</script>

<div class="card bg-base-200/50 p-4">
	<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
		<Star class="w-5 h-5" />
		{$t('adventures.min_rating')}
	</h3>
	<div class="flex flex-col gap-3">
		<!-- Interactive star selector -->
		<div
			class="flex items-center justify-center gap-1"
			on:mouseleave={() => (ratingHover = null)}
			role="group"
			aria-label="Rating filter"
		>
			{#each [1, 2, 3, 4, 5] as rating}
				{@const isActive = minRating !== 'all' && rating <= parseInt(minRating)}
				{@const isHovered = ratingHover !== null && rating <= ratingHover}
				<button
					type="button"
					class="btn btn-ghost btn-sm p-1 min-h-0 h-auto transition-transform hover:scale-125"
					on:click={() => handleRatingChange(rating)}
					on:mouseenter={() => (ratingHover = rating)}
					aria-label="Filter by {rating}+ stars"
				>
					<Star
						class="w-8 h-8 transition-all duration-150"
						style="color: {isActive || isHovered ? '#FBBD23' : 'oklch(var(--bc) / 0.2)'};"
					/>
				</button>
			{/each}
		</div>
		<!-- Current filter display -->
		<div class="text-center text-sm text-base-content/70">
			{#if minRating !== 'all'}
				<span class="font-medium">{minRating}+ {$t('adventures.stars')}</span>
				<button class="btn btn-ghost btn-xs ml-2" on:click={clearRating}>
					{$t('adventures.clear')}
				</button>
			{:else}
				<span>{$t('adventures.all')}</span>
			{/if}
		</div>
	</div>
</div>
