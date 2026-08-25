"""
AI-style matching engine for SkillSwap.

Uses a lightweight keyword/category "semantic" similarity fallback
(no heavyweight ML dependencies), so the app always works even
without an embeddings model installed - as required by the spec.
"""

# Skills that are conceptually related even when the name doesn't match exactly.
RELATED = {
    "Data Analysis": ["Python", "Excel", "Data Science", "Machine Learning"],
    "Data Science": ["Python", "Machine Learning", "Data Analysis"],
    "Machine Learning": ["Python", "Data Science", "Data Analysis"],
    "Video Editing": ["Photography", "Content Creation"],
    "Photoshop": ["Graphic Design", "UI/UX", "Photography"],
    "UI/UX": ["Figma", "Graphic Design"],
    "Graphic Design": ["Photoshop", "UI/UX"],
    "Public Speaking": ["Presentation Skills", "English Speaking"],
    "Presentation Skills": ["Public Speaking", "English Speaking"],
    "English Speaking": ["Public Speaking", "Presentation Skills"],
    "Content Creation": ["Video Editing", "Photography", "Digital Marketing"],
    "Digital Marketing": ["Content Creation", "Public Speaking"],
    "C++": ["C", "Java"],
    "C": ["C++"],
    "Java": ["C++", "JavaScript"],
    "JavaScript": ["Java", "Python"],
    "Figma": ["UI/UX", "Graphic Design"],
}

LEVEL_SCORE = {"Beginner": 0.4, "Intermediate": 0.7, "Advanced": 1.0}


def skill_similarity(learn_skill, teach_skill):
    """Return a 0..1 similarity score between a wanted skill and a taught skill."""
    if learn_skill.id == teach_skill.id:
        return 1.0
    if teach_skill.name in RELATED.get(learn_skill.name, []):
        return 0.7
    if learn_skill.category == teach_skill.category:
        return 0.4
    return 0.0


def compute_matches(student, candidates):
    """
    Compute ranked AI matches for `student` from a list of candidate Users.
    Weights: Skill Similarity 60%, Skill Level 15%, Teacher Rating 15%, Mutual Exchange 10%.
    """
    results = []

    for teacher in candidates:
        if teacher.id == student.id or not teacher.teach_skills:
            continue

        best = None
        for ls in student.learn_skills:
            for ts in teacher.teach_skills:
                sim = skill_similarity(ls.skill, ts.skill)
                if sim > 0 and (best is None or sim > best[2]):
                    best = (ls, ts, sim)

        if not best:
            continue

        learn_us, teach_us, sim = best

        skill_sim_score = sim
        level_score = LEVEL_SCORE.get(teach_us.level, 0.5)
        rating_score = (teacher.rating / 5.0) if teacher.rating_count > 0 else 0.7

        mutual = 0.0
        for tl in teacher.learn_skills:
            for ts2 in student.teach_skills:
                if skill_similarity(tl.skill, ts2.skill) > 0:
                    mutual = 1.0
                    break
            if mutual:
                break

        final_score = (
            0.60 * skill_sim_score
            + 0.15 * level_score
            + 0.15 * rating_score
            + 0.10 * mutual
        ) * 100
        final_score = int(round(max(0, min(100, final_score))))

        reasons = []
        if sim >= 0.99:
            reasons.append(f"Teaches {teach_us.skill.name}, a skill you want to learn")
        else:
            reasons.append(
                f"Teaches {teach_us.skill.name}, closely related to {learn_us.skill.name}"
            )
        if level_score >= 0.7:
            reasons.append(f"Compatible skill level ({teach_us.level})")
        if rating_score >= 0.8:
            reasons.append("Good student rating")
        if mutual:
            reasons.append("Mutual skill exchange possible")

        results.append(
            {
                "teacher": teacher,
                "score": final_score,
                "matched_skill": teach_us.skill,
                "matched_level": teach_us.level,
                "wanted_skill": learn_us.skill,
                "reasons": reasons,
            }
        )

    results.sort(key=lambda r: r["score"], reverse=True)
    return results
