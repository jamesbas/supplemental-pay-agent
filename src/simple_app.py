import os
import logging
from typing import Dict, Any, List, Optional

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions import KernelArguments, kernel_function
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

# Create a simple plugin for demonstration
class SimplePlugin:
    """A simple plugin for demonstration purposes."""
    
    @kernel_function(
        description="Get information about a specific employee",
        name="get_employee_info"
    )
    def get_employee_info(self, employee_id: str, arguments: KernelArguments) -> str:
        """
        Get information about a specific employee.
        
        Args:
            employee_id: The ID of the employee to retrieve information for
            arguments: Kernel arguments
            
        Returns:
            Employee information
        """
        logging.info(f"Getting information for employee: {employee_id}")
        return f"Employee {employee_id} is a Software Engineer based in London."
    
    @kernel_function(
        description="Calculate the supplemental pay for an employee",
        name="calculate_pay"
    )
    def calculate_pay(self, employee_id: str, hours: float, arguments: KernelArguments) -> str:
        """
        Calculate supplemental pay for an employee.
        
        Args:
            employee_id: The ID of the employee
            hours: Number of hours worked
            arguments: Kernel arguments
            
        Returns:
            Calculated pay information
        """
        logging.info(f"Calculating pay for employee {employee_id} with {hours} hours")
        hourly_rate = 25.00  # Example hourly rate
        total_pay = hours * hourly_rate
        return f"Employee {employee_id} earned ${total_pay:.2f} for {hours} hours of work."


async def main():
    """Main entry point for the application."""
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Load environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    if not api_key or not endpoint or not deployment_name:
        logging.error("Missing required environment variables. Please check .env file.")
        return
    
    # Initialize Semantic Kernel
    kernel = sk.Kernel()
    
    # Create the Azure Chat Completion service
    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        api_key=api_key,
        endpoint=endpoint,
        service_id="chat_completion"
    )
    
    # Add the service to the kernel
    kernel.add_service(azure_chat_completion)
    
    # Register our plugin
    kernel.add_plugin(SimplePlugin(), plugin_name="EmployeePlugin")
    
    # Basic prompt to test the connection
    from semantic_kernel.contents import ChatHistory
    
    # Create a chat history
    history = ChatHistory()
    
    # Create system and user messages
    system_message = """
    You are an assistant for DXC's Supplemental Pay system. 
    You can help with employee information and pay calculations.
    """
    
    user_query = "Calculate the pay for employee EMP12345 who worked 12.5 hours of overtime."
    
    # Add messages to the chat history
    history.add_system_message(system_message)
    history.add_user_message(user_query)
    
    # Get the chat service
    chat_service = kernel.get_service("chat_completion")
    
    # Simple invoke without all the complex templating
    logging.info("Sending request to Azure OpenAI...")
    try:
        # Get the execution settings with function calling capability
        execution_settings = chat_service.get_prompt_execution_settings_class()()
        execution_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()
        
        # Send the chat request
        result = await chat_service.get_chat_message_contents(
            chat_history=history,
            settings=execution_settings,
            kernel=kernel
        )
        
        # Extract the content from the result
        response_text = result[0].content if result and len(result) > 0 else "No response generated."
        
        # Print the response
        print(f"User: {user_query}")
        print(f"Assistant: {response_text}")
    except Exception as e:
        logging.error(f"Error calling Azure OpenAI: {str(e)}")
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 