# Travel Agency Management System

A Flask administrative interface for managing travel agency operations. The web
application is deployed on Render and connects to a MySQL database hosted on
Railway.

## Features
- Real-time Admin Dashboard
- Customer, Tour, and Guide Management
- Fleet and Transport Tracking
- Reservation and Payment Systems

## Local Setup
1. Create and activate the local environment:
   ```bash
   conda env create -f environment.yml
   conda activate ./env
   ```
2. Create a `.env` file with the Railway MySQL connection settings:
   ```bash
   DB_HOST=your-railway-host
   DB_PORT=your-railway-port
   DB_USER=your-railway-user
   DB_PASSWORD=your-railway-password
   DB_NAME=your-railway-database
   ```
3. Run the app:
   ```bash
   python app.py
   ```

## Deployment
The production database is managed in Railway. Render runs the Flask app and
connects to Railway through environment variables configured in the Render
dashboard.

Required Render environment variables:
- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`

Local SQL dump and seed files are not required by the deployed application.
They are only snapshots/mock data for development or database restoration.
