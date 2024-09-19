<script lang="ts">
  /*
    TODO:
    1. Mark nodes for merging
    2. Report loading errors
    3. Fix first page
    4. Search by property values in inspector?
    5. Second visualising pane?
  */

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

  // TODO: Is this necessary?
  interface ILink {
    source: string;
    target: string;
  }

  // This is the div that contains the visualisation
  let container: HTMLElement;
  let modelsLoading = false;
  let modelsLoaded = false;
  // These are the properties of a selected node in a graph
  let properties = {};

  // --- Load Models ---
  async function loadModels() {
    // TODO: Do we want the user to loadModels more than once?
    if (modelsLoaded) return;
    modelsLoaded = true;
    modelsLoading = true;

    const res = await visualiseFromEndpoint(ENDPOINT + "/model");
    if (!res.ok) {
      // TODO: Report error
    }
  }

  async function visualiseFromEndpoint(endpointAndParameters: string) {
    // The server requires a trailing slash
    if (!endpointAndParameters.includes("?")) {
      endpointAndParameters += "/";
    }

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
  let selectedNodes = [];

  // TODO
  function startSelecting() {
    merging = true;
  }

  function merge() {
    merging = false;
    // TODO: Loop through all elements of selectedNodes and remove nodes and links
    selectedNodes = [];
  }

  function clearSelection() {
    merging = false;
    selectedNodes = [];
  }

  // --- Visualisation ---
  function visualiseData(data: IGraph) {
    const links = [];

    // Simply rename the properties and remove the unnecessary ones for visualisation
    for (const relationship of data.relationships) {
      links.push({ source: relationship.start_node, target: relationship.end_node });
    }

    // TODO: Correct width and height?
    visualise(container.offsetWidth, container.offsetHeight, data.nodes, links);
  }

  function visualise(width: number, height: number, nodes: INode[], links: ILink[]) {
    modelsLoading = false;

    let svg = d3.create("svg");
    let g = svg.append("g");

    svg.call(d3.zoom().on("zoom", (event) => {
      g.attr("transform", event.transform);
    }));

    // TODO: Are the constants here reasonable?
    // TODO: Move them to the top of the file?
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        "link",
        d3
          .forceLink(links)
          .id((d) => d.id)
          .distance(100),
      )
      .force("charge", d3.forceManyBody().strength(-200))
      // TODO: width / 2?
      .force("x", d3.forceX())
      // TODO: height / 2?
      .force("y", d3.forceY())
      .on("tick", ticked);
    
      svg
        .attr("viewBox", [-width / 2, -height / 2, width, height])
        // TODO: Necessary?
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
      .join("line");

    // Add all the nodes
    let node = g
      .append("g")
      .attr("stroke", "#fff")
      .attr("stroke-width", 1.5)
      .selectAll()
      .data(nodes)
      .join("g");

    node
      .append("circle")
      .attr("r", 15)
      .attr("fill", (d) => color(d.label))
      // Setting the properties means they will be displayed in the right drawer
      .on("click", clicked);
    node
      .append("text")
      .text((d) => filterName(d.properties.name))
      .style("font-size", "15px");

    function clicked(event) {
      const data_object = event.target.__data__;

      // Allow properties to be viewed in the inspector
      properties = data_object.properties;

      // TODO
      data_object.selected = !data_object.selected;
      if (!selectedNodes.includes(event.target)) {
        selectedNodes.push(event.target);
      }
      console.log(selectedNodes);
      resetStrokeWidth(selectedNodes);
    }

    function resetStrokeWidth(circles) {
      for (const circle of circles) {
        let selected = circle.__data__.selected;
        d3.select(circle).attr("stroke-width", selected ? 3 : 1.5);
      }
    }

    function filterName(name: string) {
      return name.length <= 12 ? name : name.substring(0, 12) + "...";
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

    // TODO: Why is this necessary
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

    const endpoint = ENDPOINT + "/model/upload";
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      await fetch(endpoint, { method: "POST", body: formData });
    }

    // Clears the file list
    uploadFilesInput.value = "";
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

    // TODO: This endpoint hasn't been created
    console.log("UNIMPLEMENTED");
    return 

    const endpoint = ENDPOINT + "/schema/upload";
    const formData = new FormData();
    formData.append("file", files[0]);
    await fetch(endpoint, { method: "POST", body: formData });

    // Clears the file list
    changeSchemaInput.value = "";
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
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" checked="checked" />
      <div class="collapse-title text-xl font-medium">Loading</div>
      <div class="collapse-content flex flex-col">
        <button class="btn" on:click={loadModels}>Load Models</button>
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
      <div class="collapse-title text-xl font-medium">Queries</div>
      <div class="collapse-content space-y-4 flex flex-col">
        <!-- Query by Name -->
        <button class="btn" on:click={showQueryByNameModal}>Query by Name</button>
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
    <div class="bg-base-100 collapse">
      <input type="radio" name="my-accordion-1" />
      <div class="collapse-title text-xl font-medium">Merging</div>
      <div class="collapse-content space-y-4 flex flex-col">
        <button class="btn" on:click={startSelecting}>Start Selecting</button>
        <button class="btn" on:click={merge}>Merge</button>
        <button class="btn" on:click={clearSelection}>Clear Selection</button>
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
  <div class="bg-base-200 menu h-full w-2/6">
    {#if Object.keys(properties).length == 0}
      <li><p>Click a node to view its properties</p></li>
    {:else}
      <li><p class="text-lg">Properties</p></li>
      {#each Object.entries(properties) as [key, value]}
        <li><p class="break-all">{key.charAt(0).toUpperCase() + key.slice(1)}: {value}</p></li>
      {/each}
    {/if}
    {#if merging}
      <li><p class="text-lg text-red-500">Merging!</p></li>
    {/if}
  </div>
</div>
