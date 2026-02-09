<script lang="ts">
	/**
	 * RadioFilter - Generic radio button filter card
	 * Used for visited, visibility, ownership filters
	 */
	import { createEventDispatcher } from 'svelte';

	export let title: string;
	export let icon: any; // Svelte component
	export let value: string = 'all';
	export let options: { value: string; label: string }[] = [];
	export let name: string = 'filter'; // Unique name for radio group

	const dispatch = createEventDispatcher<{ change: string }>();

	function handleChange(newValue: string) {
		value = newValue;
		dispatch('change', newValue);
	}
</script>

<div class="card bg-base-200/50 p-4">
	<h3 class="font-semibold text-lg mb-4 flex items-center gap-2">
		<svelte:component this={icon} class="w-5 h-5" />
		{title}
	</h3>
	<div class="space-y-2">
		{#each options as option}
			<label class="label cursor-pointer justify-start gap-3">
				<input
					type="radio"
					name={name}
					class="radio radio-primary radio-sm"
					checked={value === option.value}
					on:change={() => handleChange(option.value)}
				/>
				<span class="label-text">{option.label}</span>
			</label>
		{/each}
	</div>
</div>
