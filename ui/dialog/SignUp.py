import sqlite3
import uuid
import os

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)

from core.authentication.AuthenticationService import AuthenticationService

class SignUp(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.auth_service = AuthenticationService()

        self.setWindowTitle("Create Account")
        self.setFixedSize(400, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)

        layout.addWidget(QLabel("Create New Account", objectName="header", alignment=Qt.AlignmentFlag.AlignCenter))

        self.username_input = QLineEdit(placeholderText="Username:")
        self.password_input = QLineEdit(placeholderText="Password:", echoMode=QLineEdit.EchoMode.Password)
        self.verify_password_input = QLineEdit(placeholderText="Verify Password:", echoMode=QLineEdit.EchoMode.Password)
        self.phone_input = QLineEdit(placeholderText="Phone Number:")
        self.email_input = QLineEdit(placeholderText="Email Address:")

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.verify_password_input)
        layout.addWidget(self.phone_input)
        layout.addWidget(self.email_input)

        signup_btn = QPushButton("Sign Up", objectName="redButton")
        signup_btn.clicked.connect(self.handle_signup)
        layout.addWidget(signup_btn)

    def handle_signup(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        verify_password = self.verify_password_input.text()
        phone = self.phone_input.text().strip()
        email = self.email_input.text().strip()

        # 1. Validation
        if not all([username, password, verify_password, phone, email]):
            QMessageBox.warning(self, "Error", "All fields are required.")
            return

        if password != verify_password:
            QMessageBox.warning(self, "Error", "Passwords do not match.")
            return

        try:
            conn = sqlite3.connect("WealthTrackersDB.sqlite")
            cursor = conn.cursor()

            # 2. Check for duplicate username
            cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
            if cursor.fetchone():
                QMessageBox.warning(self, "Error", "Username is already taken. Please choose another.")
                conn.close()
                return

            # 3. Cryptographic Operations
            user_id = str(uuid.uuid4())
            salt = os.urandom(16)

            # Hash password (Argon2id)
            password_hash = self.auth_service.hash_password(password)

            # Derive AES-GCM Key (PBKDF2)
            aes_key = AuthenticationService.derive_aes_key(password, salt)

            # Encrypt sensitive PII
            enc_phone = AuthenticationService.encrypt(phone, aes_key)
            enc_email = AuthenticationService.encrypt(email, aes_key)

            # 4. Save to Database
            cursor.execute("""
                           INSERT INTO users (user_id, username, password_hash, encryption_salt, enc_phone, enc_email)
                           VALUES (?, ?, ?, ?, ?, ?)
                           """, (user_id, username, password_hash, salt, enc_phone, enc_email))

            conn.commit()
            conn.close()

            QMessageBox.information(self, "Success", "Account created successfully! You can now log in.")
            self.accept()

        except sqlite3.Error as e:
            QMessageBox.critical(self, "Database Error", f"An error occurred: {str(e)}")