import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import time
from database import get_connection
from utils import evaluate_test


# ──────────────────────────────────────────────
# MOCK TEST CONFIGURATIONS
# ──────────────────────────────────────────────
MOCK_CONFIGS = {
    "CBSE": {
        "questions": 25,
        "time_minutes": 60,
        "marks_correct": 1,
        "marks_wrong": 0,
        "max_marks": 25,
        "description": "CBSE Board Pattern • 25 MCQs • 1 mark each • No negative marking",
        "emoji": "📋",
        "color": "#3b82f6"
    },
    "JEE": {
        "questions": 30,
        "time_minutes": 60,
        "marks_correct": 4,
        "marks_wrong": -1,
        "max_marks": 120,
        "description": "JEE Mains Pattern • 30 MCQs • +4 correct / −1 wrong",
        "emoji": "🏆",
        "color": "#f59e0b"
    }
}

SUBJECTS = ["Physics", "Chemistry", "Mathematics"]
SUBJECT_ICONS = {"Physics": "⚛️", "Chemistry": "🧪", "Mathematics": "📐"}


# ══════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ══════════════════════════════════════════════════════════════════════
def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">📝 Exam Simulator</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            Practice Tests • CBSE & JEE Mock Exams • Score Tracking
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state['user_id']
    tab_practice, tab_mock, tab_progress, tab_history = st.tabs([
        "🚀 Practice Tests", "🎯 Mock Exams", "📈 My Progress", "📋 Test History"
    ])
    with tab_practice:
        _show_test_mode(user_id)
    with tab_mock:
        _show_mock_section(user_id)
    with tab_progress:
        _show_progress(user_id)
    with tab_history:
        _show_test_history(user_id)


# ══════════════════════════════════════════════════════════════════════
# TAB 1 — PRACTICE TESTS (existing)
# ══════════════════════════════════════════════════════════════════════
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


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — MOCK EXAMS (CBSE + JEE Pattern)
# ══════════════════════════════════════════════════════════════════════
def _show_mock_section(user_id):

    # Show mock result if available
    if st.session_state.get('last_mock_result'):
        _render_mock_results(st.session_state['last_mock_result'])
        return

    # Show mock test if active
    if st.session_state.get('mock_active'):
        _run_mock_test(user_id)
        return

    # ── Pattern Selection ──
    st.markdown("### 🎯 Choose Exam Pattern")
    col_cbse, col_jee = st.columns(2)

    with col_cbse:
        cfg = MOCK_CONFIGS["CBSE"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe);
                    padding: 1.5rem; border-radius: 16px; border: 2px solid #3b82f6;
                    text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2.5rem;">{cfg['emoji']}</div>
            <h3 style="color: #1e40af; margin: 0.5rem 0;">CBSE Board</h3>
            <p style="color: #3b82f6; font-size: 0.85rem; margin: 0;">{cfg['description']}</p>
            <div style="margin-top: 0.8rem; display: flex; justify-content: center; gap: 1rem;">
                <span style="background: #3b82f620; color: #1e40af; padding: 0.2rem 0.6rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600;">✅ No Negative Marking</span>
            </div>
        </div>""", unsafe_allow_html=True)
        pattern_cbse = st.selectbox("Subject", SUBJECTS,
                                     format_func=lambda s: f"{SUBJECT_ICONS[s]} {s}",
                                     key="cbse_subject")
        if st.button("📋 Start CBSE Mock", use_container_width=True, key="start_cbse"):
            _start_mock(user_id, "CBSE", pattern_cbse)

    with col_jee:
        cfg = MOCK_CONFIGS["JEE"]
        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #fffbeb, #fef3c7);
                    padding: 1.5rem; border-radius: 16px; border: 2px solid #f59e0b;
                    text-align: center; margin-bottom: 1rem;">
            <div style="font-size: 2.5rem;">{cfg['emoji']}</div>
            <h3 style="color: #92400e; margin: 0.5rem 0;">JEE / Competitive</h3>
            <p style="color: #d97706; font-size: 0.85rem; margin: 0;">{cfg['description']}</p>
            <div style="margin-top: 0.8rem; display: flex; justify-content: center; gap: 1rem;">
                <span style="background: #f59e0b20; color: #92400e; padding: 0.2rem 0.6rem; border-radius: 8px; font-size: 0.8rem; font-weight: 600;">⚠️ Negative Marking −1</span>
            </div>
        </div>""", unsafe_allow_html=True)
        pattern_jee = st.selectbox("Subject", SUBJECTS,
                                    format_func=lambda s: f"{SUBJECT_ICONS[s]} {s}",
                                    key="jee_subject")
        if st.button("🏆 Start JEE Mock", use_container_width=True, key="start_jee"):
            _start_mock(user_id, "JEE", pattern_jee)

    # ── Marking scheme info ──
    st.markdown("---")
    st.markdown("### 📌 Marking Scheme")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div style="background: #f0f9ff; padding: 1rem; border-radius: 12px; border: 1px solid #bae6fd;">
            <b style="color: #0369a1;">📋 CBSE Board Pattern</b><br>
            <span style="color: #64748b; font-size: 0.85rem;">
            • 25 questions per subject<br>
            • +1 mark for correct answer<br>
            • 0 marks for wrong answer<br>
            • Total: 25 marks per subject<br>
            • Time: 60 minutes
            </span>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div style="background: #fffbeb; padding: 1rem; border-radius: 12px; border: 1px solid #fcd34d;">
            <b style="color: #92400e;">🏆 JEE Mains Pattern</b><br>
            <span style="color: #64748b; font-size: 0.85rem;">
            • 30 questions per subject<br>
            • +4 marks for correct answer<br>
            • −1 mark for wrong answer<br>
            • Total: 120 marks per subject<br>
            • Time: 60 minutes
            </span>
        </div>""", unsafe_allow_html=True)


def _start_mock(user_id, pattern, subject):
    cfg = MOCK_CONFIGS[pattern]
    conn = get_connection()
    q_df = pd.read_sql_query(
        """SELECT * FROM questions
           WHERE topic_id IN (SELECT id FROM topics WHERE subject=?)
           ORDER BY RANDOM() LIMIT ?""",
        conn, params=(subject, cfg['questions'])
    )
    conn.close()

    if q_df.empty or len(q_df) < 5:
        st.error(f"Not enough questions available for {subject}. Please try another subject.")
        return

    st.session_state['mock_active'] = True
    st.session_state['mock_pattern'] = pattern
    st.session_state['mock_subject'] = subject
    st.session_state['mock_questions'] = q_df.to_dict('records')
    st.session_state['mock_answers'] = {}
    st.session_state['mock_start_time'] = time.time()
    st.session_state['mock_time_limit'] = cfg['time_minutes'] * 60
    st.rerun()


def _run_mock_test(user_id):
    pattern = st.session_state.get('mock_pattern', 'CBSE')
    subject = st.session_state.get('mock_subject', 'Physics')
    cfg = MOCK_CONFIGS[pattern]

    elapsed = int(time.time() - st.session_state['mock_start_time'])
    time_limit = st.session_state.get('mock_time_limit', 3600)
    remaining = max(0, time_limit - elapsed)
    mins_rem = remaining // 60
    secs_rem = remaining % 60
    progress_pct = min(elapsed / time_limit, 1.0) if time_limit > 0 else 0
    timer_color = "#10b981" if progress_pct < 0.5 else "#f59e0b" if progress_pct < 0.8 else "#ef4444"
    pattern_color = cfg['color']

    # Header
    st.markdown(f"""
    <div style="background: white; padding: 1rem 1.5rem; border-radius: 12px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08); margin-bottom: 1rem; border-top: 4px solid {pattern_color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-weight: 700; color: #1a202c; font-size: 1rem;">
                    {cfg['emoji']} {pattern} Mock — {SUBJECT_ICONS.get(subject,'')} {subject}
                </span><br>
                <span style="color: #64748b; font-size: 0.8rem;">{cfg['description']}</span>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.4rem; font-weight: 800; color: {timer_color};">⏱️ {mins_rem:02d}:{secs_rem:02d}</div>
                <div style="color: #64748b; font-size: 0.8rem;">
                    {len(st.session_state.get('mock_answers', {}))} / {len(st.session_state['mock_questions'])} answered
                </div>
            </div>
        </div>
        <div style="background: #f1f5f9; border-radius: 8px; height: 6px; margin-top: 0.5rem; overflow: hidden;">
            <div style="background: {timer_color}; width: {progress_pct*100:.1f}%; height: 100%; border-radius: 8px;"></div>
        </div>
    </div>""", unsafe_allow_html=True)

    if remaining == 0:
        st.warning("⏰ Time's up! Auto-submitting your mock test…")
        _submit_mock(user_id)
        return

    answers = st.session_state.get('mock_answers', {})
    for idx, q in enumerate(st.session_state['mock_questions']):
        q_num = idx + 1
        is_answered = q['id'] in answers
        st.markdown(f"""
        <div style="background: {'#f0fdf4' if is_answered else 'white'}; padding: 1rem 1.2rem;
                    border-radius: 12px; border-left: 4px solid {'#10b981' if is_answered else '#e2e8f0'};
                    margin-bottom: 0.3rem; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
            <p style="margin: 0; color: #64748b; font-size: 0.8rem;">
                Q{q_num} • {q.get('difficulty','Medium')}
                {"• ✅ Answered" if is_answered else "• ⭕ Not answered"}
            </p>
            <h4 style="margin: 0.3rem 0; color: #0f172a;">{q['question_text']}</h4>
        </div>""", unsafe_allow_html=True)
        options = json.loads(q['options']) if isinstance(q['options'], str) else q['options']
        ans = st.radio(f"mock_q_{q_num}", options,
                      key=f"mock_q_{q['id']}", index=None, label_visibility="collapsed")
        if ans is not None:
            answers[q['id']] = ans
        st.markdown("")

    st.session_state['mock_answers'] = answers

    col_submit, col_cancel = st.columns([3, 1])
    with col_submit:
        if st.button("✅ Submit Mock Test", use_container_width=True, type="primary"):
            _submit_mock(user_id)
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            for k in ('mock_active', 'mock_questions', 'mock_answers',
                      'mock_start_time', 'mock_time_limit', 'mock_pattern', 'mock_subject'):
                st.session_state.pop(k, None)
            st.rerun()


def _submit_mock(user_id):
    pattern = st.session_state.get('mock_pattern', 'CBSE')
    subject = st.session_state.get('mock_subject', 'Physics')
    cfg = MOCK_CONFIGS[pattern]
    questions = st.session_state.get('mock_questions', [])
    answers = st.session_state.get('mock_answers', {})
    time_taken = int(time.time() - st.session_state.get('mock_start_time', time.time()))

    correct = 0
    wrong = 0
    not_attempted = 0
    topic_breakdown = {}

    for q in questions:
        q_id = q['id']
        user_ans = answers.get(q_id)
        # Get topic name for breakdown
        conn = get_connection()
        t_row = conn.execute(
            "SELECT topic_name FROM topics WHERE id=?", (q.get('topic_id', 0),)
        ).fetchone()
        conn.close()
        topic_key = t_row['topic_name'] if t_row else "Unknown"

        if topic_key not in topic_breakdown:
            topic_breakdown[topic_key] = {'correct': 0, 'wrong': 0, 'total': 0}
        topic_breakdown[topic_key]['total'] += 1

        if user_ans is None:
            not_attempted += 1
        elif user_ans == q['correct_option']:
            correct += 1
            topic_breakdown[topic_key]['correct'] += 1
        else:
            wrong += 1
            topic_breakdown[topic_key]['wrong'] += 1

    total = len(questions)
    marks_obtained = correct * cfg['marks_correct'] + wrong * cfg['marks_wrong']
    marks_obtained = max(0, marks_obtained)  # no negative total
    max_marks = total * cfg['marks_correct']
    score_pct = (marks_obtained / max_marks * 100) if max_marks > 0 else 0

    # Save to test_results table
    test_type_label = f"{pattern} Mock - {subject}"
    conn = get_connection()
    conn.execute("""
        INSERT INTO test_results
        (user_id, test_type, subject_filter, total_questions, correct_answers, time_taken, score, topic_breakdown)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, test_type_label, subject, total, correct, time_taken,
          round(score_pct, 2), json.dumps(topic_breakdown)))
    conn.commit()
    conn.close()

    st.session_state['last_mock_result'] = {
        'pattern': pattern,
        'subject': subject,
        'correct': correct,
        'wrong': wrong,
        'not_attempted': not_attempted,
        'total': total,
        'marks_obtained': marks_obtained,
        'max_marks': max_marks,
        'score_pct': score_pct,
        'time_taken': time_taken,
        'topic_breakdown': topic_breakdown,
        'questions': questions,
        'answers': answers,
        'cfg': cfg
    }
    for k in ('mock_active', 'mock_questions', 'mock_answers',
              'mock_start_time', 'mock_time_limit', 'mock_pattern', 'mock_subject'):
        st.session_state.pop(k, None)
    st.rerun()


def _render_mock_results(result):
    pattern = result['pattern']
    subject = result['subject']
    cfg = result['cfg']
    correct = result['correct']
    wrong = result['wrong']
    not_attempted = result['not_attempted']
    total = result['total']
    marks = result['marks_obtained']
    max_marks = result['max_marks']
    score_pct = result['score_pct']
    time_taken = result['time_taken']
    topic_breakdown = result.get('topic_breakdown', {})
    questions = result.get('questions', [])
    answers = result.get('answers', {})

    score_color = "#ef4444" if score_pct < 40 else "#f59e0b" if score_pct < 60 else "#10b981"
    score_emoji = "😔" if score_pct < 40 else "🤔" if score_pct < 60 else "🎉" if score_pct < 80 else "🏆"
    pattern_color = cfg['color']

    st.markdown(f"""
    <div style="background: linear-gradient(135deg, {pattern_color}15, {pattern_color}08);
                padding: 2rem; border-radius: 16px; text-align: center;
                border: 2px solid {pattern_color}40; margin: 1rem 0;">
        <div style="font-size: 2.5rem;">{score_emoji}</div>
        <h2 style="color: {score_color}; margin: 0.5rem 0;">
            {cfg['emoji']} {pattern} Mock — {SUBJECT_ICONS.get(subject,'')} {subject}
        </h2>
        <div style="font-size: 2.5rem; font-weight: 900; color: {score_color};">
            {marks}/{max_marks} marks
        </div>
        <p style="color: #64748b; margin: 0.3rem 0;">Score: {score_pct:.1f}% &nbsp;|&nbsp; Time: {time_taken//60}m {time_taken%60}s</p>
    </div>""", unsafe_allow_html=True)

    # Stats row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("✅ Correct", f"{correct}", f"+{correct * cfg['marks_correct']} marks")
    with c2:
        st.metric("❌ Wrong", f"{wrong}",
                  f"{wrong * cfg['marks_wrong']} marks" if cfg['marks_wrong'] < 0 else "0 marks")
    with c3:
        st.metric("⭕ Not Attempted", f"{not_attempted}", "0 marks")

    # Feedback
    if score_pct >= 80:
        st.success("🏆 **Excellent!** You are well prepared for this subject!")
    elif score_pct >= 60:
        st.success("👍 **Good performance!** Focus on the weak topics below.")
    elif score_pct >= 40:
        st.info("📈 **Keep going!** Review the topics below and try again.")
    else:
        st.warning("💪 **More practice needed.** Study these topics carefully before the next attempt.")

    # Topic breakdown
    if topic_breakdown:
        st.markdown("### 📊 Topic-wise Breakdown")
        for topic_key, stats in topic_breakdown.items():
            t_correct = stats.get('correct', 0)
            t_wrong = stats.get('wrong', 0)
            t_total = stats.get('total', 0)
            t_pct = (t_correct / t_total * 100) if t_total > 0 else 0
            t_color = "#ef4444" if t_pct < 50 else "#f59e0b" if t_pct < 80 else "#10b981"
            st.markdown(f"""
            <div style="background: white; padding: 0.8rem 1rem; border-radius: 10px;
                        border-left: 4px solid {t_color}; margin-bottom: 0.4rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #1a202c; font-weight: 600;">{topic_key}</span>
                    <div style="display: flex; gap: 0.5rem; align-items: center;">
                        <span style="color: #10b981; font-size: 0.8rem;">✅ {t_correct}</span>
                        <span style="color: #ef4444; font-size: 0.8rem;">❌ {t_wrong}</span>
                        <span style="background: {t_color}15; color: {t_color}; padding: 0.2rem 0.6rem;
                                     border-radius: 20px; font-weight: 700; font-size: 0.9rem;">
                            {t_pct:.0f}%
                        </span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    # Answer review
    if questions:
        st.markdown("---")
        st.markdown("### 📝 Answer Review")
        for idx, q in enumerate(questions):
            q_id = q['id']
            user_ans = answers.get(q_id, "Not answered")
            is_correct = user_ans == q['correct_option']
            not_ans = user_ans == "Not answered"
            status_icon = "✅" if is_correct else ("⭕" if not_ans else "❌")
            with st.expander(f"{status_icon} Q{idx+1}: {str(q['question_text'])[:80]}..."):
                st.markdown(f"**Question:** {q['question_text']}")
                st.markdown(f"**Your Answer:** {user_ans}")
                st.markdown(f"**Correct Answer:** {q['correct_option']}")
                if q.get('solution_text'):
                    st.info(f"**Solution:** {q['solution_text']}")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Try Another Mock", use_container_width=True, type="primary"):
            st.session_state.pop('last_mock_result', None)
            st.rerun()
    with col2:
        if st.button("📈 View My Progress", use_container_width=True):
            st.session_state.pop('last_mock_result', None)
            st.rerun()


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — MY PROGRESS
# ══════════════════════════════════════════════════════════════════════
def _show_progress(user_id):
    conn = get_connection()
    results = pd.read_sql_query("""
        SELECT test_type, subject_filter, score, correct_answers, total_questions,
               time_taken, date
        FROM test_results
        WHERE user_id=?
        ORDER BY date ASC
    """, conn, params=(user_id,))
    conn.close()

    if results.empty:
        st.markdown("""
        <div style="background: #f8fafc; padding: 3rem; border-radius: 14px;
                    text-align: center; border: 2px dashed #cbd5e1;">
            <p style="font-size: 2.5rem; margin: 0;">📈</p>
            <h3 style="color: #64748b;">No tests taken yet</h3>
            <p style="color: #94a3b8;">Take a Practice Test or Mock Exam to see your progress here!</p>
        </div>""", unsafe_allow_html=True)
        return

    results['date'] = pd.to_datetime(results['date'])
    results['test_num'] = range(1, len(results) + 1)

    # ── Summary stats ──
    total_tests = len(results)
    avg_score = results['score'].mean()
    best_score = results['score'].max()
    latest_score = results.iloc[-1]['score']

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📝 Tests Taken", total_tests)
    with c2:
        st.metric("📊 Avg Score", f"{avg_score:.1f}%")
    with c3:
        st.metric("🏆 Best Score", f"{best_score:.1f}%")
    with c4:
        trend = latest_score - avg_score
        st.metric("🎯 Latest Score", f"{latest_score:.1f}%",
                  f"{trend:+.1f}% vs avg")

    st.markdown("---")

    # ── Filter by subject ──
    all_subjects = ["All"] + sorted(results['subject_filter'].dropna().unique().tolist())
    selected_subject = st.selectbox("Filter by Subject", all_subjects, key="progress_subject")

    filtered = results.copy()
    if selected_subject != "All":
        filtered = filtered[filtered['subject_filter'] == selected_subject]

    if filtered.empty:
        st.info(f"No tests found for {selected_subject}.")
        return

    filtered = filtered.reset_index(drop=True)
    filtered['test_num'] = range(1, len(filtered) + 1)

    # ── Score over time chart ──
    st.markdown("### 📈 Score Trend")

    # Color by test type (Mock vs Practice)
    filtered['type_label'] = filtered['test_type'].apply(
        lambda x: "CBSE Mock" if "CBSE" in str(x)
        else ("JEE Mock" if "JEE" in str(x) else "Practice Test")
    )

    color_map = {
        "CBSE Mock": "#3b82f6",
        "JEE Mock": "#f59e0b",
        "Practice Test": "#8b5cf6"
    }

    fig = go.Figure()
    for ttype, color in color_map.items():
        subset = filtered[filtered['type_label'] == ttype]
        if subset.empty:
            continue
        fig.add_trace(go.Scatter(
            x=subset['test_num'],
            y=subset['score'],
            mode='lines+markers',
            name=ttype,
            line=dict(color=color, width=2.5),
            marker=dict(size=9, color=color, line=dict(width=2, color='white')),
            hovertemplate=(
                f"<b>{ttype}</b><br>"
                "Test #%{x}<br>"
                "Score: %{y:.1f}%<br>"
                "<extra></extra>"
            )
        ))

    # Add target line at 60%
    fig.add_hline(y=60, line_dash="dash", line_color="#10b981",
                  annotation_text="Target: 60%", annotation_position="bottom right")

    fig.update_layout(
        xaxis_title="Test Number",
        yaxis_title="Score (%)",
        yaxis=dict(range=[0, 105]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10),
        height=350
    )
    fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
    fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
    st.plotly_chart(fig, use_container_width=True)

    # ── Subject-wise average (bar chart) ──
    st.markdown("### 📊 Subject-wise Average Score")
    subj_avg = results.groupby('subject_filter')['score'].mean().reset_index()
    subj_avg.columns = ['Subject', 'Average Score']
    subj_avg = subj_avg[subj_avg['Subject'].notna()]

    if not subj_avg.empty:
        bar_colors = ["#3b82f6" if s == "Physics"
                      else "#10b981" if s == "Chemistry"
                      else "#8b5cf6" for s in subj_avg['Subject']]
        fig2 = go.Figure(go.Bar(
            x=subj_avg['Subject'],
            y=subj_avg['Average Score'],
            marker_color=bar_colors,
            text=subj_avg['Average Score'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside'
        ))
        fig2.update_layout(
            yaxis=dict(range=[0, 110], title="Average Score (%)"),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=10, r=10, t=20, b=10),
            height=280
        )
        fig2.update_xaxes(showgrid=False)
        fig2.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        st.plotly_chart(fig2, use_container_width=True)

    # ── Recent tests table ──
    st.markdown("### 📋 Recent Test Scores")
    display_df = filtered[['test_num', 'test_type', 'subject_filter', 'score',
                            'correct_answers', 'total_questions', 'date']].copy()
    display_df.columns = ['#', 'Test Type', 'Subject', 'Score %',
                          'Correct', 'Total', 'Date']
    display_df['Score %'] = display_df['Score %'].apply(lambda x: f"{x:.1f}%")
    display_df['Date'] = display_df['Date'].dt.strftime('%d %b %Y, %H:%M')
    st.dataframe(display_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 4 — TEST HISTORY (existing)
# ══════════════════════════════════════════════════════════════════════
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
