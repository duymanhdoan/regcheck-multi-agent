# MCP Server Services

Model Context Protocol (MCP) servers for Finance, HR, and Legal departments.

## Overview

This project contains three MCP servers that provide department-specific tools and resources:

- **Finance MCP Server**: Financial data, budgets, and invoices
- **HR MCP Server**: Employee data, org charts, and leave balances
- **Legal MCP Server**: Contracts, compliance, legal documents, and precedents

Each server implements the MCP JSON-RPC protocol and retrieves data from S3.

## Architecture

```
MCP Servers
├── Base Server (protocol handling)
│   ├── MCP Request/Response models
│   ├── Tools/Resources registration
│   └── S3 client for data retrieval
├── Finance Server
│   ├── get_financial_data
│   ├── get_budget_info
│   └── get_invoice_data
├── HR Server
│   ├── get_employee_data
│   ├── get_org_chart
│   └── get_leave_balance
└── Legal Server
    ├── get_contract_data
    ├── get_compliance_info
    ├── get_legal_document
    └── search_legal_precedents
```

## MCP Protocol

All servers implement the MCP JSON-RPC protocol with these methods:

- `tools/list`: List available tools
- `tools/call`: Execute a tool
- `resources/list`: List available resources
- `resources/read`: Read a resource

### Example Request

```json
{
  "jsonrpc": "2.0",
  "id": "123",
  "method": "tools/call",
  "params": {
    "name": "get_financial_data",
    "arguments": {
      "user_id": "user-456",
      "data_type": "balance"
    }
  }
}
```

### Example Response

```json
{
  "jsonrpc": "2.0",
  "id": "123",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\"user_id\": \"user-456\", \"data_type\": \"balance\", \"data\": {...}}"
      }
    ],
    "isError": false
  }
}
```

## Configuration

Environment variables:

- `SERVER_TYPE`: Server type (finance, hr, legal) - **Required**
- `SERVER_PORT`: Server port (default: 8082)
- `AWS_REGION`: AWS region (default: "ap-southeast-1")
- `S3_BUCKET_NAME`: S3 bucket name for data
- `S3_DATA_PREFIX`: Prefix for MCP data files (default: "mcp-data/")
- `LOG_LEVEL`: Logging level (default: "INFO")

## Development

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Run Finance Server

```bash
export SERVER_TYPE=finance
export S3_BUCKET_NAME=app-files-dev-ap-southeast-1
uvicorn src.finance.main:app --host 0.0.0.0 --port 8082 --reload
```

### Run HR Server

```bash
export SERVER_TYPE=hr
export S3_BUCKET_NAME=app-files-dev-ap-southeast-1
uvicorn src.hr.main:app --host 0.0.0.0 --port 8082 --reload
```

### Run Legal Server

```bash
export SERVER_TYPE=legal
export S3_BUCKET_NAME=app-files-dev-ap-southeast-1
uvicorn src.legal.main:app --host 0.0.0.0 --port 8082 --reload
```

## Docker

### Build Images

```bash
# Finance server
docker build -t mcp-finance-server:latest --build-arg SERVER_TYPE=finance .

# HR server
docker build -t mcp-hr-server:latest --build-arg SERVER_TYPE=hr .

# Legal server
docker build -t mcp-legal-server:latest --build-arg SERVER_TYPE=legal .
```

### Run Containers

```bash
# Finance server
docker run -p 8082:8082 \
  -e SERVER_TYPE=finance \
  -e S3_BUCKET_NAME=app-files-dev-ap-southeast-1 \
  mcp-finance-server:latest

# HR server
docker run -p 8083:8082 \
  -e SERVER_TYPE=hr \
  -e S3_BUCKET_NAME=app-files-dev-ap-southeast-1 \
  mcp-hr-server:latest

# Legal server
docker run -p 8084:8082 \
  -e SERVER_TYPE=legal \
  -e S3_BUCKET_NAME=app-files-dev-ap-southeast-1 \
  mcp-legal-server:latest
```

## Deployment

### Build and Push to ECR

```bash
# Set environment variables
export AWS_ACCOUNT_ID=123456789012
export AWS_REGION=ap-southeast-1

# Run build script
./build.sh finance
./build.sh hr
./build.sh legal
```

### Deploy to ECS

```bash
# Update Finance service
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service mcp-finance-service \
  --force-new-deployment

# Update HR service
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service mcp-hr-service \
  --force-new-deployment

# Update Legal service
aws ecs update-service \
  --cluster dev-ecs-cluster \
  --service mcp-legal-service \
  --force-new-deployment
```

## S3 Data Structure

MCP servers retrieve data from S3 with this structure:

```
s3://bucket-name/mcp-data/
├── finance/
│   ├── user_balance.json
│   ├── user_transactions.json
│   ├── budgets_department.json
│   ├── budgets_project.json
│   └── invoices.json
├── hr/
│   ├── employee_profile.json
│   ├── employee_job_details.json
│   ├── org_chart.json
│   └── leave_balances.json
└── legal/
    ├── contracts.json
    ├── compliance.json
    ├── documents.json
    └── precedents.json
```

## Finance Tools

### get_financial_data
Retrieve financial data for a user.

**Arguments:**
- `user_id` (string): User identifier
- `data_type` (string): Type of data (balance, transactions, summary)
- `date_range` (object, optional): Date range for transactions

### get_budget_info
Retrieve budget information.

**Arguments:**
- `entity_id` (string): Department or project ID
- `entity_type` (string): Entity type (department, project)
- `fiscal_year` (string, optional): Fiscal year

### get_invoice_data
Retrieve invoice data.

**Arguments:**
- `invoice_id` (string, optional): Invoice ID
- `vendor_id` (string, optional): Vendor ID filter
- `status` (string, optional): Status filter

## HR Tools

### get_employee_data
Retrieve employee data.

**Arguments:**
- `employee_id` (string): Employee identifier
- `data_type` (string): Type of data (profile, job_details, history, performance)

### get_org_chart
Retrieve organizational chart.

**Arguments:**
- `department_id` (string): Department identifier
- `include_subordinates` (boolean): Include subordinates
- `depth` (integer): Maximum hierarchy depth

### get_leave_balance
Retrieve leave balance.

**Arguments:**
- `employee_id` (string): Employee identifier
- `leave_type` (string): Leave type (annual, sick, personal, all)
- `year` (string, optional): Year for balance

## Legal Tools

### get_contract_data
Retrieve contract data.

**Arguments:**
- `contract_id` (string, optional): Contract ID
- `party_name` (string, optional): Party name filter
- `contract_type` (string, optional): Contract type
- `status` (string, optional): Status filter

### get_compliance_info
Retrieve compliance information.

**Arguments:**
- `regulation_type` (string): Regulation type (gdpr, hipaa, sox, pci-dss, iso27001)
- `department_id` (string, optional): Department ID
- `include_requirements` (boolean): Include requirements

### get_legal_document
Retrieve legal document.

**Arguments:**
- `document_id` (string): Document identifier
- `document_type` (string, optional): Document type
- `include_metadata` (boolean): Include metadata

### search_legal_precedents
Search legal precedents.

**Arguments:**
- `query` (string): Search query
- `jurisdiction` (string, optional): Legal jurisdiction
- `case_type` (string, optional): Case type
- `max_results` (integer): Maximum results

## Health Check

All servers expose a health check endpoint:

```bash
curl http://localhost:8082/health
```

Response:
```json
{
  "status": "healthy",
  "server_type": "finance",
  "version": "1.0.0"
}
```

## Error Handling

- S3 errors: Retry with exponential backoff (3 attempts)
- Tool execution errors: Return error in MCP response
- Invalid requests: Return MCP error with appropriate code

## Monitoring

- Logs: JSON-formatted logs to CloudWatch
- Metrics: CPU, memory, request count
- Health checks: `/health` endpoint for ALB
