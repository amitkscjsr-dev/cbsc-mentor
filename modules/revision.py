import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils import get_weak_topics, ask_ai, generate_flashcards_ai, update_streak
from database import get_connection

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


def generate_pdf(weak_df):
    """Generate a well-formatted PDF revision guide."""
    if not FPDF:
        return None
    
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # Title page
        pdf.add_page()
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 40, "", ln=True)
        pdf.cell(0, 15, "AI Learning Mentor", align='C', ln=True)
        pdf.set_font("helvetica", "", 14)
        pdf.cell(0, 10, "Targeted Revision Notes", align='C', ln=True)
        pdf.set_font("helvetica", "", 10)
        pdf.cell(0, 8, f"Generated on {datetime.now().strftime('%B %d, %Y')}", align='C', ln=True)
        pdf.cell(0, 8, "Focus on these topics to maximize your score!", align='C', ln=True)
        
        # Content
        pdf.add_page()
        conn = get_connection()
        c = conn.cursor()
        
        current_subject = ""
        
        def safe_text(text):
            """Safely encode text for PDF rendering."""
            if not text:
                return "N/A"
            return str(text).encode('latin-1', 'replace').decode('latin-1')
        
        for _, row in weak_df.iterrows():
            try:
                subject = row.get('subject', 'Unknown') if hasattr(row, 'get') else str(row.get('subject', 'Unknown'))
                
                # Subject header
                if subject != current_subject:
                    current_subject = subject
                    pdf.set_font("helvetica", "B", 14)
                    pdf.ln(5)
                    pdf.cell(0, 10, safe_text(subject), ln=True)
                    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
                    pdf.ln(3)
                
                topic_name = row.get('topic_name', 'Unknown') if hasattr(row, 'get') else 'Unknown'
                
                # Get topic details
                c.execute("SELECT description, formula_sheet, key_concepts, common_mistakes, tips FROM topics WHERE topic_name=? AND subject=?", 
                          (topic_name, subject))
                data = c.fetchone()
                
                # Topic header
                pdf.set_font("helvetica", "B", 11)
                mastery_text = ""
                if 'accuracy' in (row.index if hasattr(row, 'index') else []):
                    try:
                        mastery_text = f" (Accuracy: {float(row['accuracy'])*100:.0f}%)"
                    except (ValueError, TypeError):
                        pass
                pdf.cell(0, 8, safe_text(f"{topic_name}{mastery_text}"), ln=True)
                
                if data:
                    pdf.set_font("helvetica", "", 9)
                    
                    if data['description']:
                        pdf.multi_cell(0, 5, safe_text(f"Concept: {data['description']}"))
                    
                    if data['formula_sheet']:
                        pdf.multi_cell(0, 5, safe_text(f"Formula: {data['formula_sheet']}"))
                    
                    if data['key_concepts']:
                        pdf.multi_cell(0, 5, safe_text(f"Key: {data['key_concepts']}"))
                    
                    if data['common_mistakes']:
                        pdf.multi_cell(0, 5, safe_text(f"Watch out: {data['common_mistakes']}"))
                    
                    if data['tips']:
                        pdf.multi_cell(0, 5, safe_text(f"Tip: {data['tips']}"))
                
                pdf.ln(3)
            except Exception:
                # Skip problematic topics rather than failing the entire PDF
                continue
        
        conn.close()
        return bytes(pdf.output())
    except Exception:
        return None


def show():
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                padding: 1.8rem 2rem; border-radius: 16px; margin-bottom: 1.5rem;">
        <h1 style="color: white !important; margin: 0; font-size: 1.8rem;">🧠 Revision & Flashcards</h1>
        <p style="color: rgba(255,255,255,0.85); margin: 0.3rem 0 0 0;">
            Spaced repetition • AI flashcards • Targeted PDF notes • Weak area focus
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    user_id = st.session_state['user_id']
    
    tab1, tab2, tab3 = st.tabs(["⚠️ Weak Areas", "🗂️ Flashcards", "📥 Download Notes"])
    
    with tab1:
        _show_weak_areas(user_id)
    
    with tab2:
        _show_flashcards(user_id)
    
    with tab3:
        _show_download(user_id)


def _show_weak_areas(user_id):
    """Display weak topics with AI revision help."""
    st.markdown("### ⚠️ Topics That Need Your Attention")
    st.caption("Based on your test performance — topics with accuracy below 60%")
    
    weak_df = get_weak_topics(user_id)
    
    if weak_df.empty:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 2rem; 
                    border-radius: 14px; text-align: center; color: white;">
            <div style="font-size: 2.5rem;">🏆</div>
            <h3 style="color: white !important; margin: 0.5rem 0;">No Weak Areas!</h3>
            <p style="opacity: 0.9; margin: 0;">You're doing great! Keep practicing to maintain your streak.</p>
        </div>""", unsafe_allow_html=True)
        return
    
    st.warning(f"⚡ You have **{len(weak_df)}** weak topic(s). These are automatically prioritized in your study plan.")
    
    for idx, row in weak_df.iterrows():
        acc_pct = row['accuracy'] * 100
        color = "#ef4444" if acc_pct < 30 else "#f59e0b" if acc_pct < 50 else "#eab308"
        
        with st.expander(f"{'🔴' if acc_pct < 30 else '🟡'} {row['subject']} — {row['topic_name']} ({acc_pct:.0f}%)"):
            st.markdown(f"""
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem;">
                <div style="background: {color}15; padding: 0.5rem 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: {color};">{acc_pct:.0f}%</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Accuracy</div>
                </div>
                <div style="background: #f1f5f9; padding: 0.5rem 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 1.5rem; font-weight: 800; color: #334155;">{int(row['times_tested'])}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Times Tested</div>
                </div>
                <div style="background: #f1f5f9; padding: 0.5rem 1rem; border-radius: 8px; text-align: center;">
                    <div style="font-size: 0.9rem; font-weight: 600; color: #334155;">{row['chapter']}</div>
                    <div style="font-size: 0.7rem; color: #64748b;">Chapter</div>
                </div>
            </div>""", unsafe_allow_html=True)
            
            if row.get('common_mistakes'):
                st.warning(f"⚠️ **Common Mistake:** {row['common_mistakes']}")
            
            if row.get('tips'):
                st.success(f"💡 **Tip:** {row['tips']}")
            
            if st.button(f"🤖 Get AI Revision for {row['topic_name']}", key=f"rev_{idx}"):
                with st.spinner("Generating focused revision material..."):
                    prompt = f"""I'm weak in {row['subject']}, specifically "{row['topic_name']}" ({row['chapter']}).
My accuracy is only {acc_pct:.0f}% after {int(row['times_tested'])} tests.

Please create a FOCUSED revision guide:
1. **Key concept in 3 lines** — the absolute essence
2. **The formula** with what each variable means
3. **2 solved examples** — one easy, one JEE-level
4. **3 common traps** students fall into
5. **Memory trick** to never forget this concept
6. **Practice strategy** — what should I do differently?

Be concise and practical. This is exam revision, not a full lesson."""
                    response = ask_ai(prompt, user_id=user_id)
                    st.markdown(response)


def _show_flashcards(user_id):
    """Interactive flashcard system."""
    st.markdown("### 🗂️ Interactive Flashcards")
    st.caption("Quick-fire revision cards for formulas and concepts")
    
    conn = get_connection()
    
    # Check for existing flashcards
    existing = pd.read_sql_query("""
        SELECT f.*, t.topic_name, t.subject 
        FROM flashcards f 
        JOIN topics t ON f.topic_id = t.id 
        WHERE f.user_id = ?
        ORDER BY f.next_review ASC
    """, conn, params=(user_id,))
    
    # Generate new flashcards section
    st.markdown("#### Generate New Cards")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        topics_df = pd.read_sql_query("SELECT id, subject, chapter, topic_name FROM topics ORDER BY subject", conn)
        topic_options = [f"{r['subject']} — {r['topic_name']}" for _, r in topics_df.iterrows()]
        topic_map = {f"{r['subject']} — {r['topic_name']}": r for _, r in topics_df.iterrows()}
        selected = st.selectbox("Select topic for flashcards", topic_options, key="fc_topic")
    
    with col2:
        count = st.number_input("Cards", min_value=3, max_value=10, value=5, key="fc_count")
    
    if st.button("🪄 Generate Flashcards with AI", use_container_width=True):
        topic_data = topic_map[selected]
        with st.spinner("🧠 Creating flashcards..."):
            cards = generate_flashcards_ai(
                topic_data['topic_name'], topic_data['subject'], 
                topic_data['chapter'], count=count, user_id=user_id
            )
            
            if cards:
                c = conn.cursor()
                today = datetime.now().strftime('%Y-%m-%d')
                for card in cards:
                    c.execute("""
                        INSERT INTO flashcards (user_id, topic_id, front_text, back_text, next_review)
                        VALUES (?, ?, ?, ?, ?)
                    """, (user_id, topic_data['id'], card['front'], card['back'], today))
                conn.commit()
                st.success(f"✅ Created {len(cards)} flashcards! Scroll down to review them.")
                update_streak(user_id, minutes=5)
                st.rerun()
            else:
                st.warning("Couldn't generate flashcards. Check your API key or try again.")
    
    # Display existing flashcards
    if not existing.empty:
        st.markdown("---")
        
        # Cards due for review
        today = datetime.now().strftime('%Y-%m-%d')
        due_cards = existing[existing['next_review'] <= today] if 'next_review' in existing.columns else existing
        
        st.markdown(f"#### Your Cards ({len(existing)} total, {len(due_cards)} due for review)")
        
        if 'fc_index' not in st.session_state:
            st.session_state['fc_index'] = 0
        if 'fc_flipped' not in st.session_state:
            st.session_state['fc_flipped'] = False
        
        cards_to_show = due_cards if not due_cards.empty else existing
        
        if st.session_state['fc_index'] >= len(cards_to_show):
            st.session_state['fc_index'] = 0
        
        card = cards_to_show.iloc[st.session_state['fc_index']]
        card_num = st.session_state['fc_index'] + 1
        total_cards = len(cards_to_show)
        
        # Card display
        if st.session_state['fc_flipped']:
            # Back of card
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 2rem; 
                        border-radius: 16px; text-align: center; color: white; min-height: 200px;
                        display: flex; flex-direction: column; justify-content: center;
                        box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);">
                <p style="font-size: 0.8rem; opacity: 0.8; margin: 0;">📖 ANSWER ({card_num}/{total_cards})</p>
                <h3 style="color: white !important; margin: 1rem 0; line-height: 1.6;">{card['back_text']}</h3>
                <p style="font-size: 0.75rem; opacity: 0.7; margin: 0;">{card['subject']} — {card['topic_name']}</p>
            </div>""", unsafe_allow_html=True)
        else:
            # Front of card
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #4F46E5, #7C3AED); padding: 2rem; 
                        border-radius: 16px; text-align: center; color: white; min-height: 200px;
                        display: flex; flex-direction: column; justify-content: center;
                        box-shadow: 0 10px 30px rgba(79, 70, 229, 0.3);">
                <p style="font-size: 0.8rem; opacity: 0.8; margin: 0;">❓ QUESTION ({card_num}/{total_cards})</p>
                <h3 style="color: white !important; margin: 1rem 0; line-height: 1.6;">{card['front_text']}</h3>
                <p style="font-size: 0.75rem; opacity: 0.7; margin: 0;">Click "Flip" to see answer</p>
            </div>""", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Controls
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            if st.button("⏮️ Prev", use_container_width=True):
                st.session_state['fc_index'] = max(0, st.session_state['fc_index'] - 1)
                st.session_state['fc_flipped'] = False
                st.rerun()
        
        with col2:
            if st.button("🔄 Flip", use_container_width=True, type="primary"):
                st.session_state['fc_flipped'] = not st.session_state['fc_flipped']
                st.rerun()
        
        with col3:
            if st.button("⏭️ Next", use_container_width=True):
                st.session_state['fc_index'] = min(total_cards - 1, st.session_state['fc_index'] + 1)
                st.session_state['fc_flipped'] = False
                st.rerun()
        
        with col4:
            if st.button("😰 Hard", use_container_width=True, help="Review again tomorrow"):
                _update_flashcard_schedule(card['id'], 0)  # quality=0
                _advance_card(total_cards)
        
        with col5:
            if st.button("👍 Good", use_container_width=True, help="Review in 3-6 days"):
                _update_flashcard_schedule(card['id'], 1)  # quality=1
                _advance_card(total_cards)
        
        with col6:
            if st.button("✅ Easy", use_container_width=True, help="Review in 7+ days"):
                _update_flashcard_schedule(card['id'], 2)  # quality=2
                _advance_card(total_cards)
    else:
        st.info("📋 No flashcards yet. Generate some using AI above!")
    
    conn.close()


def _update_flashcard_schedule(card_id, quality):
    """Update flashcard review schedule using SuperMemo-2 algorithm.
    quality: 0=Again (Hard), 1=Good, 2=Easy
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT review_count, ease_factor FROM flashcards WHERE id=?", (card_id,))
    row = c.fetchone()
    
    if row:
        n = (row['review_count'] or 0) + 1
        ef = row['ease_factor'] or 2.5
        
        if quality == 0:  # Hard — reset interval
            interval = 1
            ef = max(1.3, ef - 0.2)
        elif quality == 1:  # Good
            if n == 1:
                interval = 3
            elif n == 2:
                interval = 6
            else:
                # Get last interval from next_review vs created_at
                interval = max(3, int(round(n * ef * 0.8)))
            ef = max(1.3, ef - 0.05)
        else:  # Easy
            if n <= 2:
                interval = 7
            else:
                interval = max(7, int(round(n * ef)))
            ef = min(3.0, ef + 0.1)
        
        next_review = (datetime.now() + timedelta(days=interval)).strftime('%Y-%m-%d')
        c.execute("""
            UPDATE flashcards SET next_review=?, review_count=?, ease_factor=? WHERE id=?
        """, (next_review, n, ef, card_id))
    
    conn.commit()
    conn.close()


def _advance_card(total):
    """Move to next flashcard."""
    st.session_state['fc_index'] = min(total - 1, st.session_state['fc_index'] + 1)
    st.session_state['fc_flipped'] = False
    st.rerun()


def _show_download(user_id):
    """PDF download section."""
    st.markdown("### 📥 Download Revision Notes")
    st.caption("Portable PDF notes for offline study and last-minute revision")
    
    weak_df = get_weak_topics(user_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: white; padding: 1.2rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
            <div style="font-size: 1.5rem;">⚠️</div>
            <h4 style="margin: 0.5rem 0;">Weak Areas Notes</h4>
            <p style="color: #64748b; font-size: 0.85rem; margin: 0;">Focus on topics where you scored below 60%</p>
        </div>""", unsafe_allow_html=True)
        
        if not weak_df.empty:
            pdf_bytes = generate_pdf(weak_df)
            if pdf_bytes:
                st.download_button(
                    label="📁 Download Weak Areas PDF",
                    data=pdf_bytes,
                    file_name="weak_areas_revision.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.warning("PDF library not available. Install fpdf2.")
        else:
            st.success("No weak areas! Generate full notes instead →")
    
    with col2:
        st.markdown("""
        <div style="background: white; padding: 1.2rem; border-radius: 12px; border: 1px solid #e2e8f0; text-align: center;">
            <div style="font-size: 1.5rem;">📚</div>
            <h4 style="margin: 0.5rem 0;">Complete Formula Book</h4>
            <p style="color: #64748b; font-size: 0.85rem; margin: 0;">All formulas across Physics, Chemistry, Math</p>
        </div>""", unsafe_allow_html=True)
        
        conn = get_connection()
        all_topics = pd.read_sql_query("SELECT topic_name, subject, chapter FROM topics ORDER BY subject, chapter", conn)
        conn.close()
        
        # Add dummy accuracy column for PDF generation
        if 'accuracy' not in all_topics.columns:
            all_topics['accuracy'] = 1.0
        
        pdf_bytes = generate_pdf(all_topics)
        if pdf_bytes:
            st.download_button(
                label="📁 Download Complete Formula Book",
                data=pdf_bytes,
                file_name="complete_formula_book.pdf",
                mime="application/pdf",
                use_container_width=True
            )
