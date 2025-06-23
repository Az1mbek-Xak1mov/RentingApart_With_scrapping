from sqlalchemy.orm import Session

from db.models import Apartment


def get_phone(session: Session, phone_number: str):
    return session.query(Apartment).filter_by(phone_number=phone_number).first()