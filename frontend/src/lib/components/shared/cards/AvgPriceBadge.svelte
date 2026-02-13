<script lang="ts">
	import { formatMoney } from '$lib/money';
	import type { DerivedPrice } from '$lib/types';

	export let avgPricePerUser: DerivedPrice | null | undefined = null;
	export let avgPricePerUserPerNight: DerivedPrice | null | undefined = null;
	export let showIcon: boolean = true;
	export let badgeClass: string = 'badge-success badge-sm';

	// Use per-night if available (lodging), otherwise per-user
	$: derivedPrice = avgPricePerUserPerNight || avgPricePerUser;
	$: priceLabel = derivedPrice
		? formatMoney({ amount: derivedPrice.amount, currency: derivedPrice.currency })
		: null;
</script>

{#if priceLabel}
	<span class="badge {badgeClass} whitespace-nowrap">
		{#if showIcon}💰{/if} {priceLabel}
	</span>
{/if}
