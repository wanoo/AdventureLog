<script lang="ts">
	/**
	 * SortOptions - Sort direction and order by options
	 */
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';
	import Sort from '~icons/mdi/sort';

	export let orderBy: string = 'updated_at';
	export let orderDirection: string = 'asc';
	export let orderByOptions: { value: string; label: string }[] = [
		{ value: 'updated_at', label: 'Updated' },
		{ value: 'name', label: 'Name' },
		{ value: 'rating', label: 'Rating' }
	];

	const dispatch = createEventDispatcher<{ change: { orderBy: string; orderDirection: string } }>();

	function handleDirectionChange(direction: string) {
		orderDirection = direction;
		dispatch('change', { orderBy, orderDirection });
	}

	function handleOrderByChange(value: string) {
		orderBy = value;
		dispatch('change', { orderBy, orderDirection });
	}
</script>

<div class="card bg-base-200/50 p-4">
	<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
		<Sort class="w-5 h-5" />
		{$t('adventures.sort')}
	</h3>

	<div class="space-y-4">
		<div>
			<!-- svelte-ignore a11y-label-has-associated-control -->
			<label class="label">
				<span class="label-text font-medium">{$t('adventures.order_direction')}</span>
			</label>
			<div class="join w-full">
				<button
					class="join-item btn btn-sm flex-1 {orderDirection === 'asc' ? 'btn-active' : ''}"
					on:click={() => handleDirectionChange('asc')}
				>
					{$t('adventures.ascending')}
				</button>
				<button
					class="join-item btn btn-sm flex-1 {orderDirection === 'desc' ? 'btn-active' : ''}"
					on:click={() => handleDirectionChange('desc')}
				>
					{$t('adventures.descending')}
				</button>
			</div>
		</div>

		<div>
			<!-- svelte-ignore a11y-label-has-associated-control -->
			<label class="label">
				<span class="label-text font-medium">{$t('adventures.order_by')}</span>
			</label>
			<div class="space-y-2">
				{#each orderByOptions as option}
					<label class="label cursor-pointer justify-start gap-3">
						<input
							type="radio"
							name="order_by_radio"
							class="radio radio-primary radio-sm"
							checked={orderBy === option.value}
							on:change={() => handleOrderByChange(option.value)}
						/>
						<span class="label-text">{option.label}</span>
					</label>
				{/each}
			</div>
		</div>
	</div>
</div>
