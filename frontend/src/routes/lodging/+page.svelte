<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import LodgingCard from '$lib/components/cards/LodgingCard.svelte';
	import TypeFilterDropdown from '$lib/components/TypeFilterDropdown.svelte';
	import type { Lodging } from '$lib/types';
	import { t } from 'svelte-i18n';
	import { LODGING_TYPES_ICONS } from '$lib';
	import LodgingModal from '$lib/components/lodging/LodgingModal.svelte';

	import Plus from '~icons/mdi/plus';
	import Filter from '~icons/mdi/filter-variant';
	import Sort from '~icons/mdi/sort';
	import Bed from '~icons/mdi/bed';
	import Eye from '~icons/mdi/eye';
	import Star from '~icons/mdi/star';

	export let data: any;

	let lodgingItems: Lodging[] = data.props.lodgingItems || [];
	let lodgingBeingUpdated: Lodging | undefined = undefined;

	// Sync the lodgingBeingUpdated with the lodgingItems array
	$: {
		if (lodgingBeingUpdated && lodgingBeingUpdated.id) {
			const index = lodgingItems.findIndex((l) => l.id === lodgingBeingUpdated?.id);

			if (index !== -1) {
				lodgingItems[index] = { ...lodgingBeingUpdated };
				lodgingItems = lodgingItems;
			} else {
				lodgingItems = [{ ...lodgingBeingUpdated }, ...lodgingItems];
				data.props.lodgingItems = lodgingItems;
			}
		}
	}

	let resultsPerPage: number = 25;
	let count = data.props.count || 0;
	let totalPages = Math.ceil(count / resultsPerPage);
	let currentPage: number = 1;

	let typeString: string = '';
	let lodgingToEdit: Lodging | null = null;
	let isLodgingModalOpen: boolean = false;
	let sidebarOpen = false;
	let ratingHover: number | null = null;

	let currentSort = {
		order_by: 'updated_at',
		order: 'asc',
		is_visited: 'all',
		is_public: 'all',
		ownership: 'all',
		min_rating: 'all'
	};

	// Get type options from the icons with localized labels
	$: typeOptions = Object.entries(LODGING_TYPES_ICONS).map(([value, icon]) => ({
		value,
		label: $t(`lodging.${value}`),
		icon
	}));

	// Reactive statements - Only read from URL, don't write
	$: {
		if (typeof window !== 'undefined') {
			let url = new URL(window.location.href);
			let types = url.searchParams.get('types');
			if (types && types !== 'all') {
				typeString = types;
			} else {
				typeString = '';
			}
		}
	}

	$: {
		let url = new URL($page.url);
		let pageParam = url.searchParams.get('page');
		if (pageParam) {
			currentPage = parseInt(pageParam);
		}
	}

	$: {
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
		}
		if (data.props.count) {
			count = data.props.count;
			totalPages = Math.ceil(count / resultsPerPage);
		}
	}

	$: {
		let url = new URL($page.url);
		currentSort.order_by = url.searchParams.get('order_by') || 'updated_at';
		currentSort.order = url.searchParams.get('order_direction') || 'asc';
		currentSort.is_visited = url.searchParams.get('is_visited') || 'all';
		currentSort.is_public = url.searchParams.get('is_public') || 'all';
		currentSort.ownership = url.searchParams.get('ownership') || 'all';
		currentSort.min_rating = url.searchParams.get('min_rating') || 'all';
	}

	function getVisitedCount() {
		return lodgingItems.filter((l) => l.is_visited).length;
	}

	function getPlannedCount() {
		return lodgingItems.filter((l) => !l.is_visited).length;
	}

	function handleChangePage(pageNumber: number) {
		currentPage = pageNumber;
		let url = new URL(window.location.href);
		url.searchParams.set('page', pageNumber.toString());
		lodgingItems = [];
		lodgingItems = data.props.lodgingItems;
		goto(url.toString(), { invalidateAll: true, replaceState: true });
	}

	function deleteLodging(event: CustomEvent<string>) {
		lodgingItems = lodgingItems.filter((l) => l.id !== event.detail);
		count = count - 1;
	}

	function editLodging(event: CustomEvent<Lodging>) {
		lodgingToEdit = event.detail;
		isLodgingModalOpen = true;
	}

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	// Dynamic filter functions (like collections)
	async function updateSort(orderBy: string, orderDirection: string) {
		const url = new URL($page.url);
		url.searchParams.set('order_by', orderBy);
		url.searchParams.set('order_direction', orderDirection);
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.order_by = orderBy;
		currentSort.order = orderDirection;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}

	async function updateVisitedFilter(isVisited: string) {
		const url = new URL($page.url);
		url.searchParams.set('is_visited', isVisited);
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.is_visited = isVisited;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}

	async function updateVisibilityFilter(visibility: string) {
		const url = new URL($page.url);
		if (visibility && visibility !== 'all') {
			url.searchParams.set('is_public', visibility);
		} else {
			url.searchParams.delete('is_public');
		}
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.is_public = visibility;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}

	async function updateOwnershipFilter(ownership: string) {
		const url = new URL($page.url);
		if (ownership && ownership !== 'all') {
			url.searchParams.set('ownership', ownership);
		} else {
			url.searchParams.delete('ownership');
		}
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.ownership = ownership;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}

	async function updateRatingFilter(minRating: string) {
		const url = new URL($page.url);
		if (minRating && minRating !== 'all') {
			url.searchParams.set('min_rating', minRating);
		} else {
			url.searchParams.delete('min_rating');
		}
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.min_rating = minRating;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}

	async function updateTypeFilter(event: CustomEvent<string>) {
		const types = event.detail;
		const url = new URL($page.url);
		if (types) {
			url.searchParams.set('types', types);
		} else {
			url.searchParams.delete('types');
		}
		url.searchParams.set('page', '1');
		currentPage = 1;
		typeString = types;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.lodgingItems) {
			lodgingItems = data.props.lodgingItems;
			count = data.props.count;
		}
	}
</script>

<svelte:head>
	<title>{$t('lodging.my_lodging') || 'My Lodging'}</title>
	<meta name="description" content="View and manage your lodging." />
</svelte:head>

{#if isLodgingModalOpen}
	<LodgingModal
		on:close={() => (isLodgingModalOpen = false)}
		lodgingToEdit={lodgingToEdit}
		bind:lodging={lodgingBeingUpdated}
	/>
{/if}

<div class="min-h-screen bg-gradient-to-br from-base-200 via-base-100 to-base-200">
	<div class="drawer lg:drawer-open">
		<input id="my-drawer" type="checkbox" class="drawer-toggle" bind:checked={sidebarOpen} />

		<div class="drawer-content">
			<!-- Header Section -->
			<div class="sticky top-0 z-30 bg-base-100/80 backdrop-blur-lg border-b border-base-300">
				<div class="container mx-auto px-6 py-4">
					<div class="flex items-center justify-between">
						<div class="flex items-center gap-4">
							<button class="btn btn-ghost btn-square lg:hidden" on:click={toggleSidebar}>
								<Filter class="w-5 h-5" />
							</button>
							<div class="flex items-center gap-3">
								<div class="p-2 bg-primary/10 rounded-xl">
									<Bed class="w-8 h-8 text-primary" />
								</div>
								<div>
									<h1 class="text-3xl font-bold bg-clip-text text-primary">
										{$t('lodging.my_lodging') || 'My Lodging'}
									</h1>
									<p class="text-sm text-base-content/60">
										{count}
										{$t('adventures.stays') || 'stays'}
									</p>
								</div>
							</div>
						</div>

						<!-- Quick Stats -->
						<div class="hidden md:flex items-center gap-3">
							<div class="stats stats-horizontal bg-base-200/50 border border-base-300/50">
								<div class="stat py-2 px-4">
									<div class="stat-figure text-primary">
										<Bed class="w-5 h-5" />
									</div>
									<div class="stat-title text-xs">{$t('adventures.total') || 'Total'}</div>
									<div class="stat-value text-lg">{count}</div>
								</div>
								<div class="stat py-2 px-4">
									<div class="stat-title text-xs">{$t('adventures.visited')}</div>
									<div class="stat-value text-lg text-success">{getVisitedCount()}</div>
								</div>
								<div class="stat py-2 px-4">
									<div class="stat-title text-xs">{$t('adventures.planned')}</div>
									<div class="stat-value text-lg text-warning">{getPlannedCount()}</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Main Content -->
			<div class="container mx-auto px-6 py-8">
				{#if lodgingItems.length === 0}
					<div class="flex flex-col items-center justify-center py-16">
						<div class="p-6 bg-base-200/50 rounded-2xl mb-6">
							<Bed class="w-16 h-16 text-base-content/30" />
						</div>
						<h3 class="text-xl font-semibold text-base-content/70 mb-2">
							{$t('lodging.no_lodging_found') || 'No lodging found'}
						</h3>
						<p class="text-base-content/50 text-center max-w-md">
							{$t('adventures.no_adventures_message')}
						</p>
						<button
							class="btn btn-primary btn-wide mt-6 gap-2"
							on:click={() => {
								lodgingToEdit = null;
								isLodgingModalOpen = true;
							}}
						>
							<Plus class="w-5 h-5" />
							{$t('lodging.create_lodging') || 'Create Lodging'}
						</button>
					</div>
				{:else}
					<!-- Lodging Grid -->
					<div
						class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
					>
						{#each lodgingItems as lodging}
							<LodgingCard
								user={data.user}
								{lodging}
								on:delete={deleteLodging}
								on:edit={editLodging}
							/>
						{/each}
					</div>

					<!-- Pagination -->
					{#if totalPages > 1}
						<div class="flex justify-center mt-12">
							<div class="join bg-base-100 shadow-lg rounded-2xl p-2">
								{#each Array.from({ length: totalPages }, (_, i) => i + 1) as pageNum}
									<button
										class="join-item btn btn-sm {currentPage === pageNum
											? 'btn-primary'
											: 'btn-ghost'}"
										on:click={() => handleChangePage(pageNum)}
									>
										{pageNum}
									</button>
								{/each}
							</div>
						</div>
					{/if}
				{/if}
			</div>
		</div>

		<!-- Sidebar -->
		<div class="drawer-side z-30">
			<label for="my-drawer" class="drawer-overlay"></label>
			<div class="w-80 min-h-full bg-base-100 shadow-2xl">
				<div class="p-6">
					<!-- Sidebar Header -->
					<div class="flex items-center gap-3 mb-8">
						<div class="p-2 bg-primary/10 rounded-lg">
							<Filter class="w-6 h-6 text-primary" />
						</div>
						<h2 class="text-xl font-bold">{$t('adventures.filters_and_sort')}</h2>
					</div>

					<!-- Filters (Dynamic like collections) -->
					<div class="space-y-6">
						<!-- Type Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Bed class="w-5 h-5" />
								{$t('transportation.type') || 'Type'}
							</h3>
							<TypeFilterDropdown bind:types={typeString} {typeOptions} on:change={updateTypeFilter} />
						</div>

						<!-- Sort Options -->
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
											class="join-item btn btn-sm flex-1 {currentSort.order === 'asc' ? 'btn-active' : ''}"
											on:click={() => updateSort(currentSort.order_by || 'updated_at', 'asc')}
										>
											{$t('adventures.ascending')}
										</button>
										<button
											class="join-item btn btn-sm flex-1 {currentSort.order === 'desc' ? 'btn-active' : ''}"
											on:click={() => updateSort(currentSort.order_by || 'updated_at', 'desc')}
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
										<label class="label cursor-pointer justify-start gap-3">
											<input
												type="radio"
												name="order_by_radio"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'updated_at'}
												on:change={() => updateSort('updated_at', currentSort.order || 'asc')}
											/>
											<span class="label-text">{$t('adventures.updated')}</span>
										</label>
										<label class="label cursor-pointer justify-start gap-3">
											<input
												type="radio"
												name="order_by_radio"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'name'}
												on:change={() => updateSort('name', currentSort.order || 'asc')}
											/>
											<span class="label-text">{$t('adventures.name')}</span>
										</label>
										<label class="label cursor-pointer justify-start gap-3">
											<input
												type="radio"
												name="order_by_radio"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'date'}
												on:change={() => updateSort('date', currentSort.order || 'asc')}
											/>
											<span class="label-text">{$t('adventures.date')}</span>
										</label>
										<label class="label cursor-pointer justify-start gap-3">
											<input
												type="radio"
												name="order_by_radio"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'rating'}
												on:change={() => updateSort('rating', currentSort.order || 'asc')}
											/>
											<span class="label-text">{$t('adventures.rating')}</span>
										</label>
									</div>
								</div>
							</div>
						</div>

						<!-- Visited Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Eye class="w-5 h-5" />
								{$t('adventures.visited')}
							</h3>
							<div class="space-y-2">
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visited_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_visited === 'all'}
										on:change={() => updateVisitedFilter('all')}
									/>
									<span class="label-text">{$t('adventures.all')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visited_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_visited === 'true'}
										on:change={() => updateVisitedFilter('true')}
									/>
									<span class="label-text">{$t('adventures.visited')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visited_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_visited === 'false'}
										on:change={() => updateVisitedFilter('false')}
									/>
									<span class="label-text">{$t('adventures.not_visited')}</span>
								</label>
							</div>
						</div>

						<!-- Visibility Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Eye class="w-5 h-5" />
								{$t('adventures.visibility')}
							</h3>
							<div class="space-y-2">
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visibility_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_public === 'all'}
										on:change={() => updateVisibilityFilter('all')}
									/>
									<span class="label-text">{$t('adventures.all')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visibility_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_public === 'true'}
										on:change={() => updateVisibilityFilter('true')}
									/>
									<span class="label-text">{$t('adventures.public')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="visibility_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.is_public === 'false'}
										on:change={() => updateVisibilityFilter('false')}
									/>
									<span class="label-text">{$t('adventures.private')}</span>
								</label>
							</div>
						</div>

						<!-- Ownership Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Eye class="w-5 h-5" />
								{$t('adventures.ownership_filter')}
							</h3>
							<div class="space-y-2">
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="ownership_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.ownership === 'all'}
										on:change={() => updateOwnershipFilter('all')}
									/>
									<span class="label-text">{$t('adventures.all')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="ownership_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.ownership === 'mine'}
										on:change={() => updateOwnershipFilter('mine')}
									/>
									<span class="label-text">{$t('adventures.my_locations')}</span>
								</label>
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="ownership_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.ownership === 'public'}
										on:change={() => updateOwnershipFilter('public')}
									/>
									<span class="label-text">{$t('adventures.public_locations')}</span>
								</label>
							</div>
						</div>

						<!-- Rating Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Star class="w-5 h-5" />
								{$t('adventures.min_rating')}
							</h3>
							<div class="flex flex-col gap-3">
								<!-- Interactive star selector -->
								<div
									class="flex items-center justify-center gap-1"
									on:mouseleave={() => ratingHover = null}
									role="group"
									aria-label="Rating filter"
								>
									{#each [1, 2, 3, 4, 5] as rating}
										{@const isActive = currentSort.min_rating !== 'all' && rating <= parseInt(currentSort.min_rating)}
										{@const isHovered = ratingHover !== null && rating <= ratingHover}
										<button
											type="button"
											class="btn btn-ghost btn-sm p-1 min-h-0 h-auto transition-transform hover:scale-125"
											on:click={() => {
												if (currentSort.min_rating === rating.toString()) {
													updateRatingFilter('all');
												} else {
													updateRatingFilter(rating.toString());
												}
											}}
											on:mouseenter={() => ratingHover = rating}
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
									{#if currentSort.min_rating !== 'all'}
										<span class="font-medium">{currentSort.min_rating}+ {$t('adventures.stars')}</span>
										<button
											class="btn btn-ghost btn-xs ml-2"
											on:click={() => updateRatingFilter('all')}
										>
											{$t('adventures.clear')}
										</button>
									{:else}
										<span>{$t('adventures.all')}</span>
									{/if}
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Floating Action Button -->
	<div class="fixed bottom-6 right-6 z-[999]">
		<button
			class="btn btn-primary btn-circle w-16 h-16 shadow-2xl hover:shadow-primary/25 transition-all duration-200"
			on:click={() => {
				isLodgingModalOpen = true;
				lodgingToEdit = null;
			}}
		>
			<Plus class="w-8 h-8" />
		</button>
	</div>
</div>
