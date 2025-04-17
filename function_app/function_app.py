import azure.functions as func
import json
import logging
import asyncio
import sys
import os

# Add the parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now we can import from the parent directory
from app import get_orchestrator, AzureAgentDefinitions

app = func.FunctionApp()

@app.route(route="manifest")
def get_manifest(req: func.HttpRequest) -> func.HttpResponse:
    """
    Return the manifest for Copilot Studio integration
    """
    host_url = req.url.split('/api/manifest')[0]
    manifest = {
        "name": "Azure Agent Orchestrator Skill",
        "version": "1.0",
        "description": "A skill that provides access to DXC Supplemental Pay AI Agents",
        "endpoints": [
            {
                "name": "default",
                "url": f"{host_url}/api/messages"
            }
        ],
        "activities": [
            {
                "type": "message",
                "name": "message",
                "description": "Process queries with AI agents"
            }
        ],
        "properties": {
            "schemaVersion": "1.0"
        }
    }
    return func.HttpResponse(
        json.dumps(manifest),
        mimetype="application/json"
    )

@app.route(route="messages", methods=["POST"])
def copilot_messages(req: func.HttpRequest) -> func.HttpResponse:
    """
    Handle messages from Copilot Studio
    """
    try:
        data = req.get_json()
        logging.info(f"Received message from Copilot Studio: {json.dumps(data)}")
        
        # Extract message from Copilot Studio payload
        message = None
        if data and "text" in data:
            message = data["text"]
        elif data and "value" in data and "text" in data["value"]:
            message = data["value"]["text"]
        
        if not message:
            logging.error("No message found in Copilot Studio request")
            return func.HttpResponse(
                json.dumps({
                    "type": "message",
                    "text": "I couldn't understand your request. Please try again."
                }),
                mimetype="application/json"
            )
        
        # Get orchestrator
        _orchestrator = get_orchestrator()
        
        # Deploy agents if not already deployed
        if not _orchestrator.agent_ids:
            logging.info("No agent IDs found, checking for existing agents...")
            agent_definitions = AzureAgentDefinitions(_orchestrator.config, debug_mode=True)
            
            # First check for existing agents
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                # First try to get existing agents
                _orchestrator.agent_ids = loop.run_until_complete(agent_definitions.get_existing_agents())
                
                # If still no agents found, deploy new ones
                if not _orchestrator.agent_ids:
                    logging.info("No existing agents found, deploying new agents...")
                    _orchestrator.agent_ids = loop.run_until_complete(agent_definitions.deploy_agents())
                    
                logging.info(f"Using agent IDs: {_orchestrator.agent_ids}")
            finally:
                loop.close()
        
        # Process the request using intelligent routing
        logging.info("Using intelligent routing for the Copilot Studio request")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            # Use the route_request method for intelligent routing
            response = loop.run_until_complete(
                _orchestrator.route_request(message)
            )
            agent_response = response.get("response", "I couldn't process your request.")
            
            return func.HttpResponse(
                json.dumps({
                    "type": "message",
                    "text": agent_response
                }),
                mimetype="application/json"
            )
        except Exception as e:
            logging.error(f"Error processing Copilot Studio request: {str(e)}")
            return func.HttpResponse(
                json.dumps({
                    "type": "message",
                    "text": f"I encountered an error processing your request: {str(e)}"
                }),
                mimetype="application/json"
            )
        finally:
            loop.close()
    except Exception as e:
        logging.error(f"Unexpected error in Copilot Studio integration: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "type": "message",
                "text": "I encountered an unexpected error. Please try again later."
            }),
            mimetype="application/json"
        ) 