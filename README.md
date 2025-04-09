# DXC Supplemental Pay AI Agent System

An intelligent agent system for analyzing and processing DXC's supplemental pay data, built using Azure AI Agent Service and Azure AI Foundry SDK.

## Overview

The DXC Supplemental Pay AI Agent System helps HR personnel, people managers, and payroll managers analyze supplemental pay data, identify trends and outliers, and make actionable recommendations based on DXC policies. The system leverages Azure AI Agent Service to process policy documents and Excel files from a local data directory and provide intelligent insights.

## Features

- **Policy Extraction**: Retrieve and process DXC policy documents from local files
- **Employee Analysis**: Calculate supplemental pay and provide recommendations for specific employees
- **Team Analysis**: Analyze trends and patterns across entire teams
- **Pay Calculation**: Automated calculation of overtime, standby, and call-out pay
- **Trend Identification**: Identify trends in supplemental pay data over time
- **Outlier Detection**: Flag unusual patterns or policy violations
- **Cost Allocation**: Analyze billable vs. internally absorbed supplemental pay

## System Architecture

The system uses Azure AI Agent Service with specialized agents:

1. **Policy Extraction Agent**: Processes policy documents to extract rules and guidelines
2. **Pay Calculation Agent**: Analyzes employee data and applies policy rules
3. **Analytics Agent**: Identifies trends, outliers, and opportunities for improvement

Data is retrieved from a local data directory and processed using pandas. The system utilizes Azure AI Agent's code interpreter capability to perform sophisticated data analysis.

## Prerequisites

- Python 3.9+
- Azure OpenAI API access with GPT-4o deployment
- Azure AI Foundry SDK access
- Azure AI Agent Service access
- Excel files in the local `data` directory

## Setup

1. Clone this repository:

```bash
git clone <repository-url>
cd dxc-suppay-agent
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file with the following environment variables:

```
# Azure OpenAI credentials
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o

# Azure AI Agent Service
AZURE_SUBSCRIPTION_ID=your_subscription_id
AZURE_RESOURCE_GROUP=your_resource_group
AZURE_PROJECT_NAME=your_project_name
AZURE_AI_HOSTNAME=eastus.api.azureml.ms

# Local data directory
DATA_DIR=data
```

5. Place your Excel files in the `data` directory:
   - Employee data file (with "EmpID_Legacy_Country_Payments_Hourly" in the filename)
   - Payment terms file (with "Standby_Callout_Overtime_Shift_Payment" in the filename) 
   - Hours data file (with "Emp_Wage_Hours" in the filename)

## Usage

### Running the System

The main entry point for the system is the Azure AI Agent orchestrator:

```bash
python src/azure_agent_orchestrator.py
```

### Example Queries

#### HR Team Member Queries
- "What are the standby payment policies for UK employees?"
- "Are employees with Payment Terms XYZ eligible for overtime?"
- "What are the approval requirements for supplemental pay?"

#### People Manager Queries
- "Calculate overtime pay for employee EMP12345"
- "Analyze supplemental pay trends for my team"
- "Provide recommendations for optimizing standby arrangements"

#### Payroll Manager Queries
- "Identify any outliers in overtime claims for February 2025"
- "Compare supplemental pay between departments"
- "What percentage of supplemental pay is billable to clients?"

## Development

### Project Structure

```
dxc-suppay-agent/
│
├── config/                           # Configuration files
│   ├── agent_config.json             # Agent configuration
│   └── local_file_config.json        # Local file settings
│
├── data/                             # Data directory containing Excel files
│   ├── UK EmpID_Legacy_Country_Payments_Hourly Rate.xlsx  # Employee data
│   ├── UK Standby_Callout_Overtime_Shift_Payment.xlsx     # Payment terms
│   └── Emp_Wage_Hours_Sep24_Oct24_Nov24_Dec24_Jan25_Feb25.xlsx  # Hours data
│
├── src/                              # Source code
│   ├── agents/                       # Agent definitions
│   │   ├── policy_extraction_agent.py  # Policy extraction agent
│   │   ├── pay_calculation_agent.py    # Pay calculation agent
│   │   └── analytics_agent.py          # Analytics agent
│   │
│   ├── data_access/                  # Data access layer
│   │   ├── local_file_connector.py   # Local file access
│   │   └── excel_processor.py        # Excel file processing
│   │
│   ├── tools/                        # Agent tools
│   │   ├── code_interpreter.py       # Code interpreter wrapper
│   │   └── document_processor.py     # Document processing utilities
│   │
│   └── azure_agent_orchestrator.py   # Main orchestration logic
│
├── tests/                           # Unit and integration tests
└── samples/                         # Sample data and notebooks
```

### Adding New Features

To add new features to the system:

1. Create new agent capabilities in the appropriate agent files
2. Update the Azure AI Agent orchestrator to route requests to the new capabilities
3. Add any necessary tools or data access methods

## License

This project is proprietary to DXC Technology.

## Contact

For more information, contact the DXC AI Team. 