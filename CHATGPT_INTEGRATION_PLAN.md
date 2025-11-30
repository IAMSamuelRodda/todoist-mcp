# Todoist ChatGPT Integration Plan

## Executive Summary

This document plans the conversion of the Todoist MCP server into a ChatGPT-compatible integration, enabling free ChatGPT users to manage their Todoist tasks through a public GPT.

**Goal**: Allow anyone with a free ChatGPT account to use a public GPT that manages their personal Todoist account.

---

## Part 1: Protocol Comparison

### MCP vs ChatGPT Actions

| Aspect | MCP (Current) | ChatGPT Actions (Target) |
|--------|---------------|--------------------------|
| **Protocol** | stdio/SSE binary | HTTP REST API |
| **Schema** | MCP tool definitions | OpenAPI 3.0+ specification |
| **Runtime** | Local process | Cloud-hosted HTTP server |
| **Auth** | Environment variables | OAuth 2.0 or API Key header |
| **Vendor** | Open standard (Anthropic) | Proprietary (OpenAI) |
| **Discovery** | Runtime tool discovery | Static OpenAPI schema |

### Key Architectural Differences

```
┌─────────────────────────────────────────────────────────────────────┐
│  MCP Architecture (Current)                                         │
├─────────────────────────────────────────────────────────────────────┤
│  Claude Code ←──stdio──→ todoist_mcp.py ←──HTTPS──→ Todoist API    │
│              (local)      (local process)           (cloud)         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│  ChatGPT Actions Architecture (Target)                              │
├─────────────────────────────────────────────────────────────────────┤
│  ChatGPT ←──HTTPS──→ Your REST API ←──HTTPS──→ Todoist API         │
│  (cloud)             (your VPS)                (cloud)              │
└─────────────────────────────────────────────────────────────────────┘
```

### Why This Conversion Is Non-Trivial

1. **No Local Process**: ChatGPT cannot run local code - everything must be HTTP
2. **Multi-Tenant Auth**: Each user needs their own Todoist token (not a shared env var)
3. **OpenAPI Schema**: Must define exact request/response shapes upfront
4. **Callback URLs**: OAuth requires ChatGPT-specific redirect handling

---

## Part 2: Authentication Strategy

### Option Analysis

| Option | Security | UX | Complexity | Recommendation |
|--------|----------|-----|------------|----------------|
| **OAuth 2.0** | High | Excellent | High | **Recommended** |
| **User-provided token** | Medium | Poor | Low | Fallback option |
| **Shared token** | None | N/A | Trivial | Demo only |

### OAuth 2.0 Flow (Recommended)

```
┌─────────────────────────────────────────────────────────────────────┐
│  OAuth 2.0 Authorization Code Flow                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User clicks "Sign in with Todoist" in GPT                      │
│     ChatGPT → redirect to https://todoist.com/oauth/authorize      │
│                                                                     │
│  2. User authorizes on Todoist                                     │
│     Todoist → redirect to https://todoist.rodda.xyz/oauth/callback │
│                                                                     │
│  3. Your server exchanges code for token                           │
│     Your API → POST https://todoist.com/oauth/access_token         │
│                                                                     │
│  4. Your server redirects back to ChatGPT with session             │
│     Your API → redirect to ChatGPT callback URL                    │
│                                                                     │
│  5. ChatGPT calls your API with session token                      │
│     ChatGPT → Authorization: Bearer <your_session_token>           │
│                                                                     │
│  6. Your API looks up Todoist token and proxies request            │
│     Your API → Todoist API (with user's actual token)              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Todoist OAuth Requirements

To use Todoist OAuth, you must:

1. **Register an app** at https://developer.todoist.com/appconsole.html
2. **Obtain**: Client ID, Client Secret
3. **Configure redirect URI**: `https://todoist.rodda.xyz/oauth/callback`
4. **Scopes needed**: `data:read_write` (full task/project access)

### Token Storage Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Token Management                                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Option A: Stateless JWT (Simpler)                                 │
│  ─────────────────────────────────                                 │
│  • Encrypt Todoist token inside a JWT                              │
│  • ChatGPT stores/sends this JWT as bearer token                   │
│  • No database needed                                              │
│  • Cons: Can't revoke tokens, larger payloads                      │
│                                                                     │
│  Option B: Session Database (More Secure)                          │
│  ─────────────────────────────────────────                         │
│  • Store Todoist token in database with session ID                 │
│  • ChatGPT only sees opaque session ID                             │
│  • Can revoke sessions, audit access                               │
│  • Cons: Requires database (SQLite or PostgreSQL)                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Recommendation**: Start with Stateless JWT for simplicity, migrate to database if needed.

---

## Part 3: VPS Infrastructure Integration

### Current Infrastructure (rodda.xyz)

Based on the do-vps-prod repository:

| Resource | Current | After Adding Todoist API |
|----------|---------|--------------------------|
| RAM Used | 1740MB / 4096MB | ~1868MB (+128MB) |
| Services | 9 containers | 10 containers |
| Domains | 7 subdomains | 8 subdomains |

### Proposed Domain

```
https://todoist.rodda.xyz
```

### Caddy Configuration Addition

```caddyfile
todoist.{$DOMAIN} {
    reverse_proxy todoist-api:8000 {
        header_up X-Forwarded-Proto {scheme}
        header_up X-Real-IP {remote_host}
    }

    # Rate limiting (prevent abuse)
    rate_limit {
        zone todoist_zone {
            key {remote_host}
            events 100
            window 1m
        }
    }
}
```

### Docker Compose Addition

```yaml
services:
  todoist-api:
    image: todoist-chatgpt-api:latest
    build:
      context: ./todoist-api
      dockerfile: Dockerfile
    container_name: todoist-api
    restart: unless-stopped
    environment:
      - TODOIST_CLIENT_ID=${TODOIST_CLIENT_ID}
      - TODOIST_CLIENT_SECRET=${TODOIST_CLIENT_SECRET}
      - JWT_SECRET=${JWT_SECRET}
      - CHATGPT_CALLBACK_URL=${CHATGPT_CALLBACK_URL}
    networks:
      - frontend
    mem_limit: 128m
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Resource Allocation

| Component | RAM | Justification |
|-----------|-----|---------------|
| FastAPI + Uvicorn | 64MB | Lightweight async Python |
| Buffer for spikes | 64MB | OAuth flows, concurrent requests |
| **Total** | **128MB** | Well within available headroom |

---

## Part 4: API Design

### Endpoints Required

```
┌─────────────────────────────────────────────────────────────────────┐
│  REST API Endpoints                                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Authentication                                                     │
│  ──────────────                                                    │
│  GET  /oauth/authorize     → Redirect to Todoist OAuth             │
│  GET  /oauth/callback      → Handle Todoist callback               │
│                                                                     │
│  Health                                                            │
│  ──────                                                            │
│  GET  /health              → API health check                      │
│  GET  /.well-known/openapi.json → OpenAPI schema for ChatGPT       │
│                                                                     │
│  Projects                                                          │
│  ────────                                                          │
│  GET  /projects            → List all projects                     │
│  GET  /projects/{id}       → Get project details                   │
│  POST /projects            → Create project                        │
│                                                                     │
│  Tasks                                                             │
│  ─────                                                             │
│  GET  /tasks               → List tasks (with filters)             │
│  GET  /tasks/{id}          → Get task details                      │
│  POST /tasks               → Create task                           │
│  PATCH /tasks/{id}         → Update task                           │
│  POST /tasks/{id}/complete → Complete task                         │
│  POST /tasks/{id}/reopen   → Reopen task                           │
│  DELETE /tasks/{id}        → Delete task                           │
│                                                                     │
│  Labels                                                            │
│  ──────                                                            │
│  GET  /labels              → List all labels                       │
│  POST /labels              → Create label                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### OpenAPI Schema Structure

```yaml
openapi: 3.1.0
info:
  title: Todoist API for ChatGPT
  description: Manage your Todoist tasks, projects, and labels
  version: 1.0.0
servers:
  - url: https://todoist.rodda.xyz
    description: Production server

components:
  securitySchemes:
    oauth2:
      type: oauth2
      flows:
        authorizationCode:
          authorizationUrl: https://todoist.rodda.xyz/oauth/authorize
          tokenUrl: https://todoist.rodda.xyz/oauth/token
          scopes:
            todoist: Full access to Todoist data

paths:
  /tasks:
    get:
      operationId: listTasks
      summary: List tasks
      description: |
        List all tasks, optionally filtered by project, label, or filter query.
        Supports Todoist's native filter syntax like "today", "overdue", "p1".
      parameters:
        - name: project_id
          in: query
          schema:
            type: string
        - name: label
          in: query
          schema:
            type: string
        - name: filter
          in: query
          schema:
            type: string
            description: "Todoist filter syntax (e.g., 'today', 'overdue', 'p1')"
      responses:
        '200':
          description: List of tasks
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/Task'
      security:
        - oauth2: [todoist]
```

---

## Part 5: Implementation Plan

### Phase 1: Core API (Week 1)

```
□ Create FastAPI application structure
□ Implement health endpoint
□ Port MCP tools to REST endpoints:
  □ /tasks (GET, POST)
  □ /tasks/{id} (GET, PATCH, DELETE)
  □ /tasks/{id}/complete (POST)
  □ /tasks/{id}/reopen (POST)
  □ /projects (GET, POST)
  □ /projects/{id} (GET)
  □ /labels (GET, POST)
□ Generate OpenAPI schema
□ Test with curl/Postman using hardcoded token
```

### Phase 2: OAuth Integration (Week 2)

```
□ Register Todoist OAuth app
□ Implement OAuth endpoints:
  □ /oauth/authorize
  □ /oauth/callback
  □ /oauth/token (for ChatGPT token exchange)
□ Implement JWT token generation/validation
□ Add token middleware to all API routes
□ Test OAuth flow end-to-end
```

### Phase 3: Deployment (Week 2-3)

```
□ Create Dockerfile
□ Add to do-vps-prod docker-compose.yml
□ Add Caddy configuration
□ Configure DNS (todoist.rodda.xyz)
□ Deploy and verify HTTPS
□ Test from external network
```

### Phase 4: GPT Creation (Week 3)

```
□ Create ChatGPT GPT (requires Plus account temporarily)
□ Configure actions with OpenAPI schema
□ Configure OAuth settings
□ Test full flow as GPT user
□ Write GPT instructions/system prompt
□ Publish GPT publicly
□ Test with free account
```

### Phase 5: Polish & Documentation (Week 3-4)

```
□ Add rate limiting
□ Add request logging
□ Create user documentation
□ Handle edge cases (expired tokens, API errors)
□ Monitor for issues
```

---

## Part 6: Technical Decisions

### Framework Choice: FastAPI

**Why FastAPI over Flask**:
- Native async support (matches existing httpx usage)
- Automatic OpenAPI schema generation
- Pydantic integration (already used in MCP server)
- Better performance for I/O-bound operations

### Code Reuse Strategy

```
┌─────────────────────────────────────────────────────────────────────┐
│  Code Migration Path                                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  todoist_mcp.py (current)                                          │
│       │                                                            │
│       ├── Pydantic Models ──────────────→ models.py (reuse 100%)   │
│       │                                                            │
│       ├── API Client Functions ─────────→ todoist_client.py        │
│       │   (extract from tools)             (reuse ~80%)            │
│       │                                                            │
│       ├── Error Handling ───────────────→ exceptions.py            │
│       │                                    (reuse ~90%)            │
│       │                                                            │
│       └── Response Formatting ──────────→ Not needed               │
│           (Markdown output)                (JSON only)             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Security Considerations

| Risk | Mitigation |
|------|------------|
| Token theft | JWT encryption, short expiry |
| API abuse | Rate limiting per IP |
| SSRF attacks | Validate all URLs, no user-controlled redirects |
| Injection | Pydantic validation, parameterized queries |
| Token leakage | Never log tokens, secure storage |

### ChatGPT-Specific Requirements

1. **Same-domain OAuth**: Authorization and token endpoints must share root domain
2. **Callback URL format**: `https://chat.openai.com/aip/plugin-{ID}/oauth/callback`
3. **Schema validation**: ChatGPT validates OpenAPI schema strictly
4. **Response format**: JSON only (no Markdown formatting)
5. **Error handling**: Must return proper HTTP status codes

---

## Part 7: GPT Configuration

### System Instructions (Draft)

```
You are a Todoist task management assistant. You help users manage their tasks,
projects, and labels in Todoist.

CAPABILITIES:
- List, create, update, and complete tasks
- Manage projects and sub-projects
- Create and assign labels
- Use natural language dates ("tomorrow", "next Monday", "every week")
- Filter tasks using Todoist syntax ("today", "overdue", "p1", "@label")

BEHAVIOR:
- Always confirm before deleting tasks or projects
- When listing tasks, summarize by project unless asked otherwise
- Suggest due dates and priorities when creating tasks
- Use labels to help organize related tasks across projects

LIMITATIONS:
- Cannot access task comments
- Cannot manage sections within projects
- Cannot access shared project permissions
```

### Conversation Starters

```
- "What tasks do I have due today?"
- "Create a task to buy groceries tomorrow"
- "Show me all my high-priority tasks"
- "What's in my Work project?"
```

---

## Part 8: Cost & Resource Analysis

### Infrastructure Costs

| Item | One-time | Monthly |
|------|----------|---------|
| Todoist OAuth App | Free | Free |
| VPS (existing) | $0 | $0 (already paid) |
| Additional RAM | $0 | $0 (within limits) |
| Domain/SSL | $0 | $0 (existing) |
| **Total** | **$0** | **$0** |

### ChatGPT Plus Requirement

- **Creating the GPT**: Requires Plus ($20/month) temporarily
- **Using the GPT**: Free for all users once published
- **Workaround**: Create GPT, publish, cancel Plus

### Todoist API Limits

| Limit | Value | Impact |
|-------|-------|--------|
| Requests/min | 450 | Unlikely to hit with ChatGPT |
| Daily requests | No published limit | Not a concern |
| OAuth apps | No limit | N/A |

---

## Part 9: Alternatives Considered

### Alternative 1: ChatGPT "Apps" (New Feature)

OpenAI recently introduced "Apps in ChatGPT" which may supersede custom GPTs. However:
- Still in early rollout
- Documentation incomplete
- GPT Actions remain the documented approach

**Decision**: Proceed with GPT Actions, monitor Apps development.

### Alternative 2: Direct API Key Input

Users could paste their Todoist API key directly into the chat.

**Pros**: No OAuth complexity, no server state
**Cons**: Poor UX, security risk (key in chat history), user friction

**Decision**: Implement as fallback if OAuth proves too complex.

### Alternative 3: Zapier/Make Integration

Use existing integration platforms.

**Pros**: No code required
**Cons**: Another service dependency, potential costs, less control

**Decision**: Rejected - defeats purpose of self-hosting.

---

## Part 10: Open Questions

### For Implementation

1. **Token refresh**: Does Todoist support refresh tokens? (Need to verify)
2. **Webhook support**: Should we add Todoist webhooks for real-time updates?
3. **Multi-user scaling**: What if this becomes popular? (SQLite vs PostgreSQL)

### For User Decision

1. **Fallback auth**: Should we support API key input as fallback?
2. **Rate limiting**: How aggressive? (100/min suggested)
3. **Logging**: How much request logging for debugging?
4. **Analytics**: Track usage statistics?

---

## Sources & References

### ChatGPT Actions & OAuth
- [GPT Action Authentication - OpenAI Platform](https://platform.openai.com/docs/actions/authentication)
- [Authenticate Users in GPT Actions - Logto Blog](https://blog.logto.io/gpt-action-oauth)
- [OAuth2 Example: Custom GPT - Guru Developer Docs](https://developer.getguru.com/docs/oauth2-example-custom-gpt)
- [Custom GPT Actions in 2025 - Lindy](https://www.lindy.ai/blog/custom-gpt-actions)

### MCP vs ChatGPT Comparison
- [ChatGPT Agent vs MCP - Medium](https://medium.com/data-science-in-your-pocket/chatgpt-agent-vs-model-context-protocol-ce4a77aff5e7)
- [MCP Comparison: Function Calling, Plugins, APIs - iKangai](https://www.ikangai.com/model-context-protocol-comparison-mcp-vs-function-calling-plugins-apis/)
- [How MCP is Changing ChatGPT - Dataslayer](https://www.dataslayer.ai/blog/how-the-model-context-protocol-mcp-is-changing-chatgpt)

### Todoist API
- [Todoist REST API Documentation](https://developer.todoist.com/rest/v2/)
- [Todoist OAuth Documentation](https://developer.todoist.com/guides/#oauth)
- [Todoist App Console](https://developer.todoist.com/appconsole.html)

---

## Next Steps

1. **Review this plan** - Confirm architecture decisions
2. **Register Todoist OAuth app** - Get client credentials
3. **Create FastAPI project structure** - Start implementation
4. **Deploy to VPS** - Integrate with existing infrastructure
5. **Create and publish GPT** - Make available to free users

---

*Document created: 2025-11-26*
*Last updated: 2025-11-26*
