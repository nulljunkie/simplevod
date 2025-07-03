import secrets
import string

def generate_random_string(length=32):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_token(user_id):
    from database import ActivationToken, get_db
    with get_db() as db:
        token = ActivationToken(user_id=user_id)
        db.add(token)
        db.commit()
        return token.token
