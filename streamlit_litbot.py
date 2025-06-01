import streamlit as st
import smtplib
from email.message import EmailMessage
from datetime import datetime
import time
import io

# 기본 설정
st.set_page_config(page_title="문학 챗봇", layout="centered")
st.title("📚 문학 챗봇과의 대화")
st.markdown("작가 박서련의 단편소설 『나, 나, 마들렌』을 함께 읽고 이야기 나눠요.")

# 사용자 이름 받기
last_name = st.text_input("성과 이름을 입력해 주세요 (예: 김 / 민영)", value="", key="last_name")
first_name = st.text_input("", value="", key="first_name")
user_name = first_name.strip()

# Claude API 대체 - 모의 응답
def get_bot_response(user_input):
    return f"{user_name}, 네 생각이 흥미롭네. 그 부분에 대해 좀 더 이야기해줄 수 있어?"

# 이메일 전송 함수
def send_email_with_attachment(file, subject, body, filename):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = st.secrets["email"]["user"]
    msg["To"] = st.secrets["email"]["user"]
    msg.set_content(body)
    file_data = file.read()
    msg.add_attachment(file_data, maintype="application", subtype="octet-stream", filename=filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(st.secrets["email"]["user"], st.secrets["email"]["password"])
        smtp.send_message(msg)

# 1. 감상문 업로드
st.header("1. 감상문 업로드")
uploaded_review = st.file_uploader("감상문 파일을 업로드하세요 (.txt, .docx)", type=["txt", "docx"])
if uploaded_review and user_name:
    review_filename = f"{user_name}_감상문.{uploaded_review.name.split('.')[-1]}"
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", review_filename)
    st.success("감상문이 성공적으로 업로드되고 전송되었습니다.")

# 2. 문학 토론
st.header("2. 챗봇과 문학 토론")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "start_time" not in st.session_state:
    st.session_state.start_time = time.time()
if "chat_done" not in st.session_state:
    st.session_state.chat_done = False

if user_name and not st.session_state.chat_done:
    st.markdown("챗봇과의 대화를 시작해보세요. ⏳ 최대 10분 동안 가능합니다.")

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    user_input = st.chat_input("메시지를 입력하세요.")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        st.chat_message("user").write(user_input)

        response = get_bot_response(user_input)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.chat_message("assistant").write(response)

    elapsed_time = time.time() - st.session_state.start_time
    if 480 < elapsed_time < 600:
        st.info("⏰ 우리의 대화 시간이 얼마 남지 않았어요. 마지막으로 꼭 나누고 싶은 생각이 있다면 지금 이야기해 주세요!")
    elif elapsed_time >= 600:
        st.session_state.chat_done = True
        st.success("대화가 종료되었습니다. 대화 내용을 메일로 전송합니다.")
        chat_log = "\n".join([f'{m["role"]}: {m["content"]}' for m in st.session_state.messages])
        chat_file = io.BytesIO(chat_log.encode("utf-8"))
        chat_file.name = f"{user_name}_대화내용.txt"
        send_email_with_attachment(chat_file, f"[대화로그] {user_name}_대화내용", "챗봇과의 전체 대화 로그입니다.", chat_file.name)

# 3. 성찰일지 업로드
if st.session_state.chat_done:
    st.header("3. 성찰일지 업로드")
    reflection_file = st.file_uploader("성찰일지를 업로드하세요 (.txt, .docx)", type=["txt", "docx"], key="reflection")
    if reflection_file:
        reflection_filename = f"{user_name}_성찰일지.{reflection_file.name.split('.')[-1]}"
        send_email_with_attachment(reflection_file, f"[성찰일지] {user_name}_성찰일지", "사용자가 업로드한 성찰일지입니다.", reflection_filename)
        st.success("성찰일지가 성공적으로 전송되었습니다.")
