# -*- coding: utf-8 -*-
import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import requests
import time

def get_claude_response(conversation_history, system_prompt):
    headers = {
        "x-api-key": st.secrets["claude"]["api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 512,
        "system": system_prompt,
        "messages": conversation_history
    }
    res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    if res.status_code == 200:
        return res.json()["content"][0]["text"]
    else:
        return f"❌ Claude API 오류: {res.status_code} - {res.text}"

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

st.title("📚 문학 토론 챗봇 - 리토")
col1, col2 = st.columns(2)
with col1:
    user_lastname = st.text_input("성을 입력해주세요", key="lastname")
with col2:
    user_firstname = st.text_input("이름을 입력해주세요", key="firstname")

if user_lastname and user_firstname:
    user_name = user_firstname
    st.success(f"안녕하세요, {user_name}님! 감상문을 업로드해주세요.")
else:
    st.warning("👤 이름과 성을 먼저 입력해주세요.")
    st.stop()

uploaded_review = st.file_uploader("📄 감상문 업로드 (.txt 또는 .docx)", type=["txt", "docx"], key="review")

if uploaded_review and "review_sent" not in st.session_state:
    file_content = uploaded_review.read().decode("utf-8")
    uploaded_review.seek(0)
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True
    st.session_state.file_content = file_content
    st.success("✅ 감상문을 성공적으로 전송했어요!")

for key in ["messages", "start_time", "chat_disabled", "last_question_flag", "final_prompt_mode"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key == "messages" else False

if uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = time.time()

    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, {user_name}! 감상문 잘 읽었어. 우리 같이 <나, 나, 마들렌> 이야기 나눠볼까?"
    })

    first_question = get_claude_response(
        [{"role": "user", "content": "감상문에서 인상 깊었던 구절 하나를 골라 짧게 말한 후 질문을 해줘."}],
        f"""
너는 {user_name}와 함께 <나, 나, 마들렌>을 읽은 동료 학습자야.
감상문에서 인상 깊은 구절을 짚고, 간결하게 너의 느낌을 말한 다음,
반드시 열린 질문으로 마무리해줘. 3~5문장 이내로 짧게 말해.

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

# 타이머 체크 (3분 테스트용: 180초)
if st.session_state.start_time:
    elapsed = time.time() - st.session_state.start_time

    if elapsed > 180 and not st.session_state.final_prompt_mode:
        st.session_state.final_prompt_mode = True

        final_prompt = f"""
지금은 마지막 응답이야.
사용자와 나눈 대화를 간단히 정리하고, 따뜻한 인사로 마무리해줘.
질문은 하지 말고, 3~5문장 이내로 간결하게 말해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ["user", "assistant"]
        ]

        response = get_claude_response(claude_messages, final_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.session_state.chat_disabled = True

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

        st.info("🕰️ 대화 시간이 종료되었습니다. 아래에서 성찰일지를 업로드해주세요.")

# 채팅 출력
for m in st.session_state.messages:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])

# 사용자 입력
if not st.session_state.chat_disabled and uploaded_review:
    if prompt := st.chat_input("✍️ 대화를 입력하세요"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        system_prompt = f"""
너는 {user_name}와 함께 <나, 나, 마들렌>을 읽은 동료야.
감상문을 참고해서 간결한 너의 감상을 전하고, 열린 질문으로 마무리해줘.
가능하면 다른 관점을 제시하거나, 다시 생각해볼만한 질문을 던져줘.

응답은 3~5문장 이내로 말해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        claude_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in st.session_state.messages
            if m["role"] in ["user", "assistant"]
        ]

        response = get_claude_response(claude_messages, system_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

# 성찰일지 업로드
if st.session_state.chat_disabled:
    st.markdown("---")
    st.subheader("📝 성찰일지를 업로드해주세요")
    uploaded_reflection = st.file_uploader("📄 성찰일지 (.txt 또는 .docx)", type=["txt", "docx"], key="reflection")

    if uploaded_reflection and "reflection_sent" not in st.session_state:
        send_email_with_attachment(
            uploaded_reflection,
            f"[성찰일지] {user_name}_성찰일지",
            "사용자가 업로드한 성찰일지입니다.",
            uploaded_reflection.name
        )
        st.success("📩 성찰일지를 성공적으로 전송했어요!")
        st.session_state.reflection_sent = True

    if uploaded_reflection and "reflection_sent" in st.session_state:
        st.success("🎉 모든 절차가 완료되었습니다. 실험에 참여해주셔서 감사합니다!")
        st.stop()
