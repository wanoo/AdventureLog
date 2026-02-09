<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { t } from 'svelte-i18n';
	import { updateLocalDate, updateUTCDate, validateDateRange } from '$lib/dateUtils';
	import type { Collection, Lodging, MoneyValue } from '$lib/types';
	import LocationSearchMap from '../shared/LocationSearchMap.svelte';

	// Icons
	import MapIcon from '~icons/mdi/map';

	import InfoIcon from '~icons/mdi/information';
	import GenerateIcon from '~icons/mdi/lightning-bolt';
	import ArrowLeftIcon from '~icons/mdi/arrow-left';
	import SaveIcon from '~icons/mdi/content-save';
	import type { Category, User } from '$lib/types';
	import MarkdownEditor from '../MarkdownEditor.svelte';
	import TimezoneSelector from '../TimezoneSelector.svelte';
	import TagComplete from '../TagComplete.svelte';
	import MoneyInput from '../shared/MoneyInput.svelte';
	import { TagsCard, DetailsActionButtons } from '../shared/form';
	import { DEFAULT_CURRENCY, normalizeMoneyPayload, toMoneyValue } from '$lib/money';
	// @ts-ignore
	import { DateTime } from 'luxon';
	import { isAllDay } from '$lib';

	const dispatch = createEventDispatcher();

	let isReverseGeocoding = false;

	let initialSelection: {
		name: string;
		lat: number;
		lng: number;
		location: string;
		category?: any;
	} | null = null;

	// Props (would be passed in from parent component)
	export let initialLodging: any = null;
	export let currentUser: any = null;
	export let editingLodging: any = null;
	export let collection: Collection | null = null;
	export let initialVisitDate: string | null = null; // Used to pre-fill visit date when adding from itinerary planner

	// Form data properties
	let lodging: {
		name: string;
		type: string;
		description: string;
		link: string;
		check_in: string | null;
		check_out: string | null;
		timezone: string | null;
		reservation_number: string | null;
		price: number | null;
		price_currency: string | null;
		latitude: number | null;
		longitude: number | null;
		location: string;
		category?: Category | null;
		collections?: string[];
		is_public?: boolean;
		tags?: string[];
	} = {
		name: '',
		type: '',
		description: '',
		link: '',
		check_in: null,
		check_out: null,
		timezone: null,
		reservation_number: null,
		price: null,
		price_currency: DEFAULT_CURRENCY,
		latitude: null,
		longitude: null,
		location: '',
		category: null,
		collections: collection?.id ? [collection.id] : [],
		is_public: true,
		tags: []
	};

	let selectedTimezone: string = Intl.DateTimeFormat().resolvedOptions().timeZone;
	let localStartDate: string = '';
	let localEndDate: string = '';
	let allDay: boolean = true;
	let constrainDates: boolean = true;
	let fullStartDate: string = '';
	let fullEndDate: string = '';

	let user: User | null = null;
	let lodgingToEdit: Lodging | null = null;
	let wikiError = '';
	let isGeneratingDesc = false;
	let ownerUser: User | null = null;
	let dateError = '';
	let moneyValue: MoneyValue = { amount: null, currency: DEFAULT_CURRENCY };
	let preferredCurrency: string = DEFAULT_CURRENCY;

	$: user = currentUser;
	$: lodgingToEdit = editingLodging;
	// Only assign a timezone when this is a timed stay. Keep timezone null for all-day entries.
	$: lodging.timezone = allDay ? null : selectedTimezone;
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

	// Set the full date range for constraining purposes
	$: if (collection && collection.start_date && collection.end_date) {
		fullStartDate = `${collection.start_date}T00:00`;
		fullEndDate = `${collection.end_date}T23:59`;
	}

	// Reactive constraints
	$: constraintStartDate = allDay
		? fullStartDate && fullStartDate.includes('T')
			? fullStartDate.split('T')[0]
			: ''
		: fullStartDate || '';
	$: constraintEndDate = allDay
		? fullEndDate && fullEndDate.includes('T')
			? fullEndDate.split('T')[0]
			: ''
		: fullEndDate || '';

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

	function handleAllDayToggle() {
		if (allDay) {
			localStartDate = localStartDate ? localStartDate.split('T')[0] : '';
			localEndDate = localEndDate ? localEndDate.split('T')[0] : '';
			// Clear timezone for all-day stays
			lodging.timezone = null;
		} else {
			localStartDate = localStartDate ? `${localStartDate}T00:00` : '';
			localEndDate = localEndDate ? `${localEndDate}T23:59` : '';
			// Restore selected timezone when switching back to timed
			lodging.timezone = selectedTimezone;
		}

		syncAndValidateDates(false);
	}

	function handleLocalDateChange() {
		syncAndValidateDates(false);
	}

	function syncAndValidateDates(autoFillEnd: boolean): boolean {
		dateError = '';

		if (localEndDate && !localStartDate) {
			dateError = 'Start date is required when end date is provided';
			localEndDate = '';
			lodging.check_out = null;
		}

		lodging.check_in = localStartDate
			? updateUTCDate({ localDate: localStartDate, timezone: selectedTimezone, allDay }).utcDate
			: null;
		lodging.check_out = localEndDate
			? updateUTCDate({ localDate: localEndDate, timezone: selectedTimezone, allDay }).utcDate
			: null;

		if (!localEndDate && localStartDate && autoFillEnd) {
			const start = allDay
				? DateTime.fromISO(localStartDate, { zone: 'UTC' })
				: DateTime.fromISO(localStartDate, { zone: selectedTimezone });
			if (start.isValid) {
				if (allDay) {
					const defaultEnd = start.plus({ days: 1 }).toISODate();
					if (defaultEnd) {
						localEndDate = defaultEnd;
						lodging.check_out = updateUTCDate({
							localDate: defaultEnd,
							timezone: selectedTimezone,
							allDay
						}).utcDate;
					}
				} else {
					const defaultEnd = start
						.plus({ days: 1 })
						.set({ hour: 9, minute: 0, second: 0, millisecond: 0 });
					const defaultEndLocal = defaultEnd.toISO({
						suppressSeconds: true,
						suppressMilliseconds: true,
						includeOffset: false
					});
					if (defaultEndLocal) {
						localEndDate = defaultEndLocal.slice(0, 16);
						lodging.check_out = updateUTCDate({
							localDate: localEndDate,
							timezone: selectedTimezone,
							allDay
						}).utcDate;
					}
				}
			}
		}

		if (lodging.check_in || lodging.check_out) {
			const validation = validateDateRange(lodging.check_in || '', lodging.check_out || '');
			if (!validation.valid) {
				dateError = validation.error || 'Invalid date range';
				lodging.check_out = null;
				localEndDate = '';
				return false;
			}
		}

		return true;
	}

	async function generateDesc() {
		if (!lodging.name) return;

		isGeneratingDesc = true;
		wikiError = '';

		try {
			// Mock Wikipedia API call - replace with actual implementation
			const response = await fetch(`/api/generate/desc/?name=${encodeURIComponent(lodging.name)}`);
			if (response.ok) {
				const data = await response.json();
				lodging.description = data.extract || '';
			} else {
				wikiError = `${$t('adventures.wikipedia_error') || 'Error fetching description from Wikipedia'}`;
			}
		} catch (error) {
			wikiError = `${$t('adventures.wikipedia_error') || ''}`;
		} finally {
			isGeneratingDesc = false;
		}
	}

	async function handleSave() {
		if (!lodging.name || !lodging.type) {
			return;
		}

		// Ensure timezone is only persisted for timed stays
		lodging.timezone = allDay ? null : selectedTimezone;

		if (!syncAndValidateDates(true)) {
			return;
		}

		// round latitude and longitude to 6 decimal places
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

		// Build payload and avoid sending an empty `collections` array when editing
		let payload: any = { ...lodging };

		// Normalize price and currency consistently, but send explicit nulls when cleared
		if (lodging.price === null) {
			payload.price = null;
			payload.price_currency = null;
		} else {
			payload = normalizeMoneyPayload(payload, 'price', 'price_currency', preferredCurrency);
		}

		// Remove empty link to avoid URL validation errors
		if (!payload.link || payload.link.trim() === '') {
			delete payload.link;
		}

		// If we're editing and the original had collections, but the form's collections
		// is empty (i.e. user didn't modify collections), omit collections from payload so the
		// server doesn't clear them unintentionally.
		if (lodgingToEdit && lodgingToEdit.id) {
			if (
				(!payload.collections || payload.collections.length === 0) &&
				lodgingToEdit.collections &&
				lodgingToEdit.collections.length > 0
			) {
				delete payload.collections;
			}

			let res = await fetch(`/api/lodging/${lodgingToEdit.id}`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			});
			let updatedLocation = await res.json();
			lodging = updatedLocation;
		} else {
			let res = await fetch(`/api/lodging`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			});
			let newLodging = await res.json();
			lodging = newLodging;
		}

		dispatch('save', {
			...lodging
		});
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
	});

	onMount(() => {
		// Prefer lodging timezone if present, otherwise keep current selection
		if (initialLodging?.timezone) {
			selectedTimezone = initialLodging.timezone;
		}

		// Determine if existing dates are all-day using shared helper
		if (initialLodging?.check_in) {
			allDay = isAllDay(initialLodging.check_in);
		}

		// Keep lodging.timezone null for all-day entries, otherwise use selectedTimezone
		lodging.timezone = allDay ? null : selectedTimezone;

		// Convert UTC dates to local display, respecting all-day formatting
		if (initialLodging?.check_in) {
			if (allDay) {
				localStartDate = initialLodging.check_in.split('T')[0];
			} else {
				const result = updateLocalDate({
					utcDate: initialLodging.check_in,
					timezone: selectedTimezone
				});
				localStartDate = result.localDate;
			}
		}
		if (initialLodging?.check_out) {
			if (allDay) {
				localEndDate = initialLodging.check_out.split('T')[0];
			} else {
				const result = updateLocalDate({
					utcDate: initialLodging.check_out,
					timezone: selectedTimezone
				});
				localEndDate = result.localDate;
			}
		}

		if (initialLodging && typeof initialLodging === 'object') {
			// Populate all fields from initialLodging
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

			if (initialLodging.user) {
				ownerUser = initialLodging.user;
			}

			// Populate tags
			if (initialLodging.tags && Array.isArray(initialLodging.tags)) {
				lodging.tags = initialLodging.tags;
			}
		}

		// If adding from itinerary, pre-fill all-day stay with next-day checkout
		if (!initialLodging?.check_in && initialVisitDate && !localStartDate) {
			const start = DateTime.fromISO(initialVisitDate, { zone: 'UTC' });
			if (start.isValid) {
				allDay = true;
				localStartDate = start.toISODate() || '';
				const nextDay = start.plus({ days: 1 }).toISODate();
				localEndDate = nextDay || '';

				syncAndValidateDates(false);
			}
		}

		return () => {
			// no-op
		};
	});
</script>

<div class="min-h-screen bg-gradient-to-br from-base-200/30 via-base-100 to-primary/5 p-6">
	<div class="max-w-full mx-auto space-y-6">
		<!-- Location Search & Map Section - FIRST! -->
		<div class="card bg-base-100 border border-base-300 shadow-lg">
			<div class="card-body p-6">
				<div class="flex items-center gap-3 mb-6">
					<div class="p-2 bg-secondary/10 rounded-lg">
						<MapIcon class="w-5 h-5 text-secondary" />
					</div>
					<div>
						<h2 class="text-xl font-bold">{$t('adventures.location_map')}</h2>
					</div>
				</div>

				<LocationSearchMap
					{initialSelection}
					bind:isReverseGeocoding
					bind:displayName={lodging.location}
					displayNamePosition="after"
					on:update={handleLocationUpdate}
					on:clear={handleLocationClear}
				/>
			</div>
		</div>

		<!-- Basic Information Section -->
		<div class="card bg-base-100 border border-base-300 shadow-lg">
			<div class="card-body p-6">
				<div class="flex items-center gap-3 mb-6">
					<div class="p-2 bg-primary/10 rounded-lg">
						<InfoIcon class="w-5 h-5 text-primary" />
					</div>
					<h2 class="text-xl font-bold">{$t('adventures.basic_information')}</h2>
				</div>

				<div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
					<!-- Left Column -->
					<div class="space-y-4">
						<!-- Name Field -->
						<div class="form-control">
							<label class="label" for="name">
								<span class="label-text font-medium">
									{$t('adventures.name')} <span class="text-error">*</span>
								</span>
							</label>
							<input
								type="text"
								id="name"
								bind:value={lodging.name}
								class="input input-bordered bg-base-100/80 focus:bg-base-100"
								placeholder={$t('lodging.enter_lodging_name')}
								required
							/>
						</div>

						<!-- Type Field -->
						<div class="form-control">
							<label class="label" for="type">
								<span class="label-text font-medium"
									>{$t('transportation.type')} <span class="text-error">*</span></span
								>
							</label>
							<select
								class="select select-bordered w-full bg-base-100/80 focus:bg-base-100"
								name="type"
								id="type"
								required
								bind:value={lodging.type}
							>
								<option disabled value="">{$t('transportation.select_type')}</option>
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
					</div>

					<!-- Right Column -->
					<div class="space-y-4">
						<!-- Link Field -->
						<div class="form-control">
							<label class="label" for="link">
								<span class="label-text font-medium">{$t('adventures.link')}</span>
							</label>
							<input
								type="url"
								id="link"
								bind:value={lodging.link}
								class="input input-bordered bg-base-100/80 focus:bg-base-100"
								placeholder={$t('transportation.enter_link')}
							/>
						</div>

						<!-- Public Toggle -->
						<div class="form-control">
							<label class="label cursor-pointer justify-start gap-4" for="is_public">
								<input
									type="checkbox"
									class="toggle toggle-primary"
									id="is_public"
									bind:checked={lodging.is_public}
								/>
								<div>
									<span class="label-text font-medium">{$t('lodging.public_lodging')}</span>
									<p class="text-sm text-base-content/60">
										{$t('lodging.public_lodging_description')}
									</p>
								</div>
							</label>
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

						<!-- Description Field -->
						<div class="form-control">
							<label class="label" for="description">
								<span class="label-text font-medium">{$t('adventures.description')}</span>
							</label>
							<MarkdownEditor bind:text={lodging.description} editor_height="h-32" />

							<div class="flex items-center gap-4 mt-3">
								<button
									type="button"
									class="btn btn-neutral btn-sm gap-2"
									on:click={generateDesc}
									disabled={!lodging.name || isGeneratingDesc || !lodging.type}
								>
									{#if isGeneratingDesc}
										<span class="loading loading-spinner loading-xs"></span>
									{:else}
										<GenerateIcon class="w-4 h-4" />
									{/if}
									{$t('adventures.generate_desc')}
								</button>
								{#if wikiError}
									<div class="alert alert-error alert-sm">
										<InfoIcon class="w-4 h-4" />
										<span class="text-sm">{wikiError}</span>
									</div>
								{/if}
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Dates are now handled via Visits -->

		<!-- Tags Section -->
		<TagsCard bind:tags={lodging.tags} />

		<!-- Action Buttons -->
		<DetailsActionButtons
			disabled={!lodging.name || !lodging.type || isReverseGeocoding}
			isProcessing={isReverseGeocoding}
			on:save={handleSave}
		/>
	</div>
</div>
