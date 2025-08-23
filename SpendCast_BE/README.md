# SpendCast Backend

Financial Data Management System with GraphDB SPARQL API and AI Chat Capabilities.

## Features

- FastAPI-based REST API
- LangGraph AI agent integration
- Both streaming and non-streaming chat endpoints
- Financial data management (customers, accounts, transactions)
- PostgreSQL database integration

## API Endpoints

### Chat with AI Agent

#### Non-streaming Chat
- **POST** `/api/v1/agent/chat`
- Returns complete response at once

```json
{
  "message": "What are my recent transactions?"
}
```

Response:
```json
{
  "response": "Here are your recent transactions...",
  "success": true,
  "error": null
}
```

#### Streaming Chat
- **POST** `/api/v1/agent/chat/stream`
- Returns response incrementally as it's generated
- Uses Server-Sent Events format

Request:
```json
{
  "message": "Analyze my spending patterns"
}
```

Response: Text stream with JSON data chunks:
```
data: {"content": "I'll analyze", "type": "message"}

data: {"content": " your spending patterns...", "type": "message"}

data: {"type": "end"}
```

## Frontend Integration Examples

### Option 1: Fetch API with ReadableStream

```javascript
async function streamChat(message) {
  const response = await fetch('/api/v1/agent/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    const lines = chunk.split('\n');
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'message') {
          // Append data.content to your chat UI
          appendToChat(data.content);
        } else if (data.type === 'end') {
          // Stream finished
          break;
        }
      }
    }
  }
}
```

### Option 2: ReadableStream Processing

```javascript
function streamChatWithEventSource(message) {
  fetch('/api/v1/agent/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message })
  }).then(response => {
    const reader = response.body.getReader();
    return new ReadableStream({
      start(controller) {
        function pump() {
          return reader.read().then(({ done, value }) => {
            if (done) {
              controller.close();
              return;
            }
            const chunk = new TextDecoder().decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
              if (line.startsWith('data: ')) {
                const data = JSON.parse(line.slice(6));
                if (data.type === 'message') {
                  displayStreamingText(data.content);
                }
              }
            }
            
            controller.enqueue(value);
            return pump();
          });
        }
        return pump();
      }
    });
  });
}
```

## Development

### Running the Application

```bash
# Install dependencies
uv install

# Run the server
uvicorn main:app --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/unit/test_streaming.py
```

## Configuration

Set environment variables in `.env` file:

```bash
DATABASE_URL=postgresql://user:password@localhost/spendcast
MCP_SERVER_COMMAND=path/to/mcp/server
MCP_SERVER_ARGS=["--arg1", "--arg2"]
```