from PIL import Image
import customtkinter as ctk
from New_Member import NewMember
from Mark_Attendance import MarkAttendance
from View_Data import ViewData
from Edit_Data import EditData
from Payment import Payment
import pywhatkit as kit
from pywhatkit.core.exceptions import InternetException, CallTimeException, CountryCodeException
import json
from datetime import datetime, timedelta
from Manage_Data import DatabaseManager
import CTkMessagebox

json_file_path = 'reminders.json'
message = CTkMessagebox.CTkMessagebox

class Home(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Attendance System")
        self.geometry('400x650')
        ctk.set_appearance_mode('dark')
        
        self.db = DatabaseManager("GYM.db")
        self.members_data = self.db.get_all_members("Members")
        
        self.layout()
        
        self.check_membership_status_and_send_reminder(self.members_data, json_file_path)
        
        self.mainloop()
        
    def layout(self):
        #image
        image_muscleHouse = ctk.CTkImage(light_image=Image.open('images/Muscle House.png'),
                                         dark_image=Image.open('images/Muscle House.png'),
                                         size=(200,200))

        image_label = ctk.CTkLabel(self, image=image_muscleHouse)
        image_label.pack(pady=20)
        
        self.create_button("Add New Member", NewMember)
        self.create_button("Mark Attendance", MarkAttendance)
        
        self.create_button("View Data", ViewData)
        self.create_button("Edit/Delete Data", EditData)
        self.create_button("Payment", Payment)

        exit_button = ctk.CTkButton(self, text='Exit', font=("Poppins", 20), width=220,
                                    fg_color="#EF5A6F", corner_radius=7, text_color='#FFF1DB', hover_color="#FFAAAA",
                                    command=self.exit)
        exit_button.pack(pady=25)
    
    def create_button(self, text, window_class):
        button = ctk.CTkButton(self, text=text, font=("Poppins", 20), width=220,
                               fg_color="#fff", corner_radius=7, text_color='#000000', hover_color="#CAF4FF",
                               command=lambda: self.open_window(window_class))
        button.pack(pady=10)
    
    def open_window(self, window_class):
        window = window_class(self)
        window.grab_set()
    
    def exit(self):
        self.destroy()
        
    def load_reminder_data(self,file_path):
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            return {}

    def save_reminder_data(self,file_path, data):
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def should_send_reminder(self,last_reminder_date):
        if not last_reminder_date:
            return True
        last_reminder = datetime.strptime(last_reminder_date, '%Y-%m-%d')
        return (datetime.now() - last_reminder) > timedelta(days=3)

    def update_reminder_data(self,reminder_data, member):
        member_id = str(member[0])
        reminder_data[member_id] = {
            'name': member[1],
            'last_reminder_date': datetime.now().strftime('%Y-%m-%d')
        }

    def check_membership_status_and_send_reminder(self,members, json_file_path):
        reminder_data = self.load_reminder_data(json_file_path)
        
        for member in members:
            if member[6] == 'UNPAID' or  member[6] == "ROOKIE":
                member_id = str(member[0])
                last_reminder_date = reminder_data.get(member_id, {}).get('last_reminder_date')
                
                if self.should_send_reminder(last_reminder_date):
                    phone_number = f"+91{member[3]}"
                    message = f"Hello {member[1]},\n\nThis is a reminder that you have not paid for your gym membership yet. Please make the payment at your earliest convenience to continue enjoying our services.\n\nThank you!"
                    
                    try:
                        # Send the WhatsApp message
                        kit.sendwhatmsg_instantly(phone_number, message)
                        print(f"Sent reminder to {member[1]} ({phone_number})")
                        
                        # Update the reminder data
                        self.update_reminder_data(reminder_data, member)
                    except InternetException:
                        print("Failed to send message due to an Internet connection error.")
                    except CallTimeException:
                        print("Failed to send message due to an invalid call time.")
                    except CountryCodeException:
                        print("Failed to send message due to an invalid country code.")
                    except Exception as e:
                        print(f"Failed to send message to {member[1]} ({phone_number}). Error: {e}")
                        message(title="Error", message=f"Failed to send message to {member[1]} ({phone_number}). Error: {e}", icon="cancel", option_1="OK",justify='center',fade_in_duration=1,sound=True)
                        
        self.save_reminder_data(json_file_path, reminder_data)

if __name__ == "__main__":
    Home()