from datetime import datetime
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from config import Config
from models import db, User, Skill, UserSkill, Session as SessionModel, Transaction, Review, Message, Notification
from matching import compute_matches
from seed import seed_database

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

DURATION_COST = {30: 25, 60: 50}


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    return User.query.get(uid)


def notify(user_id, message, link=None, icon="bi-bell"):
    """Create an in-app notification for a user. Caller does not need to commit."""
    db.session.add(Notification(user_id=user_id, message=message, link=link, icon=icon))


@app.context_processor
def inject_user():
    user = current_user()
    unread_count = 0
    recent_notifications = []
    if user:
        unread_count = Notification.query.filter_by(user_id=user.id, is_read=False).count()
        recent_notifications = (
            Notification.query.filter_by(user_id=user.id)
            .order_by(Notification.created_at.desc())
            .limit(8)
            .all()
        )
    return {
        "current_user": user,
        "unread_count": unread_count,
        "recent_notifications": recent_notifications,
    }


@app.errorhandler(404)
def not_found(e):
    return render_template("error.html", message="That page doesn't exist."), 404


@app.errorhandler(500)
def server_error(e):
    db.session.rollback()
    return render_template("error.html", message="Something went wrong on our end."), 500

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/seed-demo")
def seed_demo():
    seed_database()
    session.clear()
    flash("Demo data has been reset. Try logging in as rahul@skillswap.dev / password123", "success")
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        college = request.form.get("college", "").strip()
        department = request.form.get("department", "").strip()
        year = request.form.get("year", "").strip()

        if not name or not email or not password:
            flash("Name, email and password are required.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "danger")
            return render_template("register.html")

        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            college=college,
            department=department,
            year=year,
            skill_coins=100,
        )
        db.session.add(user)
        db.session.flush()
        db.session.add(
            Transaction(user_id=user.id, amount=100, type="BONUS", description="Welcome bonus")
        )
        db.session.commit()

        session["user_id"] = user.id
        flash("Welcome to SkillSwap! You've received 100 SkillCoins to get started.", "success")
        return redirect(url_for("edit_skills"))

    return render_template("register.html")


DEMO_ACCOUNTS = ["rahul@skillswap.dev", "kabir@skillswap.dev"]


@app.route("/demo-login/<email>")
def demo_login(email):
    email = email.strip().lower()
    if email not in DEMO_ACCOUNTS:
        flash("Unknown demo account.", "danger")
        return redirect(url_for("login"))
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Demo data isn't seeded yet — click 'reset demo data' first.", "warning")
        return redirect(url_for("login"))
    session["user_id"] = user.id
    flash(f"Logged in as {user.name} (demo).", "success")
    return redirect(url_for("dashboard"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password_hash, password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        session["user_id"] = user.id
        flash(f"Welcome back, {user.name.split(' ')[0]}!", "success")
        return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You've been logged out.", "info")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    candidates = User.query.filter(User.id != user.id).all()
    matches = compute_matches(user, candidates)[:3]

    upcoming = (
        SessionModel.query.filter(
            ((SessionModel.teacher_id == user.id) | (SessionModel.student_id == user.id)),
            SessionModel.status.in_(["REQUESTED", "ACCEPTED"]),
        )
        .order_by(SessionModel.scheduled_at.asc())
        .limit(5)
        .all()
    )
    completed = (
        SessionModel.query.filter(
            ((SessionModel.teacher_id == user.id) | (SessionModel.student_id == user.id)),
            SessionModel.status == "COMPLETED",
        )
        .count()
    )
    recent_tx = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "dashboard.html",
        user=user,
        matches=matches,
        upcoming=upcoming,
        completed_count=completed,
        recent_tx=recent_tx,
    )


@app.route("/matches")
@login_required
def matches_page():
    user = current_user()
    candidates = User.query.filter(User.id != user.id).all()
    matches = compute_matches(user, candidates)
    return render_template("matches.html", user=user, matches=matches)

@app.route("/profile/<int:user_id>")
@login_required
def profile(user_id):
    user = User.query.get_or_404(user_id)
    completed = (
        SessionModel.query.filter(
            ((SessionModel.teacher_id == user.id) | (SessionModel.student_id == user.id)),
            SessionModel.status == "COMPLETED",
        )
        .order_by(SessionModel.scheduled_at.desc())
        .all()
    )
    return render_template("profile.html", profile_user=user, completed=completed)


@app.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    user = current_user()
    if request.method == "POST":
        user.name = request.form.get("name", user.name).strip() or user.name
        user.college = request.form.get("college", "").strip()
        user.department = request.form.get("department", "").strip()
        user.year = request.form.get("year", "").strip()
        user.bio = request.form.get("bio", "").strip()
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("profile", user_id=user.id))
    return render_template("edit_profile.html", user=user)


@app.route("/skills", methods=["GET", "POST"])
@login_required
def edit_skills():
    user = current_user()
    all_skills = Skill.query.order_by(Skill.category, Skill.name).all()

    if request.method == "POST":
        skill_id = request.form.get("skill_id")
        kind = request.form.get("type")
        level = request.form.get("level", "Beginner")

        if not skill_id or kind not in ("TEACH", "LEARN"):
            flash("Please choose a skill and type.", "danger")
            return redirect(url_for("edit_skills"))

        exists = UserSkill.query.filter_by(user_id=user.id, skill_id=skill_id, type=kind).first()
        if exists:
            flash("You've already added that skill.", "warning")
            return redirect(url_for("edit_skills"))

        db.session.add(UserSkill(user_id=user.id, skill_id=skill_id, type=kind, level=level))
        db.session.commit()
        flash("Skill added.", "success")
        return redirect(url_for("edit_skills"))

    categories = {}
    for s in all_skills:
        categories.setdefault(s.category, []).append(s)

    return render_template("skills.html", user=user, categories=categories)

@app.route("/skills/<int:user_skill_id>/remove", methods=["POST"])
@login_required
def remove_skill(user_skill_id):
    user = current_user()
    us = UserSkill.query.get_or_404(user_skill_id)
    if us.user_id != user.id:
        flash("You can't remove someone else's skill.", "danger")
        return redirect(url_for("edit_skills"))
    db.session.delete(us)
    db.session.commit()
    flash("Skill removed.", "info")
    return redirect(url_for("edit_skills"))

@app.route("/sessions")
@login_required
def sessions_page():
    user = current_user()
    all_sessions = (
        SessionModel.query.filter(
            (SessionModel.teacher_id == user.id) | (SessionModel.student_id == user.id)
        )
        .order_by(SessionModel.created_at.desc())
        .all()
    )
    return render_template("sessions.html", user=user, all_sessions=all_sessions)


@app.route("/session/new/<int:teacher_id>/<int:skill_id>", methods=["GET", "POST"])
@login_required
def new_session(teacher_id, skill_id):
    user = current_user()
    teacher = User.query.get_or_404(teacher_id)
    skill = Skill.query.get_or_404(skill_id)

    if teacher.id == user.id:
        flash("You cannot request a session with yourself.", "danger")
        return redirect(url_for("matches_page"))

    taught = UserSkill.query.filter_by(user_id=teacher.id, skill_id=skill.id, type="TEACH").first()
    if not taught:
        flash("That teacher no longer offers this skill.", "danger")
        return redirect(url_for("matches_page"))

    if request.method == "POST":
        try:
            duration = int(request.form.get("duration", 30))
        except ValueError:
            duration = 30
        scheduled_raw = request.form.get("scheduled_at")
        cost = DURATION_COST.get(duration, 25)

        if user.skill_coins < cost:
            flash("You don't have enough SkillCoins for this session.", "danger")
            return redirect(url_for("new_session", teacher_id=teacher.id, skill_id=skill.id))

        try:
            scheduled_at = datetime.strptime(scheduled_raw, "%Y-%m-%dT%H:%M")
        except (TypeError, ValueError):
            scheduled_at = datetime.utcnow()

        new_sess = SessionModel(
            teacher_id=teacher.id,
            student_id=user.id,
            skill_id=skill.id,
            duration=duration,
            scheduled_at=scheduled_at,
            cost=cost,
            status="REQUESTED",
        )
        db.session.add(new_sess)
        db.session.flush()
        notify(
            teacher.id,
            f"{user.name} requested to learn {skill.name} from you.",
            link=url_for("session_thread", session_id=new_sess.id),
            icon="bi-envelope-paper",
        )
        db.session.commit()
        flash(f"Session request sent to {teacher.name}!", "success")
        return redirect(url_for("sessions_page"))

    return render_template(
        "new_session.html", teacher=teacher, skill=skill, level=taught.level, costs=DURATION_COST
    )


@app.route("/session/<int:session_id>/accept", methods=["POST"])
@login_required
def accept_session(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if sess.teacher_id != user.id:
        flash("Only the teacher can accept this session.", "danger")
        return redirect(url_for("sessions_page"))
    if sess.status != "REQUESTED":
        flash("This session can no longer be accepted.", "warning")
        return redirect(url_for("sessions_page"))
    sess.status = "ACCEPTED"
    notify(
        sess.student_id,
        f"{user.name} accepted your session request for {sess.skill.name}.",
        link=url_for("session_thread", session_id=sess.id),
        icon="bi-check2-circle",
    )
    db.session.commit()
    flash("Session accepted.", "success")
    return redirect(url_for("sessions_page"))


@app.route("/session/<int:session_id>/complete", methods=["POST"])
@login_required
def complete_session(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if user.id not in (sess.teacher_id, sess.student_id):
        flash("You're not part of this session.", "danger")
        return redirect(url_for("sessions_page"))
    if sess.status != "ACCEPTED":
        flash("Only accepted sessions can be marked complete.", "warning")
        return redirect(url_for("sessions_page"))

    student = User.query.get(sess.student_id)
    teacher = User.query.get(sess.teacher_id)

    if student.skill_coins < sess.cost:
        flash("You don't have enough SkillCoins.", "danger")
        return redirect(url_for("sessions_page"))

    student.skill_coins -= sess.cost
    teacher.skill_coins += sess.cost
    sess.status = "COMPLETED"

    db.session.add(
        Transaction(
            user_id=student.id,
            amount=-sess.cost,
            type="SPEND",
            description=f"Learned {sess.skill.name}",
            session_id=sess.id,
        )
    )
    db.session.add(
        Transaction(
            user_id=teacher.id,
            amount=sess.cost,
            type="EARN",
            description=f"Taught {sess.skill.name}",
            session_id=sess.id,
        )
    )
    notify(
        student.id if user.id == teacher.id else teacher.id,
        f"{user.name} marked your {sess.skill.name} session as completed.",
        link=url_for("session_thread", session_id=sess.id),
        icon="bi-flag-fill",
    )
    db.session.commit()
    flash(f"Session completed successfully. {sess.cost} SkillCoins have been transferred.", "success")
    return redirect(url_for("sessions_page"))


@app.route("/session/<int:session_id>/cancel", methods=["POST"])
@login_required
def cancel_session(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if user.id not in (sess.teacher_id, sess.student_id):
        flash("You're not part of this session.", "danger")
        return redirect(url_for("sessions_page"))
    if sess.status not in ("REQUESTED", "ACCEPTED"):
        flash("This session can no longer be cancelled.", "warning")
        return redirect(url_for("sessions_page"))
    sess.status = "CANCELLED"
    other = sess.other_party(user.id)
    notify(
        other.id,
        f"{user.name} cancelled the {sess.skill.name} session.",
        link=url_for("sessions_page"),
        icon="bi-x-circle",
    )
    db.session.commit()
    flash("Session cancelled.", "info")
    return redirect(url_for("sessions_page"))


@app.route("/session/<int:session_id>/rate", methods=["POST"])
@login_required
def rate_session(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)

    if sess.student_id != user.id:
        flash("Only the learner can rate this session.", "danger")
        return redirect(url_for("sessions_page"))
    if sess.status != "COMPLETED":
        flash("You can only rate completed sessions.", "warning")
        return redirect(url_for("sessions_page"))
    if sess.already_reviewed:
        flash("You've already rated this session.", "info")
        return redirect(url_for("sessions_page"))

    try:
        rating = int(request.form.get("rating", 0))
    except ValueError:
        rating = 0
    if rating < 1 or rating > 5:
        flash("Rating must be between 1 and 5.", "danger")
        return redirect(url_for("sessions_page"))

    comment = request.form.get("comment", "").strip()
    teacher = User.query.get(sess.teacher_id)

    db.session.add(
        Review(
            session_id=sess.id,
            reviewer_id=user.id,
            reviewee_id=teacher.id,
            rating=rating,
            comment=comment,
        )
    )
    teacher.rating = ((teacher.rating * teacher.rating_count) + rating) / (teacher.rating_count + 1)
    teacher.rating_count += 1
    notify(
        teacher.id,
        f"{user.name} rated your {sess.skill.name} session {rating}★.",
        link=url_for("profile", user_id=teacher.id),
        icon="bi-star-fill",
    )
    db.session.commit()
    flash("Thanks for your feedback! Rating submitted.", "success")
    return redirect(url_for("sessions_page"))


# --------------------------------------------------------------------------
# Session thread (chat + meeting link)
# --------------------------------------------------------------------------
@app.route("/session/<int:session_id>/thread")
@login_required
def session_thread(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if user.id not in (sess.teacher_id, sess.student_id):
        flash("You're not part of this session.", "danger")
        return redirect(url_for("sessions_page"))
    return render_template("session_thread.html", user=user, sess=sess)


@app.route("/session/<int:session_id>/message", methods=["POST"])
@login_required
def send_message(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if user.id not in (sess.teacher_id, sess.student_id):
        flash("You're not part of this session.", "danger")
        return redirect(url_for("sessions_page"))
    if sess.status == "CANCELLED":
        flash("This session was cancelled.", "warning")
        return redirect(url_for("session_thread", session_id=sess.id))

    body = request.form.get("body", "").strip()
    if body:
        db.session.add(Message(session_id=sess.id, sender_id=user.id, body=body))
        other = sess.other_party(user.id)
        notify(
            other.id,
            f"{user.name}: {body[:60]}{'…' if len(body) > 60 else ''}",
            link=url_for("session_thread", session_id=sess.id),
            icon="bi-chat-dots",
        )
        db.session.commit()
    return redirect(url_for("session_thread", session_id=sess.id))


@app.route("/session/<int:session_id>/link", methods=["POST"])
@login_required
def set_meeting_link(session_id):
    user = current_user()
    sess = SessionModel.query.get_or_404(session_id)
    if user.id not in (sess.teacher_id, sess.student_id):
        flash("You're not part of this session.", "danger")
        return redirect(url_for("sessions_page"))

    link = request.form.get("meeting_link", "").strip()
    if link and not (link.startswith("http://") or link.startswith("https://")):
        link = "https://" + link
    sess.meeting_link = link or None

    note = f"Shared a meeting link: {link}" if link else "Removed the meeting link."
    db.session.add(Message(session_id=sess.id, sender_id=user.id, body=note))
    other = sess.other_party(user.id)
    if link:
        notify(
            other.id,
            f"{user.name} shared a meeting link for {sess.skill.name}.",
            link=url_for("session_thread", session_id=sess.id),
            icon="bi-camera-video",
        )
    db.session.commit()
    flash("Meeting link updated.", "success")
    return redirect(url_for("session_thread", session_id=sess.id))


# --------------------------------------------------------------------------
# Notifications
# --------------------------------------------------------------------------
@app.route("/notifications/<int:notif_id>/open")
@login_required
def open_notification(notif_id):
    user = current_user()
    notif = Notification.query.get_or_404(notif_id)
    if notif.user_id != user.id:
        flash("You can't view that notification.", "danger")
        return redirect(url_for("dashboard"))
    notif.is_read = True
    db.session.commit()
    return redirect(notif.link or url_for("dashboard"))


@app.route("/notifications/mark-all-read", methods=["POST"])
@login_required
def mark_all_read():
    user = current_user()
    Notification.query.filter_by(user_id=user.id, is_read=False).update({"is_read": True})
    db.session.commit()
    return redirect(request.referrer or url_for("dashboard"))


# --------------------------------------------------------------------------
# Wallet
# --------------------------------------------------------------------------
@app.route("/wallet")
@login_required
def wallet():
    user = current_user()
    transactions = (
        Transaction.query.filter_by(user_id=user.id)
        .order_by(Transaction.created_at.desc())
        .all()
    )
    return render_template("wallet.html", user=user, transactions=transactions)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if User.query.count() == 0:
            seed_database()
    app.run(debug=True, port=5000)
