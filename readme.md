# Car Booking System

This project is a web-based car booking system built using Flask. It allows users to book seats in a car and provides an admin panel for managing bookings.

## Features

- **User Booking**: Users can book available seats in a car.
- **Admin Panel**: Admins can approve or reject bookings.
- **Email Notifications**: Users receive email notifications when their bookings are approved or rejected.
- **Weekly Database Cleanup**: The database is cleared of all bookings except for a specific seat every Sunday at midnight.

## Usage

### User Booking

Users can navigate to the home page, enter their name and email address, and select up to two seats to book. Once the booking is submitted, users will receive an email notification when their booking is approved or rejected.

### Admin Panel

Admins can log in to the admin panel using a password. From the admin panel, they can approve or reject bookings. Approved bookings will send an email notification to the user.

### Weekly Database Cleanup

The database is automatically cleared of all bookings except for a specific seat every Sunday at midnight.

## File Structure

- `main.py`: Main application file containing the Flask app and routes.
- `templates/`: HTML templates for the web pages.
- `static/css/`: CSS files for styling the web pages.
- `requirements.txt`: List of dependencies.
- `.env`: Environment variables (not included in the repository).
- `.gitignore`: Files and directories to be ignored by Git.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Flask: [https://flask.palletsprojects.com/](https://flask.palletsprojects.com/)
- APScheduler: [https://apscheduler.readthedocs.io/](https://apscheduler.readthedocs.io/)
- SQLiteCloud: [https://sqlitecloud.io/](https://sqlitecloud.io/)
