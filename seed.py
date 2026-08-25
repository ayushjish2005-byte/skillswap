from datetime import datetime
from werkzeug.security import generate_password_hash

from models import db, User, Skill, UserSkill, Session, Transaction, Review, Message, Notification

SKILLS = [
    ("Python", "Programming"),
    ("C", "Programming"),
    ("C++", "Programming"),
    ("Java", "Programming"),
    ("JavaScript", "Programming"),
    ("Machine Learning", "AI/Data"),
    ("Data Science", "AI/Data"),
    ("Data Analysis", "AI/Data"),
    ("UI/UX", "Design"),
    ("Figma", "Design"),
    ("Photoshop", "Design"),
    ("Graphic Design", "Design"),
    ("Video Editing", "Creative"),
    ("Photography", "Creative"),
    ("Content Creation", "Creative"),
    ("Public Speaking", "Communication"),
    ("English Speaking", "Communication"),
    ("Presentation Skills", "Communication"),
    ("Excel", "Other"),
    ("Digital Marketing", "Other"),
    ("Guitar", "Other"),
]

DEMO_PASSWORD = "password123"


def _skill(name):
    return Skill.query.filter_by(name=name).first()


def seed_database():
    """Wipe and re-seed the database with skills + demo students/matches."""
    db.drop_all()
    db.create_all()

    for name, category in SKILLS:
        db.session.add(Skill(name=name, category=category))
    db.session.commit()

    def make_user(name, email, college, department, year, bio, coins=100):
        u = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            college=college,
            department=department,
            year=year,
            bio=bio,
            skill_coins=coins,
        )
        db.session.add(u)
        db.session.flush()
        db.session.add(
            Transaction(
                user_id=u.id,
                amount=100,
                type="BONUS",
                description="Welcome bonus",
            )
        )
        return u

    def add_skill(user, skill_name, kind, level="Intermediate"):
        db.session.add(
            UserSkill(user_id=user.id, skill_id=_skill(skill_name).id, type=kind, level=level)
        )

    rahul = make_user(
        "Rahul Verma", "rahul@skillswap.dev", "CGC Jhanjeri", "AI & Data Science", "2nd Year",
        "Backend guy who loves Python. Trying to finally learn video editing for my projects.",
    )
    add_skill(rahul, "Python", "TEACH", "Advanced")
    add_skill(rahul, "C++", "TEACH", "Intermediate")
    add_skill(rahul, "Video Editing", "LEARN", "Beginner")

    aman = make_user(
        "Aman Sharma", "aman@skillswap.dev", "CGC Jhanjeri", "Computer Science", "3rd Year",
        "Run a small YouTube channel, editing is my thing. Want to get into Python for automation.",
    )
    add_skill(aman, "Video Editing", "TEACH", "Advanced")
    add_skill(aman, "Photoshop", "TEACH", "Intermediate")
    add_skill(aman, "Python", "LEARN", "Beginner")

    priya = make_user(
        "Priya Malhotra", "priya@skillswap.dev", "CGC Jhanjeri", "AI & Data Science", "2nd Year",
        "Design-obsessed. Figma is my happy place. Curious about ML.",
    )
    add_skill(priya, "UI/UX", "TEACH", "Advanced")
    add_skill(priya, "Figma", "TEACH", "Advanced")
    add_skill(priya, "Machine Learning", "LEARN", "Beginner")

    arjun = make_user(
        "Arjun Singh", "arjun@skillswap.dev", "CGC Jhanjeri", "AI & Data Science", "4th Year",
        "ML/Python since 1st year. Design has always been my weak spot.",
    )
    add_skill(arjun, "Machine Learning", "TEACH", "Advanced")
    add_skill(arjun, "Python", "TEACH", "Advanced")
    add_skill(arjun, "UI/UX", "LEARN", "Beginner")

    sneha = make_user(
        "Sneha Kapoor", "sneha@skillswap.dev", "CGC Jhanjeri", "Business Administration", "1st Year",
        "Marketing enthusiast. Working on my public speaking confidence.",
    )
    add_skill(sneha, "Digital Marketing", "TEACH", "Intermediate")
    add_skill(sneha, "Content Creation", "TEACH", "Intermediate")
    add_skill(sneha, "Public Speaking", "LEARN", "Beginner")
    add_skill(sneha, "Excel", "LEARN", "Beginner")

    kabir = make_user(
        "Kabir Nanda", "kabir@skillswap.dev", "CGC Jhanjeri", "AI & Data Science", "3rd Year",
        "Play guitar since school, happy to teach. Trying to get better at public speaking.",
    )
    add_skill(kabir, "Guitar", "TEACH", "Advanced")
    add_skill(kabir, "Public Speaking", "LEARN", "Intermediate")

    db.session.commit()

    # Give Aman and Priya an existing rating so the demo shows populated stars.
    for teacher, student, rating, comment in [
        (aman, rahul, 5, "Super clear explanations, learned a lot!"),
        (priya, arjun, 4, "Great intro to Figma basics."),
    ]:
        sess = Session(
            teacher_id=teacher.id,
            student_id=student.id,
            skill_id=teacher.teach_skills[0].skill_id,
            duration=30,
            scheduled_at=datetime.utcnow(),
            cost=25,
            status="COMPLETED",
        )
        db.session.add(sess)
        db.session.flush()
        db.session.add(
            Review(
                session_id=sess.id,
                reviewer_id=student.id,
                reviewee_id=teacher.id,
                rating=rating,
                comment=comment,
            )
        )
        teacher.rating = ((teacher.rating * teacher.rating_count) + rating) / (teacher.rating_count + 1)
        teacher.rating_count += 1

    db.session.commit()

    # --- Kabir: a fully "live" demo account, ready to show off chat + ---
    # --- meeting links + notifications without the judge doing anything first.

    # 1) A pending request Kabir still needs to Accept/Decline.
    pending = Session(
        teacher_id=kabir.id,
        student_id=sneha.id,
        skill_id=_skill("Guitar").id,
        duration=30,
        scheduled_at=datetime.utcnow(),
        cost=25,
        status="REQUESTED",
    )
    db.session.add(pending)
    db.session.flush()
    db.session.add(Notification(
        user_id=kabir.id,
        message=f"{sneha.name} requested to learn Guitar from you.",
        icon="bi-envelope-paper",
        link=f"/session/{pending.id}/thread",
    ))

    # 2) An already-accepted session with a real chat thread + meeting link set.
    accepted = Session(
        teacher_id=arjun.id,
        student_id=kabir.id,
        skill_id=_skill("Public Speaking").id,
        duration=30,
        scheduled_at=datetime.utcnow(),
        cost=25,
        status="ACCEPTED",
        meeting_link="https://meet.google.com/skillswap-demo",
    )
    db.session.add(accepted)
    db.session.flush()

    thread = [
        (arjun, "Hey! Accepted your request, excited to help with public speaking."),
        (kabir, "Awesome, thank you! What should I prep beforehand?"),
        (arjun, "Just bring a 2-min topic you know well, we'll practice structure and pacing."),
        (arjun, "Shared a meeting link: https://meet.google.com/skillswap-demo"),
    ]
    for sender, body in thread:
        db.session.add(Message(session_id=accepted.id, sender_id=sender.id, body=body))

    db.session.add(Notification(
        user_id=kabir.id,
        message=f"{arjun.name} shared a meeting link for Public Speaking.",
        icon="bi-camera-video",
        link=f"/session/{accepted.id}/thread",
    ))
    db.session.add(Notification(
        user_id=kabir.id,
        message=f"{arjun.name}: Just bring a 2-min topic you know well...",
        icon="bi-chat-dots",
        link=f"/session/{accepted.id}/thread",
    ))

    db.session.commit()
