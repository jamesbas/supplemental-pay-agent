import os
import logging
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
import numpy as np
from pathlib import Path


class ExcelProcessor:
    """
    Processes Excel files for the Supplemental Pay AI Agent System.
    Extracts and transforms data from Excel files for analysis.
    """
    
    def __init__(self):
        """Initialize the Excel processor."""
        self.logger = logging.getLogger(__name__)
        self.cached_dataframes = {}  # Cache dataframes to avoid reloading
    
    def load_excel(self, file_path: str, sheet_name: Optional[Union[str, int, List[Union[str, int]]]] = None) -> Dict[str, pd.DataFrame]:
        """
        Load an Excel file into pandas DataFrames.
        
        Args:
            file_path: Path to the Excel file
            sheet_name: Sheet name or index to load (None for all sheets)
            
        Returns:
            Dictionary of sheet names to pandas DataFrames
        """
        self.logger.info(f"Loading Excel file: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            self.logger.error(f"Excel file not found: {file_path}")
            raise FileNotFoundError(f"Excel file not found: {file_path}")
        
        # Generate cache key
        cache_key = f"{file_path}:{sheet_name}"
        
        # Return cached dataframe if available
        if cache_key in self.cached_dataframes:
            self.logger.info(f"Using cached data for {file_path}")
            return self.cached_dataframes[cache_key]
        
        try:
            # Load excel file with pandas
            if sheet_name is None:
                # Load all sheets
                excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
            else:
                # Load specific sheet(s)
                sheets = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
                
                # Ensure consistent return type
                if isinstance(sheets, pd.DataFrame):
                    # Single sheet was loaded
                    if isinstance(sheet_name, (str, int)):
                        excel_data = {sheet_name: sheets}
                    else:
                        excel_data = {"Sheet1": sheets}
                else:
                    # Multiple sheets were loaded
                    excel_data = sheets
            
            # Clean up column names
            for sheet_name, df in excel_data.items():
                # Convert column names to strings and strip whitespace
                df.columns = [str(col).strip() if isinstance(col, str) else str(col) for col in df.columns]
                
                # Drop completely empty columns
                df.dropna(axis=1, how='all', inplace=True)
                
                # Replace Excel's empty cells with NaN
                df.replace(['', ' ', None], np.nan, inplace=True)
            
            # Cache the loaded dataframes
            self.cached_dataframes[cache_key] = excel_data
            
            return excel_data
        except Exception as e:
            self.logger.error(f"Error loading Excel file {file_path}: {str(e)}")
            raise
    
    def get_employee_data(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Extract employee data from the appropriate Excel file.
        
        Args:
            file_paths: List of paths to Excel files
            
        Returns:
            DataFrame containing employee data
        """
        self.logger.info("Extracting employee data from Excel files")
        
        # Look for the employee file
        employee_file = None
        for file_path in file_paths:
            if "EmpID_Legacy_Country_Payments_Hourly" in file_path:
                employee_file = file_path
                break
        
        if not employee_file:
            self.logger.warning("Employee data file not found")
            return pd.DataFrame()
        
        try:
            # Load the employee data file
            excel_data = self.load_excel(employee_file)
            
            # Get the first sheet (assuming it contains employee data)
            sheet_name = list(excel_data.keys())[0]
            df = excel_data[sheet_name]
            
            # Basic validation
            required_columns = ["Emp ID", "Emp Name", "Payment Terms", "Hourly Rate"]
            
            # Check for close matches if exact columns not found
            for required in required_columns:
                if required not in df.columns:
                    close_matches = [col for col in df.columns if required.lower() in col.lower()]
                    if close_matches:
                        df.rename(columns={close_matches[0]: required}, inplace=True)
            
            # Verify required columns exist
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                self.logger.warning(f"Missing required columns in employee data: {missing_columns}")
            
            return df
        except Exception as e:
            self.logger.error(f"Error processing employee data: {str(e)}")
            return pd.DataFrame()
    
    def get_payment_terms_data(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Extract payment terms data from the appropriate Excel file.
        
        Args:
            file_paths: List of paths to Excel files
            
        Returns:
            DataFrame containing payment terms data
        """
        self.logger.info("Extracting payment terms data from Excel files")
        
        # Look for the payment terms file
        payment_file = None
        for file_path in file_paths:
            if "Standby_Callout_Overtime_Shift_Payment" in file_path:
                payment_file = file_path
                break
        
        if not payment_file:
            self.logger.warning("Payment terms file not found")
            return pd.DataFrame()
        
        try:
            # Load the payment terms file
            excel_data = self.load_excel(payment_file)
            
            # Get the first sheet (assuming it contains payment terms data)
            sheet_name = list(excel_data.keys())[0]
            df = excel_data[sheet_name]
            
            # Clean up data
            # Remove empty rows
            df.dropna(how='all', inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Error processing payment terms data: {str(e)}")
            return pd.DataFrame()
    
    def get_hours_data(self, file_paths: List[str]) -> pd.DataFrame:
        """
        Extract hours data from the appropriate Excel file.
        
        Args:
            file_paths: List of paths to Excel files
            
        Returns:
            DataFrame containing hours data
        """
        self.logger.info("Extracting hours data from Excel files")
        
        # Look for the hours file
        hours_file = None
        for file_path in file_paths:
            if "Emp_Wage_Hours" in file_path:
                hours_file = file_path
                break
        
        if not hours_file:
            self.logger.warning("Hours data file not found")
            return pd.DataFrame()
        
        try:
            # Load the hours data file
            excel_data = self.load_excel(hours_file)
            
            # Get the first sheet (assuming it contains hours data)
            sheet_name = list(excel_data.keys())[0]
            df = excel_data[sheet_name]
            
            # Clean up data
            # Remove empty rows
            df.dropna(how='all', inplace=True)
            
            return df
        except Exception as e:
            self.logger.error(f"Error processing hours data: {str(e)}")
            return pd.DataFrame()
    
    def analyze_employee(self, employee_id: str, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze data for a specific employee.
        
        Args:
            employee_id: ID of the employee to analyze
            dataframes: Dictionary of dataframes (employee_data, payment_terms, hours_data)
            
        Returns:
            Dictionary containing analysis results
        """
        self.logger.info(f"Analyzing data for employee: {employee_id}")
        
        employee_data = dataframes.get("employee_data", pd.DataFrame())
        payment_terms = dataframes.get("payment_terms", pd.DataFrame())
        hours_data = dataframes.get("hours_data", pd.DataFrame())
        
        result = {
            "employee_id": employee_id,
            "found": False,
            "employee_info": {},
            "payment_terms": {},
            "hours_data": {},
            "recommendations": []
        }
        
        try:
            # Find employee in employee data
            if not employee_data.empty:
                employee_row = employee_data[employee_data["Emp ID"] == employee_id]
                if not employee_row.empty:
                    result["found"] = True
                    result["employee_info"] = employee_row.iloc[0].to_dict()
            
            # Get relevant payment terms
            if result["found"] and not payment_terms.empty and "Payment Terms" in result["employee_info"]:
                payment_term = result["employee_info"]["Payment Terms"]
                matching_terms = payment_terms[payment_terms.iloc[:, 0] == payment_term]
                if not matching_terms.empty:
                    result["payment_terms"] = matching_terms.iloc[0].to_dict()
            
            # Get hours data
            if not hours_data.empty:
                employee_hours = hours_data[hours_data.iloc[:, 0] == employee_id]
                if not employee_hours.empty:
                    result["hours_data"] = employee_hours.to_dict('records')
            
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing employee data: {str(e)}")
            result["error"] = str(e)
            return result
    
    def analyze_team_data(self, dataframes: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """
        Analyze data for the entire team.
        
        Args:
            dataframes: Dictionary of dataframes (employee_data, payment_terms, hours_data)
            
        Returns:
            Dictionary containing team analysis results
        """
        self.logger.info("Analyzing team data")
        
        employee_data = dataframes.get("employee_data", pd.DataFrame())
        payment_terms = dataframes.get("payment_terms", pd.DataFrame())
        hours_data = dataframes.get("hours_data", pd.DataFrame())
        
        result = {
            "team_size": 0,
            "payment_terms_summary": {},
            "hours_summary": {},
            "trends": [],
            "outliers": []
        }
        
        try:
            # Basic team statistics
            if not employee_data.empty:
                result["team_size"] = len(employee_data)
                
                # Summarize payment terms
                if "Payment Terms" in employee_data.columns:
                    terms_counts = employee_data["Payment Terms"].value_counts().to_dict()
                    result["payment_terms_summary"] = terms_counts
            
            # Analyze hours data
            if not hours_data.empty:
                # Calculate total hours by month
                month_columns = [col for col in hours_data.columns if any(month in col.lower() for month in 
                                                                         ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 
                                                                          'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])]
                
                if month_columns:
                    monthly_totals = {}
                    for col in month_columns:
                        monthly_totals[col] = hours_data[col].sum()
                    
                    result["hours_summary"] = monthly_totals
                    
                    # Identify trends
                    if len(monthly_totals) > 1:
                        # Sort by month
                        months_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                        'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                        sorted_months = sorted(monthly_totals.items(), 
                                              key=lambda x: next((i for i, m in enumerate(months_order) if m in x[0]), 100))
                        
                        # Check for increasing or decreasing trend
                        values = [v for _, v in sorted_months]
                        if all(values[i] <= values[i+1] for i in range(len(values)-1)):
                            result["trends"].append("Increasing hours trend detected")
                        elif all(values[i] >= values[i+1] for i in range(len(values)-1)):
                            result["trends"].append("Decreasing hours trend detected")
            
            return result
        except Exception as e:
            self.logger.error(f"Error analyzing team data: {str(e)}")
            result["error"] = str(e)
            return result
    
    def find_outliers(self, df: pd.DataFrame, column: str, threshold: float = 1.5) -> List[int]:
        """
        Find outliers in a dataframe column using IQR method.
        
        Args:
            df: DataFrame to analyze
            column: Column name to check for outliers
            threshold: IQR multiplier for outlier detection
            
        Returns:
            List of indices containing outliers
        """
        q1 = df[column].quantile(0.25)
        q3 = df[column].quantile(0.75)
        iqr = q3 - q1
        
        lower_bound = q1 - (threshold * iqr)
        upper_bound = q3 + (threshold * iqr)
        
        outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
        return outliers.index.tolist()

    def get_payment_data(self, file_paths: List[str]) -> Dict[str, Any]:
        """
        Get payment data from Excel files for analytics purposes.
        
        Args:
            file_paths: List of paths to Excel files
            
        Returns:
            Dictionary containing payment data summary
        """
        self.logger.info("Getting payment data")
        
        try:
            # In a real implementation, this would read from the provided Excel files
            # For demonstration, return some mock data
            return {
                "total_payments": 250000,
                "payment_types": {
                    "overtime": 125000,
                    "standby": 75000,
                    "callout": 50000
                },
                "billable_ratio": 0.65,
                "top_payment_departments": [
                    {"department": "Engineering", "amount": 80000},
                    {"department": "Operations", "amount": 65000},
                    {"department": "Support", "amount": 55000}
                ],
                "monthly_trend": [
                    {"month": "Sep 2024", "amount": 40000},
                    {"month": "Oct 2024", "amount": 42000},
                    {"month": "Nov 2024", "amount": 45000},
                    {"month": "Dec 2024", "amount": 38000},
                    {"month": "Jan 2025", "amount": 43000},
                    {"month": "Feb 2025", "amount": 42000}
                ]
            }
        except Exception as e:
            self.logger.error(f"Error getting payment data: {str(e)}")
            return {
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize processor
    processor = ExcelProcessor()
    
    # Example file path
    file_path = "samples/data/UK_EmpID_Legacy_Country_Payments_Hourly_Rate.xlsx"
    
    if os.path.exists(file_path):
        # Load and process file
        excel_data = processor.load_excel(file_path)
        print(f"Loaded {len(excel_data)} sheets from Excel file")
        
        # Print first few rows of first sheet
        first_sheet = list(excel_data.keys())[0]
        print(f"\nPreview of sheet '{first_sheet}':")
        print(excel_data[first_sheet].head())
    else:
        print(f"Example file not found: {file_path}") 