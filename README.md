# Travel Agency Management System

A Flask-based administrative interface for managing a travel agency's operations, built directly from a relational ER diagram.

## 🚀 Features
- **Mission Control Dashboard**: Real-time stats and analytics.
- **Full CRM**: Complete Customer management (CRUD).
- **Inventory**: Manage Package Tours and available destinations.
- **Workforce**: Track Guides, their languages, and ratings.
- **Fleet Management**: Manage transport vehicles and drivers.
- **Transactional**: Complete Reservation system with relational links.
- **Financials**: Track payments and revenue linked to bookings.

## 🛠 Tech Stack
- **Backend**: Python / Flask
- **Database**: MySQL
- **Frontend**: Bootstrap 5 (CSS) / Jinja2 (Templating)
- **Security**: Environment variables via `.env`

## ⚙️ Setup Instructions
1. **Clone the Repo**
2. **Recreate the Environment**:
   ```bash
   conda env create -f environment.yml
   conda activate ./env
   ```
3. **Database Setup**:
   - Create a MySQL database named `travel_agency`.
   - Run the provided `mysql_schema.sql` to generate tables.
4. **Configuration**:
   - Create a `.env` file in the root directory.
   - Add your credentials:
     ```text
     DB_HOST=localhost
     DB_USER=root
     DB_PASSWORD=your_password
     DB_NAME=travel_agency
     ```
5. **Run the App**:
   ```bash
   python app.py
   ```

## 📝 Note for MySQL Specialist
The UI and Backend logic are complete. The following **Business Logic** is expected to be handled via **MySQL Triggers**:
- **Auto-Update Guide Status**: Change `availability_status` to 'On Tour' when assigned to a new reservation.
- **Price Calculation**: Automatically calculate `total_price` in the `reservations` table (Number of People * Tour Base Price).
- **Data Integrity**: Ensure bookings don't exceed tour `max_capacity`.
