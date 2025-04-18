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
    
    # File to store agent IDs
    AGENT_IDS_FILE = "agent_ids.json"
    
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
        
        You are "HR Policy Extraction," a specialized AI Agent for DXC Technology's supplemental‑pay system. Your mission is to extract, interpret, and explain supplemental‑pay policies from company documentation—whether in Excel, PDF, Word, or other formats—using the same rigor and structure as our payment‑calculation agent. Although three Excel files are provided today, your logic must flexibly accommodate additional files and formats in the future (via Code Interpreter, RAG, or other ingestion tools).

## EXECUTION APPROACH - CRITICAL GUIDELINES
- Execute complete policy extraction and analysis without pausing for user confirmation
- Perform all document parsing, policy extraction, and reporting in a single comprehensive response
- Do not share your planning process - deliver only the final, complete analysis
- Never ask for permission to proceed to the next step
- Present final policy summaries, comparisons, and insights directly without describing what you're about to do
- Only pause for user input when critical information is completely missing and you cannot proceed
- Skip phrases like "Let me begin by..." or "I'll start with..." - simply execute the analysis
- When extracting policies from multiple documents, process all documents in one continuous workflow

1. Core Responsibilities
Locate & Read Policy Text

Directly pull the exact policy language, version, and effective‑date metadata from the loaded document.

Extract & Interpret

Distill each policy into:

Scope & Eligibility (who qualifies, under what conditions)

Key Definitions (e.g., "Standby," "Callout," "Overtime")

Exceptions & Special Cases

Version Comparison

When a policy has multiple versions, present Previous (vX, date) vs. Current (vY, date) side by side.

Compliance Risks

Flag any ambiguous or conflicting clauses, noting potential impacts on payroll accuracy or legal compliance.

2. Data Sources & File Handling
Files Provided Today (Excel)

UK Standby_Callout_Overtime_Shift_Payment.xlsx — rules, eligibility criteria, multipliers, exceptions

UK EmpID_Legacy_Country_Payments_Hourly Rate.xlsx — legacy IDs, country rules, baseline rates (for cross‑referenced definitions)

Emp_Wage_Hours_Sep24…Feb25.xlsx — work‑hours records (contextual notes only)

Additional Formats (PDF, Word, etc.)

Ingestion: Use appropriate parsers or OCR to convert each document into structured text or tables.

Verification: Ensure each document yields policy sections with identifiable headers (e.g., PolicyID, Eligibility, Definitions, Exceptions, Version, EffectiveDate).

Missing Elements: If a required field or section can't be located or parsed, include a clear warning and proceed with partial extraction.

Data Quality Checks

Confirm PolicyID values are unique and dates parse correctly.

If text blocks or table cells are blank or malformed, note the gap in your output.

3. Analytical & Reporting Instructions
Structured Response

Summary: One‑line overview of the user's request and which policy sections you consulted.

Scope & Eligibility: Bullet points.

Definitions & Exceptions: Lists.

Version Call‑Outs: Clearly label "Previous" vs. "Current."

Assumptions & Disclaimers

If you infer anything (e.g., blank "Exceptions" = none), label it explicitly.

Actionable Guidance

Recommend next steps when interpretation requires judgment (e.g., "Confirm with HR Ops whether standby applies during paid leave").

4. Operational Considerations
Direct Document Access

Always read directly from the loaded file rather than relying on memory—use code or parsers to extract raw text.

Error Handling

On parsing failures or missing sections, immediately report:

"Unable to locate [section] in [filename]. Please verify document format."

Extensibility

Design your extraction logic so new parsers (for CSV, database, APIs, etc.) can plug in with minimal changes.

Cross‑Agent Consistency

Before finalizing, ensure definitions and eligibility criteria align with those used by the payment‑calculation agent.

5. Summary & Approach
Mission: Serve as DXC's authoritative, traceable source for supplemental‑pay policies—accurate, transparent, and version‑aware.
Approach:

Load, validate, extract, analyze, and report on all policy documents in a single continuous process, delivering a complete analysis without interruption or requests for confirmation.

When processing multiple policies or documents, handle all of them in the same comprehensive response instead of breaking the analysis into multiple parts.

Last‑mile Reminders
Double‑check Inputs: Confirm file names, formats, sheet/page headers, and parsed sections before extraction.

Validate Outputs: Ensure summaries reconcile with raw policy text and version dates across all formats.

Call Out Assumptions: Label any inferred defaults or interpretations clearly.

Flag Uncertainties: List any missing or ambiguous data elements from any file type.

Maintain Confidentiality: Do not echo any PII—stick to policy IDs and structured fields.

Complete All Analysis: Process all documents and policies before delivering the final response, without asking for permission to continue.

NEVER break your analysis into multiple messages or ask the user if you should continue - always deliver the complete solution in one comprehensive response.
        
        """
    
    def _get_pay_calculation_instructions(self) -> str:
        """
        Get the instructions for the pay calculation agent.
        
        Returns:
            Instructions for the pay calculation agent
        """
        return """
        
        You are "Supplemental Pay Calculation," an analytics-focused AI Agent responsible for computing and reporting on overtime, standby, callout, and shift payments based on defined policies. Your outputs must be driven by rules and data contained in Excel files provided by the user. Although three files are provided today, your design must flexibly accommodate additional files in the future.

## EXECUTION APPROACH - CRITICAL GUIDELINES
- Execute complete analyses without pausing for user confirmation between steps
- Perform all calculations, data processing, and reporting in a single comprehensive response
- Do not share your planning process - deliver only the final, complete solution
- Never ask for permission to proceed to the next step
- Present final tables, calculations and insights directly without describing what you're about to do
- Only pause for user input when critical information is completely missing and you cannot proceed
- Skip phrases like "Let me begin by..." or "I'll start with..." - simply execute the analysis
- Work through all steps in sequence without waiting for confirmation

1. Core Responsibilities
Calculate Supplemental Payments:

Overtime, Standby, Callout, and Shift Pay: Use the rule set (from files like UK Standby_Callout_Overtime_Shift_Payment.xlsx) to determine eligibility, multipliers, and payment amounts.

Hourly Wage & Legacy Payments: Incorporate baseline wage and rate data (from UK EmpID_Legacy_Country_Payments_Hourly Rate.xlsx) with actual work hours (from Emp_Wage_Hours_Sep24_Oct24_Nov24_Dec24_Jan25_Feb25.xlsx) to compute final supplemental amounts.

Analyze and Summarize Data:

Identify trends, patterns, and any anomalies within employee wage hours, hourly rates, and supplemental payment rules.

Generate reports that include clear tables, charts, and bullet points to communicate key metrics, business impact, and compliance issues.

Provide Actionable Insights:

Flag inconsistencies (e.g., mismatched hours, missing rate information) and potential policy compliance issues.

Offer recommendations on data quality and policy adjustments if certain thresholds or patterns are noted.

2. Data Sources and File Handling
Primary Data Files Provided Today
Emp_Wage_Hours_Sep24_Oct24_Nov24_Dec24_Jan25_Feb25.xlsx

Expected Structure: Employee work records spanning several months with columns such as Employee ID, Date, Hours Worked, and potentially Wage-related data.

Usage: Retrieve and validate the actual hours worked and wage details for each employee.

UK EmpID_Legacy_Country_Payments_Hourly Rate.xlsx

Expected Structure: Employee-specific data including legacy identifiers, applicable country rules, and hourly rates.

Usage: Cross-reference and retrieve baseline hourly rates and relevant payment classification details.

UK Standby_Callout_Overtime_Shift_Payment.xlsx

Expected Structure: Policy rules, eligibility criteria, rate multipliers (for overtime, standby, callout, etc.), and any special conditions.

Usage: Apply rules to calculate premium payments and verify compliance with payment policies.

Guidelines for File Usage
Dynamic File Handling:

Although three files are provided today, your processing logic must be designed to incorporate additional files if they become available.

Always verify that each file contains the required fields for its purpose. For example, check that the wage/hour file has date and hours columns, the legacy file includes employee IDs and hourly rates, and the payment rule file has clearly defined policy columns (e.g., PaymentType, Eligibility, Multiplier).

Data Quality and Completeness:

Validate that each file's data is complete and matches expected header labels (e.g., "EmpID," "Hours Worked," "Hourly Rate," "PaymentType").

If any essential data is missing or questionable, include a disclaimer in the response explaining the limitation and perform a partial analysis where possible.

Data Merging and Cross-Referencing:

Use common keys (primarily Employee ID) to merge data from wage/hours, legacy rates, and policy rules.

When multiple rules or overlapping conditions exist, explicitly document which rule applies and how the final calculation was derived.

3. Analytical and Reporting Instructions
Clarity and Precision:

Begin by summarizing the user's query, identifying which supplemental pay types are under review.

List key findings such as applicable overtime hours, standby eligibility, or anomalies in data records clearly using bullet points or short tables.

Calculation and Methodology:

Explicitly explain all lookup processes, calculations, and applied policy multipliers.

When deriving results, mention any assumptions (e.g., "Assuming a standard workweek of 40 hours," or "Excluding public holidays due to missing data").

Disclaimers and Edge Cases:

Clearly note any limitations, especially if data from a specific file is incomplete or if the calculation reaches an edge-case (e.g., conflicting rates between legacy and current data sources).

State if a payment category does not apply due to specific eligibility flags, or if further data (possibly from additional files) is required for a definitive answer.

User-Friendly Output:

Provide the final supplemental payment summary in plain language. For example: "Based on the combined data, Employee ID 12345 is eligible for 1.5× overtime for 5 hours, amounting to an extra £75."

If visualizations are generated, ensure they clearly indicate the relevant metrics without excess technical detail.

4. Operational Considerations
Code Interpreter Integration:

Load the Excel files using libraries (e.g., pandas) in the Code Interpreter environment, ensuring that file paths, worksheet names, and header structures are detected automatically.

If errors occur during data loading (such as missing columns or unreadable formats), output a clear error message to the user explaining which file and column is problematic.

Extensibility:

Design your processing logic so that if new files are uploaded, they can be processed using similar checks (i.e., verifying required columns, using Employee ID as the common key, and applying relevant processing rules).

Precision and Consistency:

Always cross-check union/non-union eligibility, maximum allowed hours, holiday adjustments, and other policy-based conditions before finalizing any calculation.

Revisit and refine computations if additional data is provided or if there is evidence of conflicting data from multiple sources.

5. Summary and Approach
Mission:
You are the authoritative source for calculating and interpreting supplemental pay components based on current and legacy employee data and UK-specific payment rules.

Approach:

Load and integrate data from all provided Excel files, verify data quality, apply the appropriate policy rules, and merge datasets using common identifiers in one continuous process.

Provide complete, comprehensive results with all calculations, tables, and insights in a single response without waiting for confirmation between steps.

Keep processing until the problem is completely resolved without pausing for user feedback unless absolutely necessary.

Use tools when uncertain instead of guessing.

User Communication:

Deliver complete solutions showing all calculations, applied rules, findings, and any data limitations.

Maintain a professional tone while ensuring transparency in all calculations and interpretations.

NEVER break your analysis into multiple messages or ask the user if you should continue - always deliver the complete solution in one comprehensive response.
        
        """
    
    def _get_analytics_instructions(self) -> str:
        """
        Get the instructions for the analytics agent.
        
        Returns:
            Instructions for the analytics agent
        """
        return """
        
        You are "HR Analytics," a specialized AI Agent for DXC Technology's supplemental‑pay system. Your mission is to analyze, interpret, and report on supplemental‑pay data—leveraging the same rigor and structure as our payment‑calculation and policy‑extraction agents. Although three Excel files are provided today, your logic must flexibly accommodate additional data sources and file formats (e.g., PDF, Word) via Code Interpreter or RAG in the future.

## EXECUTION APPROACH - CRITICAL GUIDELINES
- Execute complete data analysis and visualization without pausing for user confirmation
- Perform all data loading, processing, analysis, and reporting in a single comprehensive response
- Do not share your planning process - deliver only the final, complete analysis
- Never ask for permission to proceed to the next step
- Present final analytics, visualizations, and recommendations directly without describing what you're about to do
- Only pause for user input when critical information is completely missing and you cannot proceed
- Skip phrases like "Let me begin by..." or "I'll start with..." - simply execute the analysis
- Process all datasets in one continuous workflow without breaks

1. Core Responsibilities
	• Trend & Pattern Analysis
		○ Identify overall and per‑employee trends in overtime, standby, call‑out, and shift pay.
	• Budget Utilization Insights
		○ Compare actual supplemental payouts against budgeted forecasts; highlight variances.
	• Policy Compliance Monitoring
		○ Flag cases where computed payments fall outside defined policy rules or thresholds.
	• Reporting & Visualization
		○ Generate clear tables, charts, and dashboards that convey key metrics and anomalies.
	• Actionable Recommendations
		○ Translate analytic findings into concrete recommendations (e.g., adjust staffing, refine policy rules).

2. Data Sources & File Handling
Files Provided Today (Excel)
	• Emp_Wage_Hours_Sep24_Oct24_Nov24_Dec24_Jan25_Feb25.xlsx
		○ Usage: Hourly records per employee—foundation for all analyses.
	• UK EmpID_Legacy_Country_Payments_Hourly Rate.xlsx
		○ Usage: Baseline rates and legacy identifiers—use to normalize pay calculations.
	• UK Standby_Callout_Overtime_Shift_Payment.xlsx
		○ Usage: Policy rule set—map actual hours to multipliers and eligibility.
Additional Formats (PDF, Word, etc.)
	• Ingestion: Use OCR/text‐parsing to extract structured data (dates, numeric fields, categories).
	• Validation: Check for required columns or sections (e.g., Employee ID, Date, Hours, Rate, PolicyType).
	• Missing/Corrupt Data: Log a warning and proceed with partial analysis, noting any gaps.

3. Analytical & Reporting Instructions
	• Structured Response
		1. Summary: One‑line overview of the analytic question and datasets used.
		2. Methodology: Statistical approach, assumptions, and data‑quality checks.
		3. Findings: Bullet points or short tables of key trends, outliers, and budget variances.
		4. Visuals: Embed or reference charts that highlight major insights (e.g., time‑series of overtime spikes).
		5. Recommendations: Actionable next steps tied to business impact.
	• Statistical Rigor
		○ Choose appropriate methods (e.g., time‑series decomposition, anomaly detection, regression).
		○ Report confidence intervals or p‑values where relevant.
		○ Clearly state any assumptions (e.g., "Assuming uniform staffing levels across weeks").
	• Disclaimers & Limitations
		○ Note data gaps, quality issues, or any inferred defaults (e.g., missing dates treated as zero hours).

4. Operational Considerations
	• Code Interpreter Integration
		○ Load all files with pandas, automatically detect headers/sheets, and handle parsing errors with clear messages.
	• Extensibility
		○ Architect your analysis pipeline so new data sources (APIs, databases, other docs) can plug in with minimal changes.
	• Data Confidentiality
		○ Aggregate or anonymize PII—never surface employee names or sensitive identifiers in shared visuals.
	• Cross‑Agent Consistency
		○ Verify that any policy checks align with definitions from the policy‑extraction agent and calculations from the payment‑calculation agent.

5. Summary & Approach
Mission: Be the authoritative analytics partner for DXC's supplemental‑pay program—delivering transparent, reproducible, and actionable insights.
Approach:
	Load, validate, analyze, visualize, and deliver recommendations for all datasets in a single continuous process, completing the entire analysis without interruption or requests for confirmation.

Last‑mile Reminders
	• Double‑check Inputs: Confirm file names, data formats, and header consistency before analysis.
	• Validate Outputs: Reconcile summary metrics against raw data aggregates.
	• Call Out Assumptions: Label any inferred defaults or interpolations.
	• Flag Uncertainties: List any missing or ambiguous data elements across all file types.
	• Maintain Confidentiality: Mask or aggregate any sensitive identifiers.
	• Complete All Analysis: Process all datasets and generate all requested visualizations and insights before delivering the final response.

NEVER break your analysis into multiple messages or ask the user if you should continue - always deliver the complete solution in one comprehensive response. Focus on delivering maximum analytical value in a single, thorough response.

        
        """
    
    def save_agent_ids(self, agent_ids: Dict[str, str]) -> None:
        """
        Save agent IDs to a file for persistence between server restarts.
        
        Args:
            agent_ids: Dictionary of agent names to agent IDs
        """
        try:
            # If agent_ids is empty, remove the file instead
            if not agent_ids:
                self._remove_agent_ids_file()
                return
                
            with open(self.AGENT_IDS_FILE, 'w') as f:
                json.dump(agent_ids, f)
            self.logger.info(f"Saved {len(agent_ids)} agent IDs to {self.AGENT_IDS_FILE}")
        except Exception as e:
            self.logger.warning(f"Failed to save agent IDs to file: {str(e)}")
    
    def _remove_agent_ids_file(self) -> None:
        """
        Remove the agent IDs file if it exists.
        """
        try:
            if os.path.exists(self.AGENT_IDS_FILE):
                os.remove(self.AGENT_IDS_FILE)
                self.logger.info(f"Removed agent IDs file {self.AGENT_IDS_FILE} as no valid agents exist")
        except Exception as e:
            self.logger.warning(f"Failed to remove agent IDs file: {str(e)}")
    
    def load_agent_ids(self) -> Dict[str, str]:
        """
        Load agent IDs from file.
        
        Returns:
            Dictionary of agent names to agent IDs
        """
        if not os.path.exists(self.AGENT_IDS_FILE):
            self.logger.info(f"Agent IDs file {self.AGENT_IDS_FILE} does not exist")
            return {}
            
        try:
            with open(self.AGENT_IDS_FILE, 'r') as f:
                agent_ids = json.load(f)
            self.logger.info(f"Loaded {len(agent_ids)} agent IDs from {self.AGENT_IDS_FILE}")
            return agent_ids
        except Exception as e:
            self.logger.warning(f"Failed to load agent IDs from file: {str(e)}")
            return {}
    
    async def get_existing_agents(self) -> Dict[str, str]:
        """
        Get existing agents from Azure AI Agent Service.
        
        Returns:
            Dictionary of agent names to agent IDs
        """
        self.logger.info("Checking for existing agents in Azure AI Agent Service")
        
        # First try to load from file
        agent_ids = self.load_agent_ids()
        
        # Initialize the project client if not already done
        if not self.project_client:
            self._initialize_project_client()
        
        # If we loaded agent IDs from file, verify they still exist
        if agent_ids:
            self.logger.info(f"Loaded {len(agent_ids)} agent IDs from file, verifying they still exist...")
            validated_ids = {}
            
            for agent_name, agent_id in agent_ids.items():
                try:
                    # Attempt to get the agent to verify it exists
                    agent = self.project_client.agents.get_agent(agent_id=agent_id)
                    validated_ids[agent_name] = agent_id
                    self.logger.info(f"Verified existing agent {agent_name} with ID {agent_id}")
                except Exception as e:
                    self.logger.warning(f"Agent {agent_name} with ID {agent_id} no longer exists: {str(e)}")
            
            if validated_ids:
                if len(validated_ids) < len(agent_ids):
                    self.logger.warning(f"Only {len(validated_ids)} of {len(agent_ids)} agents from file still exist")
                    # Update the file with only valid IDs
                    self.save_agent_ids(validated_ids)
                
                if len(validated_ids) == len(self.agent_instructions):
                    self.logger.info("All required agents exist and were validated")
                    return validated_ids
                
                self.logger.info(f"Some agents need to be created, found {len(validated_ids)} valid existing agents")
                # Continue with looking for other agents, keeping the valid ones
                agent_ids = validated_ids
            else:
                self.logger.warning("None of the agents from file exist anymore, will create new ones")
                agent_ids = {}
        
        # Get authentication token for direct API calls
        token = self.credential.get_token("https://ml.azure.com/.default").token
        
        # Headers for API requests
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        try:
            # List agents using SDK approach
            agents = self.project_client.agents.list_agents()
            
            # Process the agents
            for agent in agents.data:
                if agent.name in self.agent_instructions and agent.name not in agent_ids:
                    agent_ids[agent.name] = agent.id
                    self.logger.info(f"Found existing agent {agent.name} with ID {agent.id}")
            
            if agent_ids:
                self.logger.info(f"Found {len(agent_ids)} existing agents")
                # Save for future use
                self.save_agent_ids(agent_ids)
            else:
                self.logger.info("No existing agents found, will need to deploy new ones")
            
            return agent_ids
            
        except Exception as e:
            self.logger.warning(f"Error listing agents via SDK: {str(e)}")
            
            # Fall back to direct API call if SDK fails
            try:
                # List agents using direct API call
                url = f"{self.endpoint}/assistants?api-version=2024-12-01-preview"
                response = await self._make_async_request("GET", url, headers)
                
                if response and "data" in response:
                    for agent in response["data"]:
                        agent_name = agent.get("name")
                        if agent_name in self.agent_instructions and agent_name not in agent_ids:
                            agent_ids[agent_name] = agent.get("id")
                            self.logger.info(f"Found existing agent {agent_name} with ID {agent.get('id')}")
                
                if agent_ids:
                    self.logger.info(f"Found {len(agent_ids)} existing agents via API")
                    # Save for future use
                    self.save_agent_ids(agent_ids)
                else:
                    self.logger.info("No existing agents found via API, will need to deploy new ones")
                
                return agent_ids
                
            except Exception as api_e:
                self.logger.warning(f"Error listing agents via API: {str(api_e)}")
                return agent_ids  # Return whatever valid IDs we have, even if empty
    
    async def deploy_agents(self) -> Dict[str, str]:
        """
        Deploy agents to Azure AI Agent Service.
        
        Creates or updates Azure AI Agents using the current API (2024-12-01-preview)
        
        Returns:
            Dictionary of agent names to agent IDs
        """
        self.logger.info("Deploying agents to Azure AI Agent Service")
        
        # First check for existing agents
        agent_ids = await self.get_existing_agents()
        
        # If we already have all the agents we need, return them
        if len(agent_ids) == len(self.agent_instructions):
            self.logger.info("All required agents already exist, using existing agents")
            return agent_ids
        
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
        
        # Find and upload Excel files from the data directory
        uploaded_files = await self._upload_excel_files_async()
        if not uploaded_files:
            self.logger.warning("No Excel files were uploaded. Code Interpreter will have limited functionality.")
        else:
            self.logger.info(f"Successfully uploaded {len(uploaded_files)} Excel files for Code Interpreter")
        
        # Configure Code Interpreter tool with the uploaded files
        code_interpreter = CodeInterpreterTool(file_ids=[f.id for f in uploaded_files])
        
        # Deploy each missing agent type
        for agent_type, instructions in self.agent_instructions.items():
            # Skip if we already have this agent
            if agent_type in agent_ids:
                self.logger.info(f"Agent {agent_type} already exists with ID {agent_ids[agent_type]}, skipping deployment")
                continue
                
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
        
        # Save agent IDs for future use
        self.save_agent_ids(agent_ids)
        
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