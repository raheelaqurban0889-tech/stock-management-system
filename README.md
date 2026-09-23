# 📦 Stock Management System (Django)

A web-based Stock Management System built with Django and Bootstrap, designed for tracking inventory, managing sales invoices, handling returns, suppliers, customers, and managing role-based staff accounts.

---

## Features

1. **Authentication & Role-Based Access:**
   - Secure Login and Logout functionality.
   - **Admin (Superuser):** Full access to the system and Django Admin panel.
   - **Manager:** Can manage inventory, stock, sales, and create regular Staff accounts.
   - **Staff:** Restricted access based on assigned permissions.

2. **Inventory Management:**
   - Add new products, track stock levels, and monitor low-stock alerts.
   - Real-time stock movement tracking (IN/OUT logs).

3. **Search and Filter:** Real-time search by product name and category filtering in the inventory list.

4. **Sales & Invoicing:**
   - Create multi-item invoices with automatic tax and discount calculations.
   - Automatic deduction of stock upon sale.

5. **Returns Management:**
   - Process item returns and automatically update stock levels.

6. **Reports & Dashboards:**
   - Comprehensive dashboard showing total sales, product count, and low-stock warnings.
   - Filterable sales reports by date range.

---

##  Default Login Credentials

| Role | Username | Password |
| :--- | :--- | :--- |
| **Admin** | `admin` | `admin@2026` |
| **Manager** | `manager` | `manager@2026` |
| **Staff** | `staff1` | `staff@2026` |

---

## Installation & Setup Instructions

To run this project locally on your machine, follow these steps:

1. **Clone or Download the Project Folder.**
2. **Open Terminal / Command Prompt** in the project root directory.
3. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   ```
4. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
5. **Apply Database Migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. **Run the Development Server:**
   ```bash
   python manage.py runserver
   ```
7. **Open in Browser:**
   Go to `http://127.0.0.1:8000/` to access the application.
(You can also run it directly by double-clicking the start.bat file, or use this command):
python manage.py runserver
---

## 👥 User Roles & Account Creation Hierarchy

- **Admin (Superuser):** Can access the Django Admin panel (`/admin/`) and create **Manager** accounts through the web interface (`/create-staff/`).
- **Manager:** Can log into the system, manage stock/inventory, and create regular **Staff** accounts from the sidebar menu (`Create Staff`).
- **Staff:** Can perform day-to-day operations like sales/invoicing without access to administrative creation routes.
