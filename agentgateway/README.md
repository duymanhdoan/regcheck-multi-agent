# AgentGateway Service

AgentGateway is a dual-mode routing and authentication service for the Internal File Processing System.

## Features

- **API Gateway Mode (Port 8080)**: Routes authenticated requests from Frontend to Application service
- **MCP Gateway Mode (Port 8081)**: Routes MCP protocol requests from Application to MCP servers
- **JWT Validation**: Validates Cognito JWT tokens for user authentication
- **RBAC Engine**: Enforces role-based access control policies
- **Department Isolation**: Ensures users can only access their department's MCP servers
- **Audit Logging**: Logs all requests for security auditing

## Architecture

```
Frontend → AgentGateway (8080) → Application
Application → AgentGateway (8081) → MCP Servers (Finance/HR/Legal)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SERVICE_NAME` | Service identifier | `agentgateway` |
| `API_PORT` | API Gateway port | `8080` |
| `MCP_PORT` | MCP Gateway port | `8081` |
| `AWS_REGION` | AWS region | `ap-southeast-1` |
| `COGNITO_USER_POOL_ID` | Cognito User Pool ID | Required |
| `COGNITO_REGION` | Cognito region | `ap-southeast-1` |
| `RBAC_ENABLED` | Enable RBAC enforcement | `true` |
| `DEPARTMENT_ISOLATION` | Enable department isolation | `true` |
| `APPLICATION_SERVICE_URL` | Application service URL | `http://application-service.local:8000` |
| `MCP_FINANCE_URL` | Finance MCP server URL | `http://mcp-finance-service.local:8080` |
| `MCP_HR_URL` | HR MCP server URL | `http://mcp-hr-service.local:8080` |
| `MCP_LEGAL_URL` | Legal MCP server URL | `http://mcp-legal-service.local:8080` |
| `SERVICE_TOKEN` | Service token for MCP gateway | Optional |
| `LOG_LEVEL` | Logging level | `INFO` |

## Building

```bash
docker build -t agentgateway:latest .
```

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export COGNITO_USER_POOL_ID=your-pool-id

# Run the service
python -m uvicorn src.main:app --host 0.0.0.0 --port 8080
```

## API Endpoints

### API Gateway Mode (Port 8080)

- `POST /api/process` - Route to application service
- `GET /api/status/{id}` - Route to application service
- `GET /health` - Health check

### MCP Gateway Mode (Port 8081)

- `POST /mcp` - Route to MCP servers
- `GET /health` - Health check

## RBAC Configuration

RBAC policies are defined in `src/rbac/policies.yaml`:

```yaml
roles:
  - name: finance
    permissions:
      - resource: mcp-finance-server
        actions: [read, write]
  - name: hr
    permissions:
      - resource: mcp-hr-server
        actions: [read, write]
  - name: legal
    permissions:
      - resource: mcp-legal-server
        actions: [read, write]
```

## Development

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Format code
black src/

# Lint code
pylint src/
```
