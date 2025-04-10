"""
Test script for Azure AI Agent Service

This script tests the Azure AI Agent Service implementation
"""

import os
import sys
import logging
import asyncio
import json
import argparse
import glob
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("azure_agent_test.log")
    ]
)
logger = logging.getLogger(__name__)

# Log environment variable values (except API keys) for debugging
for var_name, var_value in os.environ.items():
    if var_name.startswith('AZURE_') and not var_name.endswith('_API_KEY'):
        logger.info(f"Environment variable {var_name}: {var_value}")

# Check if all necessary environment variables are set
required_env_vars = [
    'AZURE_SUBSCRIPTION_ID', 
    'AZURE_RESOURCE_GROUP', 
    'AZURE_PROJECT_NAME',
    'AZURE_AI_HOSTNAME',
    'AZURE_OPENAI_DEPLOYMENT_NAME',
    'AZURE_OPENAI_API_KEY',
    'AZURE_OPENAI_ENDPOINT',
]

for var in required_env_vars:
    if not os.environ.get(var):
        logger.error(f"Environment variable {var} is not set.")
        sys.exit(1)

# Import directly from src to test
from src.orchestration.azure_agent_orchestrator import AzureAgentOrchestrator
from src.orchestration.azure_agent_definitions import AzureAgentDefinitions

# Parse command line arguments
def parse_args():
    parser = argparse.ArgumentParser(description='Test Azure AI Agent Service')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--test-model', type=str, help='Specify a model to test with')
    parser.add_argument('--disable-tools', action='store_true', help='Disable tools for all tests')
    parser.add_argument('--test-type', choices=['all', 'deployment', 'simple', 'excel', 'orchestrator', 'intelligent_orchestrator'], 
                        default='all', help='Type of test to run')
    return parser.parse_args()

async def test_agent_deployment(debug_mode=False, test_model=None):
    """Test deploying Azure AI Agents"""
    logger.info("\n=== Testing Azure AI Agent Service - Agent Deployment ===\n")
    
    try:
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": test_model or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
            },
            "azure_subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "azure_resource_group": os.environ.get("AZURE_RESOURCE_GROUP"),
            "azure_project_name": os.environ.get("AZURE_PROJECT_NAME"),
            "azure_ai_hostname": os.environ.get("AZURE_AI_HOSTNAME"),
            "local_files": {
                "data_dir": os.environ.get("DATA_DIR", "data")
            }
        }
        
        # Log the config (excluding API keys)
        safe_config = config.copy()
        if "azure_openai" in safe_config and "api_key" in safe_config["azure_openai"]:
            safe_config["azure_openai"]["api_key"] = "[REDACTED]"
        
        logger.info(f"Using configuration: {json.dumps(safe_config, indent=2)}")
        
        if test_model:
            logger.info(f"Using test model: {test_model}")
        
        # Initialize agent definitions with debug mode if specified
        logger.info("Initializing agent definitions...")
        agent_definitions = AzureAgentDefinitions(config, debug_mode=debug_mode)
        
        # Deploy agents
        logger.info("Deploying agents...")
        agent_ids = await agent_definitions.deploy_agents()
        
        logger.info(f"Successfully deployed agents: {json.dumps(agent_ids, indent=2)}")
        return agent_ids
    
    except Exception as e:
        logger.error(f"Error deploying agents: {str(e)}", exc_info=True)
        return None

async def test_agent_with_excel(debug_mode=False, test_model=None, disable_tools=False):
    """Test an agent with Excel file analysis using Code Interpreter"""
    logger.info("\n=== Testing Agent with Excel File Analysis using Code Interpreter ===\n")
    
    try:
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": test_model or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
            },
            "azure_subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "azure_resource_group": os.environ.get("AZURE_RESOURCE_GROUP"),
            "azure_project_name": os.environ.get("AZURE_PROJECT_NAME"),
            "azure_ai_hostname": os.environ.get("AZURE_AI_HOSTNAME"),
            "local_files": {
                "data_dir": os.environ.get("DATA_DIR", "data")
            }
        }
        
        # Initialize orchestrator
        logger.info("Initializing Azure Agent Orchestrator...")
        orchestrator = AzureAgentOrchestrator(config)
        
        # Deploy agents if needed using the updated AzureAgentDefinitions with debug mode
        if not orchestrator.agent_ids:
            logger.info("Deploying agents...")
            agent_definitions = AzureAgentDefinitions(config, debug_mode=debug_mode)
            orchestrator.agent_ids = await agent_definitions.deploy_agents()
        
        # Find the Excel files that were uploaded
        data_dir = config.get("local_files", {}).get("data_dir", os.environ.get("DATA_DIR", "data"))
        excel_files = []
        for ext in ["*.xlsx", "*.xls", "*.csv"]:
            pattern = os.path.join(data_dir, "**", ext)
            excel_files.extend(glob.glob(pattern, recursive=True))
        
        if not excel_files:
            logger.error("No Excel files found in the data directory")
            return {"error": "No Excel files found"}
        
        logger.info(f"Found {len(excel_files)} Excel files: {[os.path.basename(f) for f in excel_files]}")
        
        # Use the analytics agent for Excel analysis
        agent_type = "analytics_agent"
        agent_id = orchestrator.agent_ids.get(agent_type)
        
        if not agent_id:
            logger.error(f"Agent {agent_type} not found in deployed agents")
            return {"error": f"Agent {agent_type} not found"}
        
        # Create a query that references the uploaded Excel files
        file_names = ", ".join([os.path.basename(f) for f in excel_files])
        query = f"""
        I've uploaded some Excel files: {file_names}. 
        Please analyze the data in these files and provide the following:
        1. A summary of the contents of each file
        2. Basic statistics about each file (min, max, mean, etc. for numeric columns)
        3. Create a visualization that best represents the data in one of the files
        """
        
        logger.info(f"Testing {agent_type} with Code Interpreter and Excel files")
        logger.info(f"Query: {query}")
        
        # Use the SDK-based method with tools enabled (don't disable tools)
        response = await orchestrator._run_agent_via_sdk(agent_id, query, disable_tools=False)
        
        if "result" in response:
            result = response["result"]
            logger.info(f"\nResponse from {agent_type} using Code Interpreter:\n{result[:500]}...\n")
            
            # Check for file outputs
            thread_id = response.get("thread_id")
            run_id = response.get("run_id")
            
            if thread_id:
                logger.info(f"Thread ID: {thread_id}")
                
                # Get images and generated files
                if orchestrator.project_client:
                    try:
                        messages = orchestrator.project_client.agents.list_messages(thread_id=thread_id)
                        
                        # Save any generated files
                        target_dir = "output"
                        os.makedirs(target_dir, exist_ok=True)
                        
                        # Check for file annotations
                        file_count = 0
                        for message in messages.data:
                            if hasattr(message, "content"):
                                for content_item in message.content:
                                    if hasattr(content_item, "file_path"):
                                        file_id = content_item.file_path.file_id
                                        file_name = f"output_{file_count}.png"
                                        file_count += 1
                                        
                                        logger.info(f"Saving file ID {file_id} as {file_name}")
                                        orchestrator.project_client.agents.save_file(
                                            file_id=file_id,
                                            file_name=file_name,
                                            target_dir=target_dir
                                        )
                                        logger.info(f"Saved file to {os.path.join(target_dir, file_name)}")
                                        
                        if file_count == 0:
                            logger.info("No generated files found in the response")
                            
                    except Exception as e:
                        logger.error(f"Error retrieving generated files: {str(e)}")
        
        else:
            logger.error(f"Error from agent: {response.get('error', 'Unknown error')}")
        
        return response
        
    except Exception as e:
        logger.error(f"Error testing agent with Excel files: {str(e)}", exc_info=True)
        return {"error": str(e)}

async def test_agent_simple(debug_mode=False, test_model=None, disable_tools=False):
    """Test a single agent with a simple request"""
    logger.info("\n=== Testing Single Agent with Simple Request ===\n")
    
    try:
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": test_model or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
            },
            "azure_subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "azure_resource_group": os.environ.get("AZURE_RESOURCE_GROUP"),
            "azure_project_name": os.environ.get("AZURE_PROJECT_NAME"),
            "azure_ai_hostname": os.environ.get("AZURE_AI_HOSTNAME"),
            "local_files": {
                "data_dir": os.environ.get("DATA_DIR", "data")
            }
        }
        
        # Initialize orchestrator
        logger.info("Initializing Azure Agent Orchestrator...")
        orchestrator = AzureAgentOrchestrator(config)
        
        # Deploy agents if needed using the updated AzureAgentDefinitions with debug mode
        if not orchestrator.agent_ids:
            logger.info("Deploying agents...")
            agent_definitions = AzureAgentDefinitions(config, debug_mode=debug_mode)
            orchestrator.agent_ids = await agent_definitions.deploy_agents()
        
        # Use the analytics agent for a simple test with minimal dependencies
        agent_type = "analytics_agent"
        agent_id = orchestrator.agent_ids.get(agent_type)
        
        if not agent_id:
            logger.error(f"Agent {agent_type} not found in deployed agents")
            return None
        
        # Simple fact-based query that shouldn't require external tools
        query = "What are the benefits of tracking supplemental pay data?"
        
        logger.info(f"Testing {agent_type} with query: {query}")
        
        # Use the SDK-based method with disable_tools if specified
        response = await orchestrator._run_agent_via_sdk(agent_id, query, disable_tools=disable_tools)
        
        result = response.get("result", "No result returned")
        logger.info(f"\nResponse from {agent_type}:\n{result}\n")
        
        # Return the full response for more detailed analysis
        return response
    
    except Exception as e:
        logger.error(f"Error testing simple agent: {str(e)}", exc_info=True)
        return {"error": str(e)}

async def test_agent_orchestrator(debug_mode=False, test_model=None, disable_tools=False):
    """Test the Azure Agent Orchestrator"""
    logger.info("\n=== Testing Azure AI Agent Orchestrator ===\n")
    
    try:
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": test_model or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
            },
            "azure_subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "azure_resource_group": os.environ.get("AZURE_RESOURCE_GROUP"),
            "azure_project_name": os.environ.get("AZURE_PROJECT_NAME"),
            "azure_ai_hostname": os.environ.get("AZURE_AI_HOSTNAME"),
            "local_files": {
                "data_dir": os.environ.get("DATA_DIR", "data")
            }
        }
        
        # Initialize orchestrator
        logger.info("Initializing Azure Agent Orchestrator...")
        orchestrator = AzureAgentOrchestrator(config)
        
        # Deploy agents if needed using the updated AzureAgentDefinitions with debug mode
        if not orchestrator.agent_ids:
            logger.info("Deploying agents...")
            agent_definitions = AzureAgentDefinitions(config, debug_mode=debug_mode)
            orchestrator.agent_ids = await agent_definitions.deploy_agents()
        
        # Test running each agent type
        test_queries = {
            "policy_extraction_agent": "What are the current standby payment policies for UK employees?",
            "pay_calculation_agent": "Calculate the appropriate supplemental pay for overtime work for employee 10000518",
            "analytics_agent": "Identify trends in supplemental pay over the last quarter"
        }
        
        results = {}
        
        for agent_type, query in test_queries.items():
            logger.info(f"\nTesting {agent_type} with query: {query}")
            
            # Use the SDK-based method with disable_tools if specified
            response = await orchestrator._run_agent_via_sdk(
                orchestrator.agent_ids.get(agent_type), 
                query,
                disable_tools=disable_tools
            )
            
            results[agent_type] = response
            
            # Log just the result for readability
            result = response.get("result", "No result returned")
            if "error" in response:
                logger.error(f"\nError from {agent_type}: {response['error']}\n")
            else:
                logger.info(f"\nResponse from {agent_type}:\n{result}\n")
        
        return results
    
    except Exception as e:
        logger.error(f"Error testing agent orchestrator: {str(e)}", exc_info=True)
        return {"error": str(e)}

async def test_intelligent_orchestrator(debug_mode=False, test_model=None, disable_tools=False):
    """Test the Intelligent Orchestrator Agent functionality"""
    logger.info("\n=== Testing Intelligent Orchestrator Agent ===\n")
    
    try:
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": test_model or os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
                "api_key": os.environ.get("AZURE_OPENAI_API_KEY"),
                "endpoint": os.environ.get("AZURE_OPENAI_ENDPOINT")
            },
            "azure_subscription_id": os.environ.get("AZURE_SUBSCRIPTION_ID"),
            "azure_resource_group": os.environ.get("AZURE_RESOURCE_GROUP"),
            "azure_project_name": os.environ.get("AZURE_PROJECT_NAME"),
            "azure_ai_hostname": os.environ.get("AZURE_AI_HOSTNAME"),
            "local_files": {
                "data_dir": os.environ.get("DATA_DIR", "data")
            }
        }
        
        # Initialize orchestrator
        logger.info("Initializing Azure Agent Orchestrator...")
        orchestrator = AzureAgentOrchestrator(config)
        
        # Display available agent IDs for debugging
        logger.info(f"Available agent IDs: {orchestrator.agent_ids}")
        
        # Deploy agents if needed using the updated AzureAgentDefinitions with debug mode
        if not orchestrator.agent_ids:
            logger.info("Deploying agents...")
            agent_definitions = AzureAgentDefinitions(config, debug_mode=debug_mode)
            orchestrator.agent_ids = await agent_definitions.deploy_agents()
            logger.info(f"Deployed agent IDs: {orchestrator.agent_ids}")
        
        # Test queries for different agent types
        test_queries = [
            {
                "query": "What are the current standby payment policies for UK employees?",
                "expected_agent": "policy_extraction_agent",
                "description": "Policy extraction query"
            },
            {
                "query": "Calculate the appropriate supplemental pay for overtime work for employee 10000518",
                "expected_agent": "pay_calculation_agent",
                "description": "Pay calculation query"
            },
            {
                "query": "Identify trends in supplemental pay over the last quarter",
                "expected_agent": "analytics_agent",
                "description": "Analytics query"
            },
            {
                "query": "For a UK employee working standby, what payment should they receive and what policy covers this?",
                "expected_agent": "policy_extraction_agent",  # This is ambiguous and could go to either policy or calculation
                "description": "Mixed policy and calculation query"
            }
        ]
        
        # Add an ambiguous query to test fallback mechanisms
        test_queries.append({
            "query": "I need help with a payment issue related to policies",
            "expected_agent": "policy_extraction_agent", 
            "description": "Ambiguous query for testing fallback"
        })
        
        results = []
        
        # Test each query with the intelligent orchestrator
        for test_case in test_queries:
            query = test_case["query"]
            expected_agent = test_case["expected_agent"]
            description = test_case["description"]
            
            logger.info(f"\nTesting orchestrator with query: {query}")
            logger.info(f"Expected agent: {expected_agent}")
            
            # First test just the routing decision without calling the agent
            routing_info = await orchestrator.orchestrator_agent.analyze_query(query)
            
            logger.info(f"Routing decision: {json.dumps(routing_info, indent=2)}")
            
            # Check if routing matches expectation
            routing_correct = routing_info.get("primary_agent") == expected_agent
            
            # Now test the full route_request function
            response = await orchestrator.route_request(query)
            
            result = {
                "query": query,
                "description": description,
                "expected_agent": expected_agent,
                "routed_to": routing_info.get("primary_agent"),
                "routing_correct": routing_correct,
                "confidence": routing_info.get("confidence"),
                "response": response.get("result", "No result") if "error" not in response else f"Error: {response.get('error')}"
            }
            
            results.append(result)
            
            # Log the result without using Unicode checkmarks (Windows console compatibility)
            if routing_correct:
                logger.info(f"[CORRECT] Routing: {query} -> {routing_info.get('primary_agent')}")
            else:
                logger.warning(f"[INCORRECT] Routing: {query} -> {routing_info.get('primary_agent')} (expected {expected_agent})")
            
            if "error" in response:
                logger.error(f"Error in response: {response['error']}")
            else:
                # Show a larger portion of the response (up to 300 chars)
                result_text = response.get("result", "No result")
                logger.info(f"Response from {routing_info.get('primary_agent')}:\n{result_text[:300]}...\n")
                
                # Save full response to file for detailed review
                try:
                    os.makedirs("responses", exist_ok=True)
                    safe_filename = f"response_{routing_info.get('primary_agent')}_{test_queries.index(test_case)+1}.txt"
                    with open(os.path.join("responses", safe_filename), "w", encoding="utf-8") as f:
                        f.write(result_text)
                    logger.info(f"Full response saved to responses/{safe_filename}")
                except Exception as e:
                    logger.warning(f"Could not save response to file: {str(e)}")
        
        # Summarize the results
        correct_count = sum(1 for r in results if r["routing_correct"])
        logger.info(f"\nIntelligent Orchestrator Test Summary: {correct_count}/{len(results)} correct routings")
        
        return {
            "results": results,
            "correct_count": correct_count,
            "total_count": len(results)
        }
    
    except Exception as e:
        logger.error(f"Error testing intelligent orchestrator: {str(e)}", exc_info=True)
        return {"error": str(e)}

async def main():
    """Main test function"""
    args = parse_args()
    
    # Set logging level based on debug mode
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    try:
        # Test individual components
        logger.info("\n\n==== STARTING TESTS ====\n\n")
        logger.info(f"Test configuration: debug={args.debug}, test-model={args.test_model}, disable-tools={args.disable_tools}")
        
        # Determine which tests to run
        run_deployment = args.test_type in ['all', 'deployment']
        run_simple = args.test_type in ['all', 'simple']
        run_excel = args.test_type in ['all', 'excel']
        run_orchestrator = args.test_type in ['all', 'orchestrator']
        run_intelligent_orchestrator = args.test_type in ['all', 'intelligent_orchestrator']
        
        agent_ids = None
        if run_deployment:
            # First deploy agents
            agent_ids = await test_agent_deployment(
                debug_mode=args.debug, 
                test_model=args.test_model
            )
            
            if not agent_ids:
                logger.error("Failed to deploy agents, stopping tests")
                return 1
        
        if run_simple:
            # Test with simple query first
            simple_response = await test_agent_simple(
                debug_mode=args.debug, 
                test_model=args.test_model,
                disable_tools=args.disable_tools
            )
            
            if simple_response and "result" in simple_response and not simple_response.get("error"):
                logger.info("Simple agent test succeeded!")
            else:
                logger.warning(f"Simple agent test did not complete successfully: {simple_response.get('error', 'Unknown error')}")
        
        if run_excel:
            # Test with Excel files
            excel_response = await test_agent_with_excel(
                debug_mode=args.debug,
                test_model=args.test_model,
                disable_tools=False  # Don't disable tools for Excel test
            )
            
            if excel_response and "result" in excel_response and not excel_response.get("error"):
                logger.info("Excel analysis test succeeded!")
            else:
                logger.warning(f"Excel analysis test did not complete successfully: {excel_response.get('error', 'Unknown error')}")
        
        if run_orchestrator:
            # Then test all agents
            results = await test_agent_orchestrator(
                debug_mode=args.debug, 
                test_model=args.test_model,
                disable_tools=args.disable_tools
            )
            
            success_count = 0
            if isinstance(results, dict) and not results.get("error"):
                for agent_type, response in results.items():
                    if "result" in response and not response.get("error"):
                        logger.info(f"Test for {agent_type} completed successfully!")
                        success_count += 1
                    else:
                        error_msg = response.get("error", "Unknown error")
                        logger.warning(f"Test for {agent_type} failed: {error_msg}")
            
                if success_count > 0:
                    logger.info(f"{success_count} of {len(results)} tests completed successfully!")
                else:
                    logger.error("All tests failed.")
                    return 1
            else:
                error_msg = results.get("error", "Unknown error") if isinstance(results, dict) else "Failed to get valid results"
                logger.error(f"Orchestrator tests failed: {error_msg}")
                return 1
        
        # Test the intelligent orchestrator if requested
        if run_intelligent_orchestrator:
            logger.info("\nTesting the intelligent orchestrator...")
            orchestrator_results = await test_intelligent_orchestrator(
                debug_mode=args.debug,
                test_model=args.test_model,
                disable_tools=args.disable_tools
            )
            
            if isinstance(orchestrator_results, dict) and not orchestrator_results.get("error"):
                correct_count = orchestrator_results.get("correct_count", 0)
                total_count = orchestrator_results.get("total_count", 0)
                
                if correct_count > 0:
                    logger.info(f"Intelligent orchestrator test: {correct_count}/{total_count} correct routings")
                    
                    # Log detailed results - use ASCII symbols instead of Unicode for Windows compatibility
                    for i, result in enumerate(orchestrator_results.get("results", [])):
                        status = "[+]" if result["routing_correct"] else "[-]"
                        logger.info(f"{status} Test {i+1}: {result['description']} - routed to {result['routed_to']}")
                else:
                    logger.error("Intelligent orchestrator failed all routing tests")
                    return 1
            else:
                error_msg = orchestrator_results.get("error", "Unknown error")
                logger.error(f"Intelligent orchestrator test failed: {error_msg}")
                return 1
                
        return 0
            
    except Exception as e:
        logger.error(f"Error in main test function: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 