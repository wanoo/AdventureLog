<script lang="ts">
	import type { AdditionalLocation } from '$lib/types';
	import { onMount } from 'svelte';
	import type { PageData } from './$types';
	import { goto } from '$app/navigation';
	import { DefaultMarker, MapLibre, Popup, GeoJSON, LineLayer } from 'svelte-maplibre';
	import { t } from 'svelte-i18n';
	// @ts-ignore
	import { DateTime } from 'luxon';

	import LightbulbOn from '~icons/mdi/lightbulb-on';
	import WeatherSunset from '~icons/mdi/weather-sunset';
	import ImageDisplayModal from '$lib/components/ImageDisplayModal.svelte';
	import AttachmentCard from '$lib/components/cards/AttachmentCard.svelte';
	import { getActivityColor, getBasemapUrl, isAllDay } from '$lib';
	import ActivityCard from '$lib/components/cards/ActivityCard.svelte';
	import TrailCard from '$lib/components/cards/TrailCard.svelte';
	import NewLocationModal from '$lib/components/locations/LocationModal.svelte';
	import CashMultiple from '~icons/mdi/cash-multiple';
	import HistoryPanel from '$lib/components/HistoryPanel.svelte';
	import { DEFAULT_CURRENCY, formatMoney, toMoneyValue } from '$lib/money';

	// Shared components
	import {
		EntityNotFound,
		EntityLoading,
		EntityHeroSection,
		EntityDescriptionCard,
		EntityVisitsTimeline,
		EntityEditFab,
		EntityAttachmentsCard,
		EntityImagesCard,
		sortImagesByPrimary,
		sortVisitsChronologically,
		getTotalActivities,
		getTotalDistance,
		getTotalElevationGain
	} from '$lib/components/shared/detail';

	let geojson: any;

	export let data: PageData;
	let measurementSystem = data.user?.measurement_system || 'metric';

	let adventure: AdditionalLocation;
	let notFound: boolean = false;
	let isEditModalOpen: boolean = false;
	let modalInitialIndex: number = 0;
	let isImageModalOpen: boolean = false;
	let history: any[] = [];
	let ratingRefreshKey: number = 0;

	$: adventurePriceLabel = adventure
		? formatMoney(
				toMoneyValue(
					adventure.price,
					adventure.price_currency,
					data.user?.default_currency || DEFAULT_CURRENCY
				)
			)
		: null;

	// Note: is_visited is computed by the backend (VisitStatusMixin)
	// It checks: visit date is in the past AND (in collab mode) only current user's visits
	// Do NOT override it here - use the value from the API directly

	$: canEdit = (data.user?.uuid && adventure?.user?.uuid && data.user.uuid === adventure.user.uuid) ||
		(data.collaborativeMode && adventure?.is_public);

	// Build hero badges
	$: heroBadges = adventure ? buildHeroBadges(adventure) : [];

	function buildHeroBadges(a: AdditionalLocation) {
		const badges: { label: string; class: string; href?: string }[] = [];

		if (a.category) {
			badges.push({
				label: `${a.category.display_name} ${a.category.icon}`,
				class: 'badge-primary',
				href: `/locations?types=${a.category.name}`
			});
		}
		if (a.location) {
			badges.push({
				label: `📍 ${a.location}`,
				class: 'badge-secondary'
			});
		}
		if (a.visits && a.visits.length > 0) {
			badges.push({
				label: `🎯 ${a.visits.length} ${a.visits.length === 1 ? $t('adventures.visit') : $t('adventures.visits')}`,
				class: 'badge-accent'
			});
		}
		if (a.is_visited) {
			badges.push({
				label: `✅ ${$t('adventures.visited')}`,
				class: 'badge-success'
			});
		} else {
			badges.push({
				label: `⏳ ${$t('adventures.not_visited')}`,
				class: 'badge-warning'
			});
		}
		if (a.trails && a.trails.length > 0) {
			badges.push({
				label: `🥾 ${a.trails.length} Trail${a.trails.length === 1 ? '' : 's'}`,
				class: 'badge-info'
			});
		}

		return badges;
	}

	function hasActivityGeojson(adv: AdditionalLocation) {
		return adv.visits.some((visit) => visit.activities.some((activity) => activity.geojson));
	}

	function hasAttachmentGeojson(adv: AdditionalLocation) {
		return adv.attachments.some((attachment) => attachment.geojson);
	}

	onMount(async () => {
		if (data.props.adventure) {
			adventure = data.props.adventure;
			adventure.images = sortImagesByPrimary(adventure.images || []);
			if (adventure.visits) {
				adventure.visits = sortVisitsChronologically(adventure.visits);
			}

			// Fetch history in collaborative mode
			if (data.collaborativeMode) {
				try {
					const res = await fetch(`/api/locations/${adventure.id}/history/`);
					if (res.ok) {
						history = await res.json();
					}
				} catch (e) {
					console.error('Failed to fetch history:', e);
				}
			}
		} else {
			notFound = true;
		}
	});

	function closeImageModal() {
		isImageModalOpen = false;
	}

	function openImageModal(imageIndex: number) {
		modalInitialIndex = imageIndex;
		isImageModalOpen = true;
	}

	async function handleEditModalClose() {
		try {
			const locationRes = await fetch(`/api/locations/${adventure.id}/`);
			if (locationRes.ok) {
				adventure = await locationRes.json();
				ratingRefreshKey++;
			}
		} catch (e) {
			console.error('Failed to refresh location:', e);
		}
		// Refresh history after save in collaborative mode
		if (data.collaborativeMode && adventure.id) {
			try {
				const res = await fetch(`/api/locations/${adventure.id}/history/`);
				if (res.ok) {
					history = await res.json();
				}
			} catch (e) {
				console.error('Failed to refresh history:', e);
			}
		}
		isEditModalOpen = false;
	}
</script>

{#if notFound}
	<EntityNotFound title={$t('adventures.location_not_found')} />
{/if}

{#if isEditModalOpen}
	<NewLocationModal
		on:close={handleEditModalClose}
		user={data.user}
		locationToEdit={adventure}
		collaborativeMode={data.collaborativeMode}
	/>
{/if}

{#if isImageModalOpen}
	<ImageDisplayModal
		images={adventure.images}
		initialIndex={modalInitialIndex}
		on:close={closeImageModal}
	/>
{/if}

{#if !adventure && !notFound}
	<EntityLoading />
{/if}

{#if adventure}
	<EntityEditFab show={canEdit} onClick={() => (isEditModalOpen = true)} />

	<!-- Hero Section -->
	<EntityHeroSection
		name={adventure.name}
		images={adventure.images || []}
		averageRating={adventure.average_rating}
		rating={adventure.rating}
		{ratingRefreshKey}
		badges={heroBadges}
		on:openImage={(e) => openImageModal(e.detail)}
	/>

	<!-- Main Content -->
	<div class="container mx-auto px-2 sm:px-4 py-6 sm:py-8 max-w-7xl">
		<div class="grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-8">
			<!-- Left Column - Main Content -->
			<div class="lg:col-span-2 space-y-6 sm:space-y-8">
				<!-- Author Info Card -->
				{#if adventure.user}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body">
							<div class="flex items-center gap-4">
								{#if adventure.user.profile_pic}
									<div class="avatar">
										<div class="w-16 rounded-full ring ring-primary ring-offset-base-100 ring-offset-2">
											<img src={adventure.user.profile_pic} alt={adventure.user.username} />
										</div>
									</div>
								{:else}
									<div class="avatar placeholder">
										<div class="bg-primary text-primary-content w-16 rounded-full ring ring-primary ring-offset-base-100 ring-offset-2">
											<span class="text-xl font-bold">
												{adventure.user.first_name
													? adventure.user.first_name.charAt(0)
													: adventure.user.username.charAt(0)}{adventure.user.last_name
													? adventure.user.last_name.charAt(0)
													: ''}
											</span>
										</div>
									</div>
								{/if}
								<div class="flex-1">
									<div class="text-lg font-bold">
										{#if adventure.user.public_profile}
											<a href={`/profile/${adventure.user.username}`} class="link link-hover">
												{adventure.user.first_name || adventure.user.username}
												{adventure.user.last_name || ''}
											</a>
										{:else}
											{adventure.user.first_name || adventure.user.username}
											{adventure.user.last_name || ''}
										{/if}
									</div>
									<div class="flex items-center gap-2 text-sm opacity-70 mt-1">
										<div class="badge badge-sm">
											{adventure.is_public
												? `🌍 ${$t('adventures.public')}`
												: `🔒 ${$t('adventures.private')}`}
										</div>
										{#if adventure.collections && adventure.collections.length > 0}
											<div class="badge badge-sm badge-outline">
												📚 {adventure.collections.length} {$t('navbar.collections')}
											</div>
										{/if}
									</div>
									{#if adventure.last_modified_by}
										<div class="text-xs opacity-60 mt-2">
											{$t('adventures.last_edited_by')}
											<a href="/profile/{adventure.last_modified_by.username}" class="link link-hover link-primary font-semibold">{adventure.last_modified_by.username}</a>
											• {new Date(adventure.last_modified_by.timestamp).toLocaleDateString()}
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Contributors (Collaborative Mode) -->
				{#if adventure.contributors && adventure.contributors.length > 1}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body py-4">
							<div class="flex items-center justify-between">
								<h3 class="text-sm font-semibold opacity-70">{$t('adventures.contributors')}</h3>
								<div class="avatar-group -space-x-3 rtl:space-x-reverse">
									{#each adventure.contributors.slice(0, 8) as contributor}
										<a href="/profile/{contributor.username}" class="tooltip" data-tip={contributor.username}>
											<div class="avatar border-2 border-base-200">
												{#if contributor.profile_pic}
													<div class="w-8">
														<img src={contributor.profile_pic} alt={contributor.username} />
													</div>
												{:else}
													<div class="bg-primary text-primary-content w-8">
														<span class="text-xs">{contributor.username.charAt(0).toUpperCase()}</span>
													</div>
												{/if}
											</div>
										</a>
									{/each}
									{#if adventure.contributors.length > 8}
										<div class="avatar placeholder border-2 border-base-200">
											<div class="bg-neutral text-neutral-content w-8">
												<span class="text-xs">+{adventure.contributors.length - 8}</span>
											</div>
										</div>
									{/if}
								</div>
							</div>
						</div>
					</div>
				{/if}

				<EntityDescriptionCard description={adventure.description} />

				<!-- Trails Section -->
				{#if adventure.trails && adventure.trails.length > 0}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body">
							<h2 class="card-title text-2xl mb-6">🥾 {$t('adventures.trails')}</h2>
							<div class="grid gap-4">
								{#each adventure.trails as trail}
									<TrailCard
										{trail}
										measurementSystem={data.user?.measurement_system || 'metric'}
									/>
								{/each}
							</div>
						</div>
					</div>
				{/if}

				<EntityVisitsTimeline
					visits={adventure.visits || []}
					measurementSystem={data.user?.measurement_system || 'metric'}
					trails={adventure.trails || []}
				/>

				<!-- Map Section -->
				{#if (adventure.longitude && adventure.latitude) || hasAttachmentGeojson(adventure) || hasActivityGeojson(adventure)}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body">
							<h2 class="card-title text-2xl mb-4">🗺️ {$t('adventures.location')}</h2>

							{#if adventure.longitude && adventure.latitude}
								<!-- Compact Coordinates Card -->
								<div class="card bg-gradient-to-br from-primary/5 to-secondary/5 shadow-lg mb-4 border border-primary/10">
									<div class="card-body p-4">
										<div class="flex items-center justify-between mb-3">
											<h3 class="text-lg font-bold flex items-center gap-2">🎯 {$t('adventures.coordinates')}</h3>
										</div>

										<div class="grid grid-cols-2 gap-3 mb-4">
											<div class="text-center p-2 bg-base-200/70 rounded border border-primary/10">
												<div class="text-xs text-primary/70 uppercase tracking-wide">{$t('adventures.latitude')}</div>
												<div class="text-lg font-bold text-primary">{adventure.latitude}°</div>
											</div>
											<div class="text-center p-2 bg-base-200/70 rounded border border-secondary/10">
												<div class="text-xs text-secondary/70 uppercase tracking-wide">{$t('adventures.longitude')}</div>
												<div class="text-lg font-bold text-secondary">{adventure.longitude}°</div>
											</div>
										</div>

										<!-- Location Info -->
										{#if adventure.city || adventure.region || adventure.country}
											<div class="flex flex-wrap justify-center gap-2 mb-4">
												{#if adventure.city}
													<button
														class="btn btn-xs btn-outline hover:btn-info"
														on:click={() => {
															if (adventure.country && adventure.region) {
																goto(`/worldtravel/${adventure.country.country_code}/${adventure.region.id}`);
															} else if (adventure.country) {
																goto(`/worldtravel/${adventure.country.country_code}`);
															}
														}}
													>
														🏙️ {adventure.city.name}
													</button>
												{/if}
												{#if adventure.region}
													<button
														class="btn btn-xs btn-outline hover:btn-warning"
														on:click={() => {
															if (adventure.country && adventure.region) {
																goto(`/worldtravel/${adventure.country.country_code}/${adventure.region.id}`);
															} else if (adventure.country) {
																goto(`/worldtravel/${adventure.country.country_code}`);
															}
														}}
													>
														🗺️ {adventure.region.name}
													</button>
												{/if}
												{#if adventure.country}
													<button
														class="btn btn-xs btn-outline hover:btn-success"
														on:click={() => goto(`/worldtravel/${adventure.country?.country_code}`)}
													>
														{#if adventure.country.flag_url}
															<img src={adventure.country.flag_url} alt={adventure.country.name} class="w-4 h-3 rounded" />
														{:else}
															🌎
														{/if}
														{adventure.country.name}
													</button>
												{/if}
											</div>
										{/if}

										<!-- External Maps Links -->
										<div class="grid grid-cols-3 gap-2 mb-3">
											<a
												class="btn btn-sm btn-outline hover:btn-neutral"
												href={`https://maps.apple.com/?q=${adventure.latitude},${adventure.longitude}`}
												target="_blank"
												rel="noopener noreferrer"
											>
												🍎 Apple
											</a>
											<a
												class="btn btn-sm btn-outline hover:btn-accent"
												href={`https://maps.google.com/?q=${adventure.latitude},${adventure.longitude}`}
												target="_blank"
												rel="noopener noreferrer"
											>
												🌍 Google
											</a>
											<a
												class="btn btn-sm btn-outline hover:btn-primary"
												href={`https://www.openstreetmap.org/?mlat=${adventure.latitude}&mlon=${adventure.longitude}`}
												target="_blank"
												rel="noopener noreferrer"
											>
												🗺️ OSM
											</a>
										</div>

										<!-- Quick Copy Actions -->
										<div class="flex gap-2">
											<button
												class="btn btn-xs btn-ghost flex-1 text-xs"
												on:click={() => navigator.clipboard.writeText(`${adventure.latitude}, ${adventure.longitude}`)}
											>
												📋 {$t('adventures.copy_coordinates')}
											</button>
											<button
												class="btn btn-xs btn-ghost flex-1 text-xs"
												on:click={() => navigator.clipboard.writeText(`https://www.google.com/maps/@${adventure.latitude},${adventure.longitude},15z`)}
											>
												🔗 {$t('adventures.copy_link')}
											</button>
										</div>
									</div>
								</div>
							{/if}

							<div class="rounded-lg overflow-hidden shadow-lg">
								<MapLibre
									style={getBasemapUrl()}
									class="w-full h-96"
									standardControls
									center={{ lng: adventure.longitude || 0, lat: adventure.latitude || 0 }}
									zoom={adventure.longitude ? 12 : 1}
								>
									{#if geojson}
										<GeoJSON data={geojson}>
											<LineLayer paint={{ 'line-color': '#FF0000', 'line-width': 4 }} />
										</GeoJSON>
									{/if}

									<!-- Activity GPS tracks -->
									{#each adventure.visits as visit}
										{#each visit.activities as activity}
											{#if activity.geojson}
												<GeoJSON data={activity.geojson}>
													<LineLayer
														paint={{
															'line-color': getActivityColor(activity.sport_type),
															'line-width': 3,
															'line-opacity': 0.8
														}}
													/>
												</GeoJSON>
											{/if}
										{/each}
									{/each}

									{#each adventure.attachments as attachment}
										{#if attachment.geojson}
											<GeoJSON data={attachment.geojson}>
												<LineLayer paint={{ 'line-color': '#00FF00', 'line-width': 2, 'line-opacity': 0.6 }} />
											</GeoJSON>
										{/if}
									{/each}

									{#if adventure.longitude && adventure.latitude}
										<DefaultMarker lngLat={{ lng: adventure.longitude, lat: adventure.latitude }}>
											<Popup openOn="click" offset={[0, -10]}>
												<div class="p-2">
													<div class="text-lg font-bold text-black mb-1">{adventure.name}</div>
													<p class="font-semibold text-black text-sm mb-2">
														{adventure.category?.display_name + ' ' + adventure.category?.icon}
													</p>
													{#if adventure.visits.length > 0}
														<div class="text-xs text-black">
															{adventure.visits.length} {$t('adventures.visit')}{adventure.visits.length !== 1 ? 's' : ''}
														</div>
													{/if}
												</div>
											</Popup>
										</DefaultMarker>
									{/if}
								</MapLibre>
							</div>
						</div>
					</div>
				{/if}
			</div>

			<!-- Right Column - Sidebar -->
			<div class="space-y-4 sm:space-y-6">
				<!-- Quick Info Card -->
				<div class="card bg-base-200 shadow-xl">
					<div class="card-body">
						<h3 class="card-title text-lg mb-4">ℹ️ {$t('adventures.basic_information')}</h3>
						<div class="space-y-3">
							{#if adventurePriceLabel}
								<div class="flex items-start gap-3">
									<CashMultiple class="w-5 h-5 text-primary mt-1 flex-shrink-0" />
									<div>
										<div class="text-sm opacity-70 mb-0.5">{$t('adventures.price')}</div>
										<div class="text-base font-semibold">{adventurePriceLabel}</div>
									</div>
								</div>
							{/if}
							{#if adventure.tags && adventure.tags.length > 0}
								<div>
									<div class="text-sm opacity-70 mb-1">{$t('adventures.tags')}</div>
									<div class="flex flex-wrap gap-1">
										{#each adventure.tags as tag}
											<span class="badge badge-sm badge-outline">{tag}</span>
										{/each}
									</div>
								</div>
							{/if}
							{#if adventure.link}
								<div>
									<div class="text-sm opacity-70 mb-1">{$t('adventures.link')}</div>
									<a href={adventure.link} class="link link-primary text-sm break-all" target="_blank">
										{adventure.link.length > 30 ? `${adventure.link.slice(0, 30)}...` : adventure.link}
									</a>
								</div>
							{/if}
						</div>
					</div>
				</div>

				<!-- Activity Summary -->
				{#if getTotalActivities(adventure) > 0}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body">
							<h3 class="card-title text-lg mb-4">🏃‍♂️ Activity Summary</h3>
							<div class="space-y-2">
								<div class="stat">
									<div class="stat-title">Total Activities</div>
									<div class="stat-value text-2xl">{getTotalActivities(adventure)}</div>
								</div>
								{#if getTotalDistance(adventure, measurementSystem) > 0}
									<div class="stat">
										<div class="stat-title">Total Distance</div>
										<div class="stat-value text-xl">
											{getTotalDistance(adventure, measurementSystem).toFixed(1)}
											{measurementSystem === 'imperial' ? 'mi' : 'km'}
										</div>
									</div>
								{/if}
								{#if getTotalElevationGain(adventure, measurementSystem) > 0}
									<div class="stat">
										<div class="stat-title">Total Elevation</div>
										<div class="stat-value text-xl">
											{getTotalElevationGain(adventure, measurementSystem).toFixed(0)}
											{measurementSystem === 'imperial' ? 'ft' : 'm'}
										</div>
									</div>
								{/if}
							</div>
						</div>
					</div>
				{/if}

				<!-- Sunrise/Sunset -->
				{#if adventure.sun_times && adventure.sun_times.length > 0}
					<div class="card bg-base-200 shadow-xl">
						<div class="card-body">
							<h3 class="card-title text-lg mb-4">
								🌅 {$t('adventures.sun_times')}
								<WeatherSunset class="w-5 h-5" />
							</h3>
							<div class="space-y-3">
								{#each adventure.sun_times as sun_time}
									<div class="border-l-4 border-warning pl-3">
										<div class="font-semibold text-sm">{new Date(sun_time.date).toLocaleDateString()}</div>
										<div class="text-xs opacity-70">
											{$t('adventures.sunrise')}: {sun_time.sunrise} • {$t('adventures.sunset')}: {sun_time.sunset}
										</div>
									</div>
								{/each}
							</div>
						</div>
					</div>
				{/if}

				<EntityAttachmentsCard attachments={adventure.attachments || []} showGpxTip={true} />

				<EntityImagesCard
					images={adventure.images || []}
					columns={3}
					on:openImage={(e) => openImageModal(e.detail)}
				/>

				<!-- History Panel (Collaborative Mode) -->
				{#if data.collaborativeMode && history.length > 0}
					<HistoryPanel
						{history}
						locationId={adventure.id}
						canRevert={true}
						on:reverted={async () => {
							const historyRes = await fetch(`/api/locations/${adventure.id}/history/`);
							if (historyRes.ok) {
								history = await historyRes.json();
							}
							window.location.reload();
						}}
					/>
				{/if}
			</div>
		</div>
	</div>
{/if}

<svelte:head>
	<title>
		{data.props.adventure && data.props.adventure.name
			? `${data.props.adventure.name}`
			: 'Adventure'}
	</title>
	<meta name="description" content="Explore the world and add countries to your visited list!" />
</svelte:head>
