# biograph

## Running the backend

1. Install [PDM](https://pdm-project.org/en/latest/#installation)
2. Run `pdm install` to set up a virtual environment and install dependencies
3. Create the necessary configuration files in the `config/` directory, using the example files for reference
4. Run `pdm run prod` to start the server in production mode, or run `pdm run dev` for dev mode

## Running the UI

1. Install [bun](https://bun.sh/)
2. `cd ui`
3. Run `bun install --frozen-lockfile` to install dependencies
4. Run `bun --bun run dev -- --open` to start the dev server and open the UI in a browser


## Development

start neo4j server

`neo4j console`

This will let you easily sig int the process for any reason, and view live db logs. It'll ask you to change credentials first...

### Venv

If you are a homebrew homie you may need env isolation

`source .venv/bin/activate`
