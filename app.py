import streamlit as st
from database import init_db, populate_comprehensive_data, populate_extra_questions
from modules import profile, dashboard, study_plan, subjects, practice, tests, revision
from utils import get_streak, update_streak
from database import get_connection
import pandas as pd
from datetime import datetime, date

# Initialize DB on first run
init_db()
populate_comprehensive_data()
populate_extra_questions()  # Add extra questions for sparse topics

st.set_page_config(
    page_title="AI Learning Mentor — CBSE & JEE 2027",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
# PREMIUM CSS DESIGN SYSTEM
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');
    
    /* ── Global ────────────────────────────────────── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main {
        background: linear-gradient(180deg, #f0f4f8 0%, #e8ecf1 50%, #f0f4f8 100%);
    }
    
    /* ── Headers ───────────────────────────────────── */
    h1, h2, h3 {
        color: #0f172a !important;
        font-weight: 800 !important;
        letter-spacing: -0.02em;
    }
    h1 { font-size: 1.8rem !important; }
    h2 { font-size: 1.4rem !important; }
    h3 { font-size: 1.15rem !important; }
    
    /* ── Buttons ───────────────────────────────────── */
    .stButton>button {
        background: linear-gradient(135deg, #4F46E5 0%, #7C3AED 100%);
        color: white !important;
        border-radius: 12px;
        font-weight: 600;
        border: none;
        box-shadow: 0 4px 12px -2px rgba(79, 70, 229, 0.4);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 0.55rem 1.2rem;
        font-size: 0.9rem;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px -4px rgba(79, 70, 229, 0.5);
        color: white !important;
        border: none;
        background: linear-gradient(135deg, #4338ca 0%, #6d28d9 100%);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* ── Primary Button (highlighted) ──────────────── */
    button[kind="primary"] {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
        box-shadow: 0 4px 12px -2px rgba(16, 185, 129, 0.4) !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        box-shadow: 0 8px 20px -4px rgba(16, 185, 129, 0.5) !important;
    }
    
    /* ── Metric Cards ──────────────────────────────── */
    [data-testid="metric-container"] {
        background: white;
        border-radius: 16px;
        padding: 1.2rem;
        box-shadow: 0 4px 15px -3px rgba(0, 0, 0, 0.06);
        border: 1px solid #f1f5f9;
        text-align: center;
        transition: transform 0.2s;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }
    [data-testid="metric-container"] > div > label {
        color: #64748b;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-size: 0.7rem;
    }
    [data-testid="metric-container"] > div > div > div {
        color: #0f172a;
        font-weight: 800;
        font-size: 2rem;
    }
    
    /* ── Sidebar ───────────────────────────────────── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
    }
    [data-testid="stSidebar"] .stMarkdown {
        color: #e2e8f0;
    }
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] .stRadio label {
        color: #cbd5e1 !important;
    }
    [data-testid="stSidebar"] .stRadio label:hover {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.1);
    }
    [data-testid="stSidebar"] .stAlert {
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
    }
    
    /* ── Tabs ──────────────────────────────────────── */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: white;
        border-radius: 12px;
        padding: 0.3rem;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.85rem;
        padding: 0.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4F46E5, #7C3AED) !important;
        color: white !important;
    }
    
    /* ── Expanders ─────────────────────────────────── */
    .streamlit-expanderHeader {
        background: white;
        border-radius: 12px !important;
        font-weight: 600;
        border: 1px solid #f1f5f9;
    }
    
    /* ── Data Frames ───────────────────────────────── */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
    }
    
    /* ── Select boxes ──────────────────────────────── */
    .stSelectbox > div > div {
        border-radius: 10px;
    }
    
    /* ── Radio buttons ─────────────────────────────── */
    .stRadio > label {
        font-weight: 600;
        margin-bottom: 0.3rem;
    }
    
    /* ── Alerts ─────────────────────────────────────── */
    .stAlert {
        border-radius: 12px;
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* ── Forms ──────────────────────────────────────── */
    .stForm {
        background: white;
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }
    
    /* ── Slider ─────────────────────────────────────── */
    .stSlider > div > div > div {
        background: linear-gradient(90deg, #4F46E5, #7C3AED);
    }
    
    /* ── Hide streamlit branding ───────────────────── */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ── Smooth scrolling ──────────────────────────── */
    html { scroll-behavior: smooth; }
    </style>
""", unsafe_allow_html=True)


def main():
    # Handle user session
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None
        st.session_state['user_name'] = None

    if st.session_state['user_id'] is None:
        profile.show_login_registration()
        return

    # ── Sidebar ─────────────────────────────────────────────────────────
    user_id = st.session_state['user_id']
    user_name = st.session_state['user_name']
    
    st.sidebar.markdown(f"""
    <div style="text-align: center; padding: 1rem 0;">
        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #4F46E5, #7C3AED); 
                    border-radius: 50%; display: inline-flex; align-items: center; justify-content: center;
                    font-size: 1.5rem; color: white; margin-bottom: 0.5rem;">
            {user_name[0].upper() if user_name else '?'}
        </div>
        <h3 style="margin: 0; color: white !important;">👋 {user_name}</h3>
        <p style="color: #94a3b8; font-size: 0.8rem; margin: 0;">CBSE & JEE 2027</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Navigation
    menu = {
        "📊 Dashboard": "Dashboard",
        "📅 Study Plan": "Study Plan",
        "📚 Learn Concepts": "Subjects & Learning",
        "✍️ Practice": "Practice Engine",
        "📝 Mock Exams": "Tests",
        "🧠 Revision & Flashcards": "Revision Zone",
        "⚙️ Settings": "Profile Settings"
    }
    
    choice_label = st.sidebar.radio("Navigate", list(menu.keys()), label_visibility="collapsed")
    choice = menu[choice_label]
    
    st.sidebar.markdown("---")
    
    # Real streak
    streak = get_streak(user_id)
    streak_emoji = "🔥" if streak > 0 else "💤"
    streak_msg = f"**{streak} Day{'s' if streak != 1 else ''}**" if streak > 0 else "Start today!"
    
    st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.08); padding: 1rem; border-radius: 12px; margin-bottom: 0.5rem;">
        <div style="text-align: center;">
            <span style="font-size: 1.8rem;">{streak_emoji}</span>
            <h4 style="color: white !important; margin: 0.3rem 0 0 0;">Daily Streak: {streak_msg}</h4>
            <p style="color: #94a3b8; font-size: 0.75rem; margin: 0;">
                {'🌟 Amazing consistency!' if streak >= 7 else '💪 Keep it up!' if streak >= 3 else 'Study today to start your streak!'}
            </p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Today's progress
    conn = get_connection()
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_plan = pd.read_sql_query("""
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN status='Done' THEN 1 ELSE 0 END) as done
        FROM study_plan 
        WHERE user_id=? AND date=?
    """, conn, params=(user_id, today_str))
    
    total_today = int(today_plan.iloc[0]['total']) if not today_plan.empty else 0
    done_today = int(today_plan.iloc[0]['done'] or 0) if not today_plan.empty else 0
    
    if total_today > 0:
        pct = done_today / total_today * 100
        st.sidebar.markdown(f"""
        <div style="background: rgba(255,255,255,0.08); padding: 0.8rem; border-radius: 12px; margin-bottom: 0.5rem;">
            <p style="color: #94a3b8; font-size: 0.75rem; margin: 0 0 0.3rem 0;">📌 TODAY'S PROGRESS</p>
            <div style="background: rgba(255,255,255,0.1); border-radius: 6px; height: 6px; overflow: hidden;">
                <div style="background: #10b981; width: {pct}%; height: 100%; border-radius: 6px;"></div>
            </div>
            <p style="color: #e2e8f0; font-size: 0.8rem; margin: 0.3rem 0 0 0; font-weight: 600;">
                {done_today}/{total_today} tasks done
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Next goal
    next_task = pd.read_sql_query("""
        SELECT t.subject, t.topic_name 
        FROM study_plan sp
        JOIN topics t ON sp.topic_id = t.id
        WHERE sp.user_id=? AND sp.date=? AND sp.status='Pending'
        ORDER BY sp.priority DESC LIMIT 1
    """, conn, params=(user_id, today_str))
    
    if not next_task.empty:
        next_subj = next_task.iloc[0]['subject']
        next_topic = next_task.iloc[0]['topic_name']
        subject_icons = {'Physics': '⚛️', 'Chemistry': '🧪', 'Mathematics': '📐'}
        icon = subject_icons.get(next_subj, '📖')
        
        st.sidebar.markdown(f"""
        <div style="background: rgba(79, 70, 229, 0.2); padding: 0.8rem; border-radius: 12px; border: 1px solid rgba(79, 70, 229, 0.3);">
            <p style="color: #94a3b8; font-size: 0.75rem; margin: 0;">🎯 NEXT UP</p>
            <p style="color: white; font-size: 0.85rem; margin: 0.2rem 0 0 0; font-weight: 600;">
                {icon} {next_topic}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    conn.close()
    
    st.sidebar.markdown("---")
    
    # ── Exam Countdown ──────────────────────────────────────────────────
    try:
        conn2 = get_connection()
        c2 = conn2.cursor()
        c2.execute("SELECT target_year, target_exam FROM users WHERE id=?", (user_id,))
        _u = c2.fetchone()
        conn2.close()
        if _u:
            _target_year = int(_u['target_year']) if _u['target_year'] else 2027
            _exam = _u['target_exam'] or 'JEE Mains'
            # JEE Mains typically in January-April; CBSE Boards in March
            if 'CBSE' in _exam and 'JEE' not in _exam:
                _exam_date = date(_target_year, 3, 1)  # Approx March
                _exam_label = '📋 CBSE Boards'
            elif 'Advanced' in _exam:
                _exam_date = date(_target_year, 5, 20)  # Approx May
                _exam_label = '🏆 JEE Advanced'
            else:
                _exam_date = date(_target_year, 1, 22)  # Approx Jan
                _exam_label = '🎯 JEE Mains'
            _days_left = (_exam_date - date.today()).days
            if _days_left > 0:
                _urgency_color = '#ef4444' if _days_left < 90 else '#f59e0b' if _days_left < 180 else '#10b981'
                st.sidebar.markdown(f"""
    <div style="background: rgba(255,255,255,0.06); padding: 0.8rem; border-radius: 12px;
                border: 1px solid {_urgency_color}40; margin-bottom: 0.5rem;">
        <p style="color: #94a3b8; font-size: 0.7rem; margin: 0;">{_exam_label}</p>
        <div style="display: flex; align-items: baseline; gap: 0.3rem;">
            <span style="font-size: 1.6rem; font-weight: 800; color: {_urgency_color};">{_days_left}</span>
            <span style="color: #94a3b8; font-size: 0.75rem;">days left</span>
        </div>
        <div style="background: rgba(255,255,255,0.1); border-radius: 4px; height: 4px; margin-top: 0.4rem; overflow: hidden;">
            <div style="background: {_urgency_color}; width: {min(100, max(2, (1-_days_left/730)*100)):.0f}%; height: 100%;"></div>
        </div>
    </div>""", unsafe_allow_html=True)
    except Exception:
        pass
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state['user_id'] = None
        st.session_state['user_name'] = None
        # Clear other session state
        for key in list(st.session_state.keys()):
            if key not in ['user_id', 'user_name']:
                del st.session_state[key]
        st.rerun()
    
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 1rem 0; margin-top: 1rem;">
        <p style="color: #475569; font-size: 0.7rem; margin: 0;">
            Built with ❤️ for JEE Aspirants<br>
            Powered by AI • v2.0
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Page Router ─────────────────────────────────────────────────────
    if choice == "Dashboard":
        dashboard.show()
    elif choice == "Study Plan":
        study_plan.show()
    elif choice == "Subjects & Learning":
        subjects.show()
    elif choice == "Practice Engine":
        practice.show()
    elif choice == "Tests":
        tests.show()
    elif choice == "Revision Zone":
        revision.show()
    elif choice == "Profile Settings":
        profile.show_settings()


if __name__ == "__main__":
    main()
