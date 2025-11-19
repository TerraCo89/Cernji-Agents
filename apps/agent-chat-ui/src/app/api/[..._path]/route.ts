import { initApiPassthrough } from "langgraph-nextjs-api-passthrough";
import { getLogger } from "@/lib/logger";

// This file acts as a proxy for requests to your LangGraph server.
// Read the [Going to Production](https://github.com/langchain-ai/agent-chat-ui?tab=readme-ov-file#going-to-production) section for more information.

const logger = getLogger('api-passthrough');

// Log API configuration on startup
logger.info({
  apiUrl: process.env.LANGGRAPH_API_URL,
  hasApiKey: !!process.env.LANGSMITH_API_KEY,
}, 'API passthrough initialized');

export const { GET, POST, PUT, PATCH, DELETE, OPTIONS, runtime } =
  initApiPassthrough({
    apiUrl: process.env.LANGGRAPH_API_URL ?? "remove-me", // default, if not defined it will attempt to read process.env.LANGGRAPH_API_URL
    apiKey: process.env.LANGSMITH_API_KEY ?? "remove-me", // default, if not defined it will attempt to read process.env.LANGSMITH_API_KEY
    runtime: "edge", // default
  });
