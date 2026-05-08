import streamlit as st
import pandas as pd
from database import get_connection
from utils import ask_ai

def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">📚 Deep Concept Learning</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            Master concepts from scratch • AI mentor at your service • Step-by-step explanations
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    conn = get_connection()
    subjects_df = pd.read_sql_query("SELECT DISTINCT subject FROM topics ORDER BY subject", conn)
    
    if subjects_df.empty:
        st.warning("No subjects available in the database.")
        return
    
    # Subject/Chapter/Topic selectors
    subject_icons = {'Physics': '⚛️', 'Chemistry': '🧪', 'Mathematics': '📐'}
    
    colA, colB, colC = st.columns(3)
    with colA:
        subject_list = subjects_df['subject'].tolist()
        subject = st.selectbox("📖 Subject", subject_list, 
                               format_func=lambda x: f"{subject_icons.get(x, '📖')} {x}")
    
    chapters_df = pd.read_sql_query("SELECT DISTINCT chapter FROM topics WHERE subject=?", conn, params=(subject,))
    with colB:
        chapter = st.selectbox("📑 Chapter", chapters_df['chapter'].tolist())
    
    topics_df = pd.read_sql_query("SELECT * FROM topics WHERE subject=? AND chapter=?", conn, params=(subject, chapter))
    topic_names = ["📖 Full Chapter Overview"] + topics_df['topic_name'].tolist()
    
    with colC:
        topic = st.selectbox("🎯 Topic", topic_names)
    
    st.markdown("---")
    user_id = st.session_state.get('user_id')
    
    # Quick topic stats
    if topic != "📖 Full Chapter Overview":
        selected_topic = topics_df[topics_df['topic_name'] == topic].iloc[0]
        q_count = pd.read_sql_query(
            "SELECT COUNT(*) as cnt FROM questions WHERE topic_id=?", conn, params=(int(selected_topic['id']),)
        ).iloc[0]['cnt']
        diff_colors = {'Easy': '#10b981', 'Medium': '#f59e0b', 'Hard': '#ef4444'}
        d_color = diff_colors.get(selected_topic['difficulty'], '#6b7280')
        st.markdown(f"""
<div style="background: white; padding: 0.7rem 1.2rem; border-radius: 10px; margin-bottom: 0.5rem;
            box-shadow: 0 2px 8px rgba(0,0,0,0.04); display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;">
    <span style="background: {d_color}15; color: {d_color}; padding: 0.2rem 0.7rem; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">
        {selected_topic['difficulty']}
    </span>
    <span style="background: #eef2ff; color: #4338ca; padding: 0.2rem 0.7rem; border-radius: 6px; font-size: 0.8rem;">
        📌 CBSE: {selected_topic['cbse_weightage']}/10
    </span>
    <span style="background: #fef3c7; color: #b45309; padding: 0.2rem 0.7rem; border-radius: 6px; font-size: 0.8rem;">
        🎯 JEE: {selected_topic['jee_weightage']}/10
    </span>
    <span style="background: #f0fdf4; color: #059669; padding: 0.2rem 0.7rem; border-radius: 6px; font-size: 0.8rem;">
        ❓ {q_count} practice questions available
    </span>
</div>""", unsafe_allow_html=True)
    
    if topic == "📖 Full Chapter Overview":
        _show_chapter_view(subject, chapter, topics_df, user_id)
    else:
        selected_topic = topics_df[topics_df['topic_name'] == topic].iloc[0]
        _show_topic_view(subject, chapter, selected_topic, user_id)
    
    conn.close()


def _show_chapter_view(subject, chapter, topics_df, user_id):
    """Full chapter overview with all topics."""
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                margin-bottom: 1rem;">
        <h2 style="margin: 0 0 0.5rem 0; color: #1a202c;">📑 {chapter}</h2>
        <p style="color: #64748b; margin: 0;">Complete chapter guide with {len(topics_df)} topics</p>
    </div>""", unsafe_allow_html=True)
    
    difficulty_colors = {'Easy': '#10b981', 'Medium': '#f59e0b', 'Hard': '#ef4444'}
    
    for idx, row in topics_df.iterrows():
        diff_color = difficulty_colors.get(row['difficulty'], '#6b7280')
        
        with st.expander(f"**{idx+1}. {row['topic_name']}** — {row['difficulty']}"):
            st.markdown(f"**💡 Core Concept:** {row['description']}")
            
            if row['formula_sheet']:
                st.markdown("**📐 Key Formula:**")
                st.latex(row['formula_sheet'])
            
            if row['key_concepts']:
                st.markdown(f"**🔑 Key Concepts:** {row['key_concepts']}")
            
            if row['common_mistakes']:
                st.warning(f"⚠️ **Common Mistake:** {row['common_mistakes']}")
            
            if row['tips']:
                st.success(f"💡 **Pro Tip:** {row['tips']}")
            
            st.markdown(f"""
            <div style="display: flex; gap: 1rem; margin-top: 0.5rem;">
                <span style="background: #eef2ff; color: #4338ca; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem;">
                    CBSE: {row['cbse_weightage']}/10
                </span>
                <span style="background: #fef3c7; color: #b45309; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.8rem;">
                    JEE: {row['jee_weightage']}/10
                </span>
            </div>""", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 🤖 AI Chapter Crash-Course")
    st.markdown("Want your AI mentor to teach this entire chapter as one cohesive story?")
    
    if st.button("🪄 Generate Full Chapter Story-Mode Lesson", use_container_width=True):
        with st.spinner("✍️ Writing a chapter crash-course for you..."):
            all_topics = ", ".join(topics_df['topic_name'].tolist())
            all_formulas = "; ".join([f"{r['topic_name']}: {r['formula_sheet']}" for _, r in topics_df.iterrows() if r['formula_sheet']])
            
            prompt = f"""You are an extremely patient, world-class empathetic tutor teaching a WEAK student.
I am a 12th-grade student studying {subject} for JEE 2027. I struggle with this chapter.

Please teach me the entire chapter "{chapter}" as a cohesive story that flows naturally from one concept to the next.

Sub-topics to cover: {all_topics}
Key formulas: {all_formulas}

Structure your lesson in markdown with:
1. **The Big Picture** - Why this chapter matters for CBSE & JEE (2-3 lines)
2. **Concept Flow** - Teach each topic connecting them logically, using everyday analogies
3. **Formula Summary** - A clean table of all formulas with what each symbol means
4. **Common Exam Traps** - Top 5 mistakes students make (and how to avoid them)
5. **Quick Revision Checklist** - 10 one-liner points to revise before exam
6. **Motivation** - End with encouraging words

Use simple language. Explain like I'm hearing this for the first time."""
            
            response = ask_ai(prompt, user_id=user_id)
            st.success("✅ Crash-Course Generated!")
            st.markdown("---")
            st.markdown(response)


def _show_topic_view(subject, chapter, topic, user_id):
    """Detailed view for a single topic."""
    difficulty_colors = {'Easy': '#10b981', 'Medium': '#f59e0b', 'Hard': '#ef4444'}
    diff_color = difficulty_colors.get(topic['difficulty'], '#6b7280')
    
    st.markdown(f"""
    <div style="background: white; padding: 1.5rem; border-radius: 14px; box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                margin-bottom: 1rem;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h2 style="margin: 0; color: #1a202c;">{topic['topic_name']}</h2>
            <div style="display: flex; gap: 0.5rem;">
                <span style="background: {diff_color}15; color: {diff_color}; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.8rem; font-weight: 600;">{topic['difficulty']}</span>
                <span style="background: #eef2ff; color: #4338ca; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.8rem;">CBSE: {topic['cbse_weightage']}/10</span>
                <span style="background: #fef3c7; color: #b45309; padding: 0.3rem 0.8rem; 
                             border-radius: 20px; font-size: 0.8rem;">JEE: {topic['jee_weightage']}/10</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📖 Concept & AI Mentor", "📝 Formula Sheet", "💡 Tips & Tricks"])
    
    with tab1:
        # Core concept
        st.info(f"💡 **Definition:** {topic['description']}")
        
        if topic['key_concepts']:
            st.markdown(f"**🔑 Key Concepts:** {topic['key_concepts']}")
        
        st.markdown("---")
        
        # AI Generated Lesson
        st.markdown("### 🧑‍🏫 Full AI Lesson (From Scratch)")
        st.caption("Perfect for weak students — starts from zero and builds up step by step")
        
        if st.button("🪄 Generate Deep-Dive Lesson", use_container_width=True, key="deep_dive"):
            with st.spinner("🧠 Your AI tutor is preparing a personalized lesson..."):
                prompt = f"""You are an extremely patient, world-class empathetic tutor.
I am a 12th-grade WEAK student studying {subject} ({chapter}) preparing for JEE 2027.
I need you to teach me "{topic['topic_name']}" completely from scratch.

The core concept is: {topic['description']}
Key formula: {topic['formula_sheet']}

Please format in markdown and include:
1. **The Core Concept (ELI10)**: Explain as if I'm 10 years old
2. **Real-Life Analogy**: Give an everyday example I can relate to
3. **The Math Behind It**: Walk through the formula {topic['formula_sheet']} step by step
4. **Solved Example**: Work through a JEE-level problem VERY slowly
5. **Second Example**: Work through another problem of different type
6. **Common Traps**: What mistakes do students usually make?
7. **Quick Memory Trick**: A mnemonic or trick to remember key facts
8. **YouTube Recommendations**: Suggest 2 specific search terms for Physics Wallah or Khan Academy

Be encouraging throughout. End with motivational words."""
                
                response = ask_ai(prompt, user_id=user_id)
                st.success("✅ Lesson Generated!")
                st.markdown("---")
                st.markdown(response)
        
        st.markdown("---")
        
        # Quick explainer
        st.markdown("### 🚀 Quick Concept Clarifier")
        st.caption("Get a 2-minute explanation if you're short on time")
        
        if st.button("🤖 Explain in 2 Minutes", use_container_width=True, key="quick_explain"):
            with st.spinner("Generating quick explanation..."):
                prompt = f"""Explain "{topic['topic_name']}" ({subject}, {chapter}) in under 200 words for a Class 12 JEE student.
Use bullet points. Include the key formula and one simple example.
Be simple, clear, encouraging. Core concept: {topic['description']}"""
                response = ask_ai(prompt, user_id=user_id)
                st.success(f"**AI Mentor:**\n\n{response}")
        
        # Ask custom doubt
        st.markdown("---")
        st.markdown("### ❓ Ask Your Doubt")
        doubt = st.text_area("Type your specific doubt about this topic:", 
                             placeholder=f"e.g., I don't understand how {topic['formula_sheet']} is derived...",
                             key="doubt_input")
        if st.button("🧠 Ask AI Mentor", use_container_width=True, key="ask_doubt"):
            if doubt.strip():
                with st.spinner("Thinking..."):
                    prompt = f"""A 12th-grade student studying {subject} ({chapter} - {topic['topic_name']}) asks:
"{doubt}"

Context: The topic is about {topic['description']}. Formula: {topic['formula_sheet']}.

Please answer patiently, step by step, using simple language. Include relevant formulas if needed.
If the question involves a numerical, show complete working."""
                    response = ask_ai(prompt, user_id=user_id)
                    st.info(f"**AI Mentor:**\n\n{response}")
            else:
                st.warning("Please type your doubt first!")
    
    with tab2:
        st.markdown("### 📐 Key Formula")
        st.latex(topic['formula_sheet'])
        
        st.markdown("---")
        st.caption("💡 **Pro Tip:** Write this formula 3 times by hand, then try deriving it once. This builds deep memory.")
        
        if st.button("🧠 Generate Complete Formula Sheet for this Chapter", use_container_width=True, key="formula_gen"):
            with st.spinner("Generating comprehensive formula sheet..."):
                prompt = f"""Create a comprehensive formula sheet for the chapter "{chapter}" in {subject} for JEE preparation.

For each formula include:
- The formula (use standard mathematical notation)
- What each variable represents
- When to use it (one line)
- Any special conditions

Format as a clean organized list. Also include any important derivation steps that are commonly asked."""
                response = ask_ai(prompt, user_id=user_id)
                st.markdown(response)
    
    with tab3:
        if topic['common_mistakes']:
            st.warning(f"⚠️ **Common Mistake:** {topic['common_mistakes']}")
        
        if topic['tips']:
            st.success(f"💡 **Pro Tip:** {topic['tips']}")
        
        st.markdown("---")
        st.markdown("### 🎯 Exam Strategy for This Topic")
        
        if st.button("📋 Generate Exam Tips", use_container_width=True, key="exam_tips"):
            with st.spinner("Analyzing exam patterns..."):
                prompt = f"""For the topic "{topic['topic_name']}" ({subject}, {chapter}) in JEE and CBSE Class 12 exams:

1. **How often is this asked?** (estimate marks weightage)
2. **Types of questions** asked from this topic
3. **Top 5 tricks** to solve questions faster
4. **3 must-practice problems** (describe them, don't give full solutions)
5. **Time management** - how long should a student spend on this type in exam?

Keep it practical and actionable."""
                response = ask_ai(prompt, user_id=user_id)
                st.markdown(response)
