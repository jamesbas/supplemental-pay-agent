import os
import logging
import json
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path
from datetime import datetime

# Import the Azure Agent Orchestrator
from src.orchestration.azure_agent_orchestrator import AzureAgentOrchestrator
from src.orchestration.azure_agent_definitions import AzureAgentDefinitions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("api_server.log")
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize orchestrator (will be lazy-loaded when needed)
orchestrator = None

def get_orchestrator():
    """
    Lazy-load the orchestrator to avoid initialization at import time
    """
    global orchestrator
    if orchestrator is None:
        logger.info("Initializing Azure Agent Orchestrator")
        # Load config from environment variables
        config = {
            "azure_openai": {
                "deployment_name": os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o"),
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
        orchestrator = AzureAgentOrchestrator(config)
    return orchestrator

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        "status": "ok", 
        "message": "API server is running",
        "timestamp": str(datetime.now()),
        "orchestrator_initialized": orchestrator is not None,
        "agent_ids": orchestrator.agent_ids if orchestrator else None
    })

@app.route('/api/test', methods=['GET', 'POST'])
def test_endpoint():
    """
    Test endpoint to verify API server is functional
    """
    if request.method == 'POST':
        try:
            data = request.json or {}
            message = data.get('message', 'Test message')
            
            # If test_route_request flag is set, try calling route_request
            if data.get('test_route_request'):
                logger.info("Testing route_request method")
                try:
                    # Get orchestrator
                    _orchestrator = get_orchestrator()
                    
                    # Deploy agents if not already deployed
                    if not _orchestrator.agent_ids:
                        logger.info("Deploying agents...")
                        agent_definitions = AzureAgentDefinitions(_orchestrator.config, debug_mode=True)
                        
                        # Run the async deployment function
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            _orchestrator.agent_ids = loop.run_until_complete(agent_definitions.deploy_agents())
                            logger.info(f"Deployed agent IDs: {_orchestrator.agent_ids}")
                        finally:
                            loop.close()
                    
                    # Execute route_request
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        response = loop.run_until_complete(
                            _orchestrator.route_request(message)
                        )
                        logger.info(f"route_request response: {response}")
                        return jsonify({
                            "status": "success",
                            "message": "Successfully called route_request",
                            "route_request_response": response,
                            "data_received": data
                        })
                    finally:
                        loop.close()
                except Exception as route_error:
                    logger.error(f"Error testing route_request: {str(route_error)}", exc_info=True)
                    return jsonify({
                        "status": "error",
                        "message": f"Error testing route_request: {str(route_error)}",
                        "data_received": data
                    }), 500
            
            return jsonify({
                "status": "success",
                "message": "Test endpoint received POST data",
                "data_received": data,
                "method": "POST"
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "message": f"Error processing POST data: {str(e)}",
                "method": "POST"
            }), 500
    else:
        return jsonify({
            "status": "success",
            "message": "Test endpoint is working",
            "method": "GET",
            "timestamp": str(datetime.now())
        })

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for processing user messages
    """
    try:
        data = request.json
        # Log the full JSON data for debugging
        logger.info(f"Received raw data: {json.dumps(data)}")
        
        # Support both camelCase and snake_case for parameters
        message = data.get('message', '')
        role = data.get('role', 'hr')
        
        # Try both camelCase and snake_case for test_type
        test_type = data.get('testType', data.get('test_type', 'default'))
        
        # Try both camelCase and snake_case for disable_tools
        disable_tools = data.get('disableTools', data.get('disable_tools', False))
        
        files = data.get('files', [])
        
        logger.info(f"Processed parameters: role={role}, test_type={test_type}, disable_tools={disable_tools}")
        
        # Get orchestrator
        _orchestrator = get_orchestrator()
        
        # Deploy agents if not already deployed
        if not _orchestrator.agent_ids:
            logger.info("Deploying agents...")
            agent_definitions = AzureAgentDefinitions(_orchestrator.config, debug_mode=True)
            
            # Run the async deployment function
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                _orchestrator.agent_ids = loop.run_until_complete(agent_definitions.deploy_agents())
                logger.info(f"Deployed agent IDs: {_orchestrator.agent_ids}")
            finally:
                loop.close()
        else:
            logger.info(f"Using existing agent IDs: {_orchestrator.agent_ids}")
        
        # Convert role to lowercase to match agent ID keys
        role = role.lower()
        
        # Process the request based on role
        if role == 'intelligent':
            # Use the orchestrator's route_request method for intelligent routing
            logger.info("Using intelligent routing for the request")
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    _orchestrator.route_request(message)
                )
            finally:
                loop.close()
        else:
            # Map role to agent ID for direct agent call
            agent_id_mapping = {
                'hr': 'policy_extraction_agent',
                'manager': 'pay_calculation_agent',
                'payroll': 'analytics_agent'
            }
            
            agent_type = agent_id_mapping.get(role, 'policy_extraction_agent')
            agent_id = _orchestrator.agent_ids.get(agent_type)
            
            if not agent_id:
                logger.error(f"Agent not found for role: {role}")
                return jsonify({"error": f"Agent not found for role: {role}"}), 404
            
            # Execute the agent based on test type
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    _orchestrator._run_agent_via_sdk(agent_id, message, disable_tools)
                )
            finally:
                loop.close()
        
        # Process the response
        content = response.get("result", "I'm sorry, I couldn't generate a response.")
        if "error" in response:
            logger.error(f"Agent error: {response['error']}")
            content = f"Error: {response['error']}"
        
        # Return the response
        return jsonify({
            "content": content,
            "timestamp": str(response.get("timestamp", "")),
            "thread_id": response.get("thread_id", ""),
            "run_id": response.get("run_id", "")
        })
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    File upload endpoint
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file part"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        
        # Save the file to the upload folder
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        logger.info(f"File uploaded: {filename} to {file_path}")
        
        # In a real implementation, you would upload the file to Azure AI Agent Service
        # and return the file ID. For now, just return the filename.
        return jsonify({
            "fileId": filename,
            "fileName": filename,
            "message": "File uploaded successfully"
        })
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}", exc_info=True)
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True) 