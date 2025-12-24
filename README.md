# ✈️ EventPilot

> **Plan Your Perfect Event. Connect with Best Vendors.**

EventPilot is a comprehensive **Event Management Marketplace** connecting event organizers with trusted local vendors. It streamlines the planning process by offering features for discovery, secure booking, budget negotiation, and lead management.

![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Framework-Flask-green) ![MySQL](https://img.shields.io/badge/Database-MySQL-orange) ![Status](https://img.shields.io/badge/Status-Development-yellow)

---

## 📖 Table of Contents
1. [Features](#-features)
2. [Technology Stack](#-technology-stack)
3. [Database Schema](#-database-schema)
4. [Installation & Setup](#-installation--setup)
5. [Project Structure](#-project-structure)
6. [Usage Guide](#-usage-guide)

---

## 🌟 Features

### 👤 User (Event Organizer)
* **Search & Discovery:** Browse vendors by category (Caterers, DJs, Decorators, etc.) and location.
* **Secure Authentication:** Sign up/Login with **OTP Email Verification**.
* **Smart Booking:** Request quotes from vendors with specific event details (Budget, Date, Time, Requirements).
* **Transparency:** View vendor profiles, starting prices, and services offered.

### 🏢 Vendor (Service Provider)
* **Dedicated Dashboard:** Manage incoming leads, track revenue, and monitor booking stats.
* **Lead Management:** Accept or Reject booking requests based on availability and price.
* **Profile Management:** Update pricing, portfolio images, and business descriptions.
* **Status Tracking:** Visualize the status of requests (Pending, Confirmed, Rejected).

### 🛡️ Admin & Super Admin
* **RBAC System:** Role-Based Access Control for Super Admins and Moderators.
* **Analytics Dashboard:** Monitor total users, verified vendors, active bookings, and system health.
* **Vendor Verification:** Review and approve/reject new vendor signups before they go live.
* **User Management:** Ability to manage platform admins and users via a comprehensive list view.

---

## 🛠 Technology Stack

### Backend
* **Language:** Python 3.x
* **Framework:** Flask (Micro-framework)
* **Authentication:** Session-based auth, Werkzeug Security (Password Hashing)
* **Email:** Python `smtplib` for OTPs (Threading included for performance)

### Database
* **RDBMS:** MySQL
* **Driver:** PyMySQL
* **Design:** Normalized Relational Schema

### Frontend
* **Languages:** HTML5, CSS3, JavaScript (ES6)
* **Templating:** Jinja2
* **Styling:** Custom CSS (EventPilot Theme) + Tailwind CSS (Vendor Dashboard)
* **Libraries:** Chart.js (Admin Analytics), FontAwesome (Icons)

---

## 🗄 Database Schema
The project uses a relational database structure designed for integrity and speed.

| Table Name | Description |
| :--- | :--- |
| `user_data` | Stores organizer details (Name, Email, Phone, Password). |
| `vendor_data` | Stores vendor business profiles, verification status, and pricing. |
| `bookings` | The core transaction table linking Users and Vendors with event details (Time, Budget, Requirements). |
| `admin_data` | Platform operators with specific roles (Superadmin/Moderator). |
| `otp_store` | Temporary storage for email verification OTPs with expiration logic. |
| `temp_registrations` | Temporary holding table for users during the verification flow to prevent ID gaps. |

---

## 🚀 Installation & Setup

### Prerequisites
* Python 3.8+ installed.
* MySQL Server installed and running.

1. Clone the Repository
```bash
git clone https://github.com/your-username/EventPilot.git
cd EventPilot 

2. Set up the Virtual Environment (Recommended)
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate

3. Install Dependencies
pip install flask pymysql
 
4.configuration
def connection():
    return pymysql.connect(
        host="localhost",
        user="root",        # Your MySQL Username
        password="YourPassword", # Your MySQL Password
        database="EventPilot",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

6. Create Super Admin
Run the python script or manually insert a hashed password into the admin_data table to access the admin panel.

7.Run the Application
python app.py

8.Usage Guide
Register: Start by verifying your email via OTP. Choose your role ("Plan an Event" or "Offer Services").
Organize: As a User, search for a service (e.g., Catering). Click "Request Quote," set your budget and date.
Manage: As a Vendor, log in to your dashboard to see the request. Accept it to finalize the deal.
Monitor: As an Admin, log in to oversee the platform analytics and manage staff.

9.🛡️ License
This project is for educational and portfolio purposes.
Developed by Jyotiranjan Nayak
