from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import cv2
import os
import Manage_Data
import CTkMessagebox
import sys

# --- Constants ---
BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
PHOTO_DIR = "Members Photo"
MESSAGE_BOX = CTkMessagebox.CTkMessagebox

class NewMember(ctk.CTkToplevel):
    """
    Toplevel window for adding a new member to the gym database.
    Includes capturing a photo, filling in details, and saving to the
    database and 'Members Photo' directory.
    """
    
    def __init__(self, parent):
        """
        Initializes the NewMember window, database connection, and camera.
        """
        super().__init__(parent)
        print("[INFO] Initializing 'New Member' window...")
        self.title("Add New Member")
        self.geometry("1400x800")
        ctk.set_appearance_mode('dark')

        try:
            self.db = Manage_Data.DatabaseManager("GYM.db")
            # Use the new secure function from Manage_Data.py
            self.data = self.db.get_all_from_table('Members')
        except Exception as e:
            print(f"[CRITICAL] NewMember: Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error", message=f"Could not load database: {e}", icon="cancel")
            self.destroy()
            return
            
        # --- Camera and Photo State ---
        self.cap = None
        self.captured_image = None  # Will store the captured cv2 frame
        self.is_camera_running = False

        # Ensure the photo directory exists
        self.create_photo_directory()

        # Build the UI
        self.layout()
        
        # Start the camera feed
        self.start_camera_feed()
        
        # Bind the window's close button ("X") to the on_close function
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_photo_directory(self):
        """
        Checks if 'Members Photo' directory exists, and creates it if not.
        """
        try:
            if not os.path.exists(PHOTO_DIR):
                print(f"[WARN] '{PHOTO_DIR}' not found. Creating directory.")
                os.makedirs(PHOTO_DIR)
            else:
                print(f"[INFO] Photo directory '{PHOTO_DIR}' already exists.")
        except OSError as e:
            print(f"[ERROR] Failed to create directory '{PHOTO_DIR}': {e}")
            MESSAGE_BOX(title="Error", message=f"Could not create photo directory: {e}", icon="cancel")

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
        Creates and places all widgets for the NewMember window.
        """
        print("[INFO] Building 'New Member' layout...")
        # --- Left Panel (Info Frame) ---
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        
        ctk.CTkLabel(infoFrame, text='Add New Member', font=("Poppins", 30, "bold")).pack()
        
        # Camera Feed Label
        self.video_label = ctk.CTkLabel(infoFrame, text="Starting Camera...", font=LABEL_FONT,
                                        width=320, height=240, fg_color="gray20",
                                        corner_radius=7)
        self.video_label.pack(anchor='n', pady=10)
        
        # Take Photo Button
        self.take_photo_button = ctk.CTkButton(infoFrame, text='Take Photo', font=BUTTON_FONT,
                                               fg_color="#fff", corner_radius=7, text_color='#000000',
                                               hover_color="#CAF4FF",
                                               command=self.capture_photo,
                                               state="disabled") # Disabled until camera is running
        self.take_photo_button.pack(fill='x', expand=True, pady=5)
        
        # --- Entry Fields ---
        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth (DD-MM-YYYY)', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No. (10 digits)', '9674528439')
        
        ctk.CTkLabel(entryFrame, text="Gender", font=LABEL_FONT).pack(anchor='w')
        self.gender_ComboBox = ctk.CTkComboBox(entryFrame, values=["Male", "Female", "Other"], font=LABEL_FONT)
        self.gender_ComboBox.pack(fill='x', pady=5)
        self.gender_ComboBox.set("Male") # Default value
        
        self.address_entry = self.labelEntry_Component(entryFrame, 'Address', '123 Main St, Anytown, USA')
        self.join_date_entry = self.labelEntry_Component(entryFrame, 'Joining Date (DD-MM-YYYY)', '20-05-2023')
        
        ctk.CTkLabel(entryFrame, text="Membership Type", font=LABEL_FONT).pack(anchor='w')
        self.membership_ComboBox = ctk.CTkComboBox(entryFrame, values=["Monthly", "Quarterly", "Half-yearly", "Yearly"], font=LABEL_FONT)
        self.membership_ComboBox.pack(fill='x', pady=5)
        self.membership_ComboBox.set("Monthly") # Default value
        
        self.membeship_start_date_entry = self.labelEntry_Component(entryFrame, 'Membership Start Date (DD-MM-YYYY)', '20-05-2023')
        self.membeship_end_date_entry = self.labelEntry_Component(entryFrame, 'Membership End Date (DD-MM-YYYY)', '20-06-2023')
        self.emergency_name_entry = self.labelEntry_Component(entryFrame, 'Emergency Name', 'John Doe')
        self.emergency_contact_entry = self.labelEntry_Component(entryFrame, 'Emergency Contact (10 digits)', '9674847385')
        
        entryFrame.pack(padx=10, anchor='w', pady=20)
        
        # Add New Member Button
        self.add_member_button = ctk.CTkButton(infoFrame, text='Add Member', font=BUTTON_FONT,
                                               fg_color="#fff", corner_radius=7, text_color='#000000',
                                               hover_color="#CAF4FF",
                                               command=self.add_member)
        self.add_member_button.pack(fill='x', padx=20, expand=True, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # --- Right Panel (Table Frame) ---
        tableFrame = ctk.CTkFrame(self, fg_color='transparent')
        
        column_headings = ("id", "full_name", "date_of_birth", "phone_number", "gender", "address",
                           "member_status", "join_date", "membership_type", "membership_start_date",
                           "membership_end_date", "emergency_name", "emergency_number")
        
        self.table = ttk.Treeview(tableFrame, columns=column_headings, show='headings')
        
        for col in column_headings:
            self.table.heading(col, text=col.replace("_", " ").title())
            # Set column widths
            if col == 'id':
                self.table.column(col, width=30, anchor='center')
            elif col == 'full_name':
                self.table.column(col, width=150)
            elif col == 'address':
                self.table.column(col, width=200)
            else:
                self.table.column(col, width=100, anchor='center')
        
        self.table.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Populate table
        self.refresh_table()
        
        # Scrollbars
        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.pack(side='right', fill='y')
        
        table_scrollbar_x = ttk.Scrollbar(tableFrame, orient='horizontal', command=self.table.xview)
        self.table.configure(xscrollcommand=table_scrollbar_x.set)
        table_scrollbar_x.pack(side='bottom', fill='x')
        
        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
    
    def refresh_table(self):
        """
        Clears and repopulates the Treeview with the latest data from the database.
        """
        print("[INFO] Refreshing member table...")
        # Clear existing items
        for item in self.table.get_children():
            self.table.delete(item)
            
        # Get new data
        try:
            # Use the new secure function
            self.data = self.db.get_all_from_table('Members')
            # Insert new data
            for i, row in enumerate(self.data):
                self.table.insert(parent='', index=i, values=row)
            print(f"[INFO] Table refreshed with {len(self.data)} members.")
        except Exception as e:
            print(f"[ERROR] Failed to refresh table: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load member data for table:\n{e}", icon="cancel")
    
    def start_camera_feed(self):
        """
        Initializes the camera and starts the update_camera loop.
        """
        if self.is_camera_running:
            return  # Camera is already running

        print("[INFO] Starting camera feed...")
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # CAP_DSHOW for Windows
            if not self.cap or not self.cap.isOpened():
                raise Exception("Cannot open webcam.")
            
            self.is_camera_running = True
            self.take_photo_button.configure(state="normal", text="Take Photo", command=self.capture_photo)
            self.captured_image = None
            self.update_camera()
        except Exception as e:
            print(f"[ERROR] Failed to start camera: {e}")
            self.video_label.configure(text=f"Camera Error:\n{e}", image=None)
            MESSAGE_BOX(title="Error", message=f"Could not start camera.\nIs it connected?\n\nError: {e}", icon="cancel")

    def update_camera(self):
        """
        Reads a frame from the camera, displays it, and schedules the next update.
        """
        if not self.is_camera_running or not self.cap:
            return  # Stop the loop

        try:
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize for display
                frame_resized = cv2.resize(frame_rgb, (320, 240))
                
                img = Image.fromarray(frame_resized)
                imgtk = ImageTk.PhotoImage(image=img)
                self.video_label.configure(image=imgtk, text="")
                self.video_label.imgtk = imgtk  # Keep a reference
            else:
                print("[WARN] Failed to read frame from camera.")
            
            # Schedule next update
            self.after(20, self.update_camera)
        except Exception as e:
            print(f"[ERROR] Camera feed stopped due to error: {e}")
            self.stop_camera()
            self.video_label.configure(text="Camera feed stopped.", image=None)

    def stop_camera(self):
        """
        Stops the camera update loop and releases the camera device.
        """
        print("[INFO] Stopping camera feed...")
        self.is_camera_running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        
    def capture_photo(self):
        """
        Captures the current camera frame to memory, stops the feed,
        and displays the captured image.
        """
        if not self.is_camera_running or not self.cap:
            print("[ERROR] Cannot capture photo, camera is not running.")
            return

        print("[INFO] Capturing photo...")
        ret, frame = self.cap.read()
        
        if ret:
            # Store the full-resolution frame
            self.captured_image = frame
            print("[INFO] Photo captured to memory.")
            
            # Stop the camera feed
            self.stop_camera()
            
            # Display the captured photo
            frame_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (320, 240))
            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.configure(image=imgtk, text="")
            self.video_label.imgtk = imgtk
            
            # Update button to allow retaking
            self.take_photo_button.configure(text="Retake Photo", command=self.start_camera_feed)
        else:
            print("[ERROR] Failed to capture photo from stream.")
            MESSAGE_BOX(title="Error", message="Could not capture photo. Please try again.", icon="cancel")
    
    def add_member(self):
        """
        Validates all entry fields, adds the member to the database,
        and saves the captured photo using the new member's ID.
        """
        print("[INFO] 'Add Member' button clicked. Validating inputs...")
        # --- 1. Get and Validate Data ---
        fullName = self.full_name_entry.get().strip().title()
        dob = self.dob_entry.get().strip()
        phone = self.phone_entry.get().strip()
        gender = self.gender_ComboBox.get()
        address = self.address_entry.get().strip()
        join_date = self.join_date_entry.get().strip()
        membership_type = self.membership_ComboBox.get()
        membership_start_date = self.membeship_start_date_entry.get().strip()
        membership_end_date = self.membeship_end_date_entry.get().strip()
        emergencyName = self.emergency_name_entry.get().strip().title()
        emergencycontact = self.emergency_contact_entry.get().strip()
        
        # Check for empty fields
        if not all([fullName, dob, phone, gender, address, join_date, membership_type,
                    membership_start_date, membership_end_date, emergencyName, emergencycontact]):
            MESSAGE_BOX(title="Error", message="Please fill all fields", icon="cancel")
            return
        
        # Check phone number length
        if len(phone) != 10 or not phone.isdigit():
            MESSAGE_BOX(title="Error", message="Phone Number must be 10 digits.", icon="cancel")
            return
        
        # Check emergency contact length
        if len(emergencycontact) != 10 or not emergencycontact.isdigit():
            MESSAGE_BOX(title="Error", message="Emergency Contact must be 10 digits.", icon="cancel")
            return
            
        # --- 2. Check for Photo ---
        if self.captured_image is None:
            MESSAGE_BOX(title="Error", message="Please take a photo before adding a member.", icon="cancel")
            return
            
        # --- 3. Insert into Database ---
        print(f"[INFO] Attempting to insert {fullName} into database...")
        new_id = self.db.insert_member(
            fullName, dob, phone, gender, address, "ROOKIE", join_date,
            membership_type, membership_start_date, membership_end_date,
            emergencyName, emergencycontact
        )
        
        # --- 4. Process Result ---
        if new_id:
            print(f"[SUCCESS] Member {fullName} added with ID: {new_id}.")
            
            # --- 5. Save Photo using New ID ---
            save_path = os.path.join(PHOTO_DIR, f"{new_id}.jpg")
            try:
                # Convert the stored frame to RGB and save
                frame_rgb = cv2.cvtColor(self.captured_image, cv2.COLOR_BGR2RGB)
                pil_img = Image.fromarray(frame_rgb)
                pil_img.save(save_path, quality=90)
                print(f"[SUCCESS] Saved photo to {save_path}")
                MESSAGE_BOX(title="Success",
                              message=f"{fullName} was successfully added.\nPhoto saved as {new_id}.jpg",
                              icon="check")
            except Exception as e:
                print(f"[ERROR] Failed to save photo for member ID {new_id}: {e}")
                MESSAGE_BOX(title="Warning",
                              message=f"Member {fullName} was added, but failed to save their photo.\n\nError: {e}",
                              icon="warning")
            
            # --- 6. Reset Form ---
            self.reset_form()
            self.refresh_table()
            
        else:
            # new_id was None, insertion failed
            print("[ERROR] Failed to insert member (database error).")
            MESSAGE_BOX(title="Error",
                          message="Failed to add member.\nThe phone number may already be in use.",
                          icon="cancel")
    
    def reset_form(self):
        """
        Clears all entry fields, resets combo boxes, and restarts the camera.
        """
        print("[INFO] Resetting form...")
        # Reset text fields
        self.full_name_entry.delete(0, 'end')
        self.dob_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.address_entry.delete(0, 'end')
        self.join_date_entry.delete(0, 'end')
        self.membeship_start_date_entry.delete(0, 'end')
        self.membeship_end_date_entry.delete(0, 'end')
        self.emergency_name_entry.delete(0, 'end')
        self.emergency_contact_entry.delete(0, 'end')
        
        # Reset combo boxes
        self.gender_ComboBox.set('Male')
        self.membership_ComboBox.set('Monthly')
        
        # Restart camera feed
        self.start_camera_feed()

    def on_close(self):
        """
ObS
        Safely stops the camera and closes the window.
        This is bound to the window's 'X' button.
        """
        print("[INFO] 'New Member' window closing...")
        self.stop_camera()
        self.destroy()
