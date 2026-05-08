import streamlit as st
import pandas as pd
import os
from database import get_connection

def show_login_registration():
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0 1rem 0;">
        <h1 style="font-size: 2.5rem; background: linear-gradient(90deg, #4F46E5, #7C3AED, #EC4899); 
                   -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;">
            🎓 AI Learning Mentor
        </h1>
        <p style="color: #64748b; font-size: 1.1rem; margin-top: 0.5rem;">
            Your personalized path to ace CBSE Boards & crack JEE 2027
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Feature highlights
    st.markdown("""
    <div style="display: flex; gap: 1rem; margin: 1.5rem 0; flex-wrap: wrap;">
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #667eea, #764ba2); 
                    padding: 1.2rem; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 1.5rem;">🧠</div>
            <b>AI-Powered Learning</b>
            <p style="font-size: 0.8rem; opacity: 0.9; margin: 0.3rem 0 0 0;">Concepts explained like a patient tutor</p>
        </div>
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #f093fb, #f5576c); 
                    padding: 1.2rem; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 1.5rem;">📊</div>
            <b>Smart Analytics</b>
            <p style="font-size: 0.8rem; opacity: 0.9; margin: 0.3rem 0 0 0;">Track progress & identify weak areas</p>
        </div>
        <div style="flex: 1; min-width: 200px; background: linear-gradient(135deg, #4facfe, #00f2fe); 
                    padding: 1.2rem; border-radius: 12px; color: white; text-align: center;">
            <div style="font-size: 1.5rem;">🎯</div>
            <b>Adaptive Practice</b>
            <p style="font-size: 0.8rem; opacity: 0.9; margin: 0.3rem 0 0 0;">200+ questions across PCM</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 0.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
            <h3 style="text-align: center; color: #1a202c;">🔐 Login</h3>
        </div>""", unsafe_allow_html=True)
        
        conn = get_connection()
        users_df = pd.read_sql_query("SELECT * FROM users", conn)
        conn.close()
        
        if not users_df.empty:
            selected_user = st.selectbox("Select Your Profile", users_df['name'].tolist(), 
                                         label_visibility="collapsed",
                                         placeholder="Choose your name...")
            if st.button("🚀 Login & Start Learning", use_container_width=True):
                user_record = users_df[users_df['name'] == selected_user].iloc[0]
                st.session_state['user_id'] = int(user_record['id'])
                st.session_state['user_name'] = user_record['name']
                st.rerun()
        else:
            st.info("No profiles yet. Register to get started! →")

    with col2:
        st.markdown("""
        <div style="background: white; padding: 0.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.06);">
            <h3 style="text-align: center; color: #1a202c;">✨ New Student</h3>
        </div>""", unsafe_allow_html=True)
        
        with st.form("register_form"):
            name = st.text_input("Full Name", placeholder="e.g., Amit Kumar")
            target_year = st.selectbox("Target Exam Year", [2027, 2028])
            target_exam = st.selectbox("Target Exam", ["JEE Mains", "JEE Mains + Advanced", "CBSE Boards Only"])
            current_level = st.select_slider("How do you rate yourself currently?", 
                                              options=["Beginner", "Weak", "Average", "Good", "Strong"],
                                              value="Average")
            study_hours = st.number_input("Available Study Hours/Day", min_value=1, max_value=16, value=4,
                                          help="Be realistic! Quality > quantity")
            
            submit = st.form_submit_button("🎯 Register & Build My Roadmap", use_container_width=True)
            
            if submit and name:
                conn = get_connection()
                c = conn.cursor()
                
                # Check for duplicate name
                c.execute("SELECT id FROM users WHERE name=?", (name,))
                if c.fetchone():
                    st.error("A student with this name already exists. Please login instead.")
                    conn.close()
                else:
                    c.execute("""
                        INSERT INTO users (name, target_year, target_exam, current_level, study_hours, ai_provider) 
                        VALUES (?, ?, ?, ?, ?, 'Gemini')
                    """, (name, target_year, target_exam, current_level, study_hours))
                    new_id = c.lastrowid
                    conn.commit()
                    conn.close()
                    
                    st.success(f"🎉 Welcome aboard, {name}! Your personalized learning journey begins now.")
                    st.session_state['user_id'] = new_id
                    st.session_state['user_name'] = name
                    st.rerun()
            elif submit and not name:
                st.warning("Please enter your name.")


def show_settings():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">⚙️ Profile Settings</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">Customize your learning experience</p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (st.session_state['user_id'],))
    user_row = c.fetchone()
    
    if user_row:
        # Convert sqlite3.Row to dict for safe .get() access
        user = dict(user_row)
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h3 style="margin: 0 0 0.5rem 0;">👤 Personal Details</h3>
            </div>""", unsafe_allow_html=True)
            
            st.text_input("Name", user['name'], disabled=True)
            st.text_input("Target Exam", user.get('target_exam', 'JEE Mains') or 'JEE Mains', disabled=True)
            st.number_input("Target Year", value=user['target_year'], disabled=True)
            st.text_input("Current Level", user['current_level'], disabled=True)
            st.text_input("Member Since", str(user['created_at'])[:10], disabled=True)
        
        with col2:
            st.markdown("""
            <div style="background: white; padding: 1rem; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                <h3 style="margin: 0 0 0.5rem 0;">🔧 Learning Preferences</h3>
            </div>""", unsafe_allow_html=True)
            
            new_hours = st.number_input("Study Hours/Day", min_value=1, max_value=16, value=user['study_hours'],
                                         help="This affects your daily study plan intensity")
            
            ai_options = ["Gemini", "Groq", "OpenAI"]
            current_ai = user.get('ai_provider', 'Gemini') or 'Gemini'
            ai_index = ai_options.index(current_ai) if current_ai in ai_options else 0
            
            new_ai = st.selectbox("AI Provider", ai_options, index=ai_index,
                                   help="Gemini (free), Groq (free), OpenAI (paid)")
            
            ai_info = {
                "Gemini": "🟢 **Free** — Google's Gemini Flash. 15 requests/min, 1M tokens/day.",
                "Groq": "🟢 **Free** — LLaMA 3.3 70B on Groq. Very fast inference.",
                "OpenAI": "🟡 **Paid** — GPT-4o-mini. $0.15/1M input tokens."
            }
            st.caption(ai_info.get(new_ai, ""))
            
            st.markdown("---")
            
            if st.button("💾 Save Settings", use_container_width=True):
                c.execute("UPDATE users SET study_hours=?, ai_provider=? WHERE id=?", 
                         (new_hours, new_ai, st.session_state['user_id']))
                conn.commit()
                st.success("✅ Settings saved successfully!")
        
        # Stats summary
        st.markdown("---")
        st.markdown("### 📊 Your Journey So Far")
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        c.execute("SELECT COUNT(*) as cnt FROM test_results WHERE user_id=?", (st.session_state['user_id'],))
        total_tests = c.fetchone()['cnt']
        
        c.execute("SELECT COUNT(*) as cnt FROM performance_tracking WHERE user_id=?", (st.session_state['user_id'],))
        topics_practiced = c.fetchone()['cnt']
        
        c.execute("SELECT COUNT(*) as cnt FROM bookmarks WHERE user_id=?", (st.session_state['user_id'],))
        bookmarks_count = c.fetchone()['cnt']
        
        c.execute("SELECT COALESCE(SUM(minutes_studied), 0) as total FROM study_streaks WHERE user_id=?", 
                  (st.session_state['user_id'],))
        total_minutes = c.fetchone()['total']
        
        stats_col1.metric("Tests Taken", total_tests)
        stats_col2.metric("Topics Practiced", topics_practiced)
        stats_col3.metric("Bookmarked Qs", bookmarks_count)
        stats_col4.metric("Study Minutes", total_minutes)
    else:
        st.error("Could not load profile. Please log out and log in again.")

    conn.close()
