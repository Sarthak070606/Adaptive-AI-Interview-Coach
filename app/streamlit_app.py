import streamlit as st
import sys
import os
import tempfile
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.question_generator import generate_question
from src.difficulty_manager import get_next_difficulty
from src.answer_evaluator import evaluate_answer
from src.resume_parser import extract_text_from_pdf
from src.skill_extractor import extract_skills
from src.speech_to_text import transcribe_audio

# --------------- Page Config ---------------
st.set_page_config(
    page_title="Adaptive AI Interview Coach",
    page_icon="🗣️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------- CSS ---------------
st.markdown("""
<style>
    .main-title {
        font-size: 2.3rem;
        font-weight: 700;
        margin-bottom: 0.15rem;
    }
    .subtitle {
        opacity: 0.75;
        font-size: 1.05rem;
        margin-bottom: 1.2rem;
    }
    .metric-box {
        background: rgba(128, 128, 128, 0.15);
        border: 1px solid rgba(128, 128, 128, 0.35);
        border-radius: 10px;
        padding: 0.85rem 1rem;
        text-align: center;
        color: inherit;
    }
    .question-box {
        background: rgba(14, 165, 233, 0.12);
        border-left: 5px solid #0ea5e9;
        padding: 1.15rem 1.3rem;
        border-radius: 8px;
        margin: 0.8rem 0;
        font-size: 1.12rem;
        color: inherit;
        line-height: 1.5;
    }
    .feedback-box {
        background: rgba(34, 197, 94, 0.12);
        border-left: 5px solid #22c55e;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        margin-top: 0.8rem;
        color: inherit;
    }
    .skill-chip {
        display: inline-block;
        background: rgba(14, 165, 233, 0.2);
        color: inherit;
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        margin: 0.2rem;
        font-size: 0.9rem;
        font-weight: 500;
        border: 1px solid rgba(14, 165, 233, 0.4);
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --------------- Session State ---------------
defaults = {
    "started": False,
    "current_question": None,
    "current_difficulty": "easy",
    "question_number": 1,
    "scores": [],
    "asked_questions": [],
    "history": [],
    "last_evaluation": None,
    "use_llm": True,
    "extracted_skills": [],
    "resume_text": "",
    "selected_skills": [],
    "voice_transcript": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# --------------- Sidebar ---------------
with st.sidebar:
    st.header("🎯 Interview Setup")

    # ---- Resume Upload ----
    st.subheader("📄 Resume (optional)")
    resume_file = st.file_uploader("Upload PDF Resume", type=["pdf"], key="resume_uploader")
    if resume_file is not None:
        if st.button("Extract Skills from Resume"):
            with st.spinner("Reading resume..."):
                try:
                    # Save temp PDF
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(resume_file.read())
                        tmp_path = tmp.name
                    text = extract_text_from_pdf(tmp_path)
                    os.unlink(tmp_path)
                    skills = extract_skills(text)
                    st.session_state.resume_text = text
                    st.session_state.extracted_skills = skills
                    if skills:
                        st.success(f"Found {len(skills)} skills")
                    else:
                        st.warning("No known skills detected. You can still select manually.")
                except Exception as e:
                    st.error(f"Error: {e}")

    if st.session_state.extracted_skills:
        st.markdown("**Detected Skills:**")
        chips = " ".join([f'<span class="skill-chip">{s}</span>' for s in st.session_state.extracted_skills])
        st.markdown(chips, unsafe_allow_html=True)
        # Let user pick which ones to focus on
        st.session_state.selected_skills = st.multiselect(
            "Focus on these skills",
            options=st.session_state.extracted_skills,
            default=st.session_state.extracted_skills[:3]
        )

    st.divider()

    role = st.selectbox(
        "Target Role",
        ["Python Developer", "ML Engineer", "Data Scientist", "Backend Developer", "Full Stack Developer"]
    )
    level = st.selectbox("Experience Level", ["Beginner", "Intermediate", "Advanced"])

    # Skill selection (manual or from resume)
    available_skills = ["Python", "Machine Learning", "SQL", "Data Structures", "System Design", "Pandas", "NumPy"]
    if st.session_state.selected_skills:
        # Prefer resume skills
        skill_options = list(dict.fromkeys(st.session_state.selected_skills + available_skills))
    else:
        skill_options = available_skills

    skill = st.selectbox("Focus Skill", skill_options)

    st.divider()
    st.session_state.use_llm = st.toggle("🚀 Live AI Questions (Groq)", value=True)
    st.caption("ON = questions generated live by LLM")

    st.divider()
    st.markdown("### Session Stats")
    if st.session_state.scores:
        avg = sum(st.session_state.scores) / len(st.session_state.scores)
        st.metric("Questions Answered", len(st.session_state.scores))
        st.metric("Average Score", f"{avg:.0f}%")
        st.metric("Current Difficulty", st.session_state.current_difficulty.title())
    else:
        st.info("No answers yet")

# --------------- Header ---------------
st.markdown('<p class="main-title">🗣️ Adaptive AI Interview Coach</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Real-time AI questions • Voice answers • Adaptive difficulty • Instant feedback</p>',
    unsafe_allow_html=True
)

# --------------- Start Screen ---------------
if not st.session_state.started:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.extracted_skills:
            st.success(f"Resume skills ready: {', '.join(st.session_state.extracted_skills[:6])}")
        st.info("Configure settings on the left, then start the interview.")
        if st.button("🚀 Start Interview", use_container_width=True, type="primary"):
            st.session_state.started = True
            st.session_state.current_difficulty = "easy"
            st.session_state.question_number = 1
            st.session_state.scores = []
            st.session_state.asked_questions = []
            st.session_state.history = []
            st.session_state.last_evaluation = None
            st.session_state.voice_transcript = ""

            with st.spinner("Generating your first question..."):
                q = generate_question(
                    skill=skill,
                    difficulty="easy",
                    role=role,
                    level=level,
                    use_llm=st.session_state.use_llm
                )
            if q:
                st.session_state.current_question = q
                st.session_state.asked_questions.append(q["question"])
            st.rerun()

# --------------- Interview Screen ---------------
else:
    q = st.session_state.current_question

    # Top metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-box"><b>Question</b><br>#{st.session_state.question_number}</div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-box"><b>Skill</b><br>{skill}</div>', unsafe_allow_html=True)
    with m3:
        diff_icon = {"easy": "🟢", "medium": "🟡", "hard": "🔴"}.get(st.session_state.current_difficulty, "")
        st.markdown(f'<div class="metric-box"><b>Difficulty</b><br>{diff_icon} {st.session_state.current_difficulty.title()}</div>', unsafe_allow_html=True)
    with m4:
        source = q.get("source", "bank") if q else "—"
        st.markdown(f'<div class="metric-box"><b>Source</b><br>{"🤖 LLM" if source == "llm" else "📚 Bank"}</div>', unsafe_allow_html=True)

    st.markdown("---")

    # Previous feedback
    if st.session_state.last_evaluation:
        ev = st.session_state.last_evaluation
        st.markdown("#### Previous Answer Feedback")
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Overall", f"{ev['overall']}%")
        c2.metric("Technical", f"{ev['technical']}%")
        c3.metric("Relevance", f"{ev['relevance']}%")
        c4.metric("Completeness", f"{ev['completeness']}%")
        c5.metric("Communication", f"{ev['communication']}%")
        st.markdown(f'<div class="feedback-box"><b>Feedback:</b> {ev["feedback"]}</div>', unsafe_allow_html=True)
        if ev.get("strengths"):
            st.success("**Strengths:** " + " • ".join(ev["strengths"]))
        if ev.get("improvements"):
            st.warning("**Improve:** " + " • ".join(ev["improvements"]))
        st.markdown("---")

    if q is None:
        st.warning("No more questions. End the interview or change skill.")
    else:
        st.markdown(f"### Question {st.session_state.question_number}")
        st.markdown(f'<div class="question-box">{q["question"]}</div>', unsafe_allow_html=True)

        # ----- Answer input: Text + Voice -----
        tab_text, tab_voice = st.tabs(["⌨️ Type Answer", "🎤 Voice Answer"])

        answer = ""
        with tab_text:
            answer = st.text_area(
                "Your Answer",
                height=160,
                placeholder="Type a clear, structured answer...",
                key=f"ans_text_{st.session_state.question_number}"
            )

        with tab_voice:
            st.caption("Record your answer or upload an audio file. Transcription uses Groq Whisper.")
            audio_data = None
            # Prefer native audio_input if available
            if hasattr(st, "audio_input"):
                audio_data = st.audio_input("Record your answer", key=f"audio_{st.session_state.question_number}")
            else:
                audio_data = st.file_uploader(
                    "Upload audio (wav, mp3, m4a, webm)",
                    type=["wav", "mp3", "m4a", "webm", "ogg"],
                    key=f"audio_up_{st.session_state.question_number}"
                )

            if audio_data is not None:
                if st.button("🔊 Transcribe Voice", key=f"transcribe_{st.session_state.question_number}"):
                    with st.spinner("Transcribing with Whisper..."):
                        try:
                            if hasattr(audio_data, "read"):
                                audio_bytes = audio_data.read()
                                fname = getattr(audio_data, "name", "audio.wav")
                            else:
                                audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else bytes(audio_data)
                                fname = "recording.wav"
                            transcript = transcribe_audio(audio_bytes, filename=fname)
                            st.session_state.voice_transcript = transcript
                            st.success("Transcription complete")
                        except Exception as e:
                            st.error(f"Transcription failed: {e}")

            if st.session_state.voice_transcript:
                st.text_area(
                    "Transcribed Answer (you can edit)",
                    value=st.session_state.voice_transcript,
                    height=140,
                    key=f"voice_edit_{st.session_state.question_number}"
                )
                # Use the (possibly edited) transcript
                answer = st.session_state.get(f"voice_edit_{st.session_state.question_number}", st.session_state.voice_transcript)

        # Buttons
        col_a, col_b, col_c = st.columns([2, 1, 1])
        with col_a:
            submit = st.button("✅ Submit Answer", type="primary", use_container_width=True)
        with col_b:
            skip = st.button("⏭️ Skip", use_container_width=True)
        with col_c:
            end = st.button("🏁 End Interview", use_container_width=True)

        if submit:
            final_answer = answer.strip() if answer else ""
            if not final_answer:
                st.warning("Please provide an answer (type or voice).")
            else:
                with st.spinner("Evaluating your answer with AI..."):
                    evaluation = evaluate_answer(q["question"], final_answer, skill)

                st.session_state.scores.append(evaluation["overall"])
                st.session_state.history.append({
                    "question": q["question"],
                    "answer": final_answer,
                    "difficulty": q.get("difficulty", st.session_state.current_difficulty),
                    "skill": skill,
                    "scores": evaluation
                })
                st.session_state.last_evaluation = evaluation
                st.session_state.voice_transcript = ""

                next_diff = get_next_difficulty(evaluation["overall"])
                st.session_state.current_difficulty = next_diff

                with st.spinner(f"Generating next ({next_diff}) question..."):
                    next_q = generate_question(
                        skill=skill,
                        difficulty=next_diff,
                        role=role,
                        level=level,
                        exclude_questions=st.session_state.asked_questions,
                        use_llm=st.session_state.use_llm
                    )
                if next_q:
                    st.session_state.current_question = next_q
                    st.session_state.asked_questions.append(next_q["question"])
                    st.session_state.question_number += 1
                else:
                    st.session_state.current_question = None
                st.rerun()

        if skip:
            with st.spinner("Generating next question..."):
                next_q = generate_question(
                    skill=skill,
                    difficulty=st.session_state.current_difficulty,
                    role=role,
                    level=level,
                    exclude_questions=st.session_state.asked_questions,
                    use_llm=st.session_state.use_llm
                )
            if next_q:
                st.session_state.current_question = next_q
                st.session_state.asked_questions.append(next_q["question"])
                st.session_state.question_number += 1
            st.session_state.last_evaluation = None
            st.session_state.voice_transcript = ""
            st.rerun()

        if end:
            st.session_state.started = False
            st.rerun()

# --------------- Performance Dashboard (after interview) ---------------
if not st.session_state.started and st.session_state.history:
    st.markdown("---")
    st.markdown("## 📊 Performance Dashboard")

    history = st.session_state.history
    overall_scores = [h["scores"]["overall"] for h in history]
    avg = sum(overall_scores) / len(overall_scores) if overall_scores else 0

    # Top KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Questions Answered", len(history))
    k2.metric("Average Score", f"{avg:.0f}%")
    k3.metric("Highest Score", f"{max(overall_scores)}%" if overall_scores else "—")
    k4.metric("Lowest Score", f"{min(overall_scores)}%" if overall_scores else "—")

    # Score over time chart
    st.markdown("### Score Progression")
    chart_data = {
        "Question": list(range(1, len(overall_scores) + 1)),
        "Overall Score": overall_scores
    }
    st.line_chart(chart_data, x="Question", y="Overall Score", height=280)

    # Breakdown by dimension
    st.markdown("### Score Breakdown (Average)")
    dims = ["technical", "relevance", "completeness", "communication"]
    dim_avgs = {d: sum(h["scores"][d] for h in history) / len(history) for d in dims}
    st.bar_chart(dim_avgs, height=260)

    # Skill performance (if multiple skills appeared – currently mostly one)
    skill_scores = defaultdict(list)
    for h in history:
        skill_scores[h["skill"]].append(h["scores"]["overall"])
    if skill_scores:
        st.markdown("### Performance by Skill")
        skill_avg = {s: sum(v)/len(v) for s, v in skill_scores.items()}
        st.bar_chart(skill_avg, height=220)

    st.markdown("### Insights & Recommendations")
    weak_dims = [d for d, v in dim_avgs.items() if v < 65]
    strong_dims = [d for d, v in dim_avgs.items() if v >= 80]

    col_left, col_right = st.columns(2)
    with col_left:
        if strong_dims:
            st.success("**Strong areas:** " + ", ".join(d.title() for d in strong_dims))
        if weak_dims:
            st.error("**Needs improvement:** " + ", ".join(d.title() for d in weak_dims))
        else:
            st.info("No major weak dimensions detected.")

    with col_right:
        recommendations = []
        if "technical" in weak_dims:
            recommendations.append("Review core concepts of the focus skill and practice explaining them clearly.")
        if "completeness" in weak_dims:
            recommendations.append("Structure answers: definition → example → edge cases / trade-offs.")
        if "communication" in weak_dims:
            recommendations.append("Practice speaking or writing in short, clear sentences.")
        if "relevance" in weak_dims:
            recommendations.append("Always restate the question briefly, then answer directly.")
        if avg < 60:
            recommendations.append("Take another interview focusing on the same skill at easy/medium level.")
        if not recommendations:
            recommendations.append("Great job! Try a harder difficulty or a new skill next.")
        for i, rec in enumerate(recommendations, 1):
            st.write(f"{i}. {rec}")

    # Detailed history
    st.markdown("### Full Answer History")
    for i, h in enumerate(history, 1):
        with st.expander(f"Q{i} · {h['difficulty'].title()} · {h['scores']['overall']}%"):
            st.write("**Question:**", h["question"])
            st.write("**Your Answer:**", h["answer"])
            st.write("**Feedback:**", h["scores"]["feedback"])
            st.write(
                f"Technical {h['scores']['technical']}% · "
                f"Relevance {h['scores']['relevance']}% · "
                f"Completeness {h['scores']['completeness']}% · "
                f"Communication {h['scores']['communication']}%"
            )

    if st.button("🔄 Start New Interview", type="primary"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()
