<script lang="ts">
	import { t } from 'svelte-i18n';
	// @ts-ignore
	import { DateTime } from 'luxon';
	import { isAllDay } from '$lib';
	import StarRating from '$lib/components/StarRating.svelte';
	import ActivityCard from '$lib/components/cards/ActivityCard.svelte';

	export let visits: any[] = [];
	export let title: string = $t('adventures.visits') || 'Visits';
	export let icon: string = '🎯';
	export let measurementSystem: 'metric' | 'imperial' = 'metric';
	export let trails: any[] = [];
	export let showActivities: boolean = true;
</script>

{#if visits && visits.length > 0}
	<div class="card bg-base-200 shadow-xl">
		<div class="card-body">
			<h2 class="card-title text-2xl mb-6">{icon} {title}</h2>
			<div class="space-y-4">
				{#each visits as visit, index}
					<div class="flex gap-4">
						<div class="flex flex-col items-center">
							<div class="w-4 h-4 bg-primary rounded-full"></div>
							{#if index < visits.length - 1}
								<div class="w-0.5 bg-primary/30 h-full min-h-12"></div>
							{/if}
						</div>
						<div class="flex-1 pb-4">
							<div class="card bg-base-100 shadow">
								<div class="card-body p-4">
									{#if visit.user_username}
										<div class="flex items-center justify-between mb-2">
											<div class="text-xs opacity-60">
												{$t('adventures.added_by')} <a href="/profile/{visit.user_username}" class="font-semibold link link-hover link-primary">{visit.user_username}</a>
											</div>
											{#if visit.rating !== null && visit.rating !== undefined}
												<StarRating rating={visit.rating} size="sm" readonly />
											{/if}
										</div>
									{:else if visit.rating !== null && visit.rating !== undefined}
										<div class="flex justify-end mb-2">
											<StarRating rating={visit.rating} size="sm" readonly />
										</div>
									{/if}

									{#if isAllDay(visit.start_date)}
										<div class="flex items-center gap-2 mb-2">
											<span class="badge badge-primary">All Day</span>
											<span class="font-semibold">
												{visit.start_date ? visit.start_date.split('T')[0] : ''} – {visit.end_date
													? visit.end_date.split('T')[0]
													: ''}
											</span>
										</div>
									{:else}
										<div class="space-y-2">
											<div class="flex items-center gap-2">
												<span class="badge badge-primary">🕓 {$t('adventures.timed')}</span>
												{#if visit.timezone}
													<span class="badge badge-outline">{visit.timezone}</span>
												{/if}
											</div>
											<div class="text-sm">
												{#if visit.timezone}
													<strong>{$t('adventures.start')}:</strong>
													{DateTime.fromISO(visit.start_date, { zone: 'utc' })
														.setZone(visit.timezone)
														.toLocaleString(DateTime.DATETIME_MED)}<br />
													<strong>{$t('adventures.end')}:</strong>
													{DateTime.fromISO(visit.end_date, { zone: 'utc' })
														.setZone(visit.timezone)
														.toLocaleString(DateTime.DATETIME_MED)}
												{:else}
													<strong>{$t('adventures.start')}:</strong>
													{DateTime.fromISO(visit.start_date).toLocaleString(
														DateTime.DATETIME_MED
													)}<br />
													<strong>{$t('adventures.end')}:</strong>
													{DateTime.fromISO(visit.end_date).toLocaleString(
														DateTime.DATETIME_MED
													)}
												{/if}
											</div>
										</div>
									{/if}

									{#if visit.notes || visit.collection_info}
										<div class="mt-3 p-3 bg-base-200 rounded-lg">
											<p class="text-sm italic">
												{#if visit.notes}"{visit.notes}"{/if}{#if visit.notes && visit.collection_info} - {/if}{#if visit.collection_info}<a
														href="/collections/{visit.collection_info.id}"
														class="link link-hover link-primary font-semibold not-italic"
														>{visit.collection_info.name}</a
													>{/if}
											</p>
										</div>
									{/if}

									<!-- Activities Section -->
									{#if showActivities && visit.activities && visit.activities.length > 0}
										<div class="mt-4">
											<h4 class="font-semibold mb-3 flex items-center gap-2">
												🏃‍♂️ {$t('adventures.activities') || 'Activities'} ({visit.activities.length})
											</h4>
											<div class="space-y-3">
												{#each visit.activities as activity}
													<ActivityCard
														{activity}
														readOnly={true}
														{trails}
														{visit}
														{measurementSystem}
													/>
												{/each}
											</div>
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
