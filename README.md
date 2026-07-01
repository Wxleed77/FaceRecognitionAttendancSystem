# 🎓 AI Face Recognition Attendance System

A modern, intelligent attendance tracking system using **AI-powered face recognition** built with Flask and InsightFace. Automatically marks student attendance with real-time camera processing.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.0+-green?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)

## ✨ Key Features

| Feature | Benefit |
|---------|---------|
| **Lightning-fast Recognition** | Uses InsightFace (dlib-based), not heavy TensorFlow models |
| **Minimal Training Data** | Only **7 photos per student** needed (vs. 30+ in old systems) |
| **Zero Freezing UI** | Multi-threaded camera processing — always responsive |
| **Smart Database** | Pre-loaded embeddings for instant recognition |
| **Role-Based Access** | Separate dashboards for Students & Teachers |
| **Real-Time Processing** | Processes every 4th frame for optimal speed/accuracy |


## 📋 Requirements

- **Python 3.8+**
- **Windows/Linux/Mac**
- **Webcam** (for face capture and recognition)

## 🚀 Installation

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/AI-Attendance-System.git
cd AI-Attendance-System
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

> **Note:** On Windows, if `face_recognition` fails to install:
> ```bash
> pip install cmake
> pip install dlib
> pip install face_recognition
> ```

### Step 4: Initialize Database
```bash
python app.py
```
This will automatically create the SQLite database and tables.

## 📖 Usage

### Option 1: Register Students (First Time)
```bash
python register.py
```

**Steps:**
1. Enter **Student Name** (e.g., "John Doe")
2. Enter **Roll Number** (e.g., "A001")
3. Select **Department** (from dropdown)
4. Camera opens → **Press SPACE 7 times** to capture diverse angles
5. Press **ESC** to finish
6. Embedding is automatically saved to database ✅

### Option 2: Start Attendance System
```bash
python app.py
```

Open your browser and go to:
```
http://127.0.0.1:5000
```

**Features:**
- **Teacher Dashboard**: View attendance records, export reports
- **Student Dashboard**: Check your attendance status
- **Real-Time Recognition**: Automatic face detection and attendance marking

## ⚙️ Configuration

Edit `config.py` to customize:

```python
# Recognition threshold (0.35-0.45 range)
MATCH_THRESHOLD = 0.40        # 0.35=strict, 0.40=balanced, 0.45=lenient

# Confidence margin (prevent misidentification)
CONFIDENCE_MARGIN = 0.08       # Best match must beat 2nd by this margin

# Registration photos
REGISTER_PHOTO_COUNT = 7       # Photos per student during registration

# Camera settings
RECOGNITION_INTERVAL = 4       # Process every 4th frame (speed optimization)
CAMERA_INDEX = 0               # Change if you have multiple cameras

# Flask settings
SECRET_KEY = "attendai-secret-change-in-prod"  # Change in production!
```

## 🗂️ Project Structure

```
AI-Attendance-System/
├── app.py                      # Main Flask application
├── config.py                   # Configuration settings
├── database.py                 # Database initialization & queries
├── register.py                 # Student registration script
├── requirements.txt            # Python dependencies
│
├── routes/                     # Flask blueprints
│   ├── auth_routes.py          # Login/signup
│   ├── student_routes.py       # Student endpoints
│   └── teacher_routes.py       # Teacher endpoints
│
├── services/                   # Core functionality
│   ├── face_engine.py          # InsightFace wrapper
│   ├── camera_service.py       # Camera handling
│   ├── recognition_service.py  # Face recognition logic
│   ├── attendance_service.py   # Attendance marking
│   └── auth.py                 # Authentication
│
├── models/                     # Data models
│   └── student_model.py        # Student schema
│
├── templates/                  # HTML templates
│   ├── index.html              # Home page
│   ├── login.html              # Login page
│   ├── register_student.html   # Student registration form
│   └── dashboards/             # User dashboards
│
└── static/                     # CSS, JS, images
    ├── css/
    └── js/
```


## 🎯 API Endpoints

### Authentication
- `POST /register` — Register new user
- `POST /login` — User login
- `GET /logout` — User logout

### Teacher Routes
- `GET /teacher/dashboard` — View all attendance
- `GET /teacher/export` — Export attendance report

### Student Routes
- `GET /student/dashboard` — View personal attendance
- `POST /student/mark-attendance` — Mark attendance (camera)

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Camera not detected** | Change `CAMERA_INDEX` in `config.py` |
| **Face not recognized** | Adjust `MATCH_THRESHOLD` (lower = stricter) |
| **Slow performance** | Increase `RECOGNITION_INTERVAL` (e.g., 6 or 8) |
| **ModuleNotFoundError** | Run `pip install -r requirements.txt` in activated venv |

## 🚀 Deployment (Production)

### Before deploying:
1. Change `SECRET_KEY` in `config.py` to a random string
2. Set `debug=False` in `app.py`
3. Use a production WSGI server (Gunicorn, uWSGI)
4. Use environment variables for sensitive config

Example with Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## 📊 Tech Stack

- **Backend**: Flask (Python web framework)
- **Face Recognition**: InsightFace + ArcFace embeddings
- **Database**: SQLite3
- **Frontend**: HTML5, Bootstrap, JavaScript
- **Camera**: OpenCV
- **Math**: NumPy, SciPy (for embeddings)

## 📝 License

This project is licensed under the **MIT License** — see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/YourFeature`)
3. Commit changes (`git commit -m 'Add YourFeature'`)
4. Push to branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

## 👨‍💻 Author

**Developed with ❤️**

## ⭐ Support

If you find this project useful, please give it a ⭐ on GitHub!

---

**Questions?** Open an [Issue](https://github.com/yourusername/AI-Attendance-System/issues) on GitHub.

### Step 3 — Start attendance
Click **▶ START ATTENDANCE** in the dashboard,  
or go to: http://127.0.0.1:5000/api/start-attendance

Camera opens. Recognized faces are marked automatically.  
Press **Q** to stop.

---

## API Endpoints

| Route | Description |
|---|---|
| `GET /` | Dashboard |
| `GET /api/start-attendance` | Start camera recognition |
| `GET /api/attendance/today` | Today's records (JSON) |
| `GET /api/attendance/all` | All records (JSON) |
| `GET /api/students` | Registered students (JSON) |

---

## Tuning

Edit `config.py`:

```python
MATCH_TOLERANCE    = 0.4   # lower = stricter. Try 0.45 if too many "Unknown"
REGISTER_PHOTO_COUNT = 3   # increase to 5 for better accuracy
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `dlib` install fails | `pip install cmake` first, then retry |
| Camera not found | Change `CAMERA_INDEX = 1` in config.py |
| Too many "Unknown" | Increase `MATCH_TOLERANCE` to 0.45–0.5 |
| Too many false matches | Decrease `MATCH_TOLERANCE` to 0.35 |
| Slow recognition | Normal on CPU; recognition runs in background so camera stays smooth |
