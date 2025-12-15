import bcrypt
pw = b"password123"
print(bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8"))
