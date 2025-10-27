import sqlite3

# --- Whitelists for secure queries ---
# Used to prevent SQL injection by validating table/field names
ALLOWED_TABLES = {'Members', 'Attendance', 'Payment'}

ALLOWED_FIELDS = {
    'Members': {
        'full_name', 'date_of_birth', 'phone_number', 'gender', 'address',
        'member_status', 'join_date', 'membership_type', 'membership_start_date',
        'membership_end_date', 'emergency_name', 'emergency_number'
    },
    'Attendance': {'member_id', 'date', 'check_in_time'},
    'Payment': {'member_id', 'payment_date', 'amount', 'payment_method'}
}

class DatabaseManager:
    """
    Manages all database operations for the Gym application using SQLite.
    This class handles table creation, CRUD operations, and ensures
    relational integrity and security.
    """

    def __init__(self, db_name):
        """
        Initializes the database connection and cursor, and ensures
        tables and foreign key support are enabled.

        Args:
            db_name (str): The filename for the SQLite database (e.g., "GYM.db").
        """
        try:
            self.conn = sqlite3.connect(db_name)
            self.cursor = self.conn.cursor()
            print(f"[INFO] Connected to database: {db_name}")
            self.enable_foreign_keys()
            self.create_tables()  # Ensure tables exist on startup
        except sqlite3.Error as e:
            print(f"[CRITICAL] Database connection failed: {e}")
            raise  # Re-raise the exception to stop the app if DB fails

    def __del__(self):
        """
        Destructor to ensure the database connection is closed
        when the object is garbage collected.
        """
        self.close_connection()

    def enable_foreign_keys(self):
        """
        Enables foreign key constraint enforcement in SQLite.
        This is crucial for ON DELETE CASCADE to work.
        """
        try:
            self.cursor.execute("PRAGMA foreign_keys = ON;")
            self.conn.commit()
            print("[INFO] Foreign key enforcement enabled.")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to enable foreign keys: {e}")

    def create_tables(self):
        """
        Creates all necessary tables (Members, Attendance, Payment)
        if they do not already exist.
        """
        members_table = ('''
            CREATE TABLE IF NOT EXISTS Members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                date_of_birth DATE,
                phone_number TEXT UNIQUE,
                gender TEXT,
                address TEXT,
                member_status TEXT,
                join_date DATE NOT NULL,
                membership_type TEXT,
                membership_start_date DATE,
                membership_end_date DATE,
                emergency_name TEXT,
                emergency_number TEXT
            )
        ''')

        # 'full_name' was removed. It's redundant.
        # Get the name by JOINing with the Members table.
        attendance_table = ('''
            CREATE TABLE IF NOT EXISTS Attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                date DATE NOT NULL,
                check_in_time DATETIME NOT NULL,
                FOREIGN KEY (member_id) REFERENCES Members(id) ON DELETE CASCADE
            )
        ''')

        # 'full_name' was removed.
        payment_table = ('''
            CREATE TABLE IF NOT EXISTS Payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                payment_date DATE NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES Members(id) ON DELETE CASCADE
            )
        ''')

        try:
            self.cursor.execute(members_table)
            print("[INFO] 'Members' table checked/created successfully.")
            self.cursor.execute(attendance_table)
            print("[INFO] 'Attendance' table checked/created successfully.")
            self.cursor.execute(payment_table)
            print("[INFO] 'Payment' table checked/created successfully.")
            self.conn.commit()
        except sqlite3.OperationalError as e:
            print(f"[ERROR] Failed to create tables: {e}")

    # --- Insert Operations ---

    def insert_member(self, full_name, date_of_birth, phone_number, gender, address,
                      member_status, join_date, membership_type, membership_start_date,
                      membership_end_date, emergency_name, emergency_number):
        """
        Inserts a new member into the Members table.

        Args:
            All parameters are strings/dates matching the Members table columns.

        Returns:
            int: The ID of the newly inserted member, or None if failed.
        """
        print(f"[INFO] Attempting to insert new member: {full_name}")
        try:
            self.cursor.execute('''
                INSERT INTO Members (full_name, date_of_birth, phone_number, gender, address, 
                                 member_status, join_date, membership_type, membership_start_date, 
                                 membership_end_date, emergency_name, emergency_number) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, date_of_birth, phone_number, gender, address, member_status,
                  join_date, membership_type, membership_start_date, membership_end_date,
                  emergency_name, emergency_number))
            self.conn.commit()
            new_id = self.cursor.lastrowid
            print(f"[SUCCESS] Member inserted successfully. ID: {new_id}")
            return new_id
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Failed to insert member (IntegrityError): {e}. (e.g., Phone number may be duplicated)")
            return None
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to insert member: {e}")
            return None

    def insert_attendance(self, member_id, date, check_in_time):
        """
        Inserts a new attendance record.
        Note: 'full_name' is not stored here to avoid data duplication.

        Args:
            member_id (int): The ID of the member.
            date (str): The date of check-in (e.g., "DD-MM-YYYY").
            check_in_time (str): The time of check-in (e.g., "HH:MM:SS").
        """
        print(f"[INFO] Inserting attendance for member ID: {member_id}")
        try:
            self.cursor.execute('''
                INSERT INTO Attendance (member_id, date, check_in_time) VALUES (?, ?, ?)
            ''', (member_id, date, check_in_time))
            self.conn.commit()
            print("[SUCCESS] Attendance inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Failed to insert attendance (IntegrityError): {e}. (Likely invalid member_id)")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to insert attendance: {e}")

    def insert_payment(self, member_id, payment_date, amount, payment_method):
        """
        Inserts a new payment record.
        Note: 'full_name' is not stored here.

        Args:
            member_id (int): The ID of the member.
            payment_date (str): The date of payment.
            amount (float): The amount paid.
            payment_method (str): The method of payment (e.g., "Cash", "Online").
        """
        print(f"[INFO] Inserting payment for member ID: {member_id}")
        try:
            self.cursor.execute('''
                INSERT INTO Payment (member_id, payment_date, amount, payment_method) 
                VALUES (?, ?, ?, ?)
            ''', (member_id, payment_date, amount, payment_method))
            self.conn.commit()
            print("[SUCCESS] Payment inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"[ERROR] Failed to insert payment (IntegrityError): {e}. (Likely invalid member_id)")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to insert payment: {e}")

    # --- Read/Query Operations ---

    def get_all_from_table(self, table_name):
        """
        Securely fetches all records from a specified table.

        Args:
            table_name (str): The name of the table (must be in ALLOWED_TABLES).

        Returns:
            list: A list of tuples, or an empty list if failed/table not allowed.
        """
        if table_name not in ALLOWED_TABLES:
            print(f"[SECURITY] Denied query to non-whitelisted table: {table_name}")
            return []
        
        print(f"[INFO] Fetching all records from '{table_name}'...")
        try:
            self.cursor.execute(f"SELECT * FROM {table_name}")
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to fetch all from {table_name}: {e}")
            return []

    def get_member_by_details(self, full_name, date_of_birth, phone_number):
        """
        Finds a member based on their name, DOB, and phone number.

        Args:
            full_name (str): Member's full name.
            date_of_birth (str): Member's DOB.
            phone_number (str): Member's phone number.

        Returns:
            tuple: The member's data tuple, or None if not found.
        """
        print(f"[INFO] Searching for member: {full_name}, {phone_number}")
        try:
            self.cursor.execute('''
                SELECT * FROM Members WHERE full_name=? AND date_of_birth=? AND phone_number=?
            ''', (full_name, date_of_birth, phone_number))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to get member by details: {e}")
            return None

    def get_data_by_member_id(self, table_name, member_id):
        """
        Securely fetches all records for a specific member_id from
        Attendance or Payment, or by primary key 'id' from Members.

        Args:
            table_name (str): The table to query (must be in ALLOWED_TABLES).
            member_id (int): The member's ID.

        Returns:
            list: A list of tuples, or an empty list if failed.
        """
        if table_name not in ALLOWED_TABLES:
            print(f"[SECURITY] Denied query to non-whitelisted table: {table_name}")
            return []

        print(f"[INFO] Fetching data for member ID {member_id} from {table_name}")
        try:
            if table_name == "Members":
                self.cursor.execute("SELECT * FROM Members WHERE id=?", (member_id,))
            else:
                self.cursor.execute(f"SELECT * FROM {table_name} WHERE member_id=?", (member_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to get data by member ID: {e}")
            return []

    def get_attendance_with_names(self):
        """
        Example of a relational query: Fetches all attendance records
        and JOINs with the Members table to get the names.

        Returns:
            list: A list of tuples (Attendance.id, member_id, Member.full_name, date, check_in_time)
        """
        print("[INFO] Fetching all attendance records with member names...")
        try:
            self.cursor.execute('''
                SELECT A.id, A.member_id, M.full_name, A.date, A.check_in_time 
                FROM Attendance AS A
                JOIN Members AS M ON A.member_id = M.id
            ''')
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to get attendance with names: {e}")
            return []

    # --- Update Operations ---

    def update_field_by_id(self, table_name, row_id, field_name, new_data):
        """
        Securely updates a single field in a specific row.
        
        Args:
            table_name (str): The table to update (must be in ALLOWED_TABLES).
            row_id (int): The primary key (the 'id' column) of the row to update.
            field_name (str): The column name to update (must be in ALLOWED_FIELDS).
            new_data (any): The new value to set.
        """
        if table_name not in ALLOWED_TABLES:
            print(f"[SECURITY] Denied update to non-whitelisted table: {table_name}")
            return
        if field_name not in ALLOWED_FIELDS[table_name]:
            print(f"[SECURITY] Denied update to non-whitelisted field: {field_name}")
            return

        print(f"[INFO] Updating {table_name}.{field_name} for row ID {row_id}")
        try:
            self.cursor.execute(f'''
                UPDATE {table_name} SET {field_name}=? WHERE id=?
            ''', (new_data, row_id))
            self.conn.commit()
            print("[SUCCESS] Record updated successfully.")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to update record: {e}")

    # --- Delete Operations ---

    def fully_delete_member(self, member_id):
        """
        Deletes a member from the Members table.
        Due to 'ON DELETE CASCADE', all associated records in
        Attendance and Payment will be deleted automatically by the database.

        Args:
            member_id (int): The ID of the member to delete.
        """
        print(f"[WARN] Attempting to fully delete member ID: {member_id} and all related data.")
        try:
            self.cursor.execute("DELETE FROM Members WHERE id=?", (member_id,))
            self.conn.commit()
            print(f"[SUCCESS] User {member_id} deleted successfully from Members (and all related tables).")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to fully delete member: {e}")

    def minimal_delete_member(self, member_id):
        """
        Performs a "soft delete" by updating the member's status to "Closed".
        This keeps their data for historical records.

        Args:
            member_id (int): The ID of the member to "close".
        """
        print(f"[INFO] Setting member status to 'Closed' for ID: {member_id}")
        # --- BUG FIX ---
        # Was: WHERE member_id=? (which doesn't exist on Members)
        # Now: WHERE id=?
        try:
            self.cursor.execute("UPDATE Members SET member_status=? WHERE id=?", ("Closed", member_id))
            self.conn.commit()
            print("[SUCCESS] User status set to 'Closed'.")
        except sqlite3.Error as e:
            print(f"[ERROR] Failed to minimally delete member: {e}")

    def close_connection(self):
        """
        Closes the database connection if it is open.
        """
        if self.conn:
            print("[INFO] Closing database connection.")
            self.conn.close()
            self.conn = None # Set to None to prevent reuse

# --- Usage Example ---
def main():
    """
    Main function to demonstrate and test DatabaseManager functionality.
    """
    print("--- Running DatabaseManager Test ---")
    db_manager = None
    try:
        db_manager = DatabaseManager('GYM.db')
        
        # --- Create ---
        print("\n--- Testing Inserts ---")
        new_id = db_manager.insert_member(
            "Test User", "2000-01-01", "1234567890", "Other", "123 Main St", 
            "ROOKIE", "2024-01-01", "Monthly", "2024-01-01", "2024-02-01", 
            "Emergency Contact", "0987654321"
        )
        
        if new_id:
            db_manager.insert_attendance(new_id, "27-10-2025", "15:00:00")
            db_manager.insert_payment(new_id, "27-10-2025", 500.00, "Cash")
        
        # --- Read ---
        print("\n--- Testing Reads ---")
        print("All Members:")
        members = db_manager.get_all_from_table('Members')
        for member in members:
            print(member)
        
        print("\nAttendance with Names:")
        att_with_names = db_manager.get_attendance_with_names()
        for row in att_with_names:
            print(row)
            
        print("\nGet Member by Details (Test User):")
        found_member = db_manager.get_member_by_details("Test User", "2000-01-01", "1234567890")
        print(found_member)
        
        # --- Update ---
        if new_id:
            print("\n--- Testing Update ---")
            db_manager.update_field_by_id('Members', new_id, 'member_status', 'PAID')
            updated_member = db_manager.get_data_by_member_id('Members', new_id)
            print(f"Updated Member: {updated_member}")
            
        # --- Delete (Soft) ---
        if new_id:
            print("\n--- Testing Soft Delete ---")
            db_manager.minimal_delete_member(new_id)
            updated_member = db_manager.get_data_by_member_id('Members', new_id)
            print(f"Soft-deleted Member: {updated_member}")

        # --- Delete (Full) ---
        # Uncomment the following lines to test full deletion
        # if new_id:
        #     print("\n--- Testing Full Delete ---")
        #     db_manager.fully_delete_member(new_id)
        #     print("Members after delete:")
        #     print(db_manager.get_all_from_table('Members'))
        #     print("Attendance after delete:")
        #     print(db_manager.get_all_from_table('Attendance'))

    except Exception as e:
        print(f"\n--- An error occurred during the test --- \n{e}")
    
    finally:
        if db_manager:
            db_manager.close_connection()
    print("\n--- Test Finished ---")

if __name__ == "__main__":
    main()
