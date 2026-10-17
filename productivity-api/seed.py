from faker import Faker

from app import app
from config import db
from models import Note, User

fake = Faker()
Faker.seed(12345)


def seed():
    Note.query.delete()
    User.query.delete()

    users = []
    for name in ("echo", "amanda", "wanjiku"):
        user = User(username=name)
        user.password_hash = "password123"
        users.append(user)

    db.session.add_all(users)
    db.session.commit()

    notes = []
    for user in users:
        for _ in range(12):
            notes.append(
                Note(
                    title=fake.sentence(nb_words=4).rstrip("."),
                    content=fake.paragraph(nb_sentences=3),
                    user_id=user.id,
                )
            )

    db.session.add_all(notes)
    db.session.commit()


if __name__ == "__main__":
    with app.app_context():
        seed()
        print(f"Seeded {User.query.count()} users and {Note.query.count()} notes")
