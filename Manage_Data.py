import sqlite3

# Define a class to manage the database operations
class DatabaseManager:
    def __init__(self, db_name):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        # self.create_table()  # Create a table if it doesn't exist
    
    def create_table(self):
        members_table = ('''
            CREATE TABLE IF NOT EXISTS Members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                date_of_birth DATE,
                phone_number TEXT,
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
        attendance_table = ('''
            CREATE TABLE IF NOT EXISTS Attendance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                date DATE NOT NULL,
                check_in_time DATETIME NOT NULL,
                FOREIGN KEY (member_id) REFERENCES Members(id)
            )
        ''')
        payment_table = ('''
            CREATE TABLE IF NOT EXISTS Payment (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                "member_id"	INTEGER NOT NULL,
                "full_name"	TEXT NOT NULL,
                "payment_date" NOT NULL,
                "amount" REAL NOT NULL,
                "payment_method" TEXT NOT NULL,
                FOREIGN KEY (member_id) REFERENCES Members(id)
            )
        ''')
        
        try:
            # Attempt to execute the CREATE TABLE statement
            self.cursor.execute(members_table)
            self.cursor.execute(attendance_table)
            self.cursor.execute(payment_table)
            print("Table 'Members' created successfully (if it didn't exist).")
            print("Table 'Attendance' created successfully (if it didn't exist).")
            print("Table 'Payment' created successfully (if it didn't exist).")

        except sqlite3.OperationalError as e:
            # Handle the case where the table already exists
            print(f"Error: {e}")
    
    # Inset Data
    def insert_member(self, full_name, date_of_birth, phone_number, gender, address, member_status, join_date, membership_type, membership_start_date, membership_end_date, emergency_name, emergency_number):
        try:
            self.cursor.execute('''
                INSERT INTO Members (full_name, date_of_birth, phone_number, gender, address, member_status, join_date, membership_type, membership_start_date, membership_end_date, emergency_name, emergency_number) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (full_name, date_of_birth, phone_number, gender, address, member_status, join_date, membership_type, membership_start_date, membership_end_date, emergency_name, emergency_number))
            self.conn.commit()
            print("Member inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")
    def insert_attendance(self, member_id, full_name, date, check_in_time):
        try:
            self.cursor.execute('''
                INSERT INTO Attendance (member_id, full_name, date, check_in_time) VALUES (?, ?, ?, ?)
            ''', (member_id, full_name, date, check_in_time))
            self.conn.commit()
            print("Attendance inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")
    def insert_payment(self, member_id, full_name, payment_date, amount, payment_method):
        try:
            self.cursor.execute('''
                INSERT INTO Payment (member_id, full_name, payment_date, amount, payment_method) VALUES (?, ?, ?, ?, ?)
            ''', (member_id, full_name, payment_date, amount, payment_method))
            self.conn.commit()
            print("Payment inserted successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")
    
    
    def get_all_members(self,table):
        self.cursor.execute(f'''
            SELECT * FROM {table}
        ''')
        return self.cursor.fetchall()
    
    
    def get_members_id(self, full_name, date_of_birth, phone_number):
        self.cursor.execute('''
            SELECT * FROM Members WHERE full_name=? AND date_of_birth=? AND phone_number=?
        ''', (full_name, date_of_birth, phone_number))
        return self.cursor.fetchone()
    
    def get_Data_by_id(self, table, member_id):
        if table == "Members":
            self.cursor.execute('''
                SELECT * FROM Members WHERE id=?
            ''', (member_id,))  # Pass member_id as a single-element tuple
        else:
            self.cursor.execute(f'''
                SELECT * FROM {table} WHERE member_id=?
            ''', (member_id,))  # Pass member_id as a single-element tuple
        
        return self.cursor.fetchall()

    def update_member(self, table, member_id, field,data):
        try:
            
            if table == "Members":
                self.cursor.execute(f'''
                    UPDATE {table} SET {field}=? WHERE id=?
                ''', (data, member_id))
            else:
                self.cursor.execute(f'''
                    UPDATE {table} SET {field}=? WHERE member_id=?
                ''', (data, member_id))
            self.conn.commit()
            print("User updated successfully.")
        except sqlite3.IntegrityError as e:
            print(f"Error: {e}")
    
    def fully_delete_member(self, member_id):
        self.cursor.execute('''
            DELETE FROM Members WHERE id=?
        ''', (member_id,))
        self.cursor.execute(f'''
            DELETE FROM Attendance WHERE member_id=?
        ''', (member_id,))
        self.cursor.execute(f'''
            DELETE FROM Payment WHERE member_id=?
        ''', (member_id,))
        self.conn.commit()
        print("User deleted successfully.")
    
    def minimal_delete_member(self, member_id):
        self.cursor.execute(f'''
            UPDATE Members SET member_status=? WHERE member_id=?
        ''', ("Closed", member_id))
        self.conn.commit()
        print("User deleted successfully.")
    
    def close_connection(self):
        self.conn.close()
        print("Connection closed.")

# Usage example
if __name__ == "__main__":
    db_manager = DatabaseManager('GYM.db')  # Initialize the database manager
    
    # last_id = 1
    # data = db_manager.get_all_members('Members')
    # if data == []
    #     last_id = 1
    # else:
    #     last_id = int(data[len(data)-1][0]) + 1 

    # db_manager.update_member("Members",1,
    #     "emergency_number",'+1-888-987-6543')
    # print(db_manager.get_Data_by_id("Members",1))
    #db_manager.fully_delete_member(1)
    # print(db_manager.get_members_id("sadfasdf", "dob", "phone"))
    print(db_manager.get_Data_by_id("Members",1)[0][8])
    
    
    db_manager.close_connection()