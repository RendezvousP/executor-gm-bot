import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";
import { fetchTrendSeries, SearchApiError } from "../lib/trends";

const server = new McpServer(
  {
    name: "search-trends-mcp",
    version: "1.0.0",
    description:
      "Expose Google Trends interest-over-time data fetched via SearchAPI.io",
    websiteUrl: "https://www.searchapi.io/docs/google-trends",
  },
  {
    capabilities: {
      logging: {},
    },
  },
);

const toolInputSchema = {
  term: z.string().trim().min(1, "term must not be empty"),
  geo: z
    .string()
    .trim()
    .min(1, "geo must not be empty")
    .max(8, "geo looks too long")
    .optional(),
  category: z
    .string()
    .trim()
    .min(1, "category must not be empty")
    .max(8, "category looks too long")
    .optional(),
};

server.registerTool(
  "fetch_google_trends",
  {
    title: "Fetch Google Trends",
    description:
      "Fetch last 12 months of Google Trends relative interest for a single query term using SearchAPI.io.",
    inputSchema: toolInputSchema,
  },
  async ({ term, geo, category }) => {
    try {
      const points = await fetchTrendSeries({ term, geo, category });

      const summary = {
        term,
        geo: geo ?? null,
        category: category ?? null,
        points,
      };

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(summary, null, 2),
          },
        ],
        structuredContent: summary,
      };
    } catch (error) {
      if (error instanceof SearchApiError) {
        const payload = {
          error: error.message,
          status: error.status,
          details: error.details ?? null,
        };

        return {
          isError: true,
          content: [
            {
              type: "text",
              text: JSON.stringify(payload, null, 2),
            },
          ],
          structuredContent: payload,
        };
      }

      const message =
        error instanceof Error ? error.message : "Unknown server error.";

      return {
        isError: true,
        content: [
          {
            type: "text",
            text: JSON.stringify(
              {
                error: "Unexpected error while fetching trends.",
                details: message,
              },
              null,
              2,
            ),
          },
        ],
        structuredContent: {
          error: "Unexpected error while fetching trends.",
          details: message,
        },
      };
    }
  },
);

const app = express();
app.use(express.json());

app.get("/", (_req, res) => {
  res.json({
    name: "search-trends-mcp",
    status: "ok",
    endpoints: {
      mcp: "/mcp",
      health: "/healthz",
    },
  });
});

app.get("/healthz", (_req, res) => {
  res.json({ status: "ok" });
});

app.post("/mcp", async (req, res) => {
  // Stateless transport: explicitly disable session IDs for simple single-request flows
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });

  res.on("close", () => {
    transport.close();
  });

  try {
    await server.connect(transport);
    await transport.handleRequest(req, res, req.body);
  } catch (error) {
    console.error("Error handling MCP request:", error);
    if (!res.headersSent) {
      res.status(500).json({
        error: "Failed to handle MCP request.",
      });
    }
    transport.close();
  }
});

const port = Number.parseInt(process.env.PORT ?? "3000", 10);

app.listen(port, () => {
  console.log(
    `Search Trends MCP server running on http://localhost:${port}/mcp`,
  );
});
