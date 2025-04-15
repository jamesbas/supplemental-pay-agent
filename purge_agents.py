import os
from dotenv import load_dotenv
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

# Load environment variables from the .env file
load_dotenv()

# Get the Foundry Project connection string from the environment variable
connection_string = os.environ["AZURE_AI_PROJECT_ID"]

# The agent ID that should NOT be deleted.
EXCLUDE_AGENT_ID = "asst_Pqxrw04FDl74cZh3YqQtrYbE"

# Create an AIProjectClient instance using the connection string and the default Azure credential.
project_client = AIProjectClient.from_connection_string(
    credential=DefaultAzureCredential(),
    conn_str=connection_string
)

def bulk_delete_agents(client: AIProjectClient):
    """
    Deletes all agents in the Azure AI Foundry project except the one with the EXCLUDE_AGENT_ID.
    This function checks if the response contains a 'data' property (or key) with the list of agent objects.
    """
    # Get the response from list_agents()
    agents_response = client.agents.list_agents()
    
    # Try to extract the list of agent objects from the response.
    try:
        # If the response has a 'data' attribute, use that.
        agents = agents_response.data
    except AttributeError:
        # Otherwise, if it is a dict with a "data" key, use that.
        if isinstance(agents_response, dict) and "data" in agents_response:
            agents = agents_response["data"]
        else:
            # Fallback: assume agents_response is already the iterable of agent objects.
            agents = agents_response

    deleted_count = 0

    for agent in agents:
        # Check if the agent object has an 'id' attribute;
        # if not, assume agent is already an agent ID (string).
        agent_id = agent.id if hasattr(agent, "id") else agent
        if agent_id == EXCLUDE_AGENT_ID:
            print(f"Skipping agent with ID: {agent_id}")
            continue

        try:
            print(f"Deleting agent with ID: {agent_id}...")
            client.agents.delete_agent(agent_id)
            print(f"Successfully deleted agent with ID: {agent_id}")
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting agent with ID {agent_id}: {e}")

    print(f"Bulk deletion completed. Total agents deleted: {deleted_count}")

# Use the project client in a context manager to ensure proper resource cleanup.
with project_client:
    bulk_delete_agents(project_client)
