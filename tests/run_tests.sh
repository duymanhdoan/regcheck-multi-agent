#!/bin/bash

###############################################################################
# Integration Test Execution Script
# 
# This script executes integration tests for the Internal File Processing System
# across different zones (dev, prod) and through the Global NLB.
#
# Usage:
#   ./run_tests.sh [OPTIONS]
#
# Options:
#   --zone <dev|prod>     Run tests for specific zone (default: both)
#   --global-nlb          Run tests through Global NLB
#   --all                 Run all tests (zones + global)
#   --report-dir <path>   Directory for test reports (default: ./test-reports)
#   --verbose             Enable verbose output
#   --help                Show this help message
#
# Examples:
#   ./run_tests.sh --zone dev
#   ./run_tests.sh --zone prod
#   ./run_tests.sh --global-nlb
#   ./run_tests.sh --all
#
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
ZONE=""
RUN_GLOBAL=false
RUN_ALL=false
REPORT_DIR="./test-reports"
VERBOSE=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --zone)
            ZONE="$2"
            shift 2
            ;;
        --global-nlb)
            RUN_GLOBAL=true
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --report-dir)
            REPORT_DIR="$2"
            shift 2
            ;;
        --verbose)
            VERBOSE=true
            shift
            ;;
        --help)
            grep "^#" "$0" | grep -v "#!/bin/bash" | sed 's/^# //'
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
    echo ""
}

# Function to check if pytest is installed
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v pytest &> /dev/null; then
        print_error "pytest is not installed"
        print_info "Installing test dependencies..."
        pip install -r "${SCRIPT_DIR}/requirements.txt"
    fi
    
    print_success "Dependencies OK"
}

# Function to create report directory
setup_report_dir() {
    print_info "Setting up report directory: ${REPORT_DIR}"
    mkdir -p "${REPORT_DIR}"
    
    # Create timestamp for this test run
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    export TEST_RUN_TIMESTAMP="${TIMESTAMP}"
}

# Function to run tests for a specific zone
run_zone_tests() {
    local zone=$1
    local report_file="${REPORT_DIR}/report_${zone}_${TEST_RUN_TIMESTAMP}.html"
    local junit_file="${REPORT_DIR}/junit_${zone}_${TEST_RUN_TIMESTAMP}.xml"
    
    print_header "Running Tests for Zone: ${zone^^}"
    
    # Build pytest command
    local pytest_cmd="pytest ${SCRIPT_DIR}/integration/"
    pytest_cmd="${pytest_cmd} --zone=${zone}"
    pytest_cmd="${pytest_cmd} --html=${report_file}"
    pytest_cmd="${pytest_cmd} --self-contained-html"
    pytest_cmd="${pytest_cmd} --junitxml=${junit_file}"
    
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="${pytest_cmd} -v"
    else
        pytest_cmd="${pytest_cmd} -v --tb=short"
    fi
    
    # Add markers to exclude global-nlb specific tests
    pytest_cmd="${pytest_cmd} -m 'not global_nlb'"
    
    print_info "Executing: ${pytest_cmd}"
    
    if eval "${pytest_cmd}"; then
        print_success "Zone ${zone^^} tests PASSED"
        echo "${zone}:PASS" >> "${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
        return 0
    else
        print_error "Zone ${zone^^} tests FAILED"
        echo "${zone}:FAIL" >> "${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
        return 1
    fi
}

# Function to run tests through Global NLB
run_global_nlb_tests() {
    local report_file="${REPORT_DIR}/report_global_nlb_${TEST_RUN_TIMESTAMP}.html"
    local junit_file="${REPORT_DIR}/junit_global_nlb_${TEST_RUN_TIMESTAMP}.xml"
    
    print_header "Running Tests through Global NLB"
    
    # Check if Global NLB DNS is configured
    if [ -z "${GLOBAL_NLB_DNS}" ]; then
        print_warning "GLOBAL_NLB_DNS environment variable not set"
        print_warning "Skipping Global NLB tests"
        echo "global-nlb:SKIP" >> "${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
        return 0
    fi
    
    # Build pytest command
    local pytest_cmd="pytest ${SCRIPT_DIR}/integration/"
    pytest_cmd="${pytest_cmd} --global-nlb"
    pytest_cmd="${pytest_cmd} --html=${report_file}"
    pytest_cmd="${pytest_cmd} --self-contained-html"
    pytest_cmd="${pytest_cmd} --junitxml=${junit_file}"
    
    if [ "$VERBOSE" = true ]; then
        pytest_cmd="${pytest_cmd} -v"
    else
        pytest_cmd="${pytest_cmd} -v --tb=short"
    fi
    
    # Only run global-nlb specific tests
    pytest_cmd="${pytest_cmd} -k 'global_alb'"
    
    print_info "Executing: ${pytest_cmd}"
    
    if eval "${pytest_cmd}"; then
        print_success "Global NLB tests PASSED"
        echo "global-nlb:PASS" >> "${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
        return 0
    else
        print_error "Global NLB tests FAILED"
        echo "global-nlb:FAIL" >> "${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
        return 1
    fi
}

# Function to generate summary report
generate_summary() {
    local summary_file="${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.txt"
    local summary_html="${REPORT_DIR}/summary_${TEST_RUN_TIMESTAMP}.html"
    
    print_header "Test Execution Summary"
    
    if [ ! -f "${summary_file}" ]; then
        print_warning "No summary file found"
        return
    fi
    
    # Read summary and display
    local total=0
    local passed=0
    local failed=0
    local skipped=0
    
    while IFS=: read -r zone status; do
        total=$((total + 1))
        case $status in
            PASS)
                passed=$((passed + 1))
                print_success "${zone}: PASSED"
                ;;
            FAIL)
                failed=$((failed + 1))
                print_error "${zone}: FAILED"
                ;;
            SKIP)
                skipped=$((skipped + 1))
                print_warning "${zone}: SKIPPED"
                ;;
        esac
    done < "${summary_file}"
    
    echo ""
    print_info "Total test suites: ${total}"
    print_success "Passed: ${passed}"
    print_error "Failed: ${failed}"
    print_warning "Skipped: ${skipped}"
    echo ""
    
    # Generate HTML summary
    cat > "${summary_html}" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Test Execution Summary - ${TEST_RUN_TIMESTAMP}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        h2 {
            color: #555;
            margin-top: 30px;
        }
        .summary-stats {
            display: flex;
            justify-content: space-around;
            margin: 30px 0;
        }
        .stat-box {
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            min-width: 150px;
        }
        .stat-box.total {
            background-color: #e3f2fd;
            border: 2px solid #2196f3;
        }
        .stat-box.passed {
            background-color: #e8f5e9;
            border: 2px solid #4caf50;
        }
        .stat-box.failed {
            background-color: #ffebee;
            border: 2px solid #f44336;
        }
        .stat-box.skipped {
            background-color: #fff3e0;
            border: 2px solid #ff9800;
        }
        .stat-number {
            font-size: 48px;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 18px;
            color: #666;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background-color: #007bff;
            color: white;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .status-pass {
            color: #4caf50;
            font-weight: bold;
        }
        .status-fail {
            color: #f44336;
            font-weight: bold;
        }
        .status-skip {
            color: #ff9800;
            font-weight: bold;
        }
        .report-link {
            color: #007bff;
            text-decoration: none;
        }
        .report-link:hover {
            text-decoration: underline;
        }
        .timestamp {
            color: #999;
            font-size: 14px;
            margin-top: 30px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Integration Test Execution Summary</h1>
        <p><strong>Test Run:</strong> ${TEST_RUN_TIMESTAMP}</p>
        <p><strong>Date:</strong> $(date)</p>
        
        <div class="summary-stats">
            <div class="stat-box total">
                <div class="stat-number">${total}</div>
                <div class="stat-label">Total Suites</div>
            </div>
            <div class="stat-box passed">
                <div class="stat-number">${passed}</div>
                <div class="stat-label">Passed</div>
            </div>
            <div class="stat-box failed">
                <div class="stat-number">${failed}</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-box skipped">
                <div class="stat-number">${skipped}</div>
                <div class="stat-label">Skipped</div>
            </div>
        </div>
        
        <h2>Test Suite Results</h2>
        <table>
            <thead>
                <tr>
                    <th>Test Suite</th>
                    <th>Status</th>
                    <th>HTML Report</th>
                    <th>JUnit XML</th>
                </tr>
            </thead>
            <tbody>
EOF
    
    # Add rows for each test suite
    while IFS=: read -r zone status; do
        local status_class=""
        case $status in
            PASS) status_class="status-pass" ;;
            FAIL) status_class="status-fail" ;;
            SKIP) status_class="status-skip" ;;
        esac
        
        local html_report="report_${zone}_${TEST_RUN_TIMESTAMP}.html"
        local junit_report="junit_${zone}_${TEST_RUN_TIMESTAMP}.xml"
        
        cat >> "${summary_html}" << EOF
                <tr>
                    <td>${zone}</td>
                    <td class="${status_class}">${status}</td>
                    <td><a href="${html_report}" class="report-link">View HTML Report</a></td>
                    <td><a href="${junit_report}" class="report-link">View JUnit XML</a></td>
                </tr>
EOF
    done < "${summary_file}"
    
    cat >> "${summary_html}" << EOF
            </tbody>
        </table>
        
        <div class="timestamp">
            Generated by Integration Test Suite
        </div>
    </div>
</body>
</html>
EOF
    
    print_success "Summary report generated: ${summary_html}"
    print_info "Individual test reports available in: ${REPORT_DIR}"
    
    # Return exit code based on failures
    if [ ${failed} -gt 0 ]; then
        return 1
    else
        return 0
    fi
}

# Main execution
main() {
    print_header "Integration Test Execution"
    
    # Check dependencies
    check_dependencies
    
    # Setup report directory
    setup_report_dir
    
    # Determine what to run
    local exit_code=0
    
    if [ "$RUN_ALL" = true ]; then
        print_info "Running all tests (dev, prod, and global-nlb)"
        run_zone_tests "dev" || exit_code=1
        run_zone_tests "prod" || exit_code=1
        run_global_nlb_tests || exit_code=1
    elif [ "$RUN_GLOBAL" = true ]; then
        run_global_nlb_tests || exit_code=1
    elif [ -n "$ZONE" ]; then
        run_zone_tests "$ZONE" || exit_code=1
    else
        # Default: run both zones
        print_info "Running tests for both zones (dev and prod)"
        run_zone_tests "dev" || exit_code=1
        run_zone_tests "prod" || exit_code=1
    fi
    
    # Generate summary
    generate_summary || exit_code=1
    
    if [ ${exit_code} -eq 0 ]; then
        print_header "All Tests Completed Successfully"
    else
        print_header "Some Tests Failed"
    fi
    
    exit ${exit_code}
}

# Run main function
main
