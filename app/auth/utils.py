from app import bcrypt


def hash_password(password):
    return bcrypt.generate_password_hash(password).decode('utf-8')


def verify_password(stored_password, provided_password):
    return bcrypt.check_password_hash(stored_password, provided_password)
