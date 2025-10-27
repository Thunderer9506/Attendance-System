from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import Manage_Data
import CTkMessagebox
from datetime import datetime, timedelta
import os # Added for file path checking
import sys # Added for safe exit on critical error

# --- Constants ---
BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
PHOTO_DIR = "Members Photo"
DEFAULT_PHOTO = "images/person.jpg"
MESSAGE_BOX = CTkMessagebox.CTkMessagebox

class Payment(ctk.CTkToplevel):
    """
    Toplevel window for managing member payments.
    Allows searching for a member, viewing their payment history,
    and adding new payment records.
    """
    
    def __init__(self, parent):
        """
        Initializes the Payment window and database connection.
        """
        super().__init__(parent)
        print("[INFO] Initializing 'Payment' window...")
        self.title("Member Payment")
        self.geometry("1400x800")
        ctk.set_appearance_mode('dark')
        
        try:
            self.db = Manage_Data.DatabaseManager("GYM.db")
        except Exception as e:
            print(f"[CRITICAL] Payment: Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error", message=f"Could not load database: {e}", icon="cancel")
            self.destroy()
            return
            
        self.person_id = None # Store the ID of the currently searched member
        self_data = [] # Will be populated by refresh_payment_table
        
        self.layout()
        self.refresh_payment_table() # Load all payment data on startup
        
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
        Creates and places all widgets for the Payment window.
        """
        print("[INFO] Building 'Payment' layout...")
        # --- Left Panel (Info Frame) ---
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        
        ctk.CTkLabel(infoFrame, text='Payment', font=("Poppins", 30, "bold")).pack()
        
        # Display for the member's photo
        self.person_photo(infoFrame).pack(padx=20, pady=10, anchor='n')
        
        # --- Search Fields ---
        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth (DD-MM-YYYY)', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No. (10 digits)', '9674528439')
        
        # --- Payment Fields ---
        paymentFrame = ctk.CTkFrame(entryFrame, fg_color='transparent')
        self.payment_date_entry = self.labelEntry_Component(paymentFrame, 'Payment Date (DD-MM-YYYY)', f"{datetime.now().strftime('%d-%m-%Y')}")
        
        ctk.CTkLabel(paymentFrame, text="Amount", font=LABEL_FONT).pack(anchor='w')
        self.amount_ComboBox = ctk.CTkComboBox(paymentFrame,
                                               values=["Monthly : 700", "Quarterly : 1800", "Half-yearly : 3000", "Yearly : 4800"],
                                               font=LABEL_FONT)
        self.amount_ComboBox.pack(fill='x', pady=5)
        self.amount_ComboBox.set("Monthly : 700") # Default value
        
        ctk.CTkLabel(paymentFrame, text="Payment Method", font=LABEL_FONT).pack(anchor='w')
        self.payment_method_ComboBox = ctk.CTkComboBox(paymentFrame, values=["Online", "Cash"], font=LABEL_FONT)
        self.payment_method_ComboBox.pack(fill='x', pady=5)
        self.payment_method_ComboBox.set("Online") # Default value
        
        paymentFrame.pack(padx=5, anchor='w', pady=20)
        entryFrame.pack(padx=5, anchor='w', pady=20)
        
        # --- Buttons ---
        search_button = ctk.CTkButton(infoFrame, text='Search User', font=BUTTON_FONT,
                                          fg_color="#fff", corner_radius=7, text_color='#000000',
                                          hover_color="#CAF4FF", command=self.search_user)
        search_button.pack(fill='x', padx=20, expand=True)
        
        payment_button = ctk.CTkButton(infoFrame, text='Add Payment', font=BUTTON_FONT,
                                           fg_color="#fff", corner_radius=7, text_color='#000000',
                                           hover_color="#CAF4FF", command=self.add_payment)
        payment_button.pack(fill='x', padx=20, expand=True, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # --- Right Panel (Table Frame) ---
        tableFrame = ctk.CTkFrame(self, fg_color='transparent')
        
        # Note: 'full_name' is included, but it is NOT in the Payment table.
        # We will populate it using a JOIN (or a Python-side map).
        column_headings = ("id", "member_id", "full_name", 'payment_date', "amount", "payment_method")
        
        self.table = ttk.Treeview(tableFrame, columns=column_headings, show='headings')
        
        for col in column_headings:
            self.table.heading(col, text=col.replace("_", " ").title())
            if col == 'id' or col == 'member_id':
                self.table.column(col, width=40, anchor='center')
            elif col == 'full_name':
                self.table.column(col, width=150)
            else:
                self.table.column(col, width=100, anchor='center')
                
        self.table.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Scrollbars
        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.pack(side='right', fill='y')
        
        table_scrollbar_x = ttk.Scrollbar(tableFrame, orient='horizontal', command=self.table.xview)
        self.table.configure(xscrollcommand=table_scrollbar_x.set)
        table_scrollbar_x.pack(side='bottom', fill='x')
        
        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
    
    def refresh_payment_table(self):
        """
        Clears and repopulates the payment table with ALL payments from all members.
        This is the correct relational method, mapping member IDs to names.
        """
        print("[INFO] Refreshing full payment table...")
        # Clear existing items
        for item in self.table.get_children():
            self.table.delete(item)
            
        try:
            # 1. Get all payments
            # Use the new secure function from Manage_Data.py
            all_payments = self.db.get_all_from_table('Payment')
            
            # 2. Get all members to create a name map
            members_list = self.db.get_all_from_table('Members')
            # Create a dictionary: {1: 'Tony Stark', 2: 'Steve Rogers'}
            member_map = {member[0]: member[1] for member in members_list} # m[0] is id, m[1] is full_name
            
            # 3. Populate table
            for p in all_payments:
                # p = (id, member_id, payment_date, amount, payment_method)
                member_id = p[1]
                member_name = member_map.get(member_id, f"ID {member_id} Not Found")
                
                # Build the row to match table columns
                table_row = (p[0], member_id, member_name, p[2], p[3], p[4])
                self.table.insert(parent='', index='end', values=table_row)
                
            print(f"[INFO] Table refreshed with {len(all_payments)} payment records.")
        
        except Exception as e:
            print(f"[ERROR] Failed to refresh payment table: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load payment data:\n{e}", icon="cancel")

    def person_photo(self, parent):
        """
        Creates the frame and label for displaying the member's photo.
        Loads a default placeholder image.
        """
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        image_size = (300, 300)
        
        try:
            default_image = Image.open(DEFAULT_PHOTO)
        except FileNotFoundError:
            print(f"[ERROR] Default photo '{DEFAULT_PHOTO}' not found. Creating placeholder.")
            # Create a black placeholder if default is missing
            default_image = Image.new("RGB", image_size, (10, 10, 10))
            
        default_image = default_image.resize(image_size, Image.LANCZOS)
        self.image_person = ctk.CTkImage(default_image, size=image_size)
        
        self.image_label = ctk.CTkLabel(frame, image=self.image_person, text="")
        self.image_label.pack()
        return frame
    
    def search_user(self):
        """
        Searches for a member using the form fields and updates the table
        to show only their payment history.
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
                
                # Get payments for *only* this member
                # Use the new secure function
                payment_data = self.db.get_data_by_member_id("Payment", self.person_id)
                
                # Clear and update table with only this user's payments
                for item in self.table.get_children():
                    self.table.delete(item)
                
                for p in payment_data:
                    # p = (id, member_id, payment_date, amount, payment_method)
                    # We already have the name, so we can build the row
                    table_row = (p[0], p[1], name, p[2], p[3], p[4])
                    self.table.insert(parent='', index='end', values=table_row)
                
                # --- Load Member Photo (Safely) ---
                image_path = os.path.join(PHOTO_DIR, f"{self.person_id}.jpg")
                try:
                    new_image = Image.open(image_path)
                    new_image = new_image.resize((300, 300), Image.LANCZOS)
                    self.image_person.configure(dark_image=new_image, size=(300, 300))
                    print(f"[INFO] Loaded photo: {image_path}")
                except FileNotFoundError:
                    print(f"[WARN] Photo not found for member ID {self.person_id} at {image_path}")
                    MESSAGE_BOX(title="Info", message="Member found, but no photo exists.", icon="info")
                    # Load default photo if member-specific one isn't found
                    default_img = Image.open(DEFAULT_PHOTO).resize((300, 300), Image.LANCZOS)
                    self.image_person.configure(dark_image=default_img, size=(300, 300))
                
            else:
                print("[WARN] No matching member found.")
                self.person_id = None
                MESSAGE_BOX(title="Error", message="No matching member found", icon="cancel")
                # No user found, refresh table to show all payments
                self.refresh_payment_table()

        except Exception as e:
            print(f"[ERROR] Error during user search: {e}")
            MESSAGE_BOX(title="Error", message=f"An error occurred: {e}", icon="cancel")

    def add_payment(self):
        """
        Adds a new payment record for the currently searched member.
        """
        print("[INFO] 'Add Payment' button clicked...")
        date = self.payment_date_entry.get().strip()
        method = self.payment_method_ComboBox.get()
        amount_str = self.amount_ComboBox.get()
        
        # --- 1. Validate fields ---
        if not date or not method:
            MESSAGE_BOX(title="Error", message="Please fill all payment fields", icon="cancel")
            return
            
        # Check if a user has been searched and found
        if self.person_id is None:
            MESSAGE_BOX(title="Error", message="Please search for and select a member first", icon="cancel")
            return
            
        # --- 2. Safely parse amount ---
        try:
            amount = float(amount_str.split(" : ")[1])
        except (IndexError, ValueError, TypeError):
            print(f"[ERROR] Invalid amount string: {amount_str}")
            MESSAGE_BOX(title="Error", message="Invalid amount selected. Please check the amount dropdown.", icon="cancel")
            return
        
        # --- 3. Add payment to database ---
        try:
            print(f"[INFO] Adding payment for member ID {self.person_id}: {amount}, {method}")
            # Use the new relational-safe function (no name passed)
            self.db.insert_payment(self.person_id, date, amount, method)
            
            # --- 4. Update member's status and membership dates ---
            self.update_member_payment_status(self.person_id)
            
            # --- 5. Refresh table to show new payment ---
            # We call search_user() again to reload this user's data
            self.search_user() 
            
            MESSAGE_BOX(title="Success", message="Payment added successfully", icon="check")
            
        except Exception as e:
            print(f"[ERROR] Failed to add payment or update status: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to add payment: {e}", icon="cancel")
            
    def update_member_payment_status(self, member_id):
        """
        Updates the member's status to 'PAID' and calculates their new
        membership start and end dates based on their subscription.

        Args:
            member_id (int): The ID of the member to update.
        """
        print(f"[INFO] Updating payment status for member ID: {member_id}")
        try:
            # 1. Get member's subscription type
            # Use new secure function
            member_data = self.db.get_data_by_member_id("Members", member_id)
            if not member_data:
                print(f"[ERROR] Cannot update status: Member ID {member_id} not found.")
                return
                
            # member_data[0][8] is 'membership_type'
            subscription = member_data[0][8] 
            print(f"[INFO] Member subscription type: {subscription}")
            
            # 2. Calculate dates
            start_date = datetime.now()
            if subscription == 'Monthly':
                end_date = start_date + timedelta(days=30)
            elif subscription == 'Quarterly':
                end_date = start_date + timedelta(days=90)
            elif subscription == 'Half-yearly':
                end_date = start_date + timedelta(days=182) # Approx 6 months
            elif subscription == 'Yearly':
                end_date = start_date + timedelta(days=365)
            else:
                print(f"[WARN] Invalid membership type '{subscription}'. Cannot update dates.")
                raise ValueError(f"Invalid membership type: {subscription}")
            
            start_date_str = start_date.strftime('%d-%m-%Y')
            end_date_str = end_date.strftime('%d-%m-%Y')

            # 3. Update database using new secure function
            # Note: The 'row_id' for 'Members' table is the 'member_id'
            print(f"[INFO] Setting status=PAID, start={start_date_str}, end={end_date_str}")
            self.db.update_field_by_id("Members", member_id, "member_status", "PAID")
            self.db.update_field_by_id("Members", member_id, "membership_start_date", start_date_str)
            self.db.update_field_by_id("Members", member_id, "membership_end_date", end_date_str)
            print("[SUCCESS] Member payment status updated.")
            
        except (ValueError, TypeError) as e:
            # Handle the 'Invalid membership type'
            print(f"[ERROR] Failed to update member dates: {e}")
            MESSAGE_BOX(title="Error", message=f"Payment added, but could not update member dates.\n\nError: {e}", icon="warning")
        except (IndexError) as e:
            # Handle member_data[0][8] failing
            print(f"[ERROR] Failed to read member data to update status: {e}")
            MESSAGE_BOX(title="Error", message=f"Payment added, but could not update member status.\n\nError: {e}", icon="warning")
        except Exception as e:
            # Catch-all for other DB errors
            print(f"[ERROR] A critical error occurred in update_member_payment_status: {e}")
            
