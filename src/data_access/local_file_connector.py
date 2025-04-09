import os
import logging
import glob
from typing import Dict, Any, List, Optional
from pathlib import Path


class LocalFileConnector:
    """
    Connector for accessing local files from the data directory.
    Provides similar interface to SharePointConnector for compatibility.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the local file connector.
        
        Args:
            config: Configuration dictionary containing data_dir
        """
        self.logger = logging.getLogger(__name__)
        self.data_dir = config.get("data_dir", "data")
        
        # Ensure data directory is absolute
        if not os.path.isabs(self.data_dir):
            self.data_dir = os.path.abspath(self.data_dir)
        
        if not os.path.exists(self.data_dir):
            self.logger.warning(f"Data directory {self.data_dir} does not exist. Creating it.")
            os.makedirs(self.data_dir, exist_ok=True)
        
        self.logger.info(f"Local file connector initialized for directory: {self.data_dir}")
    
    def list_files(self, folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in the specified local folder.
        
        Args:
            folder_path: Path to the folder (relative to data_dir)
            
        Returns:
            List of file information dictionaries
        """
        target_folder = os.path.join(self.data_dir, folder_path) if folder_path else self.data_dir
        self.logger.info(f"Listing files in folder: {target_folder}")
        
        try:
            # Get all files in the directory
            file_paths = glob.glob(os.path.join(target_folder, "*"))
            
            result = []
            for file_path in file_paths:
                if os.path.isfile(file_path):
                    file_stat = os.stat(file_path)
                    file_name = os.path.basename(file_path)
                    
                    result.append({
                        "name": file_name,
                        "url": file_path,  # Use full path as "url" for compatibility
                        "size": file_stat.st_size,
                        "time_created": file_stat.st_ctime,
                        "time_modified": file_stat.st_mtime
                    })
            
            return result
        except Exception as e:
            self.logger.error(f"Error listing files in folder {target_folder}: {str(e)}")
            return []
    
    def download_file(self, file_url: str, local_path: Optional[str] = None) -> str:
        """
        "Download" a file (actually just returns the path since it's already local).
        
        Args:
            file_url: Path to the file
            local_path: Optional local path to copy the file to
            
        Returns:
            Path to the file
        """
        self.logger.info(f"Accessing local file: {file_url}")
        
        try:
            # If file_url is not an absolute path, it's relative to data_dir
            if not os.path.isabs(file_url):
                file_url = os.path.join(self.data_dir, file_url)
            
            # If local_path is specified, copy the file
            if local_path:
                import shutil
                os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                shutil.copy2(file_url, local_path)
                return local_path
            
            return file_url
        except Exception as e:
            self.logger.error(f"Error accessing local file {file_url}: {str(e)}")
            raise
    
    def get_excel_files(self) -> List[str]:
        """
        Get all Excel files in the data directory.
        
        Returns:
            List of paths to Excel files
        """
        self.logger.info("Retrieving all Excel files from data directory")
        
        # List all files
        files = self.list_files()
        
        # Filter Excel files
        excel_files = [f for f in files if f["name"].lower().endswith(('.xlsx', '.xls'))]
        
        # Return paths to Excel files
        return [f["url"] for f in excel_files]
    
    def get_policy_documents(self, document_types: Optional[List[str]] = None) -> List[str]:
        """
        Get policy documents from data directory.
        
        Args:
            document_types: Optional list of document extensions to filter by
            
        Returns:
            List of paths to policy documents
        """
        self.logger.info("Retrieving policy documents from data directory")
        
        if not document_types:
            document_types = ['.docx', '.doc', '.pdf']
        
        # List all files
        files = self.list_files()
        
        # Filter by document types
        policy_files = [
            f for f in files 
            if any(f["name"].lower().endswith(ext) for ext in document_types)
        ]
        
        # Return paths to policy documents
        return [f["url"] for f in policy_files]


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = {
        "data_dir": "data"
    }
    
    # Initialize connector
    connector = LocalFileConnector(config)
    
    # List files
    files = connector.list_files()
    print(f"Found {len(files)} files in data directory")
    
    # Get Excel files
    excel_files = connector.get_excel_files()
    print(f"Found {len(excel_files)} Excel files") 