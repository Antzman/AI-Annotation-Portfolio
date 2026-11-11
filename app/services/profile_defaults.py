from sqlalchemy import select

from app.extensions import db
from app.models import UserProfile

DEFAULT_PROFILE = {
    "name": "Ant",
    "introduction": (
        "I'm a South African technology enthusiast with a professional background "
        "in hospitality software support, operational systems and client training.\n\n"
        "During my time working with GAAP Point of Sale, I supported hospitality "
        "businesses remotely, helping clients troubleshoot software issues, "
        "investigate reporting and stock discrepancies, understand operational "
        "data and get more value from their systems.\n\n"
        "My experience has developed my ability to analyse information, follow "
        "structured processes, identify inconsistencies and communicate technical "
        "findings clearly.\n\n"
        "I'm currently expanding my knowledge of artificial intelligence, software "
        "development and data-driven technologies. My interest in AI annotation "
        "comes from the opportunity to combine careful observation, analytical "
        "thinking and attention to detail to help improve the quality of data used "
        "to train intelligent systems.\n\n"
        "This application demonstrates my independent exploration of video "
        "annotation workflows, including object identification, action recognition, "
        "movement analysis and video quality assessment."
    ),
    "experience": (
        "Remote hospitality software support\n"
        "Software troubleshooting and issue investigation\n"
        "Operational data and reporting analysis\n"
        "Stock control and system discrepancy investigation\n"
        "Client training and technical communication\n"
        "Independent software development projects"
    ),
    "technical_interests": (
        "Artificial Intelligence\n"
        "Video annotation and data labelling\n"
        "Software development\n"
        "Data quality and analysis\n"
        "Computer vision and intelligent systems"
    ),
    "skills": (
        "Attention to detail\n"
        "Analytical thinking\n"
        "Written English communication\n"
        "Following structured instructions\n"
        "Identifying inconsistencies\n"
        "Software troubleshooting\n"
        "Remote client support\n"
        "Technical documentation"
    ),
    "contact_information": None,
}


def ensure_default_profile():
    profile = db.session.execute(
        select(UserProfile).order_by(UserProfile.id).limit(1)
    ).scalar_one_or_none()
    if profile is not None:
        return

    db.session.add(UserProfile(id=1, **DEFAULT_PROFILE))
    db.session.commit()
