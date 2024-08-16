<script>
    import "../app.css";
    import Navbar from "./Navbar.svelte";
    const links = {
        "Documentation": "https://elgoog.co.za/api/docs/",
        "Server": "https://elgoog.co.za:7473",
    };
</script>

<div class="flex flex-col h-screen">
    <Navbar {links} />
    <div class="grow bg-slate-800">
        <slot></slot>
    </div>
</div>
