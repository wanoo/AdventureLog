<script lang="ts">
	/**
	 * TransportationVisits - Thin wrapper around EntityVisitsBase for transportation entities
	 */
	import type { Collection, Visit } from '$lib/types';
	import { EntityVisitsBase } from '../shared/modal';

	// Props - matching the original interface
	export let collection: Collection | null = null;
	export let visits: Visit[] | null = null;
	export let transportationId: string;
	export let initialVisitDate: string | null = null;
	export let currentUserUsername: string | null = null;
</script>

<EntityVisitsBase
	{collection}
	bind:visits
	entityId={transportationId}
	entityType="transportation"
	{initialVisitDate}
	{currentUserUsername}
	on:back
	on:close
	on:visitAdded
	on:visitDeleted
/>
