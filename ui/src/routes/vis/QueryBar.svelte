<script lang="ts">
  import Graph from "graphology";
  import forceAtlas2 from "graphology-layout-forceatlas2";
  import Sigma from "sigma";

  // TODO: Best way to do this?
  const ENDPOINT = "https://elgoog.co.za/api";
  const NODE_SIZE = 5;
  const EDGE_SIZE = 3;
  const FORCE_ITERATIONS = 20;

  function visualiseData(data: object) {
    let container = document.getElementById("container")!;
    container.innerHTML = "";

    // Create a graphology graph
    const graph = new Graph();

    let seenLabels = [];
    const colours = ["#45F0DF", "#C2CAE8", "#942911", "#FDCA40", "#FE5D26", "#297373", "#F7FF58"];

    /* This randomises the order of the colour palette
		let currentIndex = colours.length;
		while (currentIndex != 0) {
			let randomIndex = Math.floor(Math.random() * currentIndex);
			currentIndex--;

			[colours[currentIndex], colours[randomIndex]] = [colours[randomIndex], colours[currentIndex]];
		}*/

    for (const node of data.nodes) {
      const x = Math.floor(Math.random() * 150);
      const y = Math.floor(Math.random() * 50);

      let color = "#111D4A";
      if (seenLabels.indexOf(node.label) != -1) {
        color = colours[seenLabels.indexOf(node.label)];
      } else if (seenLabels.length < colours.length) {
        seenLabels.push(node.label);
      }

      const label = `${node.label} - ${node.properties.name}`;
      graph.addNode(node.id, { label, size: NODE_SIZE, x, y, color });
    }

    for (const edge of data.relationships) {
      graph.addEdge(edge.start_node, edge.end_node, { size: EDGE_SIZE });
    }

    forceAtlas2.assign(graph, FORCE_ITERATIONS);

    // Instantiate sigma.js and render the graph
    const sigmaInstance = new Sigma(graph, container);
  }

  async function visualiseFromEndpoint(endpointAndParameters: string) {
    if (!endpointAndParameters.includes("?")) {
      endpointAndParameters += "/";
    }

    const res = await fetch(endpointAndParameters, { method: "GET" });
    const data = await res.json();

    if (data) {
      visualiseData(data);
    }
  }

  // --- Load Models ---
  async function loadModels() {
    await visualiseFromEndpoint(ENDPOINT + "/model");
  }

  // --- Upload Model ---
  let files;

  async function uploadModel() {
    const endpoint = ENDPOINT + "/model/upload";
    for (const file of files) {
      const formData = new FormData();
      formData.append("file", file);
      await fetch(endpoint, { method: "POST", body: formData });
    }

    // TODO: Do the files need to flushed here?
    files = null;
  }

  // --- Query by Name ---
  let queryName = "";

  async function queryByName() {
    if (!queryName) {
      return;
    }

    const endpoint = `${ENDPOINT}/model/by-name/${queryName}`;
    await visualiseFromEndpoint(endpoint);
  }

  // --- Query by Node ---
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
  let arbQueryValue;

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

<div class="navbar flex content-center bg-base-100 text-center">
  <div class="m-auto space-x-8 text-center">
    <button class="btn" on:click={() => loadModels()}>Load Models</button>

    <button class="btn" onclick="upload_model_modal.showModal()">Upload Model</button>
    <dialog id="upload_model_modal" class="modal">
      <div class="modal-box">
        <form method="dialog">
          <button class="btn btn-circle btn-ghost btn-sm absolute right-2 top-2">✕</button>
        </form>
        <h3 class="text-lg font-bold">Upload Model</h3>
        <p class="py-4">Please select an SBML file.</p>
        <input bind:files type="file" class="file-input file-input-bordered mx-4 w-full max-w-xs" />
        <button class="btn" on:click={() => uploadModel()}>Upload</button>
      </div>
    </dialog>

    <button class="btn" onclick="query_by_name_modal.showModal()">Query by Name</button>
    <dialog id="query_by_name_modal" class="modal">
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
          <button class="btn" on:click={() => queryByName()}>Query Model</button>
        </div>
      </div>
    </dialog>

    <button class="btn" onclick="query_by_node_modal.showModal()">Query by Node</button>
    <dialog id="query_by_node_modal" class="modal">
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

    <button class="btn" onclick="arb_query_modal.showModal()">Arbitrary Query</button>
    <dialog id="arb_query_modal" class="modal">
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
          <button class="btn" on:click={() => arbQuery()}>Execute Query</button>
        </div>
      </div>
    </dialog>
  </div>
</div>
