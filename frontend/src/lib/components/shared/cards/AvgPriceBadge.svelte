<script lang="ts">
	import { t } from 'svelte-i18n';
	import { formatMoney } from '$lib/money';
	import type { DerivedPrice } from '$lib/types';

	export let avgPricePerUser: DerivedPrice | null | undefined = null;
	export let avgPricePerUserPerNight: DerivedPrice | null | undefined = null;
	export let showIcon: boolean = true;
	export let badgeClass: string = 'badge-info badge-sm';

	// Use per-night if available (lodging), otherwise per-user
	$: derivedPrice = avgPricePerUserPerNight || avgPricePerUser;
	$: priceLabel = derivedPrice
		? formatMoney({ amount: derivedPrice.amount, currency: derivedPrice.currency })
		: null;
	$: isPerNight = !!avgPricePerUserPerNight;
</script>

{#if priceLabel}
	<span class="badge {badgeClass} whitespace-nowrap">
		{#if showIcon}💰{/if} {priceLabel} <span class="opacity-70">{isPerNight ? $t('adventures.avg_per_user_per_night') : $t('adventures.avg_per_user')}</span>
	</span>
{/if}
