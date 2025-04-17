# Azure Function for Copilot Studio Integration

This directory contains an Azure Function implementation that provides a custom skill for Microsoft Copilot Studio, allowing it to interface with the DXC Supplemental Pay AI Agent Orchestrator.

## Setup

1. Install the Azure Functions Core Tools if you haven't already:
   ```
   npm install -g azure-functions-core-tools@4
   ```

2. Fill in the missing values in `local.settings.json`:
   - `AZURE_OPENAI_API_KEY`: Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT`: Your Azure OpenAI endpoint
   - `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID
   - `AZURE_RESOURCE_GROUP`: Your Azure resource group name
   - `AZURE_PROJECT_NAME`: Your Azure project name
   - `AZURE_AI_HOSTNAME`: Your Azure AI hostname

## Local Testing

To test the function locally:

1. Start the Azure Functions runtime:
   ```
   cd function_app
   func start
   ```

2. Test the manifest endpoint at:
   ```
   GET http://localhost:7071/api/manifest
   ```

3. Test the messages endpoint at:
   ```
   POST http://localhost:7071/api/messages
   Content-Type: application/json

   {
     "text": "What are the standby payment policies for UK employees?"
   }
   ```

## Deployment to Azure

1. Create a new Function App in Azure:
   ```
   az login
   az group create --name myResourceGroup --location eastus
   az storage account create --name mystorageacct --location eastus --resource-group myResourceGroup --sku Standard_LRS
   az functionapp create --resource-group myResourceGroup --consumption-plan-location eastus --runtime python --runtime-version 3.9 --functions-version 4 --name myskillapp --storage-account mystorageacct --os-type linux
   ```

2. Deploy the function app:
   ```
   cd function_app
   func azure functionapp publish myskillapp
   ```

3. Set the application settings:
   ```
   az functionapp config appsettings set --name myskillapp --resource-group myResourceGroup --settings "AZURE_OPENAI_API_KEY=your_api_key" "AZURE_OPENAI_ENDPOINT=your_endpoint" "AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o" "AZURE_SUBSCRIPTION_ID=your_subscription_id" "AZURE_RESOURCE_GROUP=your_resource_group" "AZURE_PROJECT_NAME=your_project_name" "AZURE_AI_HOSTNAME=your_hostname" "DATA_DIR=data"
   ```

## Integration with Copilot Studio

1. Open Copilot Studio in your Microsoft 365 tenant
2. Create a new agent or open an existing one
3. Go to "Settings" > "Skills" > "Add a skill"
4. For the manifest URL, use:
   ```
   https://myskillapp.azurewebsites.net/api/manifest
   ```
5. Complete the registration process
6. Create or edit a topic in your Copilot
7. Add a node that uses the DXC Supplemental Pay AI Agent skill

## Troubleshooting

- If you encounter issues with dependencies, ensure all required packages are listed in requirements.txt
- Check the function app logs in the Azure portal
- For local debugging, set `"AzureFunctionsJobHost:logging:logLevel:default": "Debug"` in local.settings.json
- Ensure you have the right permissions for the Azure OpenAI model and Azure AI Agent Service 