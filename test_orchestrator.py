import asyncio
import logging
from src.orchestration.orchestrator import SupplementalPayOrchestrator

# Set up logging
logging.basicConfig(level=logging.INFO)

async def main():
    # Initialize the orchestrator
    orchestrator = SupplementalPayOrchestrator()
    
    print("Testing HR request...")
    hr_response = await orchestrator.route_request(
        "What are the current standby payment policies for UK employees?",
        "hr"
    )
    print(f"HR Response: {hr_response[:100]}...\n")
    
    print("Testing Manager request with employee ID...")
    manager_response = await orchestrator.route_request(
        "Calculate the appropriate supplemental pay for overtime work",
        "manager",
        "10000518"
    )
    print(f"Manager Response: {manager_response[:100]}...\n")
    
    print("Testing Payroll request...")
    payroll_response = await orchestrator.route_request(
        "Identify any outliers in this month's supplemental pay claims",
        "payroll"
    )
    print(f"Payroll Response: {payroll_response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main()) 