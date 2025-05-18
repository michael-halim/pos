# POS System with PyQt6

A modern Point of Sale (POS) system built with Python and PyQt6, featuring a comprehensive set of features for managing retail operations.

## About

This POS (Point of Sale) system is designed to streamline retail operations with a user-friendly interface and robust functionality. It helps businesses manage their inventory, sales, purchases, and customer relationships effectively. The system is built with modern technologies and follows best practices in software development.

## Features

### Core Features
- User authentication and role-based access control
- Product management with categories
- Inventory management
  - Stock tracking
  - Stock opname (inventory counting)
  - Stock card listing
- Customer management
- Supplier management
- Purchase management
- Transaction processing
- Reporting system
- Database backup and restore functionality
- Printer support
- Export capabilities

### Advanced Features
- Real-time inventory tracking
- Multi-user support with role-based permissions
- Comprehensive reporting and analytics
- Data export to Excel format
- Automated database backup system
- Customizable printer settings
- Stock movement history
- Purchase order management
- Customer purchase history
- Supplier transaction history

## How to Run

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)
- Git (for cloning the repository)

### Installation Steps
```bash

python main.py

```

### Building Executable
To create a standalone executable:
```bash

make build-install
```

## Technical Stack

- **Frontend**: PyQt6 (Qt6)
- **Database**: SQLite (based on the project structure)
- **Additional Libraries**:
  - openpyxl for Excel file handling
  - pyinstaller for application packaging

## Project Structure
