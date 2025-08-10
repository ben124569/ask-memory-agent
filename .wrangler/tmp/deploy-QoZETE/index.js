var __defProp = Object.defineProperty;
var __name = (target, value) => __defProp(target, "name", { value, configurable: true });

// src/index.js
var index_default = {
  async fetch(request, env, ctx) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: {
          "Access-Control-Allow-Origin": "*",
          "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
          "Access-Control-Allow-Headers": "Content-Type, Authorization"
        }
      });
    }
    const url = new URL(request.url);
    if (url.pathname === "/health") {
      return Response.json({
        status: "healthy",
        openai: env.OPENAI_API_KEY ? "connected" : "not configured",
        neo4j: env.NEO4J_URI ? "configured" : "not configured",
        timestamp: (/* @__PURE__ */ new Date()).toISOString()
      });
    }
    if (url.pathname === "/") {
      return Response.json({
        name: "Ask Memory Agent",
        version: "1.0.0",
        type: "mcp",
        endpoint: "/mcp"
      });
    }
    if (url.pathname === "/mcp" && request.method === "POST") {
      try {
        const body = await request.json();
        const response = await handleMCP(body, env);
        return Response.json(response, {
          headers: {
            "Access-Control-Allow-Origin": "*",
            "Content-Type": "application/json"
          }
        });
      } catch (error) {
        return Response.json({
          jsonrpc: "2.0",
          error: { code: -32603, message: error.message },
          id: null
        }, { status: 500 });
      }
    }
    return new Response("Not Found", { status: 404 });
  }
};
async function handleMCP(body, env) {
  const { method, params = {}, id } = body;
  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      result: {
        protocolVersion: "0.1.0",
        capabilities: { tools: {}, prompts: {} }
      },
      id
    };
  }
  if (method === "tools/list") {
    return {
      jsonrpc: "2.0",
      result: {
        tools: [
          {
            name: "ask_memory",
            description: "Ask intelligent questions about your stored memory using ChatGPT analysis",
            inputSchema: {
              type: "object",
              properties: {
                question: {
                  type: "string",
                  description: "Question about your memory, projects, people, etc."
                }
              },
              required: ["question"]
            }
          },
          {
            name: "store_memory",
            description: "Store new information in your memory",
            inputSchema: {
              type: "object",
              properties: {
                key: {
                  type: "string",
                  description: "Key to store the information under"
                },
                value: {
                  type: "string",
                  description: "Information to store"
                }
              },
              required: ["key", "value"]
            }
          },
          {
            name: "search_memory",
            description: "Search stored memories",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "Search term"
                }
              },
              required: ["query"]
            }
          }
        ]
      },
      id
    };
  }
  if (method === "tools/call") {
    const { name, arguments: args = {} } = params;
    if (name === "ask_memory") {
      const question = args.question || "";
      const response = await askMemoryWithAI(question, env);
      return {
        jsonrpc: "2.0",
        result: {
          content: [{ type: "text", text: response }]
        },
        id
      };
    }
    if (name === "store_memory") {
      const { key, value } = args;
      if (!key || !value) {
        return {
          jsonrpc: "2.0",
          result: {
            content: [{ type: "text", text: "\u274C Both key and value are required" }]
          },
          id
        };
      }
      await env.MEMORY_KV.put(key, value);
      return {
        jsonrpc: "2.0",
        result: {
          content: [{ type: "text", text: `\u2705 Stored memory: ${key}` }]
        },
        id
      };
    }
    if (name === "search_memory") {
      const query = args.query || "";
      const results = await searchMemories(query, env);
      return {
        jsonrpc: "2.0",
        result: {
          content: [{ type: "text", text: results }]
        },
        id
      };
    }
    return {
      jsonrpc: "2.0",
      error: { code: -32601, message: `Unknown tool: ${name}` },
      id
    };
  }
  return {
    jsonrpc: "2.0",
    error: { code: -32601, message: `Unknown method: ${method}` },
    id
  };
}
__name(handleMCP, "handleMCP");
async function askMemoryWithAI(question, env) {
  if (!question.trim()) {
    return "\u2753 Please ask a question about your memory.";
  }
  const searchResults = await searchMemories(question, env);
  const prompt = `
You are a helpful memory assistant. The user asked: "${question}"

Here's what I found in their stored memories:
${searchResults}

Provide a helpful, conversational response. If no relevant memories were found, suggest what kind of information would be useful to store about this topic.
  `;
  try {
    const response = await fetch("https://api.openai.com/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${env.OPENAI_API_KEY}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: env.OPENAI_MODEL || "gpt-5",
        messages: [{ role: "user", content: prompt }],
        max_tokens: 500,
        temperature: 0.7
      })
    });
    if (!response.ok) {
      throw new Error(`OpenAI API error: ${response.status}`);
    }
    const data = await response.json();
    return `\u{1F9E0} **Memory Query**: "${question}"

\u{1F4DD} **Response**: ${data.choices[0].message.content.trim()}`;
  } catch (error) {
    return `\u{1F9E0} **Memory Query**: "${question}"

\u274C **AI Error**: ${error.message}

\u{1F4CB} **Found memories**: ${searchResults}`;
  }
}
__name(askMemoryWithAI, "askMemoryWithAI");
async function searchMemories(query, env) {
  try {
    const list = await env.MEMORY_KV.list();
    const results = [];
    for (const key of list.keys) {
      const value = await env.MEMORY_KV.get(key.name);
      if (value && (key.name.toLowerCase().includes(query.toLowerCase()) || value.toLowerCase().includes(query.toLowerCase()))) {
        results.push(`\u2022 ${key.name}: ${value}`);
      }
    }
    if (results.length === 0) {
      return `No memories found matching "${query}"`;
    }
    return `Found ${results.length} memories:
${results.join("\n")}`;
  } catch (error) {
    return `Search error: ${error.message}`;
  }
}
__name(searchMemories, "searchMemories");
export {
  index_default as default
};
//# sourceMappingURL=index.js.map
