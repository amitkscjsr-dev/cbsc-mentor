# 🎓 AI Learning Mentor — CBSE & JEE 2027

A production-ready, AI-powered personal learning platform built for **weak students** who want to ace CBSE Class 12 Boards and crack competitive engineering entrance exams (JEE Mains/Advanced).

Built with Python, Streamlit, SQLite, and multiple AI providers.

## 🌟 Key Features

### 📊 Smart Dashboard
- Real-time **JEE readiness score** across Physics, Chemistry & Mathematics  
- **Daily streak tracking** with consecutive day counter
- Subject-wise mastery progress bars with topic completion %
- Test score trend curve with passing line indicator
- Subject balance radar chart
- Weak area priority alerts with tips

### 📅 Intelligent Study Planner  
- **Spaced repetition algorithm** — automatically schedules topics based on forgetting curve
- **Weak topic priority** — topics where accuracy < 60% get boosted
- **CBSE/JEE weightage balancing** — high-weightage topics appear more frequently
- 7-day plan view with day-by-day tabs
- Task completion tracking with streak integration

### 📚 Deep Concept Learning
- **50+ real NCERT topics** across Physics, Chemistry, Mathematics
- Full chapter overview with expandable topic cards
- AI-generated **crash-course lessons** (story mode)
- **Deep-dive lessons** from scratch for weak students
- **Ask your doubt** — type any question and AI explains
- Formula sheets with LaTeX rendering
- Common mistakes & pro tips for every topic

### ✍️ Adaptive Practice Engine
- **200+ exam-quality questions** with detailed step-by-step solutions
- **AI question generation** — generates new questions when database runs out
- Subject/topic/difficulty filtering
- Working **bookmark system** — save tough questions for review
- Contextual **hints** for every question
- **AI re-explanation** — ask AI to break down any solution differently

### 📝 Exam Simulator
- Multiple test modes: Quick Quiz (5Q), Chapter Test (10Q), Full Mock (15Q), Weak Areas Only
- Subject and difficulty filters
- **Visual countdown timer** with progress bar
- **Topic-wise result breakdown** after every test
- Full answer review with solutions
- Complete **test history** with scores and time tracking

### 🧠 Revision & Flashcards
- **AI-generated flashcards** with flip interaction
- **Spaced repetition scheduling** — cards reappear based on difficulty rating
- Weak area analysis with accuracy stats and AI revision guides
- **PDF download** — Weak areas notes or complete formula book

### ⚙️ Profile & Settings
- Multi-user support with profiles
- **AI provider selection**: Gemini (free), Groq (free), OpenAI (paid)
- Target exam configuration (CBSE / JEE Mains / Advanced)
- Study hours adjustment
- Journey stats summary

## 🛠️ Setup

### Prerequisites
- Python 3.9+
- (Optional) API key for AI features

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd CBSC

# Install dependencies
pip install -r requirements.txt

# Set up API keys (optional but recommended)
# Edit .env file with your keys
```

### API Keys (Free Options)

| Provider | Cost | How to Get |
|----------|------|------------|
| **Gemini** (Recommended) | 🟢 Free | [Google AI Studio](https://aistudio.google.com/apikey) |
| **Groq** | 🟢 Free | [Groq Console](https://console.groq.com/keys) |
| **OpenAI** | 🟡 Paid | [OpenAI Platform](https://platform.openai.com/api-keys) |

### Run

```bash
streamlit run app.py
```

The database is automatically initialized with comprehensive content on first run.

## 📦 Tech Stack

- **Frontend**: Streamlit + Custom CSS Design System
- **Backend**: Python + SQLite
- **AI**: Google Gemini (primary/free) + Groq + OpenAI
- **Charts**: Plotly + Custom HTML
- **PDF**: FPDF2

## 📁 Project Structure

```
CBSC/
├── app.py              # Main application & CSS design system
├── database.py         # SQLite schema + 50+ topics + 200+ questions
├── utils.py            # AI integration, spaced repetition, streak tracking
├── requirements.txt    # Python dependencies
├── .env                # API keys (gitignored)
├── .gitignore          # Security & cleanup
├── data/
│   └── learning_app.db # Auto-generated SQLite database
└── modules/
    ├── __init__.py
    ├── dashboard.py    # Analytics & progress tracking
    ├── profile.py      # Login, registration, settings
    ├── study_plan.py   # Smart study scheduler
    ├── subjects.py     # Concept learning & AI tutor
    ├── practice.py     # Question practice & bookmarks
    ├── tests.py        # Exam simulation & history
    └── revision.py     # Flashcards & PDF export
```

## 🎯 Designed For

- **CBSE Class 12 students** preparing for Board exams
- **JEE Mains & Advanced aspirants** (2027 batch)
- **Weak students** who need patient, step-by-step explanations
- Anyone looking for **free, AI-powered** exam preparation

---

*Built with ❤️ for every student who believes hard work beats talent.*
