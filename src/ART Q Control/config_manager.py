"""
ART Configuration Manager
========================
This module manages user credentials and configuration caching using JSON.

Functionality:
1. Checks if config.json exists in the user's home directory
2. If exists: Loads cached credentials and shows confirmation popup
3. If missing: Shows input popup for all required credentials, then caches them
4. Hides config.json file using Windows attributes (hidden flag)
5. Provides easy variable access throughout the application

Usage Example:
    from config_manager import ConfigManager
    
    # Initialize and load/create config
    config = ConfigManager()
    
    # Access variables directly
    dialer_username = config.dialer_username
    dialer_password = config.dialer_password
    dialer_place_id = config.dialer_place_id
    agent_name = config.agent_name
    
    # Or get all as dictionary
    all_config = config.get_all_config()
"""

import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox
import ctypes
import sys
from pathlib import Path


class ConfigManager:
    """
    Manages application configuration with JSON file caching.
    
    Features:
    - Automatic config file detection
    - Popup-based credential input
    - Windows file hiding (hidden attribute)
    - Validation and error handling
    """
    
    def __init__(self, config_filename="art_config.json"):
        """
        Initialize ConfigManager.
        
        Args:
            config_filename (str): Name of the config file (stored in home directory)
        """
        self.config_filename = config_filename
        self.config_path = Path.home() / config_filename
        
        # Initialize attributes with None
        self.dialer_username = None
        self.dialer_password = None
        self.dialer_place_id = None
        self.agent_name = None
        
        # Load or create config
        self._initialize_config()
    
    def _initialize_config(self):
        """
        Initialize configuration by checking if file exists.
        If exists: Load and show confirmation
        If missing: Get user input and save
        """
        if self.config_path.exists():
            self._load_from_cache()
        else:
            self._get_user_input()
    
    def _load_from_cache(self):
        """
        Load credentials from existing JSON cache file.
        Validates that all required fields are present.
        """
        try:
            with open(self.config_path, 'r') as file:
                config_data = json.load(file)
            
            # Validate all required keys exist
            required_keys = ['dialer_username', 'dialer_password', 'dialer_place_id', 'agent_name']
            missing_keys = [key for key in required_keys if key not in config_data]
            
            if missing_keys:
                print(f"[WARN] Missing keys in config: {missing_keys}")
                self._get_user_input()
                return
            
            # Assign values from cache
            self.dialer_username = config_data['dialer_username']
            self.dialer_password = config_data['dialer_password']
            self.dialer_place_id = config_data['dialer_place_id']
            self.agent_name = config_data['agent_name']
            
            # Show success popup
            self._show_cached_data_popup()
            print("[INFO] Configuration loaded from cache successfully")
            
        except json.JSONDecodeError:
            print("[ERROR] Config file is corrupted. Getting new input...")
            self._get_user_input()
        except Exception as e:
            print(f"[ERROR] Failed to load config: {e}")
            self._get_user_input()
    
    def _get_user_input(self):
        """
        Show a single popup window with all credential input fields.
        Validates input and saves to cache.
        """
        from tkinter import ttk
        
        # Create root window
        root = tk.Tk()
        root.title("ART Configuration Setup")
        root.geometry("500x350")
        root.resizable(False, False)
        
        # Center window on screen
        root.update_idletasks()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width // 2) - (500 // 2)
        y = (screen_height // 2) - (350 // 2)
        root.geometry(f"+{x}+{y}")
        
        # Variables to store input
        result = {"success": False}
        
        try:
            # Main frame
            main_frame = ttk.Frame(root, padding="20")
            main_frame.pack(fill="both", expand=True)
            
            # Title
            title_label = ttk.Label(
                main_frame,
                text="Configuration Setup",
                font=("Arial", 14, "bold")
            )
            title_label.pack(pady=(0, 10))
            
            # Info text
            info_label = ttk.Label(
                main_frame,
                text="Configuration file not found.\nPlease enter your credentials.\nThese will be saved for future use.",
                font=("Arial", 9),
                justify="center"
            )
            info_label.pack(pady=(0, 15))
            
            # Create frame for form fields
            form_frame = ttk.Frame(main_frame)
            form_frame.pack(fill="both", expand=True, pady=10)
            
            # Agent Name
            ttk.Label(form_frame, text="Agent Name:", font=("Arial", 9)).grid(row=0, column=0, sticky="w", pady=5)
            agent_name_var = tk.StringVar()
            agent_name_entry = tk.Entry(form_frame, textvariable=agent_name_var, width=35, font=("Arial", 9))
            agent_name_entry.grid(row=0, column=1, sticky="ew", pady=5)
            
            # Dialer Username
            ttk.Label(form_frame, text="Dialer Username:", font=("Arial", 9)).grid(row=1, column=0, sticky="w", pady=5)
            username_var = tk.StringVar()
            username_entry = tk.Entry(form_frame, textvariable=username_var, width=35, font=("Arial", 9))
            username_entry.grid(row=1, column=1, sticky="ew", pady=5)
            
            # Dialer Password
            ttk.Label(form_frame, text="Dialer Password:", font=("Arial", 9)).grid(row=2, column=0, sticky="w", pady=5)
            password_var = tk.StringVar()
            password_entry = tk.Entry(form_frame, textvariable=password_var, width=35, font=("Arial", 9), show="*")
            password_entry.grid(row=2, column=1, sticky="ew", pady=5)
            
            # Dialer Place ID
            ttk.Label(form_frame, text="Dialer Place ID:", font=("Arial", 9)).grid(row=3, column=0, sticky="w", pady=5)
            place_id_var = tk.StringVar()
            place_id_entry = tk.Entry(form_frame, textvariable=place_id_var, width=35, font=("Arial", 9))
            place_id_entry.grid(row=3, column=1, sticky="ew", pady=5)
            
            # Placeholder text and behavior
            placeholders = {
                agent_name_entry: "Signature Name",
                username_entry: "Agent_Cairo_US_XXX",
                place_id_entry: "Place_XXXXX_SIPSwitch_US"
            }
            
            def setup_placeholder(entry, placeholder_text):
                """Setup placeholder for an entry field"""
                entry.insert(0, placeholder_text)
                entry.config(fg="grey")
                
                def on_focus_in(event):
                    if entry.get() == placeholder_text:
                        entry.delete(0, tk.END)
                        entry.config(fg="black")
                
                def on_focus_out(event):
                    if entry.get() == "":
                        entry.insert(0, placeholder_text)
                        entry.config(fg="grey")
                
                entry.bind("<FocusIn>", on_focus_in)
                entry.bind("<FocusOut>", on_focus_out)
            
            # Apply placeholders to all fields
            for entry, placeholder in placeholders.items():
                setup_placeholder(entry, placeholder)
            
            # Configure grid column width
            form_frame.columnconfigure(1, weight=1)
            
            # Button frame
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=15)
            
            def on_submit():
                """Validate and submit the form"""
                agent_name = agent_name_var.get().strip()
                username = username_var.get().strip()
                password = password_var.get().strip()
                place_id = place_id_var.get().strip()
                
                # Remove placeholder text if it's still there
                placeholder_map = {
                    "e.g., Adam Maged": "",
                    "e.g., Agent_Cairo_US_920": "",
                    "e.g., Place_57078_SIPSwitch_US": ""
                }
                
                if agent_name in placeholder_map:
                    agent_name = ""
                if username in placeholder_map:
                    username = ""
                if place_id in placeholder_map:
                    place_id = ""
                
                # Validate all fields
                if not agent_name:
                    messagebox.showerror("Validation Error", "Agent Name is required")
                    return
                if not username:
                    messagebox.showerror("Validation Error", "Dialer Username is required")
                    return
                if not password:
                    messagebox.showerror("Validation Error", "Dialer Password is required")
                    return
                if not place_id:
                    messagebox.showerror("Validation Error", "Dialer Place ID is required")
                    return
                
                # Assign values
                self.agent_name = agent_name
                self.dialer_username = username
                self.dialer_password = password
                self.dialer_place_id = place_id
                
                # Save to cache
                self._save_to_cache()
                result["success"] = True
                root.destroy()
            
            def on_cancel():
                """Cancel the configuration"""
                root.destroy()
                sys.exit(1)
            
            # Buttons
            submit_button = ttk.Button(button_frame, text="Save Configuration", command=on_submit)
            submit_button.pack(side="left", padx=5)
            
            cancel_button = ttk.Button(button_frame, text="Cancel", command=on_cancel)
            cancel_button.pack(side="right", padx=5)
            
            # Focus on first field
            agent_name_entry.focus()
            
            # Show window and wait
            root.mainloop()
            
            # Show success message if submitted
            if result["success"]:
                messagebox.showinfo(
                    "Success",
                    "Configuration saved successfully!\n\n"
                    "Your credentials are now cached for future use."
                )
            
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
            root.destroy()
            sys.exit(1)
    
    def _save_to_cache(self):
        """
        Save credentials to JSON file and hide it on Windows.
        """
        config_data = {
            'dialer_username': self.dialer_username,
            'dialer_password': self.dialer_password,
            'dialer_place_id': self.dialer_place_id,
            'agent_name': self.agent_name
        }
        
        try:
            with open(self.config_path, 'w') as file:
                json.dump(config_data, file, indent=4)
            
            # Hide file on Windows
            self._hide_config_file()
            print(f"[INFO] Configuration saved to {self.config_path}")
            
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")
            raise
    
    def _hide_config_file(self):
        """
        Hide the config file on Windows using file attributes.
        Uses ctypes to call Windows API SetFileAttributes.
        """
        if sys.platform == "win32":
            try:
                # Windows file attributes
                FILE_ATTRIBUTE_HIDDEN = 0x02
                
                # Convert Path to string
                file_path = str(self.config_path)
                
                # Call Windows API to set hidden attribute
                ctypes.windll.kernel32.SetFileAttributesW(file_path, FILE_ATTRIBUTE_HIDDEN)
                print(f"[INFO] Config file hidden: {file_path}")
                
            except Exception as e:
                print(f"[WARN] Failed to hide config file: {e}")
        else:
            print("[INFO] Running on non-Windows system - file hiding skipped")
    
    def _show_cached_data_popup(self):
        """
        Show popup confirming that data was loaded from cache.
        Displays the loaded credentials (with password masked).
        Shows the cache file location.
        """
        root = tk.Tk()
        root.withdraw()
        
        message = (
            "✓ Configuration loaded from cache successfully!\n\n"
            f"Agent Name: {self.agent_name}\n"
            f"Dialer Username: {self.dialer_username}\n"
            f"Dialer Password: {'*' * len(self.dialer_password)}\n"
            f"Dialer Place ID: {self.dialer_place_id}\n\n"
            f"Cache Location:\n{self.config_path}\n\n"
            "Proceeding with normal process..."
        )
        
        messagebox.showinfo("Configuration Loaded", message)
        root.destroy()
    
    def get_all_config(self):
        """
        Get all configuration as a dictionary.
        
        Returns:
            dict: Configuration dictionary with all credentials
        """
        return {
            'dialer_username': self.dialer_username,
            'dialer_password': self.dialer_password,
            'dialer_place_id': self.dialer_place_id,
            'agent_name': self.agent_name
        }
    
    def update_credential(self, key, value):
        """
        Update a single credential and save to cache.
        
        Args:
            key (str): Credential key (dialer_username, dialer_password, etc.)
            value (str): New credential value
        """
        valid_keys = ['dialer_username', 'dialer_password', 'dialer_place_id', 'agent_name']
        if key not in valid_keys:
            raise ValueError(f"Invalid key: {key}. Must be one of {valid_keys}")
        
        setattr(self, key, value)
        self._save_to_cache()
        print(f"[INFO] Updated {key} in cache")
    
    def reset_config(self):
        """
        Delete cached config and request new input.
        Useful for switching users or updating credentials.
        """
        try:
            if self.config_path.exists():
                self.config_path.unlink()
                print(f"[INFO] Config file deleted: {self.config_path}")
            
            # Reset attributes
            self.dialer_username = None
            self.dialer_password = None
            self.dialer_place_id = None
            self.agent_name = None
            
            # Get new input
            self._get_user_input()
            
        except Exception as e:
            print(f"[ERROR] Failed to reset config: {e}")


# ============================================================================
# USAGE EXAMPLES AND SNIPPETS
# ============================================================================

"""
SNIPPET 1: Basic Usage in Your Main Script
==========================================

from config_manager import ConfigManager

# Initialize config manager (loads or creates config)
config = ConfigManager()

# Access credentials individually
username = config.dialer_username
password = config.dialer_password
place_id = config.dialer_place_id
agent_name = config.agent_name

# Use in your code
perform_dialer_login(
    driver,
    username=username,
    password=password,
    place_id=place_id
)

print(f"Logged in as: {agent_name}")


SNIPPET 2: Get All Config as Dictionary
========================================

from config_manager import ConfigManager

config = ConfigManager()
all_creds = config.get_all_config()

# Access via dictionary
dialer_username = all_creds['dialer_username']
dialer_password = all_creds['dialer_password']
dialer_place_id = all_creds['dialer_place_id']
agent_name = all_creds['agent_name']


SNIPPET 3: Update Individual Credentials
==========================================

from config_manager import ConfigManager

config = ConfigManager()

# Update a single credential
config.update_credential('agent_name', 'New Agent Name')
config.update_credential('dialer_password', 'new_password_123')


SNIPPET 4: Reset and Start Fresh
=================================

from config_manager import ConfigManager

config = ConfigManager()

# Delete cached config and request new input
config.reset_config()


SNIPPET 5: Integration in perform_dialer_login()
================================================

from config_manager import ConfigManager

def perform_dialer_login(driver):
    # Load config
    config = ConfigManager()
    
    dialer_url = "https://104.232.254.43/ui/ad/v1/index.html"
    
    print("[INFO] Opening dialer...")
    driver.get(dialer_url)
    time.sleep(3)
    
    # Use cached credentials
    print("[INFO] Entering username...")
    send_keys_safe(
        driver, 
        By.ID, 
        'wweLoginUserNameField', 
        config.dialer_username,  # From cache
        timeout=2, 
        retries=120
    )
    
    print("[INFO] Entering password...")
    send_keys_safe(
        driver, 
        By.ID, 
        'wweLoginPasswordField', 
        config.dialer_password,  # From cache
        timeout=2, 
        retries=120, 
        enter=True
    )
    
    print("[INFO] Entering place ID...")
    send_keys_safe(
        driver, 
        By.ID, 
        'wweLoginPlaceInput', 
        config.dialer_place_id,  # From cache
        timeout=2, 
        retries=120, 
        enter=True
    )
    
    time.sleep(10)
    
    # Rest of login logic...
    handles = driver.window_handles
    dialer_handle = handles[0]
    driver.switch_to.window(dialer_handle)
    click_safe(driver, By.XPATH, "//table[@id='DataTables_Table_0']/tbody/tr/td[2]", timeout=1, retries=3)
    click_safe(driver, By.ID, "wweAgentSetNotReadyReason4Item_MyChannelsView", timeout=1, retries=3)
    
    handles = driver.window_handles
    crm_handle = handles[1]
    driver.switch_to.window(crm_handle)
    
    return True


SNIPPET 6: JSON Cache File Format
=================================

The generated config file (art_config.json) will look like this:

{
    "dialer_username": "Agent_Cairo_US_920",
    "dialer_password": "123456",
    "dialer_place_id": "Place_57078_SIPSwitch_US",
    "agent_name": "Adam Maged"
}

Location: C:\\Users\\{YourUsername}\\art_config.json
Status: Hidden (use Show Hidden Files to see)


SNIPPET 7: In Your Main_wait_untill.py or ART_EagleControl_V_17.py
===================================================================

# At the top of your script
from config_manager import ConfigManager

# Initialize as early as possible (e.g., after imports)
config = ConfigManager()

# Remove hardcoded credentials and replace with:
# Old: send_keys_safe(driver, By.ID, 'wweLoginUserNameField', "Agent_Cairo_US_920", ...)
# New: send_keys_safe(driver, By.ID, 'wweLoginUserNameField', config.dialer_username, ...)

# Remove hardcoded agent name and replace with:
# Old: AgentName = "Adam Maged"
# New: AgentName = config.agent_name

# In CaseNote construction:
# Old: CaseNote = f"... Agent: Adam Maged ..."
# New: CaseNote = f"... Agent: {config.agent_name} ..."
"""


# ============================================================================
# TEST/DEMO FUNCTION
# ============================================================================

def demo_config_manager():
    """
    Demo function to test ConfigManager functionality.
    Run this to test credential loading/creation without modifying main code.
    """
    print("=" * 60)
    print("ART Configuration Manager - Demo")
    print("=" * 60)
    
    # Initialize config
    print("\n1. Initializing ConfigManager...")
    config = ConfigManager()
    
    # Display loaded config
    print("\n2. Current Configuration:")
    all_config = config.get_all_config()
    for key, value in all_config.items():
        if 'password' in key:
            display_value = '*' * len(value)
        else:
            display_value = value
        print(f"   {key}: {display_value}")
    
    # Test individual access
    print("\n3. Individual Variable Access:")
    print(f"   Agent Name: {config.agent_name}")
    print(f"   Dialer Username: {config.dialer_username}")
    print(f"   Dialer Place ID: {config.dialer_place_id}")
    
    print("\n" + "=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    # Run demo when script is executed directly
    demo_config_manager()
