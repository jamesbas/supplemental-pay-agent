import os
import logging
from typing import Dict, Any, List, Optional
import json
import sys

# Add the project root to Python path to make imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions import KernelArguments
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

from src.data_access.local_file_connector import LocalFileConnector


class PolicyExtractionAgent:
    """
    Agent for extracting and processing DXC policy documents related to supplemental pay.
    Handles requests from HR team members.
    """
    
    def __init__(self, kernel: sk.Kernel, file_connector: LocalFileConnector):
        """
        Initialize the Policy Extraction Agent.
        
        Args:
            kernel: Initialized Semantic Kernel instance
            file_connector: File connector for accessing documents
        """
        self.logger = logging.getLogger(__name__)
        self.kernel = kernel
        self.file_connector = file_connector
        self.policy_cache = {}  # Cache for extracted policies
        
        # Set up extension data for Azure
        self.extension_data = {
            "api_type": "azure"
        }
        
        self.logger.info("Policy Extraction Agent initialized")
    
    async def _extract_policies(self, excel_files: List[str], query: str) -> Dict[str, Any]:
        """
        Extract policies from Excel files using Semantic Kernel.
        
        Args:
            excel_files: List of paths to Excel files
            query: User query to guide policy extraction
            
        Returns:
            Dictionary of extracted policies
        """
        self.logger.info(f"Extracting policies based on query: {query}")
        
        # Create a system message with instructions
        system_message = """
        You are a policy extraction assistant for DXC, specialized in extracting and interpreting supplemental pay policies.
        Your role is to help HR team members understand and apply the relevant policies for supplemental pay, vacation, overtime, stand-by, and call out.
        
        When processing a request:
        1. Extract the relevant pay policies based on the user's query
        2. Present the information in a clear, concise format
        3. Include all key details like eligibility, payment terms, and conditions
        
        Be specific and accurate in your responses. If a policy doesn't apply to the specific situation mentioned in the query, clearly state that.
        If you don't have enough information to answer, ask for clarification rather than making assumptions.
        """
        
        # Prepare prompt for policy extraction
        formatted_query = f"""
        Extract the relevant supplemental pay policies based on the following query:
        
        Query: {query}
        
        The policies should be extracted from these Excel files: {', '.join(excel_files)}
        
        For each relevant policy, provide:
        1. The policy name or category
        2. Who it applies to (eligibility criteria)
        3. The payment terms or rates
        4. Any conditions or special circumstances
        5. Whether it's billable to clients or absorbed internally by DXC
        
        Focus only on the policies that are directly relevant to the query.
        Format your response as a structured JSON object.
        """
        
        # Create chat history
        from semantic_kernel.contents import ChatHistory
        history = ChatHistory()
        
        # Add the messages
        history.add_system_message(system_message)
        history.add_user_message(formatted_query)
        
        try:
            # Get the chat service
            chat_service = self.kernel.get_service("azure_chat_completion")
            
            # Get execution settings
            execution_settings = chat_service.get_prompt_execution_settings_class()()
            execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
            
            # Invoke the chat completion
            result = await chat_service.get_chat_message_contents(
                chat_history=history,
                settings=execution_settings,
                kernel=self.kernel
            )
            
            # Get the content from the result
            result_content = result[0].content if result and len(result) > 0 else ""
            
            # Process and structure the response
            policies = self._process_agent_response(result_content)
            
            # Cache the extracted policies for future use
            cache_key = self._generate_cache_key(query)
            self.policy_cache[cache_key] = policies
            
            return policies
        except Exception as e:
            self.logger.error(f"Policy extraction failed: {str(e)}")
            return {"error": str(e)}
    
    def _process_agent_response(self, response: str) -> Dict[str, Any]:
        """
        Process the agent's response and structure it as policies.
        
        Args:
            response: Raw response from the agent
            
        Returns:
            Structured policies dictionary
        """
        try:
            # Check if the response is already structured
            if response.startswith("{") and response.endswith("}"):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
            
            # Simple processing for text responses
            policies = {
                "extracted_policies": [],
                "raw_response": response
            }
            
            # Split the response by numbered items or headers
            lines = response.split("\n")
            current_policy = None
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if this is a new policy section
                if line.startswith(("Policy:", "Category:", "1.", "2.", "3.")) or any(keyword in line for keyword in ["Overtime", "Standby", "Call out", "Vacation"]):
                    if current_policy:
                        policies["extracted_policies"].append(current_policy)
                    
                    current_policy = {
                        "title": line,
                        "details": []
                    }
                elif current_policy:
                    current_policy["details"].append(line)
            
            # Add the last policy if exists
            if current_policy:
                policies["extracted_policies"].append(current_policy)
            
            return policies
        except Exception as e:
            self.logger.error(f"Error processing agent response: {str(e)}")
            return {"error": str(e), "raw_response": response}
    
    def _generate_cache_key(self, query: str) -> str:
        """
        Generate a cache key for the query.
        
        Args:
            query: User query
            
        Returns:
            Cache key string
        """
        # Normalize the query to create a consistent key
        return query.lower().strip()
    
    async def validate_eligibility(self, employee_data: Dict[str, Any], policy_type: str) -> Dict[str, Any]:
        """
        Validate if an employee is eligible for a specific supplemental pay policy.
        
        Args:
            employee_data: Employee information
            policy_type: Type of policy to check (overtime, standby, callout, etc.)
            
        Returns:
            Validation results
        """
        self.logger.info(f"Validating eligibility for {policy_type}")
        
        # Get policy data
        excel_files = self.file_connector.get_excel_files()
        
        # Construct a query to extract eligibility criteria
        query = f"What are the eligibility criteria for {policy_type} payments?"
        
        # Extract policies
        policies = await self._extract_policies(excel_files, query)
        
        # Format the prompt for eligibility validation
        formatted_query = f"""
        Based on the following employee data and policy information, determine if the employee is eligible for {policy_type} payments:
        
        Employee Data:
        {json.dumps(employee_data, indent=2)}
        
        Policy Information:
        {json.dumps(policies, indent=2)}
        
        Provide a clear yes/no answer with justification based on the policy criteria.
        """
        
        # Create chat history
        from semantic_kernel.contents import ChatHistory
        history = ChatHistory()
        
        # Add system message
        system_message = "You are a policy verification assistant for DXC, specialized in determining eligibility for supplemental pay policies."
        history.add_system_message(system_message)
        history.add_user_message(formatted_query)
        
        # Get the chat service
        chat_service = self.kernel.get_service("azure_chat_completion")
        
        # Get execution settings
        execution_settings = chat_service.get_prompt_execution_settings_class()()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        # Invoke the chat completion
        result = await chat_service.get_chat_message_contents(
            chat_history=history,
            settings=execution_settings,
            kernel=self.kernel
        )
        
        # Get the content from the result
        response_content = result[0].content if result and len(result) > 0 else ""
        
        # Structure the response
        result = {
            "policy_type": policy_type,
            "eligible": "Yes" in response_content[:50],  # Simple check for affirmative response
            "justification": response_content,
            "employee_id": employee_data.get("Emp ID", "Unknown")
        }
        
        return result
    
    async def process_request(self, query: str) -> str:
        """
        Process an HR team member's request.
        
        Args:
            query: The HR team member's query
            
        Returns:
            Response with policy information
        """
        self.logger.info(f"Processing HR request: {query}")
        
        try:
            # Check if response is in cache
            cache_key = self._generate_cache_key(query)
            if cache_key in self.policy_cache:
                self.logger.info("Using cached policy data")
                policies = self.policy_cache[cache_key]
            else:
                # Get Excel files from local directory
                excel_files = self.file_connector.get_excel_files()
                if not excel_files:
                    return "Unable to retrieve policy documents from the data directory. Please check file availability and try again."
                
                # Extract policies based on the query
                policies = await self._extract_policies(excel_files, query)
            
            # Format the response using a plain chat completion
            formatted_query = f"""
            Based on the following policies, please provide a clear and concise response to my question:
            
            Question: {query}
            
            Policies: {json.dumps(policies, indent=2)}
            """
            
            # Create chat history
            from semantic_kernel.contents import ChatHistory
            history = ChatHistory()
            
            # Add system message
            system_message = "You are a policy extraction assistant for DXC, specialized in providing clear policy information."
            history.add_system_message(system_message)
            history.add_user_message(formatted_query)
            
            # Get the chat service
            chat_service = self.kernel.get_service("azure_chat_completion")
            
            # Get execution settings
            execution_settings = chat_service.get_prompt_execution_settings_class()()
            execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
            
            # Invoke the chat completion
            result = await chat_service.get_chat_message_contents(
                chat_history=history,
                settings=execution_settings,
                kernel=self.kernel
            )
            
            # Get the content from the result
            response_content = result[0].content if result and len(result) > 0 else ""
            
            # Return the response content
            return response_content
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return f"Sorry, I encountered an error while processing your request: {str(e)}"


# Example usage
if __name__ == "__main__":
    import asyncio
    import semantic_kernel as sk
    from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Initialize kernel
        kernel = sk.Kernel()
        
        # Create the chat service
        openai_service = AzureChatCompletion(
            deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            service_id="azure_chat_completion"
        )
        
        # Add the service to the kernel
        kernel.add_service(openai_service)
        
        # Example local file configuration
        config = {
            "data_dir": "data"
        }
        
        # Initialize local file connector
        file_connector = LocalFileConnector(config)
        
        # Initialize agent
        agent = PolicyExtractionAgent(kernel, file_connector)
        
        # Example query
        response = await agent.process_request("What are the standby payment policies for UK employees?")
        print(f"Response: {response}")
    
    asyncio.run(main()) 