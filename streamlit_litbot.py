import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import time

# ✅ 이메일 전송 함수
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

# ✅ 사용자 정보
st.title("문학 토론 챗봇 - 리토")
col1, col2 = st.columns(2)
with col1:
    user_lastname = st.text_input("성을 입력하세요", key="lastname")
with col2:
    user_firstname = st.text_input("이름을 입력하세요", key="firstname")

if user_lastname and user_firstname:
    user_name = user_firstname
    st.success(f"안녕하세요, {user_name}님! 아래에 감상문을 업로드해주세요.")
else:
    st.warning("먼저 이름과 성을 입력해주세요.")
    st.stop()

# ✅ 감상문 업로드
uploaded_review = st.file_uploader("📄 감상문 파일 업로드 (.txt 또는 .docx)", type=["txt", "docx"], key="review")

if uploaded_review and "review_sent" not in st.session_state:
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True
    st.success("감상문을 성공적으로 전송했어요!")

# ✅ 소설 원문 불러오기
with open("나, 나, 마들렌_박서련.txt", "r", encoding="utf-8") as f:
    novel_text = f.read()

# ✅ 대화 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "chat_disabled" not in st.session_state:
    st.session_state.chat_disabled = False

# ✅ 대화 시작 조건
if uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = time.time()
    st.session_state.messages.append({"role": "assistant", "content": f"안녕, 난 리토야. 우리 아까 읽은 소설 <나, 나, 마들렌>에 대해 함께 이야기해볼까? 네가 적은 감상문을 나에게 보내줘!"})

# ✅ 타이머 종료 조건 (테스트용: 10초)
if st.session_state.start_time and not st.session_state.chat_disabled:
    elapsed_time = time.time() - st.session_state.start_time
    if elapsed_time > 10:
        st.session_state.chat_disabled = True
        st.session_state.messages.append({"role": "assistant", "content": "⏰ 시간이 다 되었어. 대화는 여기까지 할게!"})

        # 대화 로그 자연어 정리 후 전송
        chat_lines = []
        for m in st.session_state.messages:
            speaker = "리토" if m["role"] == "assistant" else user_name
            chat_lines.append(f"{speaker}의 말: {m['content']}")
        chat_text = "\n".join(chat_lines)

        chat_file = BytesIO()
        chat_file.write(chat_text.encode("utf-8"))
        chat_file.seek(0)
        chat_file.name = f"{user_name}_대화기록.txt"

        send_email_with_attachment(chat_file, f"[대화기록] {user_name}_대화기록", "사용자와 챗봇의 전체 대화 기록입니다.", chat_file.name)

# ✅ 메시지 출력
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# ✅ 채팅 입력
if not st.session_state.chat_disabled and uploaded_review:
    if prompt := st.chat_input("대화를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 간단한 챗봇 응답 (실제 Claude API로 대체 예정)
        response = f"{user_name}, 너의 생각이 흥미로워. 나는 조금 다르게 느꼈는데, 너는 '{prompt}'에 대해 왜 그렇게 생각했어?"
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# ✅ 성찰일지 업로드
if st.session_state.chat_disabled:
    st.markdown("---")
    st.subheader("📝 성찰일지를 업로드해주세요")
    uploaded_reflection = st.file_uploader("📄 성찰일지 파일 업로드 (.txt 또는 .docx)", type=["txt", "docx"], key="reflection")

    if uploaded_reflection and "reflection_sent" not in st.session_state:
        send_email_with_attachment(uploaded_reflection, f"[성찰일지] {user_name}_성찰일지", "사용자가 업로드한 성찰일지입니다.", uploaded_reflection.name)
        st.success("성찰일지를 성공적으로 전송했어요!")
        st.session_state.reflection_sent = True
