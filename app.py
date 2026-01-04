import streamlit as st
import pandas as pd
import os
from datetime import datetime
import re

# ==========================================================
# 기본 설정
# ==========================================================
st.set_page_config(page_title="양복점 CRM 대시보드", layout="wide")

DATA_DIR = "data_members"
SETTINGS_DIR = "settings"

MASTER_FILE = os.path.join(DATA_DIR, "members_master.xlsx")
MEASURE_FILE = os.path.join(DATA_DIR, "members_measurements.xlsx")
SIZE_RULE_FILE = os.path.join(SETTINGS_DIR, "size_rules.xlsx")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)

# ==========================================================
# 공통 유틸
# ==========================================================
def inch_to_cm(val):
    try:
        return round(float(val) * 2.54, 1)
    except:
        return None

def normalize_birth_date(val):
    try:
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except:
        return ""

def clean_phone(value):
    if pd.isna(value):
        return ""
    digits = re.sub(r"[^0-9]", "", str(value))
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return ""

# ==========================================================
# 설정 – 사이즈 규칙
# ==========================================================
def ensure_size_rule_file():
    if not os.path.exists(SIZE_RULE_FILE):
        df = pd.DataFrame({
            "가슴_cm_하한": [92, 96, 100, 104],
            "가슴_cm_상한": [95, 99, 103, 107],
            "상의호칭": ["K48", "K50", "K52", "K54"]
        })
        df.to_excel(SIZE_RULE_FILE, index=False)

def recommend_jacket_size(chest_cm):
    if pd.isna(chest_cm):
        return "추천 불가"
    rules = pd.read_excel(SIZE_RULE_FILE)
    for _, r in rules.iterrows():
        if r["가슴_cm_하한"] <= chest_cm <= r["가슴_cm_상한"]:
            return r["상의호칭"]
    return "규칙 없음"

# ==========================================================
# 파일 보장
# ==========================================================
if not os.path.exists(MASTER_FILE):
    pd.DataFrame(columns=[
        "member_id", "이름", "생년월일", "전화번호",
        "주소", "직업", "첫방문일",
        "방문목적", "소개인", "특이사항", "등록상태"
    ]).to_excel(MASTER_FILE, index=False)

if not os.path.exists(MEASURE_FILE):
    pd.DataFrame(columns=[
        "member_id", "측정일",
        "어깨_in", "어깨_cm",
        "가슴_in", "가슴_cm",
        "허리_in", "허리_cm",
        "엉덩이_in", "엉덩이_cm",
        "소매_in", "소매_cm",
        "총장_in", "총장_cm",
        "추천_상의호칭"
    ]).to_excel(MEASURE_FILE, index=False)

# ==========================================================
# 데이터 로드
# ==========================================================
members = pd.read_excel(MASTER_FILE)
measures = pd.read_excel(MEASURE_FILE)

# ==========================================================
# 사이드바
# ==========================================================
page = st.sidebar.radio(
    "메뉴 선택",
    ["전체 대시보드", "회원 관리", "설정"]
)

# ==========================================================
# 전체 대시보드
# ==========================================================
if page == "전체 대시보드":
    st.title("양복점 CRM 요약 대시보드")

    st.metric("총 회원 수", len(members))
    st.metric("치수 등록 건수", len(measures))

# ==========================================================
# 회원 관리
# ==========================================================
elif page == "회원 관리":
    st.title("회원 관리 · 상담 / 치수 입력")

    # -------------------------
    # 회원 검색
    # -------------------------
    st.subheader("회원 검색")

    selected_member = st.session_state.get("selected_member")

    mode = st.radio("검색 방식", ["회원번호", "이름"])

    if mode == "회원번호":
        key = st.text_input("회원번호 입력")
        if key:
            result = members[members["member_id"].str.contains(key, na=False)]
            st.dataframe(result)
            if len(result) == 1:
                selected_member = result.iloc[0]["member_id"]

    else:
        key = st.text_input("이름 입력")
        if key:
            result = members[members["이름"].str.contains(key, na=False)]
            if not result.empty:
                pick = st.selectbox(
                    "선택",
                    result["member_id"] + " - " + result["이름"]
                )
                selected_member = pick.split(" - ")[0]

    # -------------------------
    # 신규 회원 등록
    # -------------------------
    st.markdown("---")
    if st.button("➕ 신규 회원 등록"):
        st.session_state.show_register = True

    if st.session_state.get("show_register"):
        st.subheader("신규 회원 등록")

        name = st.text_input("이름")
        birth = st.date_input("생년월일")
        phone = st.text_input("전화번호")
        purpose = st.text_input("방문목적")
        ref = st.text_input("소개인")
        note = st.text_area("특이사항")

        if st.button("등록 완료"):
            new_id = f"M{len(members)+1:04d}"
            new_row = {
                "member_id": new_id,
                "이름": name,
                "생년월일": birth.strftime("%Y-%m-%d"),
                "전화번호": clean_phone(phone),
                "주소": "",
                "직업": "",
                "첫방문일": datetime.now().strftime("%Y-%m-%d"),
                "방문목적": purpose,
                "소개인": ref,
                "특이사항": note,
                "등록상태": "정상"
            }
            members = pd.concat([members, pd.DataFrame([new_row])])
            members.to_excel(MASTER_FILE, index=False)

            st.session_state.selected_member = new_id
            st.session_state.show_register = False
            st.rerun()

    # -------------------------
    # 상담 / 치수 입력
    # -------------------------
    if selected_member:
        st.markdown("---")
        info = members[members["member_id"] == selected_member].iloc[0]

        st.subheader(f"상담 및 치수 입력 – {info['이름']} ({selected_member})")

        with st.form("measure_form"):
            m_date = st.date_input("측정일", value=datetime.now())

            c1, c2, c3 = st.columns(3)
            with c1:
                shoulder_in = st.number_input("어깨 (inch)", step=0.1)
                chest_in = st.number_input("가슴 (inch)", step=0.1)
            with c2:
                waist_in = st.number_input("허리 (inch)", step=0.1)
                hip_in = st.number_input("엉덩이 (inch)", step=0.1)
            with c3:
                sleeve_in = st.number_input("소매 (inch)", step=0.1)
                length_in = st.number_input("총장 (inch)", step=0.1)

            save = st.form_submit_button("치수 저장")

        if save:
            chest_cm = inch_to_cm(chest_in)
            size = recommend_jacket_size(chest_cm)

            row = {
                "member_id": selected_member,
                "측정일": m_date.strftime("%Y-%m-%d"),
                "어깨_in": shoulder_in, "어깨_cm": inch_to_cm(shoulder_in),
                "가슴_in": chest_in, "가슴_cm": chest_cm,
                "허리_in": waist_in, "허리_cm": inch_to_cm(waist_in),
                "엉덩이_in": hip_in, "엉덩이_cm": inch_to_cm(hip_in),
                "소매_in": sleeve_in, "소매_cm": inch_to_cm(sleeve_in),
                "총장_in": length_in, "총장_cm": inch_to_cm(length_in),
                "추천_상의호칭": size
            }

            measures = pd.concat([measures, pd.DataFrame([row])])
            measures.to_excel(MEASURE_FILE, index=False)
            st.success("치수 저장 완료")
            st.rerun()

        # 최근 치수
        st.subheader("최근 치수 기록")
        history = measures[measures["member_id"] == selected_member]
        history = history.sort_values("측정일", ascending=False)
        st.dataframe(history.head(5))

# ==========================================================
# 설정
# ==========================================================
elif page == "설정":
    st.title("설정 – 사이즈 규칙 / 매장 약속 용어")

    ensure_size_rule_file()
    rules = pd.read_excel(SIZE_RULE_FILE)

    st.subheader("상의 사이즈 규칙")
    edited = st.data_editor(rules, num_rows="dynamic")

    if st.button("저장"):
        edited.to_excel(SIZE_RULE_FILE, index=False)
        st.success("저장 완료")
