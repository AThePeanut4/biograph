<script lang="ts">
  import QueryBar from "./QueryBar.svelte";

  let container: HTMLDivElement;
</script>

<div class="flex h-full flex-col">
  <div class="grow" bind:this={container}></div>
  <QueryBar {container} />
</div>
