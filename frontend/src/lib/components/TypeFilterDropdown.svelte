<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import { t } from 'svelte-i18n';

	const dispatch = createEventDispatcher<{ change: string }>();

	export let types: string;
	export let typeOptions: { value: string; label: string; icon: string }[];

	let types_arr: string[] = [];

	$: types_arr = types ? types.split(',').filter((t) => t !== '') : [];

	function clearTypes() {
		types = '';
		types_arr = [];
		dispatch('change', types);
	}

	function toggleSelect(type: string) {
		if (types_arr.indexOf(type) > -1) {
			types_arr = types_arr.filter((item) => item !== type);
		} else {
			types_arr = [...types_arr, type];
		}
		types_arr = types_arr.filter((item) => item !== '');
		types = types_arr.join(',');
		dispatch('change', types);
	}
</script>

<div class="space-y-2">
	{#each typeOptions as type}
		<label class="label cursor-pointer justify-start gap-3 py-1">
			<input
				type="checkbox"
				class="checkbox checkbox-primary checkbox-sm"
				value={type.value}
				on:change={() => toggleSelect(type.value)}
				checked={types_arr.includes(type.value)}
			/>
			<span class="label-text flex items-center gap-1.5">
				<span class="text-base">{type.icon}</span>
				{type.label}
			</span>
		</label>
	{/each}
	{#if types_arr.length > 0}
		<button class="btn btn-ghost btn-xs mt-2" on:click={clearTypes}>
			{$t('adventures.clear')}
		</button>
	{/if}
</div>
