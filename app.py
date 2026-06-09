from flask import Flask
from config import SECRET_KEY
from database import create_tables
from routes.auth_routes import auth
from routes.teacher_routes import teacher
from routes.student_routes import student_bp

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['SESSION_PERMANENT'] = False

create_tables()

# Trigger background warmup of both camera and face engine at startup,
# so users don't wait for either when they click Start.
import services.face_engine      # noqa: F401 — loads InsightFace in background
import services.camera_warmup    # noqa: F401 — opens camera in background

from services.camera_warmup import camera_pool

app.register_blueprint(auth)
app.register_blueprint(teacher)
app.register_blueprint(student_bp)

import atexit
atexit.register(camera_pool.shutdown)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, threaded=True)
