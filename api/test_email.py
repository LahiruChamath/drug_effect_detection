from app import create_app, mail
from flask_mail import Message

app = create_app()
with app.app_context():
    try:
        msg = Message("Test", recipients=["lahiru8336@gmail.com"], sender="lahiru8336@gmail.com", body="Testing")
        mail.send(msg)
        print("Success!")
    except Exception as e:
        print("Failed:", e)
