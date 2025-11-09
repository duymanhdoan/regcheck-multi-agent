# Custom Langflow Components

This directory contains custom Langflow components for integrating with the Internal File Processing System backend services.

## Components

### 1. AgentGateway API Component

**Purpose**: Call AgentGateway API endpoints for file processing operations.

**Inputs**:
- `api_url`: AgentGateway API endpoint URL (default: http://agentgateway-service.local:8080)
- `endpoint`: API endpoint path (e.g., /api/process, /api/status/{id})
- `method`: HTTP method (GET, POST, PUT, DELETE)
- `payload`: JSON payload for POST/PUT requests
- `auth_token`: JWT token for authentication

**Outputs**:
- `response`: API response with status code and data

**Example Usage**:
```
1. Add AgentGateway API component to your flow
2. Set endpoint to "/api/process"
3. Set method to "POST"
4. Set payload to: {"file_id": "123", "s3_key": "uploads/user/file.pdf"}
5. Connect JWT token from authentication component
6. Connect output to next component in flow
```

### 2. S3 Operations Component

**Purpose**: Upload, download, list, and delete files from S3.

**Inputs**:
- `bucket_name`: S3 bucket name (e.g., app-files-dev-ap-southeast-1)
- `operation`: Operation to perform (upload, download, list, delete)
- `file_path`: Local file path for upload/download
- `s3_key`: S3 object key (path in bucket)
- `prefix`: Prefix for list operations (e.g., uploads/, processed/)

**Outputs**:
- `result`: Operation result with success status and details

**Example Usage - Upload**:
```
1. Add S3 Operations component
2. Set bucket_name from environment variable
3. Set operation to "upload"
4. Set file_path to local file
5. Set s3_key to "uploads/user-123/document.pdf"
6. Component uses IAM role credentials automatically
```

**Example Usage - List Files**:
```
1. Add S3 Operations component
2. Set bucket_name from environment variable
3. Set operation to "list"
4. Set prefix to "uploads/user-123/"
5. Output contains array of objects with key, size, last_modified
```

### 3. MCP Server Client Component

**Purpose**: Interact with MCP servers (Finance, HR, Legal) through AgentGateway.

**Inputs**:
- `agentgateway_url`: AgentGateway MCP endpoint (default: http://agentgateway-service.local:8081)
- `server_type`: MCP server type (finance, hr, legal)
- `method`: MCP method (tools/list, tools/call, resources/list, resources/read)
- `tool_name`: Name of tool to call (for tools/call)
- `tool_arguments`: JSON arguments for the tool
- `service_token`: Service token for authentication

**Outputs**:
- `response`: MCP response with result data

**Example Usage - Call Finance Tool**:
```
1. Add MCP Server Client component
2. Set server_type to "finance"
3. Set method to "tools/call"
4. Set tool_name to "get_financial_data"
5. Set tool_arguments to: {"user_id": "user-123", "data_type": "balance"}
6. Connect service token from secure storage
7. Output contains financial data from MCP server
```

**Example Usage - List Available Tools**:
```
1. Add MCP Server Client component
2. Set server_type to "hr"
3. Set method to "tools/list"
4. Output contains list of available HR tools
```

## Installation

These components are automatically loaded by Langflow when placed in the custom components directory.

### In Docker Container

The components are copied into the Langflow container at build time:

```dockerfile
COPY langflow_components /app/langflow_components
ENV LANGFLOW_COMPONENTS_PATH=/app/langflow_components
```

### Local Development

For local development, copy these components to your Langflow components directory:

```bash
cp -r langflow_components ~/.langflow/components/
```

## Environment Variables

The components use the following environment variables (automatically set in ECS):

- `AWS_REGION`: AWS region for S3 operations
- `S3_BUCKET_NAME`: Default S3 bucket name
- `LANGFLOW_BACKEND_URL`: AgentGateway API URL

## Authentication

### JWT Authentication (AgentGateway API)

The AgentGateway API component requires a JWT token obtained from Cognito authentication. You can:

1. Create a Cognito authentication flow in Langflow
2. Store the JWT token in a secure variable
3. Pass it to the AgentGateway API component

### Service Token (MCP Server)

The MCP Server Client requires a service token for authentication. This should be:

1. Stored as a Langflow secret
2. Passed to the component via the service_token input

### IAM Role (S3 Operations)

The S3 Operations component uses IAM role credentials from the ECS task. No explicit credentials needed.

## Example Flows

### File Processing Flow

```
1. File Upload (S3 Operations - upload)
   ↓
2. Trigger Processing (AgentGateway API - POST /api/process)
   ↓
3. Check Status (AgentGateway API - GET /api/status/{id})
   ↓
4. Download Result (S3 Operations - download)
```

### MCP Data Enrichment Flow

```
1. Get Financial Data (MCP Server Client - finance)
   ↓
2. Get Employee Data (MCP Server Client - hr)
   ↓
3. Combine Data (Data Processing Component)
   ↓
4. Upload to S3 (S3 Operations - upload)
```

## Troubleshooting

### Component Not Loading

- Check that `LANGFLOW_COMPONENTS_PATH` is set correctly
- Verify all dependencies are installed (httpx, boto3)
- Check Langflow logs for import errors

### S3 Permission Errors

- Verify ECS task role has correct S3 permissions
- Check bucket name matches environment
- Ensure S3 key follows correct prefix structure

### MCP Server Errors

- Verify AgentGateway URL is correct
- Check service token is valid
- Ensure MCP server type matches available servers
- Review AgentGateway logs for routing issues

### Authentication Errors

- Verify JWT token is not expired
- Check Cognito user pool configuration
- Ensure token is passed in correct format

## Dependencies

Required Python packages:
- `langflow` (provided by Langflow)
- `httpx` (for HTTP requests)
- `boto3` (for S3 operations)

These are included in the Langflow Docker image.
