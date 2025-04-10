# DXC Supplemental Pay AI Agent Project Structure

```
dxc-suppay-agent/
│
├── .env                              # Environment variables (API keys, endpoints)
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
├── architecture.md                   # System architecture documentation
├── project_structure.md              # Project structure documentation
├── app.py                            # Main Flask API server
├── run_orchestrator.py               # Script to run the orchestrator directly
│
├── config/                           # Configuration files
│   ├── agent_config.json             # Agent configuration
│   ├── local_file_config.json        # Local file connection settings
│   ├── sharepoint_config.json        # SharePoint connection settings
│   └── semantic_kernel_config.json   # Semantic Kernel configuration
│
├── src/                              # Source code
│   ├── __init__.py
│   ├── simple_app.py                 # Simplified version of the application
│   │
│   ├── orchestration/                # Orchestration layer
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Base orchestrator class
│   │   ├── azure_agent_orchestrator.py # Azure AI Agent Service orchestrator
│   │   └── azure_agent_definitions.py  # Agent definitions for Azure AI Agent Service
│   │
│   ├── agents/                       # Agent implementations
│   │   ├── __init__.py
│   │   ├── agent_tool_executor.py    # Tool execution for agents
│   │   ├── azure_agents_definition.py  # Azure agent definitions
│   │   ├── policy_extraction_agent.py  # Policy extraction agent
│   │   ├── pay_calculation_agent.py    # Pay calculation agent
│   │   └── analytics_agent.py          # Analytics agent
│   │
│   ├── data_access/                  # Data access layer
│   │   ├── __init__.py
│   │   ├── local_file_connector.py   # Local file access
│   │   ├── sharepoint_connector.py   # SharePoint file access
│   │   └── excel_processor.py        # Excel file processing
│   │
│   └── plugins/                      # Semantic Kernel plugins
│       ├── __init__.py
│       ├── policy_plugin.py          # Policy extraction plugin
│       ├── calculation_plugin.py     # Pay calculation plugin
│       └── analytics_plugin.py       # Analytics plugin
│
├── tests/                           # Test files
│   ├── test_azure_agent_service.py
│   ├── test_azure_agents.py
│   ├── test_orchestrator.py
│   └── test_openai_completion.py
│
├── ui/                              # Frontend UI components
│
├── uploads/                         # Directory for uploaded files
│
├── data/                            # Sample data files
│
└── output/                          # Output files generated by the system
```

## Key Files and Responsibilities

### Core Setup
- **requirements.txt**: Lists all required dependencies including Azure AI SDKs and Semantic Kernel
- **.env**: Stores configuration like API keys, endpoints, and Azure AI Agent Service settings
- **app.py**: Main Flask API server that handles client requests and orchestrates the system

### Orchestration Layer
- **orchestrator.py**: Base orchestrator class with common functionality
- **azure_agent_orchestrator.py**: Orchestrates Azure AI Agent Service interactions and agent coordination
- **azure_agent_definitions.py**: Defines and deploys Azure AI agents

### Agent Implementation
- **policy_extraction_agent.py**: Implements the agent for extracting and understanding policy documents
- **pay_calculation_agent.py**: Implements the agent for calculating pay based on policies and employee data
- **analytics_agent.py**: Implements the agent for analyzing trends and identifying outliers
- **agent_tool_executor.py**: Manages tool execution for the agents

### Data Access
- **local_file_connector.py**: Handles access to local files and documents
- **sharepoint_connector.py**: Handles access to files and documents in SharePoint
- **excel_processor.py**: Processes Excel files with pandas and provides data to agents

### Plugins
- **policy_plugin.py**: Implements semantic functions for policy extraction and validation
- **calculation_plugin.py**: Implements semantic functions for pay calculation
- **analytics_plugin.py**: Implements semantic functions for data analysis

### API Server
- **app.py**: Main Flask API server that provides endpoints for:
  - Chat interface for agent interaction
  - File upload
  - Health check
- **run_orchestrator.py**: Script to run the orchestrator directly for testing

### Testing
- **test_azure_agent_service.py**: Tests for the Azure AI Agent Service integration
- **test_azure_agents.py**: Tests for the agent implementations
- **test_orchestrator.py**: Tests for the orchestrator functionality
- **test_openai_completion.py**: Tests for OpenAI completion functionality 