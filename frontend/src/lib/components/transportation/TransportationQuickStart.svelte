<script lang="ts">
	import { createEventDispatcher, onMount } from 'svelte';
	import { MapLibre, Marker, MapEvents, GeoJSON, LineLayer } from 'svelte-maplibre';
	import { t } from 'svelte-i18n';
	import { getBasemapUrl } from '$lib';

	// Icons
	import SearchIcon from '~icons/mdi/magnify';
	import LocationIcon from '~icons/mdi/crosshairs-gps';
	import MapIcon from '~icons/mdi/map';
	import CheckIcon from '~icons/mdi/check';
	import ClearIcon from '~icons/mdi/close';
	import PinIcon from '~icons/mdi/map-marker';
	import FlagIcon from '~icons/mdi/flag';
	import SwapIcon from '~icons/mdi/swap-horizontal';

	const dispatch = createEventDispatcher();

	// Which location are we selecting?
	let selectingMode: 'origin' | 'destination' = 'origin';

	// Origin location
	let originQuery = '';
	let originResults: any[] = [];
	let originLocation: any = null;
	let originMarker: { lng: number; lat: number } | null = null;

	// Destination location
	let destinationQuery = '';
	let destinationResults: any[] = [];
	let destinationLocation: any = null;
	let destinationMarker: { lng: number; lat: number } | null = null;

	let mapCenter: [number, number] = [-74.5, 40];
	let mapZoom = 2;
	let isSearching = false;
	let isReverseGeocoding = false;
	let searchTimeout: ReturnType<typeof setTimeout>;
	let mapComponent: any;

	// Route line GeoJSON
	$: routeGeoJson =
		originMarker && destinationMarker
			? {
					type: 'Feature',
					geometry: {
						type: 'LineString',
						coordinates: [
							[originMarker.lng, originMarker.lat],
							[destinationMarker.lng, destinationMarker.lat]
						]
					}
				}
			: null;

	// Search for locations
	async function searchLocations(query: string, mode: 'origin' | 'destination') {
		if (!query.trim() || query.length < 3) {
			if (mode === 'origin') originResults = [];
			else destinationResults = [];
			return;
		}

		isSearching = true;
		try {
			const response = await fetch(
				`/api/reverse-geocode/search/?query=${encodeURIComponent(query)}`
			);
			const results = await response.json();

			const mapped = results.map((result: any) => ({
				id: result.name + result.lat + result.lon,
				name: result.name,
				lat: parseFloat(result.lat),
				lng: parseFloat(result.lon),
				type: result.type,
				category: result.category,
				location: result.display_name
			}));

			if (mode === 'origin') originResults = mapped;
			else destinationResults = mapped;
		} catch (error) {
			console.error('Search error:', error);
			if (mode === 'origin') originResults = [];
			else destinationResults = [];
		} finally {
			isSearching = false;
		}
	}

	// Debounced search for origin
	function handleOriginInput() {
		selectingMode = 'origin';
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchLocations(originQuery, 'origin');
		}, 300);
	}

	// Debounced search for destination
	function handleDestinationInput() {
		selectingMode = 'destination';
		clearTimeout(searchTimeout);
		searchTimeout = setTimeout(() => {
			searchLocations(destinationQuery, 'destination');
		}, 300);
	}

	// Select origin from search results
	function selectOriginResult(location: any) {
		originLocation = location;
		originMarker = { lng: location.lng, lat: location.lat };
		originQuery = location.name;
		originResults = [];
		fitMapToBounds();
	}

	// Select destination from search results
	function selectDestinationResult(location: any) {
		destinationLocation = location;
		destinationMarker = { lng: location.lng, lat: location.lat };
		destinationQuery = location.name;
		destinationResults = [];
		fitMapToBounds();
	}

	// Fit map to show both markers
	function fitMapToBounds() {
		if (originMarker && destinationMarker) {
			const midLng = (originMarker.lng + destinationMarker.lng) / 2;
			const midLat = (originMarker.lat + destinationMarker.lat) / 2;
			mapCenter = [midLng, midLat];
			mapZoom = 4;
		} else if (originMarker) {
			mapCenter = [originMarker.lng, originMarker.lat];
			mapZoom = 10;
		} else if (destinationMarker) {
			mapCenter = [destinationMarker.lng, destinationMarker.lat];
			mapZoom = 10;
		}
	}

	// Handle map click
	async function handleMapClick(e: { detail: { lngLat: { lng: number; lat: number } } }) {
		const { lng, lat } = e.detail.lngLat;

		if (selectingMode === 'origin') {
			originMarker = { lng, lat };
			await reverseGeocode(lng, lat, 'origin');
		} else {
			destinationMarker = { lng, lat };
			await reverseGeocode(lng, lat, 'destination');
		}
		fitMapToBounds();
	}

	// Reverse geocode
	async function reverseGeocode(lng: number, lat: number, mode: 'origin' | 'destination') {
		isReverseGeocoding = true;

		try {
			const response = await fetch(`/api/reverse-geocode/search/?query=${lat},${lng}`);
			const results = await response.json();

			const location =
				results && results.length > 0
					? {
							name: results[0].name,
							lat: lat,
							lng: lng,
							location: results[0].display_name
						}
					: {
							name: `${lat.toFixed(4)}, ${lng.toFixed(4)}`,
							lat: lat,
							lng: lng,
							location: `${lat.toFixed(4)}, ${lng.toFixed(4)}`
						};

			if (mode === 'origin') {
				originLocation = location;
				originQuery = location.name;
			} else {
				destinationLocation = location;
				destinationQuery = location.name;
			}
		} catch (error) {
			console.error('Reverse geocoding error:', error);
		} finally {
			isReverseGeocoding = false;
		}
	}

	// Swap origin and destination
	function swapLocations() {
		const tempLocation = originLocation;
		const tempMarker = originMarker;
		const tempQuery = originQuery;

		originLocation = destinationLocation;
		originMarker = destinationMarker;
		originQuery = destinationQuery;

		destinationLocation = tempLocation;
		destinationMarker = tempMarker;
		destinationQuery = tempQuery;
	}

	// Clear origin
	function clearOrigin() {
		originLocation = null;
		originMarker = null;
		originQuery = '';
		originResults = [];
	}

	// Clear destination
	function clearDestination() {
		destinationLocation = null;
		destinationMarker = null;
		destinationQuery = '';
		destinationResults = [];
	}

	// Continue with selected locations
	function continueWithLocations() {
		dispatch('locationsSelected', {
			origin: originLocation
				? {
						name: originLocation.name,
						latitude: originMarker?.lat,
						longitude: originMarker?.lng,
						location: originLocation.location
					}
				: null,
			destination: destinationLocation
				? {
						name: destinationLocation.name,
						latitude: destinationMarker?.lat,
						longitude: destinationMarker?.lng,
						location: destinationLocation.location
					}
				: null
		});
	}

	onMount(() => {
		return () => {
			clearTimeout(searchTimeout);
		};
	});
</script>

<div class="space-y-6">
	<!-- Origin & Destination Search -->
	<div class="card bg-base-200/50 border border-base-300">
		<div class="card-body p-6">
			<div class="space-y-4">
				<!-- Origin Input -->
				<div class="form-control">
					<label class="label">
						<span class="label-text font-medium flex items-center gap-2">
							<PinIcon class="w-4 h-4 text-success" />
							{$t('transportation.from') || 'From (Departure)'}
						</span>
					</label>
					<div class="relative">
						<input
							type="text"
							bind:value={originQuery}
							on:input={handleOriginInput}
							on:focus={() => (selectingMode = 'origin')}
							placeholder={$t('transportation.from_placeholder') || 'Enter departure location...'}
							class="input input-bordered w-full pr-10"
							class:input-success={originLocation}
							class:ring-2={selectingMode === 'origin'}
							class:ring-success={selectingMode === 'origin'}
						/>
						{#if originQuery}
							<button
								class="absolute inset-y-0 right-0 pr-3 flex items-center"
								on:click={clearOrigin}
							>
								<ClearIcon class="w-4 h-4 text-base-content/40 hover:text-base-content" />
							</button>
						{/if}
					</div>
					<!-- Origin Results -->
					{#if originResults.length > 0 && selectingMode === 'origin'}
						<div class="mt-2 max-h-32 overflow-y-auto space-y-1">
							{#each originResults as result}
								<button
									class="w-full text-left p-2 rounded-lg border border-base-300 hover:bg-base-100 hover:border-success/50 transition-colors text-sm"
									on:click={() => selectOriginResult(result)}
								>
									<div class="font-medium truncate">{result.name}</div>
									<div class="text-xs text-base-content/60 truncate">{result.location}</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>

				<!-- Swap Button -->
				<div class="flex justify-center">
					<button
						class="btn btn-ghost btn-sm btn-circle"
						on:click={swapLocations}
						disabled={!originLocation && !destinationLocation}
					>
						<SwapIcon class="w-5 h-5 rotate-90" />
					</button>
				</div>

				<!-- Destination Input -->
				<div class="form-control">
					<label class="label">
						<span class="label-text font-medium flex items-center gap-2">
							<FlagIcon class="w-4 h-4 text-error" />
							{$t('transportation.to') || 'To (Arrival)'}
						</span>
					</label>
					<div class="relative">
						<input
							type="text"
							bind:value={destinationQuery}
							on:input={handleDestinationInput}
							on:focus={() => (selectingMode = 'destination')}
							placeholder={$t('transportation.to_placeholder') || 'Enter arrival location...'}
							class="input input-bordered w-full pr-10"
							class:input-error={destinationLocation}
							class:ring-2={selectingMode === 'destination'}
							class:ring-error={selectingMode === 'destination'}
						/>
						{#if destinationQuery}
							<button
								class="absolute inset-y-0 right-0 pr-3 flex items-center"
								on:click={clearDestination}
							>
								<ClearIcon class="w-4 h-4 text-base-content/40 hover:text-base-content" />
							</button>
						{/if}
					</div>
					<!-- Destination Results -->
					{#if destinationResults.length > 0 && selectingMode === 'destination'}
						<div class="mt-2 max-h-32 overflow-y-auto space-y-1">
							{#each destinationResults as result}
								<button
									class="w-full text-left p-2 rounded-lg border border-base-300 hover:bg-base-100 hover:border-error/50 transition-colors text-sm"
									on:click={() => selectDestinationResult(result)}
								>
									<div class="font-medium truncate">{result.name}</div>
									<div class="text-xs text-base-content/60 truncate">{result.location}</div>
								</button>
							{/each}
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>

	<!-- Map Section -->
	<div class="card bg-base-100 border border-base-300">
		<div class="card-body p-4">
			<div class="flex items-center justify-between mb-4">
				<h3 class="font-semibold flex items-center gap-2">
					<MapIcon class="w-5 h-5" />
					{$t('adventures.select_on_map') || 'Select on Map'}
				</h3>
				<div class="flex gap-2">
					<button
						class="btn btn-xs"
						class:btn-success={selectingMode === 'origin'}
						class:btn-outline={selectingMode !== 'origin'}
						on:click={() => (selectingMode = 'origin')}
					>
						<PinIcon class="w-3 h-3" /> From
					</button>
					<button
						class="btn btn-xs"
						class:btn-error={selectingMode === 'destination'}
						class:btn-outline={selectingMode !== 'destination'}
						on:click={() => (selectingMode = 'destination')}
					>
						<FlagIcon class="w-3 h-3" /> To
					</button>
				</div>
			</div>

			<p class="text-sm text-base-content/60 mb-4">
				{$t('transportation.click_map_hint') ||
					'Click on the map to set departure or arrival location'}
			</p>

			{#if isReverseGeocoding}
				<div class="flex items-center justify-center py-2 mb-4">
					<span class="loading loading-spinner loading-sm"></span>
					<span class="ml-2 text-sm text-base-content/60">Getting location details...</span>
				</div>
			{/if}

			<div class="relative">
				<MapLibre
					bind:this={mapComponent}
					style={getBasemapUrl()}
					class="w-full h-80 rounded-lg border border-base-300"
					center={mapCenter}
					zoom={mapZoom}
					standardControls
				>
					<MapEvents on:click={handleMapClick} />

					{#if originMarker}
						<Marker
							lngLat={[originMarker.lng, originMarker.lat]}
							class="grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-success shadow-lg cursor-pointer"
						>
							<PinIcon class="w-5 h-5 text-success-content" />
						</Marker>
					{/if}

					{#if destinationMarker}
						<Marker
							lngLat={[destinationMarker.lng, destinationMarker.lat]}
							class="grid h-8 w-8 place-items-center rounded-full border-2 border-white bg-error shadow-lg cursor-pointer"
						>
							<FlagIcon class="w-5 h-5 text-error-content" />
						</Marker>
					{/if}

					{#if routeGeoJson}
						<GeoJSON data={routeGeoJson}>
							<LineLayer
								paint={{
									'line-color': '#6366f1',
									'line-width': 3,
									'line-dasharray': [2, 2]
								}}
							/>
						</GeoJSON>
					{/if}
				</MapLibre>
			</div>
		</div>
	</div>

	<!-- Selected Locations Display -->
	{#if originLocation || destinationLocation}
		<div class="card bg-info/10 border border-info/30">
			<div class="card-body p-4">
				<div class="flex items-start gap-3">
					<div class="p-2 bg-info/20 rounded-lg">
						<CheckIcon class="w-5 h-5 text-info" />
					</div>
					<div class="flex-1 space-y-2">
						{#if originLocation}
							<div>
								<span class="text-xs text-success font-medium">FROM:</span>
								<span class="text-sm ml-2">{originLocation.name}</span>
							</div>
						{/if}
						{#if destinationLocation}
							<div>
								<span class="text-xs text-error font-medium">TO:</span>
								<span class="text-sm ml-2">{destinationLocation.name}</span>
							</div>
						{/if}
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Action Buttons -->
	<div class="flex gap-3 pt-4">
		<button class="btn btn-neutral-200 flex-1" on:click={() => dispatch('cancel')}>
			{$t('adventures.cancel') || 'Cancel'}
		</button>
		<button class="btn btn-primary flex-1" on:click={continueWithLocations}>
			{#if isReverseGeocoding}
				<span class="loading loading-spinner loading-xs"></span>
			{:else}
				{$t('adventures.continue')}
			{/if}
		</button>
	</div>
</div>
