import logging
import os
import json
import glob
from typing import Dict, Any, List, Optional
import requests
import asyncio
from azure.identity import DefaultAzureCredential
from azure.ai.projects.models import CodeInterpreterTool, FilePurpose
from pathlib import Path

class AzureAgentDefinitions:
    """
    Management class for Azure AI Project Agent definitions.
    
    This class handles the definitions of various agents used in the supplemental pay system,
    including the policy extraction agent, pay calculation agent, and analytics agent.
    """
    
    def __init__(self, config: Dict[str, Any], debug_mode: bool = False):
        """
        Initialize the Azure Agent Definitions.
        
        Args:
            config: Configuration dictionary
            debug_mode: If True, enables additional logging and debugging features
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Azure Agent Definitions")
        
        # Store configuration
        self.config = config
        self.debug_mode = debug_mode
        
        # Define agent types and their instructions
        self.agent_instructions = {
            "policy_extraction_agent": self._get_policy_extraction_instructions(),
            "pay_calculation_agent": self._get_pay_calculation_instructions(),
            "analytics_agent": self._get_analytics_instructions()
        }
        
        # Set up agent API endpoint
        self.credential = DefaultAzureCredential()
        self.subscription_id = config.get("azure_subscription_id", os.getenv("AZURE_SUBSCRIPTION_ID"))
        self.resource_group = config.get("azure_resource_group", os.getenv("AZURE_RESOURCE_GROUP"))
        self.project_name = config.get("azure_project_name", os.getenv("AZURE_PROJECT_NAME"))
        self.hostname = config.get("azure_ai_hostname", os.getenv("AZURE_AI_HOSTNAME", "eastus.api.azureml.ms"))
        
        # Construct the endpoint
        self.endpoint = f"https://{self.hostname}/agents/v1.0/subscriptions/{self.subscription_id}/resourceGroups/{self.resource_group}/providers/Microsoft.MachineLearningServices/workspaces/{self.project_name}"
        
        # Initialize project client for file uploads and agent creation
        self.project_client = None
        
        # Data directory for Excel files
        self.data_dir = config.get("local_files", {}).get("data_dir", os.getenv("DATA_DIR", "data"))
        
        self.logger.info("Azure Agent Definitions initialized")
        if self.debug_mode:
            self.logger.info(f"Debug mode enabled with endpoint: {self.endpoint}")
            self.logger.info(f"Using data directory: {self.data_dir}")
    
    def get_agent_instructions(self, agent_type: str) -> str:
        """
        Get the instructions for a specific agent type.
        
        Args:
            agent_type: Type of agent (policy_extraction_agent, pay_calculation_agent, analytics_agent)
            
        Returns:
            Instructions for the specified agent
        """
        return self.agent_instructions.get(agent_type, "")
    
    def _get_policy_extraction_instructions(self) -> str:
        """
        Get the instructions for the policy extraction agent.
        
        Returns:
            Instructions for the policy extraction agent
        """
        return """
        You are a Policy Extraction Agent for DXC's supplemental pay system.
        
        Your responsibilities:
        1. Extract relevant information from HR policy documents
        2. Determine eligibility criteria for supplemental pay
        3. Identify required documentation and approval workflows
        4. Interpret policy changes and their implications
        5. Answer questions about supplemental pay policies
        
        Guidelines:
        - Base your responses on the official policy documents only
        - Cite specific sections when providing information
        - Clearly distinguish between requirements and recommendations
        - If a policy is ambiguous, acknowledge the ambiguity
        - Do not make assumptions about policies that aren't explicitly stated
        - Format your responses in a clear, structured manner
        
        When analyzing documents:
        1. Identify the key policy points
        2. Note eligibility criteria and exceptions
        3. Outline required documentation
        4. Explain approval workflows
        5. Highlight any recent changes or updates
        
        Always maintain confidentiality and only share information on a need-to-know basis.
        """
    
    def _get_pay_calculation_instructions(self) -> str:
        """
        Get the instructions for the pay calculation agent.
        
        Returns:
            Instructions for the pay calculation agent
        """
        return """
        You are a Pay Calculation Agent for DXC's supplemental pay system.
        
        Your responsibilities:
        1. Calculate supplemental pay amounts based on policy guidelines
        2. Apply appropriate tax withholdings and deductions
        3. Verify calculation inputs for accuracy
        4. Generate payment records for accounting
        5. Explain calculation methodology when requested
        
        Guidelines:
        - Follow the exact formulas specified in the pay policies
        - Apply current tax rates and withholding requirements
        - Round all calculations to the nearest cent
        - Double-check all inputs before performing calculations
        - Document all calculation steps for audit purposes
        - If data is missing, indicate what is needed rather than making assumptions
        
        When performing calculations:
        1. Verify employee eligibility
        2. Identify the correct supplemental pay category
        3. Apply the appropriate calculation formula
        4. Calculate required tax withholdings
        5. Generate a detailed breakdown of the calculation
        
        Maintain accuracy and transparency in all calculations.
        """
    
    def _get_analytics_instructions(self) -> str:
        """
        Get the instructions for the analytics agent.
        
        Returns:
            Instructions for the analytics agent
        """
        return """
        You are an Analytics Agent for DXC's supplemental pay system.
        
        Your responsibilities:
        1. Analyze supplemental pay data to identify trends and patterns
        2. Generate reports on supplemental pay distribution
        3. Provide insights on budget utilization
        4. Identify potential policy compliance issues
        5. Create visualizations of key metrics
        
        Guidelines:
        - Use appropriate statistical methods for analysis
        - Ensure all reports are based on complete and accurate data
        - Present findings in clear, actionable language
        - Include confidence levels and limitations in your analysis
        - Protect sensitive information in all reports
        - Focus on trends and patterns rather than individual cases
        
        When analyzing data:
        1. Verify data completeness and quality
        2. Apply appropriate statistical methods
        3. Identify significant trends and outliers
        4. Connect findings to business impact
        5. Provide actionable recommendations
        
        Always include context and limitations with your findings.
        """
    
    async def deploy_agents(self) -> Dict[str, str]:
        """
        Deploy agents to Azure AI Agent Service.
        
        Creates or updates Azure AI Agents using the current API (2024-12-01-preview)
        
        Returns:
            Dictionary of agent names to agent IDs
        """
        self.logger.info("Deploying agents to Azure AI Agent Service")
        
        # Initialize the project client if not already done
        if not self.project_client:
            self._initialize_project_client()
        
        # Get authentication token for direct API calls
        token = self.credential.get_token("https://ml.azure.com/.default").token
        
        # Headers for API requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # Dictionary to store agent IDs
        agent_ids = {}
        
        # Find and upload Excel files from the data directory
        uploaded_files = await self._upload_excel_files_async()
        if not uploaded_files:
            self.logger.warning("No Excel files were uploaded. Code Interpreter will have limited functionality.")
        else:
            self.logger.info(f"Successfully uploaded {len(uploaded_files)} Excel files for Code Interpreter")
        
        # Configure Code Interpreter tool with the uploaded files
        code_interpreter = CodeInterpreterTool(file_ids=[f.id for f in uploaded_files])
        
        # Deploy each agent type
        for agent_type, instructions in self.agent_instructions.items():
            self.logger.info(f"Deploying agent: {agent_type}")
            
            # Get model name with fallbacks
            model_name = self._get_model_name()
            
            try:
                # Create or update the agent using SDK approach
                agent = self.project_client.agents.create_agent(
                    model=model_name,
                    name=agent_type,
                    instructions=instructions,
                    tools=code_interpreter.definitions,
                    tool_resources=code_interpreter.resources
                )
                
                agent_ids[agent_type] = agent.id
                self.logger.info(f"Successfully deployed agent {agent_type} with ID {agent.id}")
                
            except Exception as e:
                self.logger.error(f"Error deploying agent {agent_type}: {str(e)}")
                # Fall back to direct API call if SDK fails
                try:
                    # Configure agent data
                    agent_data = {
                        "instructions": instructions,
                        "name": agent_type,
                        "tools": [{"type": "code_interpreter"}],
                        "model": model_name,
                        "tool_resources": {
                            "code_interpreter": {
                                "file_ids": [f.id for f in uploaded_files]
                            }
                        }
                    }
                    
                    if self.debug_mode:
                        # In debug mode, log more details of the request
                        agent_data_log = agent_data.copy()
                        agent_data_log["instructions"] = "[REDACTED]"
                        self.logger.debug(f"Agent data: {json.dumps(agent_data_log, indent=2)}")
                    
                    # Create or update the agent
                    url = f"{self.endpoint}/assistants?api-version=2024-12-01-preview"
                    response = await self._make_async_request("POST", url, headers, json.dumps(agent_data))
                    
                    if response and response.get("id"):
                        agent_ids[agent_type] = response["id"]
                        self.logger.info(f"Successfully deployed agent {agent_type} with ID {response['id']} via API")
                    else:
                        self.logger.error(f"Failed to deploy agent {agent_type}, response: {response}")
                
                except Exception as api_e:
                    self.logger.error(f"Error deploying agent {agent_type} via API: {str(api_e)}")
        
        if not agent_ids:
            raise Exception("Failed to deploy any agents")
        
        return agent_ids
    
    def _initialize_project_client(self):
        """
        Initialize the Azure AI Project client for file uploads and agent creation.
        """
        try:
            # Import required packages
            from azure.ai.projects import AIProjectClient
            
            # Construct the connection string
            conn_str = f"{self.hostname};{self.subscription_id};{self.resource_group};{self.project_name}"
            
            # Initialize the project client
            self.project_client = AIProjectClient.from_connection_string(
                credential=self.credential,
                conn_str=conn_str
            )
            
            self.logger.info("Successfully initialized AIProjectClient for file uploads")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize AIProjectClient: {str(e)}")
            raise
    
    async def _upload_excel_files_async(self):
        """
        Find Excel files in the data directory and upload them for Code Interpreter.
        
        Returns:
            List of uploaded file objects
        """
        if not self.project_client:
            self._initialize_project_client()
        
        # Find Excel files in the data directory
        excel_files = []
        try:
            # Look for .xlsx files
            excel_pattern = os.path.join(self.data_dir, "**", "*.xlsx")
            excel_files.extend(glob.glob(excel_pattern, recursive=True))
            
            # Also look for .xls files
            xls_pattern = os.path.join(self.data_dir, "**", "*.xls")
            excel_files.extend(glob.glob(xls_pattern, recursive=True))
            
            # And .csv files, which Code Interpreter can also handle
            csv_pattern = os.path.join(self.data_dir, "**", "*.csv")
            excel_files.extend(glob.glob(csv_pattern, recursive=True))
            
            if not excel_files:
                self.logger.warning(f"No Excel or CSV files found in {self.data_dir}")
                return []
            
            self.logger.info(f"Found {len(excel_files)} Excel/CSV files: {', '.join(os.path.basename(f) for f in excel_files)}")
        except Exception as e:
            self.logger.error(f"Error finding Excel files: {str(e)}")
            return []
        
        # Upload each file
        uploaded_files = []
        for file_path in excel_files:
            try:
                self.logger.info(f"Uploading file: {file_path}")
                uploaded_file = self.project_client.agents.upload_file_and_poll(
                    file_path=file_path,
                    purpose=FilePurpose.AGENTS
                )
                
                uploaded_files.append(uploaded_file)
                self.logger.info(f"Successfully uploaded {os.path.basename(file_path)} with ID: {uploaded_file.id}")
                
            except Exception as e:
                self.logger.error(f"Error uploading file {file_path}: {str(e)}")
        
        return uploaded_files
    
    def _get_model_name(self) -> str:
        """
        Get the model name to use for agent creation.
        Always returns "gpt-4o" regardless of configuration.
        
        Returns:
            The model name to use
        """
        # Always use gpt-4o per requirements
        model_name = "gpt-4o"
        
        # Log original configuration value for debugging
        if self.debug_mode:
            openai_config = self.config.get("azure_openai", {})
            configured_model = openai_config.get("deployment_name")
            env_model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            
            if configured_model and configured_model != model_name:
                self.logger.info(f"Overriding configured model '{configured_model}' with 'gpt-4o'")
            elif env_model and env_model != model_name:
                self.logger.info(f"Overriding environment model '{env_model}' with 'gpt-4o'")
                
        self.logger.info(f"Using model: {model_name}")
        return model_name
    
    async def _make_async_request(self, method: str, url: str, headers: Dict[str, str], data: str = None) -> Dict[str, Any]:
        """
        Make an async HTTP request to the Azure AI Agent Service API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            headers: Request headers
            data: Request data (JSON string)
            
        Returns:
            Response data as dictionary
        """
        loop = asyncio.get_event_loop()
        
        def _make_request():
            try:
                log_level = logging.INFO if self.debug_mode else logging.DEBUG
                self.logger.log(log_level, f"Making {method} request to {url}")
                if data and self.debug_mode:
                    # In debug mode, log more details but redact sensitive info
                    try:
                        data_dict = json.loads(data)
                        if "instructions" in data_dict:
                            data_dict["instructions"] = "[REDACTED]"
                        self.logger.debug(f"Request data: {json.dumps(data_dict, indent=2)}")
                    except:
                        pass
                
                if method == "GET":
                    response = requests.get(url, headers=headers)
                elif method == "POST":
                    response = requests.post(url, headers=headers, data=data)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, data=data)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, data=data)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")
                
                # Check if response is successful
                try:
                    response.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    # Log the error response content
                    self.logger.error(f"HTTP Error: {e}")
                    try:
                        error_content = response.json()
                        self.logger.error(f"Error response: {json.dumps(error_content, indent=2)}")
                    except:
                        self.logger.error(f"Error response text: {response.text}")
                    raise
                
                # Parse JSON response
                try:
                    return response.json()
                except ValueError:
                    # Handle non-JSON responses
                    if response.text.strip():
                        self.logger.warning(f"Non-JSON response: {response.text}")
                        return {"text": response.text}
                    return {}
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error: {str(e)}")
                raise
        
        # Run the request in the executor to avoid blocking
        return await loop.run_in_executor(None, _make_request) 