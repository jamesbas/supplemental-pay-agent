import os
import logging
import json
import asyncio
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
from pathlib import Path

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
    return jsonify({"status": "ok", "message": "API server is running"})

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for processing user messages
    """
    try:
        data = request.json
        message = data.get('message', '')
        role = data.get('role', 'hr')
        test_type = data.get('testType', 'default')
        disable_tools = data.get('disableTools', False)
        files = data.get('files', [])
        
        logger.info(f"Received chat request: role={role}, test_type={test_type}, disable_tools={disable_tools}")
        
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
            finally:
                loop.close()
        
        # Convert role to lowercase to match agent ID keys
        role = role.lower()
        
        # Map role to agent ID
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
    app.run(host='0.0.0.0', port=port, debug=True) 