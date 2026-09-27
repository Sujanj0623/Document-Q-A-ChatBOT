import streamlit as st
import psycopg2
import hashlib
import secrets
import os


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        st.error("❌ DATABASE_URL is not configured.")
        st.stop()

    return psycopg2.connect(database_url)


# =========================================================
# CREATE USERS TABLE
# =========================================================

def create_users_table():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    cursor.close()
    conn.close()


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password, salt=None):

    if salt is None:
        salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(password, stored_password):

    try:

        salt_hex, stored_hash = stored_password.split(":")

        salt = bytes.fromhex(salt_hex)

        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )

        return password_hash.hex() == stored_hash

    except Exception:

        return False


# =========================================================
# REGISTER USER
# =========================================================

def register_user(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            INSERT INTO users
            (username, password_hash)
            VALUES (%s, %s)
            """,
            (
                username,
                hash_password(password)
            )
        )

        conn.commit()

        return True

    except psycopg2.errors.UniqueViolation:

        conn.rollback()

        return False

    finally:

        cursor.close()
        conn.close()


# =========================================================
# LOGIN USER
# =========================================================

def check_login(username, password):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT password_hash
        FROM users
        WHERE username = %s
        """,
        (username,)
    )

    result = cursor.fetchone()

    cursor.close()
    conn.close()

    if result is None:
        return False

    stored_password = result[0]

    return verify_password(
        password,
        stored_password
    )


# =========================================================
# LOGIN PAGE
# =========================================================

def login_page():

    st.title("📄 Document Q&A AI 🤖")

    st.write(
        "Create your own account or login to continue. 🔐"
    )

    login_tab, signup_tab = st.tabs(
        [
            "🔐 Login",
            "📝 Create Account"
        ]
    )


    # =====================================================
    # LOGIN
    # =====================================================

    with login_tab:

        st.subheader("Welcome Back 👋")

        username = st.text_input(
            "Username",
            key="login_username"
        )

        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button(
            "🔐 Login",
            use_container_width=True
        ):

            if not username.strip():

                st.warning(
                    "⚠️ Please enter your username."
                )

            elif not password:

                st.warning(
                    "⚠️ Please enter your password."
                )

            elif check_login(
                username.strip(),
                password
            ):

                st.session_state.logged_in = True

                st.session_state.username = username.strip()

                st.success(
                    "✅ Login successful!"
                )

                st.rerun()

            else:

                st.error(
                    "❌ Invalid username or password."
                )


    # =====================================================
    # CREATE ACCOUNT
    # =====================================================

    with signup_tab:

        st.subheader("Create Your Own Account 📝")

        new_username = st.text_input(
            "Create Username",
            key="signup_username"
        )

        new_password = st.text_input(
            "Create Password",
            type="password",
            key="signup_password"
        )

        confirm_password = st.text_input(
            "Confirm Password",
            type="password",
            key="confirm_password"
        )


        if st.button(
            "📝 Create Account",
            use_container_width=True
        ):

            username_clean = new_username.strip()


            if not username_clean:

                st.warning(
                    "⚠️ Please enter a username."
                )


            elif len(username_clean) < 3:

                st.warning(
                    "⚠️ Username must contain at least 3 characters."
                )


            elif len(username_clean) > 100:

                st.warning(
                    "⚠️ Username is too long."
                )


            elif not new_password:

                st.warning(
                    "⚠️ Please create a password."
                )


            elif len(new_password) < 6:

                st.warning(
                    "⚠️ Password must contain at least 6 characters."
                )


            elif new_password != confirm_password:

                st.error(
                    "❌ Passwords do not match."
                )


            elif register_user(
                username_clean,
                new_password
            ):

                st.success(
                    "🎉 Account created successfully!"
                )

                st.info(
                    "👉 Go to the Login tab and login with your new account."
                )


            else:

                st.error(
                    "❌ This username already exists."
                )


# =========================================================
# LOGOUT
# =========================================================

def logout():

    if st.sidebar.button(
        "🚪 Logout",
        use_container_width=True
    ):

        st.session_state.logged_in = False

        st.session_state.username = ""

        # Clear chatbot messages when logging out
        if "messages" in st.session_state:
            st.session_state.messages = []

        # Clear vector database
        if "vector_db" in st.session_state:
            st.session_state.vector_db = None

        st.rerun()


# =========================================================
# CREATE DATABASE TABLE
# =========================================================

create_users_table()