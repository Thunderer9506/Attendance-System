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

BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
message = CTkMessagebox.CTkMessagebox

class MarkAttendance(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Attendance System")
        self.geometry("1400x750")
        ctk.set_appearance_mode('dark')

        self.db = Manage_Data.DatabaseManager("GYM.db")
        self.attendanceData = self.db.get_all_members('Attendance')
        self.memberData = self.db.get_all_members('Members')

        self.is_recognizing = False
        self.recognition_data = {"encodings": [], "ids": []}
        self.recognized_ids = set()  # For preventing duplicate attendance in one session
        self.cap = None

        self.layout()

    # ------------------ UI Components ------------------

    def labelEntry_Component(self, parent, text, placeholder):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        ctk.CTkLabel(frame, text=text, font=LABEL_FONT).pack(anchor='w')
        entry = ctk.CTkEntry(frame, font=LABEL_FONT, width=500, placeholder_text=placeholder)
        entry.pack(fill='x', expand=True)
        frame.pack(fill='x', pady=5)
        return entry

    def layout(self):
        # Left Panel - Info and Buttons
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')

        ctk.CTkLabel(infoFrame, text='Mark Attendance', font=("Poppins", 30, 'bold')).pack()

        self.camera_label = ctk.CTkLabel(infoFrame, text='Camera Feed', font=BUTTON_FONT, width=300, height=300)
        self.camera_label.pack(padx=20, pady=20, anchor='n')

        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No.', '9674528439')
        entryFrame.pack(padx=5, anchor='w', pady=20)

        # Start / Stop Recognition Buttons
        button_frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.start_recognition_button = ctk.CTkButton(
            button_frame, text='Start\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.start_recognition
        )
        self.start_recognition_button.pack(side='left', padx=5)

        self.stop_recognition_button = ctk.CTkButton(
            button_frame, text='Stop\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.stop_recognition, state="disabled"
        )
        self.stop_recognition_button.pack(side='left', padx=5)
        button_frame.pack(padx=20, pady=10)

        # Manual Mark Button
        ctk.CTkButton(
            infoFrame, text='Mark Attendance', font=BUTTON_FONT, width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.entry_attendance
        ).pack(fill='x', padx=20, pady=10)

        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)

        # Right Panel - Attendance Table
        tableFrame = ctk.CTkFrame(self, fg_color='transparent')
        self.table = ttk.Treeview(
            tableFrame, columns=("id", "member_id", 'full_name', "date", "check_in_time"),
            show='headings'
        )
        for col in ("id", "member_id", "full_name", "date", "check_in_time"):
            self.table.heading(col, text=col.replace("_", " ").title())
        self.table.pack(fill='both', expand=True)

        for i, row in enumerate(self.attendanceData):
            self.table.insert('', i, values=row)

        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.place(relx=1, rely=0, relheight=1, anchor='ne')

        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)

    # ------------------ Attendance Logic ------------------

    def update_table(self):
        self.attendanceData = self.db.get_all_members('Attendance')
        self.table.delete(*self.table.get_children())
        for i, row in enumerate(self.attendanceData):
            self.table.insert('', i, values=row)

    def entry_attendance(self, id=0):
        today = datetime.datetime.now()
        date_str = today.strftime('%d-%m-%Y')
        time_str = today.strftime('%I:%M:%S %p')

        if id == 0:
            # Manual Entry
            name = self.full_name_entry.get().strip().title()
            dob = self.dob_entry.get().strip()
            phone = self.phone_entry.get().strip()
            if not name or not dob or not phone:
                message(title="Error", message="Please fill all fields", icon="cancel")
                return
            if len(phone) != 10:
                message(title="Error", message="Phone Number must be 10 digits", icon="cancel")
                return

            data = self.db.get_members_id(name, dob, phone)
            if data:
                self.db.insert_attendance(data[0], data[1], date_str, time_str)
                message(title="Success", message=f"Attendance marked for {data[1]} at {time_str}", icon="check")
                self.update_table()
            else:
                message(title="Error", message="Member not found", icon="cancel")
        else:
            # Auto Entry from Recognition
            try:
                data = self.db.get_Data_by_id("Members", int(id))[0]
                self.db.insert_attendance(data[0], data[1], date_str, time_str)
                print(f"Attendance marked for ID {id} ({data[1]}) at {time_str}")
                self.update_table()
            except Exception as e:
                print(f"[ERROR] Auto attendance failed for ID {id}: {e}")

    # ------------------ Recognition ------------------

    def load_known_faces(self):
        folder = 'Members Photo'
        encodings = []
        ids = []

        for file in os.listdir(folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                path = os.path.join(folder, file)
                image = cv2.imread(path)
                if image is None:
                    print(f"[WARN] Could not read {path}")
                    continue
                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                faces = face_recognition.face_encodings(rgb)
                if len(faces) > 0:
                    encodings.append(faces[0])
                    ids.append(os.path.splitext(file)[0])  # numeric ID from filename
                else:
                    print(f"[INFO] No face found in {file}, skipped.")

        self.recognition_data["encodings"] = encodings
        self.recognition_data["ids"] = ids
        print(f"[INFO] Loaded {len(encodings)} known faces.")

    def start_recognition(self):
        if self.is_recognizing:
            return
        self.load_known_faces()
        if not self.recognition_data["encodings"]:
            message(title="Error", message="No known faces loaded", icon="cancel")
            return

        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            message(title="Error", message="Could not access the camera.", icon="cancel")
            return

        self.is_recognizing = True
        self.recognized_ids.clear()
        self.start_recognition_button.configure(text="Recognizing...", state="disabled")
        self.stop_recognition_button.configure(state="normal")
        self.process_frame()

    def stop_recognition(self):
        self.is_recognizing = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.start_recognition_button.configure(text="Start\nRecognition", state="normal")
        self.stop_recognition_button.configure(state="disabled")
        message(title="Info", message="Recognition stopped", icon="info")

    def process_frame(self):
        if not self.is_recognizing:
            return

        ret, frame = self.cap.read()
        if not ret:
            self.stop_recognition()
            return

        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        face_locations = face_recognition.face_locations(rgb_small)
        face_encodings = face_recognition.face_encodings(rgb_small, face_locations)

        for face_encoding in face_encodings:
            matches = face_recognition.compare_faces(self.recognition_data["encodings"], face_encoding)
            if True in matches:
                idx = matches.index(True)
                member_id = self.recognition_data["ids"][idx]
                if member_id not in self.recognized_ids:
                    self.recognized_ids.add(member_id)
                    self.entry_attendance(id=member_id)

        # Display frame in UI
        display_frame = cv2.cvtColor(cv2.resize(frame, (300, 300)), cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display_frame)
        img_tk = ImageTk.PhotoImage(img)
        self.camera_label.configure(image=img_tk)
        self.camera_label.image = img_tk

        self.after(10, self.process_frame)
