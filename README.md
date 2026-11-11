# RFID Dance Class Attendance System

> Specifically created for IZTECH World Dance Society. A Windows desktop application for tracking student attendance in dance classes using USB HID RFID card readers. Built with Python, CustomTkinter, and SQLite3.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![Platform: Windows](https://img.shields.io/badge/Platform-Windows-blue?logo=windows)](https://github.com/AdemFurkanATA/Attendance_System/releases/)

---

## Current Status

The application includes the latest attendance, reporting, Google Sheets, database-migration, and Windows release automation changes. Releases are created automatically when a tag beginning with `v` is pushed (for example, `v1.0.0`); the **Build & Release EXE** workflow can also be run manually to create a downloadable build artifact.

### Recent additions

- **Attendance on any date** — administrators can set or toggle a student's Present/Absent status for a selected date; it is not limited to a section's scheduled weekday.
- **Section student attendance view** — select a date from a section and change each student's status with one click.
- **Two-week grace period** — absences recorded during a section's first two weeks are shown separately and do not contribute to inactive-student calculations.
- **Google Sheets daily grid** — a summary push includes daily attendance data and per-section present/enrolled counts for every date.
- **PDF reports** — generate daily or full-section reports as PDF files from the Reports tab.
- **Safe database upgrade** — the startup migration removes historical duplicate sessions while preserving attendance.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Developer Setup](#developer-setup)
- [Running the App](#running-the-app)
- [Building the Executable](#building-the-executable)
- [For End-Users (Download & Run .exe)](#for-end-users-download--run-exe)
- [Project Structure](#project-structure)
- [Data, Backups & Logs](#data-backups--logs)
- [Configuration & Secrets](#configuration--secrets)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Attendance and administration

- Passive RFID attendance with automatic daily session creation and duplicate-tap protection.
- One card tap marks a student present in every enrolled section scheduled for that weekday.
- First-time cards launch registration; known students without sections can be assigned immediately and marked present.
- The PIN-protected `Ctrl+P` administration panel contains **Sections**, **Students**, **Reports**, and **Settings** tabs.
- Section Student views provide a date picker and one-click Present/Absent editing; manual attendance is allowed on any date.
- Student management includes search, sorting, pagination, attendance history, section assignments, and RFID card reassignment.

### Reporting, integrations, and resilience

- Daily and full-section PDF reports.
- Google Sheets roster import and attendance-summary export, including a daily grid and per-section present/enrolled counts.
- Configurable inactive-student detection; a section's first two weeks are excluded from absence counting.
- English/Turkish localization, automated four-hour backups, manual restore, and rotating application logs.

- **Passive RFID listening** — always-focused entry widget captures card taps instantly
- **Auto-session creation** — daily attendance sessions are created per section automatically
- **Multi-section enrollment** — one tap marks a student present in all their sections scheduled for that weekday
- **Unknown card registration** — a registration dialog opens on first tap; student is enrolled and immediately marked present
- **Zero-section handling** — known students with no sections get a section assignment dialog on tap
- **Inactive student tracking** — students exceeding the configurable consecutive-absence threshold are auto-flagged; a section's first two weeks are excluded from the calculation
- **Admin panel** (Ctrl+P, PIN-protected) with four tabs:
  - **Sections** — add/edit/delete class sections with day and time
  - **Students** — search, sort, view attendance history, edit details, and reassign RFID cards
  - **Reports** — generate daily and full-section PDF reports
  - **Settings** — change PIN, language, attendance threshold, inactive threshold, section mode, Google Sheets credentials, backup/restore, import, summary push, and daily reports
- **Google Sheets integration** — import student rosters and push per-student summaries plus daily attendance and per-section counts
- **Auto-backup** — database is backed up every 4 hours automatically; manual backup and restore available
- **Localization support** — English and Turkish, switchable live from Settings
- **Daily attendance report** — per-section breakdown with summary statistics
- **Secure PIN** — PBKDF2-HMAC-SHA256 with salt; backward-compatible with legacy hashes
- **RFID simulation panel** — development tool for testing without hardware (marked #DELETABLE)

---

## Requirements

- Windows 10 or 11 (64-bit)
- Python **3.10+**
- An RFID USB card reader (keyboard-emulation / HID mode)

---

## Developer Setup

### 1. Clone the repository

```bash
git clone https://github.com/Adrimars/Attendance_System.git
cd Attendance_System
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Google Sheets credentials (optional)

If you want Google Sheets export/import functionality:

1. Create a **Google Cloud project** and enable the **Google Sheets API** and **Google Drive API**.
2. Create a **Service Account**, download the JSON key file.
3. **Do not commit this file** — it is already excluded by `.gitignore`.
4. In the app's Settings tab, browse to your credentials `.json` file.

---

## Running the App

From the project root:

```bash
python src/main.py
```

- The app launches in a 1280×800 windowed mode (resizable, minimum 900×600).
- Press **Ctrl+P** to open the admin panel. On first use, the application asks you to create an administrator PIN; subsequent access requires that PIN.

---

## Building the Executable

The repository's release workflow builds a single-file executable named `AttendanceSystem.exe`. To reproduce the release build locally:

```bash
pyinstaller --noconfirm --onefile --noconsole --name AttendanceSystem --paths src --collect-all customtkinter --collect-all tkcalendar --hidden-import babel.numbers --collect-data babel src/main.py
```

Output: `dist\AttendanceSystem.exe`.

### Automated GitHub release

Pushing a tag whose name starts with `v` triggers `.github/workflows/release.yml`: it builds the Windows executable, creates a GitHub Release, attaches the `.exe`, and uploads it as a workflow artifact.

```bash
git tag v1.0.0
git push origin v1.0.0
```

The same workflow supports `workflow_dispatch` for a manual build. A manually dispatched run uploads an artifact but does not create a release because no tag is present.

### Legacy spec build

A pre-configured `attendance.spec` is included. Run from the project root with the virtual environment active:

```bash
pyinstaller attendance.spec
```

Output: `dist\AttendanceSystem\AttendanceSystem.exe`

### Alternative — one-file build (slower startup, no external files)

```bash
pyinstaller --onefile --noconsole --name AttendanceSystem src/main.py
```

> **Note:** The `build/` and `dist/` folders are git-ignored. The executable is distributed separately via [Attendance_System_App](https://github.com/Adrimars/Attendance_System_App).

---

## For End-Users (Download & Run .exe)

> You do **not** need Python installed.

1. Go to this repository's [Releases page](https://github.com/AdemFurkanATA/Attendance_System/releases/).
2. Download `AttendanceSystem.exe` from the newest release. If a tagged release has not yet been published, run **Build & Release EXE** manually and download its artifact from GitHub Actions.
3. Double-click `AttendanceSystem.exe` — no installation required.
4. On first launch, open the Settings panel (`Ctrl+P`), create the administrator PIN, and configure your preferences.

---

## Data, Backups & Logs

The application stores its persistent SQLite database as `attendance.db`. In a development checkout it is created at the project root; in a packaged build it is created beside the executable, so it survives application updates.

- Automatic backups run at startup and then every four hours. The `backups/` directory retains the ten most recent database snapshots.
- Manual backup and restore controls are available in **Settings**.
- Application events and unhandled errors are written to rotating log files under `logs/`.
- Database, backup, log, and Google service-account credential files are excluded from version control.

## Project Structure

```
Attendance_System/
├── src/
│   ├── main.py                    # Entry point
│   ├── controllers/               # Business logic layer
│   │   ├── attendance_controller.py
│   │   ├── import_controller.py
│   │   ├── section_controller.py
│   │   ├── session_controller.py
│   │   └── student_controller.py
│   ├── models/                    # Database access layer (SQLite3)
│   │   ├── database.py
│   │   ├── attendance_model.py
│   │   ├── section_model.py
│   │   ├── session_model.py
│   │   ├── settings_model.py
│   │   └── student_model.py
│   ├── utils/                     # Shared utilities
│   │   ├── backup.py              # Auto-backup & restore
│   │   ├── localization.py        # English/Turkish i18n
│   │   ├── logger.py              # File logging
│   │   └── pin_utils.py           # PBKDF2 PIN hashing
│   └── views/                     # UI layer (CustomTkinter)
│       ├── app.py
│       ├── attendance_tab.py
│       ├── admin_panel.py
│       ├── sections_tab.py
│       ├── students_tab.py
│       ├── settings_tab.py
│       ├── components/
│       └── dialogs/
├── specs/                         # Project specification documents
├── attendance.spec                # PyInstaller build config
├── requirements.txt
├── requirements-dev.txt
├── LICENSE
└── README.md
```


## Configuration & Secrets

Google Sheets features require a Google Cloud service account with the Google Sheets and Google Drive APIs enabled. Select its JSON key file from **Settings**, then share the target spreadsheet with the service account email address. Keep the JSON key private; it is intentionally ignored by Git.

The administrator PIN is stored as a salted PBKDF2-HMAC-SHA256 hash, never as plaintext. Existing legacy PIN hashes are accepted and upgraded transparently after a successful change.

## Contributing

Install development dependencies and run the test suite before submitting changes:

```bash
pip install -r requirements-dev.txt
python -m pytest
```

Keep the MVC boundary intact: views should call controllers rather than query models directly. Do not commit generated databases, backups, logs, executable builds, or service-account credentials.

## License

This project is licensed under the [MIT License](LICENSE) — © 2026 Adrimars.
