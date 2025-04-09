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


class AnalyticsAgent:
    """
    Agent for analyzing supplemental pay data, identifying trends and outliers.
    Handles requests from payroll managers.
    """
    
    def __init__(self, kernel: sk.Kernel, excel_processor: ExcelProcessor, file_connector=None):
        """
        Initialize the Analytics Agent.
        
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
        
        self.logger.info("Analytics Agent initialized")
    
    async def analyze_pay_data(self, query: str) -> str:
        """
        Analyze supplemental pay data based on the payroll manager's query.
        
        Args:
            query: The payroll manager's query
            
        Returns:
            Analysis results
        """
        self.logger.info(f"Analyzing pay data based on query: {query}")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            payment_data = self.excel_processor.get_payment_data(file_paths)
            
            # Prepare the prompt for analysis
            formatted_query = f"""
            Based on the following payment data and query, provide a comprehensive analysis:
            
            Query: {query}
            
            Payment Data Summary: 
            {json.dumps(payment_data, indent=2)}
            
            Please provide:
            1. A comprehensive analysis of the payment data
            2. Identification of any trends, patterns, or anomalies
            3. Recommendations based on your analysis
            4. Any potential compliance or policy issues that need attention
            
            Focus on providing actionable insights that would help a payroll manager.
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            analyze_function = KernelFunction.from_prompt(
                function_name="analyze_pay_data",
                plugin_name="analytics",
                description="Analyze supplemental pay data for trends and insights",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(analyze_function)
            
            return str(result)
        except Exception as e:
            self.logger.error(f"Error analyzing pay data: {str(e)}")
            return f"Sorry, I encountered an error while analyzing the pay data: {str(e)}"
    
    async def analyze_trends(self, time_period: str) -> Dict[str, Any]:
        """
        Analyze trends in supplemental pay over a specified time period.
        
        Args:
            time_period: Time period for trend analysis (e.g., "last_3_months", "year_to_date")
            
        Returns:
            Dictionary containing trend analysis results
        """
        self.logger.info(f"Analyzing trends for time period: {time_period}")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            hours_data = self.excel_processor.get_hours_data(file_paths)
            
            # Prepare the prompt for trend analysis
            formatted_query = f"""
            Analyze trends in supplemental pay for the time period: {time_period}
            
            Use the data from three Excel files:
            1. Employee data file: Contains employee ID, name, payment terms, and hourly rate
            2. Payment terms file: Contains the payment terms definitions for overtime, standby, and callout
            3. Hours data file: Contains supplemental pay hours claimed by employees from Sep 2024 to Feb 2025
            
            Employee data summary:
            {employee_data.to_string() if not employee_data.empty else "No employee data available"}
            
            Payment terms summary:
            {payment_terms.to_string() if not payment_terms.empty else "No payment terms data available"}
            
            Hours data summary:
            {hours_data.to_string() if not hours_data.empty else "No hours data available"}
            
            Please provide the analysis in a structured JSON format including:
            1. "time_period": The analyzed time period
            2. "overall_trend": Summary of the main trend direction
            3. "trend_by_category": Trends broken down by supplemental pay categories
            4. "trend_by_payment_terms": Trends broken down by different payment terms
            5. "month_over_month_change": Percentage changes between months
            6. "insights": Key insights derived from the trend analysis
            7. "recommendations": Actionable recommendations based on trends
            
            Format your entire response as valid JSON.
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            trend_function = KernelFunction.from_prompt(
                function_name="analyze_trends",
                plugin_name="analytics",
                description="Analyze trends in supplemental pay over time",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(trend_function)
            
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
                        "time_period": time_period,
                        "raw_response": response_content
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    "time_period": time_period,
                    "raw_response": response_content
                }
        except Exception as e:
            self.logger.error(f"Error analyzing trends: {str(e)}")
            return {
                "time_period": time_period,
                "error": str(e)
            }
    
    async def find_outliers(self, threshold: float = 1.5) -> Dict[str, Any]:
        """
        Find outliers in supplemental pay data.
        
        Args:
            threshold: IQR multiplier for outlier detection
            
        Returns:
            Dictionary containing outlier analysis results
        """
        self.logger.info(f"Finding outliers with threshold: {threshold}")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            hours_data = self.excel_processor.get_hours_data(file_paths)
            
            # Prepare the prompt for outlier detection
            formatted_query = f"""
            Find outliers in supplemental pay data using an IQR threshold of {threshold}.
            
            Use the data from three Excel files:
            1. Employee data file: Contains employee ID, name, payment terms, and hourly rate
            2. Payment terms file: Contains the payment terms definitions for overtime, standby, and callout
            3. Hours data file: Contains supplemental pay hours claimed by employees from Sep 2024 to Feb 2025
            
            Employee data summary:
            {employee_data.to_string() if not employee_data.empty else "No employee data available"}
            
            Payment terms summary:
            {payment_terms.to_string() if not payment_terms.empty else "No payment terms data available"}
            
            Hours data summary:
            {hours_data.to_string() if not hours_data.empty else "No hours data available"}
            
            For outlier detection:
            1. Use the Interquartile Range (IQR) method with a threshold of {threshold}
            2. Identify outliers in hours claimed for each supplemental pay category
            3. Identify outliers in amounts paid compared to policy standards
            4. Flag any suspicious patterns that might indicate errors or policy violations
            
            Please provide the analysis in a structured JSON format including:
            1. "outliers_by_employee": List of employees with outlier values
            2. "outliers_by_category": Outliers broken down by supplemental pay categories
            3. "outliers_by_month": Outliers broken down by month
            4. "potential_issues": Description of potential issues or policy violations
            5. "recommendations": Suggested actions for addressing the outliers
            
            Format your entire response as valid JSON.
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            outlier_function = KernelFunction.from_prompt(
                function_name="find_outliers",
                plugin_name="analytics",
                description="Find outliers in supplemental pay data",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(outlier_function)
            
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
                        "threshold": threshold,
                        "raw_response": response_content
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    "threshold": threshold,
                    "raw_response": response_content
                }
        except Exception as e:
            self.logger.error(f"Error finding outliers: {str(e)}")
            return {
                "threshold": threshold,
                "error": str(e)
            }
    
    async def analyze_billable_vs_internal(self) -> Dict[str, Any]:
        """
        Analyze which supplemental pay is billable to clients versus absorbed internally.
        
        Returns:
            Dictionary containing billability analysis results
        """
        self.logger.info("Analyzing billable vs. internal supplemental pay")
        
        try:
            # Get necessary data
            if self.file_connector:
                file_paths = self.file_connector.get_excel_files()
            else:
                file_paths = []  # This would normally come from SharePoint
            
            employee_data = self.excel_processor.get_employee_data(file_paths)
            payment_terms = self.excel_processor.get_payment_terms_data(file_paths)
            hours_data = self.excel_processor.get_hours_data(file_paths)
            
            # Prepare the prompt for billability analysis
            formatted_query = """
            Analyze which supplemental pay is billable to clients versus absorbed internally by DXC.
            
            Use the data from three Excel files:
            1. Employee data file: Contains employee ID, name, payment terms, and hourly rate
            2. Payment terms file: Contains the payment terms definitions for overtime, standby, and callout
            3. Hours data file: Contains supplemental pay hours claimed by employees from Sep 2024 to Feb 2025
            
            For this analysis:
            1. Determine which payment terms or categories are billable to clients
            2. Calculate the total amount of supplemental pay that is billable vs. internal
            3. Break down the analysis by months and categories
            4. Identify opportunities to increase billable supplemental pay
            5. Analyze any patterns in internal absorption that could be optimized
            
            Please provide the analysis in a structured JSON format including:
            1. "billable_total": Total billable supplemental pay amount
            2. "internal_total": Total internally absorbed supplemental pay amount
            3. "billable_percentage": Percentage of total that is billable
            4. "breakdown_by_category": Billable vs. internal breakdown by pay category
            5. "breakdown_by_month": Billable vs. internal breakdown by month
            6. "optimization_opportunities": Opportunities to increase billable percentage
            7. "recommendations": Strategic recommendations for optimizing cost allocation
            
            Format your entire response as valid JSON.
            """
            
            # Create a function from the prompt using the new API
            from semantic_kernel.functions import KernelFunction
            billable_function = KernelFunction.from_prompt(
                function_name="analyze_billable_vs_internal",
                plugin_name="analytics",
                description="Analyze billable vs internal supplemental pay",
                prompt=formatted_query
            )
            
            # Invoke the function with the kernel
            result = await self.kernel.invoke(billable_function)
            
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
                        "raw_response": response_content
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw response
                return {
                    "raw_response": response_content
                }
        except Exception as e:
            self.logger.error(f"Error analyzing billable vs. internal pay: {str(e)}")
            return {
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
        agent = AnalyticsAgent(kernel, excel_processor)
        
        # Example analysis
        response = await agent.analyze_pay_data("Identify trends and outliers in overtime payments for the last three months")
        print(f"Response: {response}")
    
    asyncio.run(main()) 