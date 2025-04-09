"""
Azure AI Agent Service based orchestrator for the DXC Supplemental Pay system.
This module orchestrates the Azure AI Agent Service agents.
"""

import os
import logging
from typing import Dict, Any, List, Optional
import json
import asyncio
import requests
import inspect

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

# Import existing agent implementations
from src.orchestration.azure_agent_definitions import AzureAgentDefinitions
from src.agents.agent_tool_executor import AgentToolExecutor

from src.agents.policy_extraction_agent import PolicyExtractionAgent
from src.agents.pay_calculation_agent import PayCalculationAgent
from src.agents.analytics_agent import AnalyticsAgent

from src.data_access.local_file_connector import LocalFileConnector
from src.data_access.excel_processor import ExcelProcessor

class DummyAgent:
    """A dummy agent implementation that does nothing. Used as a fallback."""
    
    async def _extract_policies(self, *args, **kwargs):
        """Dummy method for policy extraction"""
        return {"message": "Policy extraction not available"}
    
    async def validate_eligibility(self, *args, **kwargs):
        """Dummy method for eligibility validation"""
        return {"eligible": False, "reason": "Validation not available"}
    
    async def analyze_employee(self, *args, **kwargs):
        """Dummy method for employee analysis"""
        return "Employee analysis not available"
    
    async def analyze_team(self, *args, **kwargs):
        """Dummy method for team analysis"""
        return "Team analysis not available"
    
    async def calculate_pay(self, *args, **kwargs):
        """Dummy method for pay calculation"""
        return {"amount": 0, "message": "Pay calculation not available"}
    
    async def analyze_pay_data(self, *args, **kwargs):
        """Dummy method for pay data analysis"""
        return "Pay data analysis not available"
    
    async def analyze_trends(self, *args, **kwargs):
        """Dummy method for trend analysis"""
        return {"trends": [], "message": "Trend analysis not available"}
    
    async def find_outliers(self, *args, **kwargs):
        """Dummy method for outlier detection"""
        return {"outliers": [], "message": "Outlier detection not available"}
    
    async def analyze_billable_vs_internal(self, *args, **kwargs):
        """Dummy method for billable vs internal analysis"""
        return {"ratio": 0, "message": "Billable vs internal analysis not available"}

class AzureAgentOrchestrator:
    """
    Orchestrator for Azure AI Project agents.
    
    This class handles interactions with various Azure AI Project agents,
    manages agent execution, and processes responses.
    """
    
    def __init__(self, config_path_or_dict="config.json"):
        """
        Initialize the Azure Agent Orchestrator.
        
        Args:
            config_path_or_dict (str or dict): Path to the configuration file or direct configuration dictionary.
        """
        # Set up logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Initialize properties
        self.config = self._load_config(config_path_or_dict)
        self.project_client = None
        self.credential = None
        self.tool_executor = None
        self.agent_ids = {}  # Dictionary to map roles to agent IDs
        
        # Initialize Azure services
        self._initialize_azure_services()
        
        # Initialize agent definitions with the configuration
        self.agent_definitions = AzureAgentDefinitions(self.config)
        
        # Set default values for generation
        self.temperature = self.config.get("temperature", 0.7)
        self.top_p = self.config.get("top_p", 0.95)
        self.max_tokens = self.config.get("max_tokens", 4000)
        
        self.logger.info("Azure Agent Orchestrator initialized")
        
        # Initialize and set up tool_executor instance
        self._initialize_tool_executor()
        
        # Initialize semantic kernel
        self.kernel = self._initialize_kernel()
    
    def _load_config(self, config_path_or_dict) -> Dict[str, Any]:
        """Load configuration from a JSON file or directly from a dictionary.
        
        Args:
            config_path_or_dict (str or dict): Path to the configuration file or direct configuration dictionary.
            
        Returns:
            Dict[str, Any]: The configuration dictionary.
        """
        try:
            # Check if config_path_or_dict is already a dictionary
            if isinstance(config_path_or_dict, dict):
                self.logger.info("Using provided configuration dictionary")
                return config_path_or_dict
            
            # Otherwise, treat it as a file path
            with open(config_path_or_dict, 'r') as f:
                config = json.load(f)
            self.logger.info(f"Successfully loaded configuration from {config_path_or_dict}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to load configuration from {config_path_or_dict}: {str(e)}")
            raise

    def _initialize_azure_services(self):
        """Initialize Azure AI services including project client and agent IDs."""
        # Set up authentication
        self.credential = DefaultAzureCredential()
        
        # Set up agent API endpoint from config or environment variables
        self.subscription_id = self.config.get("azure_subscription_id", os.getenv("AZURE_SUBSCRIPTION_ID"))
        self.resource_group = self.config.get("azure_resource_group", os.getenv("AZURE_RESOURCE_GROUP"))
        self.project_name = self.config.get("azure_project_name", os.getenv("AZURE_PROJECT_NAME"))
        self.hostname = self.config.get("azure_ai_hostname", os.getenv("AZURE_AI_HOSTNAME", "eastus.api.azureml.ms"))
        
        # Construct the connection string for AIProjectClient
        conn_str = f"{self.hostname};{self.subscription_id};{self.resource_group};{self.project_name}"
        
        # Initialize the project client
        self.project_client = AIProjectClient.from_connection_string(
            credential=self.credential,
            conn_str=conn_str
        )
        self.logger.info("Successfully initialized AIProjectClient")
        
        # Initialize the agent IDs dictionary with role mappings
        agent_roles = {
            "hr": self.config.get("hr_agent_id", os.getenv("HR_AGENT_ID")),
            "manager": self.config.get("manager_agent_id", os.getenv("MANAGER_AGENT_ID")),
            "payroll": self.config.get("payroll_agent_id", os.getenv("PAYROLL_AGENT_ID"))
        }
        
        # Validate and store agent IDs
        for role, agent_id in agent_roles.items():
            if agent_id:
                self.agent_ids[role] = agent_id
                self.logger.info(f"Registered {role} agent with ID: {agent_id}")
            else:
                self.logger.warning(f"No agent ID found for role: {role}")
                
        # Initialize tool executor if needed
        if "tool_executor_config" in self.config:
            try:
                # This is a placeholder - implement based on your actual tool executor requirements
                self.tool_executor = None  # Replace with actual initialization
                self.logger.info("Tool executor initialized")
            except Exception as e:
                self.logger.error(f"Failed to initialize tool executor: {str(e)}")
    
    def _initialize_tool_executor(self):
        """
        Initialize the tool executor to handle tools for Azure AI agents.
        """
        try:
            # Ensure config is properly structured for local_files
            data_dir = None
            
            # Safely extract data_dir from config if available
            if isinstance(self.config, dict):
                local_files = self.config.get("local_files")
                if isinstance(local_files, dict):
                    data_dir = local_files.get("data_dir")
            
            # Use environment variable as fallback
            if not data_dir:
                data_dir = os.getenv("DATA_DIR", "data")
                
            self.logger.info(f"Using data directory: {data_dir}")
                
            # Initialize the required data components
            local_file_connector = LocalFileConnector(data_dir)
            excel_processor = ExcelProcessor(local_file_connector)
            
            # Initialize the agent implementations with proper error handling
            try:
                # Check if the PolicyExtractionAgent has a config parameter
                policy_agent_params = inspect.signature(PolicyExtractionAgent.__init__).parameters
                if 'config' in policy_agent_params:
                    policy_agent = PolicyExtractionAgent(self.config)
                else:
                    # Adjust initialization based on actual constructor parameters
                    policy_agent = PolicyExtractionAgent()
            except Exception as e:
                self.logger.warning(f"Could not initialize PolicyExtractionAgent: {str(e)}")
                policy_agent = None
                
            try:
                # Check if the PayCalculationAgent has a config parameter
                calculation_agent_params = inspect.signature(PayCalculationAgent.__init__).parameters
                if 'config' in calculation_agent_params:
                    calculation_agent = PayCalculationAgent(self.config)
                else:
                    # Adjust initialization based on actual constructor parameters
                    calculation_agent = PayCalculationAgent()
            except Exception as e:
                self.logger.warning(f"Could not initialize PayCalculationAgent: {str(e)}")
                calculation_agent = None
                
            try:
                # Check if the AnalyticsAgent has a config parameter
                analytics_agent_params = inspect.signature(AnalyticsAgent.__init__).parameters
                if 'config' in analytics_agent_params:
                    analytics_agent = AnalyticsAgent(self.config)
                else:
                    # Adjust initialization based on actual constructor parameters
                    analytics_agent = AnalyticsAgent()
            except Exception as e:
                self.logger.warning(f"Could not initialize AnalyticsAgent: {str(e)}")
                analytics_agent = None
            
            # Only create the tool executor if at least one agent is available
            if policy_agent or calculation_agent or analytics_agent:
                self.tool_executor = AgentToolExecutor(
                    policy_agent=policy_agent or DummyAgent(),
                    calculation_agent=calculation_agent or DummyAgent(),
                    analytics_agent=analytics_agent or DummyAgent()
                )
                self.logger.info("Tool executor initialized successfully")
            else:
                self.logger.warning("No agents could be initialized, tool executor will not be available")
                self.tool_executor = None
                
        except Exception as e:
            self.logger.error(f"Failed to initialize tool executor: {str(e)}")
            self.tool_executor = None
    
    def _initialize_kernel(self) -> sk.Kernel:
        """
        Initialize the Semantic Kernel with Azure OpenAI.
        Always uses "gpt-4o" as the deployment name.
        
        Returns:
            Initialized Semantic Kernel instance
        """
        kernel = sk.Kernel()
        
        try:
            # Add Azure OpenAI chat service - always use gpt-4o
            openai_service = AzureChatCompletion(
                deployment_name="gpt-4o",
                api_key=self.config["azure_openai"]["api_key"],
                endpoint=self.config["azure_openai"]["endpoint"],
                service_id="azure_chat_completion"
            )
            self.logger.info("Initialized Azure OpenAI service with model: gpt-4o")
        except Exception as e:
            self.logger.warning(f"Failed to initialize Azure OpenAI service with config: {str(e)}")
            self.logger.info("Attempting to initialize with direct environment variables, using model: gpt-4o")
            
            # Try with direct environment variables as a fallback, but still use gpt-4o
            openai_service = AzureChatCompletion(
                deployment_name="gpt-4o",
                api_key=os.getenv("AZURE_OPENAI_API_KEY"),
                endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
                service_id="azure_chat_completion"
            )
        
        # Add the service to the kernel
        kernel.add_service(openai_service)
        
        # Register plugins
        self._register_plugins(kernel)
        
        return kernel
    
    def _register_plugins(self, kernel: sk.Kernel) -> None:
        """
        Register Semantic Kernel plugins (skills).
        
        Args:
            kernel: Semantic Kernel instance
        """
        # Import here to avoid circular imports
        from src.plugins.policy_plugin import PolicyPlugin
        from src.plugins.calculation_plugin import CalculationPlugin
        from src.plugins.analytics_plugin import AnalyticsPlugin
        
        # Register plugins
        kernel.add_plugin(PolicyPlugin(), plugin_name="PolicyPlugin")
        kernel.add_plugin(CalculationPlugin(), plugin_name="CalculationPlugin")
        kernel.add_plugin(AnalyticsPlugin(), plugin_name="AnalyticsPlugin")
    
    async def deploy_agents(self) -> Dict[str, str]:
        """
        Deploy agents to Azure AI Agent Service.
        
        Returns:
            Dictionary of agent names to agent IDs
        """
        self.logger.info("Deploying agents to Azure AI Agent Service")
        
        # Deploy agents using the agent definitions
        try:
            agent_ids = await self.agent_definitions.deploy_agents()
            self.agent_ids = agent_ids
            self.logger.info(f"Deployed agents: {self.agent_ids}")
            return self.agent_ids
        except Exception as e:
            self.logger.error(f"Failed to deploy agents: {str(e)}")
            raise
    
    async def route_request(self, query: str, role: str = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Routes a user query to the appropriate agent based on the user's role.
        
        Args:
            query (str): The user query.
            role (str, optional): The user role. Defaults to None.
            parameters (Dict[str, Any], optional): Additional parameters to pass to the agent. Defaults to None.
            
        Returns:
            Dict[str, Any]: The response from the agent.
        """
        if parameters is None:
            parameters = {}
            
        self.logger.info(f"Routing request: {query} (role: {role})")
        
        # Get the appropriate agent based on the role
        agent_id = None
        if role == "HR":
            agent_id = self.agent_ids.get("hr")
            self.logger.info("Using HR agent")
        elif role == "manager":
            agent_id = self.agent_ids.get("manager")
            self.logger.info("Using Manager agent")
        elif role == "payroll":
            agent_id = self.agent_ids.get("payroll")
            self.logger.info("Using Payroll agent")
        else:
            self.logger.warning(f"Unknown role: {role}, using default agent")
            # Use the first agent as default if role not specified
            agent_id = next(iter(self.agent_ids.values()), None)
            
        if agent_id is None:
            error_message = f"No agent found for role: {role}"
            self.logger.error(error_message)
            return {"error": error_message}
            
        try:
            # Create a new thread
            thread = self.project_client.agents.create_thread()
            thread_id = thread.id
            self.logger.info(f"Created thread: {thread_id}")
            
            # Prepare message content with any additional parameters/context
            message_content = query
            if parameters:
                context_info = "\n\nContext:\n" + "\n".join([f"{k}: {v}" for k, v in parameters.items()])
                message_content += context_info
            
            # Call the new _run_agent method (with better error handling and debug options)
            disable_tools = parameters.get("disable_tools", False)
            response = await self._run_agent(thread_id, agent_id, message_content, disable_tools)
            
            # The _run_agent method now returns structured responses with either result or error
            if response is None:
                error_message = "Failed to get response from agent"
                self.logger.error(error_message)
                return {"error": error_message, "thread_id": thread_id}
            
            return response
            
        except Exception as e:
            error_message = f"Error routing request: {str(e)}"
            self.logger.error(error_message, exc_info=True)
            return {"error": error_message}
    
    async def _run_agent(self, thread_id: str, agent_id: str, message_content: str, disable_tools: bool = False) -> Dict[str, Any]:
        """Run a specific Azure AI agent on an existing thread with enhanced error handling and debug options.
        
        Args:
            thread_id (str): The thread ID to use
            agent_id (str): The agent ID to run
            message_content (str): The message content to process
            disable_tools (bool): If True, disable all tools to isolate agent issues

        Returns:
            dict: The result of the agent run and thread_id, or None if failed
        """
        if self.project_client is None:
            error_message = "AIProjectClient not initialized"
            self.logger.error(error_message)
            return {"error": error_message, "thread_id": thread_id}
            
        try:
            # Add the message to the thread
            self.logger.debug(f"Adding message to thread {thread_id}: {message_content[:100]}...")
            self.project_client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=message_content
            )
            self.logger.info(f"Added message to thread: {thread_id}")
            
            # Run the agent - optionally disable tools for debugging
            run_msg = f"Running agent {agent_id} on thread {thread_id}"
            if disable_tools:
                run_msg += " with tools disabled"
            self.logger.info(run_msg)
            
            # Set up run parameters
            run_params = {
                "thread_id": thread_id,
                "agent_id": agent_id
            }
            
            # Add tool_choice parameter if disabling tools
            if disable_tools:
                run_params["tool_choice"] = "none"
            
            # Start a run
            run = self.project_client.agents.create_run(**run_params)
            self.logger.info(f"Created run {run.id} with status: {run.status}")
            
            # Poll for run completion with exponential backoff
            max_retries = 15  # Increased from 10
            retry_count = 0
            retry_delay = 1  # Initial delay in seconds
            
            while retry_count < max_retries:
                # Get the current run status
                run = self.project_client.agents.get_run(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                current_status = run.status
                self.logger.debug(f"Run {run.id} status: {current_status}")
                
                if current_status == "completed":
                    self.logger.info(f"Run completed successfully: {run.id}")
                    break
                elif current_status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Run {run.id} ended with status: {current_status}"
                    self.logger.error(error_msg)
                    
                    # Try to get run steps for debugging
                    try:
                        steps = self.project_client.agents.list_run_steps(thread_id=thread_id, run_id=run.id)
                        step_info = [{"id": step.id, "status": step.status, "type": step.type} for step in steps.data]
                        self.logger.debug(f"Run steps: {json.dumps(step_info, indent=2)}")
                    except Exception as steps_error:
                        self.logger.error(f"Could not retrieve run steps: {str(steps_error)}")
                    
                    return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
                
                # Exponential backoff
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # Cap at 30 seconds max delay
                retry_count += 1
            
            if retry_count >= max_retries:
                error_msg = f"Maximum retries reached waiting for run {run.id} to complete"
                self.logger.error(error_msg)
                return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
            
            # Get the messages from the thread
            messages = self.project_client.agents.list_messages(thread_id=thread_id)
            
            if messages.data:
                # Filter for assistant messages only
                assistant_messages = [
                    msg for msg in messages.data 
                    if msg.role == "assistant" and hasattr(msg, "created_at")
                ]
                
                # Sort by creation time (newest first)
                assistant_messages.sort(key=lambda msg: msg.created_at, reverse=True)
                
                if assistant_messages:
                    last_message = assistant_messages[0]
                    
                    # Get the text content
                    if hasattr(last_message, "content") and last_message.content:
                        for content_part in last_message.content:
                            if hasattr(content_part, "text") and hasattr(content_part.text, "value"):
                                return {"result": content_part.text.value, "thread_id": thread_id, "run_id": run.id}
            
            error_msg = "No assistant messages found in thread or message format not recognized"
            self.logger.error(error_msg)
            return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
            
        except Exception as e:
            error_msg = f"Error running agent: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            # Return structured error response
            return {"error": error_msg, "thread_id": thread_id}

    async def _run_agent_via_sdk(self, agent_id: str, message_content: str, disable_tools: bool = False) -> Dict[str, Any]:
        """Run a specific Azure AI agent by creating a new thread and sending a message.
        
        This is a simplified method for direct agent testing without requiring a pre-existing thread.
        Uses the direct create_and_process_run pattern seen in official samples.
        
        Args:
            agent_id (str): The agent ID to run
            message_content (str): The message content to process
            disable_tools (bool): If True, disable all tools to isolate agent issues
            
        Returns:
            dict: The result of the agent run and thread_id, or error information
        """
        if self.project_client is None:
            error_message = "AIProjectClient not initialized"
            self.logger.error(error_message)
            return {"error": error_message}
        
        try:
            # Create a new thread for this SDK-based call
            thread = self.project_client.agents.create_thread()
            thread_id = thread.id
            self.logger.info(f"Created thread {thread_id} for SDK-based agent call")
            
            # Add the user message to the thread
            self.logger.debug(f"Adding message to thread {thread_id}: {message_content[:100]}...")
            self.project_client.agents.create_message(
                thread_id=thread_id,
                role="user",
                content=message_content
            )
            self.logger.info(f"Added message to thread: {thread_id}")
            
            # Set up run parameters
            run_params = {
                "thread_id": thread_id,
                "agent_id": agent_id
            }
            
            # Add tool_choice parameter if disabling tools
            if disable_tools:
                run_params["tool_choice"] = "none"
                self.logger.info("Running with tools disabled")
            
            # Start a run
            self.logger.info(f"Running agent {agent_id} on thread {thread_id}")
            run = self.project_client.agents.create_run(**run_params)
            self.logger.info(f"Created run {run.id} with status: {run.status}")
            
            # Poll for run completion with exponential backoff
            max_retries = 15
            retry_count = 0
            retry_delay = 1  # Initial delay in seconds
            
            while retry_count < max_retries:
                # Get the current run status
                run = self.project_client.agents.get_run(
                    thread_id=thread_id,
                    run_id=run.id
                )
                
                current_status = run.status
                self.logger.debug(f"Run {run.id} status: {current_status}")
                
                if current_status == "completed":
                    self.logger.info(f"Run completed successfully: {run.id}")
                    break
                elif current_status in ["failed", "cancelled", "expired"]:
                    error_msg = f"Run {run.id} ended with status: {current_status}"
                    self.logger.error(error_msg)
                    
                    # Try to get run steps for debugging
                    try:
                        steps = self.project_client.agents.list_run_steps(thread_id=thread_id, run_id=run.id)
                        step_info = [{"id": step.id, "status": step.status, "type": step.type} for step in steps.data]
                        self.logger.debug(f"Run steps: {json.dumps(step_info, indent=2)}")
                    except Exception as steps_error:
                        self.logger.error(f"Could not retrieve run steps: {str(steps_error)}")
                    
                    return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
                
                # Exponential backoff
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)  # Cap at 30 seconds max delay
                retry_count += 1
            
            if retry_count >= max_retries:
                error_msg = f"Maximum retries reached waiting for run {run.id} to complete"
                self.logger.error(error_msg)
                return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
            
            # Get the messages from the thread
            messages = self.project_client.agents.list_messages(thread_id=thread_id)
            
            if messages.data:
                # Filter for assistant messages only
                assistant_messages = [
                    msg for msg in messages.data 
                    if msg.role == "assistant" and hasattr(msg, "created_at")
                ]
                
                # Sort by creation time (newest first)
                assistant_messages.sort(key=lambda msg: msg.created_at, reverse=True)
                
                if assistant_messages:
                    last_message = assistant_messages[0]
                    
                    # Get the text content
                    if hasattr(last_message, "content") and last_message.content:
                        for content_part in last_message.content:
                            if hasattr(content_part, "text") and hasattr(content_part.text, "value"):
                                return {"result": content_part.text.value, "thread_id": thread_id, "run_id": run.id}
            
            error_msg = "No assistant messages found in thread or message format not recognized"
            self.logger.error(error_msg)
            return {"error": error_msg, "thread_id": thread_id, "run_id": run.id}
            
        except Exception as e:
            error_msg = f"Error in SDK-based agent run: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return {"error": error_msg} 