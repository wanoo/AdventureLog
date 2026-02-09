<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import type { Collection, Location, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import LocationQuickStart from './LocationQuickStart.svelte';
	import LocationDetails from './LocationDetails.svelte';
	import LocationMedia from './LocationMedia.svelte';
	import LocationVisits from './LocationVisits.svelte';
	import { StepTimeline, type ModalStep, navigateToStep } from '../shared/modal';

	export let user: User | null = null;
	export let collection: Collection | null = null;
	export let initialLatLng: { lat: number; lng: number } | null = null; // Used to pass the location from the map selection to the modal
	export let initialVisitDate: string | null = null; // Used to pre-fill visit date when adding from itinerary planner

	const dispatch = createEventDispatcher();

	// Store the initial visit date internally so it persists even if parent clears it
	let storedInitialVisitDate: string | null = initialVisitDate;

	let modal: HTMLDialogElement;

	// Whether a save/create occurred during this modal session
	let didSave = false;

	let steps: ModalStep[] = [
		{
			name: $t('adventures.quick_start'),
			selected: true,
			requires_id: false
		},
		{
			name: $t('adventures.details'),
			selected: false,
			requires_id: false
		},
		{
			name: $t('settings.media'),
			selected: false,
			requires_id: true
		},
		{
			name: $t('adventures.visits'),
			selected: false,
			requires_id: true
		}
	];

	export let location: Location = {
		id: '',
		name: '',
		visits: [],
		link: null,
		description: null,
		tags: [],
		price: null,
		price_currency: null,
		is_public: false,
		latitude: NaN,
		longitude: NaN,
		location: null,
		images: [],
		user: null,
		category: {
			id: '',
			name: '',
			display_name: '',
			icon: '',
			user: ''
		},
		attachments: [],
		trails: []
	};

	export let locationToEdit: Location | null = null;

	location = {
		id: locationToEdit?.id || '',
		name: locationToEdit?.name || '',
		link: locationToEdit?.link || null,
		description: locationToEdit?.description || null,
		tags: locationToEdit?.tags || [],
		price: locationToEdit?.price ?? null,
		price_currency: locationToEdit?.price_currency ?? null,
		is_public: locationToEdit?.is_public || false,
		latitude: locationToEdit?.latitude || NaN,
		longitude: locationToEdit?.longitude || NaN,
		location: locationToEdit?.location || null,
		images: locationToEdit?.images || [],
		user: locationToEdit?.user || null,
		visits: locationToEdit?.visits || [],
		is_visited: locationToEdit?.is_visited || false,
		collections: locationToEdit?.collections || [],
		category: locationToEdit?.category || {
			id: '',
			name: '',
			display_name: '',
			icon: '',
			user: ''
		},
		trails: locationToEdit?.trails || [],
		attachments: locationToEdit?.attachments || []
	};

	onMount(async () => {
		modal = document.getElementById('my_modal_1') as HTMLDialogElement;
		modal.showModal();
		// Skip the quick start step if editing an existing location
		if (!locationToEdit) {
			steps = navigateToStep(steps, 0);
		} else {
			steps = navigateToStep(steps, 1);
		}
		if (initialLatLng) {
			location.latitude = initialLatLng.lat;
			location.longitude = initialLatLng.lng;
			steps = navigateToStep(steps, 1);
		}
	});

	function close() {
		// If a save occurred, notify the parent with appropriate event
		if (didSave) {
			if (locationToEdit) {
				dispatch('save', location);
			} else {
				dispatch('create', location);
			}
		}

		dispatch('close');
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			close();
		}
	}
</script>

<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
<dialog id="my_modal_1" class="modal backdrop-blur-sm">
	<!-- svelte-ignore a11y-no-noninteractive-tabindex -->
	<!-- svelte-ignore a11y-no-noninteractive-element-interactions -->
	<div
		class="modal-box w-11/12 max-w-6xl bg-gradient-to-br from-base-100 via-base-100 to-base-200 border border-base-300 shadow-2xl"
		role="dialog"
		on:keydown={handleKeydown}
		tabindex="0"
	>
		<!-- Header Section - Following adventurelog pattern -->
		<div
			class="top-0 z-10 bg-base-100/90 backdrop-blur-lg border-b border-base-300 -mx-6 -mt-6 px-6 py-4 mb-6"
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-3">
					<div class="p-2 bg-primary/10 rounded-xl">
						<svg class="w-8 h-8 text-primary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
							/>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
							/>
						</svg>
					</div>
					<div>
						<h1 class="text-3xl font-bold text-primary bg-clip-text">
							{locationToEdit ? $t('adventures.edit_location') : $t('adventures.new_location')}
						</h1>
						<p class="text-sm text-base-content/60">
							{locationToEdit
								? $t('adventures.update_location_details')
								: $t('adventures.create_new_location')}
						</p>
					</div>
				</div>

				<StepTimeline
					{steps}
					entityId={location.id}
					on:stepClick={(e) => {
						steps = navigateToStep(steps, e.detail.index);
					}}
				/>

				<!-- Close Button -->
				{#if !location.id}
					<button class="btn btn-ghost btn-square" on:click={close}>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				{:else}
					<button class="btn btn-ghost btn-square" on:click={close}>
						<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M6 18L18 6M6 6l12 12"
							/>
						</svg>
					</button>
				{/if}
			</div>
		</div>

		{#if steps[0].selected}
			<!-- Main Content -->
			<LocationQuickStart
				on:locationSelected={(e) => {
					location.name = e.detail.name;
					location.location = e.detail.location;
					location.latitude = e.detail.latitude;
					location.longitude = e.detail.longitude;
					steps = navigateToStep(steps, 1);
				}}
				on:cancel={() => close()}
				on:next={() => {
					steps = navigateToStep(steps, 1);
				}}
			/>
		{/if}
		{#if steps[1].selected}
			<LocationDetails
				currentUser={user}
				initialLocation={location}
				{collection}
				bind:editingLocation={location}
				on:back={() => {
					steps = navigateToStep(steps, 0);
				}}
				on:save={(e) => {
					location.name = e.detail.name;
					location.category = e.detail.category;
					location.is_public = e.detail.is_public;
					location.link = e.detail.link;
					location.description = e.detail.description;
					location.latitude = e.detail.latitude;
					location.longitude = e.detail.longitude;
					location.location = e.detail.location;
					location.tags = e.detail.tags;
					location.user = e.detail.user;
					location.id = e.detail.id;
					location.price = e.detail.price;
					location.price_currency = e.detail.price_currency;

					// Mark that a save occurred so close() will notify parent
					didSave = true;

					steps = navigateToStep(steps, 2);
				}}
			/>
		{/if}
		{#if steps[2].selected}
			<LocationMedia
				bind:images={location.images}
				bind:attachments={location.attachments}
				bind:trails={location.trails}
				itemName={location.name}
				userIsOwner={user?.uuid === location.user?.uuid}
				on:back={() => {
					steps = navigateToStep(steps, 1);
				}}
				itemId={location.id}
				on:next={() => {
					steps = navigateToStep(steps, 3);
				}}
				measurementSystem={user?.measurement_system || 'metric'}
			/>
		{/if}
		{#if steps[3].selected}
			<LocationVisits
				bind:visits={location.visits}
				bind:trails={location.trails}
				objectId={location.id}
				on:back={() => {
					steps = navigateToStep(steps, 2);
				}}
				on:close={() => close()}
				measurementSystem={user?.measurement_system || 'metric'}
				{collection}
				initialVisitDate={storedInitialVisitDate}
				currentUserUsername={user?.username || null}
			/>
		{/if}
	</div>
</dialog>
