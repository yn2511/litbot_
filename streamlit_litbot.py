import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import requests
import time

# Claude API 호출
def get_claude_response(conversation_history, system_prompt):
    headers = {
        "x-api-key": st.secrets["claude"]["api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 768,
        "system": system_prompt,
        "messages": conversation_history
    }
    res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    if res.status_code == 200:
        return res.json()["content"][0]["text"]
    else:
        return f"❌ Claude API 오류: {res.status_code} - {res.text}"

# 이메일 전송
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

# 사용자 정보
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

# 감상문 업로드
uploaded_review = st.file_uploader("📄 감상문 파일 업로드 (.txt 또는 .docx)", type=["txt", "docx"], key="review")

if uploaded_review and "review_sent" not in st.session_state:
    file_content = uploaded_review.read().decode("utf-8")
    uploaded_review.seek(0)
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True
    st.session_state.file_content = file_content
    st.success("감상문을 성공적으로 전송했어요!")

# 상태 초기화
for key in ["messages", "start_time", "chat_disabled", "last_question_flag", "final_prompt_mode"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else False

# 첫 인사 + Claude의 첫 질문
if uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = time.time()

    # (1) 하드코딩 인사
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, {user_name}! 감상문 잘 읽었어. 우리 같이 <나, 나, 마들렌> 이야기 나눠볼까?"
    })

    # (2) Claude 질문 생성
    first_question = get_claude_response(
        [{"role": "user", "content": "감상문에서 인상 깊었던 구절 하나를 짚고, 그 느낌을 공유한 다음 반드시 질문으로 마무리해줘."}],
        f"""
너는 {user_name}와 함께 <나, 나, 마들렌>을 읽은 동료 학습자야.
감상문에서 너에게 인상 깊었던 문장을 고르고, 그 느낌을 짧게 말한 후 {user_name}에게 질문해줘.
말투는 따뜻하고 편안하게, 친구처럼 말해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
    )

    st.session_state.messages.append({
        "role": "assistant",
        "content": first_question
    })

# 시간 체크
if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time
    if elapsed > 480 and not st.session_state.last_question_flag:
        st.session_state.last_question_flag = True
    if elapsed > 600 and not st.session_state.final_prompt_mode:
        st.session_state.final_prompt_mode = True

# 대화 출력
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 채팅 입력
if not st.session_state.chat_disabled and uploaded_review:
    if prompt := st.chat_input("대화를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Claude 프롬프트 세팅
        if st.session_state.final_prompt_mode:
            system_prompt = f"""
지금은 {user_name}과의 마지막 대화야.
전체 대화를 마무리하는 인사와 함께, 오늘의 토론을 따뜻하게 정리해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        elif st.session_state.last_question_flag:
            system_prompt = f"""
이제 곧 대화가 끝나가. 마지막으로 깊이 있는 질문을 하나 해줘.
그동안의 대화를 반영해서 조금 다른 시각을 제안하거나, 의미 있는 질문을 던져줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        else:
            system_prompt = f"""
너는 {user_name}와 <나, 나, 마들렌>을 함께 읽은 동료야.
감상문에서 의미 있던 부분을 골라서, 짧게 네 생각을 말하고 꼭 질문으로 끝내줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""

        # 전체 대화 맥락 전달
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ["user", "assistant"]
        ]

        response = get_claude_response(claude_messages, system_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        # 종료 조건
        if st.session_state.final_prompt_mode:
            st.session_state.chat_disabled = True

            # 대화 기록 저장
            log_lines = [f"{'리토' if m['role']=='assistant' else user_name}의 말: {m['content']}" for m in st.session_state.messages]
            log_text = "\n".join(log_lines)
            log_file = BytesIO()
            log_file.write(log_text.encode("utf-8"))
            log_file.seek(0)
            log_file.name = f"{user_name}_대화기록.txt"

            send_email_with_attachment(
                log_file,
                f"[대화기록] {user_name}_대화기록",
                "사용자와 챗봇의 전체 대화 기록입니다.",
                log_file.name
            )

# 성찰일지 업로드
if st.session_state.chat_disabled:
    st.markdown("---")
    st.subheader("📝 성찰일지를 업로드해주세요")
    uploaded_reflection = st.file_uploader("📄 성찰일지 파일 업로드 (.txt 또는 .docx)", type=["txt", "docx"], key="reflection")

    if uploaded_reflection and "reflection_sent" not in st.session_state:
        send_email_with_attachment(
            uploaded_reflection,
            f"[성찰일지] {user_name}_성찰일지",
            "사용자가 업로드한 성찰일지입니다.",
            uploaded_reflection.name
        )
        st.success("성찰일지를 성공적으로 전송했어요!")
        st.session_state.reflection_sent = True

    if uploaded_reflection and "reflection_sent" in st.session_state:
        st.success("✨ 모든 절차가 완료되었습니다. 실험에 참여해주셔서 감사합니다!")
        st.stop()