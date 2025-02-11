from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import cv2
import os
import Manage_Data
import CTkMessagebox

BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)
message = CTkMessagebox.CTkMessagebox

class NewMember(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Attendance System")
        self.geometry("1400x800")
        ctk.set_appearance_mode('dark')
        
        self.db = Manage_Data.DatabaseManager("GYM.db")
        self.data = self.db.get_all_members('Members')
        self.last_id = 1
        # Initialize camera capture
        self.cap = cv2.VideoCapture(0)
        self.video_frame = None
        
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
        
        ctk.CTkLabel(infoFrame, text='Add New Member', font=("Poppins", 30, "bold")).pack()
        
        # Start camera feed
        self.start_camera(infoFrame).pack(anchor='n')
        
        # Take Photo
        take_photo_button = ctk.CTkButton(infoFrame, text='Take Photo', font=BUTTON_FONT,
                      fg_color="#fff", corner_radius=7, text_color='#000000',
                      hover_color="#CAF4FF")
        take_photo_button.pack(fill='x', expand=True, pady=5)
        take_photo_button.configure(command=self.capture_photo)
        
        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No.', '9674528439')
        
        ctk.CTkLabel(entryFrame, text="Gender", font=LABEL_FONT).pack(anchor='w')
        self.gender_ComboBox = ctk.CTkComboBox(entryFrame, values=["Male", "Female"], font=LABEL_FONT)
        self.gender_ComboBox.pack(fill='x', pady=5)
        
        self.address_entry = self.labelEntry_Component(entryFrame, 'Address', '123 Main St, Anytown, USA')
        self.join_date_entry = self.labelEntry_Component(entryFrame, 'Joining Date', '20-05-2023')
        
        ctk.CTkLabel(entryFrame, text="Membership Type", font=LABEL_FONT).pack(anchor='w')
        self.membership_ComboBox = ctk.CTkComboBox(entryFrame, values=["Monthly", "Quarterly", "Half-yearly", "Yearly"], font=LABEL_FONT)
        self.membership_ComboBox.pack(fill='x', pady=5)
        
        self.membeship_start_date_entry = self.labelEntry_Component(entryFrame, 'Membership Start Date', '20-05-2023')
        self.membeship_end_date_entry = self.labelEntry_Component(entryFrame, 'Membership End Date', '20-06-2023')
        self.emergency_name_entry = self.labelEntry_Component(entryFrame, 'Emergency Name', 'John Doe')
        self.emergency_contact_entry = self.labelEntry_Component(entryFrame, 'Emergency Contact', '9674847385')
        
        entryFrame.pack(padx=10, anchor='w', pady=20)
        
        # Add new member button
        add_member_button = ctk.CTkButton(infoFrame, text='Add Member', font=BUTTON_FONT,
                      fg_color="#fff", corner_radius=7, text_color='#000000',
                      hover_color="#CAF4FF")
        add_member_button.pack(fill='x', padx=20, expand=True,pady=10)
        add_member_button.configure(command=self.add_member)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # Table Frame
        tableFrame = ctk.CTkFrame(self,fg_color='transparent')
        
        self.table = ttk.Treeview(
            tableFrame,
            columns=("id","full_name", "date_of_birth", "phone_number", "gender", "address", "member_status", "join_date", "membership_type", "membership_start_date", "membership_end_date", "emergency_name", "emergency_number"),
            show='headings'
        )
        self.table.heading('id', text='ID')
        self.table.heading('full_name', text='Full Name')
        self.table.heading('date_of_birth', text='Date of Birth')
        self.table.heading('phone_number', text='Phone No.')
        self.table.heading('gender', text='Gender')
        self.table.heading('address', text='Address')
        self.table.heading("member_status", text="Member Status")
        self.table.heading('join_date', text='Joining Date')
        self.table.heading('membership_type', text='Membership Type')
        self.table.heading('membership_start_date', text='Membership Start Date')
        self.table.heading('membership_end_date', text='Membership End Date')
        self.table.heading('emergency_name', text='Emergency Name')
        self.table.heading('emergency_number', text='Emergency Number')
        
        self.table.pack(fill='both', expand=True)
        
        for i in range(len(self.data)):
            self.table.insert(parent='', index=i, values=self.data[i])
        
        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.place(relx=1, rely=0, relheight=1, anchor='ne')
        
        table_scrollbar_x = ttk.Scrollbar(tableFrame, orient='horizontal', command=self.table.xview)
        self.table.configure(xscrollcommand=table_scrollbar_x.set)
        table_scrollbar_x.place(relx=0, rely=1, relwidth=1, anchor='sw')
        
        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
    
        
    def start_camera(self, parent):
        # Function to start displaying camera feed in tkinter GUI
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        self.video_label = ctk.CTkLabel(frame,text="")
        self.video_label.pack()
        self.update_camera()
        return frame
    
    def update_camera(self):
        # Function to update video feed
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            imgtk = ImageTk.PhotoImage(image=img)
            self.video_label.configure(image=imgtk)
            self.video_label.imgtk = imgtk  # type: ignore # Keep a reference to avoid garbage collection issues
        self.video_label.after(10, self.update_camera)  # Update every 10 milliseconds (adjust as needed)
    
    def stop_camera(self):
        # Function to release the camera
        if self.cap is not None:
            self.cap.release()
    
    def capture_photo(self):
        # Capture photo from camera and save (example function)
        ret, frame = self.cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(frame_rgb)
            self.data = self.db.get_all_members('Members')
            if self.data == []:
                self.last_id = 1
            else:
                self.last_id = int(self.data[len(self.data)-1][0]) + 1 
            save_path = os.path.join('Members Photo', f"{self.last_id}.jpg")
            pil_img.save(save_path)
            message(title="Success",message=f"{self.last_id}.jpg Image saved successfully",icon="check", option_1="OK",justify='center',fade_in_duration=1)
    
    def add_member(self):
        # Example function to add member with entered details
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
        
        if not fullName or not dob or not phone or not gender or not address or not join_date or not membership_type or not membership_start_date or not membership_end_date or not emergencyName or not emergencycontact:
            message(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        if len(phone) > 10 or len(phone) < 10:
            message(title="Error", message="Phone Number is not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        if len(emergencycontact) > 10 or len(emergencycontact) < 10:
            message(title="Error", message="Emergency Phone Number is not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        
        # Example: Save to database or perform other operations
        self.db.insert_member(fullName, dob, phone, gender, address, "ROOKIE",join_date, membership_type, membership_start_date, membership_end_date, emergencyName, emergencycontact)
        
        # Reset fields after adding member
        self.full_name_entry.delete(0, 'end')
        self.dob_entry.delete(0, 'end')
        self.phone_entry.delete(0, 'end')
        self.gender_ComboBox.set('Male')
        self.address_entry.delete(0, 'end')
        self.join_date_entry.delete(0, 'end')
        self.membership_ComboBox.set('Monthly')
        self.membeship_start_date_entry.delete(0, 'end')
        self.membeship_end_date_entry.delete(0, 'end')
        self.emergency_name_entry.delete(0, 'end')
        self.emergency_contact_entry.delete(0, 'end')
        
        self.data = self.db.get_all_members('Members')
        for item in self.table.get_children():
            self.table.delete(item)
        for i in range(len(self.data)):
            self.table.insert(parent='', index=i, values=self.data[i])
            
        message(title="Success",message=f"{fullName} successfully added in the member",icon="check", option_1="OK",justify='center')
    
    def __del__(self):
        # Destructor to release the camera when closing the application
        self.stop_camera()