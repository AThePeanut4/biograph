<script lang="ts">
  export let container: HTMLElement;

  import Graph from "graphology";
  import forceAtlas2 from "graphology-layout-forceatlas2";

  let sigma: import("sigma").Sigma;

  import { onMount } from "svelte";
  onMount(async () => {
    const Sigma = (await import("sigma")).Sigma;
    // Instantiate sigma.js with an empty graph
    sigma = new Sigma(new Graph(), container);
  });

  // TODO: Best way to do this?
  const ENDPOINT = "https://elgoog.co.za/api";
  const NODE_SIZE = 5;
  const EDGE_SIZE = 3;
  const FORCE_ITERATIONS = 20;

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

  function visualiseData(data: IGraph) {
    // Create a graphology graph
    const graph = new Graph();

    let seenLabels = [];
    const colours = ["#45F0DF", "#C2CAE8", "#942911", "#FDCA40", "#FE5D26", "#297373", "#F7FF58"];

    // // This randomises the order of the colour palette
    // let currentIndex = colours.length;
    // while (currentIndex != 0) {
    //   let randomIndex = Math.floor(Math.random() * currentIndex);
    //   currentIndex--;
    //
    //   [colours[currentIndex], colours[randomIndex]] = [colours[randomIndex], colours[currentIndex]];
    // }

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

    // display the graph
    sigma.setGraph(graph);
  }

  async function visualiseFromEndpoint(endpointAndParameters: string) {
    if (!endpointAndParameters.includes("?")) {
      endpointAndParameters += "/";
    }

    const res = await fetch(endpointAndParameters, { method: "GET" });
    const data = await res.json();

    if (data) {
      visualiseData(data as IGraph);
    }
  }

  // --- Load Models ---
  async function loadModels() {
    await visualiseFromEndpoint(ENDPOINT + "/model");
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

    // clears the file list
    uploadFilesInput.value = "";
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

<div class="navbar flex content-center bg-base-100 text-center">
  <div class="m-auto space-x-8 text-center">
    <button class="btn" on:click={() => loadModels()}>Load Models</button>

    <button class="btn" on:click={() => showUploadModelModal()}>Upload Model</button>
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
        <button class="btn" on:click={() => uploadModel()}>Upload</button>
      </div>
    </dialog>

    <button class="btn" on:click={() => showQueryByNameModal()}>Query by Name</button>
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
          <button class="btn" on:click={() => queryByName()}>Query Model</button>
        </div>
      </div>
    </dialog>

    <button class="btn" on:click={() => showQueryByNodeModal()}>Query by Node</button>
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

    <button class="btn" on:click={() => showArbQueryModal()}>Arbitrary Query</button>
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
          <button class="btn" on:click={() => arbQuery()}>Execute Query</button>
        </div>
      </div>
    </dialog>
  </div>
</div>
