# LifeLink - Blood Donor Finder & Donation Registration

**LifeLink** is a modern, responsive healthcare platform designed to connect blood donors with patients in need. It features a robust Python Flask backend, SQLite database storage with SQLAlchemy, secure password-hashed user credentials, donor profile management (CRUD operations), emergency blood request triggers, and a comprehensive admin control panel.

---

## Technical Stack
- **Backend**: Flask, Flask-SQLAlchemy (ORM)
- **Database**: SQLite
- **Frontend**: Responsive HTML5, CSS3 Variables (Modern Red & White Theme), JavaScript (ES6+ AJAX, Validation)
- **Graphics**: Custom medical illustrations

---

## Directory Hierarchy
```
blood/
├── app.py                     # Main application configuration & routing
├── models.py                  # Database Models (User, Donor, EmergencyRequest)
├── requirements.txt           # Dependency specifications
├── README.md                  # Setup and execution guide
├── static/
│   ├── css/
│   │   └── style.css          # CSS Layout, variables, grids, and keyframes
│   ├── js/
│   │   └── main.js           # Navbar, FAQ accordions, availability AJAX, validations
│   └── img/
│       └── hero-banner.png    # Custom healthcare header illustration
└── templates/
    ├── base.html              # Core layout (header nav, flashing alerts, footer)
    ├── home.html              # Hero, dynamic stats counters, feature grids
    ├── about.html             # Donation facts, eligibility, FAQ accordion, compatibility grid
    ├── register_donor.html    # Verified donor registration & details editing form
    ├── find_donor.html        # Filtered donor search showing responsive cards
    ├── contact.html           # Feedback form, contact credentials, Google Maps iframe
    ├── login.html             # User login form
    ├── register.html          # User registration form
    ├── dashboard.html         # User panel, availability toggle switch, deletion/update tools
    ├── admin.html             # Admin database summary tables with complete CRUD actions
    └── emergency.html         # Active emergency request listings & request creation forms
```

---

## Step-by-Step Setup Instructions

### Prerequisites
Ensure you have **Python 3.8 or higher** installed on your operating system.

### 1. Clone or Open Workspace
Place all the project files into a workspace directory (e.g., `C:\Users\gurup\Desktop\blood`).

### 2. Set Up Virtual Environment (Recommended)
Open your terminal (PowerShell, Command Prompt, or bash) and navigate to the project directory:
```bash
cd c:\Users\gurup\Desktop\blood
```
Create a virtual environment:
```bash
python -m venv venv
```
Activate the virtual environment:
- **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
- **Windows (CMD)**:
  ```cmd
  .\venv\Scripts\activate.bat
  ```
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```

### 3. Install Dependencies
Install the required packages using pip:
```bash
pip install -r requirements.txt
```

### 4. Database Initialization & Seeding
The application has a self-seeding database setup built in. When you start the Flask application for the first time, it automatically creates the SQLite database (`lifelink.db`) and inserts test data, including an administrator account, test users, test donors, and active emergency requests.

### 5. Run the Application
Start the Flask development server:
```bash
python app.py
```
You should see output indicating the server is running:
```
Seeding database with default users, donors, and emergency requests...
Database seeded successfully!
 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:5000
```
Open your web browser and navigate to `http://127.0.0.1:5000` to interact with LifeLink.

---

## Default User Accounts (Seed Data)

The database comes pre-seeded with the following credentials to make testing immediate:

### 1. Administrator Account
- **Username**: `admin`
- **Password**: `admin123`
- *Use this account to access the `/admin` panel, where you can modify or delete any donor details, toggle emergency request fulfillment statuses, and manage user accounts.*

### 2. Standard User Account 1 (Registered Donor)
- **Username**: `john_doe` (linked donor name: *John Doe*, Blood: *O+*, Status: *Available*)
- **Password**: `password123`
- *Log in to view John's dashboard, toggle his availability toggle switch, or update his profile.*

### 3. Standard User Account 2 (Registered Donor - Unavailable)
- **Username**: `david_miller` (linked donor name: *David Miller*, Blood: *B+*, Status: *Unavailable*)
- **Password**: `password123`

### 4. Standard User Account 3 (Not a Donor)
- **Username**: `jane_smith` (linked donor name: *Jane Smith*, Blood: *A-*, Status: *Available*)
- **Password**: `password123`

---

## Features Walkthrough for Evaluation

1. **Anonymous Mode**:
   - Visit the home, about, find donor, and contact pages.
   - Run a search on the **Find Donor** page (e.g. search for blood group `O+` or city `New York`). You will see search cards but the phone numbers and email details are obscured (`+1 XXX-XXX-XXXX` and `hidden@email.com`) to protect donor privacy.
2. **Standard User Login**:
   - Log in using `john_doe` / `password123`.
   - Perform the search again on **Find Donor**. The contact numbers will now be visible, and click-to-call buttons will be active.
   - Go to **Dashboard** to see John's donor profile. Flip the **Availability Switch**. It uses an AJAX call to save to the database dynamically without page refreshes.
   - Search again or look at the admin page to see the updated status.
3. **Emergency Blood Requests**:
   - Click **Emergency Requests** in the navbar.
   - Submit an emergency form. If you are logged in, it will save it, show a success alert, and trigger a mock console email notification letting all matching available donors know that their blood type is needed urgently in that city.
4. **Admin Panel**:
   - Log in using `admin` / `admin123` and click **Admin Panel** in the navbar.
   - You can edit any donor's details (using the collapsible `<details>` accordion form), delete any donor, toggle the fulfillment of emergency requests (marking them resolved), or toggle standard user roles to make them administrators.
