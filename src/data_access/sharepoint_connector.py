import os
import logging
from typing import Dict, Any, List, Optional, BinaryIO
from pathlib import Path
import tempfile

from office365.runtime.auth.user_credential import UserCredential
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File


class SharePointConnector:
    """
    Connector for accessing SharePoint files and documents.
    Handles authentication and file retrieval from SharePoint.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SharePoint connector.
        
        Args:
            config: SharePoint configuration dictionary containing site_url and credentials
        """
        self.logger = logging.getLogger(__name__)
        self.site_url = config.get("site_url")
        self.folder_path = config.get("folder_path", "Shared Documents")
        
        # Get credentials from environment or config
        self.username = config.get("username") or os.getenv("SHAREPOINT_USERNAME")
        self.password = config.get("password") or os.getenv("SHAREPOINT_PASSWORD")
        
        if not self.site_url:
            raise ValueError("SharePoint site URL is required")
        
        if not self.username or not self.password:
            self.logger.warning("SharePoint credentials not provided. Some operations may fail.")
        
        self.logger.info(f"SharePoint connector initialized for site: {self.site_url}")
    
    def get_context(self) -> ClientContext:
        """
        Create and return an authenticated SharePoint client context.
        
        Returns:
            Authenticated SharePoint client context
        """
        try:
            credentials = UserCredential(self.username, self.password)
            context = ClientContext(self.site_url).with_credentials(credentials)
            return context
        except Exception as e:
            self.logger.error(f"Failed to create SharePoint context: {str(e)}")
            raise
    
    def list_files(self, folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files in the specified SharePoint folder.
        
        Args:
            folder_path: Path to the folder in SharePoint (relative to site root)
            
        Returns:
            List of file information dictionaries
        """
        target_folder = folder_path or self.folder_path
        self.logger.info(f"Listing files in SharePoint folder: {target_folder}")
        
        try:
            ctx = self.get_context()
            target_folder_url = f"{target_folder}"
            
            # Get folder by server relative URL
            folder = ctx.web.get_folder_by_server_relative_url(target_folder_url)
            files = folder.files
            ctx.load(files)
            ctx.execute_query()
            
            result = []
            for file in files:
                result.append({
                    "name": file.properties["Name"],
                    "url": file.properties["ServerRelativeUrl"],
                    "size": file.properties["Length"],
                    "time_created": file.properties["TimeCreated"],
                    "time_modified": file.properties["TimeLastModified"]
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error listing files in SharePoint folder {target_folder}: {str(e)}")
            return []
    
    def download_file(self, file_url: str, local_path: Optional[str] = None) -> str:
        """
        Download a file from SharePoint to a local path.
        
        Args:
            file_url: Server relative URL of the file
            local_path: Optional local path to save the file
            
        Returns:
            Path to the downloaded file
        """
        self.logger.info(f"Downloading file from SharePoint: {file_url}")
        
        try:
            ctx = self.get_context()
            
            # Create temp file if local_path not provided
            if not local_path:
                file_name = file_url.split('/')[-1]
                temp_dir = tempfile.gettempdir()
                local_path = os.path.join(temp_dir, file_name)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
            
            # Download the file
            with open(local_path, "wb") as local_file:
                file = ctx.web.get_file_by_server_relative_url(file_url)
                file.download(local_file)
                ctx.execute_query()
            
            self.logger.info(f"File downloaded successfully to {local_path}")
            return local_path
        except Exception as e:
            self.logger.error(f"Error downloading file {file_url}: {str(e)}")
            raise
    
    def get_excel_files(self) -> List[str]:
        """
        Get all Excel files in the configured folder.
        
        Returns:
            List of local paths to downloaded Excel files
        """
        self.logger.info("Retrieving all Excel files from SharePoint")
        
        # List all files
        files = self.list_files()
        
        # Filter Excel files
        excel_files = [f for f in files if f["name"].lower().endswith(('.xlsx', '.xls'))]
        
        # Download each Excel file
        local_paths = []
        for file in excel_files:
            try:
                local_path = self.download_file(file["url"])
                local_paths.append(local_path)
            except Exception as e:
                self.logger.error(f"Failed to download Excel file {file['name']}: {str(e)}")
        
        return local_paths
    
    def get_policy_documents(self, document_types: Optional[List[str]] = None) -> List[str]:
        """
        Get policy documents from SharePoint.
        
        Args:
            document_types: Optional list of document extensions to filter by
            
        Returns:
            List of local paths to downloaded policy documents
        """
        self.logger.info("Retrieving policy documents from SharePoint")
        
        if not document_types:
            document_types = ['.docx', '.doc', '.pdf', '.xlsx', '.xls']
        
        # List all files
        files = self.list_files()
        
        # Filter by document types
        policy_files = [
            f for f in files 
            if any(f["name"].lower().endswith(ext) for ext in document_types)
        ]
        
        # Download each policy document
        local_paths = []
        for file in policy_files:
            try:
                local_path = self.download_file(file["url"])
                local_paths.append(local_path)
            except Exception as e:
                self.logger.error(f"Failed to download policy document {file['name']}: {str(e)}")
        
        return local_paths


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Example configuration
    config = {
        "site_url": "https://microsoft.sharepoint.com/teams/DXC-SupplementalPayAgentDemo",
        "folder_path": "Shared Documents"
    }
    
    # Initialize connector
    connector = SharePointConnector(config)
    
    # List files
    files = connector.list_files()
    print(f"Found {len(files)} files in SharePoint")
    
    # Get Excel files
    excel_files = connector.get_excel_files()
    print(f"Downloaded {len(excel_files)} Excel files") 