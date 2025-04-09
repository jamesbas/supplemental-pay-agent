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

from src.data_access.excel_processor import ExcelProcessor


class PayCalculationAgent:
    """
    Agent for calculating supplemental pay and providing recommendations.
    Handles requests from people managers.
    """
    
    def __init__(self, kernel: sk.Kernel, excel_processor: ExcelProcessor, file_connector=None):
        """
        Initialize the Pay Calculation Agent.
        
        Args:
            kernel: Initialized Semantic Kernel instance
            excel_processor: Excel processor for data access
            file_connector: File connector for accessing Excel files
        """
        self.logger = logging.getLogger(__name__)
        self.kernel = kernel
        self.excel_processor = excel_processor
        self.file_connector = file_connector
        
        # Set up extension data for Azure
        self.extension_data = {
            "api_type": "azure"
        }
        
        self.logger.info("Pay Calculation Agent initialized")
    
    async def analyze_employee(self, employee_id: str, query: str) -> str:
        """
        Analyze supplemental pay for a specific employee.
        
        Args:
            employee_id: ID of the employee to analyze
            query: The manager's query about the employee
            
        Returns:
            Analysis and recommendations for the employee
        """
        self.logger.info(f"Analyzing employee {employee_id} based on query: {query}")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            hours_data = self.excel_processor.get_hours_data(file_paths)
            
            # Prepare data for analysis
            dataframes = {
                "employee_data": employee_data,
                "payment_terms": payment_terms,
                "hours_data": hours_data
            }
            
            # Analyze the employee data
            employee_analysis = self.excel_processor.analyze_employee(employee_id, dataframes)
            
            # Prepare the prompt for analysis
            formatted_query = f"""
            Based on the following employee data and query, calculate the appropriate supplemental pay and provide a recommendation:
            
            Query: {query}
            
            Employee Analysis: 
            {json.dumps(employee_analysis, indent=2)}
            
            Please provide:
            1. The calculated supplemental pay amount
            2. Explanation of how the calculation was performed
            3. A clear recommendation for approval or further review
            4. Any relevant policy information that supports your recommendation
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            analyze_function = KernelFunction.from_prompt(
                function_name="analyze_employee",
                plugin_name="pay_calculation",
                description="Analyze employee data and calculate supplemental pay",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(analyze_function)
            
            return str(result)
        except Exception as e:
            self.logger.error(f"Error analyzing employee: {str(e)}")
            return f"Sorry, I encountered an error while analyzing employee {employee_id}: {str(e)}"
    
    async def analyze_team(self, query: str) -> str:
        """
        Analyze supplemental pay for the entire team.
        
        Args:
            query: The manager's query about the team
            
        Returns:
            Analysis and recommendations for the team
        """
        self.logger.info(f"Analyzing team based on query: {query}")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            hours_data = self.excel_processor.get_hours_data(file_paths)
            
            # Prepare data for analysis
            dataframes = {
                "employee_data": employee_data,
                "payment_terms": payment_terms,
                "hours_data": hours_data
            }
            
            # Analyze the team data
            team_analysis = self.excel_processor.analyze_team_data(dataframes)
            
            # Prepare the prompt for team analysis
            formatted_query = f"""
            Based on the following team data and query, provide a team-wide analysis of supplemental pay:
            
            Query: {query}
            
            Team Analysis: 
            {json.dumps(team_analysis, indent=2)}
            
            Please provide:
            1. Overall team supplemental pay trends
            2. Identification of any outliers or unusual patterns
            3. Recommendations for optimizing supplemental pay across the team
            4. Breakdown by payment terms categories
            5. Analysis of which supplemental pay is billable to clients vs. absorbed internally
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            team_function = KernelFunction.from_prompt(
                function_name="analyze_team",
                plugin_name="pay_calculation",
                description="Analyze team-wide supplemental pay data",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(team_function)
            
            return str(result)
        except Exception as e:
            self.logger.error(f"Error analyzing team: {str(e)}")
            return f"Sorry, I encountered an error while analyzing team data: {str(e)}"
    
    async def calculate_pay(self, employee_id: str, hours: float, pay_type: str) -> Dict[str, Any]:
        """
        Calculate specific supplemental pay for an employee.
        
        Args:
            employee_id: ID of the employee
            hours: Number of hours worked
            pay_type: Type of supplemental pay (overtime, standby, callout)
            
        Returns:
            Calculation results
        """
        self.logger.info(f"Calculating {pay_type} pay for employee {employee_id} with {hours} hours")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            
            # Prepare data for analysis
            dataframes = {
                "employee_data": employee_data,
                "payment_terms": payment_terms
            }
            
            # Analyze the employee data
            employee_analysis = self.excel_processor.analyze_employee(employee_id, dataframes)
            
            # Prepare the prompt for calculation
            formatted_query = f"""
            Calculate the appropriate {pay_type} pay for employee {employee_id} with {hours} hours worked.
            
            Employee Analysis: 
            {json.dumps(employee_analysis, indent=2)}
            
            Please provide the calculation in a structured JSON format including:
            1. "employee_id": The employee ID
            2. "pay_type": The type of supplemental pay
            3. "hours": The hours submitted
            4. "hourly_rate": The employee's hourly rate
            5. "payment_terms": The employee's payment terms
            6. "calculation": Step-by-step calculation
            7. "amount": The final amount to be paid
            8. "billable": Whether this amount is billable to clients (true/false)
            9. "recommendation": Approval recommendation
            
            Format your entire response as valid JSON.
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            calculate_function = KernelFunction.from_prompt(
                function_name="calculate_pay",
                plugin_name="pay_calculation",
                description="Calculate supplemental pay for an employee",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(calculate_function)
            
            response_content = str(result)
            
            # Try to parse JSON from response
            try:
                # Look for JSON in the response
                start_idx = response_content.find('{')
                end_idx = response_content.rfind('}')
                
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_content[start_idx:end_idx+1]
                    result = json.loads(json_str)
                    return result
                else:
                    # If no JSON found, return formatted result
                    return {
                        "employee_id": employee_id,
                        "pay_type": pay_type,
                        "hours": hours,
                        "raw_response": response_content
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    "employee_id": employee_id,
                    "pay_type": pay_type,
                    "hours": hours,
                    "raw_response": response_content
                }
        except Exception as e:
            self.logger.error(f"Error calculating pay: {str(e)}")
            return {
                "employee_id": employee_id,
                "pay_type": pay_type,
                "hours": hours,
                "error": str(e)
            }


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
        
        # Initialize Excel processor
        excel_processor = ExcelProcessor()
        
        # Initialize agent
        agent = PayCalculationAgent(kernel, excel_processor)
        
        # Example analysis
        response = await agent.analyze_employee("EMP12345", "Calculate overtime pay for last week")
        print(f"Response: {response}")
    
    asyncio.run(main()) 