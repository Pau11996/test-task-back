from flask.cli import FlaskGroup

from app import app, db, User

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    admin = User(username="admin", password="123")
    db.session.add(admin)
    db.session.commit()


if __name__ == "__main__":
    cli()
