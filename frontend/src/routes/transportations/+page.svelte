<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import TransportationCard from '$lib/components/cards/TransportationCard.svelte';
	import TypeFilterDropdown from '$lib/components/TypeFilterDropdown.svelte';
	import type { Transportation } from '$lib/types';
	import { t } from 'svelte-i18n';
	import { TRANSPORTATION_TYPES_ICONS } from '$lib';
	import TransportationModal from '$lib/components/transportation/TransportationModal.svelte';

	import Plus from '~icons/mdi/plus';
	import Filter from '~icons/mdi/filter-variant';
	import Sort from '~icons/mdi/sort';
	import Airplane from '~icons/mdi/airplane';
	import Eye from '~icons/mdi/eye';

	export let data: any;

	let transportations: Transportation[] = data.props.transportations || [];
	let transportationBeingUpdated: Transportation | undefined = undefined;

	// Sync the transportationBeingUpdated with the transportations array
	$: {
		if (transportationBeingUpdated && transportationBeingUpdated.id) {
			const index = transportations.findIndex((t) => t.id === transportationBeingUpdated?.id);

			if (index !== -1) {
				transportations[index] = { ...transportationBeingUpdated };
				transportations = transportations;
			} else {
				transportations = [{ ...transportationBeingUpdated }, ...transportations];
				data.props.transportations = transportations;
			}
		}
	}

	let resultsPerPage: number = 25;
	let count = data.props.count || 0;
	let totalPages = Math.ceil(count / resultsPerPage);
	let currentPage: number = 1;

	let typeString: string = '';
	let transportationToEdit: Transportation | null = null;
	let isTransportationModalOpen: boolean = false;
	let sidebarOpen = false;

	let currentSort = {
		order_by: 'updated_at',
		order: 'asc',
		is_visited: 'all',
		is_public: 'all'
	};

	// Get type options from the icons with localized labels
	$: typeOptions = Object.entries(TRANSPORTATION_TYPES_ICONS).map(([value, icon]) => ({
		value,
		label: $t(`transportation.modes.${value}`),
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
		if (data.props.transportations) {
			transportations = data.props.transportations;
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
	}

	function getVisitedCount() {
		return transportations.filter((t) => t.is_visited).length;
	}

	function getPlannedCount() {
		return transportations.filter((t) => !t.is_visited).length;
	}

	function handleChangePage(pageNumber: number) {
		currentPage = pageNumber;
		let url = new URL(window.location.href);
		url.searchParams.set('page', pageNumber.toString());
		transportations = [];
		transportations = data.props.transportations;
		goto(url.toString(), { invalidateAll: true, replaceState: true });
	}

	function deleteTransportation(event: CustomEvent<string>) {
		transportations = transportations.filter((t) => t.id !== event.detail);
		count = count - 1;
	}

	function editTransportation(event: CustomEvent<Transportation>) {
		transportationToEdit = event.detail;
		isTransportationModalOpen = true;
	}

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function getTypeCount(type: string): number {
		return transportations.filter((t) => t.type === type).length;
	}
</script>

<svelte:head>
	<title>{$t('transportation.my_transportations') || 'My Transportations'}</title>
	<meta name="description" content="View and manage your transportations." />
</svelte:head>

{#if isTransportationModalOpen}
	<TransportationModal
		on:close={() => (isTransportationModalOpen = false)}
		transportationToEdit={transportationToEdit}
		bind:transportation={transportationBeingUpdated}
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
									<Airplane class="w-8 h-8 text-primary" />
								</div>
								<div>
									<h1 class="text-3xl font-bold bg-clip-text text-primary">
										{$t('transportation.my_transportations') || 'My Transportations'}
									</h1>
									<p class="text-sm text-base-content/60">
										{count}
										{$t('adventures.transportations')}
									</p>
								</div>
							</div>
						</div>

						<!-- Quick Stats -->
						<div class="hidden md:flex items-center gap-3">
							<div class="stats stats-horizontal bg-base-200/50 border border-base-300/50">
								<div class="stat py-2 px-4">
									<div class="stat-figure text-primary">
										<Airplane class="w-5 h-5" />
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
				{#if transportations.length === 0}
					<div class="flex flex-col items-center justify-center py-16">
						<div class="p-6 bg-base-200/50 rounded-2xl mb-6">
							<Airplane class="w-16 h-16 text-base-content/30" />
						</div>
						<h3 class="text-xl font-semibold text-base-content/70 mb-2">
							{$t('transportation.no_transportations_found') || 'No transportations found'}
						</h3>
						<p class="text-base-content/50 text-center max-w-md">
							{$t('adventures.no_adventures_message')}
						</p>
						<button
							class="btn btn-primary btn-wide mt-6 gap-2"
							on:click={() => {
								transportationToEdit = null;
								isTransportationModalOpen = true;
							}}
						>
							<Plus class="w-5 h-5" />
							{$t('transportation.create_transportation') || 'Create Transportation'}
						</button>
					</div>
				{:else}
					<!-- Transportations Grid -->
					<div
						class="grid grid-cols-1 sm:grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-3 gap-6"
					>
						{#each transportations as transportation}
							<TransportationCard
								user={data.user}
								{transportation}
								on:delete={deleteTransportation}
								on:edit={editTransportation}
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

					<!-- Filters Form -->
					<form method="get" class="space-y-6">
						<!-- Type Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Airplane class="w-5 h-5" />
								{$t('transportation.type') || 'Type'}
							</h3>
							<TypeFilterDropdown bind:types={typeString} {typeOptions} />
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
										<input
											class="join-item btn btn-sm flex-1"
											type="radio"
											name="order_direction"
											id="asc"
											value="asc"
											aria-label={$t('adventures.ascending')}
											checked={currentSort.order === 'asc'}
										/>
										<input
											class="join-item btn btn-sm flex-1"
											type="radio"
											name="order_direction"
											id="desc"
											value="desc"
											aria-label={$t('adventures.descending')}
											checked={currentSort.order === 'desc'}
										/>
									</div>
								</div>

								<div>
									<!-- svelte-ignore a11y-label-has-associated-control -->
									<label class="label">
										<span class="label-text font-medium">{$t('adventures.order_by')}</span>
									</label>
									<div class="grid grid-cols-2 gap-2">
										<label
											class="label cursor-pointer justify-start gap-2 p-2 rounded-lg hover:bg-base-300/50"
										>
											<input
												type="radio"
												name="order_by"
												value="updated_at"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'updated_at'}
											/>
											<span class="label-text text-sm">{$t('adventures.updated')}</span>
										</label>
										<label
											class="label cursor-pointer justify-start gap-2 p-2 rounded-lg hover:bg-base-300/50"
										>
											<input
												type="radio"
												name="order_by"
												value="name"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'name'}
											/>
											<span class="label-text text-sm">{$t('adventures.name')}</span>
										</label>
										<label
											class="label cursor-pointer justify-start gap-2 p-2 rounded-lg hover:bg-base-300/50"
										>
											<input
												type="radio"
												name="order_by"
												value="date"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'date'}
											/>
											<span class="label-text text-sm">{$t('adventures.date')}</span>
										</label>
										<label
											class="label cursor-pointer justify-start gap-2 p-2 rounded-lg hover:bg-base-300/50"
										>
											<input
												type="radio"
												name="order_by"
												value="rating"
												class="radio radio-primary radio-sm"
												checked={currentSort.order_by === 'rating'}
											/>
											<span class="label-text text-sm">{$t('adventures.rating')}</span>
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
							<div class="join w-full">
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_visited"
									id="all_visited"
									value="all"
									aria-label={$t('adventures.all')}
									checked={currentSort.is_visited === 'all'}
								/>
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_visited"
									id="visited_true"
									value="true"
									aria-label={$t('adventures.visited')}
									checked={currentSort.is_visited === 'true'}
								/>
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_visited"
									id="visited_false"
									value="false"
									aria-label={$t('adventures.not_visited')}
									checked={currentSort.is_visited === 'false'}
								/>
							</div>
						</div>

						<!-- Visibility Filter -->
						<div class="card bg-base-200/50 p-4">
							<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
								<Eye class="w-5 h-5" />
								{$t('adventures.visibility')}
							</h3>
							<div class="join w-full">
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_public"
									id="all_public"
									value="all"
									aria-label={$t('adventures.all')}
									checked={currentSort.is_public === 'all'}
								/>
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_public"
									id="public_true"
									value="true"
									aria-label={$t('adventures.public')}
									checked={currentSort.is_public === 'true'}
								/>
								<input
									class="join-item btn btn-sm flex-1"
									type="radio"
									name="is_public"
									id="public_false"
									value="false"
									aria-label={$t('adventures.private')}
									checked={currentSort.is_public === 'false'}
								/>
							</div>
						</div>

						<button type="submit" class="btn btn-primary w-full gap-2">
							<Filter class="w-4 h-4" />
							{$t('adventures.filter')}
						</button>
					</form>
				</div>
			</div>
		</div>
	</div>

	<!-- Floating Action Button -->
	<div class="fixed bottom-6 right-6 z-[999]">
		<button
			class="btn btn-primary btn-circle w-16 h-16 shadow-2xl hover:shadow-primary/25 transition-all duration-200"
			on:click={() => {
				isTransportationModalOpen = true;
				transportationToEdit = null;
			}}
		>
			<Plus class="w-8 h-8" />
		</button>
	</div>
</div>
