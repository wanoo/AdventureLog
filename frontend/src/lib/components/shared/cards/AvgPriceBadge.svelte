<script lang="ts">
	import { formatMoney } from '$lib/money';
	import type { DerivedPrice } from '$lib/types';
	import { formatConvertedPrice, ratesLoaded } from '$lib/stores/exchangeRates';

	export let avgPricePerUser: DerivedPrice | null | undefined = null;
	export let avgPricePerUserPerNight: DerivedPrice | null | undefined = null;
	export let countryCurrency: string | null = null;
	export let showIcon: boolean = true;
	export let badgeClass: string = 'badge-success badge-sm';

	// Use per-night if available (lodging), otherwise per-user
	$: derivedPrice = avgPricePerUserPerNight || avgPricePerUser;

	// Show country currency if available and different from original
	$: priceLabel = (() => {
		if (!derivedPrice) return null;
		const originalCurrency = derivedPrice.currency;
		if ($ratesLoaded && countryCurrency && countryCurrency !== originalCurrency) {
			const converted = formatConvertedPrice(derivedPrice.amount, originalCurrency, countryCurrency);
			if (converted) return converted;
		}
		return formatMoney({ amount: derivedPrice.amount, currency: originalCurrency });
	})();
</script>

{#if priceLabel}
	<span class="badge {badgeClass} whitespace-nowrap">
		{#if showIcon}💰{/if} {priceLabel}
	</span>
{/if}
