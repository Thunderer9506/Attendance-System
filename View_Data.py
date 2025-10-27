from PIL import Image, ImageTk
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import ttk
import Manage_Data
import os # Added for file path checking
import sys # Added for safe exit on critical error

# --- Constants ---
BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
PHOTO_DIR = "Members Photo"
DEFAULT_PHOTO = "images/person.jpg"
MESSAGE_BOX = CTkMessagebox

class ViewData(ctk.CTkToplevel):
    """
    Toplevel window for viewing all data tables (Members, Attendance, Payment).
    Allows for filtering data by searching for a specific member.
    """
    
    def __init__(self, parent):
        """
        Initializes the ViewData window, database connection, and default state.
        """
        super().__init__(parent)
        print("[INFO] Initializing 'View Data' window...")
        self.title("View Member Data")
        self.geometry("1400x750")
        ctk.set_appearance_mode('dark')
        
        try:
            self.db = Manage_Data.DatabaseManager("GYM.db")
        except Exception as e:
            print(f"[CRITICAL] ViewData: Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error", message=f"Could not load database: {e}", icon="cancel")
            self.destroy()
            return
            
        self.person_id = None # Tracks the ID of the searched member
        self.current_table = ctk.StringVar(value='Members') # Tracks current table
        self.table_frame = None # Will hold the current ttk.Treeview frame
        self.default_image = None # To store the loaded default image

        self.layout()
        self.display_table() # Display the default table ("Members") on startup
        
    def labelEntry_Component(self, parent, text, placeholder):
        """
        Helper function to create a standardized Label + Entry pair.

        Args:
            parent (ctk.CTkFrame): The parent frame to place the widget in.
            text (str): The text for the label.
            placeholder (str): The placeholder text for the entry.

        Returns:
            ctk.CTkEntry: The created entry widget.
        """
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        ctk.CTkLabel(frame, text=text, font=LABEL_FONT).pack(anchor='w')
        entry = ctk.CTkEntry(frame, font=LABEL_FONT, width=500, placeholder_text=placeholder)
        entry.pack(fill='x', expand=True)
        frame.pack(fill='x', pady=5)
        return entry
       
    def layout(self):
        """
        Creates and places all widgets for the ViewData window.
        """
        print("[INFO] Building 'View Data' layout...")
        # --- Left Panel (Info Frame) ---
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        
        ctk.CTkLabel(infoFrame, text='View Data', font=("Poppins", 30, 'bold')).pack()
        
        # Create and pack person_photo_frame
        self.person_photo(infoFrame).pack(padx=20, pady=10, anchor='n')

        entry_Frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entry_Frame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entry_Frame, 'Date of Birth (DD-MM-YYYY)', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entry_Frame, 'Phone No. (10 digits)', '9674528439')
        
        ctk.CTkLabel(entry_Frame, text="Table", font=LABEL_FONT).pack(anchor='w')
        self.table_ComboBox = ctk.CTkComboBox(
            entry_Frame, 
            values=["Members", "Attendance", "Payment"], 
            font=LABEL_FONT,
            variable=self.current_table,
            command=self.on_table_select) # Changed command
        self.table_ComboBox.pack(fill='x', pady=5)
        
        entry_Frame.pack(fill='x', padx=20, pady=30)
        
        # Search button
        ctk.CTkButton(infoFrame, text='Search User', font=("Poppins", 20), width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.search_user).pack(fill='x', padx=20, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # --- Right Panel (Table Container) ---
        # This frame will *hold* the dynamic table_frame
        self.table_container = ctk.CTkFrame(self, fg_color='transparent')
        self.table_container.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)

    def on_table_select(self, choice):
        """
        Called when the user selects a new table from the ComboBox.
        It clears the current search and refreshes the table.
        
        Args:
            choice (str): The selected table name (e.g., "Members").
        """
        print(f"[INFO] Table selected: {choice}")
        self.person_id = None # Clear the active user search
        
        # Clear search fields
        self.full_name_entry.delete(0, 'end')
        self.dob_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        
        self.reset_photo() # Reset to default photo
        self.display_table() # Re-display the (now different) table

    def display_table(self):
        """
        The main table-rendering function.
        Destroys the old table and creates a new one based on the
        current state (self.current_table and self.person_id).
        """
        table_name = self.current_table.get()
        print(f"[INFO] Displaying table '{table_name}'. User ID: {self.person_id}")

        # 1. Destroy the old table frame if it exists
        if self.table_frame:
            self.table_frame.destroy()
            
        # 2. Create a new frame to hold the new table and scrollbars
        # This frame is placed inside the self.table_container
        self.table_frame = ctk.CTkFrame(self.table_container, fg_color='transparent')
        self.table_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 3. Get all member data for name mapping
        try:
            members_list = self.db.get_all_from_table('Members')
            # Create a dictionary: {1: 'Tony Stark', 2: 'Steve Rogers'}
            member_map = {member[0]: member[1] for member in members_list} # m[0] is id, m[1] is full_name
        except Exception as e:
            print(f"[ERROR] Failed to build member map: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load member list: {e}", icon="cancel")
            return

        # 4. Define columns and fetch data based on the selected table
        cols = ()
        data_to_display = []

        try:
            if table_name == "Members":
                cols = ("id", "full_name", "date_of_birth", "phone_number", "gender", "address", 
                        "member_status", "join_date", "membership_type", "membership_start_date", 
                        "membership_end_date", "emergency_name", "emergency_number")
                
                # If a user is searched, get their data; otherwise, get all members
                data = (self.db.get_data_by_member_id("Members", self.person_id)
                        if self.person_id else members_list)
                data_to_display = data # Data is already in the correct format

            elif table_name == "Attendance":
                cols = ("id", "member_id", "full_name", "date", "check_in_time")
                
                # Get either specific user or all data
                # This data will NOT have names
                raw_data = (self.db.get_data_by_member_id("Attendance", self.person_id)
                            if self.person_id else self.db.get_all_from_table("Attendance"))
                
                # Manually build the table rows with the correct name
                for row in raw_data: # row = (id, member_id, date, check_in_time)
                    name = member_map.get(row[1], f"ID {row[1]} Not Found")
                    data_to_display.append((row[0], row[1], name, row[2], row[3]))

            elif table_name == "Payment":
                cols = ("id", "member_id", "full_name", "payment_date", "amount", "payment_method")
                
                raw_data = (self.db.get_data_by_member_id("Payment", self.person_id)
                            if self.person_id else self.db.get_all_from_table("Payment"))
                
                # Manually build the table rows with the correct name
                for row in raw_data: # row = (id, member_id, date, amount, method)
                    name = member_map.get(row[1], f"ID {row[1]} Not Found")
                    data_to_display.append((row[0], row[1], name, row[2], row[3], row[4]))

        except Exception as e:
            print(f"[ERROR] Failed to fetch data for table '{table_name}': {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load data for {table_name}:\n{e}", icon="cancel")
            return

        # 5. Create and populate the Treeview
        table = ttk.Treeview(self.table_frame, columns=cols, show='headings')
        
        for col in cols:
            text = col.replace("_", " ").title()
            table.heading(col, text=text)
            # Set column widths
            if col in ('id', 'member_id'):
                table.column(col, width=40, anchor='center')
            elif col == 'full_name':
                table.column(col, width=150)
            elif col == 'address':
                table.column(col, width=200)
            else:
                table.column(col, width=100, anchor='center')
        
        table.pack(fill='both', expand=True)

        for row in data_to_display:
            table.insert(parent='', index='end', values=row)
            
        # 6. Add Scrollbars
        table_scrollbar_y = ttk.Scrollbar(self.table_frame, orient='vertical', command=table.yview)
        table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.pack(side='right', fill='y')
        
        table_scrollbar_x = ttk.Scrollbar(self.table_frame, orient='horizontal', command=table.xview)
        table.configure(xscrollcommand=table_scrollbar_x.set)
        table_scrollbar_x.pack(side='bottom', fill='x')

    def person_photo(self, parent):
        """
        Creates the frame and label for displaying the member's photo.
        Loads and caches a default placeholder image.
        """
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        image_size = (300, 300)
        
        try:
            # Load the default image once and store it
            self.default_image = Image.open(DEFAULT_PHOTO)
            self.default_image = self.default_image.resize(image_size, Image.LANCZOS)
        except FileNotFoundError:
            print(f"[ERROR] Default photo '{DEFAULT_PHOTO}' not found. Creating placeholder.")
            self.default_image = Image.new("RGB", image_size, (10, 10, 10))
            
        self.image_person = ctk.CTkImage(self.default_image, size=image_size)
        
        self.image_label = ctk.CTkLabel(frame, image=self.image_person, text="")
        self.image_label.pack()
        return frame

    def reset_photo(self):
        """Resets the image label to the default placeholder."""
        print("[INFO] Resetting photo to default.")
        if self.default_image:
            self.image_person.configure(dark_image=self.default_image, size=(300, 300))
        
    def search_user(self):
        """
        Searches for a member using the form fields.
        If found, sets self.person_id and refreshes the table to show their data.
        If not found, clears self.person_id and refreshes to show all data.
        """
        print("[INFO] Searching for user...")
        name = self.full_name_entry.get().strip().title()
        dob = self.dob_entry.get().strip()
        phone = self.phone_entry.get().strip()
            
        if not name or not dob or not phone:
            MESSAGE_BOX(title="Error", message="Please fill all fields (Name, DOB, Phone)", icon="cancel")
            return
        
        if len(phone) != 10 or not phone.isdigit():
            MESSAGE_BOX(title="Error", message="Phone Number must be 10 digits.", icon="cancel")
            return
            
        try:
            # Use the new secure function from Manage_Data.py
            member_data = self.db.get_member_by_details(name, dob, phone)
            
            if member_data:
                self.person_id = member_data[0] # member_data[0] is the 'id'
                print(f"[INFO] Member found with ID: {self.person_id}")
                
                # --- Load Member Photo (Safely) ---
                image_path = os.path.join(PHOTO_DIR, f"{self.person_id}.jpg")
                try:
                    new_image = Image.open(image_path)
                    new_image = new_image.resize((300, 300), Image.LANCZOS)
                    self.image_person.configure(dark_image=new_image, size=(300, 300))
                    print(f"[INFO] Loaded photo: {image_path}")
                except FileNotFoundError:
                    print(f"[WARN] Photo not found for member ID {self.person_id} at {image_path}")
                    self.reset_photo()
                    MESSAGE_BOX(title="Info", message="Member found, but no photo exists.", icon="info")
                
            else:
                print("[WARN] No matching member found.")
                self.person_id = None
                self.reset_photo()
                MESSAGE_BOX(title="Error", message="No matching member found", icon="cancel")
        
        except Exception as e:
            print(f"[ERROR] Error during user search: {e}")
            self.person_id = None
            self.reset_photo()
            MESSAGE_BOX(title="Error", message=f"An error occurred: {e}", icon="cancel")
            
        # Finally, refresh the table.
        # It will either show the found user's data or all data (if person_id is None)
        self.display_table()
