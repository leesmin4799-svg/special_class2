import streamlit as st
import pandas as pd
import os
from datetime import datetime
from openai import OpenAI
import io

# OpenAI 클라이언트 설정 (실제 API 키로 교체하세요)
client = OpenAI(api_key="YOUR_OPENAI_API_KEY")

# 데이터 저장을 위한 CSV 파일 경로
DATA_FILE = "student_responses.csv"

# 세션 상태 초기화
if "step" not in st.session_state:
    st.session_state.step = 1
if "messages" not in st.session_state:
    st.session_state.messages = []
if "student_num" not in st.session_state:
    st.session_state.student_num = ""
if "student_name" not in st.session_state:
    st.session_state.student_name = ""
if "initial_answer" not in st.session_state:
    st.session_state.initial_answer = ""

st.title("⏳ 시간은 환상일까요?")

# 사이드바: 관리자 모드
with st.sidebar:
    st.header("🔒 관리자 모드")
    admin_pw = st.text_input("비밀번호를 입력하세요", type="password")
    
    if admin_pw == "admin123": # 관리자 비밀번호 (필요시 변경)
        st.success("관리자 인증 완료")
        if os.path.exists(DATA_FILE):
            df = pd.read_csv(DATA_FILE)
            st.dataframe(df)
            
            # 엑셀 다운로드 버튼
            towrite = io.BytesIO()
            df.to_excel(towrite, index=False, engine='openpyxl')
            towrite.seek(0)
            st.download_button(
                label="📥 엑셀 파일로 다운로드",
                data=towrite,
                file_name="student_time_responses.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.info("아직 제출된 데이터가 없습니다.")

# 메인 화면: 학생 인터랙션 흐름
st.write("즐거운 시간을 보낼 때는 시간이 쏜살같이 지나가고, 지루하거나 누군가를 기다릴 때는 시간이 느리게 가는 이유는 무엇일까요? 시간은 인간의 인식 밖에 실재하는 것일까요, 아니면 단지 우리의 뇌가 기억을 정리하기 위해 만들어낸 개념에 불과할까요?")
st.markdown("---")

# 1단계: 초기 답변 작성
if st.session_state.step == 1:
    st.subheader("Step 1. 나의 첫 번째 생각")
    
    # 학번과 이름 입력란을 가로로 배치
    col1, col2 = st.columns(2)
    with col1:
        student_num = st.text_input("학번을 입력해 주세요:")
    with col2:
        student_name = st.text_input("이름을 입력해 주세요:")
        
    initial_answer = st.text_area("위 질문에 대한 여러분의 솔직한 생각을 자유롭게 적어주세요.", height=150)
    
    if st.button("답변 제출 및 토론 시작하기"):
        # 학번, 이름, 답변이 모두 입력되었는지 확인
        if student_num and student_name and initial_answer:
            st.session_state.student_num = student_num
            st.session_state.student_name = student_name
            st.session_state.initial_answer = initial_answer
            st.session_state.step = 2
            
            # AI의 첫 질문 생성
            system_prompt = "너는 학생들의 철학적 사고를 돕는 소크라테스식 교사야. 학생이 '시간의 본질'에 대해 답변을 제출했어. 이 답변을 읽고, 학생의 생각을 더 깊이 파고들거나 새로운 관점을 제시하는 짧고 통찰력 있는 질문 하나만 던져줘."
            st.session_state.messages.append({"role": "system", "content": system_prompt})
            st.session_state.messages.append({"role": "user", "content": initial_answer})
            
            with st.spinner("AI가 학생의 답변을 읽고 질문을 준비 중입니다..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages
                )
                ai_reply = response.choices[0].message.content
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
            st.rerun()
        else:
            st.warning("학번, 이름, 그리고 답변을 모두 기재해 주세요.")

# 2단계: AI와의 대화 (챗봇)
elif st.session_state.step == 2:
    st.subheader(f"Step 2. AI와의 철학적 대화 ({st.session_state.student_name} 학생)")
    st.info("AI가 첫 번째 답변을 바탕으로 질문을 던졌습니다. 대화를 이어가며 생각을 정리해 보세요.")
    
    # 이전 대화 출력 (system 메시지 제외)
    for msg in st.session_state.messages:
        if msg["role"] != "system" and msg["content"] != st.session_state.initial_answer:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                
    # 채팅 입력
    if prompt := st.chat_input("AI의 질문에 답하거나 새로운 질문을 던져보세요."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        with st.chat_message("assistant"):
            with st.spinner("생각 중..."):
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=st.session_state.messages
                )
                ai_reply = response.choices[0].message.content
                st.markdown(ai_reply)
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        
    st.markdown("---")
    if st.button("토론을 마치고 최종 답변 작성하기"):
        st.session_state.step = 3
        st.rerun()

# 3단계: 최종 답변 작성 및 데이터 저장
elif st.session_state.step == 3:
    st.subheader("Step 3. 최종 결론")
    final_answer = st.text_area("AI와의 대화를 통해 생각에 어떤 변화가 있었나요? 최종적인 여러분의 결론을 적어주세요.", height=200)
    
    if st.button("최종 제출하기"):
        if final_answer:
            # CSV 파일에 데이터 저장 (학번, 이름 컬럼 분리)
            new_data = pd.DataFrame([{
                "제출시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "학번": st.session_state.student_num,
                "이름": st.session_state.student_name,
                "초기 답변": st.session_state.initial_answer,
                "최종 결론": final_answer
            }])
            
            if not os.path.exists(DATA_FILE):
                new_data.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')
            else:
                new_data.to_csv(DATA_FILE, mode='a', header=False, index=False, encoding='utf-8-sig')
                
            st.success("수고하셨습니다! 제출이 완료되었습니다.")
            
            # 상태 초기화 버튼
            if st.button("처음으로 돌아가기"):
                st.session_state.clear()
                st.rerun()
        else:
            st.warning("최종 답변을 작성해 주세요.")