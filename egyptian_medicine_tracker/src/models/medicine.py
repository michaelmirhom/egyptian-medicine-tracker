from src.models.user import db
from datetime import datetime

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trade_name = db.Column(db.String(200), nullable=False)
    generic_name = db.Column(db.String(200), nullable=True)
    reg_no = db.Column(db.String(100), nullable=True)
    applicant = db.Column(db.String(200), nullable=True)
    price = db.Column(db.Float, nullable=True)
    currency = db.Column(db.String(10), default='EGP')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(100), nullable=True)
    
    # API integration fields
    api_id = db.Column(db.String(200), nullable=True)  # Medicine ID from external API
    api_image = db.Column(db.String(500), nullable=True)  # Medicine image URL
    api_description = db.Column(db.Text, nullable=True)  # Medicine description
    api_components = db.Column(db.Text, nullable=True)  # Medicine components (JSON string)
    api_company = db.Column(db.String(200), nullable=True)  # Manufacturing company
    
    def to_dict(self):
        return {
            'id': self.id,
            'trade_name': self.trade_name,
            'generic_name': self.generic_name,
            'reg_no': self.reg_no,
            'applicant': self.applicant,
            'price': self.price,
            'currency': self.currency,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'source': self.source,
            'api_id': self.api_id,
            'api_image': self.api_image,
            'api_description': self.api_description,
            'api_components': self.api_components,
            'api_company': self.api_company
        }

