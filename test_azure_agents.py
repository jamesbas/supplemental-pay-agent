"""
Test script for Azure OpenAI Service

This script tests the Azure OpenAI client to ensure the basic connection works
"""

import os
import sys
import logging
from dotenv import load_dotenv
from openai import AzureOpenAI

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Check if all necessary environment variables are set
required_env_vars = ['AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_DEPLOYMENT_NAME']
for var in required_env_vars:
    if not os.environ.get(var):
        logger.error(f"Environment variable {var} is not set.")
        sys.exit(1)

def test_azure_openai():
    """Test Azure OpenAI service"""
    logger.info("\n\n=== Testing Azure OpenAI Service ===\n")
    
    try:
        # Initialize the Azure OpenAI client
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2024-02-15-preview",  # Using a more recent API version
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )
        
        deployment_name = os.environ["AZURE_OPENAI_DEPLOYMENT_NAME"]
        
        # Test a completion
        logger.info("Sending test chat completion request...")
        
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant specialized in supplemental pay policies."},
                {"role": "user", "content": "Explain the difference between overtime pay and standby pay in a few sentences."}
            ],
            temperature=0.7,
            max_tokens=150
        )
        
        logger.info(f"\nResponse: {response.choices[0].message.content}\n")
        logger.info("Azure OpenAI test completed successfully!")
        return True
    
    except Exception as e:
        logger.error(f"Error testing Azure OpenAI Service: \n\n{str(e)}\n\n")
        return False

if __name__ == "__main__":
    success = test_azure_openai()
    sys.exit(0 if success else 1) 