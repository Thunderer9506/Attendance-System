from PIL import Image
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from tkinter import ttk
import Manage_Data

BUTTON_FONT = ("Poppins",20)
LABEL_FONT = ("Poppins",16)

class EditData(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Attendance System")
        self.geometry("1400x750")
        ctk.set_appearance_mode('dark')
        
        self.db = Manage_Data.DatabaseManager("GYM.db")
        
        self.person_id = None
        self.current_table = ctk.StringVar(value='Members')  # Track current table to update display
        self.current_field = ctk.StringVar(value="full_name")

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
        
        ctk.CTkLabel(infoFrame, text='Edit Data', font=("Poppins", 30, 'bold')).pack()
        
        # Create and pack person_photo_frame
        self.person_photo(infoFrame).pack(padx=20, pady=10, anchor='n')

        entry_Frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        
        ctk.CTkLabel(entry_Frame, text="Table", font=LABEL_FONT).pack(anchor='w')
        self.table_ComboBox = ctk.CTkComboBox(
            entry_Frame, 
            values=["Members", "Attendance", "Payment"], 
            font=LABEL_FONT,
            variable=self.current_table,
            command= lambda choice:self.update_table(choice,self.db.get_all_members(choice)))
        self.table_ComboBox.pack(fill='x', pady=5)
        
        self.full_name_entry = self.labelEntry_Component(entry_Frame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entry_Frame, 'Date of Birth', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entry_Frame, 'Phone No.', '9674528439')
        
        ctk.CTkLabel(entry_Frame, text="Field", font=LABEL_FONT).pack(anchor='w')
        self.field_ComboBox = ctk.CTkComboBox(
            entry_Frame, 
            values=["full_name", "date_of_birth", "phone_number", "gender", "address", "member_status", "join_date", "membership_type", "membership_start_date", "membership_end_date", "emergency_name", "emergency_number"],
            font=LABEL_FONT,
            variable=self.current_field,
            # command= lambda choice:self.fieldlabel.configure(text = choice)
            )
        self.field_ComboBox.pack(fill='x', pady=5)
        
        self.fieldframe = ctk.CTkFrame(entry_Frame, fg_color='transparent')
        self.fieldlabel = ctk.CTkLabel(self.fieldframe, text="full_name", font=LABEL_FONT,textvariable=self.current_field).pack(anchor='w')
        self.fieldentry = ctk.CTkEntry(self.fieldframe, font=LABEL_FONT, width=500)
        self.fieldentry.pack(fill='x')
        self.fieldframe.pack(fill='x',pady=20)
        
        entry_Frame.pack(fill='x', padx=20, pady=30)
        
        # Search button
        ctk.CTkButton(infoFrame, text='Search Data', font=BUTTON_FONT, width=220,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.search_user).pack(fill='x', padx=20, pady=10)
        
        button_frame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        
        self.edit_data_button = ctk.CTkButton(button_frame, text='Edit Data', font=BUTTON_FONT,width=120,
            fg_color="#fff", corner_radius=7, text_color='#000000',
            hover_color="#CAF4FF", command=self.edit_user)
        self.edit_data_button.pack(padx=20, pady=5,side='left')
        
        self.delete_data_button = ctk.CTkButton(button_frame, text='Delete Data', font=BUTTON_FONT,width=120,
            fg_color="#fff", corner_radius=7, text_color='#000000', 
            hover_color="#CAF4FF", command=self.delete_user)
        self.delete_data_button.pack(padx=20, pady=5,side='right')
    
        button_frame.pack(pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # Table Frame
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
        
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
        self.table.heading('member_status', text='Member Status')
        self.table.heading('join_date', text='Joining Date')
        self.table.heading('membership_type', text='Membership Type')
        self.table.heading('membership_start_date', text='Membership Start Date')
        self.table.heading('membership_end_date', text='Membership End Date')
        self.table.heading('emergency_name', text='Emergency Name')
        self.table.heading('emergency_number', text='Emergency Number')
        
        self.table.pack(fill='both', expand=True)

        data = self.db.get_all_members("Members")
        for i in range(len(data)):
            self.table.insert(parent='', index=i, values=data[i])
        
        table_scrollbar_y = ttk.Scrollbar(tableFrame, orient='vertical', command=self.table.yview)
        self.table.configure(yscrollcommand=table_scrollbar_y.set)
        table_scrollbar_y.place(relx=1, rely=0, relheight=1, anchor='ne')
        
        table_scrollbar_x = ttk.Scrollbar(tableFrame, orient='horizontal', command=self.table.xview)
        self.table.configure(xscrollcommand=table_scrollbar_x.set)
        table_scrollbar_x.place(relx=0, rely=1, relwidth=1, anchor='sw')
        
        tableFrame.place(relx=0.25, rely=0, relwidth=0.75, relheight=1)
    
    def delete_user(self):
        yes_no = CTkMessagebox(title="Error", message="Do you really want to delete the user's data", option_1="YES", option_2="NO", icon="cancel",justify='center',fade_in_duration=1,sound=True)
        if yes_no == "YES":
            msg = CTkMessagebox(title="Error", message="Please fill all fields", icon="question", option_1="Minimal Delete", option_2="Fully Delete",justify='center',sound=True)
            name = self.full_name_entry.get().strip().title()
            dob = self.dob_entry.get().strip()
            phone = self.phone_entry.get().strip()
            
            if len(phone) > 10 or len(phone) < 10:
                CTkMessagebox(title="Error", message="Phone Number not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
                return
        
            if not name or not dob or not phone:
                CTkMessagebox(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
                return
            
            self.person_id = self.db.get_members_id(name, dob, phone)[0]
            if msg.get() == "Fully Delete":
                self.db.fully_delete_member(self.person_id)
            elif msg.get() == "Minimal Delete":
                self.db.minimal_delete_member(self.person_id)
        else:
            return
        
    def edit_user(self):
        if self.person_id != None:
            fieldData = self.fieldentry.get().strip().title()
            fieldComboData = self.current_field.get()
            table = self.table_ComboBox.get()
            self.db.update_member(table,self.person_id,fieldComboData,fieldData)
            CTkMessagebox(title="Success",message="Data edited successfully",icon="check", option_1="OK",justify='center')
        else:
            CTkMessagebox(title="Error", message="Search the user first", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        
    def update_table(self,table,data):
        if table == "Members":
            value = ["full_name", "date_of_birth", "phone_number", "gender", "address", "member_status", "join_date", "membership_type", "membership_start_date", "membership_end_date", "emergency_name", "emergency_number"]
            self.field_ComboBox.configure(values=value)
            self.current_field.set(value[0])
            self.table.config(columns=("id","full_name", "date_of_birth", "phone_number", "gender", "address", "member_status", "join_date", "membership_type", "membership_start_date", "membership_end_date", "emergency_name", "emergency_number"))
                
            self.table.heading('id', text='ID')
            self.table.heading('full_name', text='Full Name')
            self.table.heading('date_of_birth', text='Date of Birth')
            self.table.heading('phone_number', text='Phone No.')
            self.table.heading('gender', text='Gender')
            self.table.heading('address', text='Address')
            self.table.heading('member_status', text='Member Status')
            self.table.heading('join_date', text='Joining Date')
            self.table.heading('membership_type', text='Membership_Type')
            self.table.heading('membership_start_date', text='Membership Start Date')
            self.table.heading('membership_end_date', text='Membership End Date')
            self.table.heading('emergency_name', text='Emergency Name')
            self.table.heading('emergency_number', text='Emergency Number')
            
            for item in self.table.get_children():
                self.table.delete(item)
            
            if type(data) == list: 
                for i in range(len(data)):
                    self.table.insert(parent='', index=i, values=data[i])
            elif type(data) == tuple:
                self.table.insert(parent='', index=0, values=data)
                
        elif table == "Attendance":
            value = ["member_id", 'full_name', "check_in_time"]
            self.field_ComboBox.configure(values=value)
            self.current_field.set(value[0])
            self.table.config(columns=("id","member_id", 'full_name', "check_in_time"))
            self.table.heading('id', text='ID')
            self.table.heading('member_id', text='Member Id')
            self.table.heading('full_name', text='Full Name')
            self.table.heading('check_in_time', text='Check In Time')
            for item in self.table.get_children():
                self.table.delete(item)
            
            if type(data) == list: 
                for i in range(len(data)):
                    self.table.insert(parent='', index=i, values=data[i])
            elif type(data) == tuple:
                self.table.insert(parent='', index=0, values=data)
        elif table == "Payment":
            value=["member_id", "full_name", 'payment_date', "amount","payment_method"]
            self.field_ComboBox.configure(values=value)
            self.current_field.set(value[0])
            self.table.config(columns=("id","member_id", "full_name", 'payment_date', "amount","payment_method"))
            self.table.heading('id', text='ID')
            self.table.heading('member_id', text='Member Id')
            self.table.heading('full_name', text='Full Name')
            self.table.heading('payment_date', text='Payment Date')
            self.table.heading('amount', text='Amount')
            self.table.heading('payment_method', text='Payment Method')
            for item in self.table.get_children():
                self.table.delete(item)
            
            if type(data) == list: 
                for i in range(len(data)):
                    self.table.insert(parent='', index=i, values=data[i])
            elif type(data) == tuple:
                self.table.insert(parent='', index=0, values=data)
    
    def person_photo(self, parent):
        frame = ctk.CTkFrame(parent, fg_color='transparent')
        
        # Define a consistent size
        image_size = (300, 300)
        
        # Open and resize the default image
        default_image = Image.open('images/person.jpg')
        default_image = default_image.resize(image_size, Image.LANCZOS)
        self.image_person = ctk.CTkImage(default_image, size=image_size)
        
        image_label = ctk.CTkLabel(frame, image=self.image_person, text="")
        image_label.pack()
        return frame

    
    def search_user(self):
        name = self.full_name_entry.get().strip().title()
        dob = self.dob_entry.get().strip()
        phone = self.phone_entry.get().strip()
        table = self.table_ComboBox.get()
         
        if not name or not dob or not phone:
            CTkMessagebox(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        
        if len(phone) > 10 or len(phone) < 10:
            CTkMessagebox(title="Error", message="Phone Number not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
       
        self.person_id = self.db.get_members_id(name, dob, phone)
        
        if self.person_id != None:
            self.person_id = self.person_id[0]
            data = self.db.get_Data_by_id(table, self.person_id)[0]
            self.update_table(table,data)
            # Load and resize the new image to match the existing size
            new_image = Image.open(f'Members Photo/{self.person_id}.jpg')
            if new_image:
                new_image = new_image.resize((300, 300), Image.LANCZOS)
                # Update the CTkImage
                self.image_person.configure(dark_image=new_image, size=(300, 300))
                
            else:
                CTkMessagebox(title="Error", message="No photo is finded fo the member", icon="cancel",justify='center',fade_in_duration=1,sound=True)
        else:
            CTkMessagebox(title="Error", message="No matching member found", icon="cancel",justify='center',fade_in_duration=1,sound=True)

