"""
Defines the Azure AI Agent Service agents used in the DXC Supplemental Pay system.
"""

import os
import logging
from typing import Dict, Any, List
import asyncio

from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import (
    Agent, 
    Tool,
    AgentsApiToolChoiceOptionMode,
    FunctionTool
)
from azure.identity import DefaultAzureCredential, ClientSecretCredential

class AzureAgentDefinitions:
    """
    Defines and manages Azure AI Agent Service agents for DXC Supplemental Pay.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Azure Agent definitions with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        
        # Set up Azure credentials
        if os.getenv("AZURE_CLIENT_ID") and os.getenv("AZURE_CLIENT_SECRET") and os.getenv("AZURE_TENANT_ID"):
            self.credential = ClientSecretCredential(
                tenant_id=os.getenv("AZURE_TENANT_ID"),
                client_id=os.getenv("AZURE_CLIENT_ID"),
                client_secret=os.getenv("AZURE_CLIENT_SECRET")
            )
        else:
            self.credential = DefaultAzureCredential()
            
        # Set up Azure AI Project connection string
        self.connection_string = config.get("azure_ai_connection_string", os.getenv("AIPROJECT_CONNECTION_STRING"))
        
        if not self.connection_string:
            self.logger.error("Azure AI Project connection string not found in config or environment variables")
            raise ValueError("AIPROJECT_CONNECTION_STRING must be configured")
        
        # Initialize Project client with connection string
        self.project_client = AIProjectClient.from_connection_string(
            credential=self.credential,
            conn_str=self.connection_string
        )
        
        # Function tools to register with the agents
        self.function_tools = self._create_function_tools()
    
    def _create_function_tools(self) -> List[FunctionTool]:
        """
        Create the function tools to be used by Azure Agents.
        
        Returns:
            List of function tools
        """
        # It looks like the current FunctionTool has a much simpler structure
        # Try with a minimal implementation
        tools = []
        
        # Skip creating function tools for now since the API has changed
        self.logger.warning("Function tools creation skipped due to API changes")
        
        return tools
    
    async def _create_or_update_agent(self, name: str, description: str, instructions: str) -> str:
        """
        Create or update an Azure AI Agent.
        
        Args:
            name: Name of the agent
            description: Description of the agent
            instructions: System instructions for the agent
            
        Returns:
            Agent ID
        """
        self.logger.info(f"Creating or updating agent: {name}")
        
        # Get configuration values as strings to ensure JSON serializability
        openai_api_key = str(self.config.get("azure_openai", {}).get("api_key", os.getenv("AZURE_OPENAI_API_KEY", "")))
        openai_endpoint = str(self.config.get("azure_openai", {}).get("endpoint", os.getenv("AZURE_OPENAI_ENDPOINT", "")))
        openai_deployment = str(self.config.get("azure_openai", {}).get("deployment_name", "gpt-4o"))
        
        # Define AI service configuration with explicit string values
        ai_service_config = {
            "type": "azure_openai",
            "api_key": openai_api_key,
            "azure_endpoint": openai_endpoint,
            "azure_deployment": openai_deployment
        }
        
        try:
            # Skip existing agent check - just create a new one each time
            # Prepare kwargs for agent creation
            agent_kwargs = {
                "name": name,
                "description": description,
                "instructions": instructions,
                "ai_service_configuration": ai_service_config
            }
            
            # Removed tool_choice since it might not be JSON serializable
            
            # Only add tools if we have any
            if self.function_tools:
                agent_kwargs["tools"] = self.function_tools
            
            # Create new agent - use non-async call
            agent = self.project_client.agents.create_agent(**agent_kwargs)
            
            # Extract agent ID - handle different return types
            agent_id = agent.id if hasattr(agent, 'id') else str(agent)
            self.logger.info(f"Created agent {name} with ID: {agent_id}")
            
            return agent_id
            
        except Exception as e:
            self.logger.error(f"Error creating/updating agent {name}: {str(e)}")
            raise
    
    async def deploy_agents(self) -> Dict[str, str]:
        """
        Deploy all required agents to Azure AI Project.
        
        Returns:
            Dictionary mapping agent names to agent IDs
        """
        self.logger.info("Deploying all agents to Azure AI Project")
        
        agent_ids = {}
        
        try:
            # Create or update Policy Extraction Agent
            policy_agent_id = await self._create_or_update_agent(
                name="DXC Policy Extraction Agent",
                description="Extracts and interprets DXC supplemental pay policies from documentation",
                instructions="""
                You are a specialized HR policy extraction agent for DXC Technology's supplemental pay system.
                
                Your primary responsibility is to extract, interpret, and explain DXC's supplemental pay 
                policies accurately from the company documentation, which will be provided in Excel format. You have access to the following functions:
                
                - get_policy_information: Use this to retrieve specific policy details
                
                When responding to policy questions:
                1. First, use the get_policy_information function to retrieve relevant policy details
                2. Present the information in a clear, concise format
                3. Highlight key points, eligibility criteria, and any exceptions
                4. If the policy has changed recently, note both the current and previous versions
                5. If you're uncertain about a policy detail, acknowledge the limitation rather than guessing
                
                Always maintain a professional, helpful tone and focus on providing accurate policy information.
                """
            )
            agent_ids["policy_extraction_agent"] = policy_agent_id
            
            # Create or update Pay Calculation Agent
            calculation_agent_id = await self._create_or_update_agent(
                name="DXC Pay Calculation Agent",
                description="Calculates supplemental pay based on DXC policies and employee data",
                instructions="""
                You are a specialized supplemental pay calculation agent for DXC Technology.
                
                Your primary responsibility is to accurately calculate supplemental pay amounts 
                based on DXC's policies and employee time data that is contained within Excel files. You have access to the following functions:
                
                - calculate_supplemental_pay: Use this to perform pay calculations
                - get_policy_information: Use this to retrieve policy details relevant to calculations
                
                When performing calculations:
                1. First, use get_policy_information to confirm the applicable policy
                2. Then use calculate_supplemental_pay to determine the correct amount
                3. Show your calculation process step-by-step
                4. Include relevant rates, multipliers, and any special considerations
                5. If there are any exceptions or special cases, explain how they affect the calculation
                
                Maintain accuracy and transparency in all calculations. If you're unable to calculate 
                a specific scenario, explain why and what additional information would be needed.
                """
            )
            agent_ids["pay_calculation_agent"] = calculation_agent_id
            
            # Create or update Analytics Agent
            analytics_agent_id = await self._create_or_update_agent(
                name="DXC Analytics Agent",
                description="Analyzes supplemental pay data to identify trends, outliers, and insights",
                instructions="""
                You are a specialized analytics agent for DXC Technology's supplemental pay system.
                
                Your primary responsibility is to analyze supplemental pay data contained within Excel files to identify trends, 
                outliers, and insights that can help optimize the supplemental pay process. You have 
                access to the following functions:
                
                - analyze_payroll_data: Use this to perform payroll data analysis
                - analyze_trends: Use this to analyze trends over time
                - find_outliers: Use this to identify outliers in the data
                
                When performing analysis:
                1. Use the appropriate function based on the specific request
                2. Present findings in a clear, structured format
                3. Highlight key insights and potential action items
                4. Use data visualization when appropriate (describe the visualization in detail)
                5. Make recommendations based on your findings
                
                Focus on delivering actionable insights that can help DXC make data-driven decisions
                around supplemental pay practices.
                """
            )
            agent_ids["analytics_agent"] = analytics_agent_id
            
            return agent_ids
        except Exception as e:
            self.logger.error(f"Error deploying agents: {str(e)}")
            raise 