<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import type { Collection, Location, Transportation, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import Plane from '~icons/mdi/airplane';
	import MediaStep from '../shared/MediaStep.svelte';
	import TransportationDetails from './TransportationDetails.svelte';
	import TransportationVisits from './TransportationVisits.svelte';
	import { StepTimeline, type ModalStep, navigateToStep } from '../shared/modal';

	export let user: User | null = null;
	export let collection: Collection | null = null;
	export let initialVisitDate: string | null = null; // Used to pre-fill visit date when adding from itinerary planner

	const dispatch = createEventDispatcher();

	// Store the initial visit date internally so it persists even if parent clears it
	let storedInitialVisitDate: string | null = initialVisitDate;

	let modal: HTMLDialogElement;

	// Whether a save/create occurred during this modal session
	let didSave = false;

	let steps: ModalStep[] = [
		{
			name: $t('adventures.details'),
			selected: true,
			requires_id: false
		},
		{
			name: $t('adventures.visits'),
			selected: false,
			requires_id: true
		},
		{
			name: $t('settings.media'),
			selected: false,
			requires_id: true
		}
	];

	function createEmptyTransportation(): Transportation {
		return {
			id: '',
			user: '',
			name: '',
			type: '',
			description: null,
			rating: null,
			link: null,
			flight_number: null,
			from_location: null,
			to_location: null,
			origin_latitude: null,
			origin_longitude: null,
			destination_latitude: null,
			destination_longitude: null,
			start_code: null,
			end_code: null,
			is_public: false,
			distance: null,
			price: null,
			price_currency: 'USD',
			collections: [],
			created_at: '',
			updated_at: '',
			images: [],
			attachments: [],
			visits: [],
			tags: null
		};
	}

	export let transportation: Transportation = createEmptyTransportation();

	export let transportationToEdit: Transportation | null = null;

	// Track which transportation we're currently editing to prevent unnecessary overwrites
	let previousTransportationId: string | null = null;

	// Reactively update internal state when switching between edit/new.
	// This prevents stale values when the parent reuses `bind:transportation`.
	// Only runs when actually switching to a different transportation, not on every reactive update.
	$: {
		const currentTransportationId = transportationToEdit?.id || null;

		if (currentTransportationId !== previousTransportationId) {
			previousTransportationId = currentTransportationId;

			if (transportationToEdit) {
				transportation = {
					id: transportationToEdit.id || '',
					user: transportationToEdit.user || '',
					name: transportationToEdit.name || '',
					type: transportationToEdit.type || '',
					description: transportationToEdit.description || null,
					rating: transportationToEdit.rating || null,
					link: transportationToEdit.link || null,
					flight_number: transportationToEdit.flight_number || null,
					from_location: transportationToEdit.from_location || null,
					to_location: transportationToEdit.to_location || null,
					origin_latitude: transportationToEdit.origin_latitude || null,
					origin_longitude: transportationToEdit.origin_longitude || null,
					destination_latitude: transportationToEdit.destination_latitude || null,
					destination_longitude: transportationToEdit.destination_longitude || null,
					start_code: transportationToEdit.start_code || null,
					end_code: transportationToEdit.end_code || null,
					is_public: transportationToEdit.is_public || false,
					distance: transportationToEdit.distance || null,
					price: transportationToEdit.price ?? null,
					price_currency: transportationToEdit.price_currency || 'USD',
					collections: transportationToEdit.collections || [],
					created_at: transportationToEdit.created_at || '',
					updated_at: transportationToEdit.updated_at || '',
					images: transportationToEdit.images || [],
					attachments: transportationToEdit.attachments || [],
					visits: transportationToEdit.visits || [],
					tags: transportationToEdit.tags || null
				};
			} else if (!transportation?.id) {
				// Only reset to empty if we don't already have a saved transportation with an ID
				transportation = createEmptyTransportation();
				storedInitialVisitDate = initialVisitDate;
				// Reset steps to details when creating a new transportation
				steps = navigateToStep(steps, 0);
			}
		}
	}

	onMount(async () => {
		modal = document.getElementById('transportation_modal') as HTMLDialogElement;
		modal.showModal();
	});

	function close() {
		// If a save occurred, notify the parent with appropriate event
		if (didSave) {
			if (transportationToEdit) {
				dispatch('save', transportation);
			} else {
				dispatch('create', transportation);
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
<dialog id="transportation_modal" class="modal backdrop-blur-sm">
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
						<Plane class="w-6 h-6 text-primary" />
					</div>
					<div>
						<h1 class="text-3xl font-bold text-primary bg-clip-text">
							{transportationToEdit
								? $t('transportation.edit_transportation')
								: $t('transportation.new_transportation')}
						</h1>
						<p class="text-sm text-base-content/60">
							{transportationToEdit
								? $t('transportation.update_transportation_details')
								: $t('transportation.create_new_transportation')}
						</p>
					</div>
				</div>

				<StepTimeline
					{steps}
					entityId={transportation?.id ?? ''}
					on:stepClick={(e) => {
						steps = navigateToStep(steps, e.detail.index);
					}}
				/>

				<!-- Close Button -->
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
			</div>
		</div>

		{#if steps[0].selected}
			<TransportationDetails
				currentUser={user}
				initialTransportation={transportation}
				{collection}
				bind:editingTransportation={transportation}
				on:back={() => {
					steps = navigateToStep(steps, 0);
				}}
				on:save={(e) => {
					// Update the entire transportation object with all saved data
					transportation = { ...transportation, ...e.detail };

					// Mark that a save occurred so close() will notify parent
					didSave = true;

					// Only allow moving to next steps once we have a persisted id.
					if (!transportation?.id) {
						addToast('error', $t('adventures.lodging_save_error'));
						steps = navigateToStep(steps, 0);
						return;
					}

					steps = navigateToStep(steps, 1);
				}}
				initialVisitDate={storedInitialVisitDate}
			/>
		{/if}
		{#if steps[1].selected}
			<TransportationVisits
				{collection}
				visits={transportation.visits || []}
				transportationId={transportation.id}
				initialVisitDate={storedInitialVisitDate}
				currentUserUsername={user?.username || null}
				on:back={() => {
					steps = navigateToStep(steps, 0);
				}}
				on:close={() => {
					steps = navigateToStep(steps, 2);
				}}
				on:visitAdded={(e) => {
					// Update or add the visit (filter out existing with same ID first)
					const existingVisits = (transportation.visits || []).filter(v => v.id !== e.detail.id);
					transportation.visits = [...existingVisits, e.detail];
				}}
				on:visitDeleted={(e) => {
					// Remove the visit from the array
					transportation.visits = (transportation.visits || []).filter(v => v.id !== e.detail);
				}}
			/>
		{/if}
		{#if steps[2].selected}
			<MediaStep
				bind:images={transportation.images}
				bind:attachments={transportation.attachments}
				itemName={transportation.name}
				on:back={() => {
					steps = navigateToStep(steps, 1);
				}}
				on:close={() => close()}
				itemId={transportation.id}
				contentType="transportation"
				start_date={transportation.visits?.[0]?.start_date ?? null}
				end_date={transportation.visits?.[0]?.end_date ?? null}
				{user}
			/>
		{/if}
	</div>
</dialog>
