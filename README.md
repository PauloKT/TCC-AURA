# AURA — Automated University Roll-call and Attendance

> Web system for academic attendance control using dynamic QR Code, GPS geolocation and WebAuthn biometric authentication. Built with Django and Django REST Framework.

---

## About the Project

AURA is an academic web system developed as a final undergraduate project (TCC) to automate classroom attendance control in higher education institutions. The system combines three security layers to prevent fraud and ensure that only physically present students can register their attendance.

**Security layers:**
- **Dynamic QR Code** — unique token generated per class, expires in 60 seconds
- **GPS Geolocation** — validates that the student is within a 50-meter radius of the classroom
- **WebAuthn** — biometric authentication (Face ID / fingerprint) performed locally on the device, no biometric data is sent to or stored on the server

---

## Features

### Professor
- Register and manage subjects and classes
- Define minimum attendance percentage per subject
- Start and end class sessions
- Display dynamic QR Code for students to scan
- View real-time attendance list
- Monitor student attendance risk alerts
- Access frequency reports

### Student
- Self-registration on the platform
- Join classes via professor-generated invite link
- Register attendance by scanning the QR Code
- Track personal attendance and status per subject

---

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11+ |
| Framework | Django + Django REST Framework |
| Database | SQLite (development) |
| Frontend | HTML, CSS, JavaScript, Bootstrap 5 |
| QR Code generation | `qrcode` (Python library) |
| Geolocation | Geolocation API (browser-native) |
| Biometric auth | WebAuthn via `py_webauthn` |
| Version control | Git + GitHub |

---

## Project Structure

```
aura/
├── core/               # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── users/              # User management (professor & student profiles)
├── subjects/           # Subjects and classes
├── attendance/         # Sessions and attendance records
├── qrcodes/            # QR Code generation and token validation
├── reports/            # Frequency reports and risk alerts
├── manage.py
└── requirements.txt
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/aura.git
cd aura

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Apply migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Run the development server
python manage.py runserver
```

Access the system at `http://127.0.0.1:8000`

---

## Attendance Flow

```
Professor starts session
        ↓
System generates dynamic QR Code (unique token, expires in 60s)
        ↓
Professor displays QR Code on projector
        ↓
Student scans QR Code
        ↓
GPS validated (within 50m radius)
        ↓
Biometric confirmed (WebAuthn — Face ID / fingerprint)
        ↓
Attendance registered ✓
        ↓
Professor's list updated in real time
```

---

## Privacy & LGPD Compliance

AURA was designed with student privacy in mind. The WebAuthn protocol ensures that biometric data (fingerprint, Face ID) **never leaves the student's device** and is **never transmitted to or stored on the server**. Only a cryptographic signature is used to confirm identity, in full compliance with Brazil's General Data Protection Law (LGPD).

---

## Authors

Developed as a final undergraduate project (TCC).

- **Paulo Amaral** — [GitHub](https://github.com/PauloKT)
- **Heitor Cortes** — [GitHub](https://github.com/heitorpcrl)

---

## License

This project is for academic purposes.
