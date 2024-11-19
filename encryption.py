from cryptography.fernet import Fernet

# Generate a key for encryption
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

# Save the encryption key (secure this key)
with open("encryption_key.key", "wb") as key_file:
    key_file.write(encryption_key)

# Encrypt the API key
api_key = "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"
encrypted_key = cipher.encrypt(api_key.encode())

# Save the encrypted API key to a file
with open("encrypted_api_key.txt", "wb") as encrypted_file:
    encrypted_file.write(encrypted_key)

print("API key encrypted and saved!")
