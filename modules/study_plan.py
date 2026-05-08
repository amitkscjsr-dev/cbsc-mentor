import streamlit as st
import pandas as pd
from datetime import datetime
from utils import generate_study_plan, update_streak
from database import get_connection

def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">📅 Intelligent Study Schedule</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            AI-curated daily plan • Weak area priority • Spaced repetition
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state['user_id']
    
    # ── Weekly Overview ────────────────────────────────────────────────────────
    conn_overview = get_connection()
    from datetime import timedelta
    today_date = datetime.now().date()
    week_plan = pd.read_sql_query("""
        SELECT COUNT(*) as total,
               SUM(CASE WHEN status='Done' THEN 1 ELSE 0 END) as done
        FROM study_plan
        WHERE user_id=? AND date BETWEEN ? AND ?
    """, conn_overview, params=(user_id, today_date.isoformat(), (today_date + timedelta(days=6)).isoformat()))
    conn_overview.close()
    
    w_total = int(week_plan.iloc[0]['total']) if not week_plan.empty else 0
    w_done = int(week_plan.iloc[0]['done'] or 0) if not week_plan.empty else 0
    w_pct = (w_done / w_total * 100) if w_total > 0 else 0
    
    if w_total > 0:
        c1w, c2w, c3w = st.columns([1, 2, 1])
        with c2w:
            st.markdown(f"""
<div style="background: white; padding: 1rem 1.5rem; border-radius: 14px; 
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center; margin-bottom: 1rem;">
    <div style="color: #64748b; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em;">7-Day Plan Progress</div>
    <div style="display: flex; align-items: center; gap: 1rem; justify-content: center; margin: 0.5rem 0;">
        <div style="font-size: 2rem; font-weight: 800; color: {'#10b981' if w_pct >= 70 else '#f59e0b' if w_pct >= 40 else '#ef4444'};"
        >{w_done}/{w_total}</div>
        <div style="flex: 1; max-width: 200px;">
            <div style="background: #f1f5f9; border-radius: 8px; height: 12px; overflow: hidden;">
                <div style="background: linear-gradient(90deg, #10b981, #059669); width: {w_pct:.0f}%; height: 100%; border-radius: 8px;"></div>
            </div>
            <div style="color: #94a3b8; font-size: 0.75rem; margin-top: 0.2rem;">{w_pct:.0f}% complete</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Generate Smart Plan", use_container_width=True):
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT study_hours FROM users WHERE id=?", (user_id,))
            hours = c.fetchone()['study_hours']
            conn.close()
            with st.spinner("🧠 Analyzing your performance & building optimal schedule..."):
                generate_study_plan(user_id, hours)
            st.success("✅ Plan generated! Weak topics and high-weightage areas are prioritized.")
            st.rerun()
    
    # ── Today's Tasks ───────────────────────────────────────────────────
    st.markdown("---")
    
    conn = get_connection()
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # Show tabs for different days
    days = ["📌 Today", "Tomorrow", "+2 Days", "+3 Days", "+4 Days", "+5 Days", "+6 Days"]
    selected_tab = st.tabs(days)
    
    from datetime import timedelta
    
    for day_idx, tab in enumerate(selected_tab):
        with tab:
            target_date = (datetime.now() + timedelta(days=day_idx)).strftime('%Y-%m-%d')
            display_date = (datetime.now() + timedelta(days=day_idx)).strftime('%A, %B %d')
            
            plan_df = pd.read_sql_query("""
                SELECT sp.id, t.subject, t.chapter, t.topic_name, sp.task_type, sp.status, sp.priority,
                       t.difficulty, t.cbse_weightage, t.jee_weightage
                FROM study_plan sp
                JOIN topics t ON sp.topic_id = t.id
                WHERE sp.user_id = ? AND date = ?
                ORDER BY sp.priority DESC
            """, conn, params=(user_id, target_date))
            
            if plan_df.empty:
                st.markdown(f"""
                <div style="background: #f8fafc; padding: 2rem; border-radius: 14px; text-align: center; border: 2px dashed #cbd5e1;">
                    <p style="font-size: 1.5rem; margin: 0;">📋</p>
                    <p style="color: #64748b; margin: 0.5rem 0 0 0;">
                        No tasks for {display_date}.<br>
                        Click <b>"Generate Smart Plan"</b> to create your 7-day roadmap.
                    </p>
                </div>""", unsafe_allow_html=True)
            else:
                # Progress bar for the day
                total = len(plan_df)
                done = len(plan_df[plan_df['status'] == 'Done'])
                pct = (done / total * 100) if total > 0 else 0
                
                st.markdown(f"""
                <div style="margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 0.3rem;">
                        <span style="font-weight: 600; color: #1a202c;">{display_date}</span>
                        <span style="color: #64748b; font-size: 0.85rem;">{done}/{total} completed</span>
                    </div>
                    <div style="background: #e2e8f0; border-radius: 8px; height: 8px; overflow: hidden;">
                        <div style="background: linear-gradient(90deg, #10b981, #059669); width: {pct}%; height: 100%; 
                                    border-radius: 8px; transition: width 0.5s;"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
                
                subject_icons = {'Physics': '⚛️', 'Chemistry': '🧪', 'Mathematics': '📐'}
                difficulty_colors = {'Easy': '#10b981', 'Medium': '#f59e0b', 'Hard': '#ef4444'}
                
                for idx, row in plan_df.iterrows():
                    is_done = row['status'] == 'Done'
                    icon = subject_icons.get(row['subject'], '📖')
                    diff_color = difficulty_colors.get(row['difficulty'], '#6b7280')
                    
                    bg = "#f0fdf4" if is_done else "#ffffff"
                    border = "#10b981" if is_done else diff_color
                    
                    st.markdown(f"""
                    <div style="background: {bg}; padding: 1rem 1.2rem; border-radius: 12px; 
                                border-left: 5px solid {border}; margin-bottom: 0.5rem;
                                box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: #0f172a;">{icon} {row['subject']} — {row['topic_name']}</h4>
                                <p style="margin: 0.2rem 0 0 0; color: #64748b; font-size: 0.85rem;">
                                    {row['chapter']} • {row['task_type']}
                                </p>
                            </div>
                            <div style="display: flex; gap: 0.5rem; align-items: center;">
                                <span style="background: {diff_color}15; color: {diff_color}; padding: 0.2rem 0.6rem; 
                                             border-radius: 20px; font-size: 0.75rem; font-weight: 600;">
                                    {row['difficulty']}
                                </span>
                                <span style="color: #94a3b8; font-size: 0.7rem;">
                                    CBSE:{int(row['cbse_weightage'])} JEE:{int(row['jee_weightage'])}
                                </span>
                            </div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                    
                    # Checkbox to toggle completion (only for today)
                    if day_idx == 0:
                        new_status = st.checkbox(
                            f"{'✅ Completed' if is_done else '⬜ Mark Done'}", 
                            value=is_done, key=f"plan_{row['id']}")
                        
                        if new_status and not is_done:
                            c = conn.cursor()
                            c.execute("UPDATE study_plan SET status='Done' WHERE id=?", (int(row['id']),))
                            conn.commit()
                            update_streak(user_id, tasks=1, minutes=30)
                            st.success("🔥 Great job! Streak updated!")
                            st.rerun()
                        elif not new_status and is_done:
                            c = conn.cursor()
                            c.execute("UPDATE study_plan SET status='Pending' WHERE id=?", (int(row['id']),))
                            conn.commit()
                            st.rerun()
    
    conn.close()
