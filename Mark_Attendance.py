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
        self.last_id = 1 if not self.memberData else int(self.memberData[-1][0]) + 1
        
        self.is_recognizing = False
        self.recognition_data = {
            "known_faces_encodings": [],
            "known_faces_names": []
        }

        self.layout()
        
    def labelEntry_Component(self, parent, text, placeholder):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        ctk.CTkLabel(frame, text=text, font=LABEL_FONT).pack(anchor='w')
        entry = ctk.CTkEntry(frame, font=LABEL_FONT, width=500, placeholder_text=placeholder)
        entry.pack(fill='x', expand=True)
        frame.pack(fill='x', pady=5)
        return entry
     
    def layout(self):
        # Info Frame
        infoFrame = ctk.CTkScrollableFrame(self, fg_color='transparent')
        
        ctk.CTkLabel(infoFrame, text='Mark Attendance', font=("Poppins", 30, 'bold')).pack()
        
        self.camera_label = ctk.CTkLabel(infoFrame, text='Camera Feed', font=BUTTON_FONT, width=300, height=300)
        self.camera_label.pack(padx=20, pady=20, anchor='n')

        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No.', '9674528439')
        entryFrame.pack(padx=5, anchor='w', pady=20)
        
        # Start and Stop Recognition buttons
        button_frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        
        self.start_recognition_button = ctk.CTkButton(button_frame, text='Start\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000', hover_color="#CAF4FF", command=self.start_recognition)
        self.start_recognition_button.pack(side='left', padx=5)
        
        self.stop_recognition_button = ctk.CTkButton(button_frame, text='Stop\nRecognition', font=BUTTON_FONT,
            fg_color="#fff", corner_radius=7, text_color='#000000', hover_color="#CAF4FF", command=self.stop_recognition)
        self.stop_recognition_button.pack(side='left', padx=5)
        
        button_frame.pack(padx=20, pady=10)
        
        # Take Photo button
        ctk.CTkButton(infoFrame, text='Mark Attendance', font=BUTTON_FONT, width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000', hover_color="#CAF4FF", command=self.entry_attendance).pack(fill='x', padx=20, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # Table Frame
        tableFrame = ctk.CTkFrame(self, fg_color='transparent')
        
        self.table = ttk.Treeview(
            tableFrame,
            columns=("id", "member_id", 'full_name', "date","check_in_time"),
            show='headings'
        )
        self.table.heading('id', text='ID')
        self.table.heading('member_id', text='Member Id')
        self.table.heading('full_name', text='Full Name')
        self.table.heading('date', text='Date')
        self.table.heading('check_in_time', text='Check In Time')
        
        self.table.pack(fill='both', expand=True)
        
        for i in range(len(self.attendanceData)):
            self.table.insert(parent='', index=i, values=self.attendanceData[i])
        
        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.place(relx=1, rely=0, relheight=1, anchor='ne')
        
        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
    
    def update_table(self):
        self.attendanceData = self.db.get_all_members('Attendance')
        for item in self.table.get_children():
                self.table.delete(item)
        for i in range(len(self.attendanceData)):
            self.table.insert(parent='', index=i, values=self.attendanceData[i])
            
    def entry_attendance(self,id=0):
        today_dateTime = datetime.datetime.now()
        formatted_time = today_dateTime.strftime('%I:%M:%S %p')
        formatted_date = today_dateTime.strftime('%d-%m-%Y')
        
        if id == 0:
            name = self.full_name_entry.get().strip().title()
            dob = self.dob_entry.get().strip()
            phone = self.phone_entry.get().strip()
                    
            if not name or not dob or not phone:
                message(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
                return
            
            if len(phone) > 10 or len(phone) < 10:
                message(title="Error", message="Phone Number not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
                return

            data = self.db.get_members_id(name,dob,phone)
            
            if data:
                try:
                    self.db.insert_attendance(data[0], data[1], formatted_date, formatted_time)
                    print(f"Attendance marked for {data[1]} at {formatted_time}")
                    message(title="Success",message=f"Attendance marked of member \nName: {data[1]}\nTime: {formatted_time}",icon="check", option_1="OK",justify='center')
                except Exception as e:
                    print(f"Failed to mark attendance: {e}")
                    message(title="Error", message=f"Failed to mark attendance: {e}", icon="cancel",justify='center',sound=True)
            else:
                print(f"No data found for member {name}")
                message(title="Error", message=f"No data found for \nMember: {data[1]}\nID: {data[0]}", icon="cancel",justify='center',fade_in_duration=1,sound=True)
        else:
            data = self.db.get_Data_by_id("Members", int(id))[0]
            
            if data:
                try:
                    self.db.insert_attendance(data[0], data[1], formatted_date, formatted_time)
                    print(f"Attendance marked for {data[1]} at {formatted_time}")
                    message(title="Success",message=f"Attendance marked of member \nName: {data[1]}\nTime: {formatted_time}",icon="check", option_1="OK",justify='center')
                except Exception as e:
                    print(f"Failed to mark attendance: {e}")
                    message(title="Error", message=f"Failed to mark attendance: {e}", icon="cancel",justify='center',sound=True)
            else:
                print(f"No data found for member {id}")
                message(title="Error", message=f"No data found for \nMember: {data[1]}\nID: {data[0]}", icon="cancel",justify='center',fade_in_duration=1,sound=True)
                
    def start_recognition(self):
        if not self.is_recognizing:
            self.is_recognizing = True
            self.load_known_faces()
            self.recognize_faces()
            self.start_recognition_button.configure(text="Recognizing...", state="disabled")
            self.stop_recognition_button.configure(state="normal")
    
    def stop_recognition(self):
        self.is_recognizing = False
        self.start_recognition_button.configure(text="Start\nRecognition", state="normal")
        message(title="Info", message="Recognition Stopped",justify='center',fade_in_duration=1,sound=True)
    
    def load_known_faces(self):
        known_faces_encodings = []
        known_faces_names = []

        members_photo_folder = 'Members Photo'
        for filename in os.listdir(members_photo_folder):
            if filename.endswith('.jpg') or filename.endswith('.png'):
                member_name = os.path.splitext(filename)[0]
                member_image = cv2.imread(os.path.join(members_photo_folder, filename))
                member_face_encoding = self.get_face_encoding(member_image)
                if member_face_encoding is not None:
                    known_faces_encodings.append(member_face_encoding)
                    known_faces_names.append(member_name)
        
        self.recognition_data["known_faces_encodings"] = known_faces_encodings
        self.recognition_data["known_faces_names"] = known_faces_names

    def recognize_faces(self):
        cap = cv2.VideoCapture(0)
        recognized_ids = set()

        def process_frame():
            if not self.is_recognizing:
                cap.release()
                cv2.destroyAllWindows()
                return
            
            ret, frame = cap.read()
            if not ret:
                cap.release()
                cv2.destroyAllWindows()
                return
            
            rgb_frame = np.ascontiguousarray(frame[:, :, ::-1])
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
            
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.recognition_data["known_faces_encodings"], face_encoding)
                name = "Unknown"

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.recognition_data["known_faces_names"][first_match_index]
                    
                for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
                    cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
                    cv2.putText(frame, name, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0, (255, 255, 255), 1)
                    if name not in recognized_ids:
                        if name == "Unknown":
                            pass
                        else:
                            self.entry_attendance(id = name)
                            recognized_ids.add(name)
                            self.update_table()
                    
            resized_frame = cv2.resize(frame, (300,300))
            rgb_frame = cv2.cvtColor(resized_frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb_frame)
            img_tk = ImageTk.PhotoImage(img)
            self.camera_label.configure(image=img_tk)
            self.camera_label.image = img_tk  # Keep a reference to prevent garbage collection

            self.update_idletasks()  # Ensure the GUI updates
            
            self.after(10, process_frame)  # Call process_frame again after 100ms
        
        process_frame()

    def get_face_encoding(self, image):
        small_image = cv2.resize(image, (0, 0), fx=0.25, fy=0.25)
        rgb_small_image = np.ascontiguousarray(small_image[:, :, ::-1])
        face_locations = face_recognition.face_locations(rgb_small_image)
        if len(face_locations) == 0:
            return None
        face_encodings = face_recognition.face_encodings(rgb_small_image, face_locations)[0]
        return face_encodings
