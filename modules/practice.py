import streamlit as st
import pandas as pd
import json
import random
from database import get_connection
from utils import ask_ai, add_bookmark, remove_bookmark, is_bookmarked, generate_questions_ai, get_bookmarked_questions

def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">&#x270D;&#xFE0F; Practice Engine</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            170+ questions &bull; AI-generated extras &bull; Step-by-step solutions &bull; Bookmark tough ones
        </p>
    </div>
    """, unsafe_allow_html=True)

    user_id = st.session_state['user_id']

    mode = st.radio("Select Mode", ["Practice Questions", "Bookmarked Questions"], horizontal=True)

    if mode == "Bookmarked Questions":
        _show_bookmarks(user_id)
        return

    conn = get_connection()
    topics_df = pd.read_sql_query(
        "SELECT id, subject, chapter, topic_name FROM topics ORDER BY subject, chapter, topic_name", conn)

    col1, col2, col3 = st.columns([2, 2, 1])

    with col1:
        subject_filter = st.selectbox("Filter by Subject",
                                      ["All Subjects"] + sorted(topics_df["subject"].unique().tolist()))

    filtered_df = topics_df[topics_df["subject"] == subject_filter] if subject_filter != "All Subjects" else topics_df
    topic_options = [f"{r['subject']} -- {r['topic_name']}" for _, r in filtered_df.iterrows()]
    topic_map = {f"{r['subject']} -- {r['topic_name']}": r for _, r in filtered_df.iterrows()}

    with col2:
        selected_display = st.selectbox("Select Topic", topic_options)

    with col3:
        difficulty = st.select_slider("Difficulty", options=["Easy", "Medium", "Hard", "All"], value="All")

    selected_topic_data = topic_map[selected_display]
    topic_id = int(selected_topic_data["id"])
    topic_name = selected_topic_data["topic_name"]
    subject = selected_topic_data["subject"]
    chapter = selected_topic_data["chapter"]

    # Detect topic/difficulty change and reset session
    session_key = f"{topic_id}_{difficulty}"
    if st.session_state.get("practice_session_key") != session_key:
        for k in ["practice_queue", "practice_index", "practice_score",
                  "practice_answered", "practice_show_sol", "practice_session_key"]:
            st.session_state.pop(k, None)

    # Count available questions
    if difficulty == "All":
        q_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM questions WHERE topic_id=?", conn, params=(topic_id,)).iloc[0]["cnt"]
    else:
        q_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM questions WHERE topic_id=? AND difficulty=?",
            conn, params=(topic_id, difficulty)).iloc[0]["cnt"]

    total_all = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM questions WHERE topic_id=?", conn, params=(topic_id,)).iloc[0]["cnt"]

    if total_all == 0:
        st.warning(f"No questions yet for **{topic_name}**. Use 'Generate More AI Questions' below!")
    elif q_count == 0:
        st.info(f"No **{difficulty}** questions for this topic ({total_all} in other difficulties). Change difficulty or generate more.")
    else:
        st.caption(f"**{q_count}** questions available | {total_all} total for topic")

    col_gen1, col_gen2 = st.columns([1, 1])
    with col_gen1:
        start_clicked = st.button("Start / Restart Practice", use_container_width=True,
                                  disabled=(q_count == 0), type="primary")
    with col_gen2:
        gen_clicked = st.button("Generate More AI Questions", use_container_width=True,
                                help="AI creates 5 fresh questions for this topic")

    if gen_clicked:
        diff_for_gen = difficulty if difficulty != "All" else "Medium"
        with st.spinner("AI is creating new questions..."):
            result = generate_questions_ai(topic_name, subject, chapter, diff_for_gen, count=5, user_id=user_id)
            if result:
                st.success(f"Generated {len(result)} new questions!")
                for k in ["practice_queue", "practice_index", "practice_score",
                          "practice_answered", "practice_show_sol", "practice_session_key"]:
                    st.session_state.pop(k, None)
                st.rerun()
            else:
                st.warning("Could not generate questions. Check your API key in .env")

    if start_clicked and q_count > 0:
        if difficulty == "All":
            q_df = pd.read_sql_query(
                "SELECT * FROM questions WHERE topic_id=?", conn, params=(topic_id,))
        else:
            q_df = pd.read_sql_query(
                "SELECT * FROM questions WHERE topic_id=? AND difficulty=?",
                conn, params=(topic_id, difficulty))

        queue = q_df.to_dict("records")
        random.shuffle(queue)
        st.session_state["practice_queue"] = queue
        st.session_state["practice_index"] = 0
        st.session_state["practice_score"] = {"correct": 0, "wrong": 0}
        st.session_state["practice_answered"] = False
        st.session_state["practice_show_sol"] = False
        st.session_state["practice_session_key"] = session_key
        st.rerun()

    conn.close()

    # Active practice session
    if "practice_queue" not in st.session_state:
        # Show a motivational empty state
        st.markdown("""
<div style="background: linear-gradient(135deg, #f8fafc, #eef2ff); padding: 2.5rem 2rem; 
            border-radius: 16px; text-align: center; border: 2px dashed #c7d2fe; margin-top: 1rem;">
    <div style="font-size: 3rem; margin-bottom: 0.5rem;">✍️</div>
    <h3 style="color: #4F46E5; margin: 0 0 0.5rem 0;">Ready to Practice?</h3>
    <p style="color: #64748b; margin: 0; font-size: 0.95rem;">
        Select a topic above and click <b>Start / Restart Practice</b> to begin.
        <br>Each session tracks your score and helps identify weak spots.
    </p>
    <div style="display: flex; gap: 1rem; justify-content: center; margin-top: 1.2rem; flex-wrap: wrap;">
        <div style="background: white; padding: 0.6rem 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <span style="color: #10b981; font-weight: 700;">✅ Step-by-step</span><br>
            <span style="color: #64748b; font-size: 0.8rem;">detailed solutions</span>
        </div>
        <div style="background: white; padding: 0.6rem 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <span style="color: #4F46E5; font-weight: 700;">🔖 Bookmark</span><br>
            <span style="color: #64748b; font-size: 0.8rem;">tough questions</span>
        </div>
        <div style="background: white; padding: 0.6rem 1rem; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.06);">
            <span style="color: #f59e0b; font-weight: 700;">🤖 AI explain</span><br>
            <span style="color: #64748b; font-size: 0.8rem;">on-demand help</span>
        </div>
    </div>
</div>""", unsafe_allow_html=True)
        return

    queue = st.session_state["practice_queue"]
    idx = st.session_state["practice_index"]
    score = st.session_state["practice_score"]
    total_in_session = len(queue)

    if idx >= total_in_session:
        _show_session_summary(score, total_in_session, topic_name)
        return

    q = queue[idx]
    answered = st.session_state.get("practice_answered", False)

    st.markdown("---")

    # Progress bar + score
    progress_pct = idx / total_in_session
    st.markdown(
        "<div style='background:white;padding:1rem 1.2rem;border-radius:12px;"
        "box-shadow:0 2px 8px rgba(0,0,0,0.05);margin-bottom:1rem;'>"
        "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem;'>"
        f"<span style='font-weight:700;color:#1a202c;'>Question {idx+1} of {total_in_session}</span>"
        "<div style='display:flex;gap:1rem;'>"
        f"<span style='color:#10b981;font-weight:600;'>Correct: {score['correct']}</span>"
        f"<span style='color:#ef4444;font-weight:600;'>Wrong: {score['wrong']}</span>"
        "</div></div>"
        "<div style='background:#e2e8f0;border-radius:6px;height:8px;overflow:hidden;'>"
        f"<div style='background:linear-gradient(90deg,#4F46E5,#7C3AED);width:{progress_pct*100:.0f}%;height:100%;border-radius:6px;'></div>"
        "</div></div>",
        unsafe_allow_html=True
    )

    # Question card
    diff_colors = {"Easy": "#10b981", "Medium": "#f59e0b", "Hard": "#ef4444"}
    q_color = diff_colors.get(q.get("difficulty", "Medium"), "#6b7280")
    q_text = q["question_text"]
    q_diff = q.get("difficulty", "")
    q_type = q.get("q_type", "MCQ")

    st.markdown(
        f"<div style='background:white;padding:1.5rem;border-radius:14px;"
        f"border-left:5px solid {q_color};box-shadow:0 4px 15px rgba(0,0,0,0.05);margin-bottom:1rem;'>"
        f"<div style='display:flex;gap:0.5rem;margin-bottom:0.8rem;'>"
        f"<span style='background:{q_color}20;color:{q_color};padding:0.2rem 0.6rem;border-radius:6px;font-size:0.75rem;font-weight:600;'>{q_diff}</span>"
        f"<span style='background:#f1f5f9;color:#475569;padding:0.2rem 0.6rem;border-radius:6px;font-size:0.75rem;'>{q_type}</span>"
        f"</div>"
        f"<h3 style='margin:0;color:#0f172a;line-height:1.6;'>{q_text}</h3>"
        f"</div>",
        unsafe_allow_html=True
    )

    options = json.loads(q["options"]) if isinstance(q["options"], str) else q["options"]

    if not answered:
        selected = st.radio("Choose your answer:", options, index=None, key=f"ans_{idx}")
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            if st.button("Submit Answer", use_container_width=True, type="primary"):
                if selected:
                    st.session_state["practice_answered"] = True
                    st.session_state["practice_last_answer"] = selected
                    st.session_state["practice_show_sol"] = False
                    if selected == q["correct_option"]:
                        st.session_state["practice_score"]["correct"] += 1
                    else:
                        st.session_state["practice_score"]["wrong"] += 1
                    st.rerun()
                else:
                    st.warning("Please select an option first!")
        with c2:
            if st.button("Hint", use_container_width=True):
                hint = q.get("hint", "")
                st.info(hint if hint else "Think about the formula or main concept for this topic.")
        with c3:
            q_id = q.get("id")
            if q_id:
                bookmarked = is_bookmarked(user_id, q_id)
                if st.button("Saved" if bookmarked else "Save", use_container_width=True):
                    if bookmarked:
                        remove_bookmark(user_id, q_id)
                    else:
                        add_bookmark(user_id, q_id)
                    st.rerun()

    else:
        last_answer = st.session_state.get("practice_last_answer", "")
        correct = (last_answer == q["correct_option"])

        for opt in options:
            if opt == q["correct_option"]:
                st.success(f"CORRECT: {opt}")
            elif opt == last_answer and not correct:
                st.error(f"YOUR ANSWER: {opt}")
            else:
                st.markdown(f"- {opt}")

        if correct:
            st.success("Correct! Well done!")
        else:
            st.error(f"Wrong. Correct answer was: **{q['correct_option']}**")

        if st.session_state.get("practice_show_sol", False):
            sol = q["solution_text"]
            st.markdown("**Step-by-Step Solution:**")
            st.info(sol)
            if st.button("Still confused? Ask AI to explain differently", use_container_width=True):
                with st.spinner("AI is preparing a detailed explanation..."):
                    prompt = (
                        f"A Class 12 student is struggling with this {subject} question.\n\n"
                        f"Question: {q['question_text']}\n"
                        f"Correct Answer: {q['correct_option']}\n"
                        f"Solution: {q['solution_text']}\n\n"
                        "Please:\n"
                        "1. Explain the underlying CONCEPT first (in very simple words)\n"
                        "2. Re-solve step by step with MORE detail\n"
                        "3. Explain WHY the wrong options are wrong\n"
                        "4. Give a similar but simpler practice problem\n\n"
                        "Be extremely patient and encouraging."
                    )
                    response = ask_ai(prompt, user_id=user_id)
                    st.markdown("**AI Teacher:**")
                    st.markdown(response)

        st.markdown("<br>", unsafe_allow_html=True)
        ca, cb, cc = st.columns([1, 1, 1])
        with ca:
            if not st.session_state.get("practice_show_sol", False):
                if st.button("Show Solution", use_container_width=True):
                    st.session_state["practice_show_sol"] = True
                    st.rerun()
        with cb:
            q_id = q.get("id")
            if q_id:
                bookmarked = is_bookmarked(user_id, q_id)
                if st.button("Saved" if bookmarked else "Save", use_container_width=True, key="bm2"):
                    if bookmarked:
                        remove_bookmark(user_id, q_id)
                    else:
                        add_bookmark(user_id, q_id)
                    st.rerun()
        with cc:
            next_label = "Next Question" if idx + 1 < total_in_session else "See Results"
            if st.button(next_label, use_container_width=True, type="primary"):
                st.session_state["practice_index"] += 1
                st.session_state["practice_answered"] = False
                st.session_state["practice_show_sol"] = False
                st.session_state.pop("practice_last_answer", None)
                st.rerun()


def _show_session_summary(score, total, topic_name):
    correct = score["correct"]
    wrong = score["wrong"]
    pct = int(correct / total * 100) if total > 0 else 0

    if pct >= 80:
        emoji, grade, color = "Trophy", "Excellent!", "#10b981"
        msg = "Outstanding! You have mastered this topic."
    elif pct >= 60:
        emoji, grade, color = "Thumbs Up", "Good Job!", "#f59e0b"
        msg = "Solid effort! Review the ones you missed and try again."
    elif pct >= 40:
        emoji, grade, color = "Books", "Keep Practising", "#f59e0b"
        msg = "You are getting there! Go through the solutions carefully."
    else:
        emoji, grade, color = "Muscle", "Need More Practice", "#ef4444"
        msg = "Do not give up! Revise the concepts and try again."

    st.markdown("---")
    st.markdown(f"## Practice Complete: {topic_name}")
    c1, c2, c3 = st.columns(3)
    c1.metric("Correct", correct)
    c2.metric("Wrong", wrong)
    c3.metric("Score", f"{pct}%")
    st.markdown(f"**{grade}** — {msg}")

    if st.button("Practice Again (same topic)", use_container_width=True, type="primary"):
        for k in ["practice_queue", "practice_index", "practice_score",
                  "practice_answered", "practice_show_sol", "practice_session_key", "practice_last_answer"]:
            st.session_state.pop(k, None)
        st.rerun()


def _show_bookmarks(user_id):
    bm_df = get_bookmarked_questions(user_id)

    if bm_df.empty:
        st.info("No bookmarked questions yet. Save tricky questions while practising to review them later!")
        return

    st.markdown(f"### You have **{len(bm_df)}** saved questions")

    for idx, row in bm_df.iterrows():
        with st.expander(f"**{row['subject']} -- {row['topic_name']}**: {row['question_text'][:80]}..."):
            st.markdown(f"**Q:** {row['question_text']}")
            options = json.loads(row["options"]) if isinstance(row["options"], str) else row["options"]
            for opt in options:
                marker = "CORRECT" if opt == row["correct_option"] else "-"
                st.markdown(f"- [{marker}] {opt}")
            st.markdown(f"**Solution:** {row['solution_text']}")
            if st.button("Remove Bookmark", key=f"rm_bm_{row['id']}"):
                remove_bookmark(user_id, row["id"])
                st.rerun()
