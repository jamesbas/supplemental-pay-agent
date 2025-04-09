"""
Tool executor for Azure AI Agents in the DXC Supplemental Pay system.
This module handles the execution of tools requested by the Azure AI Agents.
"""

import os
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
import json
import asyncio

# Custom replacement classes since azure.ai.agents module is not available
class ToolParameters(dict):
    """Simplified wrapper for tool parameters"""
    pass

class ToolResponseFormat:
    """Tool response format constants"""
    JSON = "json"
    TEXT = "text"

class AgentRequest:
    """Simplified agent request class"""
    def __init__(self, tool_name: str, tool_parameters: Dict[str, Any]):
        self.tool_name = tool_name
        self.tool_parameters = ToolParameters(tool_parameters)

class ToolCallResponse:
    """Simplified tool call response"""
    def __init__(self, content: Any, format: str = ToolResponseFormat.JSON):
        self.content = content
        self.format = format

class AgentHandler:
    """Base class for agent handlers"""
    async def handle_tool_call(self, request: AgentRequest) -> ToolCallResponse:
        """Handle a tool call from an agent"""
        raise NotImplementedError("Subclasses must implement handle_tool_call")

# Import existing agent implementations
from src.agents.policy_extraction_agent import PolicyExtractionAgent
from src.agents.pay_calculation_agent import PayCalculationAgent
from src.agents.analytics_agent import AnalyticsAgent

# Import data access components
from src.data_access.local_file_connector import LocalFileConnector
from src.data_access.excel_processor import ExcelProcessor

class AgentToolExecutor(AgentHandler):
    """
    Handles tool execution for Azure AI Agents in the DXC Supplemental Pay system.
    Bridges between Azure AI Agent Service and the existing implementation.
    """
    
    def __init__(self, policy_agent: PolicyExtractionAgent, calculation_agent: PayCalculationAgent, 
                 analytics_agent: AnalyticsAgent):
        """
        Initialize the tool executor with the existing agent implementations.
        
        Args:
            policy_agent: PolicyExtractionAgent instance
            calculation_agent: PayCalculationAgent instance
            analytics_agent: AnalyticsAgent instance
        """
        self.logger = logging.getLogger(__name__)
        self.policy_agent = policy_agent
        self.calculation_agent = calculation_agent
        self.analytics_agent = analytics_agent
        
        # Tool mapping - maps tool names to handler functions
        self.tool_handlers = {
            # Policy extraction agent tools
            "extract_policy": self._handle_extract_policy,
            "validate_eligibility": self._handle_validate_eligibility,
            
            # Pay calculation agent tools
            "analyze_employee": self._handle_analyze_employee,
            "analyze_team": self._handle_analyze_team,
            "calculate_pay": self._handle_calculate_pay,
            
            # Analytics agent tools
            "analyze_pay_data": self._handle_analyze_pay_data,
            "analyze_trends": self._handle_analyze_trends,
            "find_outliers": self._handle_find_outliers,
            "analyze_billable_vs_internal": self._handle_analyze_billable_vs_internal
        }
        
        self.logger.info("Agent Tool Executor initialized")
    
    async def handle_tool_call(self, tool_call: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Handle a tool call from an Azure AI Agent Service.
        
        Args:
            tool_call: Tool call dictionary from Azure AI Agent Service containing:
                - id: The tool call ID
                - type: The type of the tool call (e.g., "function")
                - function: Function details containing name and arguments
            
        Returns:
            Tool call response compatible with Azure AI Agent Service
        """
        try:
            # Log the received tool call
            self.logger.info(f"Received tool call: {tool_call}")
            
            # Extract function details
            function_details = tool_call.get("function", {})
            
            # Extract function name and arguments
            tool_name = function_details.get("name", "")
            arguments_str = function_details.get("arguments", "{}")
            
            # Parse arguments (JSON string) into dictionary
            try:
                tool_parameters = json.loads(arguments_str) if arguments_str else {}
            except json.JSONDecodeError:
                self.logger.error(f"Invalid JSON in arguments: {arguments_str}")
                tool_parameters = {}
            
            # Create an agent request object for backward compatibility
            request = AgentRequest(tool_name=tool_name, tool_parameters=tool_parameters)
            
            # Check if we have a handler for this tool
            if tool_name not in self.tool_handlers:
                error_message = f"Unsupported tool: {tool_name}"
                self.logger.error(error_message)
                return {
                    "tool_call_id": tool_call.get("id", ""),
                    "output": json.dumps({"error": error_message})
                }
            
            # Execute the tool handler
            handler = self.tool_handlers[tool_name]
            result = await handler(tool_parameters)
            
            # Convert result to JSON-compatible format if it's not already
            if isinstance(result, (dict, list)):
                response_content = result
            else:
                response_content = {"result": str(result)}
                
            # Format the response for Azure AI Agent Service
            return {
                "tool_call_id": tool_call.get("id", ""),
                "output": json.dumps(response_content)
            }
            
        except Exception as e:
            error_message = f"Error handling tool call: {str(e)}"
            self.logger.error(error_message)
            return {
                "tool_call_id": tool_call.get("id", ""),
                "output": json.dumps({"error": error_message})
            }
    
    # For backward compatibility, keep the original method
    async def handle_tool_call_legacy(self, request: AgentRequest) -> ToolCallResponse:
        """
        Handle a tool call from an Azure AI Agent (legacy method).
        
        Args:
            request: The agent request containing tool call details
            
        Returns:
            Tool call response
        """
        tool_name = request.tool_name
        tool_parameters = request.tool_parameters
        
        self.logger.info(f"Handling tool call: {tool_name} with parameters: {tool_parameters}")
        
        # Check if we have a handler for this tool
        if tool_name not in self.tool_handlers:
            error_message = f"Unsupported tool: {tool_name}"
            self.logger.error(error_message)
            return ToolCallResponse(content={"error": error_message}, format=ToolResponseFormat.JSON)
        
        try:
            # Execute the tool handler
            handler = self.tool_handlers[tool_name]
            result = await handler(tool_parameters)
            
            # Convert result to JSON-compatible format if it's not already
            if isinstance(result, (dict, list)):
                response_content = result
            else:
                response_content = {"result": str(result)}
                
            return ToolCallResponse(content=response_content, format=ToolResponseFormat.JSON)
        
        except Exception as e:
            error_message = f"Error executing tool {tool_name}: {str(e)}"
            self.logger.error(error_message)
            return ToolCallResponse(content={"error": error_message}, format=ToolResponseFormat.JSON)
    
    # Policy Extraction Agent tool handlers
    
    async def _handle_extract_policy(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle extract_policy tool call"""
        policy_type = parameters.get("policy_type")
        arguments = parameters.get("arguments", {})
        
        # Get Excel files from arguments or use file connector
        excel_files = arguments.get("files", [])
        if not excel_files and hasattr(self.policy_agent, "file_connector"):
            excel_files = self.policy_agent.file_connector.get_excel_files()
        
        # Extract policies
        query = f"Extract {policy_type} policy for {arguments.get('region', 'all regions')}"
        policies = await self.policy_agent._extract_policies(excel_files, query)
        return policies
    
    async def _handle_validate_eligibility(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle validate_eligibility tool call"""
        employee_id = parameters.get("employee_id")
        policy_type = parameters.get("policy_type")
        
        # Mock employee data for validation
        employee_data = {"employee_id": employee_id}
        
        # Validate eligibility
        result = await self.policy_agent.validate_eligibility(employee_data, policy_type)
        return result
    
    # Pay Calculation Agent tool handlers
    
    async def _handle_analyze_employee(self, parameters: ToolParameters) -> str:
        """Handle analyze_employee tool call"""
        employee_id = parameters.get("employee_id")
        query = parameters.get("query")
        
        # Analyze employee
        result = await self.calculation_agent.analyze_employee(employee_id, query)
        return result
    
    async def _handle_analyze_team(self, parameters: ToolParameters) -> str:
        """Handle analyze_team tool call"""
        query = parameters.get("query")
        
        # Analyze team
        result = await self.calculation_agent.analyze_team(query)
        return result
    
    async def _handle_calculate_pay(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle calculate_pay tool call"""
        employee_id = parameters.get("employee_id")
        hours = parameters.get("hours")
        pay_type = parameters.get("pay_type")
        
        # Calculate pay
        result = await self.calculation_agent.calculate_pay(employee_id, hours, pay_type)
        return result
    
    # Analytics Agent tool handlers
    
    async def _handle_analyze_pay_data(self, parameters: ToolParameters) -> str:
        """Handle analyze_pay_data tool call"""
        query = parameters.get("query")
        
        # Analyze pay data
        result = await self.analytics_agent.analyze_pay_data(query)
        return result
    
    async def _handle_analyze_trends(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle analyze_trends tool call"""
        time_period = parameters.get("time_period")
        
        # Analyze trends
        result = await self.analytics_agent.analyze_trends(time_period)
        return result
    
    async def _handle_find_outliers(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle find_outliers tool call"""
        threshold = parameters.get("threshold", 1.5)
        
        # Find outliers
        result = await self.analytics_agent.find_outliers(threshold)
        return result
    
    async def _handle_analyze_billable_vs_internal(self, parameters: ToolParameters) -> Dict[str, Any]:
        """Handle analyze_billable_vs_internal tool call"""
        # Analyze billable vs internal
        result = await self.analytics_agent.analyze_billable_vs_internal()
        return result 