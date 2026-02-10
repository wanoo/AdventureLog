<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import type { Collection, Transportation, MoneyValue, User } from '$lib/types';
	import LocationSearchMap from '../shared/LocationSearchMap.svelte';
	import MoneyInput from '../shared/MoneyInput.svelte';
	import {
		InfoCard,
		NameField,
		LinkField,
		PublicToggle,
		DescriptionWithGenerate,
		TagsCard,
		DetailsActionButtons
	} from '../shared/form';
	import { TRANSPORTATION_TYPES_ICONS } from '$lib';
	import { DEFAULT_CURRENCY, normalizeMoneyPayload, toMoneyValue } from '$lib/money';
	import MapIcon from '~icons/mdi/map';
	import InfoIcon from '~icons/mdi/information';
	import type { SearchMode } from '../shared/LocationSearchMap.svelte';

	const dispatch = createEventDispatcher();

	let isReverseGeocoding = false;
	export let searchMode: SearchMode = 'location';
	let previousTransportationType: string | null = null;

	// Props
	export let initialTransportation: any = null;
	export let currentUser: any = null;
	export let editingTransportation: any = null;
	export let collection: Collection | null = null;

	// Form data
	let transportation: any = {
		name: '',
		type: '',
		description: '',
		link: '',
		flight_number: null,
		from_location: null,
		to_location: null,
		origin_latitude: null,
		origin_longitude: null,
		destination_latitude: null,
		destination_longitude: null,
		start_code: null,
		end_code: null,
		distance: null,
		collections: collection?.id ? [collection.id] : [],
		is_public: true,
		price: null,
		price_currency: DEFAULT_CURRENCY,
		tags: []
	};

	let startCodeField: string = '';
	let endCodeField: string = '';

	let user: User | null = null;
	let transportationToEdit: Transportation | null = null;
	let moneyValue: MoneyValue = { amount: null, currency: DEFAULT_CURRENCY };
	let preferredCurrency: string = DEFAULT_CURRENCY;

	$: user = currentUser;
	$: transportationToEdit = editingTransportation;
	$: preferredCurrency = user?.default_currency || DEFAULT_CURRENCY;
	$: {
		const isNewTransportation = !(initialTransportation && initialTransportation.id);
		const isEditing = Boolean(editingTransportation && editingTransportation.id);
		if (isNewTransportation && !isEditing && transportation.price_currency === DEFAULT_CURRENCY) {
			transportation.price_currency = preferredCurrency;
		}
		moneyValue =
			transportation.price === null
				? { amount: null, currency: transportation.price_currency || null }
				: toMoneyValue(transportation.price, transportation.price_currency, preferredCurrency);
	}

	function normalizeCode(code: string | null): string | null {
		if (!code) return null;
		const trimmed = code.trim().toUpperCase();
		if (!trimmed) return null;
		return trimmed.slice(0, 5);
	}

	function clearAirportCodes() {
		startCodeField = '';
		endCodeField = '';
		transportation.start_code = null;
		transportation.end_code = null;
	}

	function handleStartCodeEvent(event: Event) {
		const target = event.target as HTMLInputElement;
		startCodeField = target?.value || '';
		transportation.start_code = normalizeCode(startCodeField);
	}

	function handleEndCodeEvent(event: Event) {
		const target = event.target as HTMLInputElement;
		endCodeField = target?.value || '';
		transportation.end_code = normalizeCode(endCodeField);
	}

	// Track search mode changes
	let prevSearchMode = searchMode;
	$: if (prevSearchMode !== searchMode) {
		prevSearchMode = searchMode;
		if (searchMode === 'location') clearAirportCodes();
	}

	// Auto-set search mode based on transportation type
	$: if (transportation.type && previousTransportationType !== transportation.type) {
		previousTransportationType = transportation.type;
		if (transportation.type === 'plane' && searchMode === 'location') {
			searchMode = 'airport';
		} else if (transportation.type === 'train' && searchMode === 'location') {
			searchMode = 'train';
		} else if (transportation.type === 'bus' && searchMode === 'location') {
			searchMode = 'bus';
		}
	}

	function handleTransportationUpdate(
		event: CustomEvent<{
			start: { name: string; lat: number; lng: number; location: string; code?: string | null };
			end: { name: string; lat: number; lng: number; location: string; code?: string | null };
		}>
	) {
		const { start, end } = event.detail;

		transportation.from_location = start.name;
		transportation.origin_latitude = start.lat;
		transportation.origin_longitude = start.lng;
		transportation.start_code = normalizeCode(start.code || '');
		startCodeField = startCodeField || transportation.start_code || '';

		transportation.to_location = end.name;
		transportation.destination_latitude = end.lat;
		transportation.destination_longitude = end.lng;
		transportation.end_code = normalizeCode(end.code || '');
		endCodeField = endCodeField || transportation.end_code || '';

		if (!transportation.name) {
			transportation.name = `${start.name} → ${end.name}`;
		}
	}

	function handleLocationClear() {
		transportation.from_location = null;
		transportation.to_location = null;
		transportation.origin_latitude = null;
		transportation.origin_longitude = null;
		transportation.destination_latitude = null;
		transportation.destination_longitude = null;
		transportation.start_code = null;
		transportation.end_code = null;
	}

	async function handleSave() {
		if (!transportation.name || !transportation.type) return;

		transportation.start_code = normalizeCode(startCodeField || transportation.start_code);
		transportation.end_code = normalizeCode(endCodeField || transportation.end_code);

		// Round coordinates
		['origin_latitude', 'origin_longitude', 'destination_latitude', 'destination_longitude'].forEach(field => {
			if (transportation[field] !== null && typeof transportation[field] === 'number') {
				transportation[field] = parseFloat(transportation[field].toFixed(6));
			}
		});

		if (collection && collection.id) {
			if (!transportation.collections || transportation.collections.length === 0) {
				transportation.collections = [collection.id];
			} else if (!transportation.collections.includes(collection.id)) {
				transportation.collections = [...transportation.collections, collection.id];
			}
		}

		let payload: any = { ...transportation };

		if (transportation.price === null) {
			payload.price = null;
			payload.price_currency = null;
		} else {
			payload = normalizeMoneyPayload(payload, 'price', 'price_currency', preferredCurrency);
		}

		if (!payload.link || payload.link.trim() === '') {
			delete payload.link;
		}

		if (transportationToEdit && transportationToEdit.id) {
			if (
				(!payload.collections || payload.collections.length === 0) &&
				transportationToEdit.collections &&
				transportationToEdit.collections.length > 0
			) {
				delete payload.collections;
			}

			const res = await fetch(`/api/transportations/${transportationToEdit.id}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			transportation = await res.json();
		} else {
			const res = await fetch(`/api/transportations`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			transportation = await res.json();
		}

		dispatch('save', { ...transportation });
	}

	function handleBack() {
		dispatch('back');
	}

	onMount(() => {
		if (initialTransportation && typeof initialTransportation === 'object') {
			transportation.name = initialTransportation.name || '';
			transportation.type = initialTransportation.type || '';
			transportation.link = initialTransportation.link || '';
			transportation.description = initialTransportation.description || '';
			transportation.is_public = initialTransportation.is_public ?? true;
			transportation.flight_number = initialTransportation.flight_number || null;
			transportation.start_code = initialTransportation.start_code || null;
			transportation.end_code = initialTransportation.end_code || null;
			transportation.distance = initialTransportation.distance || null;
			transportation.price = initialTransportation.price ? Number(initialTransportation.price) : null;
			transportation.price_currency = initialTransportation.price_currency || preferredCurrency;
			moneyValue = toMoneyValue(transportation.price, transportation.price_currency, preferredCurrency);

			transportation.from_location = initialTransportation.from_location || null;
			transportation.to_location = initialTransportation.to_location || null;
			transportation.origin_latitude = initialTransportation.origin_latitude || null;
			transportation.origin_longitude = initialTransportation.origin_longitude || null;
			transportation.destination_latitude = initialTransportation.destination_latitude || null;
			transportation.destination_longitude = initialTransportation.destination_longitude || null;
			startCodeField = transportation.start_code || '';
			endCodeField = transportation.end_code || '';

			if (initialTransportation.tags && Array.isArray(initialTransportation.tags)) {
				transportation.tags = initialTransportation.tags;
			}
		}
	});
</script>

<div class="min-h-screen bg-gradient-to-br from-base-200/30 via-base-100 to-primary/5 p-6">
	<div class="max-w-full mx-auto space-y-6">
		<!-- Basic Information Section -->
		<InfoCard title={$t('adventures.basic_information')} icon={InfoIcon}>
			<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
				<!-- Left Column -->
				<div class="space-y-4">
					<NameField
						bind:value={transportation.name}
						placeholder={$t('transportation.enter_transportation_name')}
					/>

					<!-- Type Field -->
					<div class="form-control">
						<label class="label" for="type">
							<span class="label-text font-medium">
								{$t('transportation.type')} <span class="text-error">*</span>
							</span>
						</label>
						<select
							class="select select-bordered w-full bg-base-100/80 focus:bg-base-100"
							name="type"
							id="type"
							required
							bind:value={transportation.type}
						>
							<option disabled value="">{$t('transportation.select_type')}</option>
							{#each Object.entries(TRANSPORTATION_TYPES_ICONS) as [key, icon]}
								<option value={key}>{icon} {key.charAt(0).toUpperCase() + key.slice(1)}</option>
							{/each}
						</select>
					</div>

					<!-- Flight Number -->
					<div class="form-control">
						<label class="label" for="flight_number">
							<span class="label-text font-medium">{$t('transportation.flight_number')}</span>
						</label>
						<input
							type="text"
							id="flight_number"
							bind:value={transportation.flight_number}
							class="input input-bordered bg-base-100/80 focus:bg-base-100"
							placeholder={$t('transportation.enter_flight_number')}
						/>
					</div>

					<!-- Start/End Codes -->
					{#if searchMode !== 'location'}
						<div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
							<div class="form-control">
								<label class="label" for="start_code">
									<span class="label-text font-medium">
										{$t('transportation.departure_code') || 'Departure code'}
									</span>
								</label>
								<input
									type="text"
									id="start_code"
									value={startCodeField}
									on:input={handleStartCodeEvent}
									class="input input-bordered bg-base-100/80 focus:bg-base-100 uppercase"
									maxlength="5"
									placeholder={searchMode === 'airport' ? 'JFK' : $t('transportation.departure_code')}
								/>
							</div>
							<div class="form-control">
								<label class="label" for="end_code">
									<span class="label-text font-medium">
										{$t('transportation.arrival_code') || 'Arrival code'}
									</span>
								</label>
								<input
									type="text"
									id="end_code"
									value={endCodeField}
									on:input={handleEndCodeEvent}
									class="input input-bordered bg-base-100/80 focus:bg-base-100 uppercase"
									maxlength="5"
									placeholder={searchMode === 'airport' ? 'LHR' : $t('transportation.arrival_code')}
								/>
							</div>
						</div>
					{/if}

					<MoneyInput
						label={$t('adventures.price')}
						value={moneyValue}
						on:change={(event) => {
							transportation.price = event.detail.amount;
							transportation.price_currency =
								event.detail.amount === null ? null : event.detail.currency || preferredCurrency;
						}}
					/>
				</div>

				<!-- Right Column -->
				<div class="space-y-4">
					<LinkField bind:value={transportation.link} placeholder={$t('transportation.enter_link')} />

					<PublicToggle
						bind:checked={transportation.is_public}
						label={$t('transportation.public_transportation')}
						description={$t('transportation.public_transportation_description')}
					/>

					<DescriptionWithGenerate
						bind:text={transportation.description}
						entityName={transportation.name}
						disabled={!transportation.type}
					/>
				</div>
			</div>
		</InfoCard>

		<!-- Tags Section -->
		<TagsCard bind:tags={transportation.tags} />

		<!-- Location Search & Map Section -->
		<InfoCard
			title={$t('adventures.location_map')}
			icon={MapIcon}
			iconColorClass="text-secondary"
			iconBgClass="bg-secondary/10"
		>
			<LocationSearchMap
				bind:isReverseGeocoding
				transportationMode={true}
				bind:searchMode
				showDisplayNameInput={false}
				initialStartLocation={initialTransportation?.origin_latitude && initialTransportation?.origin_longitude
					? {
							name: initialTransportation.from_location || '',
							lat: Number(initialTransportation.origin_latitude),
							lng: Number(initialTransportation.origin_longitude),
							location: initialTransportation.from_location || ''
						}
					: null}
				initialEndLocation={initialTransportation?.destination_latitude && initialTransportation?.destination_longitude
					? {
							name: initialTransportation.to_location || '',
							lat: Number(initialTransportation.destination_latitude),
							lng: Number(initialTransportation.destination_longitude),
							location: initialTransportation.to_location || ''
						}
					: null}
				initialStartCode={initialTransportation?.start_code || null}
				initialEndCode={initialTransportation?.end_code || null}
				on:transportationUpdate={handleTransportationUpdate}
				on:clear={handleLocationClear}
			/>
		</InfoCard>

		<!-- Action Buttons -->
		<DetailsActionButtons
			showBack={true}
			disabled={!transportation.name || !transportation.type || isReverseGeocoding}
			isProcessing={isReverseGeocoding}
			on:back={handleBack}
			on:save={handleSave}
		/>
	</div>
</div>
