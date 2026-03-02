import os
import sys
import subprocess
import pandas as pd
from pathlib import Path
from tkinter import Tk, filedialog, messagebox
from tkinter import ttk
import tkinter as tk
from typing import Dict, List, Set, Tuple
import threading



class ExcelMergerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Excel File Merger")
        self.root.geometry("600x550")
        
        # Set icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir)) # src/Merger -> src -> root
            icon_path = os.path.join(project_root, 'assets', 'ibm_logo.png')
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, img)
        except Exception:
            pass
        
        self.excel_files = {}  # {filename: filepath}
        self.sheet_data = {}   # {filename: {sheetname: dataframe}}
        self.selected_sheets = set()
        self.all_columns = []  # All distinct columns from all sheets
        self.merge_config = {}  # {output_col_name: [list of source columns to merge]}
        
        self.create_main_screen()
    
    def create_main_screen(self):
        """Create the initial file selection screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill="both", expand=True)
        
        title = ttk.Label(frame, text="Excel File Merger", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        instruction = ttk.Label(
            frame,
            text="Step 1: Select Excel files to read\n(You can select multiple files at once)",
            justify="center"
        )
        instruction.pack(pady=10)
        
        btn_select = ttk.Button(
            frame,
            text="Select Excel Files",
            command=self.select_files
        )
        btn_select.pack(pady=20)
        
        # File list display
        list_frame = ttk.LabelFrame(frame, text="Selected Files", padding="10")
        list_frame.pack(fill="both", expand=True, pady=10)
        
        self.file_listbox = tk.Listbox(list_frame, height=10)
        self.file_listbox.pack(fill="both", expand=True, side="left")
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        
        btn_next = ttk.Button(
            button_frame,
            text="Next (Select Sheets)",
            command=self.move_to_sheet_selection
        )
        btn_next.pack(side="left", padx=5)
        
        btn_clear = ttk.Button(
            button_frame,
            text="Clear All",
            command=self.clear_files
        )
        btn_clear.pack(side="left", padx=5)

        btn_main_menu = ttk.Button(
            button_frame,
            text="Main Menu",
            command=self.return_to_main_menu
        )
        btn_main_menu.pack(side="left", padx=5)

        # Footer
        footer_text = "Developed by: Ehab Elrify | Adam Maged\nEmail: ehab.elrify@ibm.com | abdelrahman.maged@ibm.com\nAssurance Resolution Team"
        footer_label = ttk.Label(
             frame,
             text=footer_text,
             justify=tk.CENTER,
             foreground="#525252"
        )
        footer_label.pack(side="bottom", pady=20)
    
    def return_to_main_menu(self):
        """Return to the main menu application with aggressive environment cleaning"""
        try:
            if getattr(sys, 'frozen', False):
                # On Windows, os.startfile is the cleanest way to launch the EXE as a new process
                # It bypasses all environment variable inheritance issues
                try:
                    os.startfile(sys.executable)
                except AttributeError:
                    # Fallback for non-Windows
                    env = os.environ.copy()
                    for var in ['TCL_LIBRARY', 'TK_LIBRARY', '_MEIPASS', '_MEIPASS2', 
                                'PYTHONPATH', 'PYTHONHOME', 'QT_PLUGIN_PATH', 
                                'QT_QPA_PLATFORM_PLUGIN_PATH']:
                        env.pop(var, None)
                    subprocess.Popen([sys.executable], env=env)
            else:
                # Resolve path to src/main.py
                # Current file is src/Merger/Merger.py
                env = os.environ.copy()
                current_dir = os.path.dirname(os.path.abspath(__file__))
                src_dir = os.path.dirname(current_dir) # This gets to 'src'
                main_menu_path = os.path.join(src_dir, 'main.py')
                
                if os.path.exists(main_menu_path):
                    subprocess.Popen([sys.executable, main_menu_path], env=env)
                else:
                    messagebox.showerror("Error", f"Main menu script not found: {main_menu_path}")
            
            self.root.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Main Menu: {e}")
    
    def select_files(self):
        """Open file dialog to select Excel files"""
        files = filedialog.askopenfilenames(
            title="Select Excel Files",
            filetypes=[("Excel Files", "*.xlsx *.xls"), ("All Files", "*.*")]
        )
        
        if files:
            for file in files:
                filename = os.path.basename(file)
                self.excel_files[filename] = file
            
            self.update_file_list()
            self.load_excel_files()
    
    def load_excel_files(self):
        """Load Excel files in a separate thread to avoid freezing UI"""
        thread = threading.Thread(target=self._load_files_thread)
        thread.daemon = True
        thread.start()
    
    def _load_files_thread(self):
        """Load Excel files (runs in background)"""
        for filename, filepath in self.excel_files.items():
            try:
                excel_file = pd.ExcelFile(filepath)
                self.sheet_data[filename] = {}
                
                for sheet in excel_file.sheet_names:
                    self.sheet_data[filename][sheet] = excel_file.parse(sheet)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load {filename}: {str(e)}")
    
    def update_file_list(self):
        """Update the file listbox display"""
        self.file_listbox.delete(0, tk.END)
        for filename in self.excel_files.keys():
            self.file_listbox.insert(tk.END, filename)
    
    def clear_files(self):
        """Clear all selected files"""
        self.excel_files.clear()
        self.sheet_data.clear()
        self.update_file_list()
    
    def move_to_sheet_selection(self):
        """Move to sheet selection screen"""
        if not self.excel_files:
            messagebox.showwarning("Warning", "Please select at least one Excel file!")
            return
        
        # Wait for files to load
        if not all(filename in self.sheet_data for filename in self.excel_files):
            messagebox.showinfo("Info", "Please wait for files to load...")
            self.root.after(500, self.move_to_sheet_selection)
            return
        
        self.create_sheet_selection_screen()
    
    def create_sheet_selection_screen(self):
        """Create sheet selection screen with search functionality"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("900x700") # Increased for footer
        
        # Set icon
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            icon_path = os.path.join(project_root, 'assets', 'ibm_logo.png')
            if os.path.exists(icon_path):
                img = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(False, img)
        except Exception:
            pass
        
        frame = ttk.Frame(self.root, padding="20")
        frame.pack(fill="both", expand=True)
        
        title = ttk.Label(frame, text="Select Sheets", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        instruction = ttk.Label(
            frame,
            text="Step 2: Select sheets to merge\nUse search to filter sheet names",
            justify="center"
        )
        instruction.pack(pady=10)
        
        # Search frame
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill="x", pady=10)
        
        ttk.Label(search_frame, text="Search Sheets:").pack(side="left", padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_sheets())
        
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5)
        
        btn_select_all = ttk.Button(
            search_frame,
            text="Select All (Results)",
            command=self.select_all_filtered
        )
        btn_select_all.pack(side="left", padx=5)
        
        # Sheet selection frame
        list_frame = ttk.LabelFrame(frame, text="Available Sheets", padding="10")
        list_frame.pack(fill="both", expand=True, pady=10)
        
        # Create frame for checkboxes with scrollbar
        canvas = tk.Canvas(list_frame, height=250)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.sheet_frame = ttk.Frame(canvas)
        
        self.sheet_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.sheet_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.sheet_vars = {}
        self.sheet_widgets = {}
        self.file_labels = {}
        
        # Populate sheet checkboxes
        for filename in sorted(self.sheet_data.keys()):
            file_label = ttk.Label(self.sheet_frame, text=f"📁 {filename}", font=("Arial", 10, "bold"))
            file_label.pack(anchor="w", padx=10, pady=(10, 5))
            self.file_labels[filename] = file_label
            
            for sheet_name in sorted(self.sheet_data[filename].keys()):
                var = tk.BooleanVar()
                self.sheet_vars[f"{filename}:{sheet_name}"] = var
                
                check = ttk.Checkbutton(
                    self.sheet_frame,
                    text=f"  └─ {sheet_name}",
                    variable=var
                )
                check.pack(anchor="w", padx=30)
                self.sheet_widgets[f"{filename}:{sheet_name}"] = check
        
        # Button frame
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill="x", pady=10)
        
        btn_next = ttk.Button(
            button_frame,
            text="Next (Merge Configuration)",
            command=self.move_to_merge_config
        )
        btn_next.pack(side="left", padx=5)
        
        btn_back = ttk.Button(
            button_frame,
            text="Back",
            command=self.create_main_screen
        )
        btn_back.pack(side="left", padx=5)

        # Footer
        footer_text = "Developed by: Ehab Elrify | Adam Maged\nEmail: ehab.elrify@ibm.com | abdelrahman.maged@ibm.com\nAssurance Resolution Team"
        footer_label = ttk.Label(
             frame,
             text=footer_text,
             justify=tk.CENTER,
             foreground="#525252"
        )
        footer_label.pack(side="bottom", pady=20)
    
    def filter_sheets(self):
        """Filter sheet display based on search text"""
        search_text = self.search_var.get().lower()
        
        for filename, label in self.file_labels.items():
            file_has_match = False
            for key, widget in self.sheet_widgets.items():
                file, sheet_name = key.split(":")
                if file == filename:
                    if search_text in sheet_name.lower():
                        widget.pack(anchor="w", padx=30)
                        file_has_match = True
                    else:
                        widget.pack_forget()
            
            # Show/hide file label based on whether it has matching sheets
            if file_has_match or search_text == "":
                label.pack(anchor="w", padx=10, pady=(10, 5))
            else:
                label.pack_forget()
    
    def select_all_filtered(self):
        """Select all sheets that match the current search filter"""
        search_text = self.search_var.get().lower()
        
        for key, var in self.sheet_vars.items():
            sheet_name = key.split(":")[-1]
            if search_text == "" or search_text in sheet_name.lower():
                var.set(True)
    
    def move_to_merge_config(self):
        """Move to flexible merge configuration screen"""
        # Collect selected sheets
        self.selected_sheets = set()
        for key, var in self.sheet_vars.items():
            if var.get():
                self.selected_sheets.add(key)
        
        if not self.selected_sheets:
            messagebox.showwarning("Warning", "Please select at least one sheet!")
            return
        
        # Get all distinct columns from selected sheets
        self.all_columns = []
        seen = set()
        for sheet_key in sorted(self.selected_sheets):
            filename, sheet_name = sheet_key.split(":")
            df = self.sheet_data[filename][sheet_name]
            for col in df.columns:
                if col not in seen:
                    self.all_columns.append(col)
                    seen.add(col)
        
        self.create_merge_config_screen()
    
    def create_merge_config_screen(self):
        """Create flexible merge configuration screen"""
        for widget in self.root.winfo_children():
            widget.destroy()
        
        self.root.geometry("1400x800")
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        # Title
        title = ttk.Label(main_frame, text="Flexible Column Merge Configuration", font=("Arial", 14, "bold"))
        title.pack(pady=10)
        
        instruction = ttk.Label(
            main_frame,
            text="Drag columns from Available Columns to Output Result to create merge groups. Multiple columns in one line will be merged together.",
            foreground="gray",
            wraplength=800
        )
        instruction.pack(pady=5)
        
        # Main content - 3 panels layout using PanedWindow for resizable panels
        content_frame = ttk.PanedWindow(main_frame, orient="horizontal")
        content_frame.pack(fill="both", expand=True, pady=10)
        
        # Left panel: Preview
        preview_frame = ttk.LabelFrame(content_frame, text="Output Preview (Full Data)", padding="10")
        content_frame.add(preview_frame, weight=3)
        
        self.preview_tree = ttk.Treeview(preview_frame, height=20)
        self.preview_tree.pack(fill="both", expand=True, side="left")
        
        preview_scroll = ttk.Scrollbar(preview_frame, orient="vertical", command=self.preview_tree.yview)
        preview_scroll.pack(side="right", fill="y")
        self.preview_tree.configure(yscrollcommand=preview_scroll.set)
        
        # Preview status bar
        self.preview_status = ttk.Label(preview_frame, text="", foreground="blue", font=("Arial", 9))
        self.preview_status.pack(fill="x", pady=(5, 0))
        
        # Middle panel: Available columns
        available_frame = ttk.LabelFrame(content_frame, text="Available Columns (All Distinct)", padding="10")
        content_frame.add(available_frame, weight=1)
        
        avail_list_frame = ttk.Frame(available_frame)
        avail_list_frame.pack(fill="both", expand=True)
        
        self.available_listbox = tk.Listbox(avail_list_frame, height=20, width=25, selectmode="multiple")
        self.available_listbox.pack(side="left", fill="both", expand=True)
        
        avail_scroll = ttk.Scrollbar(avail_list_frame, orient="vertical", command=self.available_listbox.yview)
        avail_scroll.pack(side="right", fill="y")
        self.available_listbox.config(yscrollcommand=avail_scroll.set)
        
        # Populate available columns
        for col in self.all_columns:
            self.available_listbox.insert(tk.END, col)
        
        # Right panel: Output result configuration
        output_frame = ttk.LabelFrame(content_frame, text="Output Result Configuration", padding="10")
        content_frame.add(output_frame, weight=2)
        
        # Control buttons
        btn_frame = ttk.Frame(output_frame)
        btn_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(btn_frame, text="➕ Add to Output", command=self.add_to_output, width=20).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="➕ Add Multiple", command=self.add_multiple_columns, width=20).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="✖ Remove Selected", command=self.remove_from_output, width=20).pack(side="left", padx=2)
        
        # Output configuration listbox
        output_list_frame = ttk.Frame(output_frame)
        output_list_frame.pack(fill="both", expand=True)
        
        self.output_listbox = tk.Listbox(output_list_frame, height=20, width=50)
        self.output_listbox.pack(side="left", fill="both", expand=True)
        self.output_listbox.bind('<<ListboxSelect>>', self.on_output_select)
        
        output_scroll = ttk.Scrollbar(output_list_frame, orient="vertical", command=self.output_listbox.yview)
        output_scroll.pack(side="right", fill="y")
        self.output_listbox.config(yscrollcommand=output_scroll.set)
        
        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=10)
        
        ttk.Button(
            button_frame,
            text="Merge & Save",
            command=self.merge_and_save
        ).pack(side="left", padx=5)
        
        ttk.Button(
            button_frame,
            text="Back",
            command=self.create_sheet_selection_screen
        ).pack(side="left", padx=5)

        # Footer
        footer_text = "Developed by: Ehab Elrify | Adam Maged\nEmail: ehab.elrify@ibm.com | abdelrahman.maged@ibm.com\nAssurance Resolution Team"
        footer_label = ttk.Label(
             main_frame,
             text=footer_text,
             justify=tk.CENTER,
             foreground="#525252"
        )
        footer_label.pack(side="bottom", pady=20)
    
    def add_to_output(self):
        """Add selected column from available to output"""
        selection = self.available_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a column!")
            return
        
        col_name = self.available_listbox.get(selection[0])
        self.output_listbox.insert(tk.END, col_name)
        self.update_preview()
    
    def add_multiple_columns(self):
        """Add multiple columns to merge together"""
        selection = self.available_listbox.curselection()
        if not selection or len(selection) < 2:
            messagebox.showwarning("Warning", "Please select 2 or more columns to merge!")
            return
        
        cols = [self.available_listbox.get(i) for i in selection]
        merge_str = " + ".join(cols)
        self.output_listbox.insert(tk.END, merge_str)
        self.update_preview()
    
    def remove_from_output(self):
        """Remove selected item from output"""
        selection = self.output_listbox.curselection()
        if not selection:
            messagebox.showwarning("Warning", "Please select an item to remove!")
            return
        
        self.output_listbox.delete(selection[0])
        self.update_preview()
    
    def on_output_select(self, event):
        """Handle output selection"""
        pass
    
    def update_preview(self):
        """Update the preview with full data"""
        # Clear preview
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        # Get output configuration
        output_config = []
        for i in range(self.output_listbox.size()):
            output_config.append(self.output_listbox.get(i))
        
        if not output_config:
            self.preview_tree['columns'] = []
            self.preview_status.config(text="Total Rows: 0")
            return
        
        # Build preview data
        preview_cols = list(output_config)
        self.preview_tree['columns'] = preview_cols
        self.preview_tree.column("#0", width=0, stretch=False)
        
        for col in preview_cols:
            col_width = min(150, max(80, len(col) * 8))
            self.preview_tree.column(col, anchor="w", width=col_width)
            self.preview_tree.heading(col, text=col)
        
        # Get all data
        all_merged_dfs = []
        for sheet_key in sorted(self.selected_sheets):
            filename, sheet_name = sheet_key.split(":")
            df = self.sheet_data[filename][sheet_name].copy()
            all_merged_dfs.append(df)
        
        if all_merged_dfs:
            all_data = pd.concat(all_merged_dfs, ignore_index=True, sort=False)
            total_rows = len(all_data)
            
            # Add ALL data to preview (not just sample)
            for idx, row_idx in enumerate(range(len(all_data))):
                row_data = []
                for col_spec in output_config:
                    if " + " in col_spec:
                        # Merged columns
                        cols = col_spec.split(" + ")
                        merged_val = None
                        for col in cols:
                            col = col.strip()
                            if col in all_data.columns:
                                val = all_data.iloc[row_idx][col]
                                if pd.notna(val):
                                    merged_val = val
                                    break
                        row_data.append(str(merged_val) if merged_val is not None else "")
                    else:
                        # Single column
                        if col_spec in all_data.columns:
                            val = all_data.iloc[row_idx][col_spec]
                            row_data.append(str(val) if pd.notna(val) else "")
                        else:
                            row_data.append("")
                
                self.preview_tree.insert("", "end", values=tuple(row_data))
            
            self.preview_status.config(text=f"Total Rows: {total_rows} | Output Columns: {len(output_config)}")
        else:
            self.preview_status.config(text="No data available")
    
    def merge_and_save(self):
        """Merge data according to configuration and save"""
        # Get output configuration
        output_config = []
        for i in range(self.output_listbox.size()):
            output_config.append(self.output_listbox.get(i))
        
        if not output_config:
            messagebox.showwarning("Warning", "Please configure output columns!")
            return
        
        # Collect all dataframes
        merged_dfs = []
        for sheet_key in sorted(self.selected_sheets):
            filename, sheet_name = sheet_key.split(":")
            df = self.sheet_data[filename][sheet_name].copy()
            df['_source_file'] = filename
            df['_source_sheet'] = sheet_name
            merged_dfs.append(df)
        
        # Concatenate all data
        result_df = pd.concat(merged_dfs, ignore_index=True, sort=False)
        
        # Process output configuration
        final_columns = []
        for col_spec in output_config:
            if " + " in col_spec:
                # Merge multiple columns
                cols = [c.strip() for c in col_spec.split(" + ")]
                merged_col_name = col_spec.replace(" + ", "_")
                
                # Create merged column
                result_df[merged_col_name] = None
                for col in cols:
                    if col in result_df.columns:
                        mask = (result_df[merged_col_name].isna()) & (result_df[col].notna())
                        result_df.loc[mask, merged_col_name] = result_df.loc[mask, col]
                
                final_columns.append(merged_col_name)
                
                # Remove individual columns
                for col in cols:
                    if col in result_df.columns:
                        result_df.drop(columns=[col], inplace=True)
            else:
                # Single column
                if col_spec in result_df.columns:
                    final_columns.append(col_spec)
        
        # Add remaining columns (source info)
        for col in result_df.columns:
            if col not in final_columns:
                final_columns.append(col)
        
        result_df = result_df[final_columns]
        
        # Save
        save_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("CSV Files", "*.csv")],
            initialfile="merged_result"
        )
        
        if save_path:
            try:
                if save_path.endswith('.xlsx'):
                    result_df.to_excel(save_path, index=False)
                else:
                    result_df.to_csv(save_path, index=False)
                
                messagebox.showinfo(
                    "Success",
                    f"Merged data saved to:\n{save_path}\n\nRows: {len(result_df)}\nColumns: {len(result_df.columns)}"
                )
                self.create_main_screen()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")


def main():
    root = Tk()
    app = ExcelMergerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
