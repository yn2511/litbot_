import streamlit as st
from datetime import datetime, timedelta
from io import BytesIO
import smtplib
from email.message import EmailMessage
import time

# 초기 세션 상태 설정
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "ended" not in st.session_state:
    st.session_state.ended = False
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("📚 문학토론 챗봇 - 리토")

# 사용자 이름 입력
col1, col2 = st.columns(2)
with col1:
    user_last = st.text_input("성과 이름을 입력해주세요", placeholder="성", key="last_name")
with col2:
    user_first = st.text_input(" ", placeholder="이름", key="first_name")

user_name = user_first.strip()

# 감상문 업로드
uploaded_review = st.file_uploader("✍ 감상문 파일 업로드 (txt/docx)", type=["txt", "docx"])

# 챗봇 시작 조건 충족 시 안내멘트
if user_name and uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = datetime.now()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, 난 리토야. 우리 아까 읽은 소설 <나, 나, 마들렌>에 대해 함께 이야기해볼까? {user_name}가 적은 감상문을 잘 읽었어!"
    })

# 대화 시간 초과 체크
if st.session_state.start_time and not st.session_state.ended:
    elapsed = datetime.now() - st.session_state.start_time
    if elapsed.total_seconds() >= 10:  # ✅ 테스트용 10초
        st.session_state.ended = True
        st.warning("⏰ 대화 시간이 종료되었어요. 수고했어요!")

        # 대화 로그 자연어 저장
        chat_lines = []
        for m in st.session_state.messages:
            role = "리토" if m["role"] == "assistant" else user_name
            chat_lines.append(f"{role}의 말: {m['content']}")
        chat_text = "\n".join(chat_lines)
        chat_file = BytesIO()
        chat_file.write(chat_text.encode("utf-8"))
        chat_file.seek(0)
        chat_file.name = f"{user_name}_대화기록.txt"

        # 메일 전송
        send_email_with_attachment(chat_file, f"[대화기록] {user_name}_대화기록", "사용자와 챗봇의 전체 대화 기록입니다.", chat_file.name)

# 채팅 인터페이스
for msg in st.session_state.messages:
    with st.chat_message("assistant" if msg["role"] == "assistant" else "user"):
        st.markdown(msg["content"])

# 입력 가능 여부
if not uploaded_review or not user_name:
    st.info("👆 감상문과 이름을 모두 입력해야 대화를 시작할 수 있어요.")
elif not st.session_state.ended:
    user_msg = st.chat_input(f"{user_name}, 리토와 이야기해보세요!")
    if user_msg:
        st.session_state.messages.append({"role": "user", "content": user_msg})
        with st.chat_message("user"):
            st.markdown(user_msg)

        # 단순 반응 로직
        response = f"{user_name}, 너의 생각이 흥미로워. 나는 조금 다르게 느꼈는데, 너는 왜 그렇게 생각했어?"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# 성찰일지 업로드 (종료 후만 가능)
if st.session_state.ended:
    uploaded_reflection = st.file_uploader("📝 성찰일지를 업로드해주세요", type=["txt", "docx"])
    if uploaded_reflection:
        send_email_with_attachment(uploaded_reflection, f"[성찰일지] {user_name}_성찰일지", "사용자가 작성한 성찰일지입니다.", uploaded_reflection.name)
        st.success("📨 성찰일지를 성공적으로 전송했어요!")

# 감상문 전송은 최초 1회만
if uploaded_review and "review_sent" not in st.session_state:
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True

# 이메일 전송 함수
def send_email_with_attachment(file, subject, body, filename):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = st.secrets["email"]["user"]
    msg["To"] = "mveishu@gmail.com"
    msg.set_content(body)

    file_bytes = file.read()
    msg.add_attachment(file_bytes, maintype="application", subtype="octet-stream", filename=filename)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(st.secrets["email"]["user"], st.secrets["email"]["password"])
        smtp.send_message(msg)
