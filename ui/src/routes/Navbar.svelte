<script>
    export let links = {};
</script>

<div class="navbar bg-base-100">
  <div class="navbar-start">
    <div class="dropdown">
      <div tabindex="0" role="button" class="btn btn-ghost lg:hidden">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-5 w-5"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h8m-8 6h16" />
        </svg>
      </div>
      <ul class="menu menu-sm dropdown-content bg-base-100 rounded-box z-[1] mt-3 w-52 p-2 shadow">
        {#each Object.entries(links) as [text, href]}
        <li><a href={href}>{text}</a></li>
        {/each}
      </ul>
    </div>
    <a href="/" class="btn btn-ghost text-xl">BioGraph</a>
  </div>
  <div class="navbar-center hidden lg:flex">
    <ul class="menu menu-horizontal px-1">
      {#each Object.entries(links) as [text, href]}
      <li><a href={href}>{text}</a></li>
      {/each}
    </ul>
  </div>
  <div class="navbar-end">
    <a href="/vis" class="btn">Visualise</a>
  </div>
</div>
