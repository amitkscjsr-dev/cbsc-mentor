import streamlit as st
import pandas as pd
import json
import time
from database import get_connection
from utils import evaluate_test


def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">📝 Exam Simulator</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            Timed tests • Subject-wise • Full mock • Detailed analysis after every test
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state['user_id']
    tab_test, tab_history = st.tabs(["🚀 Take a Test", "📋 Test History"])
    with tab_test:
        _show_test_mode(user_id)
    with tab_history:
        _show_test_history(user_id)


def _show_test_mode(user_id):
    if 'test_active' not in st.session_state:
        st.session_state['test_active'] = False

    if st.session_state.get('last_test_result'):
        _render_test_results(st.session_state['last_test_result'])
        return

    if not st.session_state['test_active']:
        st.markdown("### ⚙️ Configure Your Test")
        col1, col2, col3 = st.columns(3)
        with col1:
            test_type = st.selectbox("Test Type", [
                "⚡ Quick Quiz (5 Qs)",
                "📝 Chapter Test (10 Qs)",
                "📋 Full Mock (15 Qs)",
                "🎯 Weak Areas Only (10 Qs)"
            ])
        with col2:
            conn = get_connection()
            subjects = pd.read_sql_query("SELECT DISTINCT subject FROM topics", conn)['subject'].tolist()
            subject_filter = st.selectbox("Subject", ["All Subjects"] + subjects)
        with col3:
            diff_filter = st.selectbox("Difficulty", ["Mixed", "Easy", "Medium", "Hard"])
        conn.close()

        test_configs = {
            "⚡ Quick Quiz (5 Qs)": {"limit": 5, "time": 10, "desc": "Quick daily practice. 10 minutes."},
            "📝 Chapter Test (10 Qs)": {"limit": 10, "time": 20, "desc": "Focus on one area. 20 minutes."},
            "📋 Full Mock (15 Qs)": {"limit": 15, "time": 30, "desc": "Comprehensive exam simulation. 30 minutes."},
            "🎯 Weak Areas Only (10 Qs)": {"limit": 10, "time": 20, "desc": "Target your weak spots. 20 minutes."},
        }
        config = test_configs[test_type]

        st.markdown(f"""
        <div style="background: #f8fafc; padding: 1rem; border-radius: 12px; border: 1px solid #e2e8f0; margin: 1rem 0;">
            <div style="display: flex; gap: 2rem; align-items: center;">
                <div><b>📝 Questions:</b> {config['limit']}</div>
                <div><b>⏱️ Time Limit:</b> {config['time']} min</div>
                <div><b>📌 Mode:</b> {config['desc']}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        if st.button("🚀 Start Test Now", use_container_width=True, type="primary"):
            conn = get_connection()
            limit = config['limit']
            query = "SELECT * FROM questions"
            params = []
            conditions = []
            if subject_filter != "All Subjects":
                conditions.append("topic_id IN (SELECT id FROM topics WHERE subject=?)")
                params.append(subject_filter)
            if diff_filter != "Mixed":
                conditions.append("difficulty=?")
                params.append(diff_filter)
            if "Weak Areas" in test_type:
                conditions.append("topic_id IN (SELECT topic_id FROM performance_tracking WHERE user_id=? AND weak_area_flag=1)")
                params.append(user_id)
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += f" ORDER BY RANDOM() LIMIT {limit}"
            q_df = pd.read_sql_query(query, conn, params=params)
            conn.close()

            if q_df.empty or len(q_df) < 2:
                st.error("Not enough questions available for this configuration. Try different filters.")
                return

            st.session_state['test_questions'] = q_df.to_dict('records')
            st.session_state['test_active'] = True
            st.session_state['start_time'] = time.time()
            st.session_state['test_answers'] = {}
            st.session_state['test_config'] = {
                'type': test_type,
                'time_limit': config['time'] * 60,
                'subject': subject_filter
            }
            st.rerun()

    if st.session_state['test_active']:
        config = st.session_state.get('test_config', {})
        elapsed = int(time.time() - st.session_state['start_time'])
        time_limit = config.get('time_limit', 1800)
        remaining = max(0, time_limit - elapsed)
        mins_rem = remaining // 60
        secs_rem = remaining % 60
        progress_pct = min(elapsed / time_limit, 1.0) if time_limit > 0 else 0
        timer_color = "#10b981" if progress_pct < 0.5 else "#f59e0b" if progress_pct < 0.8 else "#ef4444"

        st.markdown(f"""
        <div style="background: white; padding: 1rem 1.5rem; border-radius: 12px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05); margin-bottom: 1rem;
                    position: sticky; top: 0; z-index: 10;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="font-weight: 700; color: #1a202c;">📝 Test in Progress</div>
                <div style="font-size: 1.3rem; font-weight: 800; color: {timer_color};">
                    ⏱️ {mins_rem:02d}:{secs_rem:02d}
                </div>
                <div style="color: #64748b;">
                    {len(st.session_state.get('test_answers', {}))} / {len(st.session_state['test_questions'])} answered
                </div>
            </div>
            <div style="background: #f1f5f9; border-radius: 8px; height: 6px; margin-top: 0.5rem; overflow: hidden;">
                <div style="background: {timer_color}; width: {progress_pct*100}%; height: 100%; border-radius: 8px;
                            transition: width 1s linear;"></div>
            </div>
        </div>""", unsafe_allow_html=True)

        if remaining == 0 and time_limit > 0:
            st.warning("⏰ Time's up! Auto-submitting your test now…")
            _submit_test(user_id)

        answers = st.session_state.get('test_answers', {})
        for idx, q in enumerate(st.session_state['test_questions']):
            q_num = idx + 1
            is_answered = q['id'] in answers
            st.markdown(f"""
            <div style="background: {'#f0fdf4' if is_answered else 'white'}; padding: 1rem 1.2rem;
                        border-radius: 12px; border-left: 4px solid {'#10b981' if is_answered else '#e2e8f0'};
                        margin-bottom: 0.3rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <p style="margin: 0; color: #64748b; font-size: 0.8rem;">Question {q_num} • {q.get('difficulty', 'Medium')}</p>
                <h4 style="margin: 0.3rem 0; color: #0f172a;">{q['question_text']}</h4>
            </div>""", unsafe_allow_html=True)
            options = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
            ans = st.radio(f"Select answer for Q{q_num}", options,
                          key=f"test_q_{q['id']}", index=None, label_visibility="collapsed")
            if ans is not None:
                answers[q['id']] = ans
            st.markdown("")
        st.session_state['test_answers'] = answers

        col_submit, col_cancel = st.columns([3, 1])
        with col_submit:
            if st.button("✅ Submit Test", use_container_width=True, type="primary"):
                _submit_test(user_id)
        with col_cancel:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state['test_active'] = False
                for k in ('test_questions', 'test_answers', 'test_config', 'start_time'):
                    st.session_state.pop(k, None)
                st.rerun()


def _submit_test(user_id):
    time_taken = int(time.time() - st.session_state['start_time'])
    answers = st.session_state.get('test_answers', {})
    config = st.session_state.get('test_config', {})
    subject_filter = config.get('subject', 'All Subjects')
    if subject_filter == "All Subjects":
        subject_filter = None
    score_pct, correct, total, topic_breakdown = evaluate_test(
        user_id, config.get('type', 'Test'), answers, time_taken, subject_filter
    )
    st.session_state['last_test_result'] = {
        'score_pct': score_pct,
        'correct': correct,
        'total': total,
        'time_taken': time_taken,
        'topic_breakdown': topic_breakdown,
        'questions': st.session_state.get('test_questions', []),
        'answers': answers,
    }
    st.session_state['test_active'] = False
    for k in ('test_questions', 'test_answers', 'test_config', 'start_time'):
        st.session_state.pop(k, None)
    st.rerun()


def _render_test_results(result):
    score_pct = result['score_pct']
    correct = result['correct']
    total = result['total']
    time_taken = result['time_taken']
    topic_breakdown = result.get('topic_breakdown') or {}
    questions = result.get('questions') or []
    answers = result.get('answers') or {}

    score_color = "#ef4444" if score_pct < 40 else "#f59e0b" if score_pct < 60 else "#10b981"
    score_emoji = "😔" if score_pct < 40 else "🤔" if score_pct < 60 else "🎉" if score_pct < 80 else "🏆"

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {score_color}20, {score_color}10);
                padding: 2rem; border-radius: 16px; text-align: center; border: 2px solid {score_color}40;
                margin: 1rem 0;">
        <div style="font-size: 3rem;">{score_emoji}</div>
        <h2 style="color: {score_color}; margin: 0.5rem 0;">You scored {correct}/{total} ({score_pct:.1f}%)</h2>
        <p style="color: #64748b;">Time taken: {time_taken//60}m {time_taken%60}s</p>
    </div>""", unsafe_allow_html=True)

    if score_pct >= 80:
        st.success("🏆 **Exceptional!** You're well prepared for this section. Keep it up!")
    elif score_pct >= 60:
        st.success("👍 **Good job!** You're on track. Focus on the topics you missed.")
    elif score_pct >= 40:
        st.info("📈 **Making progress!** Review the weak topics below more carefully.")
    else:
        st.warning("💪 **Don't give up!** Everyone starts somewhere. Let's focus on understanding the basics first.")

    if topic_breakdown:
        st.markdown("### 📊 Topic-wise Breakdown")
        for topic_key, stats in topic_breakdown.items():
            t_correct = stats['correct']
            t_total = stats['total']
            t_pct = (t_correct / t_total * 100) if t_total > 0 else 0
            t_color = "#ef4444" if t_pct < 50 else "#f59e0b" if t_pct < 80 else "#10b981"
            st.markdown(f"""
            <div style="background: white; padding: 0.8rem 1rem; border-radius: 10px;
                        border-left: 4px solid {t_color}; margin-bottom: 0.3rem;
                        display: flex; justify-content: space-between; align-items: center;">
                <span style="color: #1a202c; font-weight: 600;">{topic_key}</span>
                <span style="background: {t_color}15; color: {t_color}; padding: 0.2rem 0.6rem;
                             border-radius: 20px; font-weight: 700;">{t_correct}/{t_total}</span>
            </div>""", unsafe_allow_html=True)

    if questions:
        st.markdown("---")
        st.markdown("### 📝 Answer Review")
        for idx, q in enumerate(questions):
            q_id = q['id']
            user_ans = answers.get(q_id, "Not answered")
            is_correct = user_ans == q['correct_option']
            status_icon = "✅" if is_correct else "❌"
            with st.expander(f"{status_icon} Q{idx+1}: {q['question_text'][:80]}..."):
                st.markdown(f"**Question:** {q['question_text']}")
                st.markdown(f"**Your Answer:** {user_ans}")
                st.markdown(f"**Correct Answer:** {q['correct_option']}")
                if q.get('solution_text'):
                    st.info(f"**Solution:** {q['solution_text']}")

    st.markdown("---")
    if st.button("🔄 Take Another Test", use_container_width=True, type="primary"):
        st.session_state.pop('last_test_result', None)
        st.rerun()


def _show_test_history(user_id):
    conn = get_connection()
    results = pd.read_sql_query("""
        SELECT * FROM test_results WHERE user_id=? ORDER BY date DESC LIMIT 20
    """, conn, params=(user_id,))
    conn.close()

    if results.empty:
        st.markdown("""
        <div style="background: #f8fafc; padding: 2rem; border-radius: 14px; text-align: center; border: 2px dashed #cbd5e1;">
            <p style="font-size: 2rem; margin: 0;">📋</p>
            <p style="color: #64748b; margin: 0.5rem 0 0 0;">
                No tests taken yet. Take your first test to see history here!
            </p>
        </div>""", unsafe_allow_html=True)
        return

    st.markdown(f"### Last {len(results)} Tests")
    for _, row in results.iterrows():
        score = row['score']
        color = "#ef4444" if score < 40 else "#f59e0b" if score < 60 else "#10b981"
        date_str = str(row['date'])[:16]
        time_taken_val = row['time_taken'] if pd.notna(row['time_taken']) else 0
        time_str = f"{int(time_taken_val)//60}m {int(time_taken_val)%60}s" if time_taken_val else "N/A"
        subject_label = ""
        if row.get('subject_filter'):
            subject_label = f'<span style="color: #64748b; font-size: 0.8rem;"> • {row["subject_filter"]}</span>'

        st.markdown(f"""
        <div style="background: white; padding: 1rem 1.2rem; border-radius: 12px;
                    border-left: 4px solid {color}; margin-bottom: 0.5rem;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <b style="color: #1a202c;">{row['test_type']}</b>
                    {subject_label}
                    <br><span style="color: #94a3b8; font-size: 0.8rem;">{date_str} • {time_str}</span>
                </div>
                <div style="text-align: right;">
                    <div style="background: {color}; color: white; padding: 0.3rem 1rem;
                                border-radius: 20px; font-weight: 700; font-size: 1.1rem;">
                        {score:.0f}%
                    </div>
                    <span style="color: #94a3b8; font-size: 0.8rem;">{row['correct_answers']}/{row['total_questions']}</span>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)
