<script>
  import "../app.css";
  import Navbar from "./Navbar.svelte";
</script>

<div class="flex h-screen max-h-screen flex-col">
  <Navbar />
  <div class="grow bg-slate-800 max-h-full">
    <slot></slot>
  </div>
</div>
