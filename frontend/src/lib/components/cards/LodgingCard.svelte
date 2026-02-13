<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import TrashCanOutline from '~icons/mdi/trash-can-outline';
	import FileDocumentEdit from '~icons/mdi/file-document-edit';
	import LinkVariantRemove from '~icons/mdi/link-variant-remove';
	import type { Collection, Lodging, User } from '$lib/types';
	import { addToast } from '$lib/toasts';
	import { t } from 'svelte-i18n';
	import DeleteWarning from '../DeleteWarning.svelte';
	import { LODGING_TYPES_ICONS } from '$lib';
	import { formatDateInTimezone } from '$lib/dateUtils';
	import { formatAllDayDate } from '$lib/dateUtils';
	import { isAllDay } from '$lib';
	import CardCarousel from '../CardCarousel.svelte';
	import MapMarker from '~icons/mdi/map-marker';
	import CalendarRemove from '~icons/mdi/calendar-remove';
	import Launch from '~icons/mdi/launch';
	import Globe from '~icons/mdi/globe';
	import { goto } from '$app/navigation';
	import Calendar from '~icons/mdi/calendar';
	import type { CollectionItineraryItem } from '$lib/types';
	import { CardActionsMenu, CardStatusBadge, CardPrivacyBadge, RatingDisplay, PriceBadge, VisitCountBadge, TagsDisplay, getVisitSummary } from '../shared/cards';
	import {
		getTimezoneLabel,
		getTimezoneTip,
		shouldShowTimezoneBadge
	} from '../shared/detail/detailUtils';
	import { getLodgingIcon as getLodgingIconFromStore } from '$lib/stores/entityTypes';

	let actionsMenu: { close: () => void };

	const dispatch = createEventDispatcher();

	function getLodgingIcon(type: string) {
		// First try to get from the store (admin-managed types)
		const storeIcon = getLodgingIconFromStore(type);
		if (storeIcon !== '🏨') {
			return storeIcon;
		}
		// Fallback to hardcoded icons
		if (type in LODGING_TYPES_ICONS) {
			return LODGING_TYPES_ICONS[type as keyof typeof LODGING_TYPES_ICONS];
		}
		return '🏨';
	}

	// Use shared timezone utilities
	$: timezoneTip = (zone?: string | null) =>
		getTimezoneTip(zone, $t('adventures.trip_timezone') ?? 'Trip TZ', $t('adventures.your_time') ?? 'Your time');

	const hasTimePortion = (date: string | null) => !!date && !isAllDay(date);
	const isTimedStay = (date: string | null) => hasTimePortion(date);

	let showMoreDetails = false;
	// Use LAST visit's dates for display (sorted by start_date desc)
	$: visitSummary = getVisitSummary(lodging?.visits);
	$: lastVisit = visitSummary.lastVisit;
	$: visitCount = visitSummary.visitCount;
	$: visitStartDate = lastVisit?.start_date ?? null;
	$: visitEndDate = lastVisit?.end_date ?? null;
	$: visitTimezone = lastVisit?.timezone ?? null;
	$: hasExpandableDetails = Boolean(
		visitEndDate && (isTimedStay(visitEndDate) || isTimedStay(visitStartDate))
	);
	$: if (!hasExpandableDetails) showMoreDetails = false;

	export let lodging: Lodging;
	export let user: User | null = null;
	export let collection: Collection | null = null;
	export let readOnly: boolean = false;
	export let itineraryItem: CollectionItineraryItem | null = null;

	let isWarningModalOpen: boolean = false;

	function editTransportation() {
		dispatch('edit', lodging);
	}

	async function deleteTransportation() {
		let res = await fetch(`/api/lodging/${lodging.id}`, {
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
			dispatch('delete', lodging.id);
		}
	}

	function changeDay() {
		dispatch('changeDay', { type: 'lodging', item: lodging, forcePicker: true });
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

	async function removeFromCollection() {
		if (!collection) return;

		// Remove the collection from the lodging's collections array
		const updatedCollections = (lodging.collections || []).filter(
			(c) => String(c) !== String(collection.id)
		);

		let res = await fetch(`/api/lodging/${lodging.id}/`, {
			method: 'PATCH',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ collections: updatedCollections })
		});

		if (res.ok) {
			lodging.collections = updatedCollections;
			addToast('info', $t('adventures.collection_remove_success') || 'Removed from collection');
			dispatch('delete', lodging.id); // This triggers UI update to remove from list
		} else {
			addToast('error', $t('adventures.collection_remove_error') || 'Error removing from collection');
		}
	}
</script>

{#if isWarningModalOpen}
	<DeleteWarning
		title={$t('adventures.delete_lodging')}
		button_text="Delete"
		description={$t('adventures.lodging_delete_confirm')}
		is_warning={false}
		on:close={() => (isWarningModalOpen = false)}
		on:confirm={deleteTransportation}
	/>
{/if}

<div
	class="card w-full max-w-md bg-base-300 shadow hover:shadow-md transition-all duration-200 border border-base-300 group"
	aria-label="lodging-card"
>
	<!-- Image Section with Overlay -->
	<div class="relative overflow-hidden rounded-t-2xl">
		<CardCarousel images={lodging.images} icon={getLodgingIcon(lodging.type)} name={lodging.name} />

		<CardStatusBadge isVisited={lodging.is_visited} />
		<CardPrivacyBadge isPublic={lodging.is_public} />

		<!-- Category Badge -->
		{#if lodging.type}
			<div class="absolute bottom-4 left-4">
				<div class="badge badge-primary shadow-lg font-medium">
					{$t(`lodging.${lodging.type}`)}
					{getLodgingIcon(lodging.type)}
				</div>
			</div>
		{/if}
	</div>
	<div class="card-body p-4 space-y-3 min-w-0">
		<!-- Header -->
		<div class="flex items-start justify-between gap-3">
			<a
				href="/lodging/{lodging.id}"
				class="hover:text-primary transition-colors duration-200 line-clamp-2 text-lg font-semibold"
			>
				{lodging.name}
			</a>

			<div class="flex items-center gap-2">
				<button
					class="btn btn-sm p-1 text-base-content"
					aria-label="open-details"
					on:click={() => goto(`/lodging/${lodging.id}`)}
				>
					<Launch class="w-4 h-4" />
				</button>

				{#if !readOnly && (lodging.user == user?.uuid || (collection && user && collection.shared_with?.includes(user.uuid)))}
					<CardActionsMenu bind:this={actionsMenu} ariaLabel={$t('adventures.lodging_actions') || 'Lodging actions'} let:close>
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
											dispatch('moveToGlobal', { type: 'lodging', id: lodging.id });
										}}
										class="flex items-center gap-2"
									>
										<Globe class="w-4 h-4" />
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
						{#if collection}
							<!-- Show "Remove from collection" when in collection context -->
							<li>
								<button
									class="flex items-center gap-2"
									on:click={() => {
										close();
										removeFromCollection();
									}}
								>
									<LinkVariantRemove class="w-4 h-4" />
									{$t('adventures.remove_from_collection')}
								</button>
							</li>
						{/if}
						{#if lodging.user === user?.uuid}
							<!-- Owner can delete -->
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
						{/if}
					</CardActionsMenu>
				{/if}
			</div>
		</div>

		<!-- Location -->
		{#if lodging.location}
			<div class="flex items-center gap-2 text-sm text-base-content/70 min-w-0">
				<MapMarker class="w-4 h-4 text-primary flex-shrink-0" />
				<span class="truncate">{lodging.location}</span>
			</div>
		{/if}

		<!-- Check-in & Check-out Section (from last visit) -->
		{#if visitStartDate || visitEndDate}
			<div class="flex flex-col gap-1.5">
				{#if visitCount > 1}
					<span class="text-xs text-base-content/60 font-medium">{$t('adventures.last_stay')}</span>
				{/if}
				{#if visitStartDate && visitEndDate}
					<!-- Both dates present -->
					{#if isAllDay(visitStartDate) && isAllDay(visitEndDate)}
						<!-- All-day dates -->
						<div class="flex items-center gap-2 text-sm">
							<span class="font-medium text-base-content">{formatAllDayDate(visitStartDate)}</span
							>
							<span class="text-primary">→</span>
							<span class="font-medium text-base-content"
								>{formatAllDayDate(visitEndDate)}</span
							>
						</div>
					{:else}
						<!-- Timed dates with tidy mini cards and toggle -->
						<div class="flex flex-col gap-2">
							<!-- Check-in Card (always shown) -->
							<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
								<div class="flex items-start justify-between gap-2">
									<div class="flex flex-col gap-0.5 min-w-0">
										<span class="text-xs text-base-content/60">{$t('adventures.check_in')}</span>
										<span class="text-sm font-semibold text-base-content">
											{#if isAllDay(visitStartDate)}
												{formatAllDayDate(visitStartDate)}
											{:else}
												{formatDateInTimezone(visitStartDate, visitTimezone)}
											{/if}
										</span>
									</div>
								</div>

								{#if hasTimePortion(visitStartDate) && shouldShowTimezoneBadge(visitTimezone)}
									<div class="flex items-center gap-2 text-xs text-base-content/70">
										<div class="tooltip" data-tip={timezoneTip(visitTimezone) ?? undefined}>
											<span class="badge badge-ghost badge-sm">
												{getTimezoneLabel(visitTimezone)}
											</span>
										</div>
									</div>
								{/if}
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
								<!-- Check-out Card (expandable) -->
								<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
									<div class="flex items-start justify-between gap-2">
										<div class="flex flex-col gap-0.5 min-w-0">
											<span class="text-xs text-base-content/60">{$t('adventures.check_out')}</span>
											<span class="text-sm font-semibold text-base-content">
												{#if isAllDay(visitEndDate)}
													{formatAllDayDate(visitEndDate)}
												{:else}
													{formatDateInTimezone(visitEndDate, visitTimezone)}
												{/if}
											</span>
										</div>
									</div>

									{#if hasTimePortion(visitEndDate) && shouldShowTimezoneBadge(visitTimezone)}
										<div class="flex items-center gap-2 text-xs text-base-content/70">
											<div class="tooltip" data-tip={timezoneTip(visitTimezone) ?? undefined}>
												<span class="badge badge-ghost badge-sm">
													{getTimezoneLabel(visitTimezone)}
												</span>
											</div>
										</div>
									{/if}
								</div>
							{/if}
						</div>
					{/if}
				{:else if visitStartDate}
					<!-- Check-in only -->
					<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
						<div class="flex items-start justify-between gap-2">
							<div class="flex flex-col gap-0.5">
								<span class="text-xs text-base-content/60">{$t('adventures.check_in')}</span>
								<span class="text-sm font-semibold text-base-content">
									{#if isAllDay(visitStartDate)}
										{formatAllDayDate(visitStartDate)}
									{:else}
										{formatDateInTimezone(visitStartDate, visitTimezone)}
									{/if}
								</span>
							</div>
						</div>

						{#if hasTimePortion(visitStartDate) && shouldShowTimezoneBadge(visitTimezone)}
							<div class="flex items-center gap-2 text-xs text-base-content/70">
								<div class="tooltip" data-tip={timezoneTip(visitTimezone) ?? undefined}>
									<span class="badge badge-ghost badge-sm">
										{getTimezoneLabel(visitTimezone)}
									</span>
								</div>
							</div>
						{/if}
					</div>
				{:else if visitEndDate}
					<!-- Check-out only -->
					<div class="bg-base-200 rounded-lg px-3 py-2 flex flex-col gap-2">
						<div class="flex items-start justify-between gap-2">
							<div class="flex flex-col gap-0.5">
								<span class="text-xs text-base-content/60">{$t('adventures.check_out')}</span>
								<span class="text-sm font-semibold text-base-content">
									{#if isAllDay(visitEndDate)}
										{formatAllDayDate(visitEndDate)}
									{:else}
										{formatDateInTimezone(visitEndDate, visitTimezone)}
									{/if}
								</span>
							</div>
						</div>

						{#if hasTimePortion(visitEndDate) && shouldShowTimezoneBadge(visitTimezone)}
							<div class="flex items-center gap-2 text-xs text-base-content/70">
								<div class="tooltip" data-tip={timezoneTip(visitTimezone) ?? undefined}>
									<span class="badge badge-ghost badge-sm">
										{getTimezoneLabel(visitTimezone)}
									</span>
								</div>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		{/if}

		<!-- Rating & Info Badges -->
		<div class="flex flex-wrap items-center gap-2 text-sm">
			<RatingDisplay
				averageRating={lodging.average_rating}
				fallbackRating={lodging.rating}
			/>

			<VisitCountBadge {visitCount} />

			{#if lodging.user == user?.uuid || (collection && user && collection.shared_with?.includes(user.uuid))}
				{#if lodging.reservation_number}
					<span class="badge badge-primary badge-sm font-medium">
						{$t('adventures.reservation')}: {lodging.reservation_number}
					</span>
				{/if}
				<PriceBadge price={lodging.price} currency={lodging.price_currency} />
			{/if}
		</div>

		<!-- Tags -->
		<TagsDisplay tags={lodging.tags} />
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
