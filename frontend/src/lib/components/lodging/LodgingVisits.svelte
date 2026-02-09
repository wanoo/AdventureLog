<script lang="ts">
	/**
	 * LodgingVisits - Thin wrapper around EntityVisitsBase for lodging entities
	 */
	import type { Collection, Visit } from '$lib/types';
	import { EntityVisitsBase } from '../shared/modal';

	// Props - matching the original interface
	export let collection: Collection | null = null;
	export let visits: Visit[] | null = null;
	export let lodgingId: string;
	export let initialVisitDate: string | null = null;
	export let currentUserUsername: string | null = null;
</script>

<EntityVisitsBase
	{collection}
	bind:visits
	entityId={lodgingId}
	entityType="lodging"
	{initialVisitDate}
	{currentUserUsername}
	on:back
	on:close
	on:visitAdded
	on:visitDeleted
/>
