<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import type { Collection, Transportation, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import Plane from '~icons/mdi/airplane';
	import TransportationQuickStart from './TransportationQuickStart.svelte';
	import MediaStep from '../shared/MediaStep.svelte';
	import TransportationDetails from './TransportationDetails.svelte';
	import TransportationVisits from './TransportationVisits.svelte';
	import { EntityModal, type ModalStep, navigateToStep } from '../shared/modal';

	export let user: User | null = null;
	export let collection: Collection | null = null;
	export let initialVisitDate: string | null = null;
	export let collaborativeMode: boolean = false;

	const dispatch = createEventDispatcher();

	// Store the initial visit date internally so it persists even if parent clears it
	let storedInitialVisitDate: string | null = initialVisitDate;

	// Whether a save/create occurred during this modal session
	let didSave = false;

	// Airport mode state (shared between QuickStart and Details)
	let airportMode = false;

	let entityModal: EntityModal;

	let steps: ModalStep[] = [
		{ name: $t('adventures.quick_start'), selected: true, requires_id: false },
		{ name: $t('adventures.details'), selected: false, requires_id: false },
		{ name: $t('adventures.visits'), selected: false, requires_id: true },
		{ name: $t('settings.media'), selected: false, requires_id: true }
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
				// When editing, skip quick start and go to details
				steps = navigateToStep(steps, 1);
			} else if (!transportation?.id) {
				transportation = createEmptyTransportation();
				storedInitialVisitDate = initialVisitDate;
				steps = navigateToStep(steps, 0);
			}
		}
	}

	function close() {
		if (didSave) {
			dispatch(transportationToEdit ? 'save' : 'create', transportation);
		}
		dispatch('close');
	}

	function handleStepsChange(e: CustomEvent<ModalStep[]>) {
		steps = e.detail;
	}

	$: modalTitle = transportationToEdit
		? $t('transportation.edit_transportation')
		: $t('transportation.new_transportation');
	$: modalSubtitle = transportationToEdit
		? $t('transportation.update_transportation_details')
		: $t('transportation.create_new_transportation');
</script>

<EntityModal
	bind:this={entityModal}
	modalId="transportation_modal"
	icon={Plane}
	title={modalTitle}
	subtitle={modalSubtitle}
	{steps}
	entityId={transportation?.id ?? ''}
	{didSave}
	isEditing={!!transportationToEdit}
	on:close={close}
	on:save={() => dispatch('save', transportation)}
	on:create={() => dispatch('create', transportation)}
	on:stepsChange={handleStepsChange}
>
	{#if steps[0].selected}
		<TransportationQuickStart
			bind:airportMode
			on:cancel={close}
			on:next={() => {
				steps = navigateToStep(steps, 1);
			}}
			on:locationsSelected={(e) => {
				const { origin, destination, airportMode: eventAirportMode } = e.detail;
				// Update modal-level airportMode from event
				airportMode = eventAirportMode;
				if (origin) {
					transportation.from_location = origin.location || origin.name;
					transportation.origin_latitude = origin.latitude;
					transportation.origin_longitude = origin.longitude;
					if (origin.code) transportation.start_code = origin.code;
				}
				if (destination) {
					transportation.to_location = destination.location || destination.name;
					transportation.destination_latitude = destination.latitude;
					transportation.destination_longitude = destination.longitude;
					if (destination.code) transportation.end_code = destination.code;
				}
				// Set type to plane if airport mode was used
				if (airportMode && !transportation.type) {
					transportation.type = 'plane';
				}
				// Auto-generate name if empty
				if (!transportation.name && origin && destination) {
					transportation.name = `${origin.name} → ${destination.name}`;
				}
				steps = navigateToStep(steps, 1);
			}}
		/>
	{/if}
	{#if steps[1].selected}
		<TransportationDetails
			currentUser={user}
			initialTransportation={transportation}
			{collection}
			bind:airportMode
			bind:editingTransportation={transportation}
			on:back={() => {
				steps = navigateToStep(steps, 0);
			}}
			on:save={(e) => {
				transportation = { ...transportation, ...e.detail };
				didSave = true;

				if (!transportation?.id) {
					addToast('error', $t('adventures.transportation_save_error'));
					steps = navigateToStep(steps, 1);
					return;
				}

				steps = navigateToStep(steps, 2);
			}}
		/>
	{/if}
	{#if steps[2].selected}
		<TransportationVisits
			{collection}
			visits={transportation.visits || []}
			transportationId={transportation.id}
			initialVisitDate={storedInitialVisitDate}
			currentUserUsername={user?.username || null}
			on:back={() => {
				steps = navigateToStep(steps, 1);
			}}
			on:close={() => {
				steps = navigateToStep(steps, 3);
			}}
			on:visitAdded={(e) => {
				const existingVisits = (transportation.visits || []).filter((v) => v.id !== e.detail.id);
				transportation.visits = [...existingVisits, e.detail];
			}}
			on:visitDeleted={(e) => {
				transportation.visits = (transportation.visits || []).filter((v) => v.id !== e.detail);
			}}
		/>
	{/if}
	{#if steps[3].selected}
		<MediaStep
			bind:images={transportation.images}
			bind:attachments={transportation.attachments}
			itemName={transportation.name}
			on:back={() => {
				steps = navigateToStep(steps, 2);
			}}
			on:close={close}
			itemId={transportation.id}
			contentType="transportation"
			start_date={transportation.visits?.[0]?.start_date ?? null}
			end_date={transportation.visits?.[0]?.end_date ?? null}
			{user}
			{collaborativeMode}
		/>
	{/if}
</EntityModal>
