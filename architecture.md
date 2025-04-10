# DXC Supplemental Pay AI Agent System Architecture

## System Overview

The DXC Supplemental Pay AI Agent System is designed to help HR personnel, people managers, and payroll managers analyze supplemental pay data, identify trends and outliers, and make actionable recommendations based on DXC policies. The system leverages Azure AI Agent Service and Microsoft Semantic Kernel to process policy documents and Excel files from both local directories and SharePoint, providing intelligent insights through specialized AI agents.

## Architecture Components

### 1. Core Technologies
- **Azure AI Agent Service**: For creating and managing AI agents with specific capabilities
- **Azure AI Foundry SDK**: For building and managing AI models and workflows
- **Microsoft Semantic Kernel**: For orchestrating semantic functions and plugins
- **GPT-4o**: As the core large language model
- **Python**: As the primary development language
- **Flask**: For the API server that interfaces with the frontend

### 2. System Modules

#### Data Access Layer
- **Local File Connector**: For accessing files from local directories
- **SharePoint Connector**: For accessing files from SharePoint libraries
- **Excel Processor**: For parsing and analyzing supplemental pay data in Excel files
- **Data transformation services**: For agent consumption

#### Agent Core
- **Policy Extraction Agent**: Processes policy documents to extract rules and guidelines
- **Pay Calculation Agent**: Analyzes employee data and applies policy rules
- **Analytics Agent**: Identifies trends, outliers, and opportunities for improvement
- **Intelligent Orchestrator Agent**: Routes queries to the appropriate specialized agent

#### Plugins Layer
- **Policy Plugin**: Plugin for policy extraction and validation functions
- **Calculation Plugin**: Plugin for pay calculation functions
- **Analytics Plugin**: Plugin for data analysis functions

#### Tool Execution
- **Agent Tool Executor**: Manages and executes tools for agents
- Code interpreter for data analysis
- Document processor for text extraction

## Data Flow

1. User submits a query through the Flask API server
2. The API server forwards the request to the Azure Agent Orchestrator
3. The Intelligent Orchestrator Agent analyzes the query and routes it to the appropriate specialized agent
4. The specialized agent accesses data through the Data Access Layer (local files or SharePoint)
5. The agent uses the appropriate plugins and tools to process the data
6. The Excel Processor parses and analyzes Excel files
7. The agent generates a response based on the extracted policies and data analysis
8. The response is returned to the user through the API server

## Agent Capabilities

### Policy Extraction Agent
- Access and process policy documents from local files or SharePoint
- Extract relevant pay policies
- Structure policy data for reasoning
- Validate employee/organization eligibility

### Pay Calculation Agent
- Process employee data from Excel files
- Apply policy rules extracted by Policy Extraction Agent
- Calculate appropriate supplemental pay
- Generate approval recommendations

### Analytics Agent
- Identify trends in supplemental pay data
- Flag outliers and discrepancies
- Track client billable vs. internally absorbed costs
- Generate insights for process improvement

### Intelligent Orchestrator Agent
- Analyze user queries to determine intent
- Route queries to the appropriate specialized agent
- Coordinate agent activities
- Provide fallback mechanisms when routing fails

## Integration Components

### API Server
- Provides RESTful API endpoints for frontend integration
- Handles file uploads
- Manages agent deployment and execution
- Provides health check and error handling

### Web UI
- User interface for interacting with the system
- File upload capabilities
- Chat interface for queries
- Role-based views for HR, managers, and payroll

## Security Considerations
- All data is processed securely and not stored unnecessarily
- All recommendations are traceable to source policies
- Access control through Azure AI Agent Service authentication
- Secure handling of API keys and sensitive configurations

## Implementation Architecture
- Configuration-driven setup with environment variables and JSON config files
- Asynchronous operations for improved performance
- Caching mechanisms for repeated queries
- Error handling and logging throughout the system
- Tool execution framework for agent capabilities 