import os
import asyncio
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

async def main():
    # Initialize kernel
    kernel = sk.Kernel()
    
    # Get API credentials from environment variables
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
    
    print(f"API Key: {api_key[:5]}{'*' * 10}")
    print(f"Endpoint: {endpoint}")
    
    try:
        print("Creating OpenAIChatCompletion with correct parameters...")
        
        # For OpenAI directly
        service1 = OpenAIChatCompletion(
            ai_model_id="gpt-3.5-turbo",
            api_key=api_key
        )
        print("OpenAI direct initialization worked!")
        
        # For Azure OpenAI - correct approach
        azure_service = OpenAIChatCompletion(
            ai_model_id=deployment_name,
            api_key=api_key,
            service_id="azure-openai"  # Specify a service_id for the kernel to reference
        )
        print("Azure OpenAI initialization worked!")
        
        # Add the service to the kernel
        kernel.add_chat_service("azure-openai", azure_service)
        print("Service added to kernel successfully!")
        
        # Create a semantic function for chat
        chat_function = kernel.create_function_from_prompt(
            "What is the capital of France?",
            function_name="chat",
            plugin_name="conversation"
        )
        
        # Execute the function with the Azure service
        print("Invoking the chat function...")
        result = await kernel.invoke(chat_function, 
                                    service_id="azure-openai",
                                    extension_data={"api_type": "azure", "endpoint": endpoint})
        
        print(f"Response: {result}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import inspect
        print(f"OpenAIChatCompletion.__init__ signature: {inspect.signature(OpenAIChatCompletion.__init__)}")

if __name__ == "__main__":
    asyncio.run(main()) 