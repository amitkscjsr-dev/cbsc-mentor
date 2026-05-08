import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database import get_connection
from utils import get_streak, get_weak_topics, calculate_jee_readiness, get_weekly_activity
import json
from datetime import datetime, timedelta

def show():
    user_id = st.session_state['user_id']
    conn = get_connection()
    
    # ── Motivational Quote ──────────────────────────────────────────────
    quotes = [
        '"The only way to do great work is to love what you do." — Steve Jobs',
        '"Success is not final, failure is not fatal: it is the courage to continue that counts." — Churchill',
        '"Hard work beats talent when talent doesn\'t work hard." — Tim Notke',
        '"Don\'t watch the clock; do what it does. Keep going." — Sam Levenson',
        '"A year from now you will wish you had started today."',
        '"Physics is the poetry of nature, Mathematics is its grammar."',
        '"Every expert was once a beginner."',
    ]
    import random
    quote = random.choice(quotes)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;
                box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">📊 Your Command Center</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; font-style: italic; font-size: 0.95rem;">{quote}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # ── Core Metrics Row ────────────────────────────────────────────────
    test_results = pd.read_sql_query("SELECT * FROM test_results WHERE user_id=?", conn, params=(user_id,))
    perf_tracking = pd.read_sql_query("SELECT * FROM performance_tracking WHERE user_id=?", conn, params=(user_id,))
    total_topics = pd.read_sql_query("SELECT COUNT(*) as cnt FROM topics", conn).iloc[0]['cnt']
    
    total_tests = len(test_results)
    avg_score = test_results['score'].mean() if not test_results.empty else 0
    weak_topics_count = len(perf_tracking[perf_tracking['weak_area_flag'] == 1]) if not perf_tracking.empty else 0
    topics_practiced = len(perf_tracking)
    streak = get_streak(user_id)
    jee_readiness = calculate_jee_readiness(user_id)
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #ff6b6b, #ee5a24); padding: 1.2rem; border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">🔥 {streak}</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Day Streak</div>
        </div>""", unsafe_allow_html=True)
    
    with col2:
        delta_text = "Keep pushing!" if avg_score < 60 else "Great work!"
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #4facfe, #00f2fe); padding: 1.2rem; border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{avg_score:.0f}%</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Avg Score</div>
        </div>""", unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #a18cd1, #fbc2eb); padding: 1.2rem; border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{topics_practiced}/{total_topics}</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Topics Done</div>
        </div>""", unsafe_allow_html=True)
    
    with col4:
        weak_color = "135deg, #f093fb, #f5576c" if weak_topics_count > 3 else "135deg, #43e97b, #38f9d7"
        st.markdown(f"""
        <div style="background: linear-gradient({weak_color}); padding: 1.2rem; border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{weak_topics_count}</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">Weak Areas</div>
        </div>""", unsafe_allow_html=True)
    
    with col5:
        readiness_color = "135deg, #f5af19, #f12711" if jee_readiness < 40 else "135deg, #11998e, #38ef7d"
        st.markdown(f"""
        <div style="background: linear-gradient({readiness_color}); padding: 1.2rem; border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2rem; font-weight: 800;">{jee_readiness:.0f}%</div>
            <div style="font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.9;">JEE Ready</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Subject-wise Progress ───────────────────────────────────────────
    st.markdown("### 📚 Subject-wise Mastery")
    
    subject_progress = pd.read_sql_query("""
        SELECT t.subject,
               COUNT(DISTINCT t.id) as total_topics,
               COUNT(DISTINCT CASE WHEN p.accuracy >= 0.6 THEN p.topic_id END) as mastered,
               AVG(CASE WHEN p.accuracy IS NOT NULL THEN p.accuracy ELSE 0 END) * 100 as avg_accuracy
        FROM topics t
        LEFT JOIN performance_tracking p ON t.id = p.topic_id AND p.user_id = ?
        GROUP BY t.subject
    """, conn, params=(user_id,))
    
    if not subject_progress.empty:
        cols = st.columns(len(subject_progress))
        subject_icons = {'Physics': '⚛️', 'Chemistry': '🧪', 'Mathematics': '📐'}
        subject_colors = {'Physics': '#4F46E5', 'Chemistry': '#059669', 'Mathematics': '#DC2626'}
        
        for idx, (_, row) in enumerate(subject_progress.iterrows()):
            with cols[idx]:
                icon = subject_icons.get(row['subject'], '📖')
                color = subject_colors.get(row['subject'], '#6366f1')
                pct = (row['mastered'] / row['total_topics'] * 100) if row['total_topics'] > 0 else 0
                
                st.markdown(f"""
                <div style="background: white; padding: 1.2rem; border-radius: 14px; border-left: 4px solid {color};
                            box-shadow: 0 4px 15px rgba(0,0,0,0.05);">
                    <h4 style="margin: 0; color: #1a202c;">{icon} {row['subject']}</h4>
                    <div style="margin: 0.8rem 0;">
                        <div style="background: #f1f5f9; border-radius: 8px; height: 10px; overflow: hidden;">
                            <div style="background: {color}; width: {pct}%; height: 100%; border-radius: 8px; 
                                        transition: width 1s ease;"></div>
                        </div>
                    </div>
                    <p style="margin: 0; color: #64748b; font-size: 0.8rem;">
                        <b>{int(row['mastered'])}/{int(row['total_topics'])}</b> topics mastered • Avg: <b>{row['avg_accuracy']:.0f}%</b>
                    </p>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("📝 Start practicing to see your subject-wise progress!")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Weekly Activity Heatmap ───────────────────────────────────────
    st.markdown("### 🗓️ This Week's Activity")
    
    weekly_df = get_weekly_activity(user_id)
    from datetime import timedelta
    today_date = datetime.now().date()
    days_data = []
    for i in range(6, -1, -1):
        d = today_date - timedelta(days=i)
        d_str = d.isoformat()
        row = weekly_df[weekly_df['date'] == d_str] if not weekly_df.empty else pd.DataFrame()
        if not row.empty:
            mins = int(row.iloc[0]['minutes_studied'])
            tasks = int(row.iloc[0]['tasks_completed'])
            tests_done = int(row.iloc[0]['tests_taken'])
            active = mins > 0 or tasks > 0 or tests_done > 0
        else:
            mins, tasks, tests_done, active = 0, 0, 0, False
        days_data.append({
            'date': d, 'day': d.strftime('%a'), 'mins': mins,
            'tasks': tasks, 'tests': tests_done, 'active': active
        })
    
    day_cols = st.columns(7)
    for i, day in enumerate(days_data):
        with day_cols[i]:
            is_today = (day['date'] == today_date)
            intensity = min(day['mins'] / 60, 1.0) if day['active'] else 0
            if is_today:
                bg = "linear-gradient(135deg, #4F46E5, #7C3AED)"
                border = "2px solid #7C3AED"
                text_color = "white"
            elif day['active']:
                alpha = int(40 + intensity * 215)
                bg = f"linear-gradient(135deg, #10b981{alpha:02x}, #059669{alpha:02x})"
                border = "1px solid #10b98140"
                text_color = "#0f172a" if intensity < 0.5 else "white"
            else:
                bg = "#f1f5f9"
                border = "1px solid #e2e8f0"
                text_color = "#94a3b8"
            
            emoji = "🔥" if day['active'] else ("🌟" if is_today else "⚪")
            st.markdown(f"""
<div style="background: {bg}; border: {border}; border-radius: 10px; 
            padding: 0.6rem 0.3rem; text-align: center; transition: all 0.2s;">
    <div style="font-size: 1rem;">{emoji}</div>
    <div style="font-size: 0.7rem; font-weight: 700; color: {text_color}; margin-top: 0.2rem;">{day['day']}</div>
    <div style="font-size: 0.65rem; color: {text_color}; opacity: 0.8;">
        {day['mins']}m
    </div>
</div>""", unsafe_allow_html=True)
    
    # Activity summary
    active_days = sum(1 for d in days_data if d['active'])
    total_mins = sum(d['mins'] for d in days_data)
    total_tasks_week = sum(d['tasks'] for d in days_data)
    total_tests_week = sum(d['tests'] for d in days_data)
    
    st.markdown(f"""
<div style="background: white; padding: 0.8rem 1.2rem; border-radius: 12px; margin-top: 0.8rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; gap: 2rem;">
    <div style="text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #4F46E5;">{active_days}/7</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Active Days</div>
    </div>
    <div style="text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #10b981;">{total_mins}m</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Total Study</div>
    </div>
    <div style="text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #f59e0b;">{total_tasks_week}</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Tasks Done</div>
    </div>
    <div style="text-align: center;">
        <div style="font-size: 1.3rem; font-weight: 800; color: #DC2626;">{total_tests_week}</div>
        <div style="font-size: 0.7rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em;">Tests Taken</div>
    </div>
</div>""", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ── Charts Row ──────────────────────────────────────────────────────
    st.markdown("### 📈 Performance Analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        if not test_results.empty:
            test_results['date_parsed'] = pd.to_datetime(test_results['date'])
            test_results['date_only'] = test_results['date_parsed'].dt.date
            
            fig_trend = px.line(test_results, x='date_only', y='score', markers=True,
                               title="📈 Exam Readiness Curve",
                               labels={'date_only': 'Date', 'score': 'Score (%)'},
                               color_discrete_sequence=['#4F46E5'])
            fig_trend.update_layout(
                yaxis_range=[0, 100],
                margin=dict(l=20, r=20, t=50, b=20),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(family="Inter")
            )
            fig_trend.add_hline(y=60, line_dash="dash", line_color="#ef4444",
                               annotation_text="Passing Line (60%)")
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.markdown("""
            <div style="background: #f8fafc; padding: 2rem; border-radius: 14px; text-align: center; border: 2px dashed #cbd5e1;">
                <p style="font-size: 2rem; margin: 0;">📝</p>
                <p style="color: #64748b; margin: 0.5rem 0 0 0;">Take your first test to see your progress curve!</p>
            </div>""", unsafe_allow_html=True)
    
    with chart_col2:
        if not perf_tracking.empty:
            mastery_data = pd.read_sql_query("""
                SELECT t.subject, AVG(p.accuracy)*100 as avg_mastery 
                FROM performance_tracking p
                JOIN topics t ON p.topic_id = t.id
                WHERE p.user_id = ?
                GROUP BY t.subject
            """, conn, params=(user_id,))
            
            if not mastery_data.empty and len(mastery_data) >= 2:
                fig_radar = px.line_polar(mastery_data, r='avg_mastery', theta='subject', 
                                         line_close=True, title="🎯 Subject Balance",
                                         color_discrete_sequence=['#7C3AED'])
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=50, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(family="Inter")
                )
                fig_radar.update_traces(fill='toself')
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                st.markdown("""
                <div style="background: #f8fafc; padding: 2rem; border-radius: 14px; text-align: center; border: 2px dashed #cbd5e1;">
                    <p style="font-size: 2rem; margin: 0;">🎯</p>
                    <p style="color: #64748b; margin: 0.5rem 0 0 0;">Practice in at least 2 subjects to see your balance radar!</p>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background: #f8fafc; padding: 2rem; border-radius: 14px; text-align: center; border: 2px dashed #cbd5e1;">
                <p style="font-size: 2rem; margin: 0;">🎯</p>
                <p style="color: #64748b; margin: 0.5rem 0 0 0;">Start practicing to build your subject profile!</p>
            </div>""", unsafe_allow_html=True)
    
    # ── Test History ────────────────────────────────────────────────────
    if not test_results.empty:
        st.markdown("### 📋 Recent Test History")
        display_df = test_results[['date', 'test_type', 'total_questions', 'correct_answers', 'score', 'time_taken']].copy()
        display_df['date'] = pd.to_datetime(display_df['date']).dt.strftime('%Y-%m-%d %H:%M')
        display_df['time_taken'] = display_df['time_taken'].apply(lambda x: f"{x//60}m {x%60}s" if x else "N/A")
        display_df['score'] = display_df['score'].apply(lambda x: f"{x:.1f}%")
        display_df.columns = ['Date', 'Type', 'Total', 'Correct', 'Score', 'Time']
        st.dataframe(display_df.sort_index(ascending=False).head(10), use_container_width=True, hide_index=True)
    
    # ── Weak Areas Alert ────────────────────────────────────────────────
    weak_df = get_weak_topics(user_id)
    if not weak_df.empty:
        st.markdown("### ⚠️ Priority Weak Areas")
        for _, row in weak_df.head(5).iterrows():
            acc_pct = row['accuracy'] * 100
            color = "#ef4444" if acc_pct < 30 else "#f59e0b" if acc_pct < 50 else "#eab308"
            st.markdown(f"""
            <div style="background: white; padding: 0.8rem 1.2rem; border-radius: 10px;
                        border-left: 4px solid {color}; margin-bottom: 0.5rem;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <b style="color: #1a202c;">{row['subject']} — {row['topic_name']}</b>
                        <br><span style="color: #64748b; font-size: 0.8rem;">{row['chapter']} • Tested {row['times_tested']}x</span>
                    </div>
                    <div style="background: {color}; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">
                        {acc_pct:.0f}%
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        # Show actionable tip from the WORST topic (first row), not the 5th
        worst_row = weak_df.iloc[0]
        if worst_row.get('tips'):
            st.info(f"💡 **Top Priority Tip ({worst_row['topic_name']}):** {worst_row['tips']}")

    conn.close()
