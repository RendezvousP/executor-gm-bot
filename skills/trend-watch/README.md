## Search Trends Explorer

This project combines a Google Trends visualizer built with Next.js and a Model Context Protocol (MCP) server that exposes the same data as a tool you can connect to OpenAI or any MCP-compatible client. Both experiences call [SearchAPI.io](https://www.searchapi.io/docs/google-trends) to retrieve the last 12 months of relative interest for a search term.

### Prerequisites

- Node.js 18.18+ (recommended to avoid engine warnings)
- A `SEARCH_API_KEY` from [SearchAPI.io](https://www.searchapi.io/)

Create a `.env` file with:

```bash
SEARCH_API_KEY=your_key_here
```

### Running the Next.js UI

```bash
npm install
npm run dev
```

Visit `http://localhost:3000` to use the web interface.

### Running the MCP Server

The MCP server exposes a single tool named `fetch_google_trends` over streamable HTTP.

```bash
npm install
npm run mcp:dev
```

The server listens on `http://localhost:3000/mcp` (honors the `PORT` env variable) and also serves `GET /healthz` for Render health checks.

#### Connecting from an MCP client

- **MCP Inspector:** `npx @modelcontextprotocol/inspector --server http://localhost:3000/mcp`
- **OpenAI / other agents:** add an HTTP MCP tool pointing to the same `/mcp` endpoint.

When invoked, `fetch_google_trends` expects a JSON payload:

```json
{
  "term": "electric cars",
  "geo": "US",            // optional Google Trends geo code
  "category": "0"         // optional Google Trends category id
}
```

The tool responds with structured JSON containing the normalized timeline points.

### Deploying the MCP server to Render.com

1. Create a new **Web Service** from this repository.
2. Set the start command to:
   ```bash
   npm run mcp:start
   ```
3. Add the environment variable `SEARCH_API_KEY`.
4. (Optional) Configure Render health checks to hit `/healthz`.

Render will inject `PORT`, which the server automatically respects.

### Testing & Linting

```bash
npm run lint
```

### Project Structure Highlights

- `app/` – Next.js app router with UI and `/api/trends` endpoint.
- `lib/trends.ts` – Shared SearchAPI client used by both the API route and MCP tool.
- `mcp/server.ts` – Express + MCP server exposing the `fetch_google_trends` tool.
