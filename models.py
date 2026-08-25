from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    college = db.Column(db.String(200))
    department = db.Column(db.String(120))
    year = db.Column(db.String(20))
    bio = db.Column(db.Text, default="")
    skill_coins = db.Column(db.Integer, default=100)
    rating = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_skills = db.relationship(
        "UserSkill", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    @property
    def teach_skills(self):
        return [us for us in self.user_skills if us.type == "TEACH"]

    @property
    def learn_skills(self):
        return [us for us in self.user_skills if us.type == "LEARN"]

    @property
    def avatar_letter(self):
        return self.name[0].upper() if self.name else "?"

    @property
    def display_rating(self):
        return round(self.rating, 1) if self.rating_count > 0 else 0.0


class Skill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(60), nullable=False)


class UserSkill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # TEACH / LEARN
    level = db.Column(db.String(20), default="Beginner")

    skill = db.relationship("Skill")


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skill.id"), nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    scheduled_at = db.Column(db.DateTime, nullable=False)
    cost = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="REQUESTED")  # REQUESTED/ACCEPTED/COMPLETED/CANCELLED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    meeting_link = db.Column(db.String(500))

    teacher = db.relationship("User", foreign_keys=[teacher_id])
    student = db.relationship("User", foreign_keys=[student_id])
    skill = db.relationship("Skill")
    messages = db.relationship(
        "Message", backref="session", lazy=True,
        cascade="all, delete-orphan", order_by="Message.created_at",
    )

    @property
    def already_reviewed(self):
        return Review.query.filter_by(session_id=self.id).first() is not None

    def other_party(self, user_id):
        return self.student if user_id == self.teacher_id else self.teacher


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User")


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # EARN / SPEND / BONUS
    description = db.Column(db.String(200))
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    icon = db.Column(db.String(30), default="bi-bell")
    link = db.Column(db.String(300))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    @property
    def time_ago(self):
        delta = datetime.utcnow() - self.created_at
        secs = delta.total_seconds()
        if secs < 60:
            return "just now"
        if secs < 3600:
            return f"{int(secs // 60)}m ago"
        if secs < 86400:
            return f"{int(secs // 3600)}h ago"
        return f"{int(secs // 86400)}d ago"
