import tkinter as tk
from tkinter import ttk 
from tkinter import filedialog 
from tkinter import messagebox 
import time 
import sys
import os 
import subprocess 
import json 
from datetime import datetime, timedelta, date 

# Define the structure for a single file within an assignment group
# File structure: (Path, Size, Date, Icon)
PENDING_FILE = ("PENDING", "1 KB", "", "❓")

# --- 1. Main Application Setup ---
class CollegeApp:
    # --- FINANCE CONSTANTS ---
    CURRENCY_SYMBOL = "₹"
    
    # COLOR MAPPING FOR TAGS
    FINANCE_TAG_COLORS = {
        "Tuition/Fees": "#e74c3c",    # Red
        "Rent/Housing": "#f39c12",    # Orange
        "Food/Groceries": "#2ecc71",  # Green
        "Books/Supplies": "#3498db",  # Blue
        "Transport": "#9b59b6",       # Purple
        "Part-Time Job": "#1abc9c",   # Teal
        "Scholarship": "#f1c40f",     # Yellow
        "Pocket Money": "#34495e",   # Dark Blue/Grey
        "Miscellaneous": "#bdc3c7",   # Light Grey
    }

    DEFAULT_FINANCE_TAGS = {
        "Tuition/Fees": "🎓",
        "Rent/Housing": "🏠",
        "Food/Groceries": "🍔",
        "Books/Supplies": "📚",
        "Transport": "🚌",
        "Part-Time Job": "💼",
        "Scholarship": "🌟",
        "Pocket Money": "🪙", 
        "Miscellaneous": "⚙️",
    }
    
    def __init__(self, master):
        self.master = master
        master.title("College Student Hub")
        master.geometry("1000x700") 
        master.minsize(800, 600) 
        
        self.notification_label = None
        
        # --- Persistent Data File Definition ---
        self.data_file = "college_hub_data.json"
        
        # --- DATA STRUCTURES ---
        self.courses_list = []
        self.assignment_data = {}
        self.material_data = {}
        self.finance_data = {'Income': [], 'Expenses': []} 
        self.grades_data = {} 

        # --- FINANCE FILTER VARIABLES ---
        self.finance_filter_vars = {} 
        self.filter_start_date_var = tk.StringVar()
        self.filter_end_date_var = tk.StringVar()
        self.filtered_income = []
        self.filtered_expenses = []
        self.active_date_preset = tk.StringVar(value="All Time") 

        # --- Load Data on Startup ---
        self.load_data() 
        
        self.functions = ["Finance", "Courses", "Grades", "Log Off"]
        self.current_course = None
        self.current_tab = 'assignment'
        
        # --- 2. Create Layout Frames ---
        self.sidebar_frame = tk.Frame(master, width=160, bg="#2c3e50") 
        self.sidebar_frame.pack(side="left", fill="y", padx=0, pady=0)
        
        self.main_frame = tk.Frame(master, bg="#ecf0f1")
        self.main_frame.pack(side="right", fill="both", expand=True) 
        
        self.create_sidebar_buttons() 
        self.display_content("Courses") 
        
    # ----------------------------------------------------------------------
    # --- PERSISTENCE (SAVE/LOAD) FUNCTIONS ---
    # ----------------------------------------------------------------------
    def save_data(self):
        """Saves the current application state to a JSON file."""
        data_to_save = {
            'courses': self.courses_list,
            'assignments': self.assignment_data,
            'materials': self.material_data,
            'finance': self.finance_data,
            'grades': self.grades_data, 
            'finance_tags': self.DEFAULT_FINANCE_TAGS, 
        }
        
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            print("Data saved successfully.")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save data: {e}")

    def load_data(self):
        """Loads the application state from the JSON file on startup."""
        try:
            with open(self.data_file, 'r') as f:
                loaded_data = json.load(f)
                
                self.courses_list = loaded_data.get('courses', [])
                self.assignment_data = loaded_data.get('assignments', {})
                self.material_data = loaded_data.get('materials', {})
                self.finance_data = loaded_data.get('finance', {'Income': [], 'Expenses': []})
                self.grades_data = loaded_data.get('grades', {}) 
                
                # Load custom tags, merging them with default if they exist
                loaded_tags = loaded_data.get('finance_tags', {})
                for key, value in loaded_tags.items():
                    if key not in self.DEFAULT_FINANCE_TAGS:
                        self.DEFAULT_FINANCE_TAGS[key] = value 
                        self.FINANCE_TAG_COLORS[key] = "#7f8c8d" # Default custom color

            print("Data loaded successfully.")

        except (FileNotFoundError, json.JSONDecodeError) as e:
            if isinstance(e, FileNotFoundError):
                 print("No data file found. Using default initial setup.")
            else:
                 messagebox.showerror("Load Error", "Data file is corrupted. Starting with default data.")

            self.courses_list = ["Math", "Physics", "Chemistry", "History", "CEC"] 
            self.finance_data = {'Income': [], 'Expenses': []} 
            
            for course in self.courses_list:
                if course not in self.assignment_data:
                    self.assignment_data[course] = {}
                if course not in self.material_data:
                    self.material_data[course] = []
                if course not in self.grades_data: 
                    self.grades_data[course] = []
    
    # ----------------------------------------------------------------------
    # --- GRADES FUNCTIONS ---
    # ----------------------------------------------------------------------
    def calculate_course_average(self, course_name):
        """Calculates the weighted average for a given course."""
        
        grades = self.grades_data.get(course_name, [])
        if not grades:
            return None, 0

        weighted_sum = 0
        total_weight = 0

        for entry in grades:
            # Entry structure: {'name': 'Midterm', 'score': 85, 'max_score': 100, 'weight': 30}
            try:
                score_percentage = (entry['score'] / entry['max_score']) * 100
                weight_decimal = entry['weight'] / 100.0
                
                weighted_sum += score_percentage * weight_decimal
                total_weight += entry['weight']
            except (ZeroDivisionError, KeyError, TypeError):
                # Skip invalid entries (e.g., max_score=0 or missing keys)
                continue
        
        if total_weight > 0:
            # Scale the weighted sum back up by the fraction of the total weight recorded
            current_average = weighted_sum / (total_weight / 100.0)
            return current_average, total_weight
        
        return None, 0

    def display_grades_hub(self):
        """Displays a summary of grades for all courses."""
        
        tk.Label(self.main_frame, text="Current Semester Overview", 
                 font=("Helvetica", 16, "bold"), fg="#2c3e50", bg="#ecf0f1").pack(pady=(0, 20))
        
        cards_container = tk.Frame(self.main_frame, bg="#ecf0f1")
        cards_container.pack(fill="both", expand=True, padx=20)
        
        if not self.courses_list:
             tk.Label(cards_container, text="Please add courses in the 'Courses' hub first.", 
                     font=("Helvetica", 14, "italic"), fg="gray", bg="#ecf0f1").pack(pady=50)
             return

        max_cols = 3
        
        for i, course_name in enumerate(self.courses_list):
            row = i // max_cols
            col = i % max_cols
            
            card = self.create_grade_card(cards_container, course_name)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
        for col in range(max_cols):
            cards_container.grid_columnconfigure(col, weight=1)

    def create_grade_card(self, parent_frame, course_name):
        """Creates a clickable grade summary card."""
        
        current_average, total_weight = self.calculate_course_average(course_name)
        
        container = tk.Frame(parent_frame, bg="#ffffff", bd=2, relief="raised", padx=10, pady=10)
        
        # Course Name
        tk.Label(container, text=course_name, font=("Helvetica", 18, "bold"), 
                 fg="#34495e", bg="#ffffff").pack(pady=(0, 5))
        
        tk.Label(container, text="Current Average:", font=("Helvetica", 12), 
                 fg="#7f8c8d", bg="#ffffff").pack()
                 
        # Calculated Grade
        if current_average is not None:
            grade_color = "#2ecc71" if current_average >= 80 else ("#f39c12" if current_average >= 60 else "#e74c3c")
            display_text = f"{current_average:.2f}%"
        else:
            grade_color = "#7f8c8d"
            display_text = "N/A"
            
        tk.Label(container, text=display_text, font=("Helvetica", 30, "bold"), 
                 fg=grade_color, bg="#ffffff").pack()
                 
        tk.Label(container, text=f"Weight Recorded: {total_weight}%", font=("Helvetica", 10, "italic"), 
                 fg="#7f8c8d", bg="#ffffff").pack(pady=(5, 10))

        tk.Button(container, text="View/Add Grades", 
                  command=lambda name=course_name: self.display_course_grades(name),
                  bg="#3498db", fg="white", relief="flat").pack(fill="x")
        
        return container
        
    def display_course_grades(self, course_name):
        """Displays the detailed list of grades for one course."""
        
        self.current_course = course_name
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(header_frame, text="< Back to Grades", 
                 command=lambda: self.display_content("Grades"),
                 font=("Helvetica", 10), relief="flat", bg="#bdc3c7", fg="#34495e").pack(side="left")

        tk.Label(header_frame, text=f"Grades: {course_name}", font=("Helvetica", 24, "bold"), 
                 bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=20)
        
        current_average, total_weight = self.calculate_course_average(course_name)
        
        # Display current average in the detail view
        average_color = "#2ecc71" if current_average is not None and current_average >= 80 else ("#f39c12" if current_average is not None and current_average >= 60 else "#e74c3c")
        average_text = f"{current_average:.2f}%" if current_average is not None else "N/A"
        
        summary_label = tk.Label(self.main_frame, 
                                 text=f"Current Weighted Average: {average_text} | Total Weight Recorded: {total_weight}%",
                                 font=("Helvetica", 14, "bold"), 
                                 fg=average_color, bg="#ecf0f1")
        summary_label.pack(pady=(0, 10))
        
        # Add Entry Button
        tk.Button(self.main_frame, text="+ Add Grade Entry", 
                  font=("Helvetica", 12, "bold"), bg="#2ecc71", fg="white", 
                  activebackground="#27ae60", relief="raised", padx=10, pady=5,
                  command=lambda: self.prompt_and_add_grade(course_name)).pack(pady=(0, 15))
                  
        self.draw_grades_list(self.main_frame, course_name)

    def draw_grades_list(self, parent_frame, course_name):
        """Draws the scrollable list of grades."""
        list_container = tk.Frame(parent_frame, bg="#ffffff", bd=1, relief="solid")
        list_container.pack(fill="both", expand=True, padx=20, pady=10)

        # SCROLLABLE AREA SETUP
        scrollable_area = tk.Frame(list_container, bg="#ffffff")
        scrollable_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(scrollable_area, bg="#ffffff", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scrollable_area, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)
        
        grades_container = tk.Frame(canvas, bg="#ffffff")
        canvas_window = canvas.create_window((0, 0), window=grades_container, anchor="nw")

        grades_container.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        # SCROLLABLE AREA SETUP END

        grades = self.grades_data.get(course_name, [])

        if not grades:
             tk.Label(grades_container, text="No grades recorded yet.", 
                     font=("Helvetica", 12, "italic"), fg="gray", bg="#ffffff").pack(pady=50)
             return

        # Header Row
        header_row = tk.Frame(grades_container, bg="#f5f5f5")
        header_row.pack(fill="x", pady=2)
        
        cols_config = [
            ("Name", 25, "w", 10),
            ("Score", 10, "center", 0),
            ("Weight (%)", 10, "center", 0),
            ("Grade (%)", 10, "center", 0),
            ("", 5, "center", 0) # Delete column
        ]
        
        for text, width, anchor, padx_left in cols_config:
            tk.Label(header_row, text=text, font=("Helvetica", 10, "bold"), bg="#f5f5f5", width=width, anchor=anchor).pack(side="left", padx=(padx_left, 0))

        # Grade Rows
        for i, entry in enumerate(grades):
            row_bg = "#f9f9f9" if i % 2 != 0 else "#ffffff" 
            
            row_frame = tk.Frame(grades_container, bg=row_bg, padx=10, pady=5)
            row_frame.pack(fill="x")
            
            # Use error handling for division
            try:
                score_percentage = (entry['score'] / entry['max_score']) * 100
                grade_color = "#2ecc71" if score_percentage >= 80 else ("#f39c12" if score_percentage >= 60 else "#e74c3c")
            except (ZeroDivisionError, KeyError):
                 score_percentage = 0
                 grade_color = "#7f8c8d"

            tk.Label(row_frame, text=entry['name'], font=("Helvetica", 10, "bold"), 
                     bg=row_bg, width=25, anchor="w").pack(side="left", padx=(0, 5))
            
            tk.Label(row_frame, text=f"{entry['score']}/{entry['max_score']}", font=("Helvetica", 10), 
                     bg=row_bg, width=10).pack(side="left")
            
            tk.Label(row_frame, text=f"{entry['weight']}%", font=("Helvetica", 10), 
                     bg=row_bg, width=10).pack(side="left")
                     
            tk.Label(row_frame, text=f"{score_percentage:.2f}%", font=("Helvetica", 10, "bold"), 
                     bg=row_bg, fg=grade_color, width=10).pack(side="left")
            
            tk.Button(row_frame, text="🗑️", bg=row_bg, fg="#e74c3c", 
                     relief="flat", bd=0, padx=5,
                     command=lambda index=i, name=course_name: self.delete_grade_entry(name, index)).pack(side="right")
            
            ttk.Separator(grades_container, orient='horizontal').pack(fill="x")
            
    def prompt_and_add_grade(self, course_name):
        """Opens a Toplevel window to collect grade details."""
        grade_window = tk.Toplevel(self.master)
        grade_window.title(f"Add Grade for {course_name}")
        grade_window.geometry("400x350")
        grade_window.transient(self.master)
        grade_window.grab_set()
        
        tk.Label(grade_window, text="New Grade Entry", font=("Helvetica", 14, "bold")).pack(pady=10)

        fields = [("Name (e.g., Midterm):", 'name_entry'),
                  ("Score Received:", 'score_entry'),
                  ("Max Score:", 'max_score_entry'),
                  ("Weight (%) (0-100):", 'weight_entry')]
        
        data_fields = {}

        for i, (label_text, var_name) in enumerate(fields):
            row = tk.Frame(grade_window)
            row.pack(fill="x", padx=10, pady=5)
            tk.Label(row, text=label_text, width=20, anchor="w").pack(side="left")
            
            entry = tk.Entry(row, width=20)
            entry.pack(side="right", fill="x", expand=True)
            data_fields[var_name] = entry

        tk.Button(grade_window, text="Save Grade", 
                 command=lambda: self.save_grade_entry(grade_window, course_name, data_fields)).pack(pady=20)

    def save_grade_entry(self, grade_window, course_name, data_fields):
        name = data_fields['name_entry'].get().strip()
        score_str = data_fields['score_entry'].get().strip()
        max_score_str = data_fields['max_score_entry'].get().strip()
        weight_str = data_fields['weight_entry'].get().strip()
        
        if not all([name, score_str, max_score_str, weight_str]):
            messagebox.showerror("Error", "All fields are required.")
            return

        try:
            score = float(score_str)
            max_score = float(max_score_str)
            weight = int(weight_str)
        except ValueError:
            messagebox.showerror("Error", "Score, Max Score, and Weight must be valid numbers.")
            return

        if max_score <= 0 or score < 0 or weight < 0 or weight > 100:
            messagebox.showerror("Error", "Check values: Max Score must be positive. Score and Weight must be positive and Weight must be between 0 and 100.")
            return
            
        new_entry = {
            'name': name,
            'score': score,
            'max_score': max_score,
            'weight': weight
        }
        
        self.grades_data.setdefault(course_name, []).append(new_entry)
        
        grade_window.destroy()
        self.save_data()
        self.show_upload_notification(f"📝 Grade '{name}' added to {course_name}.")
        self.display_course_grades(course_name) 

    def delete_grade_entry(self, course_name, index):
        """Deletes a grade entry by index from the list."""
        
        grades_list = self.grades_data.get(course_name, [])
        if 0 <= index < len(grades_list):
            entry_name = grades_list[index]['name']
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the grade entry '{entry_name}'?"):
                self.grades_data[course_name].pop(index)
                self.save_data()
                self.show_upload_notification(f"🗑️ Grade entry '{entry_name}' deleted.")
                self.display_course_grades(course_name) 
        else:
            messagebox.showerror("Error", "Invalid grade entry selected.")

    # ----------------------------------------------------------------------
    # --- FINANCE FUNCTIONS ---
    # ----------------------------------------------------------------------
    def prompt_and_add_transaction(self, default_type):
        """Opens a Toplevel window to collect transaction details."""
        trans_window = tk.Toplevel(self.master)
        trans_window.title("Add New Transaction")
        trans_window.geometry("400x380")
        trans_window.transient(self.master)
        trans_window.grab_set()
        
        tk.Label(trans_window, text=f"Add {default_type}", font=("Helvetica", 14, "bold")).pack(pady=10)

        fields = [("Type:", ['Income', 'Expenses'], 'type_var'),
                  (f"Amount ({self.CURRENCY_SYMBOL}):", "Entry", 'amount_entry'),
                  ("Date (YYYY-MM-DD):", "Entry", 'date_entry'),
                  ("Notes:", "Entry", 'notes_entry')]
        
        data_fields = {}
        type_var = tk.StringVar(value=default_type)
        date_entry_var = tk.StringVar(value=time.strftime("%Y-%m-%d"))

        for i, (label_text, widget_type, var_name) in enumerate(fields):
            row = tk.Frame(trans_window)
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=label_text, width=15, anchor="w").pack(side="left")

            if widget_type == 'Entry':
                entry = tk.Entry(row, width=25)
                if var_name == 'date_entry':
                    entry.config(textvariable=date_entry_var)
                entry.pack(side="right", fill="x", expand=True)
                data_fields[var_name] = entry
            elif isinstance(widget_type, list):
                type_menu = ttk.Combobox(row, textvariable=type_var, values=['Income', 'Expenses'], 
                                         state="readonly", width=23)
                type_menu.config(state="disabled") 
                type_menu.pack(side="right", fill="x", expand=True)
                data_fields[var_name] = type_var

        # --- TAG SELECTION FIELDS ---
        tag_row = tk.Frame(trans_window)
        tag_row.pack(fill="x", padx=10, pady=5)
        tk.Label(tag_row, text="Select Tag:", width=15, anchor="w").pack(side="left")
        
        tag_names = list(self.DEFAULT_FINANCE_TAGS.keys())
        tag_var = tk.StringVar(value=tag_names[0] if tag_names else "")
        tag_menu = ttk.Combobox(tag_row, textvariable=tag_var, values=tag_names, state="readonly", width=23)
        tag_menu.pack(side="right", fill="x", expand=True)
        data_fields['tag_var'] = tag_var
        
        custom_tag_row = tk.Frame(trans_window)
        custom_tag_row.pack(fill="x", padx=10, pady=2)
        tk.Label(custom_tag_row, text="OR Custom Tag:", width=15, anchor="w").pack(side="left")
        custom_tag_entry = tk.Entry(custom_tag_row, width=25)
        custom_tag_entry.pack(side="right", fill="x", expand=True)
        data_fields['custom_tag_entry'] = custom_tag_entry
        
        tk.Label(trans_window, text="(Leave 'Custom Tag' blank if using a selected tag.)", 
                 font=("Helvetica", 9, "italic"), fg="gray").pack()
        
        tk.Button(trans_window, text="Save Transaction", 
                 command=lambda: self.save_transaction(trans_window, data_fields, type_var, tag_var, custom_tag_entry)).pack(pady=15)

    def save_transaction(self, trans_window, data_fields, type_var, tag_var, custom_tag_entry):
        t_type = type_var.get()
        t_amount_str = data_fields['amount_entry'].get().strip()
        t_date = data_fields['date_entry'].get().strip()
        t_notes = data_fields['notes_entry'].get().strip()
        
        selected_tag = tag_var.get()
        custom_tag = custom_tag_entry.get().strip()
        
        # --- 1. Determine Final Tag ---
        final_tag_name = custom_tag if custom_tag else selected_tag
        if not final_tag_name:
             messagebox.showerror("Error", "Please enter or select a Tag.")
             return
        
        # --- 2. Validate Amount ---
        try:
            t_amount = float(t_amount_str)
            if t_amount <= 0:
                raise ValueError("Amount must be positive.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid positive number for Amount.")
            return

        # Transaction tuple: (Tag Name, Amount, Date, Notes)
        new_transaction = (final_tag_name, t_amount, t_date, t_notes)
        
        self.finance_data[t_type].insert(0, new_transaction)
        
        # Add custom tag to default list/color mapping if it was a new custom tag
        if final_tag_name not in self.DEFAULT_FINANCE_TAGS:
            self.DEFAULT_FINANCE_TAGS[final_tag_name] = "🏷️" # Generic icon
            self.FINANCE_TAG_COLORS[final_tag_name] = "#7f8c8d" # Default custom color

        trans_window.destroy()
        self.save_data() # Save data immediately after adding
        self.show_upload_notification(f"💲 New {t_type} transaction '{final_tag_name}' recorded.")
        self.display_content("Finance")

    def delete_transaction(self, index, category):
        """
        Deletes a transaction from the finance data model.
        """
        try:
            # 1. Identify the transaction tuple from the filtered list (using the provided index)
            if category == 'Income':
                transaction_to_delete = self.filtered_income[index]
            else:
                transaction_to_delete = self.filtered_expenses[index]

            name, amount, _, _ = transaction_to_delete
            
            if messagebox.askyesno("Confirm Delete", 
                                   f"Are you sure you want to delete the {category.lower()} entry: '{name}' ({self.CURRENCY_SYMBOL}{amount:,.2f})?"):
                
                # 2. Find the index of this exact tuple in the ORIGINAL list
                original_index = self.finance_data[category].index(transaction_to_delete)
                
                # 3. Delete from the ORIGINAL list
                self.finance_data[category].pop(original_index) 
                
                # 4. Save the updated data to the file
                self.save_data() 
                
                self.show_upload_notification(f"🗑️ {category} entry '{name}' deleted.")
                # 5. Refresh the view (this will re-run filtering and redrawing)
                self.display_content("Finance") 
            
        except ValueError:
            messagebox.showerror("Error", "Transaction not found in the original list. Data consistency error.")
        except IndexError:
            messagebox.showerror("Error", "Transaction index error. Could not delete entry.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred during deletion: {e}")

    # ----------------------------------------------------------------------
    # --- FILTERING FUNCTIONS ---
    # ----------------------------------------------------------------------
    def set_date_preset(self, preset):
        """Sets the date filter variables based on a preset and triggers filtering."""
        
        self.active_date_preset.set(preset)
        self.filter_start_date_var.set("")
        self.filter_end_date_var.set("")
        self.apply_finance_filters()


    def create_filter_panel(self, parent_frame):
        """Creates the date and tag filter controls."""
        filter_frame = tk.LabelFrame(parent_frame, text="Transaction Filters", 
                                      font=("Helvetica", 10, "bold"), padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        control_frame = tk.Frame(filter_frame, bg="#f5f5f5")
        control_frame.pack(fill="x")

        # --- 1. Date Filter PRESETS (Side: Top Left) ---
        preset_frame = tk.LabelFrame(control_frame, text="Quick Date Presets", padx=10, pady=5)
        preset_frame.pack(side="left", padx=10, pady=5)
        
        presets = ["All Time", "This Week", "This Month", "This Year"]
        for preset in presets:
            btn = tk.Button(preset_frame, text=preset, 
                            command=lambda p=preset: self.set_date_preset(p),
                            font=("Helvetica", 9), relief="raised", padx=5, pady=2)
            btn.pack(side="left", padx=3)
            # Add a style update hook to highlight the active preset
            btn.bind("<Configure>", lambda e, b=btn, p=preset: self._update_preset_style(b, p))
            
        # --- 2. Custom Date Filter (Side: Below Presets) ---
        custom_date_frame = tk.LabelFrame(control_frame, text="Or Custom Date Range (YYYY-MM-DD)", padx=10, pady=5)
        custom_date_frame.pack(side="left", padx=10, pady=5)

        tk.Label(custom_date_frame, text="Start Date:").pack(side="left", padx=5)
        tk.Entry(custom_date_frame, textvariable=self.filter_start_date_var, width=12).pack(side="left", padx=5)
        
        tk.Label(custom_date_frame, text="End Date:").pack(side="left", padx=5)
        tk.Entry(custom_date_frame, textvariable=self.filter_end_date_var, width=12).pack(side="left", padx=5)

        # Bind events to automatically update the view when custom date changes
        self.filter_start_date_var.trace_add("write", lambda *args: self.clear_preset_on_custom_entry())
        self.filter_end_date_var.trace_add("write", lambda *args: self.clear_preset_on_custom_entry())

        # --- 3. Tag Filter (Side: Right) ---
        tag_frame = tk.LabelFrame(filter_frame, text="Filter by Tag (Multi-Select)", padx=10, pady=5)
        tag_frame.pack(fill="x", padx=10, pady=5) 
        
        tag_content_frame = tk.Frame(tag_frame)
        tag_content_frame.pack(fill="x")

        self.finance_filter_vars.clear()
        
        tags = sorted(self.DEFAULT_FINANCE_TAGS.keys())
        
        for i, tag in enumerate(tags):
            var = tk.BooleanVar(value=True) # Default: All tags selected
            self.finance_filter_vars[tag] = var
            
            # Use Checkbutton's command to trigger filter update
            chk = tk.Checkbutton(tag_content_frame, text=tag, variable=var, 
                                 bg="#f5f5f5", relief="flat", padx=3, pady=1,
                                 command=self.apply_finance_filters)
            chk.grid(row=i // 4, column=i % 4, sticky="w", padx=5)
            
        # Optional: Select/Deselect All Button
        def toggle_all_tags(select_all):
            for var in self.finance_filter_vars.values():
                var.set(select_all)
            self.apply_finance_filters()

        btn_frame = tk.Frame(tag_content_frame, bg="#f5f5f5")
        btn_frame.grid(row=(len(tags) // 4) + 1, column=0, columnspan=4, sticky="w", pady=5)

        tk.Button(btn_frame, text="Select All", command=lambda: toggle_all_tags(True), font=("Helvetica", 9), bg="#bdc3c7").pack(side="left", padx=5)
        tk.Button(btn_frame, text="Deselect All", command=lambda: toggle_all_tags(False), font=("Helvetica", 9), bg="#bdc3c7").pack(side="left")

    def _update_preset_style(self, button, preset_name):
        """Updates the visual style of the date preset buttons."""
        if self.active_date_preset.get() == preset_name:
            button.config(bg="#3498db", fg="white", relief="sunken")
        else:
            button.config(bg="#ecf0f1", fg="#34495e", relief="raised")
            
    def clear_preset_on_custom_entry(self):
        """When the user types in the custom date, clear the preset selection."""
        if self.filter_start_date_var.get() or self.filter_end_date_var.get():
             self.active_date_preset.set("")
             self.master.after(50, self.apply_finance_filters)
        else:
             self.set_date_preset("All Time")


    def calculate_preset_dates(self):
        """Calculates the start and end dates based on the active preset."""
        today = date.today()
        preset = self.active_date_preset.get()
        start = None
        end = today

        if preset == "This Week":
            start = today - timedelta(days=today.weekday())
        elif preset == "This Month":
            start = today.replace(day=1)
        elif preset == "This Year":
            start = today.replace(month=1, day=1)
        elif preset == "All Time":
            start = None
            end = None 

        # Override preset if custom fields are used
        start_date_str = self.filter_start_date_var.get().strip()
        end_date_str = self.filter_end_date_var.get().strip()

        if start_date_str or end_date_str:
            try:
                start = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else None
                end = datetime.strptime(end_date_str, "%Y-%m-%d").date() if end_date_str else None
            except ValueError:
                pass 
        
        return start, end


    def apply_finance_filters(self):
        """
        Applies date and tag filters to the original finance data 
        and updates the filtered lists and the UI.
        """
        
        # 1. Get filter criteria (Preset or Custom)
        start_date, end_date = self.calculate_preset_dates()
        
        selected_tags = {tag for tag, var in self.finance_filter_vars.items() if var.get()}
        
        # 2. Filtering Logic
        def filter_list(transaction_list):
            filtered = []
            for transaction_tuple in transaction_list:
                tag, amount, date_str, notes = transaction_tuple
                
                if tag not in selected_tags:
                    continue
                
                if start_date or end_date:
                    try:
                        transaction_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    except ValueError:
                        continue
                        
                    if start_date and transaction_date < start_date:
                        continue
                        
                    if end_date and transaction_date > end_date:
                        continue

                filtered.append(transaction_tuple)
            return filtered

        self.filtered_income = filter_list(self.finance_data['Income'])
        self.filtered_expenses = filter_list(self.finance_data['Expenses'])
        
        # 3. Recalculate Totals (for filtered data)
        filtered_income_total = sum(item[1] for item in self.filtered_income)
        filtered_expenses_total = sum(item[1] for item in self.filtered_expenses)
        
        # 4. Update UI
        self.update_finance_summary(filtered_income_total, filtered_expenses_total)
        self.redraw_transaction_lists(filtered_income_total, filtered_expenses_total)


    def update_finance_summary(self, total_income, total_expenses):
        """Updates the Balance and Summary labels in the Wallet Panel."""
        
        balance = total_income - total_expenses
        balance_color = "#2ecc71" if balance >= 0 else "#e74c3c"
        
        if hasattr(self, 'balance_label'):
            self.balance_label.config(text=f"{self.CURRENCY_SYMBOL}{balance:,.2f}", fg=balance_color)
            self.income_summary_label.config(text=f"TOTAL INCOME (Filtered): {self.CURRENCY_SYMBOL}{total_income:,.2f}")
            self.expenses_summary_label.config(text=f"TOTAL EXPENSES (Filtered): {self.CURRENCY_SYMBOL}{total_expenses:,.2f}")
            
    def redraw_transaction_lists(self, income_total, expenses_total):
        """Redraws both transaction lists using the filtered data."""
        
        if hasattr(self, 'income_list_frame') and hasattr(self, 'expenses_list_frame'):
            # Clear previous content
            for widget in self.income_list_frame.winfo_children():
                widget.destroy()
            for widget in self.expenses_list_frame.winfo_children():
                widget.destroy()
            
            # Redraw with new filtered data
            self.create_transaction_list_content(self.income_list_frame, 'Income', self.filtered_income, income_total)
            self.create_transaction_list_content(self.expenses_list_frame, 'Expenses', self.filtered_expenses, expenses_total)

    def create_transaction_list_content(self, list_frame, category, transactions, total_amount):
        """The core logic for drawing the transaction list content (separated for redraw), now including scrollbars."""
        
        header_color = "#2ecc71" if category == 'Income' else "#e74c3c"
        
        tk.Label(list_frame, text=f"{category} (Total: {self.CURRENCY_SYMBOL}{total_amount:,.2f})",
                 font=("Helvetica", 14, "bold"), fg="white", bg=header_color, pady=10).pack(fill="x")
                 
        # --- SCROLLABLE AREA SETUP ---
        scrollable_area = tk.Frame(list_frame, bg="#ffffff")
        scrollable_area.pack(fill="both", expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(scrollable_area, bg="#ffffff", highlightthickness=0)
        canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(scrollable_area, orient="vertical", command=canvas.yview)
        scrollbar.pack(side="right", fill="y")

        canvas.configure(yscrollcommand=scrollbar.set)
        
        transactions_container = tk.Frame(canvas, bg="#ffffff")
        canvas_window = canvas.create_window((0, 0), window=transactions_container, anchor="nw")

        transactions_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        # --- SCROLLABLE AREA SETUP END ---
        
        if not transactions:
            tk.Label(transactions_container, text=f"No {category.lower()} recorded or no results match filters.",
                     font=("Helvetica", 10, "italic"), fg="gray", bg="#ffffff").pack(pady=20, padx=10)
            return

        ttk.Separator(transactions_container, orient='horizontal').pack(fill="x")

        # Header Row for transactions_container
        header_row = tk.Frame(transactions_container, bg="#f5f5f5")
        header_row.pack(fill="x", pady=2)
        tk.Label(header_row, text="Tag/Source", font=("Helvetica", 10, "bold"), bg="#f5f5f5", width=20).pack(side="left", padx=(10, 0))
        tk.Label(header_row, text="Amount", font=("Helvetica", 10, "bold"), bg="#f5f5f5", width=10).pack(side="left")
        tk.Label(header_row, text="Date", font=("Helvetica", 10, "bold"), bg="#f5f5f5", width=10).pack(side="left")

        # Transaction rows: Tuple structure is (Tag Name, Amount, Date, Notes)
        for i, (tag_name, amount, date, notes) in enumerate(transactions):
            row_bg = "#f9f9f9" if i % 2 != 0 else "#ffffff" 
            
            row_frame = tk.Frame(transactions_container, bg=row_bg, padx=5, pady=2)
            row_frame.pack(fill="x")
            
            # --- ICON/TAG DISPLAY (Color-Coded) ---
            icon = self.DEFAULT_FINANCE_TAGS.get(tag_name, "🏷️")
            tag_color = self.FINANCE_TAG_COLORS.get(tag_name, "#7f8c8d") # Fallback color
            
            tag_display_frame = tk.Frame(row_frame, bg=tag_color, bd=0, relief="raised")
            tag_display_frame.pack(side="left", padx=5)
            
            name_label = tk.Label(tag_display_frame, text=f"{icon} {tag_name}", 
                                  font=("Helvetica", 10, "bold"), bg=tag_color, fg="white", 
                                  anchor="w", padx=5)
            name_label.pack(side="left", fill="x")
            # Show notes on click
            name_label.bind("<Button-1>", lambda event, n=notes, item=tag_name: messagebox.showinfo(f"{item} Details", f"Notes:\n{n}"))
            
            # Amount
            tk.Label(row_frame, text=f"{self.CURRENCY_SYMBOL}{amount:,.2f}", 
                     font=("Helvetica", 10, "bold"), bg=row_bg, fg=header_color, 
                     width=10, anchor="w").pack(side="left")
            
            # Date
            tk.Label(row_frame, text=date, font=("Helvetica", 10), 
                     bg=row_bg, width=10, anchor="w").pack(side="left")
                     
            # Delete Button (Uses index 'i' which is the index in the CURRENTLY FILTERED list)
            delete_button = tk.Button(row_frame, text="🗑️", bg=row_bg, fg="#e74c3c", 
                                     relief="flat", bd=0, padx=5,
                                     command=lambda index=i, cat=category: self.delete_transaction(index, cat))
            delete_button.pack(side="right")
            
            ttk.Separator(transactions_container, orient='horizontal').pack(fill="x")


    # ----------------------------------------------------------------------
    # --- NAVIGATION AND CARD FUNCTIONS (Updated to include Grades) ---
    # ----------------------------------------------------------------------
    def execute_log_off(self):
        """Saves data and closes the application."""
        if messagebox.askyesno("Log Off Confirmation", "Are you sure you want to log off and close the application?"):
            self.save_data() # SAVE DATA BEFORE CLOSING
            self.master.destroy()

    def create_sidebar_buttons(self):
        """Creates the navigational buttons in the sidebar."""
        
        title_label = tk.Label(self.sidebar_frame, text="Navigation", 
                               bg="#2c3e50", fg="white", 
                               font=("Helvetica", 14, "bold"), pady=15)
        title_label.pack(fill="x")

        for func_name in self.functions:
            if func_name == "Log Off":
                bg_color = "#e74c3c"
                active_bg_color = "#c0392b"
                command_action = self.execute_log_off
            else:
                bg_color = "#34495e"
                active_bg_color = "#1abc9c"
                command_action = lambda name=func_name: self.display_content(name)

            button = tk.Button(self.sidebar_frame, text=func_name, font=("Helvetica", 12),
                               bg=bg_color, fg="white",
                               activebackground=active_bg_color, activeforeground="white",
                               relief="raised", pady=10,
                               command=command_action)
            
            if func_name == "Log Off":
                tk.Frame(self.sidebar_frame, height=2, bg="#34495e").pack(fill="x", pady=(10, 5), padx=10)
                button.pack(fill="x", pady=(5, 15), padx=10)
            else:
                button.pack(fill="x", pady=5, padx=10)

    # ----------------------------------------------------------------------------------
    # --- HUB DISPLAY FUNCTIONS (Updated) ---
    # ----------------------------------------------------------------------------------
    def display_content(self, title):
        """Clears the main frame and displays the content for the selected function."""
        
        # Clear main frame
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        self.current_course = None
        self.current_tab = 'assignment'

        # This outer title remains, the main canvas will be placed below it
        tk.Label(self.main_frame, text=title, font=("Helvetica", 24, "bold"), 
                 bg="#ecf0f1", fg="#2c3e50", pady=20).pack(fill="x")
        
        if title == "Finance":
            self.display_finance_hub()
        elif title == "Courses":
            self.display_courses_hub()
        elif title == "Grades": 
            self.display_grades_hub()
        else:
            tk.Label(self.main_frame, text=f"Content for {title} will go here.", 
                     font=("Helvetica", 16, "italic"), bg="#ecf0f1", fg="gray").pack(pady=50)

    def display_finance_hub(self):
        """Displays the main Finance tracking hub with a MASTER scrollbar."""

        # --- 1. MASTER SCROLLABLE AREA SETUP ---
        # This canvas will hold EVERYTHING in the finance hub and will scroll
        main_canvas = tk.Canvas(self.main_frame, bg="#ecf0f1", highlightthickness=0)
        main_canvas.pack(side="left", fill="both", expand=True)

        main_scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=main_canvas.yview)
        main_scrollbar.pack(side="right", fill="y")
        
        main_canvas.configure(yscrollcommand=main_scrollbar.set)

        # This frame is what all the content will be placed in
        scrollable_content_frame = tk.Frame(main_canvas, bg="#ecf0f1")
        main_canvas.create_window((0, 0), window=scrollable_content_frame, anchor="nw")
        
        # This binding makes the scrollbar aware of the content's size
        scrollable_content_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))

        # --- ALL FINANCE WIDGETS NOW GO INTO 'scrollable_content_frame' ---

        # Initialize filtered lists
        self.filtered_income = self.finance_data['Income']
        self.filtered_expenses = self.finance_data['Expenses']
        
        # 2. My Wallet Panel
        wallet_panel = tk.LabelFrame(scrollable_content_frame, text="My Wallet", 
                                     font=("Helvetica", 12, "bold"), padx=15, pady=15)
        wallet_panel.pack(fill="x", padx=20, pady=10)
        
        balance_frame = tk.Frame(wallet_panel, bg="#ffffff")
        balance_frame.pack(pady=5)
        
        tk.Label(balance_frame, text="CURRENT BALANCE:", 
                 font=("Helvetica", 16, "bold"), bg="#ffffff").pack(side="left", padx=(0, 10))
        
        self.balance_label = tk.Label(balance_frame, text="₹0.00", 
                                       font=("Helvetica", 16, "bold"), bg="#ffffff")
        self.balance_label.pack(side="left")

        summary_frame = tk.Frame(wallet_panel, bg="#f5f5f5", padx=10, pady=5)
        summary_frame.pack(fill="x", expand=True, pady=10)
        
        self.income_summary_label = tk.Label(summary_frame, text="TOTAL INCOME (Filtered): ₹0.00", 
                                              font=("Helvetica", 10), bg="#f5f5f5")
        self.income_summary_label.pack(side="left", expand=True)
        
        self.expenses_summary_label = tk.Label(summary_frame, text="TOTAL EXPENSES (Filtered): ₹0.00", 
                                               font=("Helvetica", 10), bg="#f5f5f5")
        self.expenses_summary_label.pack(side="right", expand=True)
        
        # --- 3. Container for the two transaction lists ---
        # This frame helps organize the two lists side-by-side
        lists_container_frame = tk.Frame(scrollable_content_frame, bg="#ecf0f1")
        lists_container_frame.pack(fill="both", expand=True, pady=10)
        
        # We need to give columns weight so they expand equally
        lists_container_frame.grid_columnconfigure(0, weight=1)
        lists_container_frame.grid_columnconfigure(1, weight=1)

        self.income_list_frame = tk.Frame(lists_container_frame, bg="#ffffff", bd=1, relief="solid")
        self.income_list_frame.grid(row=0, column=0, sticky="nsew", padx=(20, 5))
        
        self.expenses_list_frame = tk.Frame(lists_container_frame, bg="#ffffff", bd=1, relief="solid")
        self.expenses_list_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 20))

        # --- 4. Add Buttons ---
        button_frame = tk.Frame(scrollable_content_frame, bg="#ecf0f1")
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="+ Add Income", font=("Helvetica", 12, "bold"),
                  bg="#2ecc71", fg="white", activebackground="#27ae60", relief="raised",
                  padx=15, pady=8, command=lambda: self.prompt_and_add_transaction("Income")).pack(side="left", padx=10)

        tk.Button(button_frame, text="+ Add Expense", font=("Helvetica", 12, "bold"),
                  bg="#e74c3c", fg="white", activebackground="#c0392b", relief="raised",
                  padx=15, pady=8, command=lambda: self.prompt_and_add_transaction("Expenses")).pack(side="left", padx=10)
        
        # --- 5. Your Filter Panel (at the bottom) ---
        self.create_filter_panel(scrollable_content_frame)
                  
        self.apply_finance_filters()

    def display_courses_hub(self):
        """Displays a card for each course."""
        
        tk.Label(self.main_frame, text="Your Courses", 
                 font=("Helvetica", 16, "bold"), fg="#2c3e50", bg="#ecf0f1").pack(pady=(0, 10))
                 
        tk.Button(self.main_frame, text="+ Add New Course", font=("Helvetica", 12, "bold"),
                  bg="#3498db", fg="white", activebackground="#2980b9", relief="raised",
                  padx=10, pady=5, command=self.prompt_and_add_course).pack(pady=(0, 20))

        cards_container = tk.Frame(self.main_frame, bg="#ecf0f1")
        cards_container.pack(fill="both", expand=True, padx=20)
        
        if not self.courses_list:
             tk.Label(cards_container, text="No courses added yet. Click '+ Add New Course' to begin.", 
                     font=("Helvetica", 14, "italic"), fg="gray", bg="#ecf0f1").pack(pady=50)
             return

        max_cols = 3
        
        for i, course_name in enumerate(self.courses_list):
            row = i // max_cols
            col = i % max_cols
            
            card = self.create_course_card(cards_container, course_name)
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
            
        for col in range(max_cols):
            cards_container.grid_columnconfigure(col, weight=1)

    # ----------------------------------------------------------------------
    # --- COURSE MANAGEMENT FUNCTIONS ---
    # ----------------------------------------------------------------------
    def create_course_card(self, parent_frame, course_name):
        """Creates a clickable card that navigates to the course details."""
        
        container = tk.Frame(parent_frame, bg="#ffffff", bd=2, relief="raised", padx=10, pady=10)
        
        header_frame = tk.Frame(container, bg="#ffffff")
        header_frame.pack(fill="x", pady=(0, 5))
        
        tk.Label(header_frame, text=course_name, font=("Helvetica", 18, "bold"), 
                 fg="#34495e", bg="#ffffff").pack(side="left")
        
        tk.Button(header_frame, text="🗑️", bg="#ffffff", fg="#e74c3c", 
                  relief="flat", bd=0, padx=5,
                  command=lambda name=course_name: self.delete_course(name)).pack(side="right")
                  
        ttk.Separator(container, orient='horizontal').pack(fill="x", pady=(0, 10))
        
        # --- Summary Section ---
        assignment_count = len(self.assignment_data.get(course_name, {}))
        material_count = len(self.material_data.get(course_name, []))
        
        tk.Label(container, text=f"Assignments: {assignment_count}", font=("Helvetica", 11), 
                 bg="#ffffff", anchor="w").pack(fill="x", padx=5)
                 
        tk.Label(container, text=f"Materials: {material_count}", font=("Helvetica", 11), 
                 bg="#ffffff", anchor="w").pack(fill="x", padx=5, pady=(2, 10))

        tk.Button(container, text="View Details", 
                  command=lambda name=course_name: self.display_course_details(name),
                  bg="#3498db", fg="white", relief="flat").pack(fill="x")
        
        return container
        
    def prompt_and_add_course(self):
        """Opens a simple dialog to get a new course name."""
        
        course_window = tk.Toplevel(self.master)
        course_window.title("Add New Course")
        course_window.geometry("300x150")
        course_window.transient(self.master)
        course_window.grab_set()

        tk.Label(course_window, text="Enter Course Name:", font=("Helvetica", 12)).pack(pady=10)
        
        course_name_entry = tk.Entry(course_window, width=30)
        course_name_entry.pack(padx=10)
        
        def save_course():
            new_name = course_name_entry.get().strip()
            if new_name and new_name not in self.courses_list:
                self.courses_list.append(new_name)
                # Initialize data structures for the new course
                self.assignment_data[new_name] = {}
                self.material_data[new_name] = []
                self.grades_data[new_name] = []
                
                self.save_data() # Save after adding
                course_window.destroy()
                self.show_upload_notification(f"📚 Course '{new_name}' added.")
                self.display_content("Courses")
            elif new_name in self.courses_list:
                 messagebox.showerror("Error", "This course name already exists.")
            else:
                 messagebox.showerror("Error", "Course name cannot be empty.")
                 
        tk.Button(course_window, text="Save Course", command=save_course).pack(pady=15)
        
    def delete_course(self, course_name):
        """Deletes a course and all its associated data."""
        
        if messagebox.askyesno("Confirm Delete", 
                               f"Are you sure you want to delete the course '{course_name}' and ALL its associated assignments, materials, and grades? This action cannot be undone."):
            
            if course_name in self.courses_list:
                self.courses_list.remove(course_name)
                
            # Use pop to safely remove data, avoiding KeyErrors if data doesn't exist
            self.assignment_data.pop(course_name, None)
            self.material_data.pop(course_name, None)
            self.grades_data.pop(course_name, None)
            
            self.save_data()
            self.show_upload_notification(f"🗑️ Course '{course_name}' deleted.")
            self.display_content("Courses")


    # ----------------------------------------------------------------------
    # --- COURSE DETAIL DISPLAY FUNCTIONS ---
    # ----------------------------------------------------------------------
    def display_course_details(self, course_name):
        """Displays the assignments and materials for a selected course."""
        
        self.current_course = course_name
        
        for widget in self.main_frame.winfo_children():
            widget.destroy()

        header_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        header_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Button(header_frame, text="< Back to Courses", 
                 command=lambda: self.display_content("Courses"),
                 font=("Helvetica", 10), relief="flat", bg="#bdc3c7", fg="#34495e").pack(side="left")

        tk.Label(header_frame, text=f"Course: {course_name}", font=("Helvetica", 24, "bold"), 
                 bg="#ecf0f1", fg="#2c3e50").pack(side="left", padx=20)
        
        # --- TABS (Assignments/Materials) ---
        tab_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        tab_frame.pack(fill="x", padx=20)
        
        self.assignment_tab_btn = tk.Button(tab_frame, text="Assignments", 
                                            command=lambda: self.switch_course_tab('assignment'),
                                            font=("Helvetica", 12, "bold"), relief="flat", pady=5)
        self.assignment_tab_btn.pack(side="left", padx=5)

        self.material_tab_btn = tk.Button(tab_frame, text="Study Materials", 
                                          command=lambda: self.switch_course_tab('material'),
                                          font=("Helvetica", 12, "bold"), relief="flat", pady=5)
        self.material_tab_btn.pack(side="left", padx=5)
        
        # --- CONTENT AREA ---
        self.course_content_frame = tk.Frame(self.main_frame, bg="#ecf0f1")
        self.course_content_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.switch_course_tab(self.current_tab)
        
    def switch_course_tab(self, tab_name):
        """Switches the view between Assignments and Materials."""
        self.current_tab = tab_name
        
        # Reset tab button styles
        self.assignment_tab_btn.config(bg="#bdc3c7", fg="#34495e")
        self.material_tab_btn.config(bg="#bdc3c7", fg="#34495e")

        # Clear content frame
        for widget in self.course_content_frame.winfo_children():
            widget.destroy()

        if tab_name == 'assignment':
            self.assignment_tab_btn.config(bg="#3498db", fg="white")
            self.display_assignments_for_course()
        elif tab_name == 'material':
            self.material_tab_btn.config(bg="#3498db", fg="white")
            self.display_materials_for_course()
            
    def display_assignments_for_course(self):
        """Displays the assignment groups for the current course."""
        
        tk.Button(self.course_content_frame, text="+ New Assignment Group", 
                  font=("Helvetica", 12, "bold"), bg="#2ecc71", fg="white", 
                  activebackground="#27ae60", relief="raised", padx=10, pady=5,
                  command=self.prompt_and_add_assignment_group).pack(pady=(0, 15))

        assignments = self.assignment_data.get(self.current_course, {})
        
        if not assignments:
             tk.Label(self.course_content_frame, text="No assignments added for this course yet.", 
                     font=("Helvetica", 12, "italic"), fg="gray", bg="#ecf0f1").pack(pady=50)
             return

        for group_name, files in assignments.items():
            self.create_assignment_group_widget(group_name, files)

    def create_assignment_group_widget(self, group_name, files):
        """Creates a visual group for an assignment, showing its files."""
        
        group_frame = tk.LabelFrame(self.course_content_frame, text=group_name, 
                                     font=("Helvetica", 12, "bold"), padx=10, pady=10,
                                     bg="#ffffff", bd=1, relief="solid")
        group_frame.pack(fill="x", pady=10)
        
        # --- File List ---
        files_frame = tk.Frame(group_frame, bg="#ffffff")
        files_frame.pack(fill="x")
        
        for i, (path, size, date, icon) in enumerate(files):
            file_entry_frame = tk.Frame(files_frame, bg="#f9f9f9" if i%2 != 0 else "#ffffff")
            file_entry_frame.pack(fill="x", pady=2)
            
            tk.Label(file_entry_frame, text=f"{icon} {os.path.basename(path)}", 
                     font=("Helvetica", 10, "bold"), width=30, anchor="w",
                     bg=file_entry_frame.cget('bg')).pack(side="left", padx=5)
            
            tk.Label(file_entry_frame, text=size, font=("Helvetica", 10), 
                     width=15, bg=file_entry_frame.cget('bg')).pack(side="left")
            
            tk.Label(file_entry_frame, text=date, font=("Helvetica", 10), 
                     width=20, bg=file_entry_frame.cget('bg')).pack(side="left")
                     
            tk.Button(file_entry_frame, text="View", relief="flat", bg="#3498db", fg="white",
                     command=lambda p=path: self.open_file_externally(p)).pack(side="left", padx=5)

            tk.Button(file_entry_frame, text="🗑️", bg=file_entry_frame.cget('bg'), fg="#e74c3c", 
                     relief="flat", bd=0, padx=5,
                     command=lambda g=group_name, idx=i: self.delete_file_from_group(g, idx)).pack(side="left")

        # --- Action Buttons for the Group ---
        button_frame = tk.Frame(group_frame, bg="#ffffff")
        button_frame.pack(fill="x", pady=(10, 0))

        tk.Button(button_frame, text="Add File(s)", command=lambda g=group_name: self.add_files_to_group(g)).pack(side="left", padx=5)
        tk.Button(button_frame, text="Delete Group", fg="#e74c3c", command=lambda g=group_name: self.delete_assignment_group(g)).pack(side="right")


    def display_materials_for_course(self):
        """Displays the list of study materials for the current course."""
        
        tk.Button(self.course_content_frame, text="+ Add Study Material", 
                  font=("Helvetica", 12, "bold"), bg="#2ecc71", fg="white", 
                  activebackground="#27ae60", relief="raised", padx=10, pady=5,
                  command=self.add_study_materials).pack(pady=(0, 15))
        
        materials = self.material_data.get(self.current_course, [])
        
        if not materials:
            tk.Label(self.course_content_frame, text="No study materials added yet.", 
                     font=("Helvetica", 12, "italic"), fg="gray", bg="#ecf0f1").pack(pady=50)
            return
            
        list_container = tk.Frame(self.course_content_frame, bg="#ffffff", bd=1, relief="solid")
        list_container.pack(fill="both", expand=True)

        for i, (path, size, date, icon) in enumerate(materials):
            row_bg = "#f9f9f9" if i % 2 != 0 else "#ffffff" 
            
            row_frame = tk.Frame(list_container, bg=row_bg, padx=10, pady=5)
            row_frame.pack(fill="x")
            
            tk.Label(row_frame, text=f"{icon} {os.path.basename(path)}", font=("Helvetica", 10, "bold"), 
                     bg=row_bg, width=30, anchor="w").pack(side="left", padx=(0, 5))
            
            tk.Label(row_frame, text=size, font=("Helvetica", 10), 
                     bg=row_bg, width=15).pack(side="left")
            
            tk.Label(row_frame, text=date, font=("Helvetica", 10), 
                     bg=row_bg, width=20).pack(side="left")
            
            tk.Button(row_frame, text="View", relief="flat", bg="#3498db", fg="white",
                     command=lambda p=path: self.open_file_externally(p)).pack(side="left", padx=5)

            tk.Button(row_frame, text="🗑️", bg=row_bg, fg="#e74c3c", 
                     relief="flat", bd=0, padx=5,
                     command=lambda idx=i: self.delete_study_material(idx)).pack(side="right")
            
            ttk.Separator(list_container, orient='horizontal').pack(fill="x")
            
    # ----------------------------------------------------------------------
    # --- FILE/ASSIGNMENT MANAGEMENT LOGIC ---
    # ----------------------------------------------------------------------
    def prompt_and_add_assignment_group(self):
        """Opens a dialog to get a name for a new assignment group."""
        
        group_window = tk.Toplevel(self.master)
        group_window.title("New Assignment Group")
        group_window.geometry("350x150")
        group_window.transient(self.master)
        group_window.grab_set()

        tk.Label(group_window, text="Enter Assignment Group Name (e.g., 'Lab 1'):", 
                 font=("Helvetica", 11)).pack(pady=10)
        
        group_name_entry = tk.Entry(group_window, width=40)
        group_name_entry.pack(padx=10)
        
        def save_group():
            new_name = group_name_entry.get().strip()
            if new_name and new_name not in self.assignment_data[self.current_course]:
                # Initialize with an empty list of files
                self.assignment_data[self.current_course][new_name] = []
                self.save_data()
                group_window.destroy()
                self.show_upload_notification(f"📁 Assignment group '{new_name}' created.")
                self.switch_course_tab('assignment')
            elif new_name in self.assignment_data[self.current_course]:
                 messagebox.showerror("Error", "This group name already exists for this course.")
            else:
                 messagebox.showerror("Error", "Group name cannot be empty.")
                 
        tk.Button(group_window, text="Save and Add Files", command=save_group).pack(pady=15)

    def delete_assignment_group(self, group_name):
        """Deletes an entire assignment group."""
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the assignment group '{group_name}' and all its files?"):
            if group_name in self.assignment_data.get(self.current_course, {}):
                del self.assignment_data[self.current_course][group_name]
                self.save_data()
                self.show_upload_notification(f"🗑️ Assignment group '{group_name}' deleted.")
                self.switch_course_tab('assignment')

    def add_files_to_group(self, group_name):
        """Opens a file dialog to add multiple files to an assignment group."""
        
        filepaths = filedialog.askopenfilenames(
            title=f"Select files for '{group_name}'",
            filetypes=(("All files", "*.*"), 
                       ("PDF documents", "*.pdf"), 
                       ("Word documents", "*.docx"))
        )
        
        if filepaths:
            for path in filepaths:
                file_size = self._get_file_size(path)
                file_date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(path)))
                file_icon = self._get_file_icon(os.path.basename(path))
                
                # Append tuple: (Path, Size, Date, Icon)
                self.assignment_data[self.current_course][group_name].append(
                    (path, file_size, file_date, file_icon)
                )
            
            self.save_data()
            self.show_upload_notification(f"✅ {len(filepaths)} file(s) added to '{group_name}'.")
            self.switch_course_tab('assignment')

    def delete_file_from_group(self, group_name, file_index):
        """Deletes a single file from an assignment group by its index."""
        
        group_files = self.assignment_data.get(self.current_course, {}).get(group_name, [])
        
        if 0 <= file_index < len(group_files):
            file_path = group_files[file_index][0]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the file '{os.path.basename(file_path)}'?"):
                self.assignment_data[self.current_course][group_name].pop(file_index)
                self.save_data()
                self.show_upload_notification(f"🗑️ File '{os.path.basename(file_path)}' deleted.")
                self.switch_course_tab('assignment')

    def add_study_materials(self):
        """Opens a file dialog to add multiple study material files."""
        
        filepaths = filedialog.askopenfilenames(
            title="Select Study Materials",
            filetypes=(("All files", "*.*"), 
                       ("PDF documents", "*.pdf"), 
                       ("PowerPoint", "*.pptx"))
        )
        
        if filepaths:
            for path in filepaths:
                file_size = self._get_file_size(path)
                file_date = time.strftime("%Y-%m-%d", time.gmtime(os.path.getmtime(path)))
                file_icon = self._get_file_icon(os.path.basename(path))
                
                # Append tuple to the list for the current course
                self.material_data.setdefault(self.current_course, []).append(
                    (path, file_size, file_date, file_icon)
                )
            
            self.save_data()
            self.show_upload_notification(f"✅ {len(filepaths)} material file(s) added.")
            self.switch_course_tab('material')

    def delete_study_material(self, file_index):
        """Deletes a single study material file by its index."""
        
        materials = self.material_data.get(self.current_course, [])
        
        if 0 <= file_index < len(materials):
            file_path = materials[file_index][0]
            if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the material '{os.path.basename(file_path)}'?"):
                self.material_data[self.current_course].pop(file_index)
                self.save_data()
                self.show_upload_notification(f"🗑️ Material '{os.path.basename(file_path)}' deleted.")
                self.switch_course_tab('material')
    
    def open_file_externally(self, filepath):
        """
        Opens a given file using the system's default application.
        Provides cross-platform compatibility.
        """
        try:
            if not os.path.exists(filepath):
                 messagebox.showerror("File Not Found", f"The file at path '{filepath}' no longer exists.")
                 return

            if sys.platform == "win32":
                os.startfile(filepath)
            elif sys.platform == "darwin": # macOS
                subprocess.call(["open", filepath])
            else: # linux
                subprocess.call(["xdg-open", filepath])
        except Exception as e:
            messagebox.showerror("Error Opening File", f"Could not open the file.\nError: {e}")

    # ----------------------------------------------------------------------
    # --- HELPER & UTILITY FUNCTIONS ---
    # ----------------------------------------------------------------------
    def show_upload_notification(self, message):
        """Displays a temporary notification at the top of the main frame."""
        
        if self.notification_label:
            self.notification_label.destroy()

        self.notification_label = tk.Label(self.master, text=message, 
                                         bg="#2c3e50", fg="white", 
                                         font=("Helvetica", 11, "bold"),
                                         padx=15, pady=5, relief="raised", bd=1)
        
        self.master.update_idletasks()
        
        self.notification_label.place(relx=0.5, rely=0.01, anchor="n")
        
        self.master.after(3000, self.hide_upload_notification)

    def hide_upload_notification(self):
        """Hides the temporary notification."""
        if self.notification_label:
            self.notification_label.destroy()
            self.notification_label = None
            
    def _get_file_icon(self, name):
        if name.lower().endswith(".pdf"): return "📄"
        if name.lower().endswith((".doc", ".docx")): return "📝"
        if name.lower().endswith((".pptx", ".ppt")): return "💻"
        if name.lower().endswith((".zip", ".rar")): return "📦"
        return "📁" 
    
    def _get_file_size(self, path):
        if path.startswith("PENDING") or not os.path.exists(path):
            return "1 KB" 
        try:
            size_bytes = os.path.getsize(path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024**2:
                return f"{size_bytes/1024:.1f} KB"
            elif size_bytes < 1024**3:
                return f"{size_bytes/1024**2:.1f} MB"
            else:
                return f"{size_bytes/1024**3:.1f} GB"
        except FileNotFoundError:
            return "N/A"

# --- Main Execution ---
if __name__ == "__main__":
    root = tk.Tk()
    app = CollegeApp(root)
    root.mainloop()