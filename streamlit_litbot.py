import streamlit as st
import datetime
import time
import random
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from io import StringIO

st.title("📚 문학토론 챗봇 (테스트 모드)")
surname = st.text_input("성을 입력하세요:")
givenname = st.text_input("이름을 입력하세요:")

if not surname or not givenname:
    st.stop()

user_name = givenname

if "messages" not in st.session_state:
    st.session_state.messages = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "review_sent" not in st.session_state:
    st.session_state.review_sent = False
if "reflection_sent" not in st.session_state:
    st.session_state.reflection_sent = False
if "chat_log_sent" not in st.session_state:
    st.session_state.chat_log_sent = False
if "chat_ended" not in st.session_state:
    st.session_state.chat_ended = False

def send_email_with_attachment(file, subject, body, filename):
    msg = MIMEMultipart()
    msg["From"] = st.secrets["email"]["user"]
    msg["To"] = st.secrets["email"]["user"]
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))
    part = MIMEApplication(file.read(), Name=filename)
    part["Content-Disposition"] = f'attachment; filename="{filename}"'
    msg.attach(part)

    smtp = smtplib.SMTP("smtp.gmail.com", 587)
    smtp.starttls()
    smtp.login(st.secrets["email"]["user"], st.secrets["email"]["password"])
    smtp.send_message(msg)
    smtp.quit()

uploaded_review = st.file_uploader("✍ 감상문 파일 업로드", type=["txt", "docx"], key="review")
if uploaded_review and not st.session_state.review_sent:
    review_filename = f"{user_name}_감상문.{uploaded_review.name.split('.')[-1]}"
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", review_filename)
    st.success("📤 감상문 파일이 메일로 전송되었어요.")
    st.session_state.review_sent = True
    st.session_state.start_time = datetime.datetime.now()

if not st.session_state.review_sent:
    st.info("💡 감상문 파일을 업로드하면 대화를 시작할 수 있어요.")
    st.stop()

st.markdown("### 🤖 문학 토론을 시작해볼까요?")
if len(st.session_state.messages) == 0:
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, 난 리토야. 우리 아까 읽은 소설 <나, 나, 마들렌>에 대해 함께 이야기해볼까? 네가 적은 감상문을 나에게 보내줬다면, 바로 시작해보자!"
    })

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

seed_questions = [
    "마들렌이라는 인물은 너에게 어떤 느낌이었어?",
    "주인공의 마지막 선택을 어떻게 이해했어?",
    "이 작품에서 반복되는 상징이 있었다고 생각해?",
    "마들렌과 화자의 관계는 어떻게 변화했을까?",
    "너는 '나'의 감정에 공감할 수 있었어?"
]

def get_bot_response(user_input):
    follow_up = random.choice(seed_questions)
    return f"{user_name}, 너의 생각이 흥미로워. 나는 조금 다르게 느꼈는데, {follow_up}"

if st.session_state.start_time:
    elapsed = (datetime.datetime.now() - st.session_state.start_time).total_seconds()
else:
    elapsed = 0

if elapsed > 10 and not st.session_state.chat_log_sent:
    st.warning("⏰ 테스트용 타이머 종료! 대화 시간이 종료되었어요.")
    st.session_state.chat_ended = True

    chat_lines = []
    for m in st.session_state.messages:
        role = "리토" if m["role"] == "assistant" else user_name
        chat_lines.append(f"{role}의 말: {m['content']}")
    chat_text = "\n".join(chat_lines)
    chat_file = StringIO(chat_text)
    chat_file.name = f"{user_name}_대화기록.txt"
    send_email_with_attachment(chat_file, f"[대화기록] {user_name}_대화기록", "사용자와 챗봇의 전체 대화 기록입니다.", chat_file.name)
    st.session_state.chat_log_sent = True

if not st.session_state.chat_ended:
    user_input = st.chat_input("메시지를 입력하세요.")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        banned_words = ["멍청", "병신", "장애", "죽어", "혐오", "개같"]
        if any(bad in user_input for bad in banned_words):
            bot_response = "⚠️ 이 대화에는 부적절한 표현이 포함되어 있어. 다른 방식으로 표현해 줄래?"
        else:
            bot_response = get_bot_response(user_input)

        st.session_state.messages.append({"role": "assistant", "content": bot_response})
        with st.chat_message("assistant"):
            st.markdown(bot_response)
else:
    st.info("대화 시간이 끝나 채팅 입력이 비활성화되었어요.")

uploaded_reflection = st.file_uploader("📝 성찰일지 파일 업로드", type=["txt", "docx"], key="reflection")
if uploaded_reflection and not st.session_state.reflection_sent:
    reflection_filename = f"{user_name}_성찰일지.{uploaded_reflection.name.split('.')[-1]}"
    send_email_with_attachment(uploaded_reflection, f"[성찰일지] {user_name}_성찰일지", "사용자가 업로드한 성찰일지 파일입니다.", reflection_filename)
    st.success("📤 성찰일지가 메일로 전송되었어요.")
    st.session_state.reflection_sent = True
