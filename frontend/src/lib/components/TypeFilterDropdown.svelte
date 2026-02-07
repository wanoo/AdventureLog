<script lang="ts">
	import { t } from 'svelte-i18n';

	export let types: string;
	export let typeOptions: { value: string; label: string; icon: string }[];

	let types_arr: string[] = [];

	$: types_arr = types ? types.split(',').filter((t) => t !== '') : [];

	function clearTypes() {
		types = '';
		types_arr = [];
	}

	function toggleSelect(type: string) {
		if (types_arr.indexOf(type) > -1) {
			types_arr = types_arr.filter((item) => item !== type);
		} else {
			types_arr = [...types_arr, type];
		}
		types_arr = types_arr.filter((item) => item !== '');
		types = types_arr.join(',');
	}

	function getCount(typeValue: string): number {
		return typeOptions.find((t) => t.value === typeValue) ? 1 : 0;
	}
</script>

<div class="collapse collapse-plus mb-4">
	<input type="checkbox" checked />

	<div class="collapse-title text-xl bg-base-300 font-medium">
		{$t('adventures.filter_by_type') || 'Filter by Type'}
	</div>

	<div class="collapse-content bg-base-300">
		<button class="btn btn-sm btn-neutral-300 w-full mb-2" on:click={clearTypes}>
			{$t('adventures.clear')}
		</button>

		<ul>
			{#each typeOptions as type}
				<li class="mb-1">
					<label class="cursor-pointer flex items-center gap-2">
						<input
							type="checkbox"
							class="checkbox"
							value={type.value}
							on:change={() => toggleSelect(type.value)}
							checked={types_arr.includes(type.value)}
						/>
						<span>
							{type.icon} {type.label}
						</span>
					</label>
				</li>
			{/each}
		</ul>
	</div>
</div>
