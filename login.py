import streamlit as st 
def login_page():
    st.title("Welcome to Document Q&A AI😎")
    st.write("Please login to continue.🔐")
    username=st.text_input("👨‍💻Username")
    password=st.text_input("🔑password",type="password")
    if st.button("Login",use_container_width=True):
        if username == "admin" and password=="1234":
            st.session_state.logged_in=True
            st.session_state.username=username
            st.success("Login Successful")
            st.rerun()
        else:
            st.error("Invalid username or passwoard")
def logout():
    if st.sidebar.button("logout"):
        st.session_state.logged_in=False
        st.session_state.username=""
        st.rerun()