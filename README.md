# Ask Memory Agent

AI-powered memory assistant with Neo4j integration.

## Features
- Ask intelligent questions about your stored memory
- Create and manage entities (people, projects, notes)
- Add relationships between entities
- Search your knowledge graph

## Deploy to Railway
1. Connect this repo to Railway
2. Add environment variables:
   - `OPENAI_API_KEY` - Your OpenAI API key
   - `OPENAI_MODEL` - `gpt-4o` (latest model)
3. Deploy!

## Usage
Add to Claude app: `https://your-app.railway.app/mcp`

Available tools:
- `ask_memory` - Ask questions about your memory
- `create_entity` - Add new people/projects/notes
- `add_relationship` - Connect entities
- `search_entities` - Find stuff in your memory
- `update_entity` - Update existing memories