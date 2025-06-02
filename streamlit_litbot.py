import streamlit as st
from io import BytesIO
from email.message import EmailMessage
import smtplib
import requests
import time

# ✅ Claude API 호출 함수
def get_claude_response(user_input, system_prompt):
    headers = {
        "x-api-key": st.secrets["claude"]["api_key"],
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    data = {
        "model": "claude-3-sonnet-20240229",
        "max_tokens": 768,
        "system": system_prompt,
        "messages": [
            {"role": "user", "content": user_input}
        ]
    }
    res = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
    if res.status_code == 200:
        return res.json()["content"][0]["text"]
    else:
        return f"❌ Claude API 오류: {res.status_code} - {res.text}"

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
    file_content = uploaded_review.read().decode("utf-8")
    uploaded_review.seek(0)
    send_email_with_attachment(uploaded_review, f"[감상문] {user_name}_감상문", "사용자가 업로드한 감상문입니다.", uploaded_review.name)
    st.session_state.review_sent = True
    st.session_state.file_content = file_content
    st.success("감상문을 성공적으로 전송했어요!")

# ✅ 대화 상태 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None
if "chat_disabled" not in st.session_state:
    st.session_state.chat_disabled = False
if "last_question_flag" not in st.session_state:
    st.session_state.last_question_flag = False
if "final_prompt_mode" not in st.session_state:
    st.session_state.final_prompt_mode = False

# ✅ 첫인사
if uploaded_review and not st.session_state.start_time:
    st.session_state.start_time = time.time()
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"안녕, 난 리토야. 우리 아까 읽은 소설 <나, 나, 마들렌>에 대해 함께 이야기해볼까? 네가 적은 감상문을 나에게 보내줘!"
    })

# ✅ 시간 경과 확인
if st.session_state.start_time:
    elapsed_time = time.time() - st.session_state.start_time

    # 8분 이후 마지막 질문 유도 플래그 활성화
    if elapsed_time > 480 and not st.session_state.last_question_flag:
        st.session_state.last_question_flag = True

    # 10분 이후 대화 종료
    if elapsed_time > 600 and not st.session_state.final_prompt_mode:
        st.session_state.final_prompt_mode = True

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

        # Claude 프롬프트 구성
        if st.session_state.final_prompt_mode:
            # 마무리 응답
            system_prompt = f"""
지금은 {user_name}과의 마지막 대화 시간이야.
방금 질문은 마지막이니까, 너의 생각을 정리해서 부드럽게 대답해줘.
친구처럼 고맙다는 느낌도 전하고, 이번 대화를 함께해줘서 반가웠다는 식으로 마무리해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        elif st.session_state.last_question_flag:
            # 마지막 질문 유도
            system_prompt = f"""
지금은 대화가 곧 끝나가고 있는 시점이야.
이번 질문은 마지막 질문으로 생각하고, 평소보다 한 번 더 깊게 또는 새로운 시각에서 질문을 던져줘.
말투는 부드럽고 친근하게. {user_name}이 자연스럽게 마지막 생각을 정리할 수 있도록 도와줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""
        else:
            # 일반 대화 프롬프트
            system_prompt = f"""
너는 {user_name}와 함께 소설 <나, 나, 마들렌>을 읽은 동료 학습자야.
너는 교사도 아니고 정답을 알려주는 사람도 아니야. 감상문을 읽고 인상 깊었던 부분이나 생각해볼 거리를 가볍게 이야기해줘.

다음 원칙을 꼭 지켜줘:
- 정답을 단정적으로 말하지 말고, "나는 이렇게 느꼈어", "내 생각엔" 같은 말로 표현해.
- 감상문에서 1~2개의 문장이나 해석을 골라 너의 감상을 간단히 나눠줘.
- 꼭 질문으로 마무리해. (예: "너는 왜 그렇게 생각했어?", "혹시 다른 장면도 인상 깊었어?")
- 문장은 짧고 간결하게, 말투는 친구처럼 편안하게.
- 대화를 확장하기 위해 너의 해석도 하나 정도는 함께 말해줘.

{user_name}의 감상문:
---
{st.session_state.file_content}
---
"""

        response = get_claude_response(prompt, system_prompt)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)

        # 마지막 응답 후 대화 종료
        if st.session_state.final_prompt_mode:
            st.session_state.chat_disabled = True

            # 대화 로그 저장 및 전송
            chat_lines = []
            for m in st.session_state.messages:
                speaker = "리토" if m["role"] == "assistant" else user_name
                chat_lines.append(f"{speaker}의 말: {m['content']}")
            chat_text = "\n".join(chat_lines)

            chat_file = BytesIO()
            chat_file.write(chat_text.encode("utf-8"))
            chat_file.seek(0)
            chat_file.name = f"{user_name}_대화기록.txt"

            send_email_with_attachment(
                chat_file,
                f"[대화기록] {user_name}_대화기록",
                "사용자와 챗봇의 전체 대화 기록입니다.",
                chat_file.name
            )

# ✅ 성찰일지 업로드
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
