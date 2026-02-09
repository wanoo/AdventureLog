<script lang="ts">
	import type { Collection, Visit } from '$lib/types';
	import TimezoneSelector from '../TimezoneSelector.svelte';
	import { t } from 'svelte-i18n';
	import { updateLocalDate, updateUTCDate, validateDateRange } from '$lib/dateUtils';
	import { onMount } from 'svelte';
	import { isAllDay } from '$lib';
	import { createEventDispatcher } from 'svelte';

	// Icons
	import CalendarIcon from '~icons/mdi/calendar';
	import ClockIcon from '~icons/mdi/clock';
	import PlusIcon from '~icons/mdi/plus';
	import EditIcon from '~icons/mdi/pencil';
	import TrashIcon from '~icons/mdi/delete';
	import AlertIcon from '~icons/mdi/alert';
	import CheckIcon from '~icons/mdi/check';
	import SettingsIcon from '~icons/mdi/cog';
	import ArrowLeftIcon from '~icons/mdi/arrow-left';
	import InfoIcon from '~icons/mdi/information';
	import StarRating from '../StarRating.svelte';

	// Props
	export let collection: Collection | null = null;
	export let selectedStartTimezone: string = Intl.DateTimeFormat().resolvedOptions().timeZone;
	export let utcStartDate: string | null = null;
	export let utcEndDate: string | null = null;
	export let note: string | null = null;
	export let visitRating: number | null = null;
	export let visits: Visit[] | null = null;
	export let transportationId: string;
	export let initialVisitDate: string | null = null;
	export let currentUserUsername: string | null = null;

	const dispatch = createEventDispatcher();

	// Component state
	let allDay: boolean = false;
	let localStartDate: string = '';
	let localEndDate: string = '';
	let fullStartDate: string = '';
	let fullEndDate: string = '';
	let constrainDates: boolean = false;
	let isEditing = false;
	let visitIdEditing: string | null = null;

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

	// Set the full date range for constraining purposes
	$: if (collection && collection.start_date && collection.end_date) {
		fullStartDate = `${collection.start_date}T00:00`;
		fullEndDate = `${collection.end_date}T23:59`;
	}

	// Update local display dates whenever timezone or UTC dates change
	$: if (!isEditing) {
		if (allDay) {
			localStartDate = utcStartDate?.substring(0, 10) ?? '';
			localEndDate = utcEndDate?.substring(0, 10) ?? '';
		} else {
			const start = updateLocalDate({
				utcDate: utcStartDate,
				timezone: selectedStartTimezone
			}).localDate;

			const end = updateLocalDate({
				utcDate: utcEndDate,
				timezone: selectedStartTimezone
			}).localDate;

			localStartDate = start;
			localEndDate = end;
		}
	}

	// Helper functions
	function formatDateInTimezone(utcDate: string, timezone: string): string {
		try {
			return new Intl.DateTimeFormat(undefined, {
				timeZone: timezone,
				year: 'numeric',
				month: 'short',
				day: 'numeric',
				hour: '2-digit',
				minute: '2-digit',
				hour12: true
			}).format(new Date(utcDate));
		} catch {
			return new Date(utcDate).toLocaleString();
		}
	}

	// Event handlers
	function handleLocalDateChange() {
		utcStartDate = updateUTCDate({
			localDate: localStartDate,
			timezone: selectedStartTimezone,
			allDay
		}).utcDate;

		utcEndDate = updateUTCDate({
			localDate: localEndDate,
			timezone: selectedStartTimezone,
			allDay
		}).utcDate;
	}

	function handleAllDayToggle() {
		if (allDay) {
			localStartDate = localStartDate ? localStartDate.split('T')[0] : '';
			localEndDate = localEndDate ? localEndDate.split('T')[0] : '';
		} else {
			localStartDate = localStartDate + 'T00:00';
			localEndDate = localEndDate + 'T23:59';
		}

		utcStartDate = updateUTCDate({
			localDate: localStartDate,
			timezone: selectedStartTimezone,
			allDay
		}).utcDate;

		utcEndDate = updateUTCDate({
			localDate: localEndDate,
			timezone: selectedStartTimezone,
			allDay
		}).utcDate;

		localStartDate = updateLocalDate({
			utcDate: utcStartDate,
			timezone: selectedStartTimezone
		}).localDate;

		localEndDate = updateLocalDate({
			utcDate: utcEndDate,
			timezone: selectedStartTimezone
		}).localDate;
	}

	async function addVisit(isAuto: boolean = false) {
		// If editing an existing visit, patch instead of creating new
		if (visitIdEditing) {
			const response = await fetch(`/api/visits/${visitIdEditing}/`, {
				method: 'PATCH',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					start_date: utcStartDate,
					end_date: utcEndDate,
					notes: note,
					rating: visitRating,
					timezone: selectedStartTimezone
				})
			});

			if (response.ok) {
				const updatedVisit: Visit = await response.json();
				// Filter out any existing visit with same ID before adding updated one
				visits = visits ? [...visits.filter(v => v.id !== updatedVisit.id), updatedVisit] : [updatedVisit];
				dispatch('visitAdded', updatedVisit);
				visitIdEditing = null;
			} else {
				console.error('Failed to update visit');
			}
		} else {
			// post to /api/visits for new visit
			const payload = {
				start_date: utcStartDate,
				end_date: utcEndDate,
				notes: note,
				rating: visitRating,
				timezone: selectedStartTimezone,
				transportation: transportationId
			};

			const response = await fetch('/api/visits/', {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify(payload)
			});

			if (response.ok) {
				const newVisit: Visit = await response.json();
				visits = visits ? [...visits, newVisit] : [newVisit];
				dispatch('visitAdded', newVisit);
			} else {
				const errorText = await response.text();
				console.error('Failed to create visit:', errorText);
				alert(`Failed to add visit: ${errorText}`);
			}
		}

		// Reset form fields
		if (!initialVisitDate || isAuto) {
			note = '';
			visitRating = null;
			localStartDate = '';
			localEndDate = '';
			utcStartDate = null;
			utcEndDate = null;
		}
	}

	function editVisit(visit: Visit) {
		isEditing = true;
		visitIdEditing = visit.id;
		const isAllDayEvent = isAllDay(visit.start_date);
		allDay = isAllDayEvent;

		if (visit.timezone) {
			selectedStartTimezone = visit.timezone;
		}

		if (isAllDayEvent) {
			localStartDate = visit.start_date.split('T')[0];
			localEndDate = visit.end_date.split('T')[0];
		} else {
			localStartDate = updateLocalDate({
				utcDate: visit.start_date,
				timezone: selectedStartTimezone
			}).localDate;

			localEndDate = updateLocalDate({
				utcDate: visit.end_date,
				timezone: selectedStartTimezone
			}).localDate;
		}

		// Remove the visit from the array temporarily for editing
		if (visits) {
			visits = visits.filter((v) => v.id !== visit.id);
		}

		note = visit.notes;
		visitRating = visit.rating ?? null;
		constrainDates = true;
		utcStartDate = visit.start_date;
		utcEndDate = visit.end_date;

		setTimeout(() => {
			isEditing = false;
		}, 0);
	}

	function removeVisit(visitId: string) {
		// make the DELETE request
		fetch(`/api/visits/${visitId}/`, {
			method: 'DELETE'
		}).then((response) => {
			if (!response.ok) {
				console.error('Error deleting visit:', response.statusText);
			} else {
				// Remove from local array
				if (visits) {
					visits = visits.filter((v) => v.id !== visitId);
				}
				// Notify parent to update its array
				dispatch('visitDeleted', visitId);
			}
		});
	}

	function handleBack() {
		dispatch('back');
	}

	function handleClose() {
		dispatch('close');
	}

	// Lifecycle
	onMount(async () => {
		localStartDate = updateLocalDate({
			utcDate: utcStartDate,
			timezone: selectedStartTimezone
		}).localDate;

		localEndDate = updateLocalDate({
			utcDate: utcEndDate,
			timezone: selectedStartTimezone
		}).localDate;

		if (!selectedStartTimezone) {
			selectedStartTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
		}

		// If initialVisitDate is provided and a visit on that date doesn't exist, create and upload a new all day visit
		if (initialVisitDate) {
			const targetDate = initialVisitDate.split('T')[0];

			const visitExists = visits?.some((visit) => {
				const visitStart = visit.start_date.split('T')[0];
				const visitEnd = visit.end_date.split('T')[0];
				return targetDate >= visitStart && targetDate <= visitEnd;
			});

			if (!visitExists) {
				allDay = true;
				localStartDate = targetDate;
				localEndDate = targetDate;

				utcStartDate = updateUTCDate({
					localDate: localStartDate,
					timezone: selectedStartTimezone,
					allDay: true
				}).utcDate;

				utcEndDate = updateUTCDate({
					localDate: localEndDate,
					timezone: selectedStartTimezone,
					allDay: true
				}).utcDate;

				await addVisit(true);
				initialVisitDate = null;
			}
		}
	});

	$: isDateValid = validateDateRange(utcStartDate ?? '', utcEndDate ?? '').valid;
</script>

<div class="min-h-screen bg-gradient-to-br from-base-200/30 via-base-100 to-primary/5 p-6">
	<div class="max-w-full mx-auto space-y-6">
		<div class="card bg-base-100 border border-base-300 shadow-lg">
			<div class="card-body p-6">
				<!-- Header -->
				<div class="flex items-center justify-between mb-6">
					<div class="flex items-center gap-3">
						<div class="p-2 bg-primary/10 rounded-lg">
							<CalendarIcon class="w-5 h-5 text-primary" />
						</div>
						<h2 class="text-xl font-bold">{$t('adventures.date_information')}</h2>
					</div>
				</div>

				<!-- Settings Section -->
				<div class="bg-base-50 p-4 rounded-lg border border-base-200 mb-6">
					<div class="flex items-center gap-2 mb-4">
						<SettingsIcon class="w-4 h-4 text-base-content/70" />
						<h3 class="font-medium text-base-content/80">{$t('navbar.settings')}</h3>
					</div>

					<div class="space-y-4">
						<!-- Timezone Selection -->
						<div>
							<label class="label-text text-sm font-medium" for="timezone-selector"
								>{$t('adventures.timezone')}</label
							>
							<div class="mt-1">
								<TimezoneSelector bind:selectedTimezone={selectedStartTimezone} />
							</div>
						</div>

						<!-- Toggles -->
						<div class="flex flex-wrap gap-6">
							<div class="flex items-center gap-3">
								<ClockIcon class="w-4 h-4 text-base-content/70" />
								<label class="label-text text-sm font-medium" for="all-day-toggle"
									>{$t('adventures.all_day')}</label
								>
								<input
									id="all-day-toggle"
									type="checkbox"
									class="toggle toggle-primary toggle-sm"
									bind:checked={allDay}
									on:change={handleAllDayToggle}
								/>
							</div>

							{#if collection?.start_date && collection?.end_date}
								<div class="flex items-center gap-3">
									<CalendarIcon class="w-4 h-4 text-base-content/70" />
									<label class="label-text text-sm font-medium" for="constrain-dates"
										>{$t('adventures.date_constrain')}</label
									>
									<input
										id="constrain-dates"
										type="checkbox"
										class="toggle toggle-primary toggle-sm"
										bind:checked={constrainDates}
									/>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Date Selection Section -->
				<div class="bg-base-50 p-4 rounded-lg border border-base-200 mb-6">
					<h3 class="font-medium text-base-content/80 mb-4">{$t('adventures.date_selection')}</h3>

					<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
						<!-- Start Date -->
						<div>
							<label class="label-text text-sm font-medium" for="start-date-input">
								{$t('adventures.start_date')}
							</label>
							{#if allDay}
								<input
									id="start-date-input"
									type="date"
									class="input input-bordered w-full mt-1"
									bind:value={localStartDate}
									on:change={handleLocalDateChange}
									min={constrainDates ? constraintStartDate : ''}
									max={constrainDates ? constraintEndDate : ''}
								/>
							{:else}
								<input
									id="start-date-input"
									type="datetime-local"
									class="input input-bordered w-full mt-1"
									bind:value={localStartDate}
									on:change={handleLocalDateChange}
									min={constrainDates ? constraintStartDate : ''}
									max={constrainDates ? constraintEndDate : ''}
								/>
							{/if}
						</div>

						<!-- End Date -->
						{#if localStartDate}
							<div>
								<label class="label-text text-sm font-medium" for="end-date-input">
									{$t('adventures.end_date')}
								</label>
								{#if allDay}
									<input
										id="end-date-input"
										type="date"
										class="input input-bordered w-full mt-1"
										bind:value={localEndDate}
										on:change={handleLocalDateChange}
										min={constrainDates ? localStartDate : ''}
										max={constrainDates ? constraintEndDate : ''}
									/>
								{:else}
									<input
										id="end-date-input"
										type="datetime-local"
										class="input input-bordered w-full mt-1"
										bind:value={localEndDate}
										on:change={handleLocalDateChange}
										min={constrainDates ? localStartDate : ''}
										max={constrainDates ? constraintEndDate : ''}
									/>
								{/if}
							</div>
						{/if}
					</div>

					<!-- Notes -->
					<div class="mt-4">
						<label class="label-text text-sm font-medium" for="visit-notes"
							>{$t('adventures.notes')}</label
						>
						<textarea
							id="visit-notes"
							class="textarea textarea-bordered w-full mt-1"
							rows="3"
							placeholder={$t('adventures.notes_placeholder') + '...'}
							bind:value={note}
						></textarea>
					</div>

					<!-- Rating -->
					<div class="mt-4">
						<label class="label-text text-sm font-medium">{$t('adventures.rating')}</label>
						<div class="flex items-center gap-2 mt-1">
							<StarRating rating={visitRating} size="lg" readonly={false} on:change={(e) => visitRating = e.detail} />
							{#if visitRating}
								<button
									type="button"
									class="btn btn-ghost btn-xs"
									on:click={() => visitRating = null}
								>
									{$t('adventures.clear')}
								</button>
							{/if}
						</div>
					</div>

					<!-- Add Visit Button -->
					<div class="flex justify-end mt-4">
						<button
							class="btn btn-primary btn-sm gap-2"
							type="button"
							disabled={!localStartDate || !isDateValid}
							on:click={() => addVisit(false)}
						>
							<PlusIcon class="w-4 h-4" />
							{visitIdEditing ? $t('adventures.update_visit') : $t('adventures.add_visit')}
						</button>
					</div>
				</div>

				<!-- Validation Error -->
				{#if !isDateValid}
					<div class="alert alert-error mb-6">
						<AlertIcon class="w-5 h-5" />
						<span class="text-sm">{$t('adventures.invalid_date_range')}</span>
					</div>
				{/if}

				<!-- Visits List -->
				<div class="bg-base-50 p-4 rounded-lg border border-base-200">
					<h3 class="font-medium text-base-content/80 mb-4">
						{$t('adventures.visits')} ({visits?.length || 0})
					</h3>

					{#if !visits || visits.length === 0}
						<div class="text-center py-8 text-base-content/60">
							<CalendarIcon class="w-8 h-8 mx-auto mb-2 opacity-50" />
							<p class="text-sm">{$t('adventures.no_visits')}</p>
							<p class="text-xs text-base-content/40 mt-1">
								{$t('adventures.no_visits_description')}
							</p>
						</div>
					{:else}
						<div class="space-y-3">
							{#each visits as visit (visit.id)}
								<div
									class="bg-base-100 p-4 rounded-lg border border-base-300 hover:border-base-400 transition-colors"
								>
									<div class="flex items-start justify-between">
										<div class="flex-1 min-w-0">
											{#if visit.user_username}
												<div class="text-xs opacity-60 mb-2">
													{$t('adventures.added_by')}
													<a
														href="/profile/{visit.user_username}"
														class="font-semibold link link-hover link-primary"
														>{visit.user_username}</a
													>
												</div>
											{/if}
											<div class="flex items-center gap-2 mb-2">
												{#if isAllDay(visit.start_date)}
													<span class="badge badge-outline badge-sm"
														>{$t('adventures.all_day')}</span
													>
												{:else}
													<ClockIcon class="w-3 h-3 text-base-content/50" />
												{/if}
												{#if visit.timezone && !isAllDay(visit.start_date)}
													<span class="badge badge-outline badge-sm">{visit.timezone}</span>
												{/if}
												<div class="text-sm font-medium truncate">
													{#if isAllDay(visit.start_date)}
														{visit.start_date && typeof visit.start_date === 'string'
															? visit.start_date.split('T')[0]
															: ''}
														- {visit.end_date && typeof visit.end_date === 'string'
															? visit.end_date.split('T')[0]
															: ''}
													{:else if visit.timezone}
														{formatDateInTimezone(visit.start_date, visit.timezone)}
														- {formatDateInTimezone(visit.end_date, visit.timezone)}
													{:else}
														{new Date(visit.start_date).toLocaleString()}
														- {new Date(visit.end_date).toLocaleString()}
													{/if}
												</div>
											</div>

											{#if visit.notes}
												<p class="text-xs text-base-content/70 bg-base-200/50 p-2 rounded">
													"{visit.notes}"
												</p>
											{/if}
											{#if visit.rating !== null && visit.rating !== undefined}
												<div class="mt-2">
													<StarRating rating={visit.rating} size="sm" readonly />
												</div>
											{/if}
										</div>

										<!-- Visit Actions -->
										<div class="flex gap-1 ml-4">
											<!-- Only show edit/delete buttons if user owns this visit -->
											{#if !visit.user_username || visit.user_username === currentUserUsername}
												<button
													class="btn btn-warning btn-xs tooltip tooltip-top"
													data-tip={$t('adventures.edit_visit')}
													on:click={() => editVisit(visit)}
												>
													<EditIcon class="w-3 h-3" />
												</button>
												<button
													class="btn btn-error btn-xs tooltip tooltip-top"
													data-tip={$t('adventures.remove_visit')}
													on:click={() => removeVisit(visit.id)}
												>
													<TrashIcon class="w-3 h-3" />
												</button>
											{/if}
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>

		<!-- Dates not saved warning -->
		{#if localStartDate || localEndDate}
			<div class="alert alert-neutral">
				<InfoIcon class="w-5 h-5" />
				<div>
					<div class="font-medium text-sm">{$t('adventures.dates_not_saved')}</div>
					<div class="text-xs opacity-75">{$t('adventures.dates_not_saved_description')}</div>
				</div>
			</div>
		{/if}

		<div class="flex gap-3 justify-end pt-4">
			<button class="btn btn-neutral-200 gap-2" on:click={handleBack}>
				<ArrowLeftIcon class="w-5 h-5" />
				{$t('adventures.back')}
			</button>

			<button class="btn btn-primary gap-2" on:click={handleClose}>
				<CheckIcon class="w-5 h-5" />
				{$t('adventures.done')}
			</button>
		</div>
	</div>
</div>
