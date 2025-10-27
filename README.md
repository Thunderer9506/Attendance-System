# 🏋️ Gym Management System

A **desktop application** built with **Python** and **CustomTkinter** to manage gym members, track attendance using **facial recognition**, handle payments, and send **automatic payment reminders via WhatsApp**.

---

## 🚀 Features

- **Member Management:** Add new members with their photo, contact details, and membership plan.  
- **Facial Recognition Attendance:** Mark member attendance automatically using a webcam.  
- **Manual Attendance:** Manually mark attendance for members.  
- **Payment Processing:** Log payments for members and automatically update their membership status.  
- **View & Edit Data:** A comprehensive dashboard to view, search, edit, and delete member records and their associated attendance/payment history.  
- **Automated Reminders:** Automatically checks for unpaid memberships on startup and sends WhatsApp reminders to members.

---

## 🧠 Technology Stack

- **Language:** Python 3  
- **GUI:** customtkinter (for the modern user interface)  
- **Database:** sqlite3 (for local data storage)  
- **Face Recognition:** face_recognition (built on dlib)  
- **Camera:** opencv-python (for capturing camera feed)  
- **Image Processing:** Pillow (PIL)  
- **Notifications:** pywhatkit (for sending WhatsApp reminders)  
- **Alerts:** CTkMessagebox (for in-app pop-up messages)

---

## ⚙️ Installation and Setup

This project uses the `face_recognition` library, which depends on **dlib**. Installing dlib on Windows is famously difficult because it needs to be compiled from source.

Follow these steps for the most reliable installation.

---

### 1. Prerequisites

- Python 3.8+  
- A webcam (for the attendance feature)

---

### 2. Clone the Repository

```bash
git clone https://github.com/your-username/gym-management-system.git
cd gym-management-system
```

---

### 3. The `face_recognition` & `dlib` Problem

`pip install face_recognition` will almost certainly fail on a clean Windows machine.  
This is because it tries to build `dlib`, which requires the **Desktop development with C++** workload from Visual Studio — a multi-gigabyte download.

Here are two much better solutions.

---

## ✅ Solution A: Recommended (Using uv)

`uv` is an extremely fast Python package installer that is a drop-in replacement for pip.  
It is much better at resolving and installing complex packages like `dlib`.

#### Install uv

**Windows (PowerShell):**
```bash
irm https://astral.sh/uv/install.ps1 | iex
```

**macOS/Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### Create a Virtual Environment (with uv)
```bash
uv venv
```

#### Activate the Environment

**Windows:**
```bash
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

#### Install All Requirements (with uv)

Create a `requirements.txt` file in your project folder, then run:
```bash
uv pip install -r requirements.txt
```

`uv` will handle the difficult `dlib` dependency smoothly.

---

## 🧰 Solution B: Manual (Pre-trained dlib file)

If you prefer to use `pip`, you must install `dlib` manually before installing `face_recognition`.

#### Create and activate a virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate
```

#### Find your Python version:
```bash
python --version
# e.g., Python 3.10.6
```

#### Download the pre-trained `dlib` wheel (.whl) file:
- Go to a trusted source, such as the unofficial Windows binaries page or a community-driven GitHub repo for `dlib` wheels.
- Find the file that matches your Python version (e.g., `cp310` for Python 3.10) and your system (e.g., `amd64` for 64-bit Windows).
- **Example file name:** `dlib-19.24.0-cp310-cp310-win_amd64.whl`

#### Install the `.whl` file with pip:
```bash
pip install "path/to/your/dlib-19.24.0-cp310-cp310-win_amd64.whl"
```

#### Install the rest of the requirements:
```bash
pip install customtkinter face_recognition opencv-python Pillow pywhatkit CTkMessagebox
```

---

## 🧑‍💻 How to Use the Project

Once all the dependencies are installed and your virtual environment is active:

#### Run the application:
```bash
python Attendance_System.py
```

#### Create Directories:
The application will automatically look for two folders. Please create them in the main project directory:

- `images/`: Place your `Muscle House.png` logo and `person.jpg` placeholder here.  
- `Members Photo/`: This folder will be used to store the photos of new members.

---

## 💼 Using the App

- **Add a Member:** Use the “Add New Member” screen. Fill in all details and click “Take Photo” before clicking “Add Member.”  
- **Mark Attendance:** Use the “Mark Attendance” screen. Click “Start Recognition” to use the webcam or fill in fields to mark attendance manually.  
- **Payments & Data:** Use the “Payment” and “View Data” screens to manage the member database.

---

## 🗃️ Database Note

This project uses an SQLite database (`GYM.db`). This file is created automatically on the first run.

If you ever need to change the database structure (e.g., add a new column to the Members table in `Manage_Data.py`),  
you must **delete the old `GYM.db` file** for your changes to take effect.  
The app will then generate a new, empty database with the correct structure.
