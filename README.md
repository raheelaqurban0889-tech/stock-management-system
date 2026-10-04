# 🏢 Web-Based Stock, Inventory & Sales Management System

![Python](https://img.shields.io/badge/Python-3.14-blue)
![Django](https://img.shields.io/badge/Django-6.1-green)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

A comprehensive web-based ERP solution for Small and Medium-sized Enterprises (SMEs) to manage inventory, track stock levels, process sales, and generate business reports in real-time.

---

## 📋 Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Screenshots](#screenshots)
- [Technology Stack](#technology-stack)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [User Roles](#user-roles)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Contributors](#contributors)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## 📖 About the Project

The **Web-Based Stock, Inventory & Sales Management System** is a comprehensive business management application designed to automate and simplify the daily operations of small and medium-sized enterprises (SMEs). 

The system provides a centralized platform for managing:
- 📦 Inventory and stock levels
- 💰 Sales transactions and invoices
- 👥 Customer and supplier records
- 🔄 Product returns
- 📊 Business reports and analytics

### 🎯 Purpose

Replace manual record-keeping methods with an efficient computerized solution that:
- ✅ Improves accuracy and reduces human errors
- ✅ Saves time and increases operational efficiency
- ✅ Provides real-time visibility into business operations
- ✅ Enables data-driven decision making

### 🎓 Academic Context

This project was developed as part of the **BS Computer Sciences** degree requirement at **Virtual University of Pakistan** under the supervision of **Abdur Rafay**.

---

## ✨ Features

### 1. 👤 User Management
- Secure login/logout system
- Role-based access control (Admin, Manager, Salesman)
- Account creation with hierarchical permissions
- Activity logging and audit trail
- Password show/hide toggle

### 2. 📦 Inventory Management
- Add, update, delete products
- Category management
- Real-time stock tracking
- Product image upload
- Auto-generated SKU and barcode
- Low stock threshold configuration

### 3. 🚚 Stock Management
- Purchase entries from suppliers
- Automatic stock updates
- Stock movement history
- Low stock alerts and notifications
- Before/after quantity tracking

### 4. 💰 Sales Management
- Multi-item invoice creation
- Automatic stock deduction
- Tax and discount calculation
- Multiple payment methods
- Invoice PDF generation
- Print/download functionality

### 5. 🔄 Return Management
- Customer return processing
- Condition-based stock restoration
- Refund calculation
- Complete return history

### 6. 👥 Customer & Supplier Management
- Company-based records (LLC/Pvt Ltd)
- Contact person (optional)
- Country code phone format (+92, +971, etc.)
- Transaction history
- Email integration

### 7. 📊 Reports & Analytics
- Daily, monthly, yearly sales reports
- Inventory reports
- Profit/loss analysis
- Top selling products
- Top customers
- Interactive charts (Bar, Line, Pie)

### 8. 📈 Dashboard
- Real-time KPI cards
- Monthly sales chart
- Recent transactions
- Low stock alerts
- Quick action buttons

### 9. 🔍 Search & Filter
- Global search across modules
- Product search by name/SKU
- Sales filtering by date/customer
- Quick invoice lookup

### 10. 🔒 System & Security
- Data backup (JSON export)
- Activity logs
- Secure authentication (PBKDF2)
- CSRF protection
- SQL injection prevention
- Responsive design

### 11. 🎫 Barcode & QR Code
- Auto-generation of barcodes (Code128)
- QR code generation with product data
- Printable barcode labels
- Camera-based barcode scanning

---

## 📸 Screenshots

### Login Page
![Login](static/images/screenshots/login.png)

### Dashboard
![Dashboard](static/images/screenshots/dashboard.png)

### Inventory Management
![Inventory](static/images/screenshots/inventory.png)

### Create Invoice
![Invoice](static/images/screenshots/invoice.png)

### Reports & Analytics
![Reports](static/images/screenshots/reports.png)

> **Note:** Add your own screenshots to `static/images/screenshots/` folder.

---

## 🛠️ Technology Stack

| Category | Technology |
|----------|------------|
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5, Chart.js |
| **Backend** | Python 3.14, Django 6.1 |
| **Database** | SQLite (Development), MySQL (Production) |
| **Python Libraries** | Pillow, python-barcode, qrcode, ReportLab |
| **IDE** | Visual Studio Code |
| **Version Control** | Git, GitHub |
| **UI/UX Design** | Figma |
| **API Testing** | Postman |
| **Web Server** | Django Dev Server (Dev), Apache/Nginx (Prod) |

---

## 🚀 Installation

### Prerequisites

- Python 3.10+ (3.14 recommended)
- pip (Python package installer)
- Git
- Modern web browser (Chrome, Firefox, Edge)

### Step 1: Clone the Repository

```bash
git clone https://github.com/raheelaqurban0889-tech/stock-management-system.git
cd stock-management-system