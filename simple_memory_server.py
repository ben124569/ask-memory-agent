#!/usr/bin/env python3
"""
Simple Memory MCP Server
- Ask memory agent (ChatGPT + Neo4j search)
- Basic Neo4j commands to manage memories
"""

import os
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

try:
    from neo4j import GraphDatabase
    HAS_NEO4J = True
except ImportError:
    HAS_NEO4J = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

# Load environment
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(title="Simple Memory MCP", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global connections
neo4j_driver = None
openai_client = None

def init_connections():
    global neo4j_driver, openai_client
    
    # Neo4j
    if HAS_NEO4J:
        neo4j_uri = os.getenv("NEO4J_URI", "")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "")
        
        if neo4j_uri and neo4j_password:
            try:
                neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
                with neo4j_driver.session() as session:
                    session.run("RETURN 1")
                logger.info("✅ Neo4j connected")
            except Exception as e:
                logger.warning(f"Neo4j failed: {e}")
    
    # OpenAI
    if HAS_OPENAI:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            try:
                openai_client = OpenAI(api_key=openai_api_key)
                logger.info("✅ OpenAI connected")
            except Exception as e:
                logger.error(f"OpenAI failed: {e}")

init_connections()

# MCP Models
class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = {}
    id: Optional[Any] = None

class MCPResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

# Helper functions
def query_neo4j(query: str, params: Dict = None) -> List[Dict]:
    if not neo4j_driver:
        return []
    
    try:
        with neo4j_driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]
    except Exception as e:
        logger.error(f"Neo4j error: {e}")
        return []

async def ask_chatgpt(prompt: str, max_tokens: int = 500) -> str:
    if not openai_client:
        return "ChatGPT not available"
    
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"ChatGPT error: {str(e)}"

# Memory functions
async def ask_about_memory(question: str) -> str:
    if not question.strip():
        return "Please ask a question about your memory."
    
    response = f"🧠 **Memory Query**: '{question}'\n\n"
    
    if neo4j_driver:
        # Search Neo4j
        search_results = []
        search_terms = question.lower().split()[:3]
        
        for term in search_terms:
            cypher = """
            MATCH (n)
            WHERE ANY(prop IN keys(n) WHERE toString(n[prop]) =~ ('(?i).*' + $term + '.*'))
            RETURN labels(n) as labels, n as node
            LIMIT 5
            """
            
            results = query_neo4j(cypher, {"term": term})
            for result in results:
                labels = result.get('labels', [])
                node = result.get('node', {})
                search_results.append(f"{labels}: {dict(node)}")
        
        if search_results:
            # Use ChatGPT to analyze
            context_data = f"User Question: {question}\n\nFound in memory:\n"
            for result in search_results[:10]:
                context_data += f"- {result}\n"
            
            ai_prompt = f"""
            You are a helpful memory assistant. Based on this data from the user's knowledge graph:
            
            {context_data}
            
            Provide a helpful, conversational response to: "{question}"
            """
            
            ai_response = await ask_chatgpt(ai_prompt)
            response += f"📝 **Found**: {ai_response}"
        else:
            response += f"🔍 No specific data found for '{question}' in your memory database."
    else:
        response += "❌ Neo4j database not connected - cannot search memory."
    
    return response

# MCP Tools
TOOLS = [
    {
        "name": "ask_memory",
        "description": "Ask intelligent questions about your stored memory using ChatGPT analysis",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Question about your memory, projects, people, etc."
                }
            },
            "required": ["question"]
        }
    },
    {
        "name": "create_entity",
        "description": "Create a new entity (person, project, note, etc.) in your memory",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the entity"
                },
                "type": {
                    "type": "string",
                    "description": "Type of entity (Person, Project, Note, etc.)"
                },
                "properties": {
                    "type": "object",
                    "description": "Additional properties as key-value pairs"
                }
            },
            "required": ["name", "type"]
        }
    },
    {
        "name": "add_relationship",
        "description": "Create a relationship between two entities",
        "inputSchema": {
            "type": "object",
            "properties": {
                "from_name": {
                    "type": "string",
                    "description": "Name of the source entity"
                },
                "to_name": {
                    "type": "string",
                    "description": "Name of the target entity"
                },
                "relationship": {
                    "type": "string",
                    "description": "Type of relationship (KNOWS, WORKS_ON, RELATED_TO, etc.)"
                }
            },
            "required": ["from_name", "to_name", "relationship"]
        }
    },
    {
        "name": "search_entities",
        "description": "Search for entities in your memory database",
        "inputSchema": {
            "type": "object",
            "properties": {
                "search_term": {
                    "type": "string",
                    "description": "Term to search for"
                }
            },
            "required": ["search_term"]
        }
    },
    {
        "name": "update_entity",
        "description": "Update properties of an existing entity",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of entity to update"
                },
                "properties": {
                    "type": "object",
                    "description": "Properties to add/update"
                }
            },
            "required": ["name", "properties"]
        }
    }
]

# Routes
@app.get("/")
async def root():
    return {
        "name": "Simple Memory MCP",
        "version": "1.0.0",
        "features": {
            "neo4j": "connected" if neo4j_driver else "disconnected",
            "chatgpt": "connected" if openai_client else "disconnected"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "neo4j": neo4j_driver is not None,
        "openai": openai_client is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/mcp")
async def handle_mcp(request: Request):
    try:
        body = await request.json()
        mcp_req = MCPRequest(**body)
        
        if mcp_req.method == "initialize":
            result = {
                "protocolVersion": "0.1.0",
                "capabilities": {"tools": {}, "prompts": {}}
            }
            
        elif mcp_req.method == "tools/list":
            result = {"tools": TOOLS}
            
        elif mcp_req.method == "tools/call":
            tool_name = mcp_req.params.get("name")
            args = mcp_req.params.get("arguments", {})
            
            if tool_name == "ask_memory":
                question = args.get("question", "")
                text = await ask_about_memory(question)
                result = {"content": [{"type": "text", "text": text}]}
                
            elif tool_name == "create_entity":
                name = args.get("name", "")
                entity_type = args.get("type", "Entity")
                properties = args.get("properties", {})
                
                if not name:
                    text = "❌ Entity name is required"
                else:
                    # Create entity in Neo4j
                    cypher = f"""
                    MERGE (n:{entity_type} {{name: $name}})
                    SET n += $props
                    SET n.created = datetime()
                    SET n.updated = datetime()
                    RETURN n
                    """
                    
                    props = dict(properties)
                    props['name'] = name
                    
                    results = query_neo4j(cypher, {"name": name, "props": props})
                    
                    if results:
                        text = f"✅ Created {entity_type}: {name}"
                        if properties:
                            text += f" with properties: {properties}"
                    else:
                        text = f"❌ Failed to create entity: {name}"
                
                result = {"content": [{"type": "text", "text": text}]}
                
            elif tool_name == "add_relationship":
                from_name = args.get("from_name", "")
                to_name = args.get("to_name", "")
                relationship = args.get("relationship", "RELATED_TO")
                
                if not all([from_name, to_name]):
                    text = "❌ Both entity names are required"
                else:
                    cypher = f"""
                    MATCH (a {{name: $from_name}})
                    MATCH (b {{name: $to_name}})
                    MERGE (a)-[r:{relationship}]->(b)
                    SET r.created = datetime()
                    RETURN a.name, b.name, type(r)
                    """
                    
                    results = query_neo4j(cypher, {
                        "from_name": from_name,
                        "to_name": to_name
                    })
                    
                    if results:
                        text = f"✅ Created relationship: {from_name} -{relationship}-> {to_name}"
                    else:
                        text = f"❌ Failed to create relationship (entities might not exist)"
                
                result = {"content": [{"type": "text", "text": text}]}
                
            elif tool_name == "search_entities":
                search_term = args.get("search_term", "")
                
                if not search_term:
                    text = "❌ Search term is required"
                else:
                    cypher = """
                    MATCH (n)
                    WHERE toLower(n.name) CONTAINS toLower($term)
                       OR ANY(prop IN keys(n) WHERE toLower(toString(n[prop])) CONTAINS toLower($term))
                    RETURN labels(n) as labels, n as node
                    LIMIT 20
                    """
                    
                    results = query_neo4j(cypher, {"term": search_term})
                    
                    if results:
                        text = f"🔍 Found {len(results)} entities matching '{search_term}':\n\n"
                        for r in results:
                            labels = r['labels']
                            node = r['node']
                            name = node.get('name', 'Unnamed')
                            text += f"• {labels[0] if labels else 'Entity'}: {name}\n"
                            for key, value in node.items():
                                if key != 'name' and value:
                                    text += f"  - {key}: {value}\n"
                    else:
                        text = f"❌ No entities found matching '{search_term}'"
                
                result = {"content": [{"type": "text", "text": text}]}
                
            elif tool_name == "update_entity":
                name = args.get("name", "")
                properties = args.get("properties", {})
                
                if not name or not properties:
                    text = "❌ Entity name and properties are required"
                else:
                    cypher = """
                    MATCH (n {name: $name})
                    SET n += $props
                    SET n.updated = datetime()
                    RETURN n
                    """
                    
                    results = query_neo4j(cypher, {"name": name, "props": properties})
                    
                    if results:
                        text = f"✅ Updated {name} with: {properties}"
                    else:
                        text = f"❌ Entity '{name}' not found"
                
                result = {"content": [{"type": "text", "text": text}]}
                
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
                
        else:
            result = {"message": f"Method {mcp_req.method} not implemented"}
        
        return MCPResponse(jsonrpc="2.0", result=result, id=mcp_req.id).model_dump()
        
    except Exception as e:
        logger.error(f"Request error: {e}")
        return MCPResponse(
            jsonrpc="2.0",
            error={"code": -32603, "message": str(e)},
            id=body.get("id") if "body" in locals() else None
        ).model_dump()

@app.get("/tools")
async def list_tools():
    return {"tools": TOOLS}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8001))
    host = "0.0.0.0"
    
    print(f"\n🧠 Simple Memory MCP Server")
    print(f"📊 Neo4j: {'Connected' if neo4j_driver else 'Not connected'}")
    print(f"🤖 ChatGPT: {'Connected' if openai_client else 'Not connected'}")
    print(f"\n🌐 Running on port {port}")
    print(f"📱 MCP endpoint: /mcp\n")
    
    uvicorn.run(app, host=host, port=port)