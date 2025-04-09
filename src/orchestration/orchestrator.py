import os
import json
import logging
import datetime
import re
import sys
from typing import Dict, Any, List, Optional
import time

# Add the project root to Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.functions.kernel_function import KernelFunction

from src.agents.policy_extraction_agent import PolicyExtractionAgent
from src.agents.pay_calculation_agent import PayCalculationAgent
from src.agents.analytics_agent import AnalyticsAgent
from src.agents.hr_agent import HRAgent
from src.agents.payroll_agent import PayrollAgent
from src.agents.manager_agent import ManagerAgent

from src.data_access.local_file_connector import LocalFileConnector
from src.data_access.excel_processor import ExcelProcessor

# For Azure agent integration
from src.orchestration.azure_agent_orchestrator import AzureAgentOrchestrator
from src.agents.azure_agents_definition import AzureAgentDefinitions

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

class SupplementalPayOrchestrator:
    """
    Orchestrates various agents to handle HR, payroll, and management requests
    related to supplemental pay.
    """

    def __init__(self, config_file_path: str):
        """
        Initialize the orchestrator with a configuration file.

        Args:
            config_file_path: Path to the configuration file
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing SupplementalPayOrchestrator")
        
        # Load configuration
        self.config = self._load_config(config_file_path)
        
        # Initialize the kernel
        self.kernel = self._initialize_kernel()
        
        # Initialize agents
        self.hr_agent = HRAgent(self.kernel, self.config)
        self.payroll_agent = PayrollAgent(self.kernel, self.config)
        self.manager_agent = ManagerAgent(self.kernel, self.config)
        
        # Initialize Azure Agent Orchestrator if configured
        self.azure_agent_orchestrator = None
        if self.config.get("use_azure_agents", False):
            self.logger.info("Initializing Azure Agent Orchestrator")
            try:
                self.azure_agent_orchestrator = AzureAgentOrchestrator(self.config)
                self.logger.info("Azure Agent Orchestrator initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize Azure Agent Orchestrator: {str(e)}")
        
        self.logger.info("Supplemental Pay Orchestrator initialized")
    
    def _load_config(self, config_file_path: str) -> Dict[str, Any]:
        """
        Load configuration from file and process environment variable placeholders.
        
        Args:
            config_file_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        self.logger.info(f"Loading configuration from {config_file_path}")
        
        try:
            with open(config_file_path, 'r') as f:
                config = json.load(f)
                
            # Process environment variable placeholders
            self._process_env_vars(config)
            
            return config
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {config_file_path}")
            # Create default configuration
            config = {
                "azure_openai": {
                    "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
                    "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
                    "deployment_name": os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
                },
                "logging": {
                    "level": os.getenv("LOG_LEVEL", "INFO")
                },
                "agents": {
                    "use_azure_agents": True
                }
            }
            
            # Save default configuration
            with open(config_file_path, 'w') as f:
                json.dump(config, f, indent=4)
                
            self.logger.info(f"Created default configuration file: {config_file_path}")
            return config
        except json.JSONDecodeError:
            self.logger.error(f"Error parsing configuration file: {config_file_path}")
            raise
    
    def _process_env_vars(self, config: Dict[str, Any]) -> None:
        """
        Process environment variable placeholders in configuration.
        
        Args:
            config: Configuration dictionary
        """
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, (dict, list)):
                    self._process_env_vars(value)
                elif isinstance(value, str) and value.startswith("${") and value.endswith("}"):
                    env_var = value[2:-1]
                    config[key] = os.getenv(env_var, "")
        elif isinstance(config, list):
            for i, item in enumerate(config):
                if isinstance(item, (dict, list)):
                    self._process_env_vars(item)
                elif isinstance(item, str) and item.startswith("${") and item.endswith("}"):
                    env_var = item[2:-1]
                    config[i] = os.getenv(env_var, "")
    
    async def _initialize_kernel(self) -> sk.Kernel:
        """
        Initialize the kernel for the orchestrator.
        
        Returns:
            Initialized kernel
        """
        self.logger.info("Initializing kernel")
        
        kernel = sk.Kernel()
        
        # Add Azure OpenAI as a kernel source
        kernel.add_service(
            AzureChatCompletion(
                deployment_name=self.config["azure_openai"]["deployment_name"],
                api_key=self.config["azure_openai"]["api_key"],
                endpoint=self.config["azure_openai"]["endpoint"]
            )
        )
        
        self.logger.info("Kernel initialized")
        return kernel
    
    def process_hr_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a request from HR.

        Args:
            request: The HR request
            context: Additional context for the request

        Returns:
            Response from the HR agent
        """
        self.logger.info(f"Processing HR request: {request}")
        
        # Use Azure Agent if configured, otherwise use local agent
        if self.azure_agent_orchestrator and self.config.get("use_azure_agents_for_hr", False):
            self.logger.info("Using Azure Agent for HR request")
            return self.azure_agent_orchestrator.run_agent("policy_extraction_agent", request)
        
        return self.hr_agent.process_request(request, context or {})

    def process_payroll_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a request from payroll.

        Args:
            request: The payroll request
            context: Additional context for the request

        Returns:
            Response from the payroll agent
        """
        self.logger.info(f"Processing payroll request: {request}")
        
        # Use Azure Agent if configured, otherwise use local agent
        if self.azure_agent_orchestrator and self.config.get("use_azure_agents_for_payroll", False):
            self.logger.info("Using Azure Agent for payroll request")
            return self.azure_agent_orchestrator.run_agent("pay_calculation_agent", request)
        
        return self.payroll_agent.process_request(request, context or {})

    def process_manager_request(self, request: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a request from a manager.

        Args:
            request: The manager request
            context: Additional context for the request

        Returns:
            Response from the manager agent
        """
        self.logger.info(f"Processing manager request: {request}")
        
        # Use Azure Agent if configured, otherwise use local agent
        if self.azure_agent_orchestrator and self.config.get("use_azure_agents_for_manager", False):
            self.logger.info("Using Azure Agent for manager request")
            return self.azure_agent_orchestrator.run_agent("analytics_agent", request)
        
        return self.manager_agent.process_request(request, context or {})
    
    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a generic request and route to the appropriate handler.
        
        Args:
            request: Request data
            
        Returns:
            Response data
        """
        self.logger.info(f"Processing request: {request.get('request_id', 'unknown')}")
        
        # Validate request
        if not request.get("user_role"):
            return {
                "status": "error",
                "message": "User role not specified",
                "request_id": request.get("request_id")
            }
        
        if not request.get("query"):
            return {
                "status": "error",
                "message": "Query not specified",
                "request_id": request.get("request_id")
            }
        
        # Route to appropriate handler
        if request["user_role"] == "HR":
            return self.process_hr_request(request["query"])
        elif request["user_role"] == "Manager":
            return self.process_manager_request(request["query"])
        elif request["user_role"] == "Payroll":
            return self.process_payroll_request(request["query"])
        else:
            return {
                "status": "error",
                "message": f"Unsupported user role: {request['user_role']}",
                "request_id": request.get("request_id")
            }


# Main function to demonstrate usage
async def main():
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize orchestrator
    orchestrator = SupplementalPayOrchestrator("config.json")
    
    # Example HR request
    hr_response = await orchestrator.process_request(
        {
            "user_role": "HR",
            "query": "What are the current standby payment policies for UK employees?"
        }
    )
    print(f"HR Response: {hr_response}")
    
    # Example manager request
    manager_response = await orchestrator.process_request(
        {
            "user_role": "Manager",
            "query": "Calculate the appropriate supplemental pay for overtime work",
            "employee_id": "10000518"
        }
    )
    print(f"Manager Response: {manager_response}")
    
    # Example payroll request
    payroll_response = await orchestrator.process_request(
        {
            "user_role": "Payroll",
            "query": "Identify any outliers in this month's supplemental pay claims"
        }
    )
    print(f"Payroll Response: {payroll_response}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 