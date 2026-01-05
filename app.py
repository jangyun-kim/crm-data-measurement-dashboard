# app.py 
import os
import re
import json
import base64
from datetime import datetime, date
import pandas as pd
import streamlit as st

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader


# ==========================================================
# 0) Streamlit 기본 설정
# ==========================================================
st.set_page_config(page_title="엘부림 양복점 CRM", layout="wide")


# ==========================================================
# 1) 경로 / 파일 정의
# ==========================================================
DATA_DIR = "data_members"
SETTINGS_DIR = "settings"

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)

MASTER_FILE = os.path.join(DATA_DIR, "members_master.xlsx")
MEASURE_FILE = os.path.join(DATA_DIR, "members_measurements.xlsx")
CONSULT_FILE = os.path.join(DATA_DIR, "consultations.xlsx")

ORDER_FILE = os.path.join(DATA_DIR, "orders.xlsx")
SIZE_RULE_FILE = os.path.join(SETTINGS_DIR, "size_rules.xlsx")

FORM_XY_FILE = os.path.join(SETTINGS_DIR, "form_xy_customer_service.xlsx")

MEASURE_IMG_DIR = os.path.join(DATA_DIR, "measure_images")
FILLED_DIR = os.path.join(DATA_DIR, "filled_forms")
os.makedirs(MEASURE_IMG_DIR, exist_ok=True)
os.makedirs(FILLED_DIR, exist_ok=True)

# 요청한 파일명 그대로 사용
TEMPLATE_CUSTOMER_SERVICE = os.path.join(MEASURE_IMG_DIR, "elburim_customer_service.png")


# ==========================================================
# 2) 공통 유틸
# ==========================================================
def clean_phone(value: str) -> str:
    if value is None:
        return ""
    digits = re.sub(r"[^0-9]", "", str(value))
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return ""


def normalize_date_str(val) -> str:
    """date/datetime/문자열/NaN -> YYYY-MM-DD 문자열로 정규화"""
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d")
    try:
        return pd.to_datetime(val).strftime("%Y-%m-%d")
    except:
        return str(val)


def inch_to_cm(val):
    try:
        return round(float(val) * 2.54, 1)
    except:
        return None


def safe_json_dumps(obj) -> str:
    """date가 들어가도 JSON 저장되게 default=str"""
    return json.dumps(obj, ensure_ascii=False, default=str)


# ==========================================================
# 3) 컬럼 표준(내부는 영문, 엑셀 저장은 한글)
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
    "created_at": "등록시각"
}
COL_ENG_MAP_CONSULT = {v: k for k, v in COL_KOR_MAP_CONSULT.items()}


def df_to_kor(df: pd.DataFrame, kind: str):
    if df is None or df.empty:
        return df
    if kind == "members":
        return df.rename(columns=COL_KOR_MAP_MEMBERS)
    if kind == "consult":
        return df.rename(columns=COL_KOR_MAP_CONSULT)
    return df


def df_to_eng(df: pd.DataFrame, kind: str):
    if df is None or df.empty:
        return df
    if kind == "members":
        return df.rename(columns=COL_ENG_MAP_MEMBERS)
    if kind == "consult":
        return df.rename(columns=COL_ENG_MAP_CONSULT)
    return df


# ==========================================================
# 4) 파일 생성 보장
# ==========================================================
def ensure_files():
    if not os.path.exists(MASTER_FILE):
        pd.DataFrame(columns=COL_INTERNAL_MEMBERS).to_excel(MASTER_FILE, index=False)

    if not os.path.exists(MEASURE_FILE):
        # 측정값은 현장 입력: inch 저장 + cm 자동 계산 저장
        pd.DataFrame(columns=[
            "member_id", "measure_date",
            "shoulder_in", "shoulder_cm",
            "chest_in", "chest_cm",
            "waist_in", "waist_cm",
            "hip_in", "hip_cm",
            "sleeve_in", "sleeve_cm",
            "length_in", "length_cm",
            "recommend_top_size"
        ]).to_excel(MEASURE_FILE, index=False)

    if not os.path.exists(CONSULT_FILE):
        pd.DataFrame(columns=COL_INTERNAL_CONSULT).to_excel(CONSULT_FILE, index=False)

    if not os.path.exists(ORDER_FILE):
        pd.DataFrame(columns=[
            "order_id", "member_id", "template_name",
            "order_date", "fitting_date", "delivery_date",
            "fabric_code", "status",
            "payload_json", "created_at",
            "filled_pdf_path"
        ]).to_excel(ORDER_FILE, index=False)

    if not os.path.exists(SIZE_RULE_FILE):
        pd.DataFrame({
            "가슴_cm_하한": [92, 96, 100, 104],
            "가슴_cm_상한": [95, 99, 103, 107],
            "상의호칭": ["K48", "K50", "K52", "K54"],
        }).to_excel(SIZE_RULE_FILE, index=False)

    # 양식 좌표(설정에서 수정 가능)
    if not os.path.exists(FORM_XY_FILE):
        pd.DataFrame([
            # ※ 좌표는 A4(포인트) 기준 (x, y).  처음엔 대충 넣고 설정에서 조정하면 됨.
            {"필드키": "성명", "x": 90, "y": 770},
            {"필드키": "생년월일", "x": 260, "y": 770},
            {"필드키": "주소", "x": 90, "y": 735},
            {"필드키": "HP", "x": 90, "y": 700},

            {"필드키": "주문일", "x": 120, "y": 660},
            {"필드키": "가봉일", "x": 260, "y": 660},
            {"필드키": "납품일", "x": 400, "y": 660},

            {"필드키": "주문금액", "x": 470, "y": 770},
            {"필드키": "선금", "x": 470, "y": 740},
            {"필드키": "잔금", "x": 470, "y": 710},

            {"필드키": "원단코드", "x": 480, "y": 610},
            {"필드키": "원단설명", "x": 90, "y": 610},
            {"필드키": "주문내역", "x": 90, "y": 560},
        ]).to_excel(FORM_XY_FILE, index=False)


ensure_files()


# ==========================================================
# 5) 데이터 로드/세이브
# ==========================================================
def read_members() -> pd.DataFrame:
    df = pd.read_excel(MASTER_FILE)
    # 한글 컬럼으로 저장되어 있다면 -> 영문 내부로 변환
    if "이름" in df.columns:
        df = df_to_eng(df, "members")
    for c in COL_INTERNAL_MEMBERS:
        if c not in df.columns:
            df[c] = ""
    return df[COL_INTERNAL_MEMBERS]


def save_members(df: pd.DataFrame):
    df_kor = df_to_kor(df, "members")
    df_kor.to_excel(MASTER_FILE, index=False)


def read_measures() -> pd.DataFrame:
    df = pd.read_excel(MEASURE_FILE)
    # 혹시 예전 한글 컬럼으로 저장된 경우 대응
    # (member_id가 없고 "회원번호"가 있으면 변환)
    if "회원번호" in df.columns and "member_id" not in df.columns:
        df = df.rename(columns={"회원번호": "member_id"})
    if "측정일" in df.columns and "measure_date" not in df.columns:
        df = df.rename(columns={"측정일": "measure_date"})
    return df


def save_measures(df: pd.DataFrame):
    df.to_excel(MEASURE_FILE, index=False)


def read_consults() -> pd.DataFrame:
    df = pd.read_excel(CONSULT_FILE)
    if "상담일" in df.columns:
        df = df_to_eng(df, "consult")
    for c in COL_INTERNAL_CONSULT:
        if c not in df.columns:
            df[c] = ""
    return df[COL_INTERNAL_CONSULT]


def save_consults(df: pd.DataFrame):
    df_kor = df_to_kor(df, "consult")
    df_kor.to_excel(CONSULT_FILE, index=False)


def read_orders() -> pd.DataFrame:
    df = pd.read_excel(ORDER_FILE)
    return df


def save_orders(df: pd.DataFrame):
    df.to_excel(ORDER_FILE, index=False)


# ==========================================================
# 6) 사이즈 추천(설정 기반)
# ==========================================================
def recommend_top_size(chest_cm):
    if chest_cm is None or pd.isna(chest_cm):
        return "추천 불가"
    rules = pd.read_excel(SIZE_RULE_FILE)
    for _, r in rules.iterrows():
        if float(r["가슴_cm_하한"]) <= float(chest_cm) <= float(r["가슴_cm_상한"]):
            return str(r["상의호칭"])
    return "규칙 없음"


# ==========================================================
# 7) PDF 생성(양식 위에 값 찍기)
# ==========================================================
def load_xy_map_customer_service() -> dict:
    df = pd.read_excel(FORM_XY_FILE)
    xy = {}
    for _, r in df.iterrows():
        k = str(r["필드키"]).strip()
        try:
            x = float(r["x"])
            y = float(r["y"])
            xy[k] = (x, y)
        except:
            continue
    return xy


def generate_filled_pdf(template_png_path: str, out_pdf_path: str, field_values: dict, field_xy: dict):
    """A4 배경 이미지 위에 텍스트를 좌표로 찍어 PDF 생성"""
    c = canvas.Canvas(out_pdf_path, pagesize=A4)
    w, h = A4

    bg = ImageReader(template_png_path)
    c.drawImage(bg, 0, 0, width=w, height=h)

    c.setFont("Helvetica", 11)

    for k, (x, y) in field_xy.items():
        v = field_values.get(k, "")
        if v is None:
            v = ""
        if isinstance(v, (date, datetime)):
            v = v.strftime("%Y-%m-%d")
        c.drawString(x, y, str(v))

    c.showPage()
    c.save()


# ==========================================================
# 8) 세션 상태
# ==========================================================
if "selected_member" not in st.session_state:
    st.session_state["selected_member"] = None
if "show_register" not in st.session_state:
    st.session_state["show_register"] = False


# ==========================================================
# 9) 데이터 로드(전역)
# ==========================================================
members = read_members()
measures = read_measures()
consults = read_consults()
orders = read_orders()


# ==========================================================
# 10) 사이드바 메뉴
# ==========================================================
page = st.sidebar.radio("메뉴", ["HOME", "회원 관리", "설정"])


# ==========================================================
# HOME
# ==========================================================
if page == "HOME":
    st.title("엘부림 양복점 CRM 요약")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("총 회원 수", int(len(members)))
    with col2:
        st.metric("치수 등록 건수", int(len(measures)))
    with col3:
        st.metric("주문/작업지시서 건수", int(len(orders)))

    st.markdown("---")
    st.subheader("최근 등록 회원(상위 10)")
    view = df_to_kor(members.sort_values("first_visit", ascending=False).head(10), "members")
    st.dataframe(view, use_container_width=True)


# ==========================================================
# 회원 관리
# ==========================================================
elif page == "회원 관리":
    st.title("회원 관리")

    # -------------------------
    # 1) 회원 검색
    # -------------------------
    st.subheader("1) 회원 검색 및 조회")

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
    # 2) 신규 회원 등록
    # -------------------------
    st.markdown("---")
    st.subheader("2) 회원 등록/관리")

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
            if members.empty:
                new_id = "M0001"
            else:
                nums = members["member_id"].astype(str).str.replace("M", "", regex=False)
                nums = pd.to_numeric(nums, errors="coerce")
                new_num = int(nums.max()) + 1 if nums.notna().any() else (len(members) + 1)
                new_id = f"M{new_num:04d}"

            new_row = {
                "member_id": new_id,
                "name": str(name).strip(),
                "birth_date": normalize_date_str(birth),
                "phone": clean_phone(phone),
                "address": str(address).strip(),
                "job": str(job).strip(),
                "first_visit": datetime.now().strftime("%Y-%m-%d"),
                "note": str(note).strip(),
                "status": status,
            }

            members = pd.concat([members, pd.DataFrame([new_row])], ignore_index=True)
            save_members(members)

            st.session_state["selected_member"] = new_id
            st.session_state["show_register"] = False
            st.success(f"신규 회원 등록 완료: {new_id}")
            st.rerun()

    # -------------------------
    # 3) 선택 회원 상세 + 상담 + 치수 + 주문서
    # -------------------------
    selected_member = st.session_state["selected_member"]
    if selected_member:
        st.markdown("---")
        st.subheader("3) 선택 회원 상세")

        info = members[members["member_id"] == selected_member].iloc[0]

        # 상단 요약 카드
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("회원번호", info["member_id"])
        c2.metric("이름", info["name"])
        c3.metric("전화번호", info["phone"])
        c4.metric("등록상태", info["status"])

        st.write(f"생년월일: {info['birth_date']}")
        st.write(f"주소: {info['address']}")
        st.write(f"직업: {info['job']}")
        st.write(f"첫방문일: {info['first_visit']}")
        st.write(f"메모: {info['note']}")

        tab1, tab2, tab3, tab4 = st.tabs(["상담 기록", "치수 입력", "주문서(저장→양식 PDF)", "주문/작업 목록"])

        # -------------------------
        # TAB1) 상담 기록
        # -------------------------
        with tab1:
            st.subheader("상담 기록 입력")

            with st.form(f"consult_form_{selected_member}"):
                consult_date = st.date_input("상담일", value=datetime.now().date())
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
                    "consult_date": normalize_date_str(consult_date),
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

            st.markdown("### 상담 이력")
            hist_c = consults[consults["member_id"] == selected_member].copy()
            if hist_c.empty:
                st.info("상담 이력이 없습니다.")
            else:
                hist_c["상담일_dt"] = pd.to_datetime(hist_c["consult_date"], errors="coerce")
                hist_c = hist_c.sort_values("상담일_dt", ascending=False).drop(columns=["상담일_dt"])
                st.dataframe(df_to_kor(hist_c, "consult"), use_container_width=True)

        # -------------------------
        # TAB2) 치수 입력
        # -------------------------
        with tab2:
            st.subheader("치수 입력 (inch → cm 자동변환 + 상의호칭 추천)")

            with st.form(f"measure_form_{selected_member}"):
                m_date = st.date_input("측정일", value=datetime.now().date())

                a, b, c = st.columns(3)
                with a:
                    shoulder_in = st.number_input("어깨(inch)", step=0.1, min_value=0.0)
                    chest_in = st.number_input("가슴(inch)", step=0.1, min_value=0.0)
                with b:
                    waist_in = st.number_input("허리(inch)", step=0.1, min_value=0.0)
                    hip_in = st.number_input("엉덩이(inch)", step=0.1, min_value=0.0)
                with c:
                    sleeve_in = st.number_input("소매(inch)", step=0.1, min_value=0.0)
                    length_in = st.number_input("총장(inch)", step=0.1, min_value=0.0)

                save_measure_btn = st.form_submit_button("치수 저장")

            if save_measure_btn:
                chest_cm = inch_to_cm(chest_in)
                top_size = recommend_top_size(chest_cm)

                row = {
                    "member_id": selected_member,
                    "measure_date": normalize_date_str(m_date),

                    "shoulder_in": shoulder_in,
                    "shoulder_cm": inch_to_cm(shoulder_in),

                    "chest_in": chest_in,
                    "chest_cm": chest_cm,

                    "waist_in": waist_in,
                    "waist_cm": inch_to_cm(waist_in),

                    "hip_in": hip_in,
                    "hip_cm": inch_to_cm(hip_in),

                    "sleeve_in": sleeve_in,
                    "sleeve_cm": inch_to_cm(sleeve_in),

                    "length_in": length_in,
                    "length_cm": inch_to_cm(length_in),

                    "recommend_top_size": top_size,
                }

                measures2 = pd.concat([measures, pd.DataFrame([row])], ignore_index=True)
                save_measures(measures2)
                st.success(f"치수 저장 완료 / 추천 상의호칭: {top_size}")
                st.rerun()

            st.markdown("### 최근 치수 기록")
            history = measures[measures["member_id"] == selected_member].copy()
            if history.empty:
                st.info("치수 이력이 없습니다.")
            else:
                history["측정일_dt"] = pd.to_datetime(history["measure_date"], errors="coerce")
                history = history.sort_values("측정일_dt", ascending=False).drop(columns=["측정일_dt"])
                st.dataframe(history.head(10), use_container_width=True)

        # -------------------------
        # TAB3) 주문서 입력 + 저장하면 양식 PDF 생성
        # -------------------------
        with tab3:
            st.subheader("주문서 입력 (저장 시 양식 PDF 자동 생성)")

            # 양식 이미지 존재 확인
            if not os.path.exists(TEMPLATE_CUSTOMER_SERVICE):
                st.error(
                    "양식 이미지가 없습니다.\n\n"
                    f"- 필요 경로: {TEMPLATE_CUSTOMER_SERVICE}\n"
                    "- 파일명을 정확히 확인하세요(요청한 그대로: elburim_customer_service.png)"
                )
                st.stop()

            st.image(TEMPLATE_CUSTOMER_SERVICE, caption="고객 상담/주문 양식(저장 시 PDF 생성)", use_container_width=True)

            # 프리셋(회원정보 자동 채움)
            preset = {
                "성명": info["name"],
                "생년월일": info["birth_date"],
                "주소": info["address"],
                "HP": info["phone"],
            }

            # 최근 치수에서 참고할 값이 있으면 추가(원하면 확장)
            recent_m = measures[measures["member_id"] == selected_member].copy()
            if not recent_m.empty:
                recent_m["d"] = pd.to_datetime(recent_m["measure_date"], errors="coerce")
                recent_m = recent_m.sort_values("d", ascending=False).drop(columns=["d"])
                preset["추천_상의호칭"] = str(recent_m.iloc[0].get("recommend_top_size", ""))

            with st.form(f"order_form_{selected_member}"):
                st.markdown("#### 기본 정보")
                성명 = st.text_input("성명", value=str(preset.get("성명", "")))
                생년월일 = st.text_input("생년월일", value=str(preset.get("생년월일", "")))
                주소 = st.text_input("주소", value=str(preset.get("주소", "")))
                HP = st.text_input("HP", value=str(preset.get("HP", "")))

                st.markdown("#### 일정")
                주문일 = st.date_input("주문일", value=datetime.now().date())
                가봉일 = st.date_input("가봉일", value=datetime.now().date())
                납품일 = st.date_input("납품일", value=datetime.now().date())

                st.markdown("#### 금액")
                주문금액 = st.number_input("주문금액", step=10000, value=0)
                선금 = st.number_input("선금", step=10000, value=0)
                잔금 = st.number_input("잔금", step=10000, value=0)

                st.markdown("#### 원단 / 주문내역")
                원단코드 = st.text_input("원단코드(A0-001 등)", value="")
                원단설명 = st.text_area("원단/색상/메모", value="")
                주문내역 = st.text_area("주문내역(작업 지시 내용)", value="")

                상태 = st.selectbox("상태", ["진행중", "가봉완료", "납품완료", "보류", "취소"])

                save_order_btn = st.form_submit_button("저장(양식 PDF 생성)")

            if save_order_btn:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                order_id = f"O{datetime.now().strftime('%Y%m%d')}-{len(orders) + 1:04d}"

                payload = {
                    "성명": 성명,
                    "생년월일": 생년월일,
                    "주소": 주소,
                    "HP": HP,

                    "주문일": 주문일,
                    "가봉일": 가봉일,
                    "납품일": 납품일,

                    "주문금액": 주문금액,
                    "선금": 선금,
                    "잔금": 잔금,

                    "원단코드": 원단코드,
                    "원단설명": 원단설명,
                    "주문내역": 주문내역,

                    "상태": 상태,
                }

                # PDF 생성
                xy = load_xy_map_customer_service()
                out_pdf = os.path.join(FILLED_DIR, f"{order_id}_고객상담양식.pdf")

                # PDF에는 날짜를 문자열로 찍히게 normalize
                field_values = payload.copy()
                field_values["주문일"] = normalize_date_str(주문일)
                field_values["가봉일"] = normalize_date_str(가봉일)
                field_values["납품일"] = normalize_date_str(납품일)

                generate_filled_pdf(
                    template_png_path=TEMPLATE_CUSTOMER_SERVICE,
                    out_pdf_path=out_pdf,
                    field_values=field_values,
                    field_xy=xy
                )

                # orders.xlsx 저장
                new_o = {
                    "order_id": order_id,
                    "member_id": selected_member,
                    "template_name": "고객상담양식(elburim_customer_service)",
                    "order_date": normalize_date_str(주문일),
                    "fitting_date": normalize_date_str(가봉일),
                    "delivery_date": normalize_date_str(납품일),
                    "fabric_code": 원단코드,
                    "status": 상태,
                    "payload_json": safe_json_dumps(payload),  # date 직렬화 문제 해결
                    "created_at": now_str,
                    "filled_pdf_path": out_pdf,
                }

                orders2 = pd.concat([orders, pd.DataFrame([new_o])], ignore_index=True)
                save_orders(orders2)

                st.success("저장 완료 + 양식 PDF 생성 완료")
                with open(out_pdf, "rb") as f:
                    st.download_button(
                        "📄 생성된 양식(PDF) 다운로드",
                        data=f,
                        file_name=os.path.basename(out_pdf),
                        mime="application/pdf"
                    )
                st.info(f"저장 위치: {out_pdf}")

                st.rerun()

        # -------------------------
        # TAB4) 회원별 주문/작업 목록
        # -------------------------
        with tab4:
            st.subheader("회원별 주문/작업 목록")

            my_orders = orders[orders["member_id"] == selected_member].copy()
            if my_orders.empty:
                st.info("주문/작업 이력이 없습니다.")
            else:
                my_orders["등록시각_dt"] = pd.to_datetime(my_orders["created_at"], errors="coerce")
                my_orders = my_orders.sort_values("등록시각_dt", ascending=False).drop(columns=["등록시각_dt"])

                # 보기용 컬럼 한국어
                view = my_orders.rename(columns={
                    "order_id": "주문번호",
                    "template_name": "양식명",
                    "order_date": "주문일",
                    "fitting_date": "가봉일",
                    "delivery_date": "납품일",
                    "fabric_code": "원단코드",
                    "status": "상태",
                    "created_at": "등록시각",
                    "filled_pdf_path": "PDF경로",
                })
                st.dataframe(view, use_container_width=True)

                st.markdown("#### PDF 다운로드")
                for _, r in my_orders.head(10).iterrows():
                    p = str(r.get("filled_pdf_path", "")).strip()
                    if p and os.path.exists(p):
                        with open(p, "rb") as f:
                            st.download_button(
                                f"📄 {r['order_id']} PDF 다운로드",
                                data=f,
                                file_name=os.path.basename(p),
                                mime="application/pdf",
                                key=f"dl_{r['order_id']}"
                            )


# ==========================================================
# 설정
# ==========================================================
elif page == "설정":
    st.title("설정")

    st.markdown("### 1) 상의호칭 추천 규칙(가슴 cm 기준)")
    rules = pd.read_excel(SIZE_RULE_FILE)
    edited_rules = st.data_editor(rules, num_rows="dynamic", use_container_width=True)

    if st.button("상의호칭 규칙 저장"):
        edited_rules.to_excel(SIZE_RULE_FILE, index=False)
        st.success("저장 완료")

    st.markdown("---")
    st.markdown("### 2) 고객상담 양식 좌표 설정(양식 PDF에 값 찍는 위치)")
    st.caption("※ x, y 값은 A4 기준 좌표(포인트). 숫자만 바꾸면 코드 수정 없이 출력 위치 조정 가능")

    xy_df = pd.read_excel(FORM_XY_FILE)
    edited_xy = st.data_editor(xy_df, num_rows="dynamic", use_container_width=True)

    if st.button("양식 좌표 저장"):
        edited_xy.to_excel(FORM_XY_FILE, index=False)
        st.success("저장 완료(다음 저장부터 반영됨)")

    st.markdown("---")
    st.markdown("### 3) 양식 이미지 파일 확인")
    st.write("현재 경로:", TEMPLATE_CUSTOMER_SERVICE)
    st.write("파일 존재 여부:", "✅ 있음" if os.path.exists(TEMPLATE_CUSTOMER_SERVICE) else "❌ 없음")
    if os.path.exists(TEMPLATE_CUSTOMER_SERVICE):
        st.image(TEMPLATE_CUSTOMER_SERVICE, caption="현재 사용 중인 양식 이미지", use_container_width=True)
