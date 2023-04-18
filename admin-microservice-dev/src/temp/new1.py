from argon2 import PasswordHasher


def hashpass(password):
    hashedpass = PasswordHasher().hash(password)
    print(hashedpass)
    # return hashedpass


hashpass(password='flynavaadmin@1234')
