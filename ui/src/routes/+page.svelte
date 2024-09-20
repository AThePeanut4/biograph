<script lang="ts">
  /*
    Future TODOs:
    1. Move constants to the top of the file
  */

  import { onMount } from "svelte";
  import * as d3 from "d3";
  const ENDPOINT = import.meta.env.VITE_ENDPOINT;

  interface IGraph {
    nodes: INode[];
    relationships: IRelationship[];
  }

  interface INode {
    id: string;
    label: string;
    properties: Record<string, string>;
  }

  interface IRelationship {
    start_node: string;
    end_node: string;
    properties: Record<string, string>;
  }

  // This is the div that contains the visualisation
  let container: HTMLElement;
  let modelsLoading = false;
  // These are the properties of a selected node in a graph
  let properties = {};

  onMount(() => {
    loadModels();
  });

  // --- Load Models ---
  async function loadModels() {
    if (modelsLoading) return;
    modelsLoading = true;

    // Remove previous graph
    container.innerHTML = "";

    try {
      const res = await visualiseFromEndpoint(ENDPOINT + "/model/all");
    } catch (error) {
      networkError("The models failed to load");
      modelsLoading = false;
    }
  }

  async function visualiseFromEndpoint(endpointAndParameters: string) {
    const res = await fetch(endpointAndParameters, { method: "GET" });
    const data = await res.json();

    if (data) {
      visualiseData(data as IGraph);
    } else {
      console.log(res);
    }

    return res;
  }

  // --- Merging ---
  let merging = false;
  let previewingMerge = false;
  let selectedNodes = [];
  let similarity;

  function startSelecting() {
    merging = true;
  }

  async function previewMerge() {
    if (selectedNodes.length < 2) {
      alert("Please select at least two nodes to merge.");
      return;
    }

    merging = false;
    previewingMerge = true;

    // This and the similarity endpoint simply require a list of UUIDs
    const body = { uuids: selectedNodes.map((node) => node.__data__.id) };
    const request = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };

    const res = await fetch(ENDPOINT + "/merge/nodes", request);
    const data = await res.json();

    if (data) {
      visualiseData(data as IGraph);
      
      const resSimilarity = await fetch(ENDPOINT + "/merge/similarity", request);
      similarity = await resSimilarity.json();
    } else {
      networkError("Merging has failed");
    }
  }

  async function acceptMerge() {
    previewingMerge = false;

    // This time apply is true so the changes are pushed to the database
    const body = { uuids: selectedNodes.map((node) => node.__data__.id), apply: true };
    const request = { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
    await fetch(ENDPOINT + "/merge/nodes", request);

    selectedNodes = [];
    // Load models to view update
    loadModels();
  }

  function clearSelection() {
    merging = false;
    previewingMerge = false;

    selectedNodes = [];
    loadModels();
  }

  function networkError(beginning: String) {
    alert(beginning + " due to a network error. We recommend checking your internet connection, refreshing the page and trying again.");
  }

  // --- Suggested Merges ---
  let suggestingMerges = false;
  let suggestions = [];
  let suggestionIndex = 0;

  async function suggestMerges() {
    suggestingMerges = true;

    const res = await fetch(ENDPOINT + "TODO", { method: "GET" });
    const data = await res.json();

    if (data) {
      suggestions = data;
      suggestionIndex = 0;
    } else {
      networkError("Suggesting merges has failed")
    }
  }

  function nextSuggestion() {
    suggestionIndex++;

    // TODO: Hide all irrelevant nodes and links?
    // TODO: Highlight the two nodes
    // Show similarity
  }

  function acceptSuggestion() {
    // TODO: Send request to server
    loadModels();
  }

  function endSuggestions() {
    suggestingMerges = false;
  }

  // --- Visualisation ---
  function resetStrokeWidth(circles) {
    for (const circle of circles) {
      let selected = circle.__data__.selected;
      // Larger stroke width for selected nodes
      d3.select(circle).attr("stroke-width", selected ? 3 : 1.5);
    }
  }

  function visualiseData(data: IGraph) {
    const links = [];

    // Simply rename the properties and remove the unnecessary ones for visualisation
    for (const relationship of data.relationships) {
      links.push({ source: relationship.start_node, target: relationship.end_node });
    }

    visualise(container.offsetWidth, container.offsetHeight, data.nodes, links);
  }

  // links type often changes
  function visualise(width: number, height: number, nodes: INode[], links: any[]) {
    modelsLoading = false;

    // Create the primary svg and container elements
    let svg = d3.create("svg");
    let g = svg.append("g");

    // On pans or zooms, apply the transform change to the main container
    svg.call(d3.zoom().on("zoom", (event) => {
      g.attr("transform", event.transform);
    }));

    // Create the container with the given nodes, links and force constants
    const simulation = d3
      .forceSimulation(nodes)
      // Keep linked nodes together
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(100),
      )
      // Repel nodes away from each other
      .force("charge", d3.forceManyBody().strength(-800))
      // Push nodes towards the center
      .force("x", d3.forceX())
      .force("y", d3.forceY())
      .on("tick", ticked);
    
      // (0, 0) is the center of the svg
      svg
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        .attr("style", "max-width: 100%; height: auto;");

    // This is used to set node colors according to a scheme
    const color = d3.scaleOrdinal(d3.schemeCategory10);

    // Add a line for each link
    const link = g
      .append("g")
      .attr("stroke", "#AAA")
      .attr("stroke-width", 4)
      .selectAll()
      .data(links)
      .join("line")
      .attr("class", "link");

    // Add all the nodes
    let node = g
      .append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll()
      .data(nodes)
      .join("g")
      .attr("class", "node");

    // Add the circle and text to each node element
    node
      .append("circle")
      .attr("r", 25)
      .attr("fill", (d) => color(d.label))
      .style("cursor", "pointer")
      .on("click", clicked);
    node
      .append("text")
      .text((d) => filterName(d.properties.name))
      .attr("fill", "#fff")
      .style("font-size", "25px");

    function clicked(event) {
      const data_object = event.target.__data__;

      // Allow properties to be viewed in the inspector
      properties = data_object.properties;
      properties["label"] = data_object.label;

      // Toggle selection
      if (merging) {
        data_object.selected = !data_object.selected;
        if (data_object.selected) {
          selectedNodes.push(event.target);
        } else {
          selectedNodes.splice(selectedNodes.indexOf(event.target), 1);
        }
        resetStrokeWidth([event.target]);
      }
    }

    function filterName(name: string) {
      return name.length <= 9 ? name : name.substring(0, 9) + "...";
    }

    // Set the position attributes of links and nodes each time the simulation ticks
    function ticked() {
      link
        .attr("x1", (d) => d.source.x)
        .attr("y1", (d) => d.source.y)
        .attr("x2", (d) => d.target.x)
        .attr("y2", (d) => d.target.y);

      node.attr("transform", (d) => `translate(${d.x}, ${d.y})`);
    }

    node.call(d3.drag().on("start", dragstarted).on("drag", dragged).on("end", dragended));

    // Reheat the simulation when drag starts, and fix the node's position
    function dragstarted(event) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    // Update the node's position
    function dragged(event) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    // Restore the target alpha so the simulation cools after dragging ends, and unfix position
    function dragended(event) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    // Remove previous graph and add graph to the DOM
    container.innerHTML = "";
    container.appendChild(svg.node()!);
  }

  // --- Upload Model ---
  let uploadModelModal: HTMLDialogElement;
  function showUploadModelModal() {
    uploadModelModal.showModal();
  }

  let uploadFilesInput: HTMLInputElement;

  async function uploadModel() {
    const files = uploadFilesInput.files;
    if (!files) return;

    // Simply upload each file one at a time as form data
    const endpoint = ENDPOINT + "/model/upload";
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      await fetch(endpoint, { method: "POST", body: formData });
    }

    // Clears the file list
    uploadFilesInput.value = "";

    uploadModelModal.close();
    loadModels();
  }

  // --- Change Schema ---
  let changeSchemaModal: HTMLDialogElement;
  function showChangeSchemaModal() {
    changeSchemaModal.showModal();
  }

  let changeSchemaInput: HTMLInputElement;

  async function changeSchema() {
    const files = changeSchemaInput.files;
    if (!files) return;

    const endpoint = ENDPOINT + "/model/upload-schema";
    const formData = new FormData();
    formData.append("file", files[0]);
    await fetch(endpoint, { method: "POST", body: formData });

    // Clears the file list
    changeSchemaInput.value = "";

    changeSchemaModal.close();
  }

  // --- Clear Models ---
  async function clearModels() {
    await fetch(ENDPOINT + "/model/all", { method: "DELETE" });
    container.innerHTML = "";
  }

  // --- Query by Name ---
  let queryByNameModal: HTMLDialogElement;
  function showQueryByNameModal() {
    queryByNameModal.showModal();
  }

  let queryName = "";

  async function queryByName() {
    if (!queryName) {
      return;
    }

    const endpoint = `${ENDPOINT}/model/by-name/${queryName}`;
    await visualiseFromEndpoint(endpoint);
  }

  // --- Query by Node ---
  let queryByNodeModal: HTMLDialogElement;
  function showQueryByNodeModal() {
    queryByNodeModal.showModal();
  }

  let queryLabel = "";
  let queryProperty = "";
  let queryValue = "";

  async function queryByNode() {
    if (!queryLabel && !queryProperty && !queryValue) {
      return;
    }

    const paramNames = ["label", "property", "value"];
    const paramValues = [queryLabel, queryProperty, queryValue];

    // Add all the parameters with the proper formatting
    let params = new URLSearchParams();
    for (let i = 0; i < 3; i++) {
      if (paramValues[i]) {
        params.append(paramNames[i], paramValues[i]);
      }
    }

    const endpoint = `${ENDPOINT}/model/by-node?${params.toString()}`;
    await visualiseFromEndpoint(endpoint);
  }

  // --- Arbitrary Query ---
  let arbQueryModal: HTMLDialogElement;
  function showArbQueryModal() {
    arbQueryModal.showModal();
  }

  let arbQueryValue: string;

  async function arbQuery() {
    if (!arbQueryValue) {
      return;
    }

    let params = new URLSearchParams();
    params.append("q", arbQueryValue);
    const endpoint = `${ENDPOINT}/query/graph?${params.toString()}`;
    await visualiseFromEndpoint(endpoint);
  }
</script>

<div class="flex flex h-full">
  <!-- Left Drawer -->
  <div class="bg-base-200 h-full w-2/6 space-y-4 p-4">
    {#if !merging && !previewingMerge && !suggestingMerges}
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" checked="checked" />
      <div class="collapse-title text-xl font-medium">Visualisation</div>
      <div class="collapse-content flex flex-col">
        <button class="btn" on:click={loadModels}>Visualise Models</button>
      </div>
    </div>
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" />
      <div class="collapse-title text-xl font-medium">Uploading</div>
      <div class="collapse-content space-y-4 flex flex-col">
        <button class="btn" on:click={showUploadModelModal}>Upload Model</button>
        <dialog bind:this={uploadModelModal} class="modal">
          <div class="modal-box">
            <form method="dialog">
              <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold">Upload Model</h3>
            <p class="py-4">Please select an SBML file.</p>
            <input
              bind:this={uploadFilesInput}
              type="file"
              multiple
              class="file-input file-input-bordered mx-4 w-full max-w-xs"
            />
            <button class="btn" on:click={uploadModel}>Upload</button>
          </div>
        </dialog>

        <button class="btn" on:click={showChangeSchemaModal}>Change Schema</button>
        <dialog bind:this={changeSchemaModal} class="modal">
          <div class="modal-box">
            <form method="dialog">
              <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold">Change Schema</h3>
            <p class="py-4">Please select a schema.</p>
            <input
              bind:this={changeSchemaInput}
              type="file"
              class="file-input file-input-bordered mx-4 w-full max-w-xs"
            />
            <button class="btn" on:click={changeSchema}>Upload</button>
          </div>
        </dialog>
      </div>
    </div>
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" />
      <div class="collapse-title text-xl font-medium">Deletion</div>
      <div class="collapse-content flex flex-col">
        <button class="btn" on:click={clearModels}>Clear Models</button>
      </div>
    </div>
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" />
      <div class="collapse-title text-xl font-medium">Queries</div>
      <div class="collapse-content space-y-4 flex flex-col">
        <!-- Query by Name -->
        <button class="btn" on:click={showQueryByNameModal}>Query by Model Name</button>
        <dialog bind:this={queryByNameModal} class="modal">
          <div class="modal-box">
            <form method="dialog">
              <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold">Query by Name</h3>
            <p class="py-4">The name must be provided.</p>
            <div class="space-y-4">
              <label class="input input-bordered flex items-center gap-2">
                Name
                <input type="text" class="grow" placeholder="COVID-HEAT" bind:value={queryName} />
              </label>
              <button class="btn" on:click={queryByName}>Query Model</button>
            </div>
          </div>
        </dialog>

        <!-- Query by Node -->
        <button class="btn" on:click={showQueryByNodeModal}>Query by Node</button>
        <dialog bind:this={queryByNodeModal} class="modal">
          <div class="modal-box">
            <form method="dialog">
              <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold">Query by Node</h3>
            <p class="py-4">At least one field must be provided.</p>
            <div class="space-y-4">
              <label class="input input-bordered flex items-center gap-2">
                Label
                <input type="text" class="grow" placeholder="species" bind:value={queryLabel} />
              </label>
              <label class="input input-bordered flex items-center gap-2">
                Property
                <input type="text" class="grow" placeholder="name" bind:value={queryProperty} />
              </label>
              <label class="input input-bordered flex items-center gap-2">
                Value
                <input type="text" class="grow" placeholder="recovered" bind:value={queryValue} />
              </label>
              <button class="btn" on:click={() => queryByNode()}>Query Models</button>
            </div>
          </div>
        </dialog>

        <!-- Arbitrary Query -->
        <button class="btn" on:click={showArbQueryModal}>Arbitrary Query</button>
        <dialog bind:this={arbQueryModal} class="modal">
          <div class="modal-box">
            <form method="dialog">
              <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
            </form>
            <h3 class="text-lg font-bold">Arbitrary Query</h3>
            <p class="py-4">The query must return a subset of the database.</p>
            <div class="space-y-4">
              <textarea
                bind:value={arbQueryValue}
                class="textarea textarea-bordered w-full"
                placeholder="Query"
              ></textarea>
              <button class="btn" on:click={arbQuery}>Execute Query</button>
            </div>
          </div>
        </dialog>
      </div>
    </div>
    {/if}
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" />
      <div class="collapse-title text-xl font-medium">Merging</div>
      <div class="collapse-content space-y-4 flex flex-col">
        {#if !merging && !previewingMerge && !suggestingMerges}
        <button class="btn" on:click={startSelecting}>Start Merge</button>
        <button class="btn" on:click={suggestMerges}>Suggest Merges</button>
        {:else}
          {#if !suggestingMerges}
            {#if !previewingMerge}
              <p>Click on a node to select it for merging.</p>
              <button class="btn" on:click={previewMerge}>Preview Merge</button>
            {:else}
              {#if similarity}
                <p>Similarity: {similarity}</p>
              {/if}
              <button class="btn" on:click={acceptMerge}>Accept Merge</button>
            {/if}
            <button class="btn" on:click={clearSelection}>Reset</button>
          {:else}
            <button class="btn" on:click={nextSuggestion}>Next Suggestion</button>
            <button class="btn" on:click={acceptSuggestion}>Accept Suggestion</button>
            <button class="btn" on:click={endSuggestions}>End Suggestions</button>
          {/if}
        {/if}
      </div>
    </div>
  </div>

  <!-- Visualisation -->
  <div class="flex h-full w-full" bind:this={container}>
    {#if modelsLoading}
      <div class="m-auto">
        <span class="loading loading-spinner loading-lg"></span>
      </div>
    {/if}
  </div>

  <!-- Right Drawer -->
  <div class="bg-base-200 menu max-h-full h-full w-2/6 min-h-0 overflow-y-auto">
    {#if Object.keys(properties).length == 0}
      <li><p>Click a node to view its properties</p></li>
    {:else}
      <li><p class="text-lg">Properties</p></li>
      {#each Object.entries(properties) as [key, value]}
        {#if key != "annotation"}
          <li><p class="break-all select-text">{key.charAt(0).toUpperCase() + key.slice(1)}: {value}</p></li>
        {/if}
      {/each}
    {/if}
  </div>
</div>
