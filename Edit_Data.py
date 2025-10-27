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

# Define the fields for the Members table
MEMBER_FIELDS = [
    "full_name", "date_of_birth", "phone_number", "gender", "address", 
    "member_status", "join_date", "membership_type", "membership_start_date", 
    "membership_end_date", "emergency_name", "emergency_number"
]

class EditData(ctk.CTkToplevel):
    """
    Toplevel window for editing and deleting member data.
    This window is specifically for the 'Members' table.
    """
    
    def __init__(self, parent):
        """
        Initializes the EditData window, database connection, and default state.
        """
        super().__init__(parent)
        print("[INFO] Initializing 'Edit Data' window...")
        self.title("Edit Member Data")
        self.geometry("1400x750")
        ctk.set_appearance_mode('dark')
        
        try:
            self.db = Manage_Data.DatabaseManager("GYM.db")
        except Exception as e:
            print(f"[CRITICAL] EditData: Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error", message=f"Could not load database: {e}", icon="cancel")
            self.destroy()
            return
            
        self.person_id = None # Tracks the ID of the searched member
        self.current_field = ctk.StringVar(value=MEMBER_FIELDS[0]) # Track selected field
        self.table_frame = None # Will hold the current ttk.Treeview frame
        self.default_image = None # To store the loaded default image

        self.layout()
        self.refresh_table() # Display the 'Members' table on startup

        # Set a custom close action
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
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
        Creates and places all widgets for the EditData window.
        """
        print("[INFO] Building 'Edit Data' layout...")
        # --- Left Panel (Info Frame) ---
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        
        ctk.CTkLabel(infoFrame, text='Edit Data', font=("Poppins", 30, 'bold')).pack()
        
        # Create and pack person_photo_frame
        self.person_photo(infoFrame).pack(padx=20, pady=10, anchor='n')

        # --- Search Frame ---
        entry_Frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        
        ctk.CTkLabel(entry_Frame, text="Search for Member to Edit/Delete", font=LABEL_FONT, text_color="#77C3EC").pack(anchor='w', pady=(0, 5))
        self.full_name_entry = self.labelEntry_Component(entry_Frame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entry_Frame, 'Date of Birth (DD-MM-YYYY)', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entry_Frame, 'Phone No. (10 digits)', '9674528439')
        
        # --- Edit Frame ---
        ctk.CTkLabel(entry_Frame, text="Field to Edit", font=LABEL_FONT, text_color="#77C3EC").pack(anchor='w', pady=(20, 5))
        self.field_ComboBox = ctk.CTkComboBox(
            entry_Frame, 
            values=MEMBER_FIELDS,
            font=LABEL_FONT,
            variable=self.current_field
        )
        self.field_ComboBox.pack(fill='x', pady=5)
        
        # Frame to hold the dynamic label and entry
        self.fieldframe = ctk.CTkFrame(entry_Frame, fg_color='transparent')
        # Label text updates automatically via the textvariable
        ctk.CTkLabel(self.fieldframe, font=LABEL_FONT, textvariable=self.current_field).pack(anchor='w')
        self.fieldentry = ctk.CTkEntry(self.fieldframe, font=LABEL_FONT, width=500, placeholder_text="Enter new value...")
        self.fieldentry.pack(fill='x')
        self.fieldframe.pack(fill='x',pady=(10,0))
        
        entry_Frame.pack(fill='x', padx=20, pady=20)
        
        # --- Buttons ---
        
        # Search button
        ctk.CTkButton(infoFrame, text='Search Member', font=BUTTON_FONT, width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.search_user).pack(fill='x', padx=20, pady=10)
        
        # Edit/Delete button frame
        button_frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        
        self.edit_data_button = ctk.CTkButton(button_frame, text='Save Edit', font=BUTTON_FONT,width=120,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.edit_user)
        self.edit_data_button.pack(padx=10, pady=5, side='left', fill='x', expand=True)
        
        self.delete_data_button = ctk.CTkButton(button_frame, text='Delete', font=BUTTON_FONT,width=120,
            fg_color="#EF5A6F", corner_radius=7, text_color='#FFF1DB', 
            hover_color="#FFAAAA", command=self.delete_user)
        self.delete_data_button.pack(padx=10, pady=5, side='right', fill='x', expand=True)
    
        button_frame.pack(fill='x', padx=20, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # --- Right Panel (Table Container) ---
        # This frame will *hold* the dynamic table_frame
        self.table_container = ctk.CTkFrame(self, fg_color='transparent')
        self.table_container.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)

    def refresh_table(self):
        """
        The main table-rendering function.
        Destroys the old table and creates a new one for the 'Members' table.
        Filters by self.person_id if one is selected.
        """
        print(f"[INFO] Refreshing 'Members' table. User ID: {self.person_id}")

        # 1. Destroy the old table frame if it exists
        if self.table_frame:
            self.table_frame.destroy()
            
        # 2. Create a new frame to hold the new table and scrollbars
        self.table_frame = ctk.CTkFrame(self.table_container, fg_color='transparent')
        self.table_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # 3. Define columns and fetch data
        cols = MEMBER_FIELDS.copy()
        cols.insert(0, 'id') # Add 'id' to the beginning
        
        data_to_display = []
        try:
            if self.person_id:
                # Get data for the single searched member
                data_to_display = self.db.get_data_by_member_id("Members", self.person_id)
            else:
                # Get all members
                data_to_display = self.db.get_all_from_table("Members")
        
        except Exception as e:
            print(f"[ERROR] Failed to fetch data for 'Members' table: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load member data:\n{e}", icon="cancel")
            return

        # 4. Create and populate the Treeview
        self.table = ttk.Treeview(self.table_frame, columns=cols, show='headings')
        
        for col in cols:
            text = col.replace("_", " ").title()
            self.table.heading(col, text=text)
            # Set column widths
            if col == 'id':
                self.table.column(col, width=40, anchor='center')
            elif col == 'full_name':
                self.table.column(col, width=150)
            elif col == 'address':
                self.table.column(col, width=200)
            else:
                self.table.column(col, width=100, anchor='center')
        
        self.table.pack(side='left', fill='both', expand=True)

        for row in data_to_display:
            self.table.insert(parent='', index='end', values=row)
            
        # 5. Add Scrollbars
        table_scrollbar_y = ttk.Scrollbar(self.table_frame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.pack(side='right', fill='y')
        
        table_scrollbar_x = ttk.Scrollbar(self.table_frame, orient='horizontal', command=self.table.xview)
        self.table.configure(xscrollcommand=table_scrollbar_x.set)
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
            
    def clear_search(self):
        """Clears the search fields, resets the photo, and clears the person_id."""
        print("[INFO] Clearing search fields.")
        self.person_id = None
        self.full_name_entry.delete(0, 'end')
        self.dob_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.fieldentry.delete(0, 'end')
        self.reset_photo()

    def search_user(self):
        """
        Searches for a member using the form fields.
        If found, sets self.person_id and refreshes the table.
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
            # Use the new secure function
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
                self.clear_search()
                MESSAGE_BOX(title="Error", message="No matching member found", icon="cancel")
        
        except Exception as e:
            print(f"[ERROR] Error during user search: {e}")
            self.clear_search()
            MESSAGE_BOX(title="Error", message=f"An error occurred: {e}", icon="cancel")
            
        # Refresh the table. Will show just the user if found, or all users if not.
        self.refresh_table()

    def delete_user(self):
        """
        Deletes the currently searched member after confirmation.
        Offers 'Minimal' (sets status to 'Closed') or 'Full' (deletes all data).
        """
        print("[INFO] 'Delete' button clicked.")
        # 1. Check if a user is selected
        if self.person_id is None:
            MESSAGE_BOX(title="Error", message="Please search for a member to delete first.", icon="cancel")
            return

        # 2. First confirmation
        confirm_box = MESSAGE_BOX(title="Confirm Delete", 
                                  message=f"Are you sure you want to delete data for member ID {self.person_id}?",
                                  icon="question", option_1="YES", option_2="NO")
        
        if confirm_box.get() == "YES":
            print(f"[INFO] User confirmed first delete prompt for ID: {self.person_id}")
            # 3. Second confirmation (Minimal vs. Full)
            delete_type_box = MESSAGE_BOX(title="Delete Type",
                                          message="Choose delete method:\n\nMinimal: Sets member status to 'Closed'.\nFully: Deletes member and all related attendance/payment data.",
                                          icon="warning", option_1="Minimal Delete", option_2="Fully Delete", option_3="Cancel")
            
            delete_type = delete_type_box.get()

            try:
                if delete_type == "Fully Delete":
                    print(f"[WARN] Performing FULL DELETE for member ID: {self.person_id}")
                    # Uses cascading delete setup in DB
                    self.db.fully_delete_member(self.person_id)
                    MESSAGE_BOX(title="Success", message="Member fully deleted.", icon="check")
                
                elif delete_type == "Minimal Delete":
                    print(f"[INFO] Performing MINIMAL DELETE for member ID: {self.person_id}")
                    self.db.minimal_delete_member(self.person_id)
                    MESSAGE_BOX(title="Success", message="Member status set to 'Closed'.", icon="check")
                
                else:
                    print("[INFO] Delete action cancelled.")
                    return

                # If delete was successful, clear the search and refresh the table
                self.clear_search()
                self.refresh_table()

            except Exception as e:
                print(f"[ERROR] Failed to delete member ID {self.person_id}: {e}")
                MESSAGE_BOX(title="Error", message=f"Failed to delete member:\n{e}", icon="cancel")
        else:
            print("[INFO] Delete action cancelled by user.")

    def edit_user(self):
        """
        Updates a single field for the currently searched member.
        """
        print("[INFO] 'Save Edit' button clicked.")
        # 1. Check if a user is selected
        if self.person_id is None:
            MESSAGE_BOX(title="Error", message="Please search for a member to edit first.", icon="cancel")
            return
            
        # 2. Get data from fields
        field_to_edit = self.current_field.get()
        new_value = self.fieldentry.get().strip() # Use strip() but not title()
        
        if not new_value:
            MESSAGE_BOX(title="Error", message="The new value cannot be empty.", icon="cancel")
            return
            
        # 3. Phone/Gender validation
        if field_to_edit == 'phone_number' and (len(new_value) != 10 or not new_value.isdigit()):
            MESSAGE_BOX(title="Error", message="Phone Number must be 10 digits.", icon="cancel")
            return
        if field_to_edit == 'gender' and new_value.title() not in ('Male', 'Female'):
            MESSAGE_BOX(title="Error", message="Gender must be 'Male' or 'Female'.", icon="cancel")
            return
            
        print(f"[INFO] Attempting to update member ID {self.person_id}, field '{field_to_edit}' to '{new_value}'")
        try:
            # 4. Call the secure database function
            self.db.update_field_by_id(
                table_name="Members",
                row_id=self.person_id,
                field_name=field_to_edit,
                new_data=new_value
            )
            
            MESSAGE_BOX(title="Success", message=f"Member data updated successfully.", icon="check")
            
            # 5. Clear the entry field and refresh the table
            self.fieldentry.delete(0, 'end')
            self.refresh_table()
            
            
        except Exception as e:
            print(f"[ERROR] Failed to update member ID {self.person_id}: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to update data:\n{e}", icon="cancel")

    def on_close(self):
        """
        Handles the window 'X' button click.
        Safely closes the database connection.
        """
        print("[INFO] 'Edit Data' window closing...")
        try:
            self.db.close_connection()
        except Exception as e:
            print(f"[ERROR] Error closing DB connection: {e}")
        self.destroy() # Close the Toplevel window
