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
import sys  # Import sys for exiting on critical error

# --- Globals ---
JSON_FILE_PATH = 'reminders.json'
MESSAGE_BOX = CTkMessagebox.CTkMessagebox

class Home(ctk.CTk):
    """
    Main application window (Home screen) for the Gym Attendance System.
    This class initializes the main menu, loads member data, and triggers
    the automatic payment reminder check.
    """
    def __init__(self):
        """
        Initializes the main application window, database connection,
        and loads initial data.
        """
        super().__init__()
        print("[INFO] Initializing main application...")
        self.title("Gym Management System")
        self.geometry('400x650')
        ctk.set_appearance_mode('dark')

        self.db = None
        self.members_data = []

        try:
            # Connect to the database
            self.db = DatabaseManager("GYM.db")
            
            # --- UPDATED LINE ---
            # Load all member data on startup using the new secure function
            self.members_data = self.db.get_all_from_table("Members")
            # --- END OF UPDATE ---
            
            print(f"[INFO] Loaded {len(self.members_data)} members from database.")
        except Exception as e:
            print(f"[CRITICAL] Failed to load database: {e}")
            MESSAGE_BOX(title="Critical Error",
                        message=f"Could not load database. The application will close.\n\nError: {e}",
                        icon="cancel")
            sys.exit(1) # Exit the application if DB fails

        # Draw the UI components
        self.layout()

        # Check for reminders *after* the main window has loaded
        # This prevents the app from freezing on startup
        print("[INFO] Scheduling reminder check...")
        self.after(1000, self.check_membership_status_and_send_reminder)

        self.mainloop()

    def layout(self):
        """
        Creates and places all widgets on the main window.
        """
        print("[INFO] Building main layout...")
        try:
            # Logo Image
            image_muscleHouse = ctk.CTkImage(light_image=Image.open('images/Muscle House.png'),
                                             dark_image=Image.open('images/Muscle House.png'),
                                             size=(200, 200))
            image_label = ctk.CTkLabel(self, image=image_muscleHouse, text="")
            image_label.pack(pady=20)
        except FileNotFoundError:
            print("[ERROR] 'images/Muscle House.png' logo not found.")
            # Create a placeholder label if image is missing
            image_label = ctk.CTkLabel(self,
                                     text="Muscle House Logo (Not Found)",
                                     font=("Poppins", 16),
                                     width=200, height=200,
                                     fg_color="gray20")
            image_label.pack(pady=20)
        except Exception as e:
            print(f"[ERROR] Failed to load logo: {e}")

        # --- Menu Buttons ---
        self.create_button("Add New Member", NewMember)
        self.create_button("Mark Attendance", MarkAttendance)
        self.create_button("View Data", ViewData)
        self.create_button("Edit/Delete Data", EditData)
        self.create_button("Payment", Payment)

        # --- Exit Button ---
        exit_button = ctk.CTkButton(self, text='Exit', font=("Poppins", 20), width=220,
                                    fg_color="#EF5A6F", corner_radius=7, text_color='#FFF1DB', hover_color="#FFAAAA",
                                    command=self.exit_app)
        exit_button.pack(pady=25)

    def create_button(self, text, window_class):
        """
        Helper function to create a standardized menu button.

        Args:
            text (str): The text to display on the button.
            window_class (Toplevel): The class of the window to open when clicked.
        """
        button = ctk.CTkButton(self, text=text, font=("Poppins", 20), width=220,
                               fg_color="#fff", corner_radius=7, text_color='#000000', hover_color="#CAF4FF",
                               command=lambda: self.open_window(window_class))
        button.pack(pady=10)

    def open_window(self, window_class):
        """
        Opens a new Toplevel window and makes it modal.
        (Prevents interaction with the main window until closed)

        Args:
            window_class (Toplevel): The window class to instantiate.
        """
        try:
            print(f"[INFO] Opening window: {window_class.__name__}")
            window = window_class(self)
            window.grab_set()  # Makes the new window modal
        except Exception as e:
            print(f"[ERROR] Failed to open window {window_class.__name__}: {e}")
            MESSAGE_BOX(title="Error", message=f"Could not open window.\n\nError: {e}", icon="cancel")

    def exit_app(self):
        """
        Closes the application.
        """
        print("[INFO] Exiting application.")
        self.destroy()

    def load_reminder_data(self, file_path):
        """
        Loads the reminder history from a JSON file.

        Args:
            file_path (str): The path to the reminders.json file.

        Returns:
            dict: The loaded reminder data, or {} if not found/invalid.
        """
        try:
            with open(file_path, 'r') as file:
                data = json.load(file)
                print(f"[INFO] Loaded reminder data from {file_path}")
                return data
        except FileNotFoundError:
            print(f"[WARN] {file_path} not found. Will create a new one.")
            return {}
        except json.JSONDecodeError:
            print(f"[ERROR] {file_path} is corrupt or poorly formatted. Returning empty data.")
            return {}
        except Exception as e:
            print(f"[ERROR] Failed to load reminder data: {e}")
            return {}

    def save_reminder_data(self, file_path, data):
        """
        Saves the updated reminder history to a JSON file.

        Args:
            file_path (str): The path to the reminders.json file.
            data (dict): The reminder data to save.
        """
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=4)
            print(f"[INFO] Saved updated reminder data to {file_path}")
        except (IOError, PermissionError) as e:
            print(f"[ERROR] Could not save reminder data to {file_path}: {e}")
            MESSAGE_BOX(title="Error", message=f"Could not save reminder file.\n\nError: {e}", icon="cancel")
        except Exception as e:
            print(f"[ERROR] An unexpected error occurred while saving reminder data: {e}")

    def should_send_reminder(self, last_reminder_date):
        """
        Checks if a new reminder should be sent (last reminder was > 3 days ago).

        Args:
            last_reminder_date (str): The date string (YYYY-MM-DD) of the last reminder.

        Returns:
            bool: True if a reminder should be sent, False otherwise.
        """
        if not last_reminder_date:
            print("[INFO] No last reminder date found. Sending reminder.")
            return True  # No reminder sent before
        try:
            last_reminder = datetime.strptime(last_reminder_date, '%Y-%m-%d')
            # Check if more than 3 days have passed
            should_send = (datetime.now() - last_reminder) > timedelta(days=3)
            print(f"[INFO] Last reminder: {last_reminder_date}. Send new: {should_send}")
            return should_send
        except ValueError:
            print(f"[ERROR] Invalid date format '{last_reminder_date}' in JSON. Sending reminder just in case.")
            return True # Send if date is corrupt

    def update_reminder_data(self, reminder_data, member):
        """
        Updates the reminder dictionary with the current date for a member.

        Args:
            reminder_data (dict): The full reminder data dictionary.
            member (tuple): The member's data tuple from the database.
        """
        # member[0] is ID, member[1] is Name
        member_id = str(member[0])
        reminder_data[member_id] = {
            'name': member[1],
            'last_reminder_date': datetime.now().strftime('%Y-%m-%d')
        }

    def check_membership_status_and_send_reminder(self):
        """
        Loops through all members, checks their payment status, and sends
        a WhatsApp reminder if they are UNPAID or ROOKIE and haven't
        received a reminder in the last 3 days.

        Uses self.members_data and JSON_FILE_PATH.
        """
        print("[INFO] --- Starting membership reminder check ---")
        reminder_data = self.load_reminder_data(JSON_FILE_PATH)

        for member in self.members_data:
            # member[6] is payment_status
            member_status = member[6]
            if member_status == 'UNPAID' or member_status == "ROOKIE":
                # member[0] is ID
                member_id = str(member[0])
                last_reminder_date = reminder_data.get(member_id, {}).get('last_reminder_date')

                if self.should_send_reminder(last_reminder_date):
                    # member[3] is phone_no
                    # NOTE: Assumes all phone numbers are Indian (+91).
                    phone_number = f"+91{member[3]}"
                    # member[1] is full_name
                    message_body = (f"Hello {member[1]},\n\n"
                                    "This is a reminder from Muscle House Gym.\n"
                                    "Our records show your membership payment is pending. "
                                    "Please make the payment at your earliest convenience to continue enjoying our services.\n\n"
                                    "Thank you!")

                    print(f"[INFO] Attempting to send reminder to {member[1]} ({phone_number})")
                    try:
                        # Send the WhatsApp message
                        kit.sendwhatmsg_instantly(phone_number, message_body, wait_time=15, tab_close=True)
                        print(f"[SUCCESS] Sent reminder to {member[1]} ({phone_number})")

                        # Update the reminder data
                        self.update_reminder_data(reminder_data, member)

                    except InternetException:
                        print("[ERROR] Failed to send message: No internet connection.")
                        MESSAGE_BOX(title="Error", message="No internet connection. Reminder was not sent.", icon="warning")
                    except CallTimeException:
                        print("[ERROR] Failed to send message: Invalid call time (pywhatkit).")
                    except CountryCodeException:
                        print(f"[ERROR] Failed to send message: Invalid country code for {phone_number}.")
                    except Exception as e:
                        print(f"[ERROR] Failed to send message to {member[1]} ({phone_number}). Error: {e}")
                        MESSAGE_BOX(title="Error",
                                    message=f"Failed to send message to {member[1]}.\n\nError: {e}",
                                    icon="cancel")
                else:
                    print(f"[INFO] Skipping reminder for {member[1]} (sent recently).")

        # Save any updates to the reminder file
        self.save_reminder_data(JSON_FILE_PATH, reminder_data)
        print("[INFO] --- Finished membership reminder check ---")

if __name__ == "__main__":
    Home()