from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import ttk
import cv2
import Manage_Data
import CTkMessagebox
from datetime import datetime, timedelta

BUTTON_FONT = ("Poppins", 20)
LABEL_FONT = ("Poppins", 16)

message = CTkMessagebox.CTkMessagebox

class Payment(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Attendance System")
        self.geometry("1400x800")
        ctk.set_appearance_mode('dark')
        
        self.db = Manage_Data.DatabaseManager("GYM.db")
        
        self.person_id = None
        self.data = self.db.get_all_members('Payment')
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
        
        ctk.CTkLabel(infoFrame, text='Payment', font=("Poppins", 30, "bold")).pack()
        
        self.person_photo(infoFrame).pack(padx=20, pady=10, anchor='n')
        
        entryFrame = ctk.CTkFrame(infoFrame, fg_color='transparent')
        self.full_name_entry = self.labelEntry_Component(entryFrame, 'Full Name', 'Tony Stark')
        self.dob_entry = self.labelEntry_Component(entryFrame, 'Date of Birth', '12-03-1985')
        self.phone_entry = self.labelEntry_Component(entryFrame, 'Phone No.', '9674528439')
        
        paymentFrame = ctk.CTkFrame(entryFrame, fg_color='transparent')
        self.payment_date_entry = self.labelEntry_Component(paymentFrame, 'Payment Date', f"{datetime.now().strftime('%d-%m-%Y')}")
        
        ctk.CTkLabel(paymentFrame, text="Amount", font=LABEL_FONT).pack(anchor='w')
        self.amount_ComboBox = ctk.CTkComboBox(paymentFrame, values=["Monthly : 700", "Quarterly : 1800", "Half-yearly : 3000", "Yearly : 4800"], font=LABEL_FONT)
        self.amount_ComboBox.pack(fill='x', pady=5)
        
        ctk.CTkLabel(paymentFrame, text="Paymen Method", font=LABEL_FONT).pack(anchor='w')
        self.payment_method_ComboBox = ctk.CTkComboBox(paymentFrame, values=["Online", "Offline"], font=LABEL_FONT)
        self.payment_method_ComboBox.pack(fill='x', pady=5)
        paymentFrame.pack(padx=5, anchor='w', pady=20)
        
        entryFrame.pack(padx=5, anchor='w', pady=20)
        
        # Add new member button
        add_member_button = ctk.CTkButton(infoFrame, text='Search User', font=BUTTON_FONT,
                      fg_color="#fff", corner_radius=7, text_color='#000000',
                      hover_color="#CAF4FF",command=self.search_user)
        add_member_button.pack(fill='x', padx=20, expand=True)
        
        # Take Photo
        take_photo_button = ctk.CTkButton(infoFrame, text='Add Payment', font=BUTTON_FONT,
                      fg_color="#fff", corner_radius=7, text_color='#000000',
                      hover_color="#CAF4FF",command=self.add_payment)
        take_photo_button.pack(fill='x', padx=20, expand=True, pady=10)
        
        infoFrame.place(relx=0, rely=0, relwidth=0.25, relheight=1)
        
        # Table Frame
        tableFrame = ctk.CTkFrame(self,fg_color='transparent')
        
        self.table = ttk.Treeview(
            tableFrame,
            columns=("id","member_id", "full_name", 'payment_date', "amount","payment_method"),
            show='headings'
        )
        self.table.heading('id', text='ID')
        self.table.heading('member_id', text='Member Id')
        self.table.heading('full_name', text='Full Name')
        self.table.heading('payment_date', text='Payment Date')
        self.table.heading('amount', text='Amount')
        self.table.heading('payment_method', text='Payment Method')
        
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
    
    def update_table(self,data):
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
        
        self.image_label = ctk.CTkLabel(frame, image=self.image_person, text="")
        self.image_label.pack()
        return frame
    
    def search_user(self):
        name = self.full_name_entry.get().strip().title()
        dob = self.dob_entry.get().strip()
        phone = self.phone_entry.get().strip()
        
        if not name or not dob or not phone:
            message(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        if len(phone) > 10 or len(phone) < 10:
            message(title="Error", message="Phone Number not filled correctly", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        
        self.person_id = self.db.get_members_id(name, dob, phone)
        
        if self.person_id != None:
            self.person_id = self.person_id[0]
            
            self.data = self.db.get_Data_by_id("Payment",self.person_id)
            self.update_table(self.data)
            
            # Load and resize the new image to match the existing size
            new_image = Image.open(f'Members Photo/{self.person_id}.jpg')
            if new_image:
                new_image = new_image.resize((300, 300), Image.LANCZOS)
                # Update the CTkImage
                self.image_person.configure(dark_image=new_image, size=(300, 300))
            else:
                message(title="Error", message="No photo is finded for the member", icon="cancel",justify='center',fade_in_duration=1,sound=True)
        else:
            message(title="Error", message="No matching member found", icon="cancel",justify='center',fade_in_duration=1,sound=True)

    def add_payment(self):
        date = self.payment_date_entry.get().strip()
        amount = self.amount_ComboBox.get().split(" : ")[1]
        method = self.payment_method_ComboBox.get()
        
        if not date or not amount or not method:
            message(title="Error", message="Please fill all fields", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            return
        
        if self.person_id != None:
            self.db.insert_payment(self.person_id, self.full_name_entry.get().strip().title(),date,amount,method)
            self.update_member_payment(self.person_id)
            self.data = self.db.get_Data_by_id("Payment",self.person_id)
            self.update_table(self.data)
            message(title="Success",message="Payment added successfully",icon="check", option_1="OK",justify='center',fade_in_duration=1)
        else:
            message(title="Error", message="Search the user first", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
            
    def update_member_payment(self, member_id):
        # Calculate the start and end dates
        start_date = datetime.now()
        subcription = self.db.get_Data_by_id("Members",member_id)[0][8]
        if subcription == 'Monthly':
            end_date = start_date + timedelta(days=30)
        elif subcription == 'Quarterly':
            end_date = start_date + timedelta(days=90)
        elif subcription == 'Half-yearly':
            end_date = start_date + timedelta(days=182)
        elif subcription == 'Yearly':
            end_date = start_date + timedelta(days=365)
        else:
            raise ValueError("Invalid membership type")
        
        self.db.update_member("Members",member_id,"member_status","PAID")
        self.db.update_member("Members",member_id,"membership_start_date",start_date.strftime('%d-%m-%Y'))
        self.db.update_member("Members",member_id,"membership_end_date", end_date.strftime('%d-%m-%Y'))
        
        