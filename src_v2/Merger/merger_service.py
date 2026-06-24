"""
Merger Service Layer (Phase 6.3)
=================================

Pure business logic for Excel file merging operations.
Extracted from original tkinter-based Merger.py.

This module handles:
- Excel workbook loading and sheet enumeration
- Column header extraction
- Multi-file merging with flexible column mapping
- Data concatenation and transformation
- Export operations

No UI code - all PyQt5 UI is in separate components.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass


@dataclass
class FileInfo:
    """Information about a loaded Excel file."""
    path: str
    name: str
    sheets: List[str]
    selected_sheet: Optional[str] = None


@dataclass
class ColumnMapping:
    """Column mapping configuration."""
    output_name: str  # Name in output file
    source_columns: List[str]  # Source columns to merge (priority order)
    merge_strategy: str = 'first_non_null'  # 'first_non_null', 'concatenate'


@dataclass
class MergeConfig:
    """Configuration for merge operation."""
    files: List[FileInfo]
    column_mappings: List[ColumnMapping]
    output_path: str
    include_source_info: bool = True  # Add _source_file and _source_sheet columns


@dataclass
class MergeResult:
    """Result of merge operation."""
    success: bool
    output_file: str
    rows_merged: int
    columns_count: int
    errors: List[str]
    warnings: List[str]


class MergerService:
    """
    Service layer for Excel file merging operations.
    
    Handles all business logic for analyzing and merging Excel data.
    Thread-safe and UI-independent.
    """
    
    def __init__(self):
        """Initialize the merger service."""
        self.loaded_files: Dict[str, FileInfo] = {}  # path -> FileInfo
        self.sheet_data: Dict[str, Dict[str, pd.DataFrame]] = {}  # path -> {sheet -> df}
    
    def load_file(self, file_path: str) -> Tuple[bool, str, Optional[FileInfo]]:
        """
        Load an Excel file and enumerate its sheets.
        
        Args:
            file_path: Path to Excel file (.xlsx or .xls)
        
        Returns:
            Tuple[bool, str, Optional[FileInfo]]: (success, message, file_info)
        """
        path = Path(file_path)
        
        # Validate file
        if not path.exists():
            return False, f"File not found: {file_path}", None
        
        if path.suffix.lower() not in ['.xlsx', '.xls']:
            return False, f"Invalid file type: {path.suffix}. Expected .xlsx or .xls", None
        
        try:
            # Load Excel file
            excel_file = pd.ExcelFile(file_path)
            sheet_names = excel_file.sheet_names
            
            # Create FileInfo
            file_info = FileInfo(
                path=file_path,
                name=path.name,
                sheets=sheet_names,
                selected_sheet=sheet_names[0] if sheet_names else None
            )
            
            # Store file info
            self.loaded_files[file_path] = file_info
            
            # Load all sheets into memory
            self.sheet_data[file_path] = {}
            for sheet_name in sheet_names:
                self.sheet_data[file_path][sheet_name] = excel_file.parse(sheet_name)
            
            excel_file.close()
            
            return True, f"Loaded {len(sheet_names)} sheets from {path.name}", file_info
        
        except Exception as e:
            return False, f"Failed to load {path.name}: {str(e)}", None
    
    def remove_file(self, file_path: str) -> bool:
        """
        Remove a loaded file.
        
        Args:
            file_path: Path to file to remove
        
        Returns:
            bool: True if removed, False if not found
        """
        if file_path in self.loaded_files:
            del self.loaded_files[file_path]
            if file_path in self.sheet_data:
                del self.sheet_data[file_path]
            return True
        return False
    
    def get_loaded_files(self) -> List[FileInfo]:
        """
        Get list of loaded files.
        
        Returns:
            List[FileInfo]: List of loaded file information
        """
        return list(self.loaded_files.values())
    
    def set_selected_sheet(self, file_path: str, sheet_name: str) -> bool:
        """
        Set the selected sheet for a file.
        
        Args:
            file_path: Path to file
            sheet_name: Name of sheet to select
        
        Returns:
            bool: True if successful, False if file/sheet not found
        """
        if file_path in self.loaded_files:
            file_info = self.loaded_files[file_path]
            if sheet_name in file_info.sheets:
                file_info.selected_sheet = sheet_name
                return True
        return False
    
    def get_all_columns(self) -> List[str]:
        """
        Get all distinct column names from all selected sheets.
        
        Returns:
            List[str]: List of unique column names (order preserved)
        """
        all_columns = []
        seen = set()
        
        for file_path, file_info in self.loaded_files.items():
            if file_info.selected_sheet:
                df = self.sheet_data[file_path][file_info.selected_sheet]
                for col in df.columns:
                    if col not in seen:
                        all_columns.append(str(col))
                        seen.add(col)
        
        return all_columns
    
    def get_column_headers(self, file_path: str, sheet_name: str) -> List[str]:
        """
        Get column headers from a specific sheet.
        
        Args:
            file_path: Path to file
            sheet_name: Name of sheet
        
        Returns:
            List[str]: List of column names
        """
        if file_path in self.sheet_data and sheet_name in self.sheet_data[file_path]:
            return [str(col) for col in self.sheet_data[file_path][sheet_name].columns]
        return []
    
    def preview_merge(
        self,
        column_mappings: List[ColumnMapping],
        max_rows: int = 100
    ) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        Preview merge result without saving.
        
        Args:
            column_mappings: List of column mapping configurations
            max_rows: Maximum rows to include in preview
        
        Returns:
            Tuple[bool, str, Optional[DataFrame]]: (success, message, preview_df)
        """
        try:
            if not self.loaded_files:
                return False, "No files loaded", None
            
            if not column_mappings:
                return False, "No column mappings configured", None
            
            # Collect all dataframes
            all_dfs = []
            for file_path, file_info in self.loaded_files.items():
                if file_info.selected_sheet:
                    df = self.sheet_data[file_path][file_info.selected_sheet].copy()
                    df['_source_file'] = file_info.name
                    df['_source_sheet'] = file_info.selected_sheet
                    all_dfs.append(df)
            
            if not all_dfs:
                return False, "No sheets selected", None
            
            # Concatenate all data
            merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
            
            # Apply column mappings
            result_df = self._apply_column_mappings(merged_df, column_mappings)
            
            # Limit to preview size
            preview_df = result_df.head(max_rows)
            
            message = f"Preview: {len(preview_df)} of {len(result_df)} rows, {len(result_df.columns)} columns"
            return True, message, preview_df
        
        except Exception as e:
            return False, f"Preview failed: {str(e)}", None
    
    def merge_files(
        self,
        config: MergeConfig,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> MergeResult:
        """
        Merge files according to configuration and save.
        
        Args:
            config: Merge configuration
            progress_callback: Optional callback(message: str) for progress updates
        
        Returns:
            MergeResult: Result of merge operation
        """
        errors = []
        warnings = []
        
        try:
            if progress_callback:
                progress_callback("Collecting data from files...")
            
            # Validate configuration
            if not config.files:
                return MergeResult(
                    success=False,
                    output_file="",
                    rows_merged=0,
                    columns_count=0,
                    errors=["No files configured"],
                    warnings=[]
                )
            
            if not config.column_mappings:
                return MergeResult(
                    success=False,
                    output_file="",
                    rows_merged=0,
                    columns_count=0,
                    errors=["No column mappings configured"],
                    warnings=[]
                )
            
            # Collect all dataframes
            all_dfs = []
            for file_info in config.files:
                if file_info.selected_sheet:
                    if file_info.path in self.sheet_data:
                        df = self.sheet_data[file_info.path][file_info.selected_sheet].copy()
                        
                        # Add source information if requested
                        if config.include_source_info:
                            df['_source_file'] = file_info.name
                            df['_source_sheet'] = file_info.selected_sheet
                        
                        all_dfs.append(df)
                        
                        if progress_callback:
                            progress_callback(f"Loaded {file_info.name} - {file_info.selected_sheet}")
                else:
                    warnings.append(f"No sheet selected for {file_info.name}")
            
            if not all_dfs:
                return MergeResult(
                    success=False,
                    output_file="",
                    rows_merged=0,
                    columns_count=0,
                    errors=["No data to merge"],
                    warnings=warnings
                )
            
            if progress_callback:
                progress_callback("Merging data...")
            
            # Concatenate all data
            merged_df = pd.concat(all_dfs, ignore_index=True, sort=False)
            
            if progress_callback:
                progress_callback("Applying column mappings...")
            
            # Apply column mappings
            result_df = self._apply_column_mappings(merged_df, config.column_mappings)
            
            # Add source columns if requested and not already in mappings
            if config.include_source_info:
                if '_source_file' in merged_df.columns and '_source_file' not in result_df.columns:
                    result_df['_source_file'] = merged_df['_source_file']
                if '_source_sheet' in merged_df.columns and '_source_sheet' not in result_df.columns:
                    result_df['_source_sheet'] = merged_df['_source_sheet']
            
            if progress_callback:
                progress_callback("Saving output file...")
            
            # Save to file
            output_path = Path(config.output_path)
            if output_path.suffix.lower() == '.xlsx':
                result_df.to_excel(config.output_path, index=False, engine='openpyxl')
            elif output_path.suffix.lower() == '.csv':
                result_df.to_csv(config.output_path, index=False)
            else:
                return MergeResult(
                    success=False,
                    output_file="",
                    rows_merged=0,
                    columns_count=0,
                    errors=[f"Unsupported output format: {output_path.suffix}"],
                    warnings=warnings
                )
            
            if progress_callback:
                progress_callback("Merge complete!")
            
            return MergeResult(
                success=True,
                output_file=config.output_path,
                rows_merged=len(result_df),
                columns_count=len(result_df.columns),
                errors=errors,
                warnings=warnings
            )
        
        except Exception as e:
            return MergeResult(
                success=False,
                output_file="",
                rows_merged=0,
                columns_count=0,
                errors=[f"Merge failed: {str(e)}"],
                warnings=warnings
            )
    
    def _apply_column_mappings(
        self,
        df: pd.DataFrame,
        mappings: List[ColumnMapping]
    ) -> pd.DataFrame:
        """
        Apply column mappings to create output dataframe.
        
        Args:
            df: Source dataframe
            mappings: List of column mappings
        
        Returns:
            pd.DataFrame: Transformed dataframe
        """
        result_df = pd.DataFrame()
        
        for mapping in mappings:
            if mapping.merge_strategy == 'first_non_null':
                # Take first non-null value from source columns (priority order)
                result_df[mapping.output_name] = None
                for source_col in mapping.source_columns:
                    if source_col in df.columns:
                        # Fill nulls in result with values from source
                        mask = result_df[mapping.output_name].isna() & df[source_col].notna()
                        result_df.loc[mask, mapping.output_name] = df.loc[mask, source_col]
            
            elif mapping.merge_strategy == 'concatenate':
                # Concatenate all non-null values with separator
                values = []
                for source_col in mapping.source_columns:
                    if source_col in df.columns:
                        values.append(df[source_col].fillna(''))
                
                if values:
                    # Concatenate with space separator, remove extra spaces
                    result_df[mapping.output_name] = values[0]
                    for val in values[1:]:
                        result_df[mapping.output_name] = (
                            result_df[mapping.output_name].astype(str) + ' ' + val.astype(str)
                        )
                    result_df[mapping.output_name] = result_df[mapping.output_name].str.strip()
                else:
                    result_df[mapping.output_name] = None
            
            else:
                # Unknown strategy - just take first column
                if mapping.source_columns and mapping.source_columns[0] in df.columns:
                    result_df[mapping.output_name] = df[mapping.source_columns[0]]
                else:
                    result_df[mapping.output_name] = None
        
        return result_df
    
    def get_merge_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded files and potential merge.
        
        Returns:
            Dict with statistics
        """
        total_files = len(self.loaded_files)
        total_sheets = sum(len(f.sheets) for f in self.loaded_files.values())
        selected_sheets = sum(1 for f in self.loaded_files.values() if f.selected_sheet)
        
        total_rows = 0
        for file_path, file_info in self.loaded_files.items():
            if file_info.selected_sheet:
                df = self.sheet_data[file_path][file_info.selected_sheet]
                total_rows += len(df)
        
        all_columns = self.get_all_columns()
        
        return {
            'total_files': total_files,
            'total_sheets': total_sheets,
            'selected_sheets': selected_sheets,
            'total_rows': total_rows,
            'unique_columns': len(all_columns),
            'all_columns': all_columns
        }
    
    def clear_all(self):
        """Clear all loaded files and data."""
        self.loaded_files.clear()
        self.sheet_data.clear()


# Export public API
__all__ = [
    'MergerService',
    'FileInfo',
    'ColumnMapping',
    'MergeConfig',
    'MergeResult',
]

# Made with Bob