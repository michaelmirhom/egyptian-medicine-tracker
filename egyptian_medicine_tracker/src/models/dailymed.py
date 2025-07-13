from src.models.user import db

class DailyMedLabel(db.Model):
    __tablename__ = "dailymed_label"
    __table_args__ = {'extend_existing': True}
    id           = db.Column(db.Integer, primary_key=True)
    setid        = db.Column(db.String(36), unique=True)
    brand        = db.Column(db.String(250))
    generic      = db.Column(db.String(200), index=True)
    indications  = db.Column(db.Text)
    contraind    = db.Column(db.Text)
    ingredients  = db.Column(db.Text)

    def to_dict(self):
        return {k: getattr(self, k) for k in
                ("brand","generic","indications","contraind","ingredients")} 