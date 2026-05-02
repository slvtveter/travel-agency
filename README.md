# Travel Agency Management System

A Flask administrative interface for managing travel agency operations.

## Features
- Real-time Admin Dashboard
- Customer, Tour, and Guide Management
- Fleet and Transport Tracking
- Reservation and Payment Systems

## Setup
1. **Environment**:
   ```bash
   conda env create -f environment.yml
   conda activate ./env
   ```
2. **Database**: Create a MySQL database named `travel_agency` and run `mysql_schema.sql`.
3. **Secrets**: Create a `.env` file with your `DB_HOST`, `DB_USER`, `DB_PASSWORD`, and `DB_NAME`.
4. **Run**: `python app.py`
