from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import Manage_Data
import face_recognition
import cv2
import os
import numpy as np
import datetime
import CTkMessagebox
import sys # Added for safe exit on critical error

# --- Constants ---
BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
MESSAGE_BOX = CTkMessagebox.CTkMessagebox
PHOTO_DIR = "Members Photo"

class MarkAttendance(ctk.CTkToplevel):
    """
    Toplevel window for marking member attendance, either manually
    or via facial recognition.
    """
    
    def __init__(self, parent):
        """
        Initializes the MarkAttendance window, database connection,
        and camera state.
        """
        super().__init__(parent)
        print("[INFO] Initializing 'Mark Attendance' window...")
        self.title("Mark Attendance")
        self.geometry("1400x750")
        ctk.set_appearance_mode('dark')

        try:
            self.db = Manage_Data.DatabaseManager("GYM.db")
            # Load all members into a dictionary for quick name lookup
            # This is the "member map"
            all_members = self.db.get_all_from_table('Members')
            # Creates a map like {1: 'Tony Stark', 2: 'Steve Rogers'}
            self.member_map = {member[0]: member[1] for member in all_members}
            print(f"[INFO] Created member map with {len(self.member_map)} members.")
            
        except Exception as e:
            print(f"[CRITICAL] MarkAttendance: Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error", message=f"Could not load database: {e}", icon="cancel")
            self.destroy()
            return

        self.is_recognizing = False  # Flag to control the camera loop
        self.recognition_data = {"encodings": [], "ids": []} # Holds known faces
        self.recognized_ids = set()  # Prevents duplicate entries in one session
        self.cap = None # Will hold the cv2.VideoCapture object
        self.frame_count = 0  # For frame skipping (performance)

        self.layout()
        self.update_table() # Populate the table on startup

        # Set a custom close action
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    # ------------------ UI Components ------------------

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
        Creates and places all widgets for the MarkAttendance window.
        """
        print("[INFO] Building 'Mark Attendance' layout...")
        # --- Left Panel (Info and Buttons) ---
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')

        ctk.CTkLabel(infoFrame, text='Mark Attendance', font=("Poppins", 30, 'bold')).pack()

        self.camera_label = ctk.CTkLabel(infoFrame, text='Camera Feed', font=BUTTON_FONT, width=300, height=300, fg_color="gray20", corner_radius=10)
        self.camera_label.pack(padx=20, pady=20, anchor='n')

        # --- Manual Entry Fields ---
        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth (DD-MM-YYYY)', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No. (10 digits)', '9674528439')
        entryFrame.pack(padx=5, anchor='w', pady=20)

        # --- Recognition Buttons ---
        button_frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.start_recognition_button = ctk.CTkButton(
            button_frame, text='Start\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", 
            command=self.start_recognition
        )
        self.start_recognition_button.pack(side='left', padx=5)

        self.stop_recognition_button = ctk.CTkButton(
            button_frame, text='Stop\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", 
            command=self.stop_recognition, 
            state="disabled"
        )
        self.stop_recognition_button.pack(side='left', padx=5)
        button_frame.pack(padx=20, pady=10)

        # --- Manual Mark Button ---
        ctk.CTkButton(
            infoFrame, text='Mark Attendance', font=BUTTON_FONT, width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", 
            command=self.entry_attendance # Calls with default id=0
        ).pack(fill='x', padx=20, pady=10)

        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)

        # --- Right Panel (Attendance Table) ---
        tableFrame = ctk.CTkFrame(self, fg_color='transparent')
        
        columns = ("id", "member_id", 'full_name', "date", "check_in_time")
        self.table = ttk.Treeview(tableFrame, columns=columns, show='headings')
        
        for col in columns:
            text = col.replace("_", " ").title()
            self.table.heading(col, text=text)
            if col == 'id' or col == 'member_id':
                self.table.column(col, width=40, anchor='center')
            elif col == 'full_name':
                self.table.column(col, width=150)
            else:
                self.table.column(col, width=100, anchor='center')
                
        self.table.pack(fill='both', expand=True, padx=10, pady=10)

        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.pack(side='right', fill='y')

        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)

    # ------------------ Attendance Logic ------------------

    def update_table(self):
        """
        Clears and repopulates the attendance table.
        Uses the 'self.member_map' to show the correct name for each 'member_id'.
        """
        print("[INFO] Refreshing attendance table...")
        # Clear existing items
        for item in self.table.get_children():
            self.table.delete(item)
            
        try:
            # 1. Get all attendance records (they don't have names)
            all_attendance = self.db.get_all_from_table('Attendance')
            
            # 2. Populate table
            for row in all_attendance:
                # row = (id, member_id, date, check_in_time)
                member_id = row[1]
                # Look up the name from the map we created in __init__
                member_name = self.member_map.get(member_id, f"ID {member_id} Not Found")
                
                # Build the row to match table columns
                display_row = (row[0], member_id, member_name, row[2], row[3])
                self.table.insert(parent='', index='end', values=display_row)
                
            print(f"[INFO] Table refreshed with {len(all_attendance)} attendance records.")
        
        except Exception as e:
            print(f"[ERROR] Failed to refresh attendance table: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to load attendance data:\n{e}", icon="cancel")

    def entry_attendance(self, member_id=0):
        """
        Adds an attendance record to the database.
        
        Args:
            member_id (int, optional): The ID of the member.
                If 0 (default), it's a manual entry from the form fields.
                If > 0, it's an auto-entry from face recognition.
        """
        today = datetime.datetime.now()
        date_str = today.strftime('%d-%m-%Y')
        time_str = today.strftime('%I:%M:%S %p')

        try:
            if member_id == 0:
                # --- Manual Entry ---
                print("[INFO] Attempting manual attendance entry...")
                name = self.full_name_entry.get().strip().title()
                dob = self.dob_entry.get().strip()
                phone = self.phone_entry.get().strip()
                
                if not name or not dob or not phone:
                    MESSAGE_BOX(title="Error", message="Please fill all fields", icon="cancel")
                    return
                if len(phone) != 10 or not phone.isdigit():
                    MESSAGE_BOX(title="Error", message="Phone Number must be 10 digits", icon="cancel")
                    return

                # Use the new secure function
                data = self.db.get_member_by_details(name, dob, phone)
                
                if data:
                    member_id_found = data[0] # Get the ID
                    member_name = data[1] # Get the Name
                    
                    # Use new relational function (no name)
                    self.db.insert_attendance(member_id_found, date_str, time_str)
                    
                    MESSAGE_BOX(title="Success", message=f"Attendance marked for {member_name} at {time_str}", icon="check")
                    self.update_table() # Refresh table with new data
                else:
                    MESSAGE_BOX(title="Error", message="Member not found", icon="cancel")
            
            else:
                # --- Auto Entry from Recognition ---
                print(f"[INFO] Attempting auto attendance for member ID: {member_id}")
                
                # We already have the member_id, just need to log it
                # We can get the name from our map for the print log
                member_name = self.member_map.get(int(member_id), f"ID {member_id}")

                # Use new relational function (no name)
                self.db.insert_attendance(int(member_id), date_str, time_str)
                
                print(f"[SUCCESS] Attendance marked for ID {member_id} ({member_name}) at {time_str}")
                
                # Show a non-blocking success message
                MESSAGE_BOX(title="Success", message=f"Welcome, {member_name}!", icon="check", sound=True)
                
                self.update_table()

        except Exception as e:
            print(f"[ERROR] Failed to insert attendance for ID {member_id}: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to save attendance:\n{e}", icon="cancel")

    # ------------------ Recognition ------------------

    def load_known_faces(self):
        """
        Loads all member photos from the 'Members Photo' directory,
        encodes them, and stores them in self.recognition_data.
        """
        folder = PHOTO_DIR
        encodings = []
        ids = []
        self.recognized_ids.clear() # Clear previously recognized IDs for this session
        
        if not os.path.exists(folder):
            print(f"[ERROR] '{folder}' directory not found. Cannot load faces.")
            MESSAGE_BOX(title="Error", message=f"Directory not found: {folder}", icon="cancel")
            return

        print("[INFO] Loading known faces...")
        for file in os.listdir(folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(folder, file)
                try:
                    image = cv2.imread(path)
                    if image is None:
                        print(f"[WARN] Could not read {path}, skipping.")
                        continue
                        
                    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    
                    # Use face_locations to be more robust
                    boxes = face_recognition.face_locations(rgb, model='hog') # 'cnn' is more accurate but slower
                    
                    if len(boxes) > 0:
                        # Use the first face found
                        faces = face_recognition.face_encodings(rgb, known_face_locations=boxes)
                        if faces:
                            encodings.append(faces[0])
                            ids.append(os.path.splitext(file)[0])  # Get ID from filename
                    else:
                        print(f"[INFO] No face found in {file}, skipped.")
                        
                except Exception as e:
                    print(f"[ERROR] Failed to process {path}: {e}")

        self.recognition_data["encodings"] = encodings
        self.recognition_data["ids"] = ids
        print(f"[INFO] Loaded {len(encodings)} known faces.")

    def start_recognition(self):
        """
        Called by the 'Start Recognition' button.
        Loads faces and starts the camera feed loop.
        """
        print("[INFO] 'Start Recognition' clicked.")
        # 1. Load faces
        self.load_known_faces()
        
        # 2. Check if we have faces to recognize
        if not self.recognition_data["encodings"]:
            MESSAGE_BOX(title="Error", message="No known faces found. Please add member photos.", icon="cancel")
            return
            
        # 3. Start camera and loop
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW) # CAP_DSHOW is more stable on Windows
            if not self.cap.isOpened():
                print("[ERROR] Cannot open webcam.")
                MESSAGE_BOX(title="Error", message="Cannot open webcam.", icon="cancel")
                return
        except Exception as e:
            print(f"[ERROR] Failed to open webcam: {e}")
            MESSAGE_BOX(title="Error", message=f"Failed to open webcam:\n{e}", icon="cancel")
            return
            
        print("[INFO] Camera started.")
        self.camera_label.configure(text="")
        self.start_recognition_button.configure(state="disabled")
        self.stop_recognition_button.configure(state="normal")
        
        self.frame_count = 0
        self.is_recognizing = True
        self.process_frame() # Start the loop


    def stop_recognition(self):
        """
        Called by the 'Stop Recognition' button.
        Sets the flag to stop the camera loop.
        """
        print("[INFO] 'Stop Recognition' clicked.")
        self.is_recognizing = False
        # The loop in process_frame will see this and stop itself.
        

    def process_frame(self):
        """
        The main camera loop. Reads a frame, processes it, and schedules
        the next frame.
        """
        # 1. Check if we should stop
        if not self.is_recognizing:
            print("[INFO] Stopping recognition loop.")
            if self.cap:
                self.cap.release()
                self.cap = None
            self.camera_label.configure(text="Camera Feed", image=None)
            self.start_recognition_button.configure(state="normal")
            self.stop_recognition_button.configure(state="disabled")
            return # Exit the loop

        # 2. Read frame
        ret, frame = self.cap.read()
        if not ret:
            print("[WARN] Cannot read frame, stopping.")
            self.is_recognizing = False # Trigger stop
        else:
            try:
                self.frame_count += 1
                
                # 3. --- Perform expensive recognition only every 5 frames ---
                if self.frame_count % 5 == 0:
                    # Resize for *processing* (faster)
                    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                    rgb_small = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
                    
                    # Find all faces in the *current* frame
                    face_encodings = face_recognition.face_encodings(rgb_small)

                    for face_encoding in face_encodings:
                        # Compare against known faces
                        matches = face_recognition.compare_faces(self.recognition_data["encodings"], face_encoding)
                        
                        if True in matches:
                            idx = matches.index(True)
                            member_id = self.recognition_data["ids"][idx]
                            
                            # Check if we've *already* marked this person in this session
                            if member_id not in self.recognized_ids:
                                self.recognized_ids.add(member_id)
                                print(f"[INFO] Recognized member {member_id}")
                                # Run DB insert *without* blocking the GUI loop
                                self.after(0, self.entry_attendance, member_id)

                # 4. --- Display frame (every time for smooth video) ---
                display_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                # Resize for *display* (to fit the 300x300 label)
                display_frame = cv2.resize(display_frame, (300, 300))
                
                img = Image.fromarray(display_frame)
                img_tk = ImageTk.PhotoImage(img)
                self.camera_label.configure(image=img_tk)
                self.camera_label.image = img_tk
            
            except Exception as e:
                print(f"[ERROR] Error in frame processing: {e}")

        # 5. Schedule the next frame
        self.after(20, self.process_frame) # ~50fps target (GUI only, processing is 1/5 of this)
        
    def on_close(self):
        """
        Handles the window 'X' button click.
        Safely stops the camera loop before destroying the window.
        """
        print("[INFO] 'Mark Attendance' window closing...")
        self.is_recognizing = False # Signal the loop to stop
        
        # Wait a moment for the loop to finish
        self.after(50, self.safe_close)
        
    def safe_close(self):
        """
        Performs the actual cleanup and destruction of the window.
        """
        print("[INFO] Releasing camera and closing window.")
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # self.db.close_connection() # <-- FIX: Do not close the connection here.
        self.destroy() # Close the Toplevel window

