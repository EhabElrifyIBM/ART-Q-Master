from datetime import datetime
import os
import json
import logging
import pandas as pd
import itertools
import pytz
import re
import math
from collections import defaultdict

class FileProcessor:
    def __init__(self):
        self.setup_logging()
        self.file_path = None
        self.output_path = None
        self.settings = None
        self.excluded_answers = None
        self.include_files = None
        self.previous_assignments = {}
        
        # Initialize tracking attributes for summary
        self.bank_sutherland_updated_cases = []
        self.dnd_updated_cases = []
        self.duplicate_company_cases = None
        
        # Define filtering criteria
        self.excluded_work_order_status = [
            'Cancelled',
            'Cancelled by lenovo'
        ]
        
        self.excluded_case_reasons = [
            'Escalation/Complaint'
        ]
        
        self.excluded_closing_codes = [
            'Customer Induced Damage',
            'Cancelled by Customer',
            'Cancelled by Lenovo',
            'Customer Not available',
            'Machine Not Found',
            'Returned but Un-repaired'
        ]
        
        # Define canonical field mapping - the single source of truth for column names
        self.canonical_fields = {
            'Customer Name': [' Contact Name (Contact) (Contact)', 'Contact Name', 'Contact Name (Contact)'],
            'Company Name': ['Company Name'],
            'Country': ['Country/Region (Contact) (Contact)', 'Country'],
            'State/Province': ['State/Province (Case) (Case)', 'State/Province'],
            'Phone Number': ['Contact Mobile Phone', 'Phone Number'],
            'Email': ['Primary Email (Contact) (Contact)', 'Email'],
            'Last Status Change': ['Last Status Change (Workflow Use Only) (Case) (Case)', 'Last Status Change'],
            'Case Status': ['Case Status (Case) (Case)', 'Case Status'],  # Specific to Case
            'Status': ['Status'],  # Independent status field
            'Work Order Status': ['Work Order Status'],  # Specific to Work Order
            'DND (Do Not Disturb)': ['Do Not Disturb (Contact) (Contact)', 'DND (Do Not Disturb)'],
            'Problem Description': ['Problem Description (Case) (Case)', 'Problem Description'],
            'Incoming Channel': ['Incoming Channel (Case) (Case)', 'Incoming Channel'],
            'Case Reason': ['Case Reason (Case) (Case)', 'Case Reason'],
            'Work Order ID': ['Work Order ID'],
            'Product ID (MTM)': ['Product ID (MTM) (Case) (Case)', 'Product ID (MTM)'],
            'Machine Type': ['Machine Type'],
            'Product Description': ['Product Description'],
            'Serial Number': ['Serial Number (Case) (Case)', 'Serial Number'],
            'Survey Preference': ['Survey Preference (Case) (Case)', 'Survey Preference'],
            'Survey Fatigue': ['Survey Fatigue (Case) (Case)', 'Survey Fatigue'],
            'No survey reason': ['No survey reason (Case) (Case)', 'No survey reason'],
            'Program': ['Program (Case) (Case)', 'Program'],
            'Repeat Frequency': ['Repeat Frequency (Case) (Case)', 'Repeat Frequency'],
            'Repeat Repair': ['Repeat Repair'],
            'Closing Code': ['Closing Code']
        }
        
        # Define output columns and raw-to-output mapping
        self.output_columns = [
            'Case Number', 'Work Order Type', 'State/Province', 'Local Time', 'Action 1', 'Action 2', 'Action 3', 'Final Action', 'Assigned To', 'Status',
            'Company Name', 'DND (Do Not Disturb)', 'Email', 'Phone Number', 'Incoming Channel', 'Last Status Change', 'Country', 'Customer Name',
            'Case', 'Problem Description', 'Case Status', 'Case Status Updated', 'Case Reason', 'Work Order ID', 'Work Order Status', 'Order Type', 'Work Order Priority',
            'Product ID (MTM)', 'Machine Type', 'Product Description', 'Serial Number', 'Created On', 'Survey Preference', 'Survey Fatigue', 'No survey reason',
            'Program', 'Repeat Frequency', 'Repeat Repair', 'Closing Code', 'Reported Symptom', 'Completion Date'
        ]

        # Define output columns and raw-to-output mapping (aligned with canonical_fields)
        self.raw_to_output = {
            # Core identifiers and workflow fields
            'Case Number': ['Case Number'],
            'Work Order Type': ['Work Order Type'],
            'Local Time': ['Local Time'],
            'Action 1': ['Action 1'],
            'Action 2': ['Action 2'],
            'Action 3': ['Action 3'],
            'Final Action': ['Final Action'],
            'Assigned To': ['Assigned To'],
            
            # Status fields (kept separate)
            'Status': ['Status'],  # Independent status
            'Case Status': ['Case Status (Case) (Case)', 'Case Status'],  # Case-specific status
            'Work Order Status': ['Work Order Status'],  # Work Order-specific status
            
            # Contact and location information
            'Customer Name': [' Contact Name (Contact) (Contact)', 'Contact Name', 'Contact Name (Contact)'],
            'Company Name': ['Company Name'],
            'Email': ['Primary Email (Contact) (Contact)', 'Email'],
            'Phone Number': ['Contact Mobile Phone', 'Phone Number'],
            'Country': ['Country/Region (Contact) (Contact)', 'Country'],
            'State/Province': ['State/Province (Case) (Case)', 'State/Province'],
            
            # Case details
            'Case': ['Case'],
            'Problem Description': ['Problem Description (Case) (Case)', 'Problem Description'],
            'Case Status Updated': ['Case status Updated (Case) (Case)', 'Case Status Updated'],
            'Case Reason': ['Case Reason (Case) (Case)', 'Case Reason'],
            'Reported Symptom': ['Reported Symptom'],
            'Last Status Change': ['Last Status Change (Workflow Use Only) (Case) (Case)', 'Last Status Change'],
            
            # Work Order details
            'Work Order ID': ['Work Order ID'],
            'Order Type': ['Order Type'],
            'Work Order Priority': ['Work Order Priority'],
            
            # Product information
            'Product ID (MTM)': ['Product ID (MTM) (Case) (Case)', 'Product ID (MTM)'],
            'Machine Type': ['Machine Type'],
            'Product Description': ['Product Description'],
            'Serial Number': ['Serial Number (Case) (Case)', 'Serial Number'],
            
            # Additional metadata
            'Created On': ['Created On'],
            'Incoming Channel': ['Incoming Channel (Case) (Case)', 'Incoming Channel'],
            'DND (Do Not Disturb)': ['Do Not Disturb (Contact) (Contact)', 'DND (Do Not Disturb)'],
            'Survey Preference': ['Survey Preference (Case) (Case)', 'Survey Preference'],
            'Survey Fatigue': ['Survey Fatigue (Case) (Case)', 'Survey Fatigue'],
            'No survey reason': ['No survey reason (Case) (Case)', 'No survey reason'],
            'Program': ['Program (Case) (Case)', 'Program'],
            'Repeat Frequency': ['Repeat Frequency (Case) (Case)', 'Repeat Frequency'],
            'Repeat Repair': ['Repeat Repair'],
            'Closing Code': ['Closing Code'],
            'Completion Date': ['Completion Date']
        }
        # Default canonical column name mapping used across the processor.
        # This provides a central place for code that references self.columns[...] to
        # look up the expected column name in incoming dataframes. Values here are
        # defaults and may be overridden later if different variants are detected.
        self.columns = {
            # Core identifiers and workflow
            'case_number': 'Case Number',
            'local_time': 'Local Time',
            'action_1': 'Action 1',
            'action_2': 'Action 2',
            'action_3': 'Action 3',
            'final_action': 'Final Action',
            'assigned_to': 'Assigned To',
            
            # Status fields (kept separate)
            'status': 'Status',  # Independent status
            'case_status': 'Case Status (Case) (Case)',  # Case-specific status
            'wo_status': 'Work Order Status',  # Work Order-specific status
            
            # Contact and location information
            'customer_name': 'Contact Name (Contact) (Contact)',
            'company': 'Company Name',
            'email': 'Primary Email (Contact) (Contact)',
            'phone': 'Contact Mobile Phone',
            'country': 'Country/Region (Contact) (Contact)',
            'state': 'State/Province (Case) (Case)',
            
            # Case details
            'case': 'Case',
            'problem_description': 'Problem Description (Case) (Case)',
            'case_status_updated': 'Case status Updated (Case) (Case)',
            'case_reason': 'Case Reason (Case) (Case)',
            'last_status_change': 'Last Status Change (Workflow Use Only) (Case) (Case)',
            'incoming_channel': 'Incoming Channel (Case) (Case)',
            
            # Work Order details
            'wo_id': 'Work Order ID',
            'wo_type': 'Work Order Type',
            'order_type': 'Order Type',
            'wo_priority': 'Work Order Priority',
            
            # Product information
            'product_id': 'Product ID (MTM) (Case) (Case)',
            'machine_type': 'Machine Type',
            'product_desc': 'Product Description',
            'serial': 'Serial Number (Case) (Case)',
            
            # Additional metadata
            'created_on': 'Created On',
            'dnd': 'DND (Do Not Disturb)',
            'survey_pref': 'Survey Preference (Case) (Case)',
            'survey_fatigue': 'Survey Fatigue (Case) (Case)',
            'no_survey_reason': 'No survey reason (Case) (Case)',
            'program': 'Program (Case) (Case)',
            'repeat_freq': 'Repeat Frequency (Case) (Case)',
            'repeat_repair': 'Repeat Repair',
            'closing_code': 'Closing Code',
            'reported_symptom': 'Reported Symptom',
            'completion_date': 'Completion Date'
        }
        
    def setup_logging(self, log_callback=None):
        """Set up logging configuration with optional GUI callback"""
        class GUIHandler(logging.Handler):
            def __init__(self, callback):
                super().__init__()
                self.callback = callback

            def emit(self, record):
                if self.callback:
                    msg = self.format(record)
                    self.callback(msg)

        # Set up basic logging format
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # File handler with detailed logging using UTF-8 encoding 
        file_handler = logging.FileHandler('file_processing.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        
        # Console handler — do not reassign sys.stdout.buffer (can fail in some environments)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(logging.INFO)
        
        # GUI handler (if callback provided) - only important messages
        handlers = [file_handler, console_handler]
        if log_callback is not None:
            gui_handler = GUIHandler(log_callback)
            gui_handler.setFormatter(formatter)
            gui_handler.setLevel(logging.INFO)  # Only INFO and above to GUI
            handlers.append(gui_handler)
        
        # Configure logger
        logging.basicConfig(
            level=logging.DEBUG,  # Allow all levels for file logging
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True
        )
        
        self.logger = logging.getLogger(__name__)
        
        # Create a separate logger for dropped cases tracking
        self.dropped_cases_logger = logging.getLogger('dropped_cases')
        self.dropped_cases_logger.setLevel(logging.INFO)
        
        # Create dropped cases log file with UTF-8 encoding
        dropped_handler = logging.FileHandler('dropped_cases.log', encoding='utf-8')
        dropped_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.dropped_cases_logger.addHandler(dropped_handler)
        self.dropped_cases_logger.propagate = False  # Don't propagate to root logger
        
    def get_raw_col(self, df, output_col):
        """Return the best matching raw column name for a given output column.
        Uses the mapping stored in self.raw_to_output. Performs matches in order:
        1. Exact case-insensitive match
        2. Normalized string match (removes spaces, special chars)
        3. Partial substring match
        4. Fuzzy match on column name components
        """
        try:
            if output_col not in getattr(self, 'raw_to_output', {}):
                self.logger.warning(f"No mapping defined for output column: {output_col}")
                return None
                
            def normalize_colname(col):
                """Normalize column name for comparison"""
                return re.sub(r'[^a-z0-9]', '', str(col).lower())
            
            candidates = self.raw_to_output[output_col]
            self.logger.debug(f"\nLooking for raw column matching {output_col}")
            self.logger.debug(f"Candidates: {candidates}")
            
            # 1. Try exact case-insensitive match
            for raw_candidate in candidates:
                for col in df.columns:
                    try:
                        if col.strip().lower() == raw_candidate.strip().lower():
                            self.logger.debug(f"Found exact match: {col}")
                            return col
                    except Exception:
                        continue
            
            # 2. Try normalized string match
            for raw_candidate in candidates:
                norm_candidate = normalize_colname(raw_candidate)
                for col in df.columns:
                    try:
                        if normalize_colname(col) == norm_candidate:
                            self.logger.debug(f"Found normalized match: {col}")
                            return col
                    except Exception:
                        continue
            
            # 3. Try partial match
            for raw_candidate in candidates:
                norm_candidate = normalize_colname(raw_candidate)
                for col in df.columns:
                    try:
                        if norm_candidate in normalize_colname(col):
                            self.logger.debug(f"Found partial match: {col}")
                            return col
                    except Exception:
                        continue
            
            # No match found
            self.logger.warning(f"No matching raw column found for {output_col}")
            self.logger.debug("Available columns:")
            for col in df.columns:
                self.logger.debug(f"  {col}")
                
            return None
            
        except Exception as e:
            self.logger.error(f"Error in get_raw_col for {output_col}: {str(e)}")
            return None
        
    def log_dropped_case(self, case_number, reason, details=None, status=None):
        """Log a dropped case with its reason and details"""
        try:
            log_message = f"DROPPED CASE: {case_number} - Reason: {reason}"
            if status:
                log_message += f" - Status: {status}"
            if details:
                log_message += f" - Details: {details}"
            
            self.dropped_cases_logger.info(log_message)
            self.logger.debug(log_message)  # Also log to main log file for debugging
        except Exception as e:
            self.logger.error(f"Error logging dropped case: {str(e)}")
    
    def log_case_status_change(self, case_number, old_status, new_status, reason=None):
        """Log when a case status changes (e.g., to fixed, not fixed, DND)"""
        try:
            log_message = f"STATUS CHANGE: {case_number} - {old_status} -> {new_status}"
            if reason:
                log_message += f" - Reason: {reason}"
            
            self.dropped_cases_logger.info(log_message)
            self.logger.info(log_message)  # Show status changes in main log
        except Exception as e:
            self.logger.error(f"Error logging status change: {str(e)}")
    
    def log_filtering_summary(self, filter_name, initial_count, final_count, dropped_reasons):
        """Log a summary of filtering results with dropped case details"""
        try:
            dropped_count = initial_count - final_count
            self.logger.info(f"\n{filter_name} Filter Summary:")
            self.logger.info(f"  Initial count: {initial_count}")
            self.logger.info(f"  Final count: {final_count}")
            self.logger.info(f"  Dropped count: {dropped_count}")
            
            if dropped_reasons:
                self.logger.info(f"  Dropped reasons:")
                for reason, cases in dropped_reasons.items():
                    self.logger.info(f"    {reason}: {len(cases)} cases")
                    # Log individual dropped cases to dropped cases log
                    for case in cases:
                        self.log_dropped_case(case, reason, filter_name)
            
            # Also log to dropped cases log
            self.dropped_cases_logger.info(f"FILTER SUMMARY: {filter_name} - Dropped {dropped_count} out of {initial_count} cases")
            
        except Exception as e:
            self.logger.error(f"Error logging filtering summary: {str(e)}")
    
    def log_issue_not_fixed_case(self, case_number, source, details=None):
        """Log when a case is added to the Issue Not Fixed sheet"""
        try:
            log_message = f"ISSUE NOT FIXED CASE: {case_number} - Source: {source}"
            if details:
                log_message += f" - Details: {details}"
            
            self.dropped_cases_logger.info(log_message)
            self.logger.info(log_message)  # Show in main log as well
        except Exception as e:
            self.logger.error(f"Error logging issue not fixed case: {str(e)}")
    
    def log_issue_not_fixed_summary(self, total_cases, sms_cases, email_cases, new_cases):
        """Log a summary of Issue Not Fixed cases processing"""
        try:
            self.logger.info(f"\n=== Issue Not Fixed Processing Summary ===")
            self.logger.info(f"Total cases in Issue Not Fixed sheet: {total_cases}")
            self.logger.info(f"Cases from SMS processing: {sms_cases}")
            self.logger.info(f"Cases from Email processing: {email_cases}")
            self.logger.info(f"New cases added: {new_cases}")
            
            # Also log to dropped cases log
            self.dropped_cases_logger.info(f"ISSUE NOT FIXED SUMMARY: Total {total_cases}, SMS {sms_cases}, Email {email_cases}, New {new_cases}")
            
        except Exception as e:
            self.logger.error(f"Error logging issue not fixed summary: {str(e)}")

    def process_raw_file(self, file_path):
        """Process the raw input file"""
        self.logger.info(f"Processing file: {file_path}")
        # Implementation will be added based on specific requirements
        
    def update_case_status(self, case_id, status):
        """Update status for a specific case"""
        self.logger.info(f"Updating status for case {case_id} to {status}")
        # Implementation will be added based on specific requirements
        
    def assign_cases_to_handlers(self, cases, handlers):
        """Assign cases to handlers based on rules"""
        self.logger.info(f"Assigning {len(cases)} cases to {len(handlers)} handlers")
        # Implementation will be added based on specific requirements

    def validate_files(self, raw_file, prev_file=None, sms_file=None):
        """Validate input files"""
        try:
            # Check if raw file exists
            if not os.path.exists(raw_file):
                return False, "Raw file does not exist"
            
            # Check previous file if provided
            if prev_file and not os.path.exists(prev_file):
                return False, "Previous file does not exist"
            
            # Check SMS file if provided
            if sms_file and not os.path.exists(sms_file):
                return False, "SMS file does not exist"
            
            return True, "All files validated successfully"
        except Exception as e:
            self.logger.error(f"File validation error: {str(e)}")
            return False, f"Error during file validation: {str(e)}"

    def clean_string_series(self, series):
        """Clean string series by removing extra whitespace and converting to lowercase"""
        # First convert to string, handling NaN values
        series = series.fillna('').astype(str)
        return series.str.strip().str.lower()

    def filter_case(self, df):
        """Filter cases based on CID and DMR rules"""
        try:
            original_len = len(df)
            
            self.logger.info("\nStarting CID/DMR filtering:")
            self.logger.info(f"Initial count: {original_len}")
            
            # Debug: Print sample of cases before filtering
            self.logger.debug("\nSample of cases before filtering:")
            case_col_name = self.get_raw_col(df, 'Case')
            sample_cases = df[case_col_name].head() if case_col_name else []
            for case in sample_cases:
                self.logger.debug(f"Case value: {case}")
            
            # Create a mask for cases to keep
            case_col = df[case_col_name] if case_col_name else pd.Series(dtype=str)
            
            # 1. Find "not cid" cases (these should be kept)
            not_cid_mask = case_col.str.contains(r'not\s*[\[\(]?cid[\]\)]?', case=False, regex=True, na=False)
            not_cid_count = not_cid_mask.sum()
            self.logger.info(f"\nFound {not_cid_count} cases with 'not cid'")
            
            # 2. Find CID cases
            cid_mask = case_col.str.contains(r'[\[\(]?cid[\]\)]?', case=False, regex=True, na=False)
            cid_count = cid_mask.sum()
            self.logger.info(f"Found {cid_count} cases with 'cid'")
            
            # 3. Find DMR cases
            dmr_mask = case_col.str.contains(r'[\[\(]?dmr[\]\)]?', case=False, regex=True, na=False)
            dmr_count = dmr_mask.sum()
            self.logger.info(f"Found {dmr_count} cases with 'dmr'")
            
            # Create the final mask
            # Keep rows that either:
            # 1. Contain "not cid", OR
            # 2. Don't contain either "cid" or "dmr"
            mask = not_cid_mask | (~cid_mask & ~dmr_mask)
            
            # Store removed cases for analysis
            removed_cases = df[~mask].copy()
            
            # Apply the filter
            df_filtered = df[mask].copy()
            
            # Log detailed results
            self.logger.info("\nCID/DMR filtering results:")
            self.logger.info(f"Original count: {original_len}")
            self.logger.info(f"After filtering: {len(df_filtered)}")
            self.logger.info(f"Removed {len(removed_cases)} cases")
            
            # Log sample of removed cases with their full case text
            if not removed_cases.empty:
                self.logger.debug("\nSample of removed cases:")
                sample_size = min(10, len(removed_cases))
                for idx, row in removed_cases.head(sample_size).iterrows():
                    case_text = row[case_col_name] if case_col_name in row else ''
                    case_num_col = self.get_raw_col(df, 'Case Number')
                    case_num = row[case_num_col] if case_num_col in row else ''
                    self.logger.debug(f"Case Number: {case_num}")
                    self.logger.debug(f"Case Text: {case_text}")
                    self.logger.debug("---")
            
            # Use new logging system for dropped cases
            case_num_col = self.get_raw_col(df, 'Case Number')
            dropped_reasons = {
                'CID Case': removed_cases[cid_mask & ~not_cid_mask][case_num_col].tolist() if case_num_col else [],
                'DMR Case': removed_cases[dmr_mask][case_num_col].tolist() if case_num_col else []
            }
            
            self.log_filtering_summary("CID/DMR", original_len, len(df_filtered), dropped_reasons)
            
            return df_filtered, removed_cases
            
        except Exception as e:
            self.logger.error(f"Error in filter_case: {str(e)}")
            self.logger.error("Stack trace:", exc_info=True)
            raise

    def validate_columns(self, df):
        """Validate that all required columns are present in the dataframe"""
        missing_columns = []
        found_columns = []
        
        self.logger.info("\n=== Column Validation Analysis ===")
        self.logger.info("\nAvailable columns in file:")
        for col in df.columns:
            # Check column contents
            null_count = df[col].isnull().sum()
            empty_count = (df[col].fillna('').astype(str).str.strip() == '').sum()
            total_rows = len(df)
            self.logger.info(f"'{col}': {null_count} null, {empty_count} empty out of {total_rows} total rows")
            
            # Sample non-empty values if they exist
            non_empty_values = df[df[col].notna() & (df[col].astype(str).str.strip() != '')][col].head(3).tolist()
            if non_empty_values:
                self.logger.info(f"  Sample values: {non_empty_values}")
        
        self.logger.info("\nExpected output columns:")
        for out_col in self.output_columns:
            self.logger.info(f"'{out_col}'")
            # Track potential sources for this column
            potential_sources = self.raw_to_output.get(out_col, [])
            self.logger.info(f"  Potential source columns: {potential_sources}")
            
            # Check if any potential sources exist in df
            found_sources = [src for src in potential_sources if src in df.columns]
            if found_sources:
                self.logger.info(f"  Found these source columns: {found_sources}")
                for src in found_sources:
                    null_count = df[src].isnull().sum()
                    empty_count = (df[src].fillna('').astype(str).str.strip() == '').sum()
                    self.logger.info(f"    '{src}': {null_count} null, {empty_count} empty values")
            else:
                self.logger.warning(f"  No source columns found for {out_col}")
        
        # Column mapping analysis
        self.logger.info("\n=== Column Mapping Analysis ===")
        for out_col in self.output_columns:
            raw_col = self.get_raw_col(df, out_col)
            if raw_col:
                found_columns.append(f"{out_col}: Found as '{raw_col}'")
                # Analyze content of found column
                null_count = df[raw_col].isnull().sum()
                empty_count = (df[raw_col].fillna('').astype(str).str.strip() == '').sum()
                total_rows = len(df)
                self.logger.info(f"\nAnalysis for {out_col} -> {raw_col}:")
                self.logger.info(f"  Total rows: {total_rows}")
                self.logger.info(f"  Null values: {null_count} ({(null_count/total_rows)*100:.1f}%)")
                self.logger.info(f"  Empty strings: {empty_count} ({(empty_count/total_rows)*100:.1f}%)")
                
                # Sample values
                sample = df[df[raw_col].notna() & (df[raw_col].astype(str).str.strip() != '')][raw_col].head()
                if not sample.empty:
                    self.logger.info(f"  Sample values: {sample.tolist()}")
            else:
                missing_columns.append(f"{out_col}")
                self.logger.error(f"\nNo mapping found for {out_col}")
                self.logger.error(f"Expected sources: {self.raw_to_output.get(out_col, [])}")
        
        if missing_columns:
            self.logger.error("\n=== Missing Columns Analysis ===")
            for col in missing_columns:
                self.logger.error(f"Missing: {col}")
                expected_sources = self.raw_to_output.get(col, [])
                self.logger.error(f"  Expected source columns: {expected_sources}")
                # Check if any of these sources exist with different casing/spacing
                for src in expected_sources:
                    close_matches = [c for c in df.columns if src.lower() in c.lower()]
                    if close_matches:
                        self.logger.error(f"  Similar columns found: {close_matches}")
            
            self.logger.info("\n=== Found Columns ===")
            for col in found_columns:
                self.logger.info(f"Found: {col}")
        
        return len(missing_columns) == 0

    def ensure_output_columns(self, df, prev_df=None):
        """Ensure that every expected output column exists in `df`.
        Maps fields correctly from raw file to standardized output columns,
        particularly for Email, Phone Number, Last Status Change, Country, State/Province, Case Status.
        Uses canonical_fields mapping to find the correct source columns.
        """
        created = []
        try:
            self.logger.info("Ensuring output columns with proper mapping...")

            # IMPORTANT: Convert Completion Date Timestamps to strings early
            if 'Completion Date' in df.columns:
                self.logger.info("Converting Completion Date Timestamps to strings...")
                df['Completion Date'] = df['Completion Date'].astype(str)
                self.logger.info("Completion Date converted to string format")
                
                # DIAGNOSTIC: Check if conversion actually worked
                non_empty_after_early_conversion = (df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC ensure_output_columns: After early conversion - {non_empty_after_early_conversion}/{len(df)} non-empty")
                if non_empty_after_early_conversion > 0:
                    samples_early = df[df['Completion Date'].fillna('').astype(str).str.strip() != '']['Completion Date'].head(3).tolist()
                    self.logger.info(f"DIAGNOSTIC ensure_output_columns: Sample values after early conversion: {samples_early}")
                else:
                    all_samples_early = df['Completion Date'].head(3).tolist()
                    self.logger.info(f"DIAGNOSTIC ensure_output_columns: ALL values after early conversion: {all_samples_early}")

            # Ensure df has a normalized Case Number column for lookups
            if 'Case Number' not in df.columns:
                for col in df.columns:
                    if 'case' in str(col).lower() and 'number' in str(col).lower():
                        df['Case Number'] = df[col]
                        self.logger.info(f"Found Case Number column: {col}")
                        break

            # Define critical field mappings - strict priority order
            critical_fields = {
                'Email': [
                    'Primary Email (Contact) (Contact)',  # First priority
                    'Email Address',  # Second priority
                    'Email',  # Third priority
                    'Contact Email'  # Fourth priority
                ],
                'Phone Number': [
                    'Contact Mobile Phone',  # First priority
                    'Phone Number',  # Second priority
                    'Mobile Phone',  # Third priority
                    'Contact Phone'  # Fourth priority
                ],
                'Last Status Change': [
                    'Last Status Change (Workflow Use Only) (Case) (Case)',  # First priority
                    'Last Status Change (Case) (Case)',  # Second priority
                    'Last Status Change'  # Third priority
                ],
                'Country': [
                    'Country/Region (Contact) (Contact)',  # First priority
                    'Country/Region',  # Second priority
                    'Country (Contact)',  # Third priority
                    'Country'  # Fourth priority
                ],
                'State/Province': [
                    'State/Province (Case) (Case)',  # First priority
                    'State/Province (Contact) (Contact)',  # Second priority
                    'State/Province (Contact)',  # Third priority
                    'State/Province'  # Fourth priority
                ],
                'Case Status': [
                    'Case Status (Case) (Case)',  # First priority
                    'Case Status (Case)',  # Second priority
                    'Case Status'  # Third priority
                ],
                'Customer Name': [
                    ' Contact Name (Contact) (Contact)',  # First priority
                    'Contact Name',  # Second priority
                    'Contact Name (Contact) (Contact)',  # Third priority
                    'Customer Name'  # Fourth priority
                ],
                'Completion Date': [
                    'Completion Date'  # Direct mapping from raw file
                ]
            }

                # Process each output column
            for out_col in self.output_columns:
                # Log the current column being processed
                self.logger.info(f"\nProcessing output column: {out_col}")
                
                # Check current state of column
                if out_col in df.columns:
                    null_count = df[out_col].isnull().sum()
                    empty_count = (df[out_col].fillna('').astype(str).str.strip() == '').sum()
                    self.logger.info(f"Column '{out_col}' exists: {null_count} null values, {empty_count} empty strings")
                else:
                    self.logger.info(f"Column '{out_col}' does not exist yet")
                
                # Check if this is a critical field needing special handling
                # Critical fields should ALWAYS be processed to fill in missing values
                if out_col in critical_fields:
                    source_cols = critical_fields[out_col]
                    found_data = False
                    
                    # Initialize the output column if it doesn't exist
                    if out_col not in df.columns:
                        df[out_col] = ''
                        created.append(out_col)
                        self.logger.info(f"Created column {out_col}")
                    
                    # Try each source column in strict priority order
                    for source_col in source_cols:
                        self.logger.info(f"\nTrying source column '{source_col}' for {out_col}")
                        
                        # Skip if source and target are the same column - column already has its data
                        if source_col == out_col:
                            self.logger.info(f"Source and target are the same column - skipping update (data already present)")
                            found_data = True
                            continue
                        
                        if source_col in df.columns:
                            # Log the source column's current state
                            source_null = df[source_col].isnull().sum()
                            source_empty = (df[source_col].fillna('').astype(str).str.strip() == '').sum()
                            self.logger.info(f"Source column exists with {source_null} null values, {source_empty} empty strings")
                            
                            # Only copy to empty cells or cells that need updating
                            empty_mask = (df[out_col].fillna('').astype(str).str.strip() == '')
                            empty_count = empty_mask.sum()
                            self.logger.info(f"Target column has {empty_count} empty cells to potentially fill")
                            
                            source_values = df[source_col].fillna('').astype(str).str.strip()
                            valid_source_mask = (source_values != '')
                            valid_count = valid_source_mask.sum()
                            self.logger.info(f"Source column has {valid_count} non-empty values available")
                            
                            # Update only where we have valid source values and target is empty
                            update_mask = empty_mask & valid_source_mask
                            updates_possible = update_mask.sum()
                            self.logger.info(f"Found {updates_possible} cells that can be updated")
                            
                            if update_mask.any():
                                # For Completion Date, convert Timestamp to string if needed
                                if out_col == 'Completion Date':
                                    # Convert Timestamp objects to strings in the proper format
                                    df.loc[update_mask, out_col] = df.loc[update_mask, source_col].astype(str)
                                    self.logger.info(f"Special handling: Converted Timestamps to strings for Completion Date")
                                else:
                                    df.loc[update_mask, out_col] = df.loc[update_mask, source_col]
                                found_data = True
                                self.logger.info(f"Successfully mapped {source_col} -> {out_col} ({update_mask.sum()} rows)")
                                
                                # Debug logging for ALL updated values
                                updates = df[update_mask]
                                self.logger.info("\nDetailed update log:")
                                for idx, row in updates.iterrows():
                                    self.logger.info(f"Updated {out_col} for case {row['Case Number']}: '{row[source_col]}' -> '{df.loc[idx, out_col]}'")
                                
                                # Log sample of cells that couldn't be updated
                                still_empty = df[empty_mask & ~update_mask]
                                if not still_empty.empty:
                                    self.logger.warning(f"\nSample of cases where update failed from this source:")
                                    for _, row in still_empty.head().iterrows():
                                        self.logger.warning(f"Case {row['Case Number']}: Source value: '{row.get(source_col, 'N/A')}', Current target value: '{row.get(out_col, 'N/A')}'")
                            else:
                                self.logger.warning(f"No updates possible from {source_col} to {out_col}")
                    
                    # Double-check if we still have empty values after trying all sources
                    still_empty = (df[out_col].fillna('').astype(str).str.strip() == '').sum()
                    if still_empty > 0:
                        self.logger.warning(f"{still_empty} rows still missing {out_col} after checking all source columns")
                        # Log some examples of cases with missing data
                        empty_examples = df[df[out_col].fillna('').astype(str).str.strip() == '']['Case Number'].head(5).tolist()
                        self.logger.warning(f"Example cases missing {out_col}: {empty_examples}")
                    else:
                        self.logger.info(f"Successfully populated all rows for {out_col}")
                else:
                    # Standard column handling - skip if already exists and has data
                    if out_col in df.columns and not df[out_col].isnull().all():
                        # Check if column has any meaningful data
                        has_data = (df[out_col].fillna('').astype(str).str.strip() != '').any()
                        if has_data:
                            self.logger.info(f"Column '{out_col}' already has data - skipping")
                            continue
                    
                    raw_col = self.get_raw_col(df, out_col)
                    if raw_col and raw_col in df.columns:
                        # Check data in raw column before mapping
                        non_empty = df[raw_col].fillna('').astype(str).str.strip() != ''
                        if non_empty.any():
                            df[out_col] = df[raw_col]
                            created.append(out_col)
                            self.logger.info(f"Standard mapping: {raw_col} -> {out_col} ({non_empty.sum()} non-empty values)")
                            # Log sample of mapped values
                            sample = df[non_empty][raw_col].head(3)
                            self.logger.info(f"Sample values mapped: {sample.tolist()}")
                        else:
                            self.logger.warning(f"Raw column {raw_col} found but contains no non-empty values")
                    elif out_col not in df.columns:
                        df[out_col] = ''
                        created.append(out_col)
                        self.logger.info(f"Created empty column: {out_col}")

            # Fill in from previous file for existing cases
            if prev_df is not None and not prev_df.empty and 'Case Number' in prev_df.columns:
                self.logger.info("Checking previous file for existing cases...")
                
                # First normalize case numbers in previous file
                prev_df['Case Number'] = prev_df['Case Number'].apply(self.normalize_case_number)
                prev_case_nums = set(prev_df['Case Number'].dropna())
                self.logger.info(f"Found {len(prev_case_nums)} unique case numbers in previous file")
                
                # Track which cases and columns are populated from previous file
                prev_file_updates = defaultdict(list)
                raw_file_values = defaultdict(list)
                
                for out_col in self.output_columns:
                    # SKIP Completion Date - it should NOT be overwritten by previous file data
                    # It was just properly populated from the raw file
                    if out_col == 'Completion Date':
                        self.logger.info(f"Skipping {out_col} - preserving values from raw file")
                        continue
                    
                    if out_col in prev_df.columns:
                        try:
                            # Log column state before population
                            self.logger.info(f"\nPopulating {out_col} from previous file:")
                            self.logger.info("Current state:")
                            non_empty_current = (df[out_col].fillna('').astype(str).str.strip() != '').sum() if out_col in df.columns else 0
                            self.logger.info(f"  Non-empty values in current data: {non_empty_current}")
                            
                            updates = 0
                            for idx, row in df.iterrows():
                                case_num = self.normalize_case_number(row['Case Number'])
                                if case_num in prev_case_nums:
                                    # Store original value before update
                                    orig_val = str(row.get(out_col, '')).strip()
                                    if orig_val:
                                        raw_file_values[case_num].append(f"{out_col}={orig_val}")
                                        
                                    # Get value from previous file
                                    prev_val = prev_df[prev_df['Case Number'] == case_num][out_col].iloc[0]
                                    if pd.notna(prev_val) and str(prev_val).strip():
                                        df.at[idx, out_col] = prev_val
                                        prev_file_updates[case_num].append(f"{out_col}={prev_val}")
                                        updates += 1
                            
                            self.logger.info(f"  Updated {updates} cases from previous file")
                        except Exception as e:
                            self.logger.warning(f"Error copying {out_col} from previous data: {str(e)}")

                # Verify and fix critical fields for new cases
            if prev_df is not None:
                self.logger.info("\n=== Beginning New Cases Verification ===")
                
                # Normalize case numbers for comparison
                df['_normalized_case'] = df['Case Number'].apply(self.normalize_case_number)
                prev_df['_normalized_case'] = prev_df['Case Number'].apply(self.normalize_case_number)
                
                # Identify new cases
                current_cases = set(df['_normalized_case'])
                previous_cases = set(prev_df['_normalized_case'])
                new_case_nums = current_cases - previous_cases
                
                self.logger.info(f"Total cases in current file: {len(current_cases)}")
                self.logger.info(f"Total cases in previous file: {len(previous_cases)}")
                self.logger.info(f"Number of new cases identified: {len(new_case_nums)}")
                
                # Log the first few new cases for verification
                sample_new_cases = list(new_case_nums)[:5]
                self.logger.info(f"Sample of new cases: {sample_new_cases}")
                
                if new_case_nums:
                    self.logger.info(f"\n=== Verifying Critical Fields for {len(new_case_nums)} New Cases ===")
                    
                    for field, source_cols in critical_fields.items():
                        if field not in df.columns:
                            df[field] = ''  # Ensure the column exists
                            
                        # Check which new cases are missing this field
                        new_cases_mask = df['_normalized_case'].isin(new_case_nums)
                        empty_mask = (df[field].fillna('').astype(str).str.strip() == '')
                        missing_mask = new_cases_mask & empty_mask
                        
                        if missing_mask.any():
                            missing_count = missing_mask.sum()
                            self.logger.warning(f"\nFound {missing_count} new cases missing {field}")
                            
                            # Try to fill missing values from each source column
                            for source_col in source_cols:
                                if source_col in df.columns:
                                    source_values = df[source_col].fillna('').astype(str).str.strip()
                                    valid_source = (source_values != '')
                                    update_mask = missing_mask & valid_source
                                    
                                    if update_mask.any():
                                        df.loc[update_mask, field] = df.loc[update_mask, source_col]
                                        self.logger.info(f"Filled {update_mask.sum()} missing {field} values from {source_col}")
                                        
                                        # Update the missing mask
                                        missing_mask = new_cases_mask & (df[field].fillna('').astype(str).str.strip() == '')
                                        
                                        if not missing_mask.any():
                                            self.logger.info(f"Successfully filled all missing {field} values")
                                            break
                            
                            # Final check for any remaining missing values
                            still_missing = missing_mask.sum()
                            if still_missing > 0:
                                missing_cases = df[missing_mask]['Case Number'].tolist()[:5]
                                self.logger.error(f"CRITICAL: Still missing {field} for {still_missing} new cases")
                                self.logger.error(f"Example cases missing {field}: {missing_cases}")
                        else:
                            self.logger.info(f"All new cases have {field} populated")
                    
                    # Clean up temporary column
                    df = df.drop(columns=['_normalized_case'])
                    if '_normalized_case' in prev_df.columns:
                        prev_df = prev_df.drop(columns=['_normalized_case'])

            return created

        except Exception as e:
            self.logger.error(f"Error ensuring output columns: {str(e)}")
            return created
        

    def _normalize_id_columns(self, df):
        for col in df.columns:
            if 'case number' in col.lower():
                df[col] = df[col].apply(self.normalize_case_number)
                df[col] = pd.to_numeric(df[col], errors='coerce').astype('Int64')
            elif 'phone' in col.lower():
                def norm_phone(val):
                    if pd.isna(val):
                        return ''
                    if isinstance(val, float) and val.is_integer():
                        return str(int(val))
                    return str(val).strip()
                df[col] = df[col].apply(norm_phone)
        return df

    def process_files(self, raw_file, prev_file, sms_file, email_file, output_file, selected_handlers):
        """Process the input files"""
        try:
            self.logger.info("\n=== Starting file processing ===")
            self.logger.info(f"Selected handlers: {selected_handlers}")
            
            # Read the raw file
            self.logger.info(f"\nReading raw file: {raw_file}")
            df = pd.read_excel(raw_file)
            
            # Log file loaded (removed verbose per-column sample logging)
            self.logger.info(f"Loaded {len(df)} records with {len(df.columns)} columns")
            
            # Clean and normalize all string columns
            string_cols = df.select_dtypes(include=['object']).columns
            for col in string_cols:
                df[col] = df[col].fillna('').astype(str).str.strip()
                
            # Normalize ID columns
            df = self._normalize_id_columns(df)
            initial_count = len(df)
            
            self.logger.info(f"Initial record count after normalization: {initial_count}")
            
            # Load previous file if it exists
            prev_df = None
            if prev_file and os.path.exists(prev_file):
                self.logger.info(f"\nLoading previous file: {prev_file}")
                try:
                    prev_df = self.load_previous_file(prev_file)
                    self.logger.info(f"Previous file loaded successfully with {len(prev_df)} records")
                except Exception as e:
                    self.logger.error(f"Error loading previous file: {str(e)}")
                    self.logger.warning("Continuing without previous file data")
                    prev_df = None
            
            # Validate columns before processing
            valid = self.validate_columns(df)
            if not valid:
                # Instead of failing immediately, attempt to standardize column names
                self.logger.info("Standardizing column names for consistency...")
                created_cols = self.ensure_output_columns(df, prev_df)
                self.logger.info(f"Standardized column names to: {created_cols}")
                # Re-run validation
                if not self.validate_columns(df):
                    raise ValueError("Missing required columns in input file after attempted standardization")
            
            # Clean and normalize the relevant columns
            self.logger.info("\nCleaning and normalizing columns...")
            
            # CRITICAL: Save Completion Date before filtering, as it might be lost during operations
            completion_date_backup = None
            if 'Completion Date' in df.columns:
                completion_date_backup = df['Completion Date'].copy()
                self.logger.info(f"DIAGNOSTIC: Saved Completion Date backup with {(completion_date_backup.fillna('').astype(str).str.strip() != '').sum()} non-empty values")
            
            for out_col in ['Work Order Status', 'Case Reason', 'Closing Code', 'Case', 'Case Number']:
                raw_col = self.get_raw_col(df, out_col)
                if raw_col:
                    df[raw_col] = self.clean_string_series(df[raw_col])
            
            # Apply filters with detailed tracking
            self.logger.info("\n=== Applying Filters ===")
            
            # Track all dropped cases for comprehensive logging
            all_dropped_cases = []
            dropped_cases_details = {}
            
            # 1. Work Order Status filter
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            excluded_wo_status = [x.strip().lower() for x in self.excluded_work_order_status]
            wo_status_col = self.get_raw_col(df, 'Work Order Status')
            mask_wo = ~df[wo_status_col].isin(excluded_wo_status) if wo_status_col else pd.Series([True]*len(df))
            removed_wo = df[~mask_wo]
            if not isinstance(removed_wo, pd.DataFrame):
                removed_wo = pd.DataFrame(removed_wo)
            
            # DIAGNOSTIC: Check Completion Date before Work Order Status filter
            if 'Completion Date' in df.columns:
                completion_date_non_empty = (df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: Before Work Order Status filter - Completion Date has {completion_date_non_empty}/{len(df)} non-empty")
            
            df = df[mask_wo]
            
            # DIAGNOSTIC: Check Completion Date after Work Order Status filter
            if 'Completion Date' in df.columns:
                completion_date_non_empty = (df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: After Work Order Status filter - Completion Date has {completion_date_non_empty}/{len(df)} non-empty")
            wo_status_count = len(df)
            self.logger.info(f"\n1. After Work Order Status filter: {wo_status_count} records remaining")
            # Log dropped cases from Work Order Status filter
            if not removed_wo.empty and wo_status_col:
                dropped_reasons = {}
                case_num_col = self.get_raw_col(df, 'Case Number')
                for status in excluded_wo_status:
                    status_cases = removed_wo[removed_wo[wo_status_col] == status]
                    if not status_cases.empty and case_num_col:
                        dropped_reasons[f"Status: {status}"] = status_cases[case_num_col].tolist()
                self.log_filtering_summary("Work Order Status", initial_count, wo_status_count, dropped_reasons)
                # Add to dropped cases details for summary table
                for status in excluded_wo_status:
                    status_cases = removed_wo[removed_wo[wo_status_col] == status]
                    if not status_cases.empty and case_num_col:
                        dropped_cases_details[f"Work Order Status: {status}"] = status_cases[case_num_col].tolist()
            
            # 2. Case Reason filter
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            excluded_case_reasons = [x.strip().lower() for x in self.excluded_case_reasons]
            case_reason_col = self.get_raw_col(df, 'Case Reason')
            mask_case = ~df[case_reason_col].isin(excluded_case_reasons) if case_reason_col else pd.Series([True]*len(df))
            removed_case = df[~mask_case]
            if not isinstance(removed_case, pd.DataFrame):
                removed_case = pd.DataFrame(removed_case)
            df = df[mask_case]
            case_reason_count = len(df)
            self.logger.info(f"\n2. After Case Reason filter: {case_reason_count} records remaining")
            # Log dropped cases from Case Reason filter
            if not removed_case.empty and case_reason_col:
                dropped_reasons = {}
                case_num_col = self.get_raw_col(df, 'Case Number')
                for reason in excluded_case_reasons:
                    reason_cases = removed_case[removed_case[case_reason_col] == reason]
                    if not reason_cases.empty and case_num_col:
                        dropped_reasons[f"Reason: {reason}"] = reason_cases[case_num_col].tolist()
                self.log_filtering_summary("Case Reason", wo_status_count, case_reason_count, dropped_reasons)
                # Add to dropped cases details for summary table
                for reason in excluded_case_reasons:
                    reason_cases = removed_case[removed_case[case_reason_col] == reason]
                    if not reason_cases.empty and case_num_col:
                        dropped_cases_details[f"Case Reason: {reason}"] = reason_cases[case_num_col].tolist()
            
            # 3. Closing Code filter
            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)
            excluded_closing_codes = [x.strip().lower() for x in self.excluded_closing_codes]
            closing_code_col = self.get_raw_col(df, 'Closing Code')
            mask_closing = ~df[closing_code_col].isin(excluded_closing_codes) if closing_code_col else pd.Series([True]*len(df))
            removed_closing = df[~mask_closing]
            if not isinstance(removed_closing, pd.DataFrame):
                removed_closing = pd.DataFrame(removed_closing)
            df = df[mask_closing]
            closing_code_count = len(df)
            self.logger.info(f"\n3. After Closing Code filter: {closing_code_count} records remaining")
            
            # CRITICAL: Restore Completion Date after filtering
            if completion_date_backup is not None and 'Completion Date' in df.columns:
                # Only restore for rows that are still in df
                df.loc[df.index, 'Completion Date'] = completion_date_backup.loc[df.index]
                restored_non_empty = (df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: Restored Completion Date after filters - {restored_non_empty}/{len(df)} non-empty")
            # Log dropped cases from Closing Code filter
            if not removed_closing.empty and closing_code_col:
                dropped_reasons = {}
                case_num_col = self.get_raw_col(df, 'Case Number')
                for code in excluded_closing_codes:
                    code_cases = removed_closing[removed_closing[closing_code_col] == code]
                    if not code_cases.empty and case_num_col:
                        dropped_reasons[f"Closing Code: {code}"] = code_cases[case_num_col].tolist()
                self.log_filtering_summary("Closing Code", case_reason_count, closing_code_count, dropped_reasons)
                # Add to dropped cases details for summary table
                for code in excluded_closing_codes:
                    code_cases = removed_closing[removed_closing[closing_code_col] == code]
                    if not code_cases.empty and case_num_col:
                        dropped_cases_details[f"Closing Code: {code}"] = code_cases[case_num_col].tolist()
            
            # 4. Apply CID/DMR filter with detailed logging
            self.logger.info(f"\n4. Applying CID/DMR filter:")
            pre_cid_count = len(df)
            df, removed_cases = self.filter_case(df)
            if not isinstance(removed_cases, pd.DataFrame):
                removed_cases = pd.DataFrame(removed_cases)
            post_cid_count = len(df)
            self.logger.info(f"   Records remaining: {post_cid_count}")
            
            # Add CID/DMR dropped cases to details
            if not removed_cases.empty:
                # Check if there are CID and DMR cases
                case_col = self.columns['case']
                cid_mask = removed_cases[case_col].astype(str).str.contains('cid', case=False, na=False)
                dmr_mask = removed_cases[case_col].astype(str).str.contains('dmr', case=False, na=False)
                
                if not cid_mask.empty:
                    cid_cases = removed_cases[cid_mask][self.columns['case_number']].tolist()
                    if cid_cases:
                        dropped_cases_details['CID Case'] = cid_cases
                
                if not dmr_mask.empty:
                    dmr_cases = removed_cases[dmr_mask][self.columns['case_number']].tolist()
                    if dmr_cases:
                        dropped_cases_details['DMR Case'] = dmr_cases
            
            # 5. Remove duplicate cases based on Case Number
            self.logger.info(f"\n5. Removing duplicate cases:")
            pre_duplicate_count = len(df)
            # Normalize to integer case numbers for accurate deduplication
            if self.columns['case_number'] in df.columns:
                df[self.columns['case_number']] = df[self.columns['case_number']].apply(self.normalize_case_number)
                df[self.columns['case_number']] = pd.Series(pd.to_numeric(df[self.columns['case_number']], errors='coerce')).astype('Int64')
            
            # Sort by Created On date (newest first) before removing duplicates
            created_on_col = self.columns['created_on']
            if created_on_col in df.columns:
                self.logger.info(f"   Sorting by '{created_on_col}' to keep newest duplicate cases")
                # Parse Created On to datetime for proper sorting
                try:
                    # Remove extra spaces and parse the date
                    df['_created_on_parsed'] = pd.to_datetime(df[created_on_col].astype(str).str.replace(r'\s+', ' ', regex=True), 
                                                               format='%m/%d/%Y %I:%M:%S %p', errors='coerce')
                    
                    # If parsing fails, try alternative format
                    if df['_created_on_parsed'].isna().any():
                        df['_created_on_parsed'] = pd.to_datetime(df[created_on_col], errors='coerce')
                    
                    # Sort by the parsed date in descending order (newest first)
                    df = df.sort_values('_created_on_parsed', ascending=False, na_position='last')
                    self.logger.info(f"   Successfully sorted by Created On date")
                except Exception as e:
                    self.logger.warning(f"   Could not parse Created On dates for sorting: {str(e)}")
                    # Fallback: sort by original column as string
                    df = df.sort_values(created_on_col, ascending=False, na_position='last')
            
            duplicates = df[df.duplicated(subset=[self.columns['case_number']], keep='first')]
            df = df.dropna(subset=[self.columns['case_number']]).drop_duplicates(subset=[self.columns['case_number']], keep='first')
            
            # Drop the temporary sorting column if it exists
            if '_created_on_parsed' in df.columns:
                df = df.drop(columns=['_created_on_parsed'])
            
            post_duplicate_count = len(df)
            self.logger.info(f"   Records remaining: {post_duplicate_count}")
            
            # Log dropped cases from Duplicate filter
            if not duplicates.empty:
                dropped_reasons = {"Duplicate Case Number": duplicates[self.columns['case_number']].tolist()}
                self.log_filtering_summary("Duplicate Removal", pre_duplicate_count, post_duplicate_count, dropped_reasons)
                
                # Add to dropped cases details for summary table
                dropped_cases_details['Duplicate Case Number'] = duplicates[self.columns['case_number']].tolist()

            # --- Log cases present in both raw and previous file but missing from output ---
            if prev_df is not None and not prev_df.empty:
                # Integer-normalize for reliable comparisons
                prev_cn = pd.Series(prev_df['Case Number']).apply(self.normalize_case_number).astype('Int64')
                raw_cn = pd.Series(df['Case Number']).apply(self.normalize_case_number).astype('Int64')
                out_cn = pd.Series(df['Case Number']).apply(self.normalize_case_number).astype('Int64')
                prev_case_numbers = set(prev_cn.dropna().tolist())
                raw_case_numbers = set(raw_cn.dropna().tolist())
                output_case_numbers = set(out_cn.dropna().tolist())
                missing_in_output = (prev_case_numbers & raw_case_numbers) - output_case_numbers
                if missing_in_output:
                    self.logger.warning(f"Cases present in both raw and previous file but missing from output: {missing_in_output}")
                    for case_num in missing_in_output:
                        self.log_dropped_case(case_num, "Missing in output after filtering", "Present in both raw and previous file")

            # Final count after all filters
            filtered_count = len(df)
            self.logger.info(f"\n=== Filtering Summary ===")
            self.logger.info(f"Initial count: {initial_count}")
            self.logger.info(f"After Work Order Status filter: {wo_status_count}")
            self.logger.info(f"After Case Reason filter: {case_reason_count}")
            self.logger.info(f"After Closing Code filter: {closing_code_count}")
            self.logger.info(f"After CID/DMR filter: {post_duplicate_count}")
            self.logger.info(f"After Duplicate Removal: {filtered_count}")
            self.logger.info(f"Total removed: {initial_count - filtered_count}")

            # Calculate previous file statistics if prev_df is available
            prev_stats = {}
            if prev_df is not None and not prev_df.empty:
                prev_cn = pd.Series(prev_df['Case Number']).apply(self.normalize_case_number).astype('Int64')
                raw_cn = pd.Series(df['Case Number']).apply(self.normalize_case_number).astype('Int64')
                prev_case_numbers = set(prev_cn.dropna().tolist())
                raw_case_numbers = set(raw_cn.dropna().tolist())
                prev_stats['Initial Count'] = len(prev_df)
                prev_stats['Matching Cases'] = len(prev_case_numbers & raw_case_numbers)
                prev_stats['New Cases'] = len(raw_case_numbers - prev_case_numbers)
                # Updated cases: cases in both, but with any field different (simplified: count all matches as updated)
                updated_cases = 0
                for case_num in (prev_case_numbers & raw_case_numbers):
                    prev_row = prev_df[prev_df['Case Number'] == case_num]
                    raw_row = df[df['Case Number'] == case_num]
                    if not prev_row.equals(raw_row):
                        updated_cases += 1
                prev_stats['Updated Cases'] = updated_cases
            else:
                prev_stats['Initial Count'] = ''
                prev_stats['Matching Cases'] = ''
                prev_stats['New Cases'] = ''
                prev_stats['Updated Cases'] = ''

            # Format the output data and merge with previous file
            self.logger.info("\nFormatting output data and merging with previous file...")
            output_df = self.format_output_data(df, prev_df)

            # Assign handlers (all cases processed normally)
            self.logger.info("\nAssigning handlers...")
            output_df = self.assign_handlers(output_df, selected_handlers, prev_df, prev_file)

            # AFTER handler assignment: Identify email duplicates in NEW cases only
            self.logger.info("\n=== Identifying email duplicates in new cases for Companies sheet ===")
            output_df, self.duplicate_company_cases = self.identify_email_duplicates_new_cases(output_df, prev_df, prev_file)

            # Final cleanup - ensure no completely empty rows
            output_df = self.clean_empty_rows(output_df)
            final_count = len(output_df)
            self.logger.info(f"\nFinal record count: {final_count}")

            # Process DND Emails Database and update PA Cases
            self.logger.info("\nProcessing DND Emails Database...")
            output_df = self.process_dnd_emails_database(output_df, prev_file)

            # Prepare a place to collect handler sheet updates from SMS/Email processing
            updated_handler_sheets = {}
            # tentative prev file for final (may be replaced if we write updated handler sheets)
            prev_file_for_final = prev_file

            # Process SMS replies if provided
            sms_processing_stats = {}
            if sms_file and os.path.exists(sms_file):
                self.logger.info(f"\nProcessing SMS replies file: {sms_file}")
                output_df, sms_processing_stats, updated_handler_sheets = self.process_sms_replies(output_df, sms_file, prev_file)
                self.logger.info("SMS processing completed")
                # If handler sheets were updated in-memory, persist them to a temporary prev_file
                # so FinalProcessor will pick up the updated handler sheets when creating the final workbook.
                prev_file_for_final = prev_file
                if updated_handler_sheets:
                    try:
                        # Create a small excel file containing updated handler sheets + Issue Not Fixed + DND Emails
                        tmp_dir = os.path.dirname(output_file) or os.getcwd()
                        tmp_prev_path = os.path.join(tmp_dir, f"{os.path.splitext(os.path.basename(output_file))[0]}_prev_handlers.xlsx")
                        
                        self.logger.info(f"Creating comprehensive temp file with handlers, Issue Not Fixed, and DND Emails: {tmp_prev_path}")
                        
                        with pd.ExcelWriter(tmp_prev_path, engine='xlsxwriter') as tmp_writer:
                            # Write handler sheets
                            for sheet_name, sheet_df in updated_handler_sheets.items():
                                try:
                                    # Ensure DataFrame has proper columns and is safe to write
                                    if isinstance(sheet_df, pd.DataFrame) and not sheet_df.empty:
                                        sheet_df.to_excel(tmp_writer, sheet_name=sheet_name, index=False)
                                    else:
                                        # Write empty frame with Case Number header if nothing else
                                        pd.DataFrame(columns=['Case Number']).to_excel(tmp_writer, sheet_name=sheet_name, index=False)
                                except Exception:
                                    # Skip problematic sheets
                                    continue
                            
                            # ALSO load Issue Not Fixed, DND Emails, and Companies from the ORIGINAL prev_file if it exists
                            if prev_file and os.path.exists(prev_file):
                                try:
                                    prev_excel = pd.ExcelFile(prev_file)
                                    prev_sheets = prev_excel.sheet_names
                                    self.logger.info(f"Original prev_file sheets: {prev_sheets}")
                                    
                                    # Load and add Issue Not Fixed sheet
                                    if 'Issue Not Fixed' in prev_sheets:
                                        try:
                                            issue_not_fixed_df = pd.read_excel(prev_file, sheet_name='Issue Not Fixed')
                                            self.logger.info(f"Loading {len(issue_not_fixed_df)} Issue Not Fixed cases from original prev_file")
                                            issue_not_fixed_df.to_excel(tmp_writer, sheet_name='Issue Not Fixed', index=False)
                                            self.logger.info(f"✓ Added Issue Not Fixed sheet with {len(issue_not_fixed_df)} cases")
                                        except Exception as e:
                                            self.logger.warning(f"Could not load Issue Not Fixed from prev_file: {str(e)}")
                                    
                                    # Load and add DND Emails sheet
                                    if 'DND Emails' in prev_sheets:
                                        try:
                                            dnd_emails_df = pd.read_excel(prev_file, sheet_name='DND Emails')
                                            self.logger.info(f"Loading {len(dnd_emails_df)} DND Emails from original prev_file")
                                            dnd_emails_df.to_excel(tmp_writer, sheet_name='DND Emails', index=False)
                                            self.logger.info(f"✓ Added DND Emails sheet with {len(dnd_emails_df)} emails")
                                        except Exception as e:
                                            self.logger.warning(f"Could not load DND Emails from prev_file: {str(e)}")
                                    
                                    # Load and add Companies sheet (for preservation across runs)
                                    if 'Companies' in prev_sheets:
                                        try:
                                            companies_df = pd.read_excel(prev_file, sheet_name='Companies')
                                            self.logger.info(f"Loading {len(companies_df)} Companies cases from original prev_file")
                                            companies_df.to_excel(tmp_writer, sheet_name='Companies', index=False)
                                            self.logger.info(f"✓ Added Companies sheet with {len(companies_df)} cases")
                                        except Exception as e:
                                            self.logger.warning(f"Could not load Companies from prev_file: {str(e)}")
                                except Exception as e:
                                    self.logger.warning(f"Could not load Issue Not Fixed/DND Emails/Companies from prev_file: {str(e)}")
                        
                        prev_file_for_final = tmp_prev_path
                        self.logger.info(f" Wrote comprehensive temp file with handlers + Issue Not Fixed + DND Emails: {prev_file_for_final}")
                    except Exception as e:
                        self.logger.error(f"Could not write temporary prev handler file: {str(e)}")
                        import traceback
                        self.logger.error(f"Traceback: {traceback.format_exc()}")
                else:
                    prev_file_for_final = prev_file

            # Process Email replies if provided
            email_processing_stats = {}
            self.logger.info(f"\nEmail file path: {email_file}")
            if email_file:
                self.logger.info(f"Email file exists: {os.path.exists(email_file)}")
                if os.path.exists(email_file):
                    self.logger.info(f"Processing Email replies file: {email_file}")
                    # Collect handler sheet updates from email processing as well
                    output_df, email_processing_stats, email_updated_handler_sheets = self.process_email_replies(output_df, email_file, prev_file)
                    self.logger.info("Email processing completed")
                    # Merge any handler sheet updates from email processing into the updated_handler_sheets map
                    try:
                        if email_updated_handler_sheets:
                            if not updated_handler_sheets:
                                updated_handler_sheets = {}
                            for k, v in email_updated_handler_sheets.items():
                                updated_handler_sheets[k] = v
                    except Exception:
                        pass
                else:
                    self.logger.warning(f"Email file does not exist: {email_file}")
            else:
                self.logger.info("No email file provided")

            # Extract DND emails from raw file
            raw_dnd_emails = []
            if self.columns['dnd'] in df.columns and self.columns['email'] in df.columns:
                dnd_mask = df[self.columns['dnd']].astype(str).str.strip().str.lower() == 'yes'
                dnd_cases = df[dnd_mask]
                
                for idx, row in dnd_cases.iterrows():
                    email = str(row[self.columns['email']]).strip()
                    if email and email.lower() not in ['', 'nan', 'none']:
                        raw_dnd_emails.append({
                            'Email': email,
                            'DND': 'Yes'
                        })
                
                self.logger.info(f"Found {len(raw_dnd_emails)} DND emails from raw file")

            # Prepare processing statistics for final processor
            processing_stats = {
                'Initial Count': initial_count,
                'After Work Order Status': wo_status_count,
                'After Case Reason': case_reason_count,
                'After Closing Code': closing_code_count,
                'After CID/DMR Filter': post_cid_count,
                'After Duplicate Removal': filtered_count,
                'Final Count': final_count,
                'Total Removed': initial_count - filtered_count,
                'Raw File Final Count After Cleaning': filtered_count,
                'Previous File Stats': prev_stats,
                'SMS Processing Stats': sms_processing_stats,
                'Email Processing Stats': email_processing_stats,
                'Raw File DND Emails': raw_dnd_emails,
                'DND Database': getattr(self, 'dnd_database', []),
                'Dropped Cases Details': dropped_cases_details,
                'Bank/Sutherland Updated Cases': getattr(self, 'bank_sutherland_updated_cases', []),
                'DND Updated Cases': getattr(self, 'dnd_updated_cases', [])
            }
            
            # Log processing summary
            self.logger.info(f"Processing complete: {initial_count} → {final_count} records ({initial_count - final_count} removed)")
            
            # Use final processor for additional sheets and validations
            try:
                from src.file_processing.final_processor import FinalProcessor
                final_processor = FinalProcessor()
                
                # Validate output data before final processing
                validation_results, critical_issues = final_processor.validate_output_data(output_df)
                
                if critical_issues:
                    self.logger.warning("Critical issues found during validation:")
                    for issue in critical_issues:
                        self.logger.warning(f"  - {issue}")
                
                # Process final output with additional sheets
                # Use prev_file_for_final if we created one with updated handler sheets
                try:
                    prev_for_final = prev_file_for_final if 'prev_file_for_final' in locals() else prev_file
                except Exception:
                    prev_for_final = prev_file

                success, message = final_processor.process_final_output(
                    output_df, 
                    output_file, 
                    processing_stats, 
                    sms_file, 
                    email_file, 
                    prev_for_final, 
                    duplicate_company_cases=self.duplicate_company_cases,
                    selected_handlers=selected_handlers
                )
                
                if not success:
                    raise Exception(f"Final processing failed: {message}")
            except ImportError as e:
                self.logger.error(f"Error importing FinalProcessor: {str(e)}")
                # Fallback: save basic output without additional sheets
                output_df.to_excel(output_file, index=False)
                self.logger.warning("Saved basic output without additional sheets due to import error")
            except Exception as e:
                self.logger.error(f"Error in final processing: {str(e)}")
                # Fallback: save basic output
                output_df.to_excel(output_file, index=False)
                self.logger.warning("Saved basic output due to final processing error")
            
            return True, f"Processing completed successfully. Final record count: {final_count}"
            
        except Exception as e:
            self.logger.error(f"File processing error: {str(e)}")
            self.logger.error("Stack trace:", exc_info=True)
            return False, f"Error during file processing: {str(e)}"
    
    def load_previous_file(self, prev_file):
        """Load and process the previous file, allowing for flexible customer name column detection."""
        if not prev_file or not os.path.exists(prev_file):
            self.logger.info("No previous file provided or file doesn't exist")
            return pd.DataFrame()
        try:
            self.logger.info(f"Loading previous file: {prev_file}")
            prev_df = pd.read_excel(prev_file)
            prev_df = self._normalize_id_columns(prev_df)
            # --- Flexible customer name column detection ---
            customer_col = None
            for col in prev_df.columns:
                if '(customer)' in col.lower() or 'customer name' in col.lower():
                    customer_col = col
                    break
            if customer_col and customer_col != 'Customer Name':
                prev_df['Customer Name'] = prev_df[customer_col]
            # Store previous assignments in a dictionary
            if 'Case Number' in prev_df.columns and 'Assigned To' in prev_df.columns:
                self.previous_assignments = dict(zip(prev_df['Case Number'], prev_df['Assigned To']))
                self.logger.info(f"Loaded {len(self.previous_assignments)} previous assignments")
            else:
                self.previous_assignments = {}
            return prev_df
        except Exception as e:
            self.logger.error(f"Error loading previous file: {str(e)}")
            return pd.DataFrame()

    def process_sms_replies(self, output_df, sms_file, prev_file=None):
        """Process SMS replies file and update PA cases based on the latest SMS text values per case.

        Matching is performed against handler sheets ("<handler>'s Cases") inside `prev_file` when available.
        Only exact replies '1', '2', or '3' are considered actionable. Other replies are skipped.
        """

        try:
            self.logger.info("Starting SMS replies processing...")
            sms_df = pd.read_excel(sms_file)
            sms_df = self._normalize_id_columns(sms_df)
            self.logger.info(f"SMS file loaded with {len(sms_df)} records")
            self.logger.info(f"SMS file columns: {list(sms_df.columns)}")

            # Load handler sheets from previous file (sheet names ending with "'s Cases")
            handler_sheets_map = {}
            if prev_file and os.path.exists(prev_file):
                try:
                    excel = pd.ExcelFile(prev_file)
                    for sheet_name in excel.sheet_names:
                        try:
                            if not isinstance(sheet_name, str):
                                continue
                            if not sheet_name.endswith("'s Cases"):
                                continue
                            sheet_df = pd.read_excel(prev_file, sheet_name=sheet_name)
                            # Normalize Case Number in the handler sheet if present
                            if 'Case Number' in sheet_df.columns:
                                sheet_df['Case Number'] = sheet_df['Case Number'].apply(self.normalize_case_number)
                                sheet_df['Case Number'] = pd.to_numeric(sheet_df['Case Number'], errors='coerce').astype('Int64')
                            handler_sheets_map[sheet_name] = sheet_df
                        except Exception:
                            # Skip problematic sheets
                            continue
                except Exception as e:
                    self.logger.warning(f"Could not read previous file for handler sheets: {str(e)}")

            # Robust column detection
            def find_col(df, target):
                for col in df.columns:
                    if col.strip().lower() == target.strip().lower():
                        return col
                for col in df.columns:
                    if target.strip().lower() in col.strip().lower():
                        return col
                return None

            sms_text_col = find_col(sms_df, 'SMS Text')
            case_number_col = find_col(sms_df, 'Case Number (Regarding) (Case)')
            # Try to find a timestamp/date column
            timestamp_col = None
            for col in sms_df.columns:
                col_lc = col.lower()
                if 'date' in col_lc or 'time' in col_lc or 'created' in col_lc:
                    timestamp_col = col
                    break
            if not sms_text_col or not case_number_col or not timestamp_col:
                self.logger.warning(f"Could not find required columns in SMS file. Columns found: {list(sms_df.columns)}")
                self.logger.warning(f"Expected: 'SMS Text', 'Case Number (Regarding) (Case)', and a date/time column.")
                return output_df, {'Skipped Cases': [{'Case Number': 'N/A', 'SMS Text': '', 'Reason': 'Required columns not found in SMS file'}]}, {}

            self.logger.info(f"Using columns - SMS Text: {sms_text_col}, Case Number: {case_number_col}, Timestamp: {timestamp_col}")

            # Convert timestamp to datetime
            sms_df[timestamp_col] = pd.to_datetime(sms_df[timestamp_col], errors='coerce')
            # Drop rows with missing case number or timestamp
            sms_df = sms_df.dropna(subset=[case_number_col, timestamp_col])
            # Sort and get latest SMS per case
            sms_df = sms_df.sort_values([case_number_col, timestamp_col])
            latest_sms = sms_df.groupby(case_number_col, as_index=False).last()

            summary = {'Fixed': [], 'Issue Not Fixed': [], 'Refused Callback': [], 'DND': [], 'Ambiguous': [], 'Updated SMS': []}
            skipped_cases = []

            # Only accept exact '1','2','3' as actionable replies
            def interpret_sms_text(sms_text):
                text = str(sms_text).strip()
                if text == '1':
                    return 'Fixed'
                if text == '2':
                    return 'Issue Not Fixed'
                if text == '3':
                    return 'DND'
                return None

            # --- HANDLER SHEET UPDATE LOGIC ---
            # After processing, update handler sheets if available
            def update_handler_sheets_from_output(output_df, handler_sheets_dict):
                # handler_sheets_dict: {handler_name: handler_df}
                if not handler_sheets_dict:
                    return
                for handler, handler_df in handler_sheets_dict.items():
                    # Normalize case numbers for matching
                    handler_df['Case Number'] = handler_df['Case Number'].apply(self.normalize_case_number).astype('Int64')
                    output_df['Case Number'] = output_df['Case Number'].apply(self.normalize_case_number).astype('Int64')
                    # Update rows in handler_df with values from output_df
                    for idx, row in handler_df.iterrows():
                        case_num = row['Case Number']
                        match = output_df[output_df['Case Number'] == case_num]
                        if not match.empty:
                            # Update status and final action
                            handler_df.at[idx, 'Status'] = match.iloc[0].get('Status', row.get('Status', ''))
                            handler_df.at[idx, 'Final Action'] = match.iloc[0].get('Final Action', row.get('Final Action', ''))
                return handler_sheets_dict
            # Usage: update_handler_sheets_from_output(output_df, handler_sheets_dict)

            for idx, row in latest_sms.iterrows():
                sms_text = str(row.get(sms_text_col, '')).strip()
                case_number = self.normalize_case_number(row.get(case_number_col, None))
                action = interpret_sms_text(sms_text)
                if case_number is None:
                    skipped_cases.append({
                        'Case Number': 'N/A',
                        'SMS Text': sms_text,
                        'Reason': 'Missing case number'
                    })
                    continue
                if action in ['Fixed', 'Issue Not Fixed', 'DND']:
                    # Match only against handler sheets (previous file) rather than PA Cases
                    found_in_handler = False
                    matched_sheet_name = None
                    matched_sheet_indices = []
                    for sheet_name, sheet_df in handler_sheets_map.items():
                        try:
                            if 'Case Number' not in sheet_df.columns:
                                continue
                            mask = sheet_df['Case Number'] == case_number
                            if mask.any():
                                found_in_handler = True
                                matched_sheet_name = sheet_name
                                matched_sheet_indices = sheet_df[mask].index.tolist()
                                # Update the handler sheet rows in-memory
                                for mi in matched_sheet_indices:
                                    if action == 'Fixed':
                                        sheet_df.at[mi, 'Final Action'] = 'Fixed'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                    elif action == 'Issue Not Fixed':
                                        sheet_df.at[mi, 'Final Action'] = 'Issue Not Fixed'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                    elif action == 'DND':
                                        sheet_df.at[mi, 'Final Action'] = 'DND'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                # store back updated sheet
                                handler_sheets_map[sheet_name] = sheet_df
                                break
                        except Exception:
                            continue

                    if found_in_handler:
                        # Per user's request: do NOT search/update PA Cases for SMS replies anymore.
                        # Always treat this as a handler-sheet update and record it for persistence.
                        update_made = f"Final Action set to {action}, Status=closed"
                        skipped_entry = {
                            'Case Number': case_number,
                            'SMS Text': sms_text,
                            'Reason': f'Handler-only update: {matched_sheet_name}',
                            'Source': 'SMS',
                            'Update Made': update_made,
                            'Handler Sheet': matched_sheet_name
                        }
                        skipped_cases.append(skipped_entry)
                        try:
                            summary.setdefault('Updated SMS', []).append({
                                'case_number': case_number,
                                'sms_text': sms_text,
                                'action': action,
                                'handler_sheet': matched_sheet_name,
                                'pa_updated': False,
                                'update_made': update_made
                            })
                        except Exception:
                            pass
                        self.logger.info(f"Handler-only update for SMS case {case_number}: {update_made} (handler: {matched_sheet_name}); PA Cases not checked/updated per configuration")
                    else:
                        reason = 'Case not found in handler sheets'
                        skipped_cases.append({
                            'Case Number': case_number,
                            'SMS Text': sms_text,
                            'Reason': reason
                        })
                        self.logger.info(f"Skipped SMS case {case_number}: {reason}")
                # All other replies are skipped
                else:
                    reason = f"Invalid or irrelevant SMS text: '{sms_text}'"
                    skipped_cases.append({
                        'Case Number': case_number,
                        'SMS Text': sms_text,
                        'Reason': reason
                    })
                    self.logger.info(f"Skipped SMS case {case_number}: {reason}")

            summary['Skipped Cases'] = skipped_cases
            # Log updated/skipped SMS summary
            try:
                self.logger.info(f"SMS updated count: {len(summary.get('Updated SMS', []))}")
                if summary.get('Updated SMS'):
                    self.logger.info(f"Updated SMS cases: {summary.get('Updated SMS')}")
                self.logger.info(f"SMS skipped count: {len(summary.get('Skipped Cases', []))}")
            except Exception:
                pass

            self.logger.info(f"SMS Processing Summary:")
            self.logger.info(f"Fixed: {len(summary['Fixed'])} cases")
            self.logger.info(f"Issue Not Fixed: {len(summary['Issue Not Fixed'])} cases")
            self.logger.info(f"Refused Callback: {len(summary['Refused Callback'])} cases")
            self.logger.info(f"DND: {len(summary['DND'])} cases")
            self.logger.info(f"Ambiguous (needs review): {len(summary['Ambiguous'])} cases")
            self.logger.info(f"Skipped: {len(skipped_cases)} cases")
            
            # Log comprehensive summary for Issue Not Fixed cases
            if summary['Issue Not Fixed']:
                self.log_issue_not_fixed_summary(
                    total_cases=len(summary['Issue Not Fixed']),
                    sms_cases=len(summary['Issue Not Fixed']),
                    email_cases=0,
                    new_cases=len(summary['Issue Not Fixed'])
                )

            return output_df, summary, handler_sheets_map
        except Exception as e:
            self.logger.error(f"Error processing SMS replies: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return output_df, {}, {}

    def process_email_replies(self, output_df, email_file, prev_file=None):
        """Process Email replies in the same strict way as SMS replies.

        - Accept only exact replies '1', '2', '3' (after trimming).
        - Case numbers: prefer header 'Case Number (Object) (Email)', else column F (index 5).
        - Replies: prefer header 'Action', else column H (index 7).
        - Only update handler sheets (sheets ending with "'s Cases") from prev_file; do not update PA Cases.
        - Return a summary containing a unified 'Skipped/Updated Entries' list of dicts with keys:
          Timestamp, Source, Case Number, Reply Text, Result, Reason
        """

        try:
            self.logger.info("Starting Email replies processing (SMS-style)...")
            email_df = pd.read_excel(email_file)
            email_df = self._normalize_id_columns(email_df)
            self.logger.info(f"Email file loaded with {len(email_df)} records")

            # Load handler sheets from previous file (sheet names ending with "'s Cases")
            handler_sheets_map = {}
            if prev_file and os.path.exists(prev_file):
                try:
                    excel = pd.ExcelFile(prev_file)
                    for sheet_name in excel.sheet_names:
                        try:
                            if not isinstance(sheet_name, str):
                                continue
                            if not sheet_name.endswith("'s Cases"):
                                continue
                            sheet_df = pd.read_excel(prev_file, sheet_name=sheet_name)
                            if 'Case Number' in sheet_df.columns:
                                sheet_df['Case Number'] = sheet_df['Case Number'].apply(self.normalize_case_number)
                                sheet_df['Case Number'] = pd.to_numeric(sheet_df['Case Number'], errors='coerce').astype('Int64')
                            handler_sheets_map[sheet_name] = sheet_df
                        except Exception:
                            continue
                except Exception as e:
                    self.logger.warning(f"Could not read previous file for handler sheets (emails): {str(e)}")

            # Column resolution: prefer named headers, otherwise use Excel column indices (F=5, H=7)
            def col_by_name_or_index(df, name, idx):
                if name in df.columns:
                    return name
                if len(df.columns) > idx:
                    return df.columns[idx]
                return None

            case_col = col_by_name_or_index(email_df, 'Case Number (Object) (Email)', 5)
            reply_col = col_by_name_or_index(email_df, 'Action', 7)

            # Timestamp column: try to find a date/time-like column; else None
            timestamp_col = None
            for col in email_df.columns:
                col_lc = str(col).lower()
                if 'date' in col_lc or 'time' in col_lc or 'created' in col_lc:
                    timestamp_col = col
                    break

            if not case_col or not reply_col:
                self.logger.warning(f"Could not find required email columns. Found columns: {list(email_df.columns)}")
                return output_df, {'Skipped/Updated Entries': [{'Timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Source': 'Email', 'Case Number': 'N/A', 'Reply Text': '', 'Result': 'Skipped', 'Reason': 'Required columns not found in email file'}]}, {}

            self.logger.info(f"Using columns - Case Number: {case_col}, Reply: {reply_col}, Timestamp: {timestamp_col}")

            # Prepare dataframe: convert timestamp if present
            if timestamp_col:
                email_df[timestamp_col] = pd.to_datetime(email_df[timestamp_col], errors='coerce')
                email_df = email_df.dropna(subset=[case_col])
                email_df = email_df.sort_values([case_col, timestamp_col])
                latest = email_df.groupby(case_col, as_index=False).last()
            else:
                # No timestamp: use last occurrence in file order
                latest = email_df.dropna(subset=[case_col]).copy()
                latest = latest.groupby(case_col, as_index=False).last()

            # Interpret replies: exact matches only
            def interpret_reply(text):
                t = str(text).strip()
                if t == '1':
                    return 'Fixed'
                if t == '2':
                    return 'Issue Not Fixed'
                if t == '3':
                    return 'DND'
                return None

            skipped_or_updated_entries = []
            summary = {'Fixed': [], 'Issue Not Fixed': [], 'DND': [], 'Ambiguous': [], 'Updated Emails': [], 'Skipped/Updated Entries': skipped_or_updated_entries}

            for idx, row in latest.iterrows():
                raw_case = row.get(case_col, '')
                case_number = self.normalize_case_number(raw_case)
                reply_text = str(row.get(reply_col, '')).strip()
                ts_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if timestamp_col:
                    val = row.get(timestamp_col)
                    try:
                        ts = pd.to_datetime(str(val), errors='coerce')
                        if isinstance(ts, pd.Timestamp) and not pd.isna(ts):
                            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        ts_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

                action = interpret_reply(reply_text)

                # Normalize case existence check
                if case_number is None:
                    skipped_or_updated_entries.append({'Timestamp': ts_str, 'Source': 'Email', 'Case Number': 'N/A', 'Reply Text': reply_text, 'Result': 'Skipped', 'Reason': 'Missing or invalid case number'})
                    continue

                if action in ['Fixed', 'Issue Not Fixed', 'DND']:
                    # Attempt to find and update in handler sheets only
                    found_in_handler = False
                    matched_sheet = None
                    for sheet_name, sheet_df in handler_sheets_map.items():
                        try:
                            if 'Case Number' not in sheet_df.columns:
                                continue
                            mask = sheet_df['Case Number'] == case_number
                            if mask.any():
                                found_in_handler = True
                                matched_sheet = sheet_name
                                indices = sheet_df[mask].index.tolist()
                                for mi in indices:
                                    if action == 'Fixed':
                                        sheet_df.at[mi, 'Final Action'] = 'Fixed'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                    elif action == 'Issue Not Fixed':
                                        sheet_df.at[mi, 'Final Action'] = 'Issue Not Fixed'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                    elif action == 'DND':
                                        sheet_df.at[mi, 'Final Action'] = 'DND'
                                        sheet_df.at[mi, 'Status'] = 'closed'
                                handler_sheets_map[sheet_name] = sheet_df
                                break
                        except Exception:
                            continue

                    if found_in_handler:
                        skipped_or_updated_entries.append({'Timestamp': ts_str, 'Source': 'Email', 'Case Number': str(case_number), 'Reply Text': reply_text, 'Result': 'Updated', 'Reason': f'Handler-only update: {matched_sheet}'})
                        summary.setdefault('Updated Emails', []).append({'case_number': case_number, 'reply_text': reply_text, 'action': action, 'handler_sheet': matched_sheet, 'pa_updated': False})
                        self.logger.info(f"Handler-only update for Email case {case_number} in {matched_sheet}")
                    else:
                        skipped_or_updated_entries.append({'Timestamp': ts_str, 'Source': 'Email', 'Case Number': str(case_number), 'Reply Text': reply_text, 'Result': 'Skipped', 'Reason': 'Case not found in handler sheets'})
                        self.logger.info(f"Skipped Email case {case_number}: not found in handler sheets")
                else:
                    skipped_or_updated_entries.append({'Timestamp': ts_str, 'Source': 'Email', 'Case Number': str(case_number), 'Reply Text': reply_text, 'Result': 'Skipped', 'Reason': 'Invalid or non-actionable reply'})

            summary['Skipped/Updated Entries'] = skipped_or_updated_entries
            self.logger.info(f"Email processing completed: {len(skipped_or_updated_entries)} skipped/updated entries recorded")
            return output_df, summary, handler_sheets_map
        except Exception as e:
            self.logger.error(f"Error processing Email replies: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return output_df, {}, {}

    def _interpret_sms_text_for_test(self, sms_text):
        """Simplified SMS interpreter for runtime: accept only exact '1','2','3'.

        Returns:
            'Fixed' | 'Issue Not Fixed' | 'DND' | None
        """
        text = str(sms_text).strip()
        if text == '1':
            return 'Fixed'
        if text == '2':
            return 'Issue Not Fixed'
        if text == '3':
            return 'DND'
        return None

    def _interpret_email_reply_for_test(self, reply_text):
        """Test method for email interpretation - extracts the logic for testing"""
        text = reply_text.lower().strip()
        
        # HIGH CONFIDENCE patterns (definite matches)
        high_confidence_fixed = [
            r'^\s*1\s*$',                           # Just "1"
            r'\b1\b.*issue resolved',               # "1 issue resolved"
            r'\bissue resolved\b',                  # "issue resolved"
            r'\bfixed\b',                           # "fixed"
            r'\bresolved\b',                        # "resolved"
            r'\bsorted\b',                          # "sorted"
            r'\bdone\b',                            # "done"
            r'\bcomplete\b',                        # "complete"
            r'\bfinished\b',                        # "finished"
            r'\bworking\b.*\bnow\b',               # "working now"
            r'\bproblem\b.*\bsolved\b',             # "problem solved"
            r'\ball\b.*\bgood\b',                   # "all good"
        ]
        
        high_confidence_not_fixed = [
            r'^\s*2\s*$',                           # Just "2"
            r'\b2\b.*need assistance',               # "2 need assistance"
            r'\bnot fixed\b',                       # "not fixed"
            r'\bissue not fixed\b',                 # "issue not fixed"
            r'\bstill broken\b',                    # "still broken"
            r'\bproblem persists\b',                # "problem persists"
            r'\bnot working\b',                     # "not working"
            r'\bneed\b.*\bhelp\b',                  # "need help"
            r'\bstill\b.*\bissue\b',                # "still issue"
        ]
        
        high_confidence_dnd = [
            r'^\s*2\s*$',                           # Just "2"
            r'\b3\b.*stop',                         # "3 stop"
            r'\bstop text messages\b',               # "stop text messages"
            r'\bdnd\b',                             # "dnd"
            r'\bdo not disturb\b',                   # "do not disturb"
            r'\bopt out\b',                         # "opt out"
            r'\bunsubscribe\b',                     # "unsubscribe"
        ]
        
        # MEDIUM CONFIDENCE patterns (likely matches)
        medium_confidence_fixed = [
            r'\bissue\b.*\bresolved\b',             # "issue resolved"
            r'\bresolved\b.*\bissue\b',             # "resolved issue"
            r'\bsorted\b.*\bout\b',                 # "sorted out"
            r'\bworking\b.*\bproperly\b',           # "working properly"
            r'\bissue\b.*\bfixed\b',                # "issue fixed"
            r'\bfixed\b.*\bissue\b',                # "fixed issue"
        ]
        
        medium_confidence_not_fixed = [
            r'\bassistance\b.*\bneeded\b',          # "assistance needed"
            r'\bproblem\b.*\bcontinues\b',          # "problem continues"
            r'\bissue\b.*\bremains\b',              # "issue remains"
            r'\bnot\b.*\bresolved\b',               # "not resolved"
        ]
        
        # Check HIGH CONFIDENCE patterns first (definite matches)
        for pat in high_confidence_fixed:
            if re.search(pat, text):
                return 'Fixed'
        for pat in high_confidence_not_fixed:
            if re.search(pat, text):
                return 'Issue Not Fixed'
        for pat in high_confidence_dnd:
            if re.search(pat, text):
                return 'DND'
        
        # Check MEDIUM CONFIDENCE patterns (likely matches)
        for pat in medium_confidence_fixed:
            if re.search(pat, text):
                return 'Fixed'
        for pat in medium_confidence_not_fixed:
            if re.search(pat, text):
                return 'Issue Not Fixed'
        
        # If we get here, the text is unclear - log it for review
        # This prevents losing potentially important responses
        return 'Ambiguous'  # New status for unclear responses

    def process_dnd_emails_database(self, output_df, prev_file):
        """Process DND Emails Database and update PA Cases accordingly"""
        try:
            self.logger.info("Starting DND Emails Database processing...")
            
            # Load DND emails from previous file's database
            prev_dnd_emails = self.load_previous_dnd_database(prev_file)
            self.logger.info(f"Loaded {len(prev_dnd_emails)} DND emails from previous file database")
            
            # Extract current DND emails from PA Cases
            current_dnd_emails = []
            if 'DND (Do Not Disturb)' in output_df.columns and 'Email' in output_df.columns:
                dnd_mask = output_df['DND (Do Not Disturb)'].astype(str).str.strip().str.lower() == 'yes'
                dnd_cases = output_df[dnd_mask]
                
                for idx, row in dnd_cases.iterrows():
                    email = str(row['Email']).strip()
                    if email and email.lower() not in ['', 'nan', 'none']:
                        current_dnd_emails.append({
                            'Email': email,
                            'DND': 'Yes'
                        })
                
                self.logger.info(f"Found {len(current_dnd_emails)} DND emails from current PA Cases")
            
            # Combine DND emails (previous + current)
            all_dnd_emails = prev_dnd_emails.copy()
            existing_emails = {email['Email'] for email in prev_dnd_emails}
            
            # Add new DND emails from current PA Cases
            new_dnd_emails = []
            for dnd_email in current_dnd_emails:
                if dnd_email['Email'] not in existing_emails:
                    all_dnd_emails.append(dnd_email)
                    existing_emails.add(dnd_email['Email'])
                    new_dnd_emails.append(dnd_email['Email'])
            
            self.logger.info(f"Added {len(new_dnd_emails)} new DND emails to database")
            
            # Store the combined DND database for later use
            self.dnd_database = all_dnd_emails
            
            # Update PA Cases based on DND database
            updated_cases = self.update_pa_cases_with_dnd_database(output_df, all_dnd_emails)
            
            self.logger.info(f"Updated {updated_cases} PA Cases with DND status")
            
            return output_df
            
        except Exception as e:
            self.logger.error(f"Error processing DND Emails Database: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return output_df

    def load_previous_dnd_database(self, prev_file):
        """Load DND emails from previous file's DND Emails Database sheet"""
        try:
            if not prev_file or not os.path.exists(prev_file):
                self.logger.info("No previous file provided or file doesn't exist - starting with empty DND database")
                return []
            
            # Try to read the previous file
            try:
                prev_df = pd.read_excel(prev_file, sheet_name='DND Emails Database')
                self.logger.info(f"Successfully loaded DND Emails Database from previous file with {len(prev_df)} emails")
                
                # Convert to list of dictionaries
                dnd_emails = []
                if 'Email' in prev_df.columns and 'DND' in prev_df.columns:
                    for idx, row in prev_df.iterrows():
                        email = str(row['Email']).strip()
                        if email and email.lower() not in ['', 'nan', 'none']:
                            dnd_emails.append({
                                'Email': email,
                                'DND': 'Yes'
                            })
                
                return dnd_emails
                
            except Exception as e:
                self.logger.warning(f"Could not read DND Emails Database from previous file: {str(e)}")
                self.logger.info("Starting with empty DND database")
                return []
                
        except Exception as e:
            self.logger.error(f"Error loading previous DND database: {str(e)}")
            return []

    def update_pa_cases_with_dnd_database(self, output_df, dnd_database):
        """Update PA Cases based on DND database matches"""
        try:
            if not dnd_database or 'Email' not in output_df.columns:
                self.logger.info("No DND database or Email column found - skipping PA Cases update")
                return 0
            
            # Create set of DND emails for faster lookup
            dnd_emails_set = {email['Email'].lower() for email in dnd_database}
            
            # Find matching cases
            updated_count = 0
            
            for idx, row in output_df.iterrows():
                email = str(row['Email']).strip().lower()
                if email and email in dnd_emails_set:
                    # Update the case to DND status
                    output_df.at[idx, 'DND (Do Not Disturb)'] = 'Yes'
                    output_df.at[idx, 'Action 1'] = 'DND'
                    output_df.at[idx, 'Action 2'] = 'DND'
                    output_df.at[idx, 'Action 3'] = 'DND'
                    output_df.at[idx, 'Final Action'] = 'DND'
                    output_df.at[idx, 'Status'] = 'Closed'
                    updated_count += 1
                    
                    # Log the update
                    case_number = str(row.get('Case Number', 'N/A'))
                    self.logger.info(f"Updated case {case_number} to DND status (email: {email})")
            
            self.logger.info(f"Total PA Cases updated to DND status: {updated_count}")
            return updated_count
            
        except Exception as e:
            self.logger.error(f"Error updating PA Cases with DND database: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return 0

    def clean_handler_name(self, handler):
        """Clean handler name by removing any extra formatting, booleans, or special characters"""
        if pd.isna(handler) or not str(handler).strip():
            return ''
        
        handler = str(handler).strip()
        
        # If it's a tuple string like "(name, False)", extract just the name
        if handler.startswith('(') and handler.endswith(')'):
            handler = handler[1:-1].split(',')[0]
            
        # Remove common artifacts
        handler = handler.replace("'", "").replace('"', '').replace('(', '').replace(')', '')
        handler = handler.split(',')[0]  # Remove everything after a comma
        handler = handler.replace('False', '').replace('True', '')  # Remove boolean values
        
        # Remove any remaining whitespace
        handler = handler.strip()
        
        return handler

    def normalize_case_number(self, case_number):
        """Normalize case number to an integer where possible to avoid '.0' string artifacts.

        Returns:
            int | pandas._libs.missing.NAType | None: Integer case number when numeric, NA/None otherwise
        """
        if case_number is None or (isinstance(case_number, float) and pd.isna(case_number)):
            return None

        text_value = str(case_number).strip()
        if text_value == "" or text_value.lower() in {"nan", "none"}:
            return None

        # If it is an integer-like number possibly with a trailing .0, coerce to int
        if re.fullmatch(r"\d+(?:\.0+)?", text_value):
            try:
                return int(float(text_value))
            except Exception:
                pass

        # Try general numeric coercion then keep only integers
        try:
            numeric_value = pd.to_numeric(text_value, errors='coerce')
            if pd.notna(numeric_value) and float(numeric_value).is_integer():
                return int(numeric_value)
        except Exception:
            pass

        # If still not numeric, try to extract a contiguous digit sequence (common when values contain notes)
        try:
            m = re.search(r"(\d+)", text_value)
            if m:
                return int(m.group(1))
        except Exception:
            pass

        # Non-numeric or non-integer-like case numbers are treated as missing for dedup/compare
        return None

    def identify_email_duplicates_new_cases(self, df, prev_df=None, prev_file=None):
        """
        Identify NEW cases that have duplicate emails (2+ occurrences).
        Only checks cases that are NOT in the previous file.
        These cases will be added to the Companies sheet and preserved across runs.
        
        CRITICAL: Checks against ALL sheets in previous file (PA Cases + handler sheets + Companies)
        to correctly identify truly new cases.
        
        Args:
            df: Current processed DataFrame
            prev_df: Previous file DataFrame (for identifying new cases)
            prev_file: Path to previous file (for loading all sheets)
        
        Returns: 
            tuple (df_with_cleared_assigned_to, duplicate_cases_df)
            - df_with_cleared_assigned_to: Original df with Assigned To cleared for duplicate cases
            - duplicate_cases_df: DataFrame of cases with duplicate emails (for Companies sheet)
        """
        try:
            self.logger.info("=== Analyzing new cases for email duplicates ===")
            
            # Make a copy to avoid modifying original
            df = df.copy()
            
            # Build comprehensive set of ALL previous case numbers from ALL sheets
            prev_case_numbers = set()
            
            # Add cases from prev_df (PA Cases - first sheet)
            if prev_df is not None and not prev_df.empty and 'Case Number' in prev_df.columns:
                for cn in prev_df['Case Number'].dropna():
                    normalized = self.normalize_case_number(cn)
                    if normalized is not None:
                        prev_case_numbers.add(normalized)
                self.logger.info(f"Loaded {len(prev_case_numbers)} case numbers from PA Cases")
            
            # ALSO load case numbers from ALL handler sheets and Companies in the Excel file
            # This is critical - otherwise cases from handler sheets would be treated as "new"
            import os
            if prev_file and os.path.exists(prev_file):
                try:
                    with pd.ExcelFile(prev_file) as excel:
                        for sheet_name in excel.sheet_names:
                            if not isinstance(sheet_name, str):
                                continue
                            # Include handler sheets and Companies sheet
                            if sheet_name.endswith("'s Cases") or 'companies' in sheet_name.lower():
                                try:
                                    sheet_df = pd.read_excel(prev_file, sheet_name=sheet_name)
                                    if 'Case Number' in sheet_df.columns:
                                        for cn in sheet_df['Case Number'].dropna():
                                            normalized = self.normalize_case_number(cn)
                                            if normalized is not None:
                                                prev_case_numbers.add(normalized)
                                except Exception:
                                    continue
                    self.logger.info(f"After loading all sheets: {len(prev_case_numbers)} total previous case numbers")
                except Exception as e:
                    self.logger.warning(f"Could not load additional sheets from prev file: {e}")
            
            # Identify new cases (not in ANY previous sheet)
            if prev_case_numbers:
                df['_normalized_case_num'] = df['Case Number'].apply(self.normalize_case_number)
                new_cases_mask = ~df['_normalized_case_num'].isin(prev_case_numbers)
                new_cases = df[new_cases_mask].copy()
                
                self.logger.info(f"Total cases: {len(df)}, Previous cases (all sheets): {len(prev_case_numbers)}, New cases: {len(new_cases)}")
            else:
                new_cases = df.copy()
                new_cases['_normalized_case_num'] = new_cases['Case Number'].apply(self.normalize_case_number)
                self.logger.info(f"No previous file - checking all {len(new_cases)} cases for email duplicates")
            
            if new_cases.empty:
                self.logger.info("No new cases to check for email duplicates")
                # Drop temp column if added
                if '_normalized_case_num' in df.columns:
                    df = df.drop(columns=['_normalized_case_num'])
                return df, pd.DataFrame()
            
            # Check for Email column
            if 'Email' not in new_cases.columns:
                self.logger.warning("No Email column found - cannot detect email duplicates")
                if '_normalized_case_num' in df.columns:
                    df = df.drop(columns=['_normalized_case_num'])
                return df, pd.DataFrame()
            
            # Normalize emails for comparison (case-insensitive, trimmed)
            new_cases['_email_normalized'] = new_cases['Email'].astype(str).str.strip().str.lower()
            
            # CRITICAL: Only count NEW/OPEN cases (not closed) for duplicate detection
            # This prevents adding cases where email has 1 open + several closed
            if 'Status' in new_cases.columns:
                open_statuses = ['new', 'in_progress', 'in progress', 'in progress today', 'skipped', '']
                status_normalized = new_cases['Status'].astype(str).str.strip().str.lower()
                open_cases_mask = status_normalized.isin(open_statuses) | status_normalized.isna()
                new_open_cases = new_cases[open_cases_mask].copy()
                self.logger.info(f"Filtered to {len(new_open_cases)} NEW/OPEN cases (from {len(new_cases)} new cases) for duplicate check")
            else:
                new_open_cases = new_cases.copy()
                self.logger.info("No Status column - using all new cases for duplicate check")
            
            # Find emails that appear 2+ times in NEW/OPEN cases only
            email_counts = new_open_cases['_email_normalized'].value_counts()
            duplicate_emails = email_counts[email_counts >= 2].index.tolist()
            
            # Remove blank/invalid emails from duplicate list
            invalid_emails = ['', 'nan', 'none', 'null', 'n/a', 'na']
            duplicate_emails = [e for e in duplicate_emails if e and e not in invalid_emails]
            
            if not duplicate_emails:
                self.logger.info("No email duplicates found in new cases")
                # Drop temp columns
                if '_normalized_case_num' in df.columns:
                    df = df.drop(columns=['_normalized_case_num'])
                return df, pd.DataFrame()
            
            self.logger.info(f"Found {len(duplicate_emails)} duplicate email addresses in new cases:")
            for email in duplicate_emails[:10]:  # Log first 10 for brevity
                count = email_counts[email]
                self.logger.info(f"  '{email}': {count} occurrences")
            if len(duplicate_emails) > 10:
                self.logger.info(f"  ... and {len(duplicate_emails) - 10} more")
            
            # FIXED: Get only OPEN cases with duplicate emails (not closed cases for same email)
            # This ensures only 2+ OPEN cases go to Companies sheet
            duplicate_cases = new_open_cases[new_open_cases['_email_normalized'].isin(duplicate_emails)].copy()
            
            # Drop temporary columns from duplicate_cases
            temp_cols = ['_email_normalized', '_normalized_case_num']
            for col in temp_cols:
                if col in duplicate_cases.columns:
                    duplicate_cases = duplicate_cases.drop(columns=[col])
            
            # Clear Assigned To column for these cases (will be assigned in Companies sheet)
            duplicate_cases['Assigned To'] = ''
            
            # Get case numbers of duplicate cases
            duplicate_case_numbers = set(duplicate_cases['Case Number'].dropna().apply(self.normalize_case_number))
            
            # Clear Assigned To in main df for duplicate cases
            df['_normalized_case_num'] = df['Case Number'].apply(self.normalize_case_number)
            df.loc[df['_normalized_case_num'].isin(duplicate_case_numbers), 'Assigned To'] = ''
            
            # Drop temp column from main df
            df = df.drop(columns=['_normalized_case_num'])
            self.logger.info(f"✓ Identified {len(duplicate_cases)} OPEN cases with duplicate emails")
            self.logger.info(f"  These cases will be added to the Companies sheet")
            
            return df, duplicate_cases
            
        except Exception as e:
            self.logger.warning(f"Error identifying email duplicates: {str(e)}")
            import traceback
            self.logger.warning(f"Traceback: {traceback.format_exc()}")
            # Clean up any temp columns
            if '_normalized_case_num' in df.columns:
                df = df.drop(columns=['_normalized_case_num'])
            return df, pd.DataFrame()

    def assign_handlers(self, df, selected_handlers, prev_df=None, prev_file=None):
        """Assign handlers for the current dataset only (no preservation from previous sheets).
        - Do NOT read or rely on previous handler sheets or special preservation columns
        - Distribute cases fairly across SELECTED handlers based on company grouping
        - Preservation is handled later during per-handler sheet merging
        """
        try:
            self.logger.info("=== SEPARATED APPROACH: Preserve ALL Previous Work + Assign NEW Cases to SELECTED Handlers Only ===")
            self.logger.info(f"RAW selected_handlers received: {selected_handlers}")
            cleaned_handlers = [self.clean_handler_name(h) for h in selected_handlers if self.clean_handler_name(h)]
            self.logger.info(f"SELECTED handlers for NEW case assignment: {cleaned_handlers}")
            
            if 'Case Number' not in df.columns:
                raise ValueError("Case Number column not found in dataframe")
            if 'Assigned To' not in df.columns:
                df['Assigned To'] = ''
            
            selected_handlers_set = set(cleaned_handlers)

            # STEP 1: NORMALIZE ALL CASE NUMBERS FIRST
            self.logger.info("=== STEP 1: NORMALIZING ALL CASE NUMBERS ===")
            df['Case Number'] = df['Case Number'].apply(self.normalize_case_number)
            # Enforce integer dtype with nullable Int64 to preserve NA
            df['Case Number'] = pd.to_numeric(df['Case Number'], errors='coerce').astype('Int64')
            self.logger.info(f"Normalized all case numbers in current data (stored as integers)")
            
            # STEP 2: Preserve existing assignments from previous main file (LOCK old cases)
            self.logger.info("=== STEP 2: PRESERVING previous-file assignments (lock old cases) ===")
            prev_assignments = set()
            prev_case_to_handler = {}
            if prev_df is not None and not prev_df.empty:
                try:
                    prev_df_local = prev_df.copy()
                    # Normalize case numbers in previous file
                    prev_df_local['Case Number'] = prev_df_local['Case Number'].apply(self.normalize_case_number)
                    prev_df_local['Case Number'] = pd.to_numeric(prev_df_local['Case Number'], errors='coerce').astype('Int64')
                    # Build mapping and set for quick lookup
                    for _, row in prev_df_local.dropna(subset=['Case Number']).iterrows():
                        case_num = int(row['Case Number'])
                        handler = self.clean_handler_name(row.get('Assigned To', ''))
                        if handler:
                            prev_case_to_handler[case_num] = handler
                            prev_assignments.add(case_num)
                    # Apply preserved assignments to current df where case exists
                    for case_num, handler in prev_case_to_handler.items():
                        mask = df['Case Number'] == case_num
                        if mask.any():
                            idx = mask.idxmax()
                            df.at[idx, 'Assigned To'] = handler
                    self.logger.info(f"Preserved {len(prev_assignments)} existing cases from previous file")
                except Exception as preserve_err:
                    self.logger.warning(f"Could not preserve previous assignments from main file: {str(preserve_err)}")

            # Also preserve assignments from previous individual handler sheets (by case number → handler)
            try:
                if prev_file and os.path.exists(prev_file):
                    excel_file = pd.ExcelFile(prev_file)
                    handler_sheets = [sheet for sheet in excel_file.sheet_names if isinstance(sheet, str) and sheet.endswith("'s Cases")]
                    preserved_from_sheets = 0
                    for sheet_name in handler_sheets:
                        handler_name = sheet_name.replace("'s Cases", '').strip()
                        try:
                            sheet_df = pd.read_excel(prev_file, sheet_name=sheet_name)
                            if 'Case Number' not in sheet_df.columns:
                                continue
                            # Normalize and iterate
                            sheet_df_local = sheet_df.copy()
                            sheet_df_local['Case Number'] = sheet_df_local['Case Number'].apply(self.normalize_case_number)
                            sheet_df_local['Case Number'] = pd.to_numeric(sheet_df_local['Case Number'], errors='coerce').astype('Int64')
                            for _, row in sheet_df_local.dropna(subset=['Case Number']).iterrows():
                                case_num = int(row['Case Number'])
                                prev_case_to_handler[case_num] = handler_name
                                if case_num not in prev_assignments:
                                    prev_assignments.add(case_num)
                                    preserved_from_sheets += 1
                        except Exception:
                            continue
                    # Apply preserved assignments from sheets to current df
                    applied = 0
                    for case_num, handler in prev_case_to_handler.items():
                        mask = df['Case Number'] == case_num
                        if mask.any():
                            idx = mask.idxmax()
                            df.at[idx, 'Assigned To'] = handler
                            applied += 1
                    self.logger.info(f"Preserved {preserved_from_sheets} new cases from previous handler sheets; applied to {applied} rows in current data")
            except Exception as e:
                self.logger.warning(f"Could not preserve from previous handler sheets: {str(e)}")

            # STEP 3: Calculate current workload after preservation
            self.logger.info("=== STEP 3: Calculating Current Workload After Preservation ===")
            current_workload = {}
            for handler in cleaned_handlers:
                count = len(df[df['Assigned To'] == handler])
                current_workload[handler] = count
            
            self.logger.info(f"Current workload after preservation: {current_workload}")
            
            # STEP 4: Assign ONLY NEW cases to SELECTED handlers (do not touch preserved ones)
            self.logger.info("=== STEP 4: Assigning ONLY NEW cases to SELECTED handlers ===")
            if prev_assignments:
                new_cases_df = df[~df['Case Number'].isin(prev_assignments)].copy()
            else:
                new_cases_df = df.copy()
            
            if not new_cases_df.empty:
                self.logger.info(f"Processing {len(new_cases_df)} NEW cases for assignment")
                self.logger.info(f"Cases will ONLY be assigned to SELECTED handlers: {cleaned_handlers}")
                # Extra log: preserved vs new per handler before assignment
                try:
                    preserved_counts = {}
                    for handler in cleaned_handlers:
                        preserved_counts[handler] = len(df[(df['Assigned To'] == handler) & (df['Case Number'].isin(prev_assignments))])
                    self.logger.info(f"Preserved counts (locked from previous): {preserved_counts}")
                except Exception:
                    pass
                
                # Get company column
                company_col = self._get_company_column(df)
                if company_col is None:
                    self.logger.warning("No company column found - cannot do company-based assignment")
                    return df
                
                # FAIR DISTRIBUTION LOGIC: Only assign to SELECTED handlers
                self.logger.info("=== FAIR DISTRIBUTION: Assigning cases only to SELECTED handlers ===")
                
                # Group new cases by company
                new_cases_df['Company_Lower'] = new_cases_df[company_col].fillna('').astype(str).str.strip().str.lower()
                company_groups = new_cases_df.groupby('Company_Lower')
                
                self.logger.info(f"Found {len(company_groups)} unique companies in NEW cases")
                
                # Separate companies with multiple cases from single cases and no-company cases
                multi_case_companies = {}
                single_case_companies = {}
                no_company_cases = []
                
                for company, group in company_groups:
                    case_count = len(group)
                    if company == '' or company == 'nan' or company == 'none':
                        # No company cases
                        no_company_cases.extend(group['Case Number'].tolist())
                    elif case_count == 1:
                        # Single case companies
                        single_case_companies[company] = group['Case Number'].iloc[0]
                    else:
                        # Multi-case companies
                        multi_case_companies[company] = group['Case Number'].tolist()
                
                self.logger.info(f"Company breakdown:")
                self.logger.info(f"  Multi-case companies: {len(multi_case_companies)} (companies with 2+ cases)")
                self.logger.info(f"  Single-case companies: {len(single_case_companies)} (companies with 1 case)")
                self.logger.info(f"  No-company cases: {len(no_company_cases)} (cases without company)")
                
                # STEP 3A: Distribute multi-case companies fairly across SELECTED handlers only
                self.logger.info("=== STEP 3A: Distributing Multi-Case Companies Fairly to SELECTED Handlers ===")
                multi_case_assignments = {}
                
                if multi_case_companies:
                    # Sort companies by number of cases (largest first for better distribution)
                    sorted_companies = sorted(multi_case_companies.items(), key=lambda x: len(x[1]), reverse=True)
                    
                    # Distribute companies across SELECTED handlers in round-robin fashion
                    handler_index = 0
                    for company, case_numbers in sorted_companies:
                        assigned_handler = cleaned_handlers[handler_index % len(cleaned_handlers)]
                        
                        # Assign all cases from this company to the same SELECTED handler
                        for case_num in case_numbers:
                            multi_case_assignments[case_num] = assigned_handler
                        
                        self.logger.info(f"Company '{company}' ({len(case_numbers)} cases) -> {assigned_handler} (SELECTED)")
                        
                        # Move to next SELECTED handler for next company
                        handler_index += 1
                    
                    self.logger.info(f"Distributed {len(multi_case_companies)} multi-case companies across SELECTED handlers")
                else:
                    self.logger.info("No multi-case companies found")
                
                # STEP 3B: Distribute single-case companies and no-company cases to SELECTED handlers
                self.logger.info("=== STEP 3B: Distributing Single Cases to SELECTED Handlers ===")
                single_and_no_company_assignments = {}
                
                # Combine single cases and no-company cases
                all_single_cases = list(single_case_companies.values()) + no_company_cases
                
                if all_single_cases:
                    # Distribute these cases evenly across SELECTED handlers only
                    handler_index = 0
                    for case_num in all_single_cases:
                        assigned_handler = cleaned_handlers[handler_index % len(cleaned_handlers)]
                        single_and_no_company_assignments[case_num] = assigned_handler
                        
                        # Move to next SELECTED handler for next case
                        handler_index += 1
                    
                    self.logger.info(f"Distributed {len(all_single_cases)} single cases and no-company cases across SELECTED handlers")
                else:
                    self.logger.info("No single cases or no-company cases found")
                
                # STEP 3C: Apply all assignments to the dataframe
                self.logger.info("=== STEP 3C: Applying All Assignments ===")
                all_new_assignments = {**multi_case_assignments, **single_and_no_company_assignments}
                
                # VALIDATION: Ensure no unselected handlers get new cases
                unselected_handlers_with_new_cases = []
                for case_num, handler in all_new_assignments.items():
                    if handler not in selected_handlers_set:
                        unselected_handlers_with_new_cases.append((case_num, handler))
                
                if unselected_handlers_with_new_cases:
                    self.logger.error(f"❌ CRITICAL ERROR: Unselected handlers are getting new cases!")
                    for case_num, handler in unselected_handlers_with_new_cases:
                        self.logger.error(f"   Case {case_num} assigned to unselected handler: {handler}")
                    raise ValueError("Unselected handlers are getting new cases - this should not happen!")
                
                for case_num, handler in all_new_assignments.items():
                    case_mask = df['Case Number'] == case_num
                    if case_mask.any():
                        case_idx = case_mask.idxmax()
                        df.at[case_idx, 'Assigned To'] = handler
                        self.logger.debug(f"Assigned NEW case {case_num} -> {handler}")
                
                self.logger.info(f"Applied {len(all_new_assignments)} new case assignments")
                self.logger.info(f"VALIDATION PASSED: All cases assigned only to selected handlers")
                
                # STEP 3D: Distribution Summary
                self.logger.info("=== STEP 3D: Distribution Summary ===")
                handler_counts = {}
                for handler in cleaned_handlers:
                    count = len(df[df['Assigned To'] == handler])
                    handler_counts[handler] = count
                
                self.logger.info(f"Final distribution after NEW case assignment:")
                for handler, count in sorted(handler_counts.items()):
                    self.logger.info(f"  {handler}: {count} total cases")
                
                # Calculate distribution fairness
                if handler_counts:
                    min_cases = min(handler_counts.values())
                    max_cases = max(handler_counts.values())
                    fairness_ratio = min_cases / max_cases if max_cases > 0 else 1.0
                    self.logger.info(f"Distribution fairness ratio: {fairness_ratio:.2f} (1.0 = perfectly fair)")
                    
                    if fairness_ratio < 0.8:
                        self.logger.warning(f"⚠️  Distribution may be uneven (fairness ratio: {fairness_ratio:.2f})")
                    else:
                        self.logger.info(f"Distribution is fair (fairness ratio: {fairness_ratio:.2f})")
            else:
                self.logger.info("No new cases to assign")

            # STEP 5: Final deduplication check
            self.logger.info("=== STEP 5: Final Deduplication Check ===")
            pre_dedup_count = len(df)
            # Ensure integer dtype for deduplication
            df['Case Number'] = pd.Series(pd.to_numeric(df['Case Number'], errors='coerce')).astype('Int64')
            df = df.dropna(subset=['Case Number']).drop_duplicates(subset=['Case Number'], keep='last')
            post_dedup_count = len(df)
            duplicates_removed = pre_dedup_count - post_dedup_count
            
            if duplicates_removed > 0:
                self.logger.warning(f"⚠️  Removed {duplicates_removed} duplicate case entries during assignment")
                self.logger.warning(f"   This prevents cases from being assigned to multiple handlers")
            else:
                self.logger.info("No duplicates found in assigned cases")
            
            # STEP 6: Final workload summary
            self.logger.info("=== STEP 6: Final Workload Summary ===")
            
            # Get ALL handlers (including preserved ones)
            all_handlers = df['Assigned To'].dropna().unique()
            all_handlers = [h for h in all_handlers if h and str(h).strip()]
            
            final_workload = {}
            for handler in all_handlers:
                count = len(df[df['Assigned To'] == handler])
                final_workload[handler] = count
            
            self.logger.info(f"Final workload distribution (ALL handlers): {final_workload}")
            
            # Show separation between selected and preserved handlers
            selected_workload = {h: final_workload.get(h, 0) for h in cleaned_handlers}
            preserved_workload = {h: final_workload.get(h, 0) for h in all_handlers if h not in cleaned_handlers}
            
            self.logger.info(f"SELECTED handlers workload: {selected_workload}")
            if preserved_workload:
                self.logger.info(f"PRESERVED handlers workload (no new cases): {preserved_workload}")
            
            # Calculate distribution fairness for selected handlers only
            if selected_workload and len(selected_workload) > 1:
                min_cases = min(selected_workload.values())
                max_cases = max(selected_workload.values())
                fairness_ratio = min_cases / max_cases if max_cases > 0 else 1.0
                self.logger.info(f"Distribution fairness ratio (selected handlers only): {fairness_ratio:.2f} (1.0 = perfectly fair)")
                
                if fairness_ratio < 0.8:
                    self.logger.warning(f"⚠️  Distribution may be uneven (fairness ratio: {fairness_ratio:.2f})")
                else:
                    self.logger.info(f"Distribution is fair (fairness ratio: {fairness_ratio:.2f})")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error in assign_handlers: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return df

    def _load_handler_sheet_assignments_v2(self, prev_file, selected_handlers_set):
        """SEPARATED METHOD: Load ALL handler sheet assignments for preservation
        - Preserves ALL handler work regardless of selection status
        - Selection status only affects NEW case assignment, not preservation
        - This ensures Ibrahim keeps his existing cases even when not selected"""
        try:
            self.logger.info(f"=== LOADING ALL HANDLER SHEET ASSIGNMENTS FOR PRESERVATION ===")
            self.logger.info(f"File: {prev_file}")
            self.logger.info(f"Selected handlers for NEW assignments: {selected_handlers_set}")
            
            if not os.path.exists(prev_file):
                self.logger.error(f"File does not exist: {prev_file}")
                return {}
            
            # Read the Excel file
            excel_file = pd.ExcelFile(prev_file)
            self.logger.info(f"Excel sheets found: {excel_file.sheet_names}")
            
            handler_sheet_assignments = {}
            total_cases_found = 0
            total_assignments_loaded = 0
            
            # Look for sheets ending with "'s Cases"
            handler_sheets = [sheet for sheet in excel_file.sheet_names if isinstance(sheet, str) and sheet.endswith("'s Cases")]
            self.logger.info(f"Handler sheets found: {handler_sheets}")
            
            for sheet_name in handler_sheets:
                try:
                    self.logger.info(f"\n--- Processing sheet: {sheet_name} ---")
                    
                    # Extract handler name from sheet name
                    handler_name = sheet_name.replace("'s Cases", "").strip()
                    self.logger.info(f"Extracted handler name: '{handler_name}'")
                    
                    # CRITICAL: Always process ALL handler sheets to preserve work
                    # Selection status only affects NEW case assignment, not preservation
                    cleaned_handler = self.clean_handler_name(handler_name)
                    if cleaned_handler not in selected_handlers_set:
                        self.logger.info(f"Handler '{cleaned_handler}' not selected for NEW cases, but PRESERVING their existing work")
                    else:
                        self.logger.info(f"Handler '{cleaned_handler}' is selected - preserving existing work AND allowing new assignments")
                    
                    # Read the sheet
                    sheet_df = pd.read_excel(prev_file, sheet_name=sheet_name)
                    self.logger.info(f"Sheet columns: {list(sheet_df.columns)}")
                    self.logger.info(f"Sheet shape: {sheet_df.shape}")
                    
                    # Look for Case Number column (case insensitive)
                    case_col = None
                    for col in sheet_df.columns:
                        if 'case' in str(col).lower() and 'number' in str(col).lower():
                            case_col = col
                            break
                    
                    if case_col is None:
                        self.logger.warning(f"No Case Number column found in {sheet_name}")
                        continue
                    
                    self.logger.info(f"Using Case Number column: '{case_col}'")
                    
                    # Look for _Source_Sheet column (case insensitive) - CRITICAL FOR PRESERVATION
                    source_col = None
                    for col in sheet_df.columns:
                        if '_source_sheet' in str(col).lower() or '_Source_Sheet' in str(col):
                            source_col = col
                            break
                    
                    if source_col is None:
                        self.logger.warning(f"No _Source_Sheet column found in {sheet_name} - CRITICAL FOR PRESERVATION")
                        
                        # CRITICAL FIX: Only use fallback for selected handlers to prevent new case assignment
                        if cleaned_handler not in selected_handlers_set:
                            self.logger.warning(f"Handler '{cleaned_handler}' not selected - SKIPPING fallback assignment")
                            self.logger.warning(f"  This prevents unselected handlers from getting new cases through fallback logic")
                            self.logger.warning(f"  Ibrahim's existing cases will be preserved through other means")
                            continue
                        
                        # FALLBACK: Only for selected handlers - assume all cases in this sheet belong to this handler
                        self.logger.info(f"Using fallback for SELECTED handler: All cases in '{sheet_name}' will be assigned to '{cleaned_handler}'")
                        
                        # Process each row in the sheet using fallback logic
                        sheet_cases = 0
                        sheet_assignments = 0
                        
                        for idx, row in sheet_df.iterrows():
                            try:
                                # Get case number (case insensitive, handle NaN)
                                case_number_raw = row.get(case_col)
                                if pd.isna(case_number_raw):
                                    continue
                                
                                case_number = self.normalize_case_number(case_number_raw)
                                if not case_number:
                                    continue
                                
                                sheet_cases += 1
                                
                                # FALLBACK LOGIC: Case is in this sheet, so it belongs to this handler (selected handlers only)
                                # Store normalized case number to prevent .0 suffix issues
                                handler_sheet_assignments[case_number] = cleaned_handler
                                sheet_assignments += 1
                                total_assignments_loaded += 1
                                
                                self.logger.debug(f"  ✅ Case {case_number} -> {cleaned_handler} (fallback: sheet location)")
                                
                            except Exception as row_error:
                                self.logger.warning(f"Error processing row {idx} in {sheet_name}: {str(row_error)}")
                                continue
                        
                        self.logger.info(f"Sheet {sheet_name}: {sheet_cases} total cases, {sheet_assignments} assigned to {cleaned_handler} (fallback method)")
                        total_cases_found += sheet_cases
                        continue
                    
                    self.logger.info(f"Using _Source_Sheet column: '{source_col}'")
                    
                    # Process each row in the sheet
                    sheet_cases = 0
                    sheet_assignments = 0
                    sheet_skipped = 0
                    
                    for idx, row in sheet_df.iterrows():
                        try:
                            # Get case number (case insensitive, handle NaN)
                            case_number_raw = row.get(case_col)
                            if pd.isna(case_number_raw):
                                continue
                            
                            case_number = self.normalize_case_number(case_number_raw)
                            if not case_number:
                                continue
                            
                            # Get source sheet (case insensitive, handle NaN)
                            source_sheet_raw = row.get(source_col)
                            if pd.isna(source_sheet_raw):
                                continue
                            
                            source_sheet = str(source_sheet_raw).strip()
                            if not source_sheet:
                                continue
                            
                            sheet_cases += 1
                            
                            # CRITICAL LOGIC: Use _Source_Sheet to determine ownership
                            # If _Source_Sheet matches this sheet name, the case belongs to this handler
                            if source_sheet == sheet_name:
                                # This case belongs to this handler based on _Source_Sheet
                                handler_sheet_assignments[case_number] = cleaned_handler
                                sheet_assignments += 1
                                total_assignments_loaded += 1
                                
                                self.logger.debug(f"  ✅ Case {case_number} -> {cleaned_handler} (Source: {source_sheet})")
                            else:
                                # Case is in this sheet but _Source_Sheet says it belongs elsewhere
                                # This is important for debugging - cases shouldn't be in wrong sheets
                                sheet_skipped += 1
                                self.logger.warning(f"  ⚠️  Case {case_number} in sheet '{sheet_name}' but _Source_Sheet says '{source_sheet}'")
                                self.logger.warning(f"     This case will NOT be assigned to {cleaned_handler} - it belongs to {source_sheet}")
                                
                        except Exception as row_error:
                            self.logger.warning(f"Error processing row {idx} in {sheet_name}: {str(row_error)}")
                            continue
                    
                    self.logger.info(f"Sheet {sheet_name}: {sheet_cases} total cases, {sheet_assignments} assigned to {cleaned_handler}, {sheet_skipped} skipped")
                    total_cases_found += sheet_cases
                    
                except Exception as sheet_error:
                    self.logger.error(f"Error processing sheet {sheet_name}: {str(sheet_error)}")
                    continue
            
            self.logger.info(f"\n=== HANDLER SHEET ASSIGNMENTS V2 SUMMARY (IMPROVED) ===")
            self.logger.info(f"Total cases found across all sheets: {total_cases_found}")
            self.logger.info(f"Total assignments loaded: {total_assignments_loaded}")
            self.logger.info(f"Assignment success rate: {(total_assignments_loaded/total_cases_found*100):.1f}%" if total_cases_found > 0 else "N/A")
            
            # Log detailed assignment breakdown
            if handler_sheet_assignments:
                self.logger.info(f"\nDetailed assignments loaded:")
                for case_num, handler in sorted(handler_sheet_assignments.items())[:20]:  # Show first 20
                    self.logger.info(f"  {case_num} -> {handler}")
                if len(handler_sheet_assignments) > 20:
                    self.logger.info(f"  ... and {len(handler_sheet_assignments) - 20} more cases")
                
                # Log handler distribution
                handler_counts = {}
                for handler in handler_sheet_assignments.values():
                    handler_counts[handler] = handler_counts.get(handler, 0) + 1
                
                self.logger.info(f"\nHandler distribution from sheets:")
                for handler, count in sorted(handler_counts.items()):
                    self.logger.info(f"  {handler}: {count} cases")
            else:
                self.logger.warning("No assignments loaded from handler sheets!")
            
            return handler_sheet_assignments
            
        except Exception as e:
            self.logger.error(f"Error in _load_handler_sheet_assignments_v2: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return {}

    def _case_belongs_to_handler(self, row, handler_name, sheet_name):
        """Helper method to determine if a case belongs to a specific handler based on various indicators"""
        try:
            # Check if there are any other columns that might indicate handler assignment
            # This is a fallback method for cases where _Source_Sheet and _handler_name are not definitive
            
            # Look for any column containing the handler name
            for col_name, value in row.items():
                if pd.notna(value) and str(value).strip():
                    value_str = str(value).strip().lower()
                    handler_lower = handler_name.lower()
                    
                    # Check if the value contains the handler name
                    if handler_lower in value_str:
                        return True
                    
                    # Check if the value contains the sheet name (without "'s Cases")
                    sheet_base = sheet_name.replace("'s Cases", "").lower()
                    if sheet_base in value_str:
                        return True
            
            # If no clear indicators found, be conservative and return False
            return False
            
        except Exception as e:
            self.logger.debug(f"Error in _case_belongs_to_handler: {str(e)}")
            return False

    def _calculate_current_workload(self, df, handlers):
        """Calculate current workload (case count) per handler"""
        workload = {handler: 0 for handler in handlers}
        
        for handler in handlers:
            workload[handler] = len(df[df['Assigned To'] == handler])
        
        return workload

    def _get_company_column(self, df):
        """Helper method to find the company column"""
        for col in ['Company Name', 'Customer Name']:
            if col in df.columns:
                return col
        return None

    def clean_empty_rows(self, df):
        """Remove only completely empty rows while preserving all data"""
        try:
            before_count = len(df)
            
            # Check for completely empty rows (all columns empty or contain only whitespace/NaN/NaT)
            empty_mask = df.apply(lambda row: all(
                pd.isna(val) or str(val).strip() == '' or str(val).strip().lower() in ['nan', 'nat', 'none', 'null']
                for val in row
            ), axis=1)
            
            # Remove only completely empty rows
            df_cleaned = df[~empty_mask].copy()
            after_count = len(df_cleaned)
            
            removed_count = before_count - after_count
            if removed_count > 0:
                self.logger.info(f"Removed {removed_count} completely empty rows")
            else:
                self.logger.info("No completely empty rows found")
            
            # Final cleanup: replace any remaining NaN/NaT/None with empty strings
            df_cleaned = df_cleaned.fillna('').replace(['NaT', 'nan', 'None', 'null'], '')
            
            return df_cleaned
            
        except Exception as e:
            self.logger.error(f"Error cleaning empty rows: {str(e)}")
            return df

    def _ensure_fields_for_new_cases(self, df, new_cases):
        """Helper function to ensure required fields are populated for new cases"""
        try:
            new_cases_mask = df['Case Number'].isin(new_cases)
            
            # Define critical fields that must be populated for new cases
            critical_fields = {
                'Email': ['Primary Email (Contact) (Contact)', 'Primary Email', 'Contact Email', 'Email'],
                'Country': ['Country/Region (Contact) (Contact)', 'Country/Region', 'Country (Contact)', 'Country'],
                'State/Province': ['State/Province (Case) (Case)', 'State/Province (Case)', 'State/Province (Contact) (Contact)', 'State/Province (Contact)', 'State/Province'],
                'Case Status': ['Case Status (Case) (Case)', 'Case Status (Case)', 'Case Status'],
                'Last Status Change': ['Last Status Change (Workflow Use Only) (Case) (Case)', 'Last Status Change (Case)', 'Last Status Change'],
                'Customer Name': [' Contact Name (Contact) (Contact)', 'Contact Name', 'Contact Name (Contact)', 'Customer Name'],
                'Company Name': ['Company Name', 'Company Name (Contact) (Contact)', 'Company (Contact)'],
                'Status': ['Status']
            }
            
            # For each critical field
            for target_field, source_fields in critical_fields.items():
                # Ensure target field exists
                if target_field not in df.columns:
                    df[target_field] = ''
                
                # Check for empty values including NaN and whitespace
                empty_mask = df[target_field].fillna('').astype(str).str.strip() == ''
                update_mask = new_cases_mask & empty_mask
                
                if update_mask.any():
                    self.logger.info(f"Found {sum(update_mask)} empty {target_field} values in new cases")
                    # Try each source field in order until we find values
                    for source_field in source_fields:
                        if source_field in df.columns:
                            source_values = df.loc[update_mask, source_field].fillna('').astype(str).str.strip()
                            valid_values = source_values != ''
                            if valid_values.any():
                                # Update only where we have valid values
                                update_indices = update_mask[valid_values.index] & valid_values
                                df.loc[update_indices, target_field] = source_values[valid_values]
                                self.logger.info(f"Backfilled {sum(valid_values)} {target_field} values from {source_field}")
                                # Update the mask to exclude rows we just filled
                                update_mask = update_mask & ~valid_values
                                if not update_mask.any():
                                    self.logger.info(f"All {target_field} values have been populated")
                                    break
            
            return df
        except Exception as e:
            self.logger.error(f"Error in _ensure_fields_for_new_cases: {str(e)}")
            return df
    
    def merge_with_previous(self, new_df, prev_df):
        """Merge new data with previous file data while preserving all existing data and adding new cases.
        Additionally, backfill empty cells in previous/overlapping rows using values from the raw (new_df) by Case Number.
        Ensures critical fields (Email, Country, State/Province, etc.) are populated for new cases.
        """
        try:
            self.logger.info("\nMerging with previous file data...")
            
            # IMPORTANT: Convert Completion Date Timestamps to strings early
            if 'Completion Date' in new_df.columns:
                self.logger.info("Converting Completion Date Timestamps in new_df to strings...")
                
                # DIAGNOSTIC: Log BEFORE conversion
                completion_date_dtype = new_df['Completion Date'].dtype
                non_empty_before = (new_df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: Before conversion - dtype={completion_date_dtype}, non-empty={non_empty_before}/{len(new_df)}")
                samples_before = new_df['Completion Date'].head(3).tolist()
                self.logger.info(f"DIAGNOSTIC: Sample values before: {samples_before}")
                
                # Do the conversion
                new_df['Completion Date'] = new_df['Completion Date'].astype(str)
                self.logger.info("Completion Date in new_df converted to string format")
                
                # DIAGNOSTIC: Log AFTER conversion
                completion_date_dtype = new_df['Completion Date'].dtype
                non_empty_count = (new_df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: After conversion - dtype={completion_date_dtype}, non-empty={non_empty_count}/{len(new_df)}")
                if non_empty_count > 0:
                    samples = new_df[new_df['Completion Date'].fillna('').astype(str).str.strip() != '']['Completion Date'].head(3).tolist()
                    self.logger.info(f"DIAGNOSTIC: Sample values after (non-empty): {samples}")
                else:
                    samples_after = new_df['Completion Date'].head(3).tolist()
                    self.logger.info(f"DIAGNOSTIC: Sample values after (ALL): {samples_after}")
            
            if prev_df is None or prev_df.empty:
                self.logger.info("No previous file data to merge - using only new data")
                return new_df
            
            # Ensure Case Number columns are integer-normalized in both dataframes
            new_df = new_df.copy()
            prev_df = prev_df.copy()
            new_df['Case Number'] = new_df['Case Number'].apply(self.normalize_case_number)
            prev_df['Case Number'] = prev_df['Case Number'].apply(self.normalize_case_number)
            new_df['Case Number'] = pd.Series(pd.to_numeric(new_df['Case Number'], errors='coerce')).astype('Int64')
            prev_df['Case Number'] = pd.Series(pd.to_numeric(prev_df['Case Number'], errors='coerce')).astype('Int64')
            
            # Get case numbers from both dataframes
            new_case_numbers = set(new_df['Case Number'].dropna().tolist())
            prev_case_numbers = set(prev_df['Case Number'].dropna().tolist())
            
            # Identify overlapping and new cases
            overlapping_cases = new_case_numbers & prev_case_numbers
            new_cases = new_case_numbers - prev_case_numbers
            existing_only_cases = prev_case_numbers - new_case_numbers
            
            self.logger.info(f"Merge Summary:")
            self.logger.info(f"  New cases: {len(new_cases)}")
            self.logger.info(f"  Overlapping cases: {len(overlapping_cases)}")
            self.logger.info(f"  Existing only cases: {len(existing_only_cases)}")
            
            # Create a list to store rows in the correct order
            ordered_rows = []
            
            # Check if Completion Date exists in previous file
            completion_date_in_prev = 'Completion Date' in prev_df.columns
            self.logger.info(f"Completion Date in previous file: {completion_date_in_prev}")
            
            # Helper function to find matching column names for special fields
            def get_column_variants(field):
                if field not in self.canonical_fields:
                    return [field]
                return self.canonical_fields[field]
            
            # 1. Add NEW cases first (these are cases that don't exist in previous file)
            new_cases_df = new_df[new_df['Case Number'].isin(new_cases)]
            
            # DIAGNOSTIC: Log Completion Date state in new_cases_df
            if 'Completion Date' in new_cases_df.columns:
                non_empty_count = (new_cases_df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                self.logger.info(f"DIAGNOSTIC: new_cases_df has {non_empty_count}/{len(new_cases_df)} non-empty Completion Date values")
                if non_empty_count == 0:
                    self.logger.error(f"CRITICAL: All Completion Date values were lost when extracting new_cases_df!")
            
            if not new_cases_df.empty:
                # Handle special fields for new cases
                for field, variants in self.canonical_fields.items():
                    # SPECIAL HANDLING FOR COMPLETION DATE (NEW COLUMN ON FIRST RUN)
                    if field == 'Completion Date' and not completion_date_in_prev:
                        # Completion Date not in previous file - only populate new cases
                        self.logger.info("Completion Date column not in previous file - will populate only new cases")
                        target_col = field
                        if target_col not in new_cases_df.columns:
                            new_cases_df[target_col] = ''
                        
                        # Populate from variants (direct source columns)
                        for variant in variants:
                            if variant in new_cases_df.columns:
                                # Get non-empty values from raw file
                                non_empty_mask = (new_cases_df[variant].fillna('').astype(str).str.strip() != '')
                                if non_empty_mask.any():
                                    target_empty = (new_cases_df[target_col].fillna('').astype(str).str.strip() == '')
                                    update_mask = target_empty & non_empty_mask
                                    if update_mask.any():
                                        # Convert Timestamps to strings for Completion Date
                                        new_cases_df.loc[update_mask, target_col] = new_cases_df.loc[update_mask, variant].astype(str)
                                        self.logger.info(f"Completion Date: Populated {update_mask.sum()} new cases from raw file")
                                        sample_vals = new_cases_df.loc[update_mask, target_col].head(3).tolist()
                                        self.logger.info(f"Completion Date sample values: {sample_vals}")
                        continue  # Skip to next field
                    
                    target_col = field
                    
                    # Initialize the target column if it doesn't exist
                    if target_col not in new_cases_df.columns:
                        new_cases_df[target_col] = ''
                    
                    # Try to populate from variants, checking for actual non-empty data
                    for variant in variants:
                        if variant in new_cases_df.columns:
                            # Only copy non-empty values
                            non_empty_mask = (new_cases_df[variant].fillna('').astype(str).str.strip() != '')
                            if non_empty_mask.any():
                                # Copy only where target is empty and source has data
                                target_empty = (new_cases_df[target_col].fillna('').astype(str).str.strip() == '')
                                update_mask = target_empty & non_empty_mask
                                if update_mask.any():
                                    new_cases_df.loc[update_mask, target_col] = new_cases_df.loc[update_mask, variant]
                                    self.logger.debug(f"New cases: Populated {update_mask.sum()} {target_col} values from {variant}")
                
                # Ensure critical fields are populated for new cases
                new_cases_df = self._ensure_fields_for_new_cases(new_cases_df, new_cases)
                ordered_rows.append(new_cases_df)
                self.logger.info(f"Added {len(new_cases_df)} NEW cases at the top")
            
            # 2. Add OVERLAPPING cases (cases that exist in both files)
            # For overlapping cases, start from previous row, then fill any empty cells with new data values
            overlapping_rows = []
            for case_num in overlapping_cases:
                try:
                    new_row = new_df[new_df['Case Number'] == case_num].iloc[0]
                    prev_row = prev_df[prev_df['Case Number'] == case_num].iloc[0]
                    
                    # Start from previous row to preserve agent updates
                    merged_row = prev_row.copy()
                    
                    # Handle special fields that need merging
                    for field, variants in self.canonical_fields.items():
                        # SPECIAL HANDLING FOR COMPLETION DATE
                        if field == 'Completion Date':
                            # Initialize if not in previous row
                            if field not in merged_row.index:
                                merged_row[field] = ''
                            
                            # If Completion Date NOT in previous file, populate from new file for overlapping cases
                            if not completion_date_in_prev:
                                # This is an overlapping case where Completion Date column is new
                                # Populate from new file
                                for variant in variants:
                                    if variant in new_row.index:
                                        new_val = str(new_row[variant]).strip() if pd.notna(new_row[variant]) else ''
                                        if new_val:
                                            merged_row[field] = new_val
                                            self.logger.debug(f"Overlapping case {case_num}: Populated Completion Date from new file")
                                            break
                            else:
                                # Completion Date exists in previous file - preserve it
                                prev_val = str(merged_row[field]).strip() if pd.notna(merged_row[field]) else ''
                                # Don't overwrite - keep previous
                                merged_row[field] = prev_val
                            continue  # Skip to next field
                        
                        # Initialize if not in previous row (e.g., other new columns)
                        if field not in merged_row.index:
                            merged_row[field] = ''
                        
                        # Get value from previous file (preserve it)
                        prev_val = str(merged_row[field]).strip() if pd.notna(merged_row[field]) else ''
                        
                        # If previous doesn't have it, try to get from new file for new columns
                        if not prev_val:
                            for variant in variants:
                                if variant in new_row.index:
                                    new_val = str(new_row[variant]).strip() if pd.notna(new_row[variant]) else ''
                                    if new_val:
                                        merged_row[field] = new_val
                                        break
                        else:
                            merged_row[field] = prev_val
                    
                    # Handle all other columns
                    for col in new_df.columns:
                        if col not in merged_row.index and col not in self.canonical_fields:
                            merged_row[col] = ''
                        if pd.isna(merged_row[col]) or str(merged_row[col]).strip() == '':
                            new_val = new_row.get(col)
                            if pd.notna(new_val) and str(new_val).strip():
                                merged_row[col] = new_val
                    
                    overlapping_rows.append(merged_row)
                    
                except Exception as e:
                    self.logger.warning(f"Error processing overlapping case {case_num}: {str(e)}")
                    try:
                        fallback_prev = prev_df[prev_df['Case Number'] == case_num].iloc[0]
                        overlapping_rows.append(fallback_prev)
                    except Exception:
                        overlapping_rows.append(new_df[new_df['Case Number'] == case_num].iloc[0])
                    continue
            
            if overlapping_rows:
                overlapping_df = pd.DataFrame(overlapping_rows)
                # Ensure canonical fields are properly set and populated
                for field, variants in self.canonical_fields.items():
                    if field not in overlapping_df.columns:
                        overlapping_df[field] = ''
                    # Try to populate empty values from variants
                    empty_mask = overlapping_df[field].fillna('').astype(str).str.strip() == ''
                    if empty_mask.any():
                        for variant in variants:
                            if variant in overlapping_df.columns:
                                variant_values = overlapping_df.loc[empty_mask, variant].fillna('').astype(str).str.strip()
                                valid_values = variant_values != ''
                                if valid_values.any():
                                    overlapping_df.loc[empty_mask & valid_values.index.isin(overlapping_df.index), field] = variant_values[valid_values]
                                    empty_mask = empty_mask & ~valid_values
                                    if not empty_mask.any():
                                        break
                ordered_rows.append(overlapping_df)
                self.logger.info(f"Added {len(overlapping_df)} OVERLAPPING cases (updated with new data)")
            
            # 3. Add EXISTING cases (cases that only exist in previous file, in their original order)
            if existing_only_cases:
                # Get the original order from previous file
                prev_df_ordered = prev_df.copy()
                prev_df_ordered['_original_index'] = range(len(prev_df_ordered))
                
                # Filter to only include cases not in new data
                existing_only_df = prev_df_ordered[prev_df_ordered['Case Number'].isin(existing_only_cases)]
                
                # Sort by original index to maintain order
                existing_only_df = existing_only_df.sort_values('_original_index')
                existing_only_df = existing_only_df.drop(columns=['_original_index'])
                
                # Handle canonical fields for existing cases
                for field, variants in self.canonical_fields.items():
                    values_found = []
                    for variant in variants:
                        if variant in existing_only_df.columns:
                            non_empty_values = existing_only_df[variant].fillna('').astype(str).str.strip()
                            values_found.extend([(idx, val) for idx, val in non_empty_values.items() if val])
                    if values_found:
                        existing_only_df[field] = ''  # Initialize the canonical field
                        for idx, val in values_found:
                            existing_only_df.at[idx, field] = val
                
                # Ensure all new columns exist and are properly ordered
                for col in new_df.columns:
                    if col not in existing_only_df.columns and col not in self.canonical_fields:
                        existing_only_df[col] = ''
                
                ordered_rows.append(existing_only_df)
                self.logger.info(f"Added {len(existing_only_df)} EXISTING cases in their original order")
            
            # Combine all rows in the correct order
            if ordered_rows:
                merged_df = pd.concat(ordered_rows, ignore_index=True)
            else:
                merged_df = new_df.copy()
            
            # Ensure all canonical fields are present
            for field in self.canonical_fields.keys():
                if field not in merged_df.columns:
                    merged_df[field] = ''
            
            # Final data cleanup and verification
            for field, variants in self.canonical_fields.items():
                if field not in merged_df.columns:
                    continue
                    
                # Clean empty values
                merged_df[field] = merged_df[field].fillna('').astype(str).str.strip()
                
                # SPECIAL HANDLING FOR COMPLETION DATE - only populate new cases from raw data
                if field == 'Completion Date' and not completion_date_in_prev:
                    self.logger.info("Final cleanup: Completion Date not in previous file - only populating new cases")
                    new_cases_mask = merged_df['Case Number'].isin(new_cases)
                    empty_mask = merged_df[field] == ''
                    for variant in variants:
                        if variant in merged_df.columns:
                            update_mask = new_cases_mask & empty_mask
                            if update_mask.any():
                                variant_values = merged_df.loc[update_mask, variant].fillna('').astype(str).str.strip()
                                non_empty_mask = variant_values != ''
                                if non_empty_mask.any():
                                    merged_df.loc[update_mask & non_empty_mask, field] = variant_values[non_empty_mask]
                                    final_populated = (merged_df[field] != '').sum()
                                    self.logger.info(f"Final: Populated {sum(non_empty_mask)} empty Completion Date values from {variant} for new cases")
                                    self.logger.info(f"Total rows with Completion Date: {final_populated}/{len(merged_df)}")
                    continue  # Skip standard population logic for Completion Date
                
                # For new cases, ensure data is populated from variant columns if main field is empty
                new_cases_mask = merged_df['Case Number'].isin(new_cases)
                empty_mask = merged_df[field] == ''
                for variant in variants:
                    if variant in merged_df.columns:
                        update_mask = new_cases_mask & empty_mask
                        variant_values = merged_df.loc[update_mask, variant].fillna('').astype(str).str.strip()
                        non_empty_mask = variant_values != ''
                        if non_empty_mask.any():
                            merged_df.loc[update_mask & non_empty_mask, field] = variant_values[non_empty_mask]
                            self.logger.debug(f"Populated {sum(non_empty_mask)} empty {field} values from {variant}")
            
            # Drop duplicate variant columns and raw contact-related columns
            columns_to_drop = []
            
            # Drop variant columns from canonical fields
            for variants in self.canonical_fields.values():
                for variant in variants:
                    if variant in merged_df.columns and variant not in self.canonical_fields:
                        columns_to_drop.append(variant)
            
            # Drop any raw contact-related columns to prevent confusion
            contact_patterns = ['contact name', 'contact) (contact', 'Contact Name (Contact)', ' Contact Name (Contact) (Contact)']
            for col in merged_df.columns:
                if any(pattern in col.lower() for pattern in contact_patterns):
                    if col not in self.canonical_fields and col != 'Customer Name':
                        columns_to_drop.append(col)
            
            # Drop the columns and log what was removed
            if columns_to_drop:
                self.logger.info("Removing duplicate/raw columns:")
                for col in columns_to_drop:
                    self.logger.info(f"  - {col}")
                merged_df = merged_df.drop(columns=list(set(columns_to_drop)), errors='ignore')
            
            # Ensure proper column order and data types
            merged_df = merged_df.reset_index(drop=True)
            
            self.logger.info(f"\nMerge completed successfully:")
            self.logger.info(f"  Final merged DataFrame shape: {merged_df.shape}")
            self.logger.info(f"  New cases added first: {len(new_cases)}")
            self.logger.info(f"  Overlapping cases updated: {len(overlapping_cases)}")
            self.logger.info(f"  Existing cases preserved in order: {len(existing_only_cases)}")
            
            # Data quality checks
            self.logger.info("\nData Quality Summary:")
            for field in ['Customer Name', 'Email', 'Country', 'State/Province']:
                if field in merged_df.columns:
                    non_empty = (merged_df[field].fillna('').astype(str).str.strip() != '').sum()
                    self.logger.info(f"  {field}: {non_empty} non-empty values ({non_empty/len(merged_df)*100:.1f}%)")
            
            # Order verification
            if len(merged_df) > 0:
                first_new_case = merged_df.iloc[0]['Case Number']
                if first_new_case in new_cases:
                    self.logger.info(f"\nVERIFIED: First case is NEW: {first_new_case}")
                else:
                    self.logger.warning(f"⚠ WARNING: First case is NOT new: {first_new_case}")
                
                # Case distribution verification
                new_cases_in_output = merged_df[merged_df['Case Number'].isin(new_cases)]
                overlapping_cases_in_output = merged_df[merged_df['Case Number'].isin(overlapping_cases)]
                existing_cases_in_output = merged_df[merged_df['Case Number'].isin(existing_only_cases)]
                
                self.logger.info(f"\nCase Distribution Verification:")
                self.logger.info(f"  New cases in output: {len(new_cases_in_output)} (expected {len(new_cases)})")
                self.logger.info(f"  Overlapping cases: {len(overlapping_cases_in_output)} (expected {len(overlapping_cases)})")
                self.logger.info(f"  Existing cases: {len(existing_cases_in_output)} (expected {len(existing_only_cases)})")
                
                # Verify Completion Date population
                if 'Completion Date' in merged_df.columns:
                    completion_date_populated = (merged_df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                    self.logger.info(f"\nCompletion Date Verification:")
                    self.logger.info(f"  Total rows: {len(merged_df)}")
                    self.logger.info(f"  Populated Completion Dates: {completion_date_populated}")
                    self.logger.info(f"  Empty Completion Dates: {len(merged_df) - completion_date_populated}")
                    
                    # Check new cases specifically
                    new_cases_completion = (new_cases_in_output['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                    self.logger.info(f"  Completion Date in new cases: {new_cases_completion}/{len(new_cases_in_output)}")
                    if new_cases_completion > 0:
                        sample_completion = new_cases_in_output[new_cases_in_output['Completion Date'].fillna('').astype(str).str.strip() != '']['Completion Date'].head(3).tolist()
                        self.logger.info(f"  Sample Completion Date values: {sample_completion}")
            
            return merged_df
            
        except Exception as e:
            self.logger.error(f"Error in merge_with_previous: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            # Return new data if merge fails
            return new_df

    def _apply_bank_sutherland_rule(self, df, prev_case_numbers=None):
        """Set Action 1/2/3/Final Action/Status to Bank/Sutherland/closed for specific company names, but do NOT match 'citi' in 'citizen' or 'citizen group'.
        Only applies to new cases (not in prev_case_numbers) to preserve agent actions on previous cases."""
        # List of patterns (case-insensitive, partial match, with special handling for 'citi')
        patterns = [
            r"\bcitibank\b|\bcitigroup\b|\bciti group\b|\bciti bank\b|\bciti corp\b|\bciti\b",  # Citi, but not Citizen
            r"amgen",
            r"sanofi",
            r"bns|scotiabank|scotia bank|scotiabank canada|scotiaBank|bank of nova scotia|bank nova scotia",
            r"rbc|royal bank|royal bank of canada|rbc wealth management",
            r"hsbc",
            r"td bank"
        ]
        import re
        def matches_company(name):
            if not isinstance(name, str):
                return False
            name_lc = name.lower()
            # Special handling: skip if 'citizen' in name
            if 'citizen' in name_lc:
                return False
            return any(re.search(p, name_lc) for p in patterns)
        
        # Determine the company column in a flexible/canonical way
        company_col = self._get_company_column(df)
        # Additional fallbacks for variant names
        if company_col is None:
            for candidate in ['Company Name', 'Customer Name', 'company name', 'customer name']:
                if candidate in df.columns:
                    company_col = candidate
                    break

        # If still not found, create a canonical 'Company Name' column so downstream logic can rely on it
        if company_col is None:
            self.logger.warning("Company column not found; creating empty 'Company Name' column for Bank/Sutherland rule")
            df['Company Name'] = ''
            company_col = 'Company Name'

        # Ensure we operate on a clean string series for matching
        company_series = df[company_col].fillna('').astype(str)

        # Only apply to new cases (not in previous file)
        if prev_case_numbers is not None:
            # Create mask for new cases only using integer-normalized case numbers
            try:
                df['Case Number'] = df['Case Number'].apply(self.normalize_case_number).astype('Int64')
            except Exception:
                # If Case Number normalization fails, coerce to numeric as fallback
                df['Case Number'] = pd.Series(pd.to_numeric(df['Case Number'], errors='coerce')).astype('Int64')
            new_cases_mask = ~df['Case Number'].isin(prev_case_numbers)
            company_match_mask = company_series.apply(matches_company)
            # Combine masks: must be both a new case AND match company pattern
            mask = new_cases_mask & company_match_mask
            self.logger.info(f"Bank/Sutherland rule: Applied to {mask.sum()} new cases (out of {company_match_mask.sum()} total matching companies) using column '{company_col}'")
        else:
            # Fallback: apply to all cases if no previous case numbers provided
            mask = company_series.apply(matches_company)
            self.logger.info(f"Bank/Sutherland rule: Applied to {mask.sum()} cases (no previous case filter) using column '{company_col}'")
        
        # Store the updated cases for summary tracking
        if mask.sum() > 0:
            updated_cases = df[mask].copy()
            # Add to processing stats for summary
            if not hasattr(self, 'bank_sutherland_updated_cases'):
                self.bank_sutherland_updated_cases = []
            
            for idx, row in updated_cases.iterrows():
                case_number = str(row['Case Number']).strip()
                try:
                    company_name = str(row.get(company_col, '')).strip()
                except Exception:
                    company_name = ''
                self.bank_sutherland_updated_cases.append({
                    'case_number': case_number,
                    'company_name': company_name
                })
            
            # Debug logging for Bank/Sutherland tracking
            self.logger.info(f"Bank/Sutherland Debug - Updated {len(updated_cases)} cases")
            self.logger.info(f"Bank/Sutherland Debug - Tracking {len(self.bank_sutherland_updated_cases)} total cases")
            for case in self.bank_sutherland_updated_cases[-len(updated_cases):]:  # Show the latest ones
                self.logger.info(f"Bank/Sutherland Debug - Case: {case['case_number']}, Company: {case['company_name']}")
        
        for col in ['Action 1', 'Action 2', 'Action 3', 'Final Action']:
            df.loc[mask, col] = 'Bank/Sutherland'
        df.loc[mask, 'Status'] = 'closed'
        return df

    def format_output_data(self, df, prev_df=None):
        """Format the data according to the required output columns"""
        try:
            # Canonical column mapping for all input variants - MUST match self.output_columns names
            canonical_mapping = {
                'Case Number': ['Case Number'],
                'Work Order Type': ['Work Order Type'],
                'State/Province': ['State/Province (Case) (Case)', 'State/Province'],  # CRITICAL: Use exact output column name
                'Local Time': ['Local Time'],
                'Action 1': ['Action 1'],
                'Action 2': ['Action 2'],
                'Action 3': ['Action 3'],
                'Final Action': ['Final Action'],
                'Assigned To': ['Assigned To'],
                'Status': ['Status'],
                'Company Name': ['Company Name'],
                'DND (Do Not Disturb)': ['DND (Do Not Disturb)', 'Do Not Disturb (Contact) (Contact)'],
                'Email': ['Primary Email (Contact) (Contact)', 'Email'],  # CRITICAL: Use exact output column name
                'Phone Number': ['Contact Mobile Phone', 'Phone Number'],
                'Incoming Channel': ['Incoming Channel (Case) (Case)', 'Incoming Channel'],
                'Last Status Change': ['Last Status Change (Workflow Use Only) (Case) (Case)', 'Last Status Change'],
                'Country': ['Country/Region (Contact) (Contact)', 'Country'],  # CRITICAL: Use exact output column name
                'Customer Name': [' Contact Name (Contact) (Contact)', 'Contact Name', 'Contact Name (Contact)', 'Customer Name'],  # CRITICAL: Add Customer Name mapping
                'Case': ['Case'],
                'Problem Description': ['Problem Description (Case) (Case)', 'Problem Description'],
                'Case Status': ['Case Status (Case) (Case)', 'Case Status'],  # CRITICAL: Add Case Status mapping
                'Case Status Updated': ['Case status Updated (Case) (Case)', 'Case Status Updated'],
                'Case Reason': ['Case Reason (Case) (Case)', 'Case Reason'],
                'Work Order ID': ['Work Order ID'],
                'Work Order Status': ['Work Order Status'],
                'Order Type': ['Order Type'],
                'Work Order Priority': ['Work Order Priority'],
                'Product ID (MTM)': ['Product ID (MTM) (Case) (Case)', 'Product ID (MTM)'],
                'Machine Type': ['Machine Type'],
                'Product Description': ['Product Description'],
                'Serial Number': ['Serial Number (Case) (Case)', 'Serial Number'],
                'Created On': ['Created On'],
                'Survey Preference': ['Survey Preference (Case) (Case)', 'Survey Preference'],
                'Survey Fatigue': ['Survey Fatigue (Case) (Case)', 'Survey Fatigue'],
                'No survey reason': ['No survey reason (Case) (Case)', 'No survey reason'],
                'Program': ['Program (Case) (Case)', 'Program'],
                'Repeat Frequency': ['Repeat Frequency (Case) (Case)', 'Repeat Frequency'],
                'Repeat Repair': ['Repeat Repair'],
                'Closing Code': ['Closing Code'],
                'Reported Symptom': ['Reported Symptom'],
                'Completion Date': ['Completion Date']  # CRITICAL: Add Completion Date mapping
            }

            # Use self.output_columns as the desired output columns (defined at init)
            # This ensures consistency with expected output format
            desired_columns = list(self.output_columns) + ['_Source_Sheet']
            
            # Initialize input mapping (not really used but kept for backward compatibility)
            input_mapping = {
                # Fixed order columns first
                'Case Number': self.columns.get('case_number', 'Case Number'),
                'Work Order Type': 'Work Order Type',
                'State/Province': self.columns.get('state', 'State/Province (Case) (Case)'),
                
                # Then map all input columns
                'Country/Region (Contact) (Contact)': 'Country/Region (Contact) (Contact)',
                'Customer Name': [' Contact Name (Contact) (Contact)', 'Contact Name', 'Customer Name'],  # Map contact fields to Customer Name
                'Company Name': 'Company Name',
                'Primary Email (Contact) (Contact)': 'Primary Email (Contact) (Contact)',
                'Contact Mobile Phone': 'Contact Mobile Phone',
                'Case': 'Case',
                'Case Status (Case) (Case)': 'Case Status (Case) (Case)',
                'Last Status Change (Workflow Use Only) (Case) (Case)': 'Last Status Change (Workflow Use Only) (Case) (Case)',
                'Phone Number': self.columns.get('phone', 'Phone Number'),
                'Case Number': self.columns.get('case_number', 'Case Number'),
                'Case': self.columns.get('case', 'Case'),
                'Reported Symptom': self.columns.get('reported_symptom', 'Reported Symptom'),
                'Problem Description': self.columns.get('problem_description', 'Problem Description (Case) (Case)'),
                'Last Status Change': self.columns.get('last_status_change', 'Last Status Change'),
                'Case Status Updated': self.columns.get('case_status_updated', 'Case status Updated'),
                'Case Reason': self.columns.get('case_reason', 'Case Reason'),
                'Work Order ID': self.columns.get('wo_id', 'Work Order ID'),
                'Work Order Status': self.columns.get('wo_status', 'Work Order Status'),
                'Work Order Type': self.columns.get('wo_type', 'Work Order Type'),
                'Incoming Channel': self.columns.get('incoming_channel', 'Incoming Channel'),
                'Order Type': self.columns.get('order_type', 'Order Type'),
                'Work Order Priority': self.columns.get('wo_priority', 'Work Order Priority'),
                'Product ID (MTM)': self.columns.get('product_id', 'Product ID (MTM) (Case) (Case)'),
                'Machine Type': self.columns.get('machine_type', 'Machine Type'),
                'Product Description': self.columns.get('product_desc', 'Product Description'),
                'Serial Number': self.columns.get('serial', 'Serial Number'),
                'Created On': self.columns.get('created_on', 'Created On'),
                'Survey Preference': self.columns.get('survey_pref', 'Survey Preference'),
                'Survey Fatigue': self.columns.get('survey_fatigue', 'Survey Fatigue'),
                'No survey reason': self.columns.get('no_survey_reason', 'No survey reason'),
                'Program': self.columns.get('program', 'Program'),
                'Repeat Frequency': self.columns.get('repeat_freq', 'Repeat Frequency'),
                'Repeat Repair': self.columns.get('repeat_repair', 'Repeat Repair'),
                'Closing Code': self.columns.get('closing_code', 'Closing Code'),
                'DND (Do Not Disturb)': self.columns.get('dnd', 'Do Not Disturb'),
            }
            
            # Create a new DataFrame with the same index as the input DataFrame
            output_df = pd.DataFrame(index=df.index, columns=desired_columns)
            
            # Initialize all columns with empty strings
            for col in desired_columns:
                output_df[col] = ''
            
            # Copy data from source DataFrame to output DataFrame using canonical mapping
            for target_col, source_cols in canonical_mapping.items():
                found_col = None
                found_value = None
                
                # First pass: Look for exact matches in all source columns
                for source_col in source_cols:
                    if source_col in df.columns:
                        found_values = df[source_col].fillna('')
                        non_empty = found_values[found_values.astype(str).str.strip() != '']
                        if not non_empty.empty:
                            found_col = source_col
                            found_value = non_empty.iloc[0]  # Take first non-empty value
                            self.logger.debug(f"Found exact match for {target_col} in {source_col}")
                            break
                
                if found_col:
                    if target_col in ['Last Status Change', 'Created On', 'Completion Date'] and pd.notna(found_value) and hasattr(found_value, 'strftime'):
                        # Handle datetime values - date only format (no time)
                        output_df[target_col] = df[found_col].apply(
                            lambda x: x.strftime('%Y-%m-%d') if pd.notna(x) and hasattr(x, 'strftime') else str(x) if pd.notna(x) else ''
                        )
                    else:
                        output_df[target_col] = df[found_col].fillna('').astype(str)
                    
                    non_empty_count = (output_df[target_col] != '').sum()
                    self.logger.info(f"Mapped {found_col} -> {target_col}: {non_empty_count} non-empty values")
                    
                    # Special handling for DND and Problem Description in new cases
                    if target_col in ['DND (Do Not Disturb)', 'Problem Description']:
                        # Only update if we actually have data from raw input
                        raw_values = df[found_col].fillna('').astype(str).str.strip()
                        non_empty_raw = raw_values[raw_values != '']
                        if not non_empty_raw.empty:
                            # Log for each case that gets data from raw
                            for idx, val in non_empty_raw.items():
                                case_num = df.at[idx, 'Case Number']
                                if pd.notna(case_num):
                                    self.logger.debug(f"Set {target_col} for case {case_num} from raw input: '{val}'")
                    
                    # Add debug logging for merged fields
                    if found_col != target_col:  # Only log when a secondary name was used
                        sample_data = output_df[output_df[target_col] != '']
                        if not sample_data.empty:
                            sample_cases = sample_data['Case Number'].head(3).tolist()
                            self.logger.debug(f"Merged '{found_col}' into '{target_col}' for cases: {sample_cases}")
                    
                    # Add debug logging for merged fields
                    if found_col != target_col:  # Only log when a secondary name was used
                        sample_data = output_df[output_df[target_col] != '']
                        if not sample_data.empty:
                            sample_cases = sample_data['Case Number'].head(3).tolist()
                            self.logger.debug(f"Merged '{found_col}' into '{target_col}' for cases: {sample_cases}")
                    
                    # Special debugging for Incoming Channel
                    if target_col == 'Incoming Channel':
                        sample_values = output_df[target_col].head(5).tolist()
                        self.logger.info(f"Incoming Channel sample values: {sample_values}")
                    
                    # Special debugging for State/Province
                    if target_col == 'State/Province':
                        sample_values = output_df[target_col].head(5).tolist()
                        self.logger.info(f"State/Province sample values: {sample_values}")
                        # Additional debugging for State/Province
                        non_empty_count = (output_df[target_col].astype(str).str.strip() != '').sum()
                        self.logger.info(f"State/Province non-empty count: {non_empty_count} out of {len(output_df)}")
                        if non_empty_count > 0:
                            non_empty_values = output_df[target_col][output_df[target_col].astype(str).str.strip() != ''].head(10).tolist()
                            self.logger.info(f"State/Province non-empty values: {non_empty_values}")
                else:
                    self.logger.warning(f"None of the source columns {source_cols} found in input data")
                    # Special debugging for State/Province source column
                    if target_col == 'State/Province':
                        self.logger.error(f"State/Province source columns {source_cols} not found in input data")
                        self.logger.info(f"Available columns in input data: {df.columns.tolist()}")
                        # Check for similar column names
                        similar_cols = [col for col in df.columns if 'state' in col.lower() or 'province' in col.lower()]
                        if similar_cols:
                            self.logger.info(f"Found similar columns: {similar_cols}")
            
            # Add Local Time column (empty for later processing)
            output_df['Local Time'] = ''
            
            # Ensure _Source_Sheet exists for preservation logic
            if '_Source_Sheet' not in output_df.columns:
                output_df['_Source_Sheet'] = ''
                
            # Set initial Status while preserving previous statuses
            # Default all statuses to 'new'
            output_df['Status'] = 'new'
                
            # If we have previous data, preserve existing case statuses
            if prev_df is not None and not prev_df.empty and 'Status' in prev_df.columns:
                try:
                    # Normalize case numbers in both frames
                    output_df['_temp_case'] = output_df['Case Number'].apply(self.normalize_case_number)
                    prev_df['_temp_case'] = prev_df['Case Number'].apply(self.normalize_case_number)
                    
                    # Create mask for matching cases
                    for case_num in prev_df['_temp_case'].dropna().unique():
                        mask = (output_df['_temp_case'] == case_num)
                        if mask.any():
                            prev_status = prev_df.loc[prev_df['_temp_case'] == case_num, 'Status'].iloc[0]
                            output_df.loc[mask, 'Status'] = prev_status
                            self.logger.debug(f"Preserved Status '{prev_status}' for case {case_num}")
                    
                    # Clean up temp columns
                    output_df = output_df.drop(columns=['_temp_case'])
                    prev_df = prev_df.drop(columns=['_temp_case'])
                        
                except Exception as e:
                    self.logger.warning(f"Error preserving previous statuses: {str(e)}")
                    # Remove temp column if it exists
                    if '_temp_case' in output_df.columns:
                        output_df = output_df.drop(columns=['_temp_case'])
                    if '_temp_case' in prev_df.columns:
                        prev_df = prev_df.drop(columns=['_temp_case'])
            
            # Ensure all columns are strings and empty values are handled
            for col in output_df.columns:
                output_df[col] = output_df[col].fillna('').astype(str)
            
            # Debug: Show sample of formatted data
            self.logger.info(f"\nSample of formatted data (first 3 rows):")
            try:
                for idx, row in output_df.head(3).iterrows():
                    case_num = row.get('Case Number', 'N/A')
                    Customer_name = row.get(' Contact Name (Contact) (Contact)', 'N/A')
                    company = row.get('Company Name', 'N/A')
                    self.logger.info(f"Row {idx}: Case={case_num}, Contact={Customer_name}, Company={company}")
            except Exception as e:
                self.logger.warning(f"Error showing sample data: {str(e)}")

            # Add the previous data if available
            prev_case_numbers = set()
            if prev_df is not None and not prev_df.empty:
                # DIAGNOSTIC: Check Completion Date in output_df before filtering
                if 'Completion Date' in output_df.columns:
                    completion_date_non_empty = (output_df['Completion Date'].fillna('').astype(str).str.strip() != '').sum()
                    self.logger.info(f"DIAGNOSTIC format_output_data: Before filtering - Completion Date has {completion_date_non_empty}/{len(output_df)} non-empty values")
                    if completion_date_non_empty == 0:
                        self.logger.error(f"CRITICAL: Completion Date is empty in output_df BEFORE merge_with_previous!")
                else:
                    self.logger.error(f"CRITICAL: Completion Date column not in output_df at all!")
                
                for col in desired_columns:
                    if col not in prev_df.columns:
                        prev_df[col] = ''
                output_df = output_df[desired_columns]
                prev_df = prev_df[desired_columns]
                merged_df = self.merge_with_previous(output_df, prev_df)
                # Get previous case numbers for filtering rules
                prev_case_numbers = set(pd.Series(prev_df['Case Number']).apply(self.normalize_case_number).astype('Int64').dropna().tolist())
            else:
                merged_df = output_df

            # Create case number mask for new cases
            new_cases_mask = ~merged_df['Case Number'].apply(self.normalize_case_number).isin(prev_case_numbers)

            # Backfill important contact/company/location fields for NEW cases using values from the pre-merge output_df
            try:
                # Build a lookup from normalized Case Number -> value for each field from output_df
                out_lookup = output_df.copy()
                out_lookup['__norm_case'] = out_lookup['Case Number'].apply(self.normalize_case_number)
                out_lookup = out_lookup.set_index('__norm_case')

                fields_to_backfill = [
                    ('Email', ['Primary Email (Contact) (Contact)', 'Email', 'Contact Email']),
                    ('Phone Number', ['Contact Mobile Phone', 'Phone Number', 'Mobile Phone', 'Contact Phone']),
                    ('Country', ['Country/Region (Contact) (Contact)', 'Country/Region', 'Country (Contact)', 'Country']),
                    ('State/Province', ['State/Province (Case) (Case)', 'State/Province (Contact) (Contact)', 'State/Province (Case)', 'State/Province']),
                    ('Case Status', ['Case Status (Case) (Case)', 'Case Status (Case)', 'Case Status']),
                    ('Last Status Change', ['Last Status Change (Workflow Use Only) (Case) (Case)', 'Last Status Change (Case)', 'Last Status Change']),
                    ('Customer Name', [' Contact Name (Contact) (Contact)', 'Contact Name', 'Contact Name (Contact)', 'Customer Name']),
                    ('Company Name', ['Company Name', 'Company Name (Contact) (Contact)', 'Company (Contact)']),
                ]
                for field, source_fields in fields_to_backfill:
                    if field not in merged_df.columns:
                        merged_df[field] = ''  # Create the column if it doesn't exist
                    
                    # Rows that are new and currently empty for this field
                    empty_mask = merged_df[field].fillna('').astype(str).str.strip() == ''
                    to_fill_mask = new_cases_mask & empty_mask
                    if not to_fill_mask.any():
                        continue

                    # Try each source field in order
                    for source_field in source_fields:
                        if source_field in out_lookup.columns:
                            for idx in merged_df[to_fill_mask].index:
                                try:
                                    case_norm = self.normalize_case_number(merged_df.at[idx, 'Case Number'])
                                    if case_norm is not None and case_norm in out_lookup.index:
                                        val = out_lookup.at[case_norm, source_field]
                                        if pd.notna(val) and str(val).strip() != '':
                                            merged_df.at[idx, field] = str(val).strip()
                                            to_fill_mask.at[idx] = False  # Mark as filled
                                            self.logger.debug(f"Backfilled {field} for new case {case_norm} from {source_field}")
                                except Exception:
                                    continue
                            
                            if not to_fill_mask.any():  # Stop if all rows are filled
                                break

                    # For each row needing fill, try to lookup from out_lookup by normalized case
                    for idx in merged_df[to_fill_mask].index:
                        try:
                            case_norm = self.normalize_case_number(merged_df.at[idx, 'Case Number'])
                            if case_norm is None:
                                continue
                            if case_norm in out_lookup.index:
                                val = out_lookup.at[case_norm, field] if field in out_lookup.columns else ''
                                if pd.notna(val) and str(val).strip() != '':
                                    merged_df.at[idx, field] = str(val).strip()
                                    self.logger.debug(f"Backfilled {field} for new case {case_norm} from raw data")
                        except Exception:
                            continue
            except Exception as e:
                self.logger.debug(f"Error during backfill of important fields for new cases: {e}")
            
            # Set default DND value for new cases with empty DND
            if 'DND (Do Not Disturb)' in merged_df.columns:
                empty_dnd_mask = merged_df['DND (Do Not Disturb)'].fillna('').astype(str).str.strip() == ''
                new_empty_dnd_mask = new_cases_mask & empty_dnd_mask
                if new_empty_dnd_mask.any():
                    merged_df.loc[new_empty_dnd_mask, 'DND (Do Not Disturb)'] = 'No'
                    for case_num in merged_df.loc[new_empty_dnd_mask, 'Case Number']:
                        self.logger.debug(f"Set default DND='No' for new case {case_num}")

            # Check for empty Problem Description in new cases
            if 'Problem Description' in merged_df.columns:
                empty_desc_mask = merged_df['Problem Description'].fillna('').astype(str).str.strip() == ''
                new_empty_desc_mask = new_cases_mask & empty_desc_mask
                if new_empty_desc_mask.any():
                    for case_num in merged_df.loc[new_empty_desc_mask, 'Case Number']:
                        self.logger.debug(f"No Problem Description found for new case {case_num}")
            
            # Final verification of DND values
            if 'DND (Do Not Disturb)' in merged_df.columns:
                new_cases_no_dnd = merged_df[new_cases_mask & (merged_df['DND (Do Not Disturb)'].fillna('').astype(str).str.strip() == '')]
                if not new_cases_no_dnd.empty:
                    self.logger.warning(f"Found {len(new_cases_no_dnd)} new cases still missing DND value after setting defaults")
                    for _, row in new_cases_no_dnd.head(5).iterrows():
                        self.logger.warning(f"Case {row['Case Number']} missing DND value")
            # Apply Bank/Sutherland rule (only to new cases)
            self.logger.info("\n=== Applying Bank/Sutherland Rule ===")
            merged_df = self._apply_bank_sutherland_rule(merged_df, prev_case_numbers=prev_case_numbers)
            self.logger.info(f"Bank/Sutherland rule applied. Total cases tracked: {len(getattr(self, 'bank_sutherland_updated_cases', []))}")
            
            # Apply DND rule (only to new cases)
            self.logger.info("\n=== Applying DND Rule ===")
            merged_df = self._apply_dnd_actions_and_status(merged_df, prev_case_numbers=prev_case_numbers)
            self.logger.info(f"DND rule applied. Total cases tracked: {len(getattr(self, 'dnd_updated_cases', []))}")
            
            # CRITICAL DATA QUALITY CHECK for new cases
            if prev_df is not None and not prev_df.empty:
                self.logger.info("\n=== NEW CASES DATA QUALITY CHECK ===")
                new_cases_data = merged_df[new_cases_mask].copy()
                if not new_cases_data.empty:
                    for field in ['Customer Name', 'Email', 'Country', 'State/Province', 'Case Status']:
                        if field in new_cases_data.columns:
                            empty_count = (new_cases_data[field].fillna('').astype(str).str.strip() == '').sum()
                            if empty_count > 0:
                                self.logger.warning(f"WARNING: {empty_count} new cases missing {field}")
                                sample_missing = new_cases_data[new_cases_data[field].fillna('').astype(str).str.strip() == '']['Case Number'].head(5).tolist()
                                self.logger.warning(f"Sample cases missing {field}: {sample_missing}")
                else:
                    self.logger.info("No new cases found for data quality check")

            # FINAL VERIFICATION: Ensure the order is maintained after applying rules
            if prev_df is not None and not prev_df.empty:
                self.logger.info("\n=== FINAL ORDER VERIFICATION ===")
                
                # Get the case numbers in order from the final output
                final_case_numbers = pd.Series(merged_df['Case Number']).apply(self.normalize_case_number).astype('Int64').dropna().tolist()
                
                # Count how many new cases are at the top
                new_cases_at_top = 0
                for case_num in final_case_numbers:
                    if case_num not in prev_case_numbers:
                        new_cases_at_top += 1
                    else:
                        break  # Stop counting when we hit the first previous case
                
                self.logger.info(f"New cases at the top: {new_cases_at_top}")
                
                # Verify that new cases are actually at the top
                if new_cases_at_top > 0:
                    first_new_case = merged_df.iloc[0]['Case Number']
                    if first_new_case not in prev_case_numbers:
                        self.logger.info(f"SUCCESS: First case is NEW: {first_new_case}")
                    else:
                        self.logger.error(f"❌ ERROR: First case is NOT new: {first_new_case}")
                    
                    # Show the first few cases to verify order
                    first_10_cases = merged_df.head(10)['Case Number'].tolist()
                    self.logger.info(f"First 10 cases in final output: {first_10_cases}")
                    
                    # Count new vs previous cases in first 10
                    new_in_first_10 = sum(1 for case in first_10_cases if case not in prev_case_numbers)
                    prev_in_first_10 = sum(1 for case in first_10_cases if case in prev_case_numbers)
                    self.logger.info(f"First 10 breakdown: {new_in_first_10} new, {prev_in_first_10} previous")
                else:
                    self.logger.warning("⚠ WARNING: No new cases found at the top of the output")
            
            # Verify the output
            self.logger.info(f"\nOutput DataFrame created with {len(merged_df)} rows")
            self.logger.info(f"Columns in order: {merged_df.columns.tolist()}")
            
            # Debug: Check if State/Province column exists in final output
            if 'State/Province' in merged_df.columns:
                self.logger.info(f"State/Province column found at position {merged_df.columns.get_loc('State/Province') + 1}")
                state_count = (merged_df['State/Province'].astype(str).str.strip() != '').sum()
                self.logger.info(f"State/Province non-empty count in final output: {state_count} out of {len(merged_df)}")
            else:
                self.logger.error("CRITICAL ERROR: State/Province column is missing from final output!")
                self.logger.error(f"Available columns: {merged_df.columns.tolist()}")
            
                # CRITICAL FINAL VERIFICATION: Ensure State/Province column is present and has data
                state_province_col = 'State/Province (Case) (Case)'  # Use full column name
                if state_province_col in merged_df.columns:
                    final_state_count = (merged_df[state_province_col].astype(str).str.strip() != '').sum()
                    self.logger.info(f"Final State/Province non-empty count: {final_state_count} out of {len(merged_df)}")
                    if final_state_count > 0:
                        final_states = merged_df[state_province_col][merged_df[state_province_col].astype(str).str.strip() != ''].head(10).tolist()
                        self.logger.info(f"Final State/Province sample values: {final_states}")
                    else:
                        self.logger.warning("WARNING: No State/Province data found in final output!")
                else:
                    self.logger.error("CRITICAL ERROR: State/Province column missing from final output!")
                    # Emergency fix: add State/Province column after Country/Region
                    country_col = 'Country/Region (Contact) (Contact)'  # Use full column name
                    try:
                        # First try to add after Country/Region
                        merged_df.insert(merged_df.columns.get_loc(country_col) + 1, state_province_col, '')
                        self.logger.info("Emergency fix: Added State/Province column after Country/Region")
                    except (KeyError, ValueError):
                        # If Country/Region not found, add as third column (after Work Order Type)
                        merged_df.insert(2, state_province_col, '')
                        self.logger.info("Emergency fix: Added State/Province column as third column")
                
            # Filter to only include expected output columns (remove unwanted columns like "Unnamed: 18", "Contact Name", etc.)
            self.logger.info(f"\n=== FILTERING FINAL OUTPUT COLUMNS ===")
            self.logger.info(f"Before filtering: {len(merged_df.columns)} columns")
            self.logger.info(f"Columns before filtering: {merged_df.columns.tolist()}")
            
            final_columns = list(self.output_columns)
            if '_Source_Sheet' in merged_df.columns:
                final_columns.append('_Source_Sheet')
            
            # Get only columns that exist in merged_df
            available_final_columns = [col for col in final_columns if col in merged_df.columns]
            
            # Filter merged_df to only include these columns (in the correct order)
            merged_df = merged_df[available_final_columns]
            
            self.logger.info(f"After filtering: {len(merged_df.columns)} columns")
            self.logger.info(f"Final output columns: {merged_df.columns.tolist()}")
            
            # Check for any unwanted columns that might have sneaked in
            unwanted_columns = [col for col in merged_df.columns if col not in final_columns and col != '_Source_Sheet']
            if unwanted_columns:
                self.logger.warning(f"WARNING: Found unwanted columns in final output: {unwanted_columns}")
                # Remove them
                merged_df = merged_df[[col for col in merged_df.columns if col in final_columns or col == '_Source_Sheet']]
                self.logger.info(f"Removed unwanted columns. Final count: {len(merged_df.columns)}")
            
            return merged_df
        except Exception as e:
            self.logger.error(f"Error in format_output_data: {str(e)}")
            self.logger.error(f"Input DataFrame shape: {df.shape}")
            self.logger.error(f"Input DataFrame columns: {df.columns.tolist()}")
            raise

    def _apply_dnd_actions_and_status(self, df, prev_case_numbers=None):
        """After merging, if the 'DND (Do Not Disturb)' column is 'Yes' for any case, set Action 1, Action 2, Action 3, and Final Action to 'DND', and Status to 'closed' for that row.
        Only applies to new cases (not in prev_case_numbers) to preserve agent actions on previous cases."""
        dnd_col = 'DND (Do Not Disturb)'
        if dnd_col in df.columns:
            dnd_mask = df[dnd_col].astype(str).str.strip().str.lower() == 'yes'
            
            # Only apply to new cases (not in previous file)
            if prev_case_numbers is not None:
                # Create mask for new cases only using integer-normalized case numbers
                df['Case Number'] = df['Case Number'].apply(self.normalize_case_number).astype('Int64')
                new_cases_mask = ~df['Case Number'].isin(prev_case_numbers)
                # Combine masks: must be both a new case AND have DND = 'Yes'
                mask = new_cases_mask & dnd_mask
                self.logger.info(f"DND rule: Applied to {mask.sum()} new cases (out of {dnd_mask.sum()} total DND cases)")
            else:
                # Fallback: apply to all cases if no previous case numbers provided
                mask = dnd_mask
                self.logger.info(f"DND rule: Applied to {mask.sum()} cases (no previous case filter)")
            
            # Store the updated cases for summary tracking
            if mask.sum() > 0:
                updated_cases = df[mask].copy()
                # Add to processing stats for summary
                if not hasattr(self, 'dnd_updated_cases'):
                    self.dnd_updated_cases = []
                
                for idx, row in updated_cases.iterrows():
                    case_number = str(row['Case Number']).strip()
                    self.dnd_updated_cases.append({
                        'case_number': case_number,
                        'source': 'DND rule'
                    })
                
                # Debug logging for DND tracking
                self.logger.info(f"DND Debug - Updated {len(updated_cases)} cases")
                self.logger.info(f"DND Debug - Tracking {len(self.dnd_updated_cases)} total cases")
                for case in self.dnd_updated_cases[-len(updated_cases):]:  # Show the latest ones
                    self.logger.info(f"DND Debug - Case: {case['case_number']}, Source: {case['source']}")
            
            for action_col in ['Action 1', 'Action 2', 'Action 3', 'Final Action']:
                if action_col in df.columns:
                    df.loc[mask, action_col] = 'DND'
            if 'Status' in df.columns:
                df.loc[mask, 'Status'] = 'closed'
        return df

    def _force_additional_balancing(self, df, handlers, prev_assignments):
        """Force additional balancing to achieve much more even distribution"""
        try:
            self.logger.info("Starting additional balancing for fairer distribution...")
            
            # Work on a copy to avoid corrupting the original
            df_copy = df.copy()
            
            # Ensure preserved assignments are maintained
            for idx, row in df_copy.iterrows():
                case_num = self.normalize_case_number(row['Case Number'])
                if case_num is not None and case_num in prev_assignments:
                    df_copy.at[idx, 'Assigned To'] = prev_assignments[case_num]
            
            # Calculate current workload
            current_workload = {}
            for handler in handlers:
                count = len(df_copy[df_copy['Assigned To'] == handler])
                current_workload[handler] = count
            
            self.logger.info(f"Current workload before additional balancing: {current_workload}")
            
            # Find handlers that are significantly overloaded and underloaded
            avg_workload = sum(current_workload.values()) / len(current_workload)
            overloaded_threshold = avg_workload * 1.15  # 15% above average
            underloaded_threshold = avg_workload * 0.85  # 15% below average
            
            overloaded_handlers = [h for h, w in current_workload.items() if w > overloaded_threshold]
            underloaded_handlers = [h for h, w in current_workload.items() if w < underloaded_threshold]
            
            self.logger.info(f"Overloaded handlers (> {overloaded_threshold:.1f}): {overloaded_handlers}")
            self.logger.info(f"Underloaded handlers (< {underloaded_threshold:.1f}): {underloaded_handlers}")
            
            # Move cases from overloaded to underloaded handlers (ONLY NEW CASES)
            moved_count = 0
            
            for overloaded_handler in overloaded_handlers:
                if not underloaded_handlers:
                    break
                
                # Find ONLY NEW cases assigned to this overloaded handler
                new_cases_mask = ~df_copy['Case Number'].isin(prev_assignments)
                overloaded_cases = df_copy[(df_copy['Assigned To'] == overloaded_handler) & new_cases_mask]
                
                self.logger.info(f"Found {len(overloaded_cases)} new cases for {overloaded_handler} that can be moved")
                
                if not overloaded_cases.empty:
                    # Sort cases by company to maintain consistency
                    company_col = self._get_company_column(df_copy)
                    if company_col and company_col in df_copy.columns:
                        overloaded_cases['Company_Lower'] = overloaded_cases[company_col].fillna('').astype(str).str.strip().str.lower()
                        overloaded_cases = overloaded_cases.sort_values('Company_Lower')
                    
                    # Move cases to underloaded handlers
                    for idx, row in overloaded_cases.iterrows():
                        if not underloaded_handlers:
                            break
                        
                        # Find the most underloaded handler
                        target_handler = min(underloaded_handlers, key=lambda h: current_workload[h])
                        
                        # Only move if it's not in previous assignments
                        case_num = self.normalize_case_number(row['Case Number'])
                        if case_num is not None and case_num in prev_assignments:
                            continue
                        
                        # Move the case
                        old_handler = df_copy.at[idx, 'Assigned To']
                        df_copy.at[idx, 'Assigned To'] = target_handler
                        current_workload[overloaded_handler] -= 1
                        current_workload[target_handler] += 1
                        moved_count += 1
                        
                        self.logger.info(f"Moved case {case_num} from {old_handler} to {target_handler}")
                        
                        # Remove target handler if it's no longer underloaded
                        if current_workload[target_handler] >= underloaded_threshold:
                            underloaded_handlers.remove(target_handler)
                            self.logger.info(f"Handler {target_handler} no longer underloaded, removing from list")
                        
                        # Update the workload tracking
                        self.logger.debug(f"Updated workload: {current_workload}")
            
            self.logger.info(f"Additional balancing completed: {moved_count} cases moved")
            
            # Verify that no preserved assignments were corrupted
            preserved_corrupted = []
            for idx, row in df_copy.iterrows():
                case_num = self.normalize_case_number(row['Case Number'])
                if case_num is not None and case_num in prev_assignments:
                    expected_handler = prev_assignments[case_num]
                    actual_handler = row['Assigned To']
                    if expected_handler != actual_handler:
                        preserved_corrupted.append((case_num, expected_handler, actual_handler))
            
            if preserved_corrupted:
                self.logger.error(f"CRITICAL ERROR: {len(preserved_corrupted)} preserved assignments corrupted during additional balancing!")
                for case_num, expected, actual in preserved_corrupted:
                    self.logger.error(f"  {case_num}: expected {expected}, got {actual}")
                    # Restore immediately
                    case_idx = df_copy[df_copy['Case Number'] == case_num].index
                    if len(case_idx) > 0:
                        df_copy.at[case_idx[0], 'Assigned To'] = expected
                        self.logger.info(f"Immediately restored corrupted assignment: {case_num} -> {expected}")
            else:
                self.logger.info("SUCCESS: All preserved assignments maintained during additional balancing")
            
            # Final workload calculation
            final_workload = {}
            for handler in handlers:
                count = len(df_copy[df_copy['Assigned To'] == handler])
                final_workload[handler] = count
            
            self.logger.info(f"Final workload after additional balancing: {final_workload}")
            
            return df_copy
            
        except Exception as e:
            self.logger.error(f"Error in additional balancing: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return df

    def _force_gentle_rebalancing(self, df, handlers, prev_assignments):
        """Force additional balancing to achieve much more even distribution"""
        try:
            self.logger.info("Starting additional balancing for fairer distribution...")
            
            # Work on a copy to avoid corrupting the original
            df_copy = df.copy()
            
            # Ensure preserved assignments are maintained
            for idx, row in df_copy.iterrows():
                case_num = self.normalize_case_number(row['Case Number'])
                if case_num is not None and case_num in prev_assignments:
                    df_copy.at[idx, 'Assigned To'] = prev_assignments[case_num]
            
            # Calculate current workload
            current_workload = {}
            for handler in handlers:
                count = len(df_copy[df_copy['Assigned To'] == handler])
                current_workload[handler] = count
            
            self.logger.info(f"Current workload before additional balancing: {current_workload}")
            
            # Find handlers that are significantly overloaded and underloaded
            avg_workload = sum(current_workload.values()) / len(current_workload)
            overloaded_threshold = avg_workload * 1.15  # 15% above average
            underloaded_threshold = avg_workload * 0.85  # 15% below average
            
            overloaded_handlers = [h for h, w in current_workload.items() if w > overloaded_threshold]
            underloaded_handlers = [h for h, w in current_workload.items() if w < underloaded_threshold]
            
            self.logger.info(f"Overloaded handlers (> {overloaded_threshold:.1f}): {overloaded_handlers}")
            self.logger.info(f"Underloaded handlers (< {underloaded_threshold:.1f}): {underloaded_handlers}")
            
            # Move cases from overloaded to underloaded handlers (ONLY NEW CASES)
            moved_count = 0
            
            for overloaded_handler in overloaded_handlers:
                if not underloaded_handlers:
                    break
                
                # Find ONLY NEW cases assigned to this overloaded handler
                new_cases_mask = ~df_copy['Case Number'].isin(prev_assignments)
                overloaded_cases = df_copy[(df_copy['Assigned To'] == overloaded_handler) & new_cases_mask]
                
                self.logger.info(f"Found {len(overloaded_cases)} new cases for {overloaded_handler} that can be moved")
                
                if not overloaded_cases.empty:
                    # Sort cases by company to maintain consistency
                    company_col = self._get_company_column(df_copy)
                    if company_col and company_col in df_copy.columns:
                        overloaded_cases['Company_Lower'] = overloaded_cases[company_col].fillna('').astype(str).str.strip().str.lower()
                        overloaded_cases = overloaded_cases.sort_values('Company_Lower')
                    
                    # Move cases to underloaded handlers
                    for idx, row in overloaded_cases.iterrows():
                        if not underloaded_handlers:
                            break
                        
                        # Find the most underloaded handler
                        target_handler = min(underloaded_handlers, key=lambda h: current_workload[h])
                        
                        # Only move if it's not in previous assignments
                        case_num = self.normalize_case_number(row['Case Number'])
                        if case_num is not None and case_num in prev_assignments:
                            continue
                        
                        # Move the case
                        old_handler = df_copy.at[idx, 'Assigned To']
                        df_copy.at[idx, 'Assigned To'] = target_handler
                        current_workload[overloaded_handler] -= 1
                        current_workload[target_handler] += 1
                        moved_count += 1
                        
                        self.logger.info(f"Moved case {case_num} from {old_handler} to {target_handler}")
                        
                        # Remove target handler if it's no longer underloaded
                        if current_workload[target_handler] >= underloaded_threshold:
                            underloaded_handlers.remove(target_handler)
                            self.logger.info(f"Handler {target_handler} no longer underloaded, removing from list")
                        
                        # Update the workload tracking
                        self.logger.debug(f"Updated workload: {current_workload}")
            
            self.logger.info(f"Additional balancing completed: {moved_count} cases moved")
            
            # Verify that no preserved assignments were corrupted
            preserved_corrupted = []
            for idx, row in df_copy.iterrows():
                case_num = self.normalize_case_number(row['Case Number'])
                if case_num is not None and case_num in prev_assignments:
                    expected_handler = prev_assignments[case_num]
                    actual_handler = row['Assigned To']
                    if expected_handler != actual_handler:
                        preserved_corrupted.append((case_num, expected_handler, actual_handler))
            
            if preserved_corrupted:
                self.logger.error(f"CRITICAL ERROR: {len(preserved_corrupted)} preserved assignments corrupted during additional balancing!")
                for case_num, expected, actual in preserved_corrupted:
                    self.logger.error(f"  {case_num}: expected {expected}, got {actual}")
                    # Restore immediately
                    case_idx = df_copy[df_copy['Case Number'] == case_num].index
                    if len(case_idx) > 0:
                        df_copy.at[case_idx[0], 'Assigned To'] = expected
                        self.logger.info(f"Immediately restored corrupted assignment: {case_num} -> {expected}")
            else:
                self.logger.info("SUCCESS: All preserved assignments maintained during additional balancing")
            
            # Final workload calculation
            final_workload = {}
            for handler in handlers:
                count = len(df_copy[df_copy['Assigned To'] == handler])
                final_workload[handler] = count
            
            self.logger.info(f"Final workload after additional balancing: {final_workload}")
            
            return df_copy
            
        except Exception as e:
            self.logger.error(f"Error in additional balancing: {str(e)}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            return df


