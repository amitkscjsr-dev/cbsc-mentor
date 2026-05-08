import pandas as pd
from datetime import datetime, timedelta
import json
import random
from google import genai
from groq import Groq
from openai import OpenAI
import os
from dotenv import load_dotenv
from database import get_connection

load_dotenv()

# =============================================================================
# AI PROVIDER (Default: Gemini — free 15 RPM, 1M tokens/day)
# =============================================================================

def get_ai_provider(user_id=None):
    """Get the user's preferred AI provider. Defaults to Gemini (free)."""
    if user_id:
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT ai_provider FROM users WHERE id=?", (user_id,))
        row = c.fetchone()
        conn.close()
        if row and row['ai_provider']:
            return row['ai_provider']
    return "Gemini"


def ask_ai(prompt, ai_provider=None, user_id=None):
    """Call AI with fallback chain: User's choice → Gemini → Groq → Mock."""
    if ai_provider is None:
        ai_provider = get_ai_provider(user_id)
    
    # Try the selected provider first
    providers_to_try = [ai_provider]
    for p in ["Gemini", "Groq", "OpenAI"]:
        if p not in providers_to_try:
            providers_to_try.append(p)
    
    for provider in providers_to_try:
        api_key = os.environ.get(f"{provider.upper()}_API_KEY", "")
        if not api_key or api_key.strip() == "":
            continue
        
        try:
            if provider == "Gemini":
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                return response.text
                
            elif provider == "Groq":
                client = Groq(api_key=api_key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                )
                return chat_completion.choices[0].message.content
                
            elif provider == "OpenAI":
                client = OpenAI(api_key=api_key)
                chat_completion = client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="gpt-4o-mini",
                )
                return chat_completion.choices[0].message.content
                
        except Exception:
            continue  # Try next provider
    
    # All providers failed — return helpful mock
    return _get_mock_response(prompt)


def _get_mock_response(prompt):
    """Provide a helpful mock response when no API is available."""
    return """⚠️ **AI is currently unavailable** (no valid API key configured).

**To enable AI features (free):**
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create a free Gemini API key
3. Add it to your `.env` file as `GEMINI_API_KEY=your_key_here`
4. Restart the app

**In the meantime, here's a study tip:**
> Break complex problems into smaller steps. Write down what you KNOW, what you NEED to find, and which FORMULA connects them. This 3-step approach works for 90% of Physics and Chemistry numericals!
"""


# =============================================================================
# AI-POWERED QUESTION GENERATION
# =============================================================================

def generate_questions_ai(topic_name, subject, chapter, difficulty="Medium", count=3, user_id=None):
    """Generate new questions using AI when database runs out."""
    prompt = f"""You are an expert CBSE and JEE exam paper setter.
Generate {count} {difficulty}-level multiple choice questions on the topic "{topic_name}" 
from {subject} ({chapter}) for a Class 12 student preparing for JEE 2027.

IMPORTANT RULES:
- Each question must have exactly 4 options
- Include detailed step-by-step solution
- Mix numerical and conceptual questions
- Make sure questions test deep understanding, not just memory
- For numerical questions, include actual calculations in solution

Return ONLY a valid JSON array (no markdown, no extra text) in this exact format:
[
  {{
    "question": "question text here",
    "options": ["option A", "option B", "option C", "option D"],
    "correct": "correct option text (must match one of the options exactly)",
    "solution": "detailed step-by-step solution",
    "hint": "a helpful hint without giving away the answer",
    "type": "Numerical or Conceptual"
  }}
]"""

    response = ask_ai(prompt, user_id=user_id)
    
    try:
        # Try to extract JSON from response
        text = response.strip()
        # Handle markdown code blocks
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        questions = json.loads(text.strip())
        
        # Validate structure
        valid_questions = []
        for q in questions:
            if all(k in q for k in ['question', 'options', 'correct', 'solution']):
                if len(q['options']) == 4 and q['correct'] in q['options']:
                    valid_questions.append(q)
        
        if valid_questions:
            # Store in database for caching
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT id FROM topics WHERE topic_name=? AND subject=?", (topic_name, subject))
            topic_row = c.fetchone()
            if topic_row:
                for q in valid_questions:
                    c.execute("""
                        INSERT INTO questions (topic_id, q_type, difficulty, question_text, options, correct_option, solution_text, hint)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (topic_row['id'], q.get('type', 'Mixed'), difficulty, 
                          q['question'], json.dumps(q['options']), q['correct'], 
                          q['solution'], q.get('hint', '')))
            conn.commit()
            conn.close()
            return valid_questions
    except (json.JSONDecodeError, KeyError, IndexError):
        pass
    
    return None


def generate_flashcards_ai(topic_name, subject, chapter, count=5, user_id=None):
    """Generate flashcards for a topic using AI."""
    prompt = f"""Create {count} study flashcards for the topic "{topic_name}" from {subject} ({chapter}) 
for a Class 12 CBSE student preparing for JEE 2027.

Each flashcard should have:
- FRONT: A concise question, formula, or concept name
- BACK: The answer, derivation, or detailed explanation

Focus on:
- Key formulas and their derivations
- Common exam tricks and shortcuts
- Frequently asked concepts
- Memory aids and mnemonics

Return ONLY a valid JSON array:
[
  {{"front": "front text", "back": "back text"}},
  ...
]"""
    
    response = ask_ai(prompt, user_id=user_id)
    
    try:
        text = response.strip()
        if '```json' in text:
            text = text.split('```json')[1].split('```')[0]
        elif '```' in text:
            text = text.split('```')[1].split('```')[0]
        
        cards = json.loads(text.strip())
        valid_cards = [c for c in cards if 'front' in c and 'back' in c]
        return valid_cards if valid_cards else None
    except (json.JSONDecodeError, KeyError):
        return None


# =============================================================================
# SMART STUDY PLAN (Spaced Repetition + Weak Area Priority)
# =============================================================================

def generate_study_plan(user_id, study_hours, weak_subjects=None):
    """
    Generates an intelligent study plan using:
    1. Weak topic prioritization (topics with accuracy < 60%)
    2. Spaced repetition (topics not practiced recently get priority)
    3. CBSE/JEE weightage balancing
    4. Subject rotation for balanced preparation
    """
    conn = get_connection()
    
    topics_df = pd.read_sql_query("SELECT * FROM topics", conn)
    if topics_df.empty:
        conn.close()
        return False
    
    # Clear existing pending plan
    c = conn.cursor()
    c.execute("DELETE FROM study_plan WHERE user_id=? AND status='Pending'", (user_id,))
    
    # Get weak topics
    weak_df = pd.read_sql_query("""
        SELECT topic_id, accuracy, last_practiced 
        FROM performance_tracking 
        WHERE user_id=? AND weak_area_flag=1
        ORDER BY accuracy ASC
    """, conn, params=(user_id,))
    
    weak_topic_ids = set(weak_df['topic_id'].tolist()) if not weak_df.empty else set()
    
    # Get all practiced topics with recency info
    practiced_df = pd.read_sql_query("""
        SELECT topic_id, last_practiced 
        FROM performance_tracking 
        WHERE user_id=?
    """, conn, params=(user_id,))
    
    practiced_topics = {}
    if not practiced_df.empty:
        for _, row in practiced_df.iterrows():
            practiced_topics[row['topic_id']] = row['last_practiced']
    
    # Score each topic for priority
    topic_scores = []
    for _, topic in topics_df.iterrows():
        score = 0
        tid = topic['id']
        
        # Weak area bonus (highest priority)
        if tid in weak_topic_ids:
            score += 50
        
        # High weightage bonus
        score += (topic['cbse_weightage'] + topic['jee_weightage']) * 2
        
        # Not yet practiced bonus
        if tid not in practiced_topics:
            score += 30
        else:
            # Spaced repetition: older = higher priority
            last = practiced_topics[tid]
            if last:
                try:
                    days_ago = (datetime.now() - datetime.fromisoformat(str(last))).days
                    score += min(days_ago * 2, 20)  # Cap at 20
                except (ValueError, TypeError):
                    score += 10
        
        # Difficulty variety
        if topic['difficulty'] == 'Hard':
            score += 5
        
        topic_scores.append((tid, score, topic['subject']))
    
    # Sort by score descending
    topic_scores.sort(key=lambda x: x[1], reverse=True)
    
    plan_days = 7
    topics_per_day = max(study_hours, 2)  # At least 2 topics per day
    today = datetime.now().date()
    
    # Distribute across days with subject rotation
    subjects = list(set(t[2] for t in topic_scores))
    
    for day in range(plan_days):
        current_date = today + timedelta(days=day)
        day_topics = []
        subject_count = {}
        
        for tid, score, subj in topic_scores:
            if len(day_topics) >= topics_per_day:
                break
            
            # Ensure subject balance
            if subject_count.get(subj, 0) >= max(topics_per_day // len(subjects) + 1, 1):
                continue
            
            # Avoid repeating same topic within 2 days
            already_scheduled = any(t[0] == tid for t in day_topics)
            if not already_scheduled:
                # Determine task type
                if tid in weak_topic_ids:
                    task_type = "Revision + Extra Practice"
                elif tid not in practiced_topics:
                    task_type = "Learn Concept + Practice"
                else:
                    task_type = "Practice + Test"
                
                priority = score
                day_topics.append((tid, task_type, priority))
                subject_count[subj] = subject_count.get(subj, 0) + 1
        
        for tid, task_type, priority in day_topics:
            c.execute("""
                INSERT INTO study_plan (user_id, date, topic_id, task_type, priority, status)
                VALUES (?, ?, ?, ?, ?, 'Pending')
            """, (user_id, current_date, tid, task_type, priority))
        
        # Rotate topics for next day
        if topic_scores:
            # Move used topics to end
            used_ids = {t[0] for t in day_topics}
            remaining = [t for t in topic_scores if t[0] not in used_ids]
            used = [t for t in topic_scores if t[0] in used_ids]
            topic_scores = remaining + used
    
    conn.commit()
    conn.close()
    return True


# =============================================================================
# TEST EVALUATION
# =============================================================================

def evaluate_test(user_id, test_type, answers_dict, total_time, subject_filter=None):
    """
    Evaluates test answers, updates test_results and performance_tracking.
    Returns (score_percentage, correct_count, total, topic_breakdown).
    """
    conn = get_connection()
    c = conn.cursor()
    
    correct_count = 0
    total = len(answers_dict)
    topic_results = {}
    
    for q_id, selected in answers_dict.items():
        c.execute("SELECT topic_id, correct_option FROM questions WHERE id=?", (q_id,))
        row = c.fetchone()
        if row:
            topic_id, correct_option = row['topic_id'], row['correct_option']
            
            # Get topic name for breakdown
            c.execute("SELECT topic_name, subject FROM topics WHERE id=?", (topic_id,))
            topic_info = c.fetchone()
            topic_key = f"{topic_info['subject']} - {topic_info['topic_name']}" if topic_info else str(topic_id)
            
            if topic_key not in topic_results:
                topic_results[topic_key] = {'correct': 0, 'total': 0, 'topic_id': topic_id}
            topic_results[topic_key]['total'] += 1
            
            if selected == correct_option:
                correct_count += 1
                topic_results[topic_key]['correct'] += 1
    
    score = (correct_count / total) * 100 if total > 0 else 0
    
    # Save test result with topic breakdown
    breakdown_json = json.dumps({k: {'correct': v['correct'], 'total': v['total']} 
                                  for k, v in topic_results.items()})
    
    c.execute("""
        INSERT INTO test_results (user_id, test_type, subject_filter, total_questions, correct_answers, time_taken, score, topic_breakdown)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, test_type, subject_filter, total, correct_count, total_time, score, breakdown_json))
    
    # Update performance metrics
    for topic_key, stats in topic_results.items():
        t_id = stats['topic_id']
        c.execute("SELECT * FROM performance_tracking WHERE user_id=? AND topic_id=?", (user_id, t_id))
        perf = c.fetchone()
        
        acc = stats['correct'] / stats['total'] if stats['total'] > 0 else 0
        is_weak = 1 if acc < 0.6 else 0
        
        if perf:
            new_tests = perf['times_tested'] + 1
            new_acc = ((perf['accuracy'] * perf['times_tested']) + acc) / new_tests
            is_weak = 1 if new_acc < 0.6 else 0
            c.execute("""
                UPDATE performance_tracking 
                SET accuracy=?, times_tested=?, weak_area_flag=?, last_practiced=CURRENT_TIMESTAMP
                WHERE user_id=? AND topic_id=?
            """, (new_acc, new_tests, is_weak, user_id, t_id))
        else:
            c.execute("""
                INSERT INTO performance_tracking (user_id, topic_id, accuracy, times_tested, weak_area_flag, last_practiced)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (user_id, t_id, acc, 1, is_weak))
    
    # Commit + close BEFORE update_streak (which opens its own connection).
    # Otherwise the second connection deadlocks on the still-open write txn.
    conn.commit()
    conn.close()

    update_streak(user_id, tests_taken=1)
    return score, correct_count, total, topic_results


# =============================================================================
# WEAK TOPICS
# =============================================================================

def get_weak_topics(user_id):
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT t.topic_name, t.subject, t.chapter, p.accuracy, p.times_tested, p.last_practiced,
               t.common_mistakes, t.tips
        FROM performance_tracking p
        JOIN topics t ON p.topic_id = t.id
        WHERE p.user_id = ? AND p.weak_area_flag = 1
        ORDER BY p.accuracy ASC
    """, conn, params=(user_id,))
    conn.close()
    return df


# =============================================================================
# STREAK TRACKING
# =============================================================================

def update_streak(user_id, minutes=0, tasks=0, tests_taken=0):
    """Update today's streak entry."""
    conn = get_connection()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')
    
    c.execute("SELECT * FROM study_streaks WHERE user_id=? AND date=?", (user_id, today))
    existing = c.fetchone()
    
    if existing:
        c.execute("""
            UPDATE study_streaks 
            SET minutes_studied = minutes_studied + ?,
                tasks_completed = tasks_completed + ?,
                tests_taken = tests_taken + ?
            WHERE user_id=? AND date=?
        """, (minutes, tasks, tests_taken, user_id, today))
    else:
        c.execute("""
            INSERT INTO study_streaks (user_id, date, minutes_studied, tasks_completed, tests_taken)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, today, minutes, tasks, tests_taken))
    
    conn.commit()
    conn.close()


def get_streak(user_id):
    """Calculate current consecutive day streak."""
    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""
        SELECT date FROM study_streaks 
        WHERE user_id=? AND (minutes_studied > 0 OR tasks_completed > 0 OR tests_taken > 0)
        ORDER BY date DESC
    """, (user_id,))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return 0
    
    streak = 0
    today = datetime.now().date()
    
    # Check if today counts
    dates = [datetime.strptime(r['date'], '%Y-%m-%d').date() if isinstance(r['date'], str) else r['date'] for r in rows]
    
    # Start from today or yesterday
    check_date = today
    if dates and dates[0] != today:
        check_date = today - timedelta(days=1)
    
    for d in dates:
        if d == check_date:
            streak += 1
            check_date -= timedelta(days=1)
        elif d < check_date:
            break
    
    return streak


def get_weekly_activity(user_id):
    """Get last 7 days of activity for heatmap."""
    conn = get_connection()
    today = datetime.now().date()
    week_ago = today - timedelta(days=6)
    
    df = pd.read_sql_query("""
        SELECT date, minutes_studied, tasks_completed, tests_taken
        FROM study_streaks
        WHERE user_id=? AND date >= ?
        ORDER BY date ASC
    """, conn, params=(user_id, week_ago.isoformat()))
    conn.close()
    return df


# =============================================================================
# BOOKMARKS
# =============================================================================

def add_bookmark(user_id, question_id, note=""):
    """Add a question to bookmarks."""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT OR IGNORE INTO bookmarks (user_id, question_id, note) VALUES (?, ?, ?)",
                  (user_id, question_id, note))
        conn.commit()
        success = True
    except Exception:
        success = False
    conn.close()
    return success


def remove_bookmark(user_id, question_id):
    """Remove a question from bookmarks."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM bookmarks WHERE user_id=? AND question_id=?", (user_id, question_id))
    conn.commit()
    conn.close()


def is_bookmarked(user_id, question_id):
    """Check if a question is bookmarked."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM bookmarks WHERE user_id=? AND question_id=?", (user_id, question_id))
    result = c.fetchone() is not None
    conn.close()
    return result


def get_bookmarked_questions(user_id):
    """Get all bookmarked questions for a user."""
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT q.*, b.note as bookmark_note, b.created_at as bookmarked_at,
               t.topic_name, t.subject
        FROM bookmarks b
        JOIN questions q ON b.question_id = q.id
        JOIN topics t ON q.topic_id = t.id
        WHERE b.user_id = ?
        ORDER BY b.created_at DESC
    """, conn, params=(user_id,))
    conn.close()
    return df


# =============================================================================
# JEE READINESS SCORE
# =============================================================================

def calculate_jee_readiness(user_id):
    """Calculate an overall JEE readiness score (0-100)."""
    conn = get_connection()
    
    # Get all topics with JEE weightage
    topics_df = pd.read_sql_query("SELECT id, jee_weightage FROM topics", conn)
    total_weight = topics_df['jee_weightage'].sum()
    
    if total_weight == 0:
        conn.close()
        return 0
    
    # Get user's performance on each topic
    perf_df = pd.read_sql_query("""
        SELECT p.topic_id, p.accuracy, t.jee_weightage
        FROM performance_tracking p
        JOIN topics t ON p.topic_id = t.id
        WHERE p.user_id = ?
    """, conn, params=(user_id,))
    conn.close()
    
    if perf_df.empty:
        return 0
    
    # Weighted score
    weighted_sum = (perf_df['accuracy'] * perf_df['jee_weightage']).sum()
    readiness = (weighted_sum / total_weight) * 100
    
    return min(readiness, 100)
