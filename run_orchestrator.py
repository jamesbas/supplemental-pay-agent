#!/usr/bin/env python
"""
Wrapper script to run the SupplementalPayOrchestrator from the root directory.
This avoids relative import issues.
"""
import asyncio
import logging
from src.orchestration.orchestrator import main

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Run the main function
    asyncio.run(main()) 