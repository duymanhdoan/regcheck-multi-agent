# Integration Test Suite

This directory contains integration tests for the Internal File Processing System deployed on AWS Fargate.

## Overview

The test suite validates end-to-end workflows across multiple zones (dev, prod) and through the Global ALB, ensuring all components work together correctly.

## Prerequisites

- Python 3.8 or higher
- AWS credentials configured
- Access to deployed infrastructure (dev and/or prod zones)
- Environment variables configured (see Configuration section)

## Installation

Install test dependencies:

```bash
pip install -r tests/requirements.txt
```

## Configuration

Set the following environment variables before running tests:

### Required for Zone Tests

```bash
# AWS Configuration
export AWS_REGION="ap-southeast-1"

# Zone A (Dev) Configuration
export DEV_NLB_DNS="dev-nlb-ap-southeast-1-xxxxx.elb.ap-southeast-1.amazonaws.com"
export DEV_COGNITO_POOL_ID="ap-southeast-1_xxxxx"
export DEV_COGNITO_CLIENT_ID="xxxxx"

# Zone B (Prod) Configuration
export PROD_NLB_DNS="prod-nlb-ap-southeast-1-xxxxx.elb.ap-southeast-1.amazonaws.com"
export PROD_COGNITO_POOL_ID="ap-southeast-1_xxxxx"
export PROD_COGNITO_CLIENT_ID="xxxxx"

# Test User Credentials
export TEST_USERNAME="test-user"
export TEST_PASSWORD="TestPassword123"
export TEST_DEPARTMENT="finance"
```

### Required for Global ALB Tests

```bash
# Global ALB Configuration
export GLOBAL_NLB_DNS="global-alb-ap-southeast-1-xxxxx.elb.ap-southeast-1.amazonaws.com"
```

### Optional Configuration

```bash
# Service Token for MCP Gateway
export SERVICE_TOKEN="your-service-token"
```

## Running Tests

### Quick Start

Run all tests (both zones):
```bash
./tests/run_tests.sh
```

### Zone-Specific Tests

Test only dev zone:
```bash
./tests/run_tests.sh --zone dev
```

Test only prod zone:
```bash
./tests/run_tests.sh --zone prod
```

### Global ALB Tests

Test through Global ALB:
```bash
./tests/run_tests.sh --global-nlb
```

### Run All Tests

Run all tests (dev, prod, and global-nlb):
```bash
./tests/run_tests.sh --all
```

### Custom Report Directory

Specify custom report directory:
```bash
./tests/run_tests.sh --report-dir ./my-reports
```

### Verbose Output

Enable verbose test output:
```bash
./tests/run_tests.sh --verbose
```

## Test Reports

After running tests, reports are generated in the `test-reports` directory (or custom directory specified with `--report-dir`):

- **HTML Reports**: Individual HTML reports for each test suite
  - `report_dev_YYYYMMDD_HHMMSS.html`
  - `report_prod_YYYYMMDD_HHMMSS.html`
  - `report_global_nlb_YYYYMMDD_HHMMSS.html`

- **JUnit XML**: Machine-readable test results
  - `junit_dev_YYYYMMDD_HHMMSS.xml`
  - `junit_prod_YYYYMMDD_HHMMSS.xml`
  - `junit_global_nlb_YYYYMMDD_HHMMSS.xml`

- **Summary Report**: Consolidated HTML summary
  - `summary_YYYYMMDD_HHMMSS.html`

### Viewing Reports

Open the summary report in your browser:
```bash
open test-reports/summary_*.html
```

Or view individual test reports:
```bash
open test-reports/report_dev_*.html
```

## Test Coverage

The integration test suite covers:

### Authentication Tests (`test_auth_flow.py`)
- User authentication with Cognito
- JWT token validation
- Session management

### File Upload Tests (`test_file_upload.py`)
- File upload to S3 through frontend
- Upload validation
- Error handling

### File Processing Tests (`test_file_processing.py`)
- End-to-end file processing workflow
- MCP data enrichment
- Processed file retrieval

### MCP Communication Tests (`test_mcp_communication.py`)
- AgentGateway routing
- MCP server communication
- Service token validation

### RBAC Tests (`test_rbac.py`)
- Role-based access control
- Department-specific access
- Permission enforcement

### Auto Scaling Tests (`test_auto_scaling.py`)
- Service scaling behavior
- CPU-based scaling triggers
- Task count validation

### Global ALB Tests (`test_global_alb.py`)
- Traffic distribution across zones
- Session stickiness
- Load balancing verification

### Global ALB Failover Tests (`test_global_alb_failover.py`)
- Zone failure simulation
- Automatic failover
- Traffic rerouting

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── requirements.txt               # Test dependencies
├── run_tests.sh                   # Test execution script
├── README.md                      # This file
├── integration/                   # Integration test modules
│   ├── test_auth_flow.py
│   ├── test_file_upload.py
│   ├── test_file_processing.py
│   ├── test_mcp_communication.py
│   ├── test_rbac.py
│   ├── test_auto_scaling.py
│   ├── test_global_alb.py
│   └── test_global_alb_failover.py
└── test_data/                     # Test data files
    └── sample.txt
```

## Troubleshooting

### Tests Fail to Connect

- Verify NLB DNS names are correct
- Check security groups allow traffic from your IP
- Ensure services are running in ECS

### Authentication Failures

- Verify Cognito User Pool ID and Client ID
- Check test user exists in Cognito
- Ensure test user password meets requirements

### Global ALB Tests Skipped

- Set `GLOBAL_NLB_DNS` environment variable
- Verify Global ALB is deployed and healthy

### Timeout Errors

- Increase timeout in `conftest.py` if needed
- Check service health in AWS Console
- Verify NAT Gateway is functioning

## CI/CD Integration

The test script can be integrated into CI/CD pipelines:

```bash
# Example: GitHub Actions
- name: Run Integration Tests
  run: |
    ./tests/run_tests.sh --all --report-dir ./test-results
  env:
    AWS_REGION: ${{ secrets.AWS_REGION }}
    DEV_NLB_DNS: ${{ secrets.DEV_NLB_DNS }}
    # ... other environment variables
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

## Support

For issues or questions, refer to:
- Architecture documentation: `docs/interal-docs/Enterprise_Architecture_Design_v2.md`
- Deployment guide: `DEPLOYMENT_SUMMARY.md`
- Requirements: `.kiro/specs/simple-fargate-architecture/requirements.md`
