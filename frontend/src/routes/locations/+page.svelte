<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import LocationCard from '$lib/components/cards/LocationCard.svelte';
	import CategoryFilterDropdown from '$lib/components/CategoryFilterDropdown.svelte';
	import CategoryModal from '$lib/components/CategoryModal.svelte';
	import type { Location } from '$lib/types';
	import { t } from 'svelte-i18n';

	import Plus from '~icons/mdi/plus';
	import Filter from '~icons/mdi/filter-variant';
	import Sort from '~icons/mdi/sort';
	import MapMarker from '~icons/mdi/map-marker';
	import Eye from '~icons/mdi/eye';
	import Calendar from '~icons/mdi/calendar';
	import Tag from '~icons/mdi/tag';
	import Compass from '~icons/mdi/compass';
	import Star from '~icons/mdi/star';
	import NewLocationModal from '$lib/components/locations/LocationModal.svelte';

	export let data: any;

	let adventures: Location[] = data.props.adventures || [];

	let currentSort = {
		order_by: '',
		order: '',
		visited: true,
		planned: true,
		includeCollections: true,
		is_visited: 'all',
		is_public: 'all',
		ownership: 'all',
		min_rating: 'all'
	};

	let locationBeingUpdated: Location | undefined = undefined;

	// Sync the locationBeingUpdated with the adventures array
	$: {
		if (locationBeingUpdated && locationBeingUpdated.id) {
			const index = adventures.findIndex((adventure) => adventure.id === locationBeingUpdated?.id);

			if (index !== -1) {
				adventures[index] = { ...locationBeingUpdated };
				adventures = adventures; // Trigger reactivity
			} else {
				adventures = [{ ...locationBeingUpdated }, ...adventures];
				data.props.adventures = adventures; // Update data.props.adventures as well
			}
		}
	}

	let resultsPerPage: number = 25;
	let count = data.props.count || 0;
	let totalPages = Math.ceil(count / resultsPerPage);
	let currentPage: number = 1;

	let is_category_modal_open: boolean = false;
	let typeString: string = '';
	let adventureToEdit: Location | null = null;
	let isLocationModalOpen: boolean = false;
	let sidebarOpen = false;


	// Reactive statements - Only read from URL, don't write
	$: {
		if (typeof window !== 'undefined') {
			let url = new URL(window.location.href);
			let types = url.searchParams.get('types');
			if (types) {
				typeString = types;
			} else {
				typeString = '';
			}
		}
	}

	$: {
		let url = new URL($page.url);
		let page = url.searchParams.get('page');
		if (page) {
			currentPage = parseInt(page);
		}
	}

	$: {
		if (data.props.adventures) {
			adventures = data.props.adventures;
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

		if (url.searchParams.get('planned') === 'on') {
			currentSort.planned = true;
		} else {
			currentSort.planned = false;
		}
		if (url.searchParams.get('visited') === 'on') {
			currentSort.visited = true;
		} else {
			currentSort.visited = false;
		}
		if (url.searchParams.get('include_collections') === 'true') {
			currentSort.includeCollections = true;
		} else if (url.searchParams.get('include_collections') === 'false') {
			currentSort.includeCollections = false;
		} else {
			// Default to true when no parameter is present (first visit)
			currentSort.includeCollections = true;
		}

		if (!currentSort.visited && !currentSort.planned) {
			currentSort.visited = true;
			currentSort.planned = true;
		}

		if (url.searchParams.get('is_visited')) {
			currentSort.is_visited = url.searchParams.get('is_visited') || 'all';
		}
		currentSort.is_public = url.searchParams.get('is_public') || 'all';
		currentSort.ownership = url.searchParams.get('ownership') || 'all';
		currentSort.min_rating = url.searchParams.get('min_rating') || 'all';
	}

	function handleChangePage(pageNumber: number) {
		currentPage = pageNumber;
		let url = new URL(window.location.href);
		url.searchParams.set('page', pageNumber.toString());
		adventures = [];
		adventures = data.props.adventures;
		goto(url.toString(), { invalidateAll: true, replaceState: true });
	}

	function deleteAdventure(event: CustomEvent<string>) {
		adventures = adventures.filter((adventure) => adventure.id !== event.detail);
	}

	function editAdventure(event: CustomEvent<Location>) {
		adventureToEdit = event.detail;
		isLocationModalOpen = true;
	}

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function getVisitedCount() {
		return adventures.filter((a) => a.is_visited).length;
	}

	function getPlannedCount() {
		return adventures.filter((a) => !a.is_visited).length;
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
			count = data.props.count;
		}
	}

	async function updateIncludeCollections(include: boolean) {
		const url = new URL($page.url);
		url.searchParams.set('include_collections', include.toString());
		url.searchParams.set('page', '1');
		currentPage = 1;
		currentSort.includeCollections = include;
		await goto(url.toString(), { invalidateAll: true, replaceState: true });
		if (data.props.adventures) {
			adventures = data.props.adventures;
			count = data.props.count;
		}
	}

	async function updateCategoryFilter(event: CustomEvent<string>) {
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
		if (data.props.adventures) {
			adventures = data.props.adventures;
			count = data.props.count;
		}
	}
</script>

<svelte:head>
	<title>{$t('locations.locations')}</title>
	<meta name="description" content="View your completed and planned adventures." />
</svelte:head>

{#if isLocationModalOpen}
	<NewLocationModal
		on:close={() => (isLocationModalOpen = false)}
		user={data.user}
		locationToEdit={adventureToEdit}
		bind:location={locationBeingUpdated}
	/>
{/if}

{#if is_category_modal_open}
	<CategoryModal
		on:close={() => (is_category_modal_open = false)}
		collaborativeMode={data.collaborativeMode}
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
									<Compass class="w-8 h-8 text-primary" />
								</div>
								<div>
									<h1 class="text-3xl font-bold bg-clip-text text-primary">
										{$t('locations.my_locations')}
									</h1>
									<p class="text-sm text-base-content/60">
										{count}
										{$t('locations.locations')} • {getVisitedCount()}
										{$t('adventures.visited')} • {getPlannedCount()}
										{$t('adventures.planned')}
									</p>
								</div>
							</div>
						</div>

						<!-- Quick Stats -->
						<div class="hidden md:flex items-center gap-3">
							<div class="stats stats-horizontal bg-base-200/50 border border-base-300/50">
								<div class="stat py-2 px-4">
									<div class="stat-figure text-primary">
										<Eye class="w-5 h-5" />
									</div>
									<div class="stat-title text-xs">{$t('adventures.visited')}</div>
									<div class="stat-value text-lg">{getVisitedCount()}</div>
								</div>
								<div class="stat py-2 px-4">
									<div class="stat-figure text-secondary">
										<Calendar class="w-5 h-5" />
									</div>
									<div class="stat-title text-xs">{$t('adventures.planned')}</div>
									<div class="stat-value text-lg">{getPlannedCount()}</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>

			<!-- Main Content -->
			<div class="container mx-auto px-6 py-8">
				{#if adventures.length === 0}
					<div class="flex flex-col items-center justify-center py-16">
						<div class="p-6 bg-base-200/50 rounded-2xl mb-6">
							<Compass class="w-16 h-16 text-base-content/30" />
						</div>
						<h3 class="text-xl font-semibold text-base-content/70 mb-2">
							{$t('adventures.no_locations_found')}
						</h3>
						<p class="text-base-content/50 text-center max-w-md">
							{$t('adventures.no_adventures_message')}
						</p>
						<button
							class="btn btn-primary btn-wide mt-6 gap-2"
							on:click={() => {
								adventureToEdit = null;
								isLocationModalOpen = true;
							}}
						>
							<Plus class="w-5 h-5" />
							{$t('adventures.create_location')}
						</button>
					</div>
				{:else}
					<!-- Adventures Grid -->
					<div
						class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
					>
						{#each adventures as adventure}
							<LocationCard
								user={data.user}
								{adventure}
								on:delete={deleteAdventure}
								on:edit={editAdventure}
							/>
						{/each}
					</div>

					<!-- Pagination -->
					{#if totalPages > 1}
						<div class="flex justify-center mt-12">
							<div class="join bg-base-100 shadow-lg rounded-2xl p-2">
								{#each Array.from({ length: totalPages }, (_, i) => i + 1) as page}
									<button
										class="join-item btn btn-sm {currentPage === page
											? 'btn-primary'
											: 'btn-ghost'}"
										on:click={() => handleChangePage(page)}
									>
										{page}
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
						<!-- Category Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Tag class="w-5 h-5" />
								{$t('adventures.categories')}
							</h3>
							<CategoryFilterDropdown bind:types={typeString} on:change={updateCategoryFilter} />
							<button
								type="button"
								on:click={() => (is_category_modal_open = true)}
								class="btn btn-outline btn-sm w-full mt-3 gap-2"
							>
								<Tag class="w-4 h-4" />
								{$t('categories.manage_categories')}
							</button>
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

						<!-- Visit Status Filter -->
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

						<!-- Sources Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<MapMarker class="w-5 h-5" />
								{$t('adventures.sources')}
							</h3>
							<label class="label cursor-pointer justify-start gap-3">
								<input
									type="checkbox"
									class="checkbox checkbox-primary"
									checked={currentSort.includeCollections}
									on:change={(e) => updateIncludeCollections(e.currentTarget.checked)}
								/>
								<span class="label-text">{$t('adventures.collection_locations')}</span>
							</label>
						</div>

						<!-- Rating Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Star class="w-5 h-5" />
								{$t('adventures.min_rating')}
							</h3>
							<div class="space-y-2">
								<label class="label cursor-pointer justify-start gap-3">
									<input
										type="radio"
										name="rating_filter"
										class="radio radio-primary radio-sm"
										checked={currentSort.min_rating === 'all'}
										on:change={() => updateRatingFilter('all')}
									/>
									<span class="label-text">{$t('adventures.all')}</span>
								</label>
								{#each [1, 2, 3, 4, 5] as rating}
									<label class="label cursor-pointer justify-start gap-3">
										<input
											type="radio"
											name="rating_filter"
											class="radio radio-primary radio-sm"
											checked={currentSort.min_rating === rating.toString()}
											on:change={() => updateRatingFilter(rating.toString())}
										/>
										<span class="label-text flex items-center gap-1">
											{rating}+ <Star class="w-4 h-4 text-warning" />
										</span>
									</label>
								{/each}
							</div>
						</div>

						<!-- Visibility Filter (collaborative mode only) -->
						{#if data.collaborativeMode}
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
						{/if}
					</div>
				</div>
			</div>
		</div>
	</div>

	<!-- Floating Action Button -->
	<div class="fixed bottom-6 right-6 z-[999]">
		<div class="dropdown dropdown-top dropdown-end">
			<div
				tabindex="0"
				role="button"
				class="btn btn-primary btn-circle w-16 h-16 shadow-2xl hover:shadow-primary/25 transition-all duration-200"
			>
				<Plus class="w-8 h-8" />
			</div>
			<ul
				class="dropdown-content z-[40] menu p-4 shadow-2xl bg-base-100 rounded-2xl w-64 border border-base-300"
			>
				<div class="text-center mb-4">
					<h3 class="font-bold text-lg">{$t('adventures.create_new')}</h3>
				</div>
				<button
					class="btn btn-primary gap-2 w-full"
					on:click={() => {
						isLocationModalOpen = true;
						adventureToEdit = null;
					}}
				>
					<Compass class="w-5 h-5" />
					{$t('locations.location')}
				</button>
			</ul>
		</div>
	</div>
</div>
