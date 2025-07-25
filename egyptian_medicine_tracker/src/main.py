import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)))

from flask import Flask, send_from_directory
from src.models.user import db
from src.models.medicine import Medicine
from src.models.chat_memory import ChatMessage
from src.models.dailymed import DailyMedLabel
from src.routes.user import user_bp
from src.routes.medicine import medicine_bp
from src.routes.label import label_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(medicine_bp, url_prefix='/api')
app.register_blueprint(label_bp, url_prefix='/api')

# Database configuration - use persistent file-based database
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
