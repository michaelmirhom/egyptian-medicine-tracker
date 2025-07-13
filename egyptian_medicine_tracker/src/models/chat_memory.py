from src.models.user import db
from datetime import datetime

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(64), index=True, nullable=False)
    role = db.Column(db.String(8), nullable=False)  # 'user' or 'bot'
    text = db.Column(db.Text, nullable=False)
    # Store list of variant product dicts when bot provides multiple choices
    variants = db.Column(db.JSON, nullable=True)
    # Store the selected variant as dict
    selected_variant = db.Column(db.JSON, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
            "variants": self.variants,
            "selected_variant": self.selected_variant,
        } 