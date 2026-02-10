<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import type { Collection, Lodging, MoneyValue, User } from '$lib/types';
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
	import { DEFAULT_CURRENCY, normalizeMoneyPayload, toMoneyValue } from '$lib/money';
	import MapIcon from '~icons/mdi/map';
	import InfoIcon from '~icons/mdi/information';

	const dispatch = createEventDispatcher();

	let isReverseGeocoding = false;

	let initialSelection: {
		name: string;
		lat: number;
		lng: number;
		location: string;
	} | null = null;

	// Props
	export let initialLodging: any = null;
	export let currentUser: any = null;
	export let editingLodging: any = null;
	export let collection: Collection | null = null;

	// Form data
	let lodging: {
		name: string;
		type: string;
		description: string;
		link: string;
		reservation_number: string | null;
		price: number | null;
		price_currency: string | null;
		latitude: number | null;
		longitude: number | null;
		location: string;
		collections?: string[];
		is_public?: boolean;
		tags?: string[];
	} = {
		name: '',
		type: '',
		description: '',
		link: '',
		reservation_number: null,
		price: null,
		price_currency: DEFAULT_CURRENCY,
		latitude: null,
		longitude: null,
		location: '',
		collections: collection?.id ? [collection.id] : [],
		is_public: true,
		tags: []
	};

	let user: User | null = null;
	let lodgingToEdit: Lodging | null = null;
	let moneyValue: MoneyValue = { amount: null, currency: DEFAULT_CURRENCY };
	let preferredCurrency: string = DEFAULT_CURRENCY;

	$: user = currentUser;
	$: lodgingToEdit = editingLodging;
	$: preferredCurrency = user?.default_currency || DEFAULT_CURRENCY;
	$: {
		const isNewLodging = !(initialLodging && initialLodging.id);
		const isEditing = Boolean(editingLodging && editingLodging.id);
		if (isNewLodging && !isEditing && lodging.price_currency === DEFAULT_CURRENCY) {
			lodging.price_currency = preferredCurrency;
		}
	}
	$: moneyValue =
		lodging.price === null
			? { amount: null, currency: lodging.price_currency || null }
			: toMoneyValue(lodging.price, lodging.price_currency, preferredCurrency);
	$: initialSelection =
		initialLodging && initialLodging.latitude && initialLodging.longitude
			? {
					name: initialLodging.name || '',
					lat: Number(initialLodging.latitude),
					lng: Number(initialLodging.longitude),
					location: initialLodging.location || ''
				}
			: null;

	function handleLocationUpdate(
		event: CustomEvent<{ name?: string; lat: number; lng: number; location: string }>
	) {
		const { name, lat, lng, location } = event.detail;
		if (!lodging.name && name) lodging.name = name;
		lodging.latitude = lat;
		lodging.longitude = lng;
		lodging.location = location;
	}

	function handleLocationClear() {
		lodging.latitude = null;
		lodging.longitude = null;
		lodging.location = '';
	}

	async function handleSave() {
		if (!lodging.name || !lodging.type) return;

		if (lodging.latitude !== null && typeof lodging.latitude === 'number') {
			lodging.latitude = parseFloat(lodging.latitude.toFixed(6));
		}
		if (lodging.longitude !== null && typeof lodging.longitude === 'number') {
			lodging.longitude = parseFloat(lodging.longitude.toFixed(6));
		}
		if (collection && collection.id) {
			if (!lodging.collections || lodging.collections.length === 0) {
				lodging.collections = [collection.id];
			} else if (!lodging.collections.includes(collection.id)) {
				lodging.collections = [...lodging.collections, collection.id];
			}
		}

		let payload: any = { ...lodging };

		if (lodging.price === null) {
			payload.price = null;
			payload.price_currency = null;
		} else {
			payload = normalizeMoneyPayload(payload, 'price', 'price_currency', preferredCurrency);
		}

		if (!payload.link || payload.link.trim() === '') {
			delete payload.link;
		}

		if (lodgingToEdit && lodgingToEdit.id) {
			if (
				(!payload.collections || payload.collections.length === 0) &&
				lodgingToEdit.collections &&
				lodgingToEdit.collections.length > 0
			) {
				delete payload.collections;
			}

			const res = await fetch(`/api/lodging/${lodgingToEdit.id}`, {
				method: 'PATCH',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			lodging = await res.json();
		} else {
			const res = await fetch(`/api/lodging`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(payload)
			});
			lodging = await res.json();
		}

		dispatch('save', { ...lodging });
	}

	function handleBack() {
		dispatch('back');
	}

	onMount(() => {
		if (initialLodging && initialLodging.latitude && initialLodging.longitude) {
			lodging.latitude = initialLodging.latitude;
			lodging.longitude = initialLodging.longitude;
			if (!lodging.name) lodging.name = initialLodging.name || '';
			if (initialLodging.location) lodging.location = initialLodging.location;
		}

		if (initialLodging && typeof initialLodging === 'object') {
			lodging.name = initialLodging.name || '';
			lodging.type = initialLodging.type || '';
			lodging.link = initialLodging.link || '';
			lodging.description = initialLodging.description || '';
			lodging.is_public = initialLodging.is_public ?? true;
			lodging.reservation_number = initialLodging.reservation_number || null;
			const money = toMoneyValue(
				initialLodging.price,
				initialLodging.price_currency,
				preferredCurrency
			);
			lodging.price = money.amount;
			lodging.price_currency = money.currency || preferredCurrency;

			if (initialLodging.location) {
				lodging.location = initialLodging.location;
			}

			if (initialLodging.tags && Array.isArray(initialLodging.tags)) {
				lodging.tags = initialLodging.tags;
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
					<NameField bind:value={lodging.name} placeholder={$t('lodging.enter_lodging_name')} />

					<!-- Type Field -->
					<div class="form-control">
						<label class="label" for="type">
							<span class="label-text font-medium">
								{$t('lodging.type')} <span class="text-error">*</span>
							</span>
						</label>
						<select
							class="select select-bordered w-full bg-base-100/80 focus:bg-base-100"
							name="type"
							id="type"
							required
							bind:value={lodging.type}
						>
							<option disabled value="">{$t('lodging.select_type')}</option>
							<option value="hotel">{$t('lodging.hotel')}</option>
							<option value="hostel">{$t('lodging.hostel')}</option>
							<option value="resort">{$t('lodging.resort')}</option>
							<option value="bnb">{$t('lodging.bnb')}</option>
							<option value="campground">{$t('lodging.campground')}</option>
							<option value="cabin">{$t('lodging.cabin')}</option>
							<option value="apartment">{$t('lodging.apartment')}</option>
							<option value="house">{$t('lodging.house')}</option>
							<option value="villa">{$t('lodging.villa')}</option>
							<option value="motel">{$t('lodging.motel')}</option>
							<option value="other">{$t('lodging.other')}</option>
						</select>
					</div>

					<!-- Reservation Number -->
					<div class="form-control">
						<label class="label" for="reservation">
							<span class="label-text font-medium">{$t('lodging.reservation_number')}</span>
						</label>
						<input
							type="text"
							id="reservation"
							bind:value={lodging.reservation_number}
							class="input input-bordered bg-base-100/80 focus:bg-base-100"
							placeholder={$t('lodging.enter_reservation_number')}
						/>
					</div>

					<MoneyInput
						label={$t('adventures.price')}
						value={moneyValue}
						on:change={(event) => {
							lodging.price = event.detail.amount;
							lodging.price_currency =
								event.detail.amount === null ? null : event.detail.currency || preferredCurrency;
						}}
					/>
				</div>

				<!-- Right Column -->
				<div class="space-y-4">
					<LinkField bind:value={lodging.link} placeholder={$t('lodging.enter_link')} />

					<PublicToggle
						bind:checked={lodging.is_public}
						label={$t('lodging.public_lodging')}
						description={$t('lodging.public_lodging_description')}
					/>

					<DescriptionWithGenerate
						bind:text={lodging.description}
						entityName={lodging.name}
						disabled={!lodging.type}
					/>
				</div>
			</div>
		</InfoCard>

		<!-- Tags Section -->
		<TagsCard bind:tags={lodging.tags} />

		<!-- Location Search & Map Section -->
		<InfoCard
			title={$t('adventures.location_map')}
			icon={MapIcon}
			iconColorClass="text-secondary"
			iconBgClass="bg-secondary/10"
		>
			<LocationSearchMap
				{initialSelection}
				bind:isReverseGeocoding
				bind:displayName={lodging.location}
				displayNamePosition="before"
				on:update={handleLocationUpdate}
				on:clear={handleLocationClear}
			/>
		</InfoCard>

		<!-- Action Buttons -->
		<DetailsActionButtons
			showBack={true}
			disabled={!lodging.name || !lodging.type || isReverseGeocoding}
			isProcessing={isReverseGeocoding}
			on:back={handleBack}
			on:save={handleSave}
		/>
	</div>
</div>
