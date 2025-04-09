# DXC Supplemental Pay AI Agent Project Structure

```
dxc-suppay-agent/
│
├── .env                              # Environment variables (API keys, endpoints)
├── README.md                         # Project documentation
├── requirements.txt                  # Python dependencies
│
├── config/                           # Configuration files
│   ├── agent_config.json             # Agent configuration
│   └── local_file_config.json        # Local file connection settings
│
├── src/                              # Source code
│   ├── __init__.py
│   │
│   ├── agents/                       # Agent definitions
│   │   ├── __init__.py
│   │   ├── policy_extraction_agent.py  # Policy extraction agent
│   │   ├── pay_calculation_agent.py    # Pay calculation agent
│   │   └── analytics_agent.py          # Analytics agent
│   │
│   ├── data_access/                  # Data access layer
│   │   ├── __init__.py
│   │   ├── local_file_connector.py   # Local file access
│   │   └── excel_processor.py        # Excel file processing
│   │
│   ├── tools/                        # Agent tools
│   │   ├── __init__.py
│   │   ├── code_interpreter.py       # Code interpreter wrapper
│   │   └── document_processor.py     # Document processing utilities
│   │
│   └── azure_agent_orchestrator.py   # Main orchestration logic
│
├── tests/                           # Unit and integration tests
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_data_access.py
│   └── test_orchestration.py
│
└── samples/                         # Sample data and notebooks
    ├── notebooks/                   # Jupyter notebooks for examples
    └── data/                        # Sample Excel files for testing
```

## Key Files and Responsibilities

### Core Setup
- **requirements.txt**: Lists all required dependencies including Azure AI SDKs
- **.env**: Stores configuration like API keys, endpoints, and Azure AI Agent Service settings

### Agent Implementation
- **policy_extraction_agent.py**: Implements the agent for extracting and understanding policy documents
- **pay_calculation_agent.py**: Implements the agent for calculating pay based on policies and employee data
- **analytics_agent.py**: Implements the agent for analyzing trends and identifying outliers

### Data Access
- **local_file_connector.py**: Handles access to local files and documents
- **excel_processor.py**: Processes Excel files with pandas and provides data to agents

### Tools
- **code_interpreter.py**: Wrapper for the code interpreter tool to analyze data
- **document_processor.py**: Utilities for document parsing and text extraction

### Orchestration
- **azure_agent_orchestrator.py**: Main logic for coordinating agent activities and managing the Azure AI Agent Service integration 