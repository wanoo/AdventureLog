<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import type { Collection, Lodging, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import Bed from '~icons/mdi/bed';
	import LodgingDetails from './LodgingDetails.svelte';
	import MediaStep from '../shared/MediaStep.svelte';
	import LodgingVisits from './LodgingVisits.svelte';
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

	function createEmptyLodging(): Lodging {
		return {
			id: '',
			user: '',
			name: '',
			type: '',
			description: null,
			rating: null,
			link: null,
			reservation_number: null,
			price: null,
			price_currency: 'USD',
			latitude: null,
			longitude: null,
			location: null,
			is_public: false,
			collections: [],
			created_at: '',
			updated_at: '',
			images: [],
			attachments: [],
			visits: [],
			tags: null
		};
	}

	export let lodging: Lodging = createEmptyLodging();

	export let lodgingToEdit: Lodging | null = null;

	// Track which lodging we're currently editing to prevent unnecessary overwrites
	let previousLodgingId: string | null = null;

	// Reactively update internal state when switching between edit/new.
	// This prevents stale values when the parent reuses `bind:lodging`.
	// Only runs when actually switching to a different lodging, not on every reactive update.
	$: {
		const currentLodgingId = lodgingToEdit?.id ?? null;

		if (currentLodgingId !== previousLodgingId) {
			previousLodgingId = currentLodgingId;

			if (lodgingToEdit) {
				lodging = {
					id: lodgingToEdit.id || '',
					user: lodgingToEdit.user || '',
					name: lodgingToEdit.name || '',
					type: lodgingToEdit.type || '',
					description: lodgingToEdit.description || null,
					rating: lodgingToEdit.rating || null,
					link: lodgingToEdit.link || null,
					reservation_number: lodgingToEdit.reservation_number || null,
					price: lodgingToEdit.price || null,
					price_currency: lodgingToEdit.price_currency || 'USD',
					latitude: lodgingToEdit.latitude || null,
					longitude: lodgingToEdit.longitude || null,
					location: lodgingToEdit.location || null,
					is_public: lodgingToEdit.is_public || false,
					collections: lodgingToEdit.collections || [],
					created_at: lodgingToEdit.created_at || '',
					updated_at: lodgingToEdit.updated_at || '',
					images: lodgingToEdit.images || [],
					attachments: lodgingToEdit.attachments || [],
					visits: lodgingToEdit.visits || [],
					tags: lodgingToEdit.tags || null
				};
			} else if (!lodging?.id) {
				// Only reset to empty if we don't already have a saved lodging with an ID
				lodging = createEmptyLodging();
				storedInitialVisitDate = initialVisitDate;
				// Reset steps to details when creating a new lodging
				steps = navigateToStep(steps, 0);
			}
		}
	}

	onMount(async () => {
		modal = document.getElementById('my_modal_1') as HTMLDialogElement;
		modal.showModal();
	});

	function close() {
		// If a save occurred, notify the parent with appropriate event
		if (didSave) {
			if (lodgingToEdit) {
				dispatch('save', lodging);
			} else {
				dispatch('create', lodging);
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
						<Bed class="w-6 h-6 text-primary" />
					</div>
					<div>
						<h1 class="text-3xl font-bold text-primary bg-clip-text">
							{lodgingToEdit ? $t('lodging.edit_lodging') : $t('lodging.new_lodging')}
						</h1>
						<p class="text-sm text-base-content/60">
							{lodgingToEdit
								? $t('lodging.update_lodging_details')
								: $t('lodging.create_new_lodging')}
						</p>
					</div>
				</div>

				<StepTimeline
					{steps}
					entityId={lodging?.id ?? ''}
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
			<LodgingDetails
				currentUser={user}
				initialLodging={lodging}
				{collection}
				bind:editingLodging={lodging}
				on:back={() => {
					steps = navigateToStep(steps, 0);
				}}
				on:save={(e) => {
					// Update the entire lodging object with all saved data
					const detail = e.detail || {};
					const previousImages = lodging.images || [];
					const previousAttachments = lodging.attachments || [];
					lodging = { ...lodging, ...detail };
					// Preserve any prefilled 'rec-' images or attachments if the server returned an empty array
					if (Array.isArray(detail.images)) {
						if (
							detail.images.length === 0 &&
							previousImages.some((i) => String(i.id).startsWith('rec-'))
						) {
							lodging.images = previousImages;
						}
					} else {
						lodging.images = previousImages;
					}
					if (Array.isArray(detail.attachments)) {
						if (
							detail.attachments.length === 0 &&
							previousAttachments.some((a) => String(a.id).startsWith('rec-'))
						) {
							lodging.attachments = previousAttachments;
						}
					} else {
						lodging.attachments = previousAttachments;
					}

					// Mark that a save occurred so close() will notify parent
					didSave = true;

					// Only allow moving to next steps once we have a persisted id.
					if (!lodging?.id) {
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
			<LodgingVisits
				{collection}
				visits={lodging.visits || []}
				lodgingId={lodging.id}
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
					const existingVisits = (lodging.visits || []).filter(v => v.id !== e.detail.id);
					lodging.visits = [...existingVisits, e.detail];
				}}
				on:visitDeleted={(e) => {
					// Remove the visit from the array
					lodging.visits = (lodging.visits || []).filter(v => v.id !== e.detail);
				}}
			/>
		{/if}
		{#if steps[2].selected}
			<MediaStep
				bind:images={lodging.images}
				bind:attachments={lodging.attachments}
				itemName={lodging.name}
				on:back={() => {
					steps = navigateToStep(steps, 1);
				}}
				on:close={() => close()}
				itemId={lodging.id}
				contentType="lodging"
			/>
		{/if}
	</div>
</dialog>
