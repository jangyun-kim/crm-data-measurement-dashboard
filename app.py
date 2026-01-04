import os
import re
from datetime import datetime
import pandas as pd
import streamlit as st
import json

# ==========================================================
# 기본 설정
# ==========================================================
st.set_page_config(page_title="양복점 CRM 대시보드", layout="wide")

DATA_DIR = "data_members"
SETTINGS_DIR = "settings"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)

MASTER_FILE = os.path.join(DATA_DIR, "members_master.xlsx")
MEASURE_FILE = os.path.join(DATA_DIR, "members_measurements.xlsx")
CONSULT_FILE = os.path.join(DATA_DIR, "consultations.xlsx")
SIZE_RULE_FILE = os.path.join(SETTINGS_DIR, "size_rules.xlsx")

# ==========================================================
# 공통: 컬럼 표준/한글 매핑 (members/consult 내부처리용)
# ==========================================================
COL_INTERNAL_MEMBERS = [
    "member_id", "name", "birth_date", "phone",
    "address", "job", "first_visit", "note", "status"
]

COL_KOR_MAP_MEMBERS = {
    "member_id": "회원번호",
    "name": "이름",
    "birth_date": "생년월일",
    "phone": "전화번호",
    "address": "주소",
    "job": "직업",
    "first_visit": "첫방문일",
    "note": "메모",
    "status": "등록상태",
}
COL_ENG_MAP_MEMBERS = {v: k for k, v in COL_KOR_MAP_MEMBERS.items()}

COL_INTERNAL_CONSULT = [
    "consult_id", "member_id", "consult_date",
    "visit_purpose", "referrer", "special_notes", "consult_note",
    "created_at"
]
COL_KOR_MAP_CONSULT = {
    "consult_id": "상담번호",
    "member_id": "회원번호",
    "consult_date": "상담일",
    "visit_purpose": "방문목적",
    "referrer": "소개인",
    "special_notes": "고객특이사항",
    "consult_note": "상담메모",
    "created_at": "등록시각",
}

COL_INTERNAL_MEASURES = [
    "member_id", "measure_date",
    "shoulder_in", "shoulder_cm",
    "chest_in", "chest_cm",
    "waist_in", "waist_cm",
    "hip_in", "hip_cm",
    "sleeve_in", "sleeve_cm",
    "length_in", "length_cm",
    "recommended_jacket_size"
]

COL_KOR_MAP_MEASURES = {
    "member_id": "회원번호",
    "measure_date": "측정일",
    "shoulder_in": "어깨_in",
    "shoulder_cm": "어깨_cm",
    "chest_in": "가슴_in",
    "chest_cm": "가슴_cm",
    "waist_in": "허리_in",
    "waist_cm": "허리_cm",
    "hip_in": "엉덩이_in",
    "hip_cm": "엉덩이_cm",
    "sleeve_in": "소매_in",
    "sleeve_cm": "소매_cm",
    "length_in": "총장_in",
    "length_cm": "총장_cm",
    "recommended_jacket_size": "추천_상의호칭",
}

COL_ENG_MAP_MEASURES = {v: k for k, v in COL_KOR_MAP_MEASURES.items()}
COL_ENG_MAP_CONSULT = {v: k for k, v in COL_KOR_MAP_CONSULT.items()}

# ==========================================================
# 유틸
# ==========================================================
def df_to_kor(df, kind="members"):
    if df is None or df.empty:
        return df
    if kind == "members":
        return df.rename(columns=COL_KOR_MAP_MEMBERS)
    if kind == "consult":
        return df.rename(columns=COL_KOR_MAP_CONSULT)
    return df

def df_to_eng(df, kind="members"):
    if df is None or df.empty:
        return df
    if kind == "members":
        return df.rename(columns=COL_ENG_MAP_MEMBERS)
    if kind == "consult":
        return df.rename(columns=COL_ENG_MAP_CONSULT)
    return df

def inch_to_cm(val):
    try:
        return round(float(val) * 2.54, 1)
    except:
        return None

def normalize_birth_date(val):
    try:
        if pd.isna(val) or str(val).strip() == "":
            return ""
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
    if pd.isna(chest_cm) or chest_cm is None:
        return "추천 불가"
    rules = pd.read_excel(SIZE_RULE_FILE)
    for _, r in rules.iterrows():
        if r["가슴_cm_하한"] <= chest_cm <= r["가슴_cm_상한"]:
            return r["상의호칭"]
    return "규칙 없음"

# ==========================================================
# 파일 생성 보장
# ==========================================================
def ensure_files():
    # 회원: 저장은 한글 컬럼으로 저장(엑셀 보기 편하게)
    if not os.path.exists(MASTER_FILE):
        df = pd.DataFrame(columns=[COL_KOR_MAP_MEMBERS[c] for c in COL_INTERNAL_MEMBERS])
        df.to_excel(MASTER_FILE, index=False)

    # 치수: 한글 컬럼으로 저장(현장 입력용)
    if not os.path.exists(MEASURE_FILE):
        pd.DataFrame(columns=[
            "회원번호", "측정일",
            "어깨_in", "어깨_cm",
            "가슴_in", "가슴_cm",
            "허리_in", "허리_cm",
            "엉덩이_in", "엉덩이_cm",
            "소매_in", "소매_cm",
            "총장_in", "총장_cm",
            "추천_상의호칭"
        ]).to_excel(MEASURE_FILE, index=False)

    # 상담: 내부처리(영문)지만 저장은 한글로
    if not os.path.exists(CONSULT_FILE):
        df = pd.DataFrame(columns=[COL_KOR_MAP_CONSULT[c] for c in COL_INTERNAL_CONSULT])
        df.to_excel(CONSULT_FILE, index=False)

ensure_files()
ensure_size_rule_file()

# ==========================================================
# 로드/세이브 (중요: 내부처리는 영문 컬럼 통일)
# ==========================================================
def read_members():
    df = pd.read_excel(MASTER_FILE)
    # 한글 컬럼이면 영문으로 변환
    if "이름" in df.columns:
        df = df_to_eng(df, "members")

    # 누락 컬럼 보정
    for c in COL_INTERNAL_MEMBERS:
        if c not in df.columns:
            df[c] = ""

    # birth_date 정규화
    df["birth_date"] = df["birth_date"].apply(normalize_birth_date)
    df["phone"] = df["phone"].apply(clean_phone)

    return df[COL_INTERNAL_MEMBERS]

def save_members(df_internal):
    df_internal = df_internal.copy()
    # 내부(영문) -> 한글로 저장
    df_kor = df_to_kor(df_internal, "members")
    df_kor.to_excel(MASTER_FILE, index=False)

def df_to_kor_measures(df):
    if df is None or df.empty:
        return df
    return df.rename(columns=COL_KOR_MAP_MEASURES)

def df_to_eng_measures(df):
    if df is None or df.empty:
        return df
    return df.rename(columns=COL_ENG_MAP_MEASURES)

def ensure_measures_file():
    if not os.path.exists(MEASURE_FILE):
        pd.DataFrame(columns=COL_INTERNAL_MEASURES).to_excel(MEASURE_FILE, index=False)

def read_measures():
    ensure_measures_file()
    df = pd.read_excel(MEASURE_FILE)

    # 한글로 저장된 파일이면 영문으로 변환
    if "회원번호" in df.columns:
        df = df_to_eng_measures(df)

    # 누락 컬럼 보정
    for c in COL_INTERNAL_MEASURES:
        if c not in df.columns:
            df[c] = ""

    return df[COL_INTERNAL_MEASURES]

def save_measures(df):
    df_kor = df_to_kor_measures(df)
    df_kor.to_excel(MEASURE_FILE, index=False)


def read_consults():
    df = pd.read_excel(CONSULT_FILE)
    if "상담일" in df.columns:
        df = df_to_eng(df, "consult")

    for c in COL_INTERNAL_CONSULT:
        if c not in df.columns:
            df[c] = ""

    return df[COL_INTERNAL_CONSULT]

def save_consults(df_internal):
    df_kor = df_to_kor(df_internal, "consult")
    df_kor.to_excel(CONSULT_FILE, index=False)

def read_measures():
    # 치수는 한글 컬럼으로 계속 유지 (현장/엑셀 보기 우선)
    df = pd.read_excel(MEASURE_FILE)
    for col in ["회원번호", "측정일"]:
        if col not in df.columns:
            df[col] = ""
    return df

def save_measures(df):
    df.to_excel(MEASURE_FILE, index=False)

# ==========================================================
# 주문/작업지시서 파일 처리
# ==========================================================
ORDER_FILE = os.path.join(DATA_DIR, "orders.xlsx")

def ensure_orders_file():
    if not os.path.exists(ORDER_FILE):
        df = pd.DataFrame(columns=[
            "order_id",        # 주문번호
            "member_id",       # 회원번호
            "template_name",   # 템플릿명
            "order_date",      # 주문일
            "fitting_date",    # 가봉일
            "delivery_date",   # 납품일
            "fabric_code",     # 원단코드
            "status",          # 상태
            "payload",         # 템플릿 입력값(JSON)
            "created_at"       # 등록시각
        ])
        df.to_excel(ORDER_FILE, index=False)

def read_orders():
    ensure_orders_file()
    return pd.read_excel(ORDER_FILE)

def save_orders(df):
    df.to_excel(ORDER_FILE, index=False)


# ==========================================================
# 데이터 로드
# ==========================================================
members = read_members()

# 기존 엑셀 파일이 영문 컬럼이면 → 한글 컬럼으로 1회 강제 저장(마이그레이션)
def migrate_excel_columns_to_korean():
    # 1) members_master.xlsx
    df_m = pd.read_excel(MASTER_FILE)

    # 영문 컬럼이거나(= member_id 등) 한글 컬럼이 없으면 → 내부로 읽어서 한글로 저장
    if ("member_id" in df_m.columns) or ("회원번호" not in df_m.columns):
        _internal = read_members()     # 내부영문 통일
        save_members(_internal)        # 한글로 강제 저장

    # 2) consultations.xlsx
    df_c = pd.read_excel(CONSULT_FILE)
    if ("consult_id" in df_c.columns) or ("상담번호" not in df_c.columns):
        _c_internal = read_consults()
        save_consults(_c_internal)

    # 3) members_measurements.xlsx  (치수는 한글로 유지가 원칙)
    df_me = pd.read_excel(MEASURE_FILE)

    # 예전에 영문 컬럼으로 저장된 적이 있으면 여기서 한글로 강제 변환
    # (영문 치수 파일을 쓰던 버전이 있었다면 아래 매핑을 맞춰주면 됨)
    eng_to_kor_measure = {
        "member_id": "회원번호",
        "measure_date": "측정일",
        "shoulder_in": "어깨_in", "shoulder_cm": "어깨_cm",
        "chest_in": "가슴_in", "chest_cm": "가슴_cm",
        "waist_in": "허리_in", "waist_cm": "허리_cm",
        "hip_in": "엉덩이_in", "hip_cm": "엉덩이_cm",
        "sleeve_in": "소매_in", "sleeve_cm": "소매_cm",
        "length_in": "총장_in", "length_cm": "총장_cm",
        "recommended_jacket": "추천_상의호칭",
        "recommend_jacket_size": "추천_상의호칭",
    }

    changed = False
    for e, k in eng_to_kor_measure.items():
        if e in df_me.columns and k not in df_me.columns:
            df_me.rename(columns={e: k}, inplace=True)
            changed = True

    if changed:
        df_me.to_excel(MEASURE_FILE, index=False)

# 실행
migrate_excel_columns_to_korean()

members = read_members()
measures = read_measures()
consults = read_consults()

# ==========================================================
# session_state 기본값
# ==========================================================
if "selected_member" not in st.session_state:
    st.session_state["selected_member"] = None
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False

# ==========================================================
# 사이드바
# ==========================================================
page = st.sidebar.radio("메뉴 선택", ["HOME - ELBURIM 양복점", "회원 관리", "설정"])

# ==========================================================
# HOME
# ==========================================================
if page == "HOME - ELBURIM 양복점":
    st.title("ELBURIM 양복점 CRM 요약")
    st.metric("총 회원 수", len(members))
    st.metric("치수 등록 건수", len(measures))

# ==========================================================
# 회원 관리
# ==========================================================
elif page == "회원 관리":
    import json
    st.title("회원 관리 시스템")

    # -------------------------
    # 0) 세션 기본값
    # -------------------------
    if "selected_member" not in st.session_state:
        st.session_state["selected_member"] = None
    if "show_register" not in st.session_state:
        st.session_state["show_register"] = False

    # -------------------------
    # 1) 데이터 로드 (내부표준: 영문 컬럼 고정)
    # -------------------------
    members = read_members()      # 내부: member_id, name, birth_date, phone, address, job, first_visit, note, status(있으면)
    consults = read_consults()    # 내부: consult_id, member_id, consult_date ...
    measures = read_measures()    # 내부: member_id, measure_date, shoulder_in, shoulder_cm ... (네 파일 구조에 맞춰)
    orders = read_orders()        # 내부: order_id, member_id, template_name, payload ...

    # members에 status 컬럼 없으면 추가(안전)
    if "status" not in members.columns:
        members["status"] = "정상"

    # -------------------------
    # 2) 회원 검색
    # -------------------------
    st.subheader("회원 검색 및 조회")
    mode = st.radio("검색 방식", ["이름", "회원번호"], horizontal=False)

    selected_member = st.session_state["selected_member"]

    if mode == "이름":
        key = st.text_input("이름 입력")
        if key:
            matched = members[members["name"].astype(str).str.contains(key, na=False)]
            st.dataframe(df_to_kor(matched, "members"), use_container_width=True)

            if not matched.empty:
                options = (matched["member_id"] + " - " + matched["name"]).tolist()
                pick = st.selectbox("회원 선택", ["선택 안 함"] + options)
                if pick != "선택 안 함":
                    selected_member = pick.split(" - ")[0]

    else:
        key = st.text_input("회원번호 입력 (예: M0001)")
        if key:
            result = members[members["member_id"].astype(str).str.contains(key, na=False)]
            st.dataframe(df_to_kor(result, "members"), use_container_width=True)
            if len(result) == 1:
                selected_member = result.iloc[0]["member_id"]

    st.session_state["selected_member"] = selected_member

    # -------------------------
    # 3) 신규 회원 등록
    # -------------------------
    st.markdown("---")
    st.subheader("회원 등록/관리")

    col_btn1, col_btn2 = st.columns([1, 3])
    with col_btn1:
        if st.button("신규 회원 등록"):
            st.session_state["show_register"] = True

    if st.session_state["show_register"]:
        st.markdown("---")
        st.subheader("신규 회원 등록")

        with st.form("register_form"):
            name = st.text_input("이름")
            birth = st.date_input("생년월일")
            phone = st.text_input("전화번호 (010-0000-0000)")
            address = st.text_input("주소")
            job = st.text_input("직업")
            note = st.text_area("메모/특이사항")
            status = st.selectbox("등록상태", ["정상", "등록보류"])
            submit = st.form_submit_button("등록 완료")

        if submit:
            # 새 ID 생성
            if members.empty:
                new_id = "M0001"
            else:
                nums = members["member_id"].astype(str).str.replace("M", "", regex=False)
                nums = pd.to_numeric(nums, errors="coerce")
                new_num = int(nums.max()) + 1 if nums.notna().any() else (len(members) + 1)
                new_id = f"M{new_num:04d}"

            new_row = {
                "member_id": new_id,
                "name": name.strip(),
                "birth_date": birth.strftime("%Y-%m-%d"),
                "phone": clean_phone(phone),
                "address": address.strip(),
                "job": job.strip(),
                "first_visit": datetime.now().strftime("%Y-%m-%d"),
                "note": note.strip(),
                "status": status,
            }

            members = pd.concat([members, pd.DataFrame([new_row])], ignore_index=True)
            save_members(members) 

            st.session_state["selected_member"] = new_id
            st.session_state["show_register"] = False
            st.success(f"신규 회원 등록 완료: {new_id}")
            st.rerun()

    # -------------------------
    # 4) 선택 회원 상세 / 상담 / 치수 / 주문서
    # -------------------------
    selected_member = st.session_state["selected_member"]

    if selected_member:
        st.markdown("---")
        st.subheader("선택 회원 상세")

        info = members[members["member_id"] == selected_member].iloc[0]

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"회원번호: {info['member_id']}")
            st.write(f"이름: {info['name']}")
            st.write(f"생년월일: {info['birth_date']}")
        with c2:
            st.write(f"전화번호: {info['phone']}")
            st.write(f"주소: {info['address']}")
            st.write(f"직업: {info['job']}")
            st.write(f"등록상태: {info.get('status','정상')}")

        # -------------------------
        # 상담 기록
        # -------------------------
        st.markdown("---")
        st.subheader("상담 기록 입력")

        with st.form(f"consult_form_{selected_member}"):
            consult_date = st.date_input("상담일")
            visit_purpose = st.text_input("방문목적")
            referrer = st.text_input("소개인")
            special_notes = st.text_area("고객특이사항")
            consult_note = st.text_area("상담메모")
            save_consult_btn = st.form_submit_button("상담 저장")

        if save_consult_btn:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today_key = datetime.now().strftime("%Y%m%d")
            today_consults = consults[
                consults["consult_id"].astype(str).str.contains(f"C{today_key}-", na=False)
            ]
            seq = 1 if today_consults.empty else (today_consults.shape[0] + 1)
            consult_id = f"C{today_key}-{seq:04d}"

            new_c = {
                "consult_id": consult_id,
                "member_id": selected_member,
                "consult_date": consult_date.strftime("%Y-%m-%d"),
                "visit_purpose": visit_purpose,
                "referrer": referrer,
                "special_notes": special_notes,
                "consult_note": consult_note,
                "created_at": now_str,
            }

            consults = pd.concat([consults, pd.DataFrame([new_c])], ignore_index=True)
            save_consults(consults)
            st.success("상담 저장 완료")
            st.rerun()

        hist_c = consults[consults["member_id"] == selected_member].copy()
        if hist_c.empty:
            st.info("상담 이력이 없습니다.")
        else:
            hist_c["consult_date_dt"] = pd.to_datetime(hist_c["consult_date"], errors="coerce")
            hist_c = hist_c.sort_values("consult_date_dt", ascending=False).drop(columns=["consult_date_dt"])
            st.dataframe(df_to_kor(hist_c, "consult"), use_container_width=True)

        # -------------------------
        # 치수 입력 (inch -> cm)
        # -------------------------
        st.markdown("---")
        st.subheader("치수 입력 (inch 입력 → cm 변환 + 기성 사이즈 추천)")

        with st.form(f"measure_form_{selected_member}"):
            m_date = st.date_input("측정일", value=datetime.now().date())

            c1, c2, c3 = st.columns(3)
            with c1:
                shoulder_in = st.number_input("어깨 (inch)", step=0.1, min_value=0.0)
                chest_in = st.number_input("가슴 (inch)", step=0.1, min_value=0.0)
            with c2:
                waist_in = st.number_input("허리 (inch)", step=0.1, min_value=0.0)
                hip_in = st.number_input("엉덩이 (inch)", step=0.1, min_value=0.0)
            with c3:
                sleeve_in = st.number_input("소매 (inch)", step=0.1, min_value=0.0)
                length_in = st.number_input("총장 (inch)", step=0.1, min_value=0.0)

            save_measure_btn = st.form_submit_button("치수 저장")

        if save_measure_btn:
            chest_cm = inch_to_cm(chest_in)
            size = recommend_jacket_size(chest_cm)

            row = {
                "member_id": selected_member,
                "measure_date": m_date.strftime("%Y-%m-%d"),
                "shoulder_in": shoulder_in, "shoulder_cm": inch_to_cm(shoulder_in),
                "chest_in": chest_in, "chest_cm": chest_cm,
                "waist_in": waist_in, "waist_cm": inch_to_cm(waist_in),
                "hip_in": hip_in, "hip_cm": inch_to_cm(hip_in),
                "sleeve_in": sleeve_in, "sleeve_cm": inch_to_cm(sleeve_in),
                "length_in": length_in, "length_cm": inch_to_cm(length_in),
                "recommend_jacket": size,
            }

            measures = pd.concat([measures, pd.DataFrame([row])], ignore_index=True)
            save_measures(measures) 
            st.success("치수 저장 완료")
            st.rerun()

        st.write("최근 치수 기록")
        history = measures[measures["member_id"] == selected_member].copy()
        if history.empty:
            st.info("치수 이력이 없습니다.")
        else:
            history["measure_date_dt"] = pd.to_datetime(history["measure_date"], errors="coerce")
            history = history.sort_values("measure_date_dt", ascending=False).drop(columns=["measure_date_dt"])
            st.dataframe(df_to_kor_measures(history.head(10)), use_container_width=True)

        # -------------------------
        # 주문서/작업지시서 템플릿(다음 단계 기반)
        # -------------------------
        st.markdown("---")
        st.subheader("작업지시서/주문서 입력 (템플릿 기반)")

        template_name = st.selectbox("양식 선택", list(TEMPLATES.keys()))

        preset = {
            "성명": info["name"],
            "생년월일": info["birth_date"],
            "주소": info["address"],
            "HP": info["phone"],
        }

        with st.form(f"order_template_form_{selected_member}"):
            payload = render_template_form(template_name, preset=preset)
            payload2 = inch_fields_to_cm(payload)
            status = st.selectbox("상태", ["진행중", "가봉완료", "납품완료", "보류", "취소"])
            submit = st.form_submit_button("저장")

        if submit:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            order_id = f"O{datetime.now().strftime('%Y%m%d')}-{(len(orders)+1):04d}"

            row = {
                "order_id": order_id,
                "member_id": selected_member,
                "template_name": template_name,
                "order_date": str(payload.get("주문일", "")),
                "fitting_date": str(payload.get("가봉일", "")),
                "delivery_date": str(payload.get("납품일", "")),
                "fabric_code": payload.get("원단코드", ""),
                "status": status,
                "payload": json.dumps(payload2, ensure_ascii=False),
                "created_at": now_str,
            }

            orders = pd.concat([orders, pd.DataFrame([row])], ignore_index=True)
            save_orders(orders)
            st.success("저장 완료")
            st.rerun()

        st.write("저장된 주문/작업지시서 목록(회원 기준)")
        my_orders = orders[orders["member_id"] == selected_member].copy()
        if my_orders.empty:
            st.info("저장된 주문서가 없습니다.")
        else:
            my_orders = my_orders.sort_values("created_at", ascending=False)
            st.dataframe(df_to_kor_orders(my_orders), use_container_width=True)


# ==========================================================
# 설정
# ==========================================================
elif page == "설정":
    st.title("설정 – 사이즈 규칙 / 매장 약속 용어(추가 예정)")

    ensure_size_rule_file()
    rules = pd.read_excel(SIZE_RULE_FILE)

    st.subheader("상의 사이즈 규칙 (가슴 cm 범위 → 상의호칭)")
    edited = st.data_editor(rules, num_rows="dynamic", use_container_width=True)

    if st.button("저장"):
        edited.to_excel(SIZE_RULE_FILE, index=False)
        st.success("저장 완료")
