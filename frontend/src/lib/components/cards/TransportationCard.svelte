<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import TrashCanOutline from '~icons/mdi/trash-can-outline';
	import FileDocumentEdit from '~icons/mdi/file-document-edit';
	import type { Collection, Transportation, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import DeleteWarning from '../DeleteWarning.svelte';
	import { TRANSPORTATION_TYPES_ICONS } from '$lib';
	import { formatAllDayDate, formatDateInTimezone } from '$lib/dateUtils';
	import { isAllDay } from '$lib';
	import { DEFAULT_CURRENCY, formatMoney, toMoneyValue } from '$lib/money';
	import CardCarousel from '../CardCarousel.svelte';
	import TransportationRoutePreview from './TransportationRoutePreview.svelte';
	import StarRating from '../StarRating.svelte';
	import Calendar from '~icons/mdi/calendar';
	import CalendarRemove from '~icons/mdi/calendar-remove';
	import Launch from '~icons/mdi/launch';
	import Globe from '~icons/mdi/globe';
	import { goto } from '$app/navigation';
	import type { CollectionItineraryItem } from '$lib/types';
	import { CardActionsMenu, CardStatusBadge, CardPrivacyBadge } from '../shared/cards';
	import {
		getLocalTimezone,
		getTimezoneLabel,
		getTimezoneTip,
		shouldShowTimezoneBadge
	} from '../shared/detail/detailUtils';

	let actionsMenu: { close: () => void };

	function getTransportationIcon(type: string) {
		if (type in TRANSPORTATION_TYPES_ICONS) {
			return TRANSPORTATION_TYPES_ICONS[type as keyof typeof TRANSPORTATION_TYPES_ICONS];
		} else {
			return '🚗';
		}
	}

	const dispatch = createEventDispatcher();

	// Use shared timezone utilities
	$: timezoneTip = (zone?: string | null) =>
		getTimezoneTip(zone, $t('adventures.trip_timezone') ?? 'Trip TZ', $t('adventures.your_time') ?? 'Your time');

	export let transportation: Transportation;
	export let user: User | null = null;
	export let collection: Collection | null = null;
	export let readOnly: boolean = false;
	export let itineraryItem: CollectionItineraryItem | null = null;

	const toMiles = (km: any) => (Number(km) * 0.621371).toFixed(1);

	const formatTravelDuration = (minutes: number | null | undefined) => {
		if (minutes === null || minutes === undefined || Number.isNaN(minutes)) return null;
		const safeMinutes = Math.max(0, Math.floor(minutes));
		const hours = Math.floor(safeMinutes / 60);
		const mins = safeMinutes % 60;
		const parts = [] as string[];
		if (hours) parts.push(`${hours}h`);
		parts.push(`${mins}m`);
		return parts.join(' ');
	};

	function changeDay() {
		dispatch('changeDay', { type: 'transportation', item: transportation, forcePicker: true });
	}

	let travelDurationLabel: string | null = null;
	$: travelDurationLabel = formatTravelDuration(transportation?.travel_duration_minutes ?? null);

	let showMoreDetails = false;

	$: hasCodePair = Boolean(transportation?.start_code && transportation?.end_code);
	$: routeFromLabel = hasCodePair
		? transportation.start_code
		: (transportation.from_location ?? transportation.start_code ?? null);
	$: routeToLabel = hasCodePair
		? transportation.end_code
		: (transportation.to_location ?? transportation.end_code ?? null);
	// Use first visit's dates for display
	$: firstVisit = transportation?.visits?.[0] ?? null;
	$: visitStartDate = firstVisit?.start_date ?? null;
	$: visitEndDate = firstVisit?.end_date ?? null;
	$: visitTimezone = firstVisit?.timezone ?? null;
	$: hasExpandableDetails = Boolean(visitEndDate || travelDurationLabel);
	$: if (!hasExpandableDetails) showMoreDetails = false;
	$: transportationPriceLabel = formatMoney(
		toMoneyValue(transportation.price, transportation.price_currency, DEFAULT_CURRENCY)
	);

	$: routeGeojson =
		transportation?.attachments?.find((attachment) => attachment?.geojson)?.geojson ?? null;

	let isWarningModalOpen: boolean = false;

	function editTransportation() {
		dispatch('edit', transportation);
	}

	async function deleteTransportation() {
		let res = await fetch(`/api/transportations/${transportation.id}`, {
			method: 'DELETE',
			headers: {
				'Content-Type': 'application/json'
			}
		});
		if (!res.ok) {
			console.log($t('transportation.transportation_delete_error'));
		} else {
			addToast('info', $t('transportation.transportation_deleted'));
			isWarningModalOpen = false;
			dispatch('delete', transportation.id);
		}
	}

	async function removeFromItinerary() {
		let itineraryItemId = itineraryItem?.id;
		let res = await fetch(`/api/itineraries/${itineraryItemId}`, {
			method: 'DELETE'
		});
		if (res.ok) {
			addToast('info', $t('itinerary.item_remove_success'));
			dispatch('removeFromItinerary', itineraryItem);
		} else {
			addToast('error', $t('itinerary.item_remove_error'));
		}
	}
</script>

{#if isWarningModalOpen}
	<DeleteWarning
		title={$t('adventures.delete_transportation')}
		button_text="Delete"
		description={$t('adventures.transportation_delete_confirm')}
		is_warning={false}
		on:close={() => (isWarningModalOpen = false)}
		on:confirm={deleteTransportation}
	/>
{/if}

<div
	class="card w-full max-w-md bg-base-300 shadow hover:shadow-md transition-all duration-200 border border-base-300 group"
	aria-label="transportation-card"
>
	<!-- Image Section with Overlay -->
	<div class="relative overflow-hidden rounded-t-2xl">
		{#if routeGeojson}
			<TransportationRoutePreview
				geojson={routeGeojson}
				name={transportation.name}
				images={transportation.images}
			/>
		{:else}
			<CardCarousel
				images={transportation.images}
				icon={getTransportationIcon(transportation.type)}
				name={transportation.name}
			/>
		{/if}

		<CardStatusBadge isVisited={transportation.is_visited} />
		<CardPrivacyBadge isPublic={transportation.is_public} />

		<!-- Category Badge -->
		{#if transportation.type}
			<div class="absolute bottom-4 left-4">
				<div class="badge badge-primary shadow-lg font-medium">
					{$t(`transportation.modes.${transportation.type}`)}
					{getTransportationIcon(transportation.type)}
				</div>
			</div>
		{/if}
	</div>

	<div class="card-body p-4 space-y-3 min-w-0">
		<!-- Header -->
		<div class="flex items-start justify-between gap-3">
			<a
				href="/transportations/{transportation.id}"
				class="hover:text-primary transition-colors duration-200 line-clamp-2 text-lg font-semibold"
			>
				{transportation.name}
			</a>

			<div class="flex items-center gap-2">
				<button
					class="btn btn-sm p-1 text-base-content"
					aria-label="open-details"
					on:click={() => goto(`/transportations/${transportation.id}`)}
				>
					<Launch class="w-4 h-4" />
				</button>

				{#if !readOnly && (transportation.user === user?.uuid || (collection && user && collection.shared_with?.includes(user.uuid)))}
					<CardActionsMenu bind:this={actionsMenu} ariaLabel={$t('adventures.transportation_actions') || 'Transportation actions'} let:close>
						<li>
							<button
								on:click={() => {
									close();
									editTransportation();
								}}
								class="flex items-center gap-2"
							>
								<FileDocumentEdit class="w-4 h-4" />
								{$t('transportation.edit')}
							</button>
						</li>
						{#if itineraryItem && itineraryItem.id}
							<div class="divider my-1"></div>
							{#if !itineraryItem.is_global}
								<li>
									<button
										on:click={() => {
											close();
											dispatch('moveToGlobal', { type: 'transportation', id: transportation.id });
										}}
										class=" flex items-center gap-2"
									>
										<Globe class="w-4 h-4 " />
										{$t('itinerary.move_to_trip_context') || 'Move to Trip Context'}
									</button>
								</li>
								<li>
									<button
										on:click={() => {
											close();
											changeDay();
										}}
										class=" flex items-center gap-2"
									>
										<Calendar class="w-4 h-4 text" />
										{$t('itinerary.change_day')}
									</button>
								</li>
							{/if}
							<li>
								<button
									on:click={() => {
										close();
										removeFromItinerary();
									}}
									class="text-error flex items-center gap-2"
								>
									<CalendarRemove class="w-4 h-4 text-error" />
									{#if itineraryItem.is_global}
										{$t('itinerary.remove_from_trip_context') || 'Remove from Trip Context'}
									{:else}
										{$t('itinerary.remove_from_itinerary')}
									{/if}
								</button>
							</li>
						{/if}
						<div class="divider my-1"></div>
						<li>
							<button
								class="text-error flex items-center gap-2"
								on:click={() => {
									close();
									isWarningModalOpen = true;
								}}
							>
								<TrashCanOutline class="w-4 h-4" />
								{$t('adventures.delete')}
							</button>
						</li>
					</CardActionsMenu>
				{/if}
			</div>
		</div>

		<!-- Route & Flight Info -->
		{#if routeFromLabel || routeToLabel}
			<div class="flex items-center gap-2 min-w-0">
				{#if routeFromLabel}
					<span class="text-base font-semibold text-base-content truncate max-w-[10rem]"
						>{routeFromLabel}</span
					>
				{/if}
				{#if routeFromLabel && routeToLabel}
					<span class="text-primary text-lg">→</span>
				{/if}
				{#if routeToLabel}
					<span class="text-base font-semibold text-base-content truncate max-w-[10rem]"
						>{routeToLabel}</span
					>
				{/if}
				{#if hasCodePair && transportation.type === 'plane' && transportation.flight_number}
					<div class="divider divider-horizontal mx-1"></div>
					<span class="badge badge-primary badge-sm font-medium"
						>{transportation.flight_number}</span
					>
				{/if}
			</div>
		{/if}

		<!-- Date & Time Section (from first visit) -->
		{#if visitStartDate}
			<div class="flex flex-col gap-1.5">
				{#if isAllDay(visitStartDate) && (!visitEndDate || isAllDay(visitEndDate))}
					<!-- All-day event -->
					<div class="flex items-center gap-2 text-sm">
						<span class="font-medium text-base-content"
							>{formatAllDayDate(visitStartDate)}</span
						>
						{#if visitEndDate && visitEndDate !== visitStartDate}
							<span class="text-base-content/40">→</span>
							<span class="font-medium text-base-content"
								>{formatAllDayDate(visitEndDate)}</span
							>
						{/if}
					</div>
				{:else}
					<!-- Compact departure card with tidy layout -->
					<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
						<div class="flex items-start justify-between gap-2">
							<div class="flex flex-col gap-0.5 min-w-0">
								<span class="text-xs text-base-content/60">Departure</span>
								<span class="text-sm font-semibold text-base-content">
									{formatDateInTimezone(visitStartDate, visitTimezone)}
								</span>
							</div>
							{#if hasCodePair}
								<span class="badge badge-outline badge-sm font-medium whitespace-nowrap">
									{transportation.start_code} → {transportation.end_code}
								</span>
							{/if}
						</div>

						<div class="flex items-center gap-2 text-xs text-base-content/70">
							<div
								class="tooltip"
								data-tip={timezoneTip(visitTimezone) ?? undefined}
							>
								<span class="badge badge-ghost badge-sm">
									{getTimezoneLabel(visitTimezone)}
								</span>
							</div>
						</div>
					</div>

					{#if hasExpandableDetails}
						<div class="flex justify-end">
							<button
								class="btn btn-neutral-200 btn-xs"
								aria-expanded={showMoreDetails}
								on:click={() => (showMoreDetails = !showMoreDetails)}
								type="button"
							>
								{showMoreDetails
									? ($t('common.show_less') ?? 'Hide details')
									: ($t('common.show_more') ?? 'Show more')}
							</button>
						</div>
					{/if}

					{#if showMoreDetails && hasExpandableDetails}
						<div class="flex flex-col gap-1">
							{#if visitEndDate}
								<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
									<div class="flex items-center justify-between gap-2">
										<div class="flex flex-col gap-0.5 min-w-0">
											<span class="text-xs text-base-content/60">Arrival</span>
											<span class="text-sm font-semibold text-base-content">
												{formatDateInTimezone(
													visitEndDate,
													visitTimezone
												)}
											</span>
										</div>
									</div>

									<div class="flex items-center gap-2 text-xs text-base-content/70">
										<div
											class="tooltip"
											data-tip={timezoneTip(visitTimezone) ?? undefined}
										>
											<span class="badge badge-ghost badge-sm">
												{getTimezoneLabel(visitTimezone)}
											</span>
										</div>
									</div>
								</div>
							{/if}
						</div>
					{/if}
				{/if}
			</div>
		{/if}

		<!-- Stats & Rating -->
		<div class="flex flex-wrap items-center gap-2 text-sm">
			{#if transportationPriceLabel}
				<span class="badge badge-ghost badge-sm">💰 {transportationPriceLabel}</span>
			{/if}
			{#if transportation.distance && !isNaN(+transportation.distance)}
				<span class="badge badge-ghost badge-sm">
					🌍 {user?.measurement_system === 'imperial'
						? `${toMiles(transportation.distance)} mi`
						: `${(+transportation.distance).toFixed(1)} km`}
				</span>
			{/if}

			{#if travelDurationLabel}
				<span class="badge badge-ghost badge-sm">⏱️ {travelDurationLabel}</span>
			{/if}

			{#if transportation.average_rating !== null && transportation.average_rating !== undefined}
				<div class="flex items-center gap-1">
					<StarRating rating={transportation.average_rating} size="sm" readonly />
					<span class="text-xs text-base-content/60">({transportation.average_rating})</span>
				</div>
			{:else if transportation.rating}
				<div class="flex items-center gap-1">
					<StarRating rating={transportation.rating} size="sm" readonly />
					<span class="text-xs text-base-content/60">({transportation.rating}/5)</span>
				</div>
			{/if}
		</div>
	</div>
</div>

<style>
	.line-clamp-2 {
		display: -webkit-box;
		-webkit-line-clamp: 2;
		line-clamp: 2;
		-webkit-box-orient: vertical;
		overflow: hidden;
	}
</style>
