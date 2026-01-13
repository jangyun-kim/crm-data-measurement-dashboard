import streamlit as st
import pandas as pd
import json
import os
import base64
import re
from datetime import datetime, date

# =====================================
# 기본 설정
# =====================================
st.set_page_config(page_title="ELBURIM CRM", layout="wide")

DATA_DIR = "data_members"
os.makedirs(DATA_DIR, exist_ok=True)

MEMBER_FILE = os.path.join(DATA_DIR, "members_master.csv")
RECORD_FILE = os.path.join(DATA_DIR, "measure_records.csv")

# =====================================
# (추가) 기존 엑셀 회원데이터 → CSV 마이그레이션(1회)
# =====================================
LEGACY_XLSX = os.path.join(DATA_DIR, "members_master.xlsx")  # 예전 파일명
LEGACY_XLSX_ALT = os.path.join(DATA_DIR, "members_master.xlsx")  # 혹시 경로/이름 다르면 여기에 추가

def migrate_legacy_members_if_needed():
    """
    - members.csv가 비어있거나 없고
    - legacy 엑셀 파일이 존재하면
    → 엑셀 데이터를 members.csv로 옮김(1회)
    """
    # 이미 CSV가 있고 데이터가 있으면 아무것도 안 함
    if os.path.exists(MEMBER_FILE):
        try:
            cur = pd.read_csv(MEMBER_FILE, encoding="utf-8-sig")
            if not cur.empty:
                return
        except:
            pass

    legacy_path = None
    if os.path.exists(LEGACY_XLSX):
        legacy_path = LEGACY_XLSX
    elif os.path.exists(LEGACY_XLSX_ALT):
        legacy_path = LEGACY_XLSX_ALT

    if legacy_path is None:
        return

    df = pd.read_excel(legacy_path)

    # ✅ 한글/영문 컬럼 대응 (너가 예전에 쓰던 파일에 맞춰 최대한 안전하게)
    # 가능한 케이스:
    # - "member_id" / "name" / "phone"
    # - "회원번호" / "이름" / "전화번호"
    col_map = {}
    if "member_id" not in df.columns and "회원번호" in df.columns:
        col_map["회원번호"] = "member_id"
    if "name" not in df.columns and "이름" in df.columns:
        col_map["이름"] = "name"
    if "phone" not in df.columns and "전화번호" in df.columns:
        col_map["전화번호"] = "phone"

    if col_map:
        df = df.rename(columns=col_map)

    # 최소 컬럼만 추림
    for c in ["member_id", "name", "phone"]:
        if c not in df.columns:
            df[c] = ""

    df = df[["member_id", "name", "phone"]].copy()

    # member_id 없으면 자동 생성
    if df["member_id"].astype(str).str.strip().eq("").all():
        df["member_id"] = [f"M{i+1:04d}" for i in range(len(df))]

    # 중복 제거
    df["member_id"] = df["member_id"].astype(str)
    df = df.drop_duplicates(subset=["member_id"]).reset_index(drop=True)

    df.to_csv(MEMBER_FILE, index=False, encoding="utf-8-sig")


# 앱 시작 시 마이그레이션 실행
migrate_legacy_members_if_needed()


# 1) 프로젝트 내부 상대경로(배포/다른PC 대비) - 우선
TEMPLATE_REL = os.path.join(DATA_DIR, "measure_images", "elburim_customer_service.png")
# 2) 로컬 PC 절대경로(네가 준 경로) - fallback
TEMPLATE_ABS = r"G:\My Drive\MyPortfolio\No2_data_automation\data_members\measure_images\elburim_customer_service.png"


# =====================================
# 유틸
# =====================================
def image_to_data_url(path: str) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f"data:image/png;base64,{b64}"

def get_template_path():
    # 상대경로 우선
    if os.path.exists(TEMPLATE_REL):
        return TEMPLATE_REL
    # 절대경로 fallback
    if os.path.exists(TEMPLATE_ABS):
        return TEMPLATE_ABS
    return None

def _read_csv_safe(path: str):
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except:
        # 혹시 인코딩 꼬이면 기본 utf-8 시도
        return pd.read_csv(path, encoding="utf-8")

def _write_csv_safe(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False, encoding="utf-8-sig")

def normalize_phone(s: str) -> str:
    if s is None:
        return ""
    raw = str(s).strip()
    if raw == "":
        return ""
    digits = re.sub(r"[^0-9]", "", raw)
    # 010XXXXXXXX 형태만 정규화
    if len(digits) == 11 and digits.startswith("010"):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return raw  # 입력 그대로 두되, 검색 가능하도록 문자열 유지

def load_members():
    df = _read_csv_safe(MEMBER_FILE)
    if df.empty:
        return pd.DataFrame(columns=["member_id", "name", "phone"])
    # 컬럼 누락 방어
    for c in ["member_id", "name", "phone"]:
        if c not in df.columns:
            df[c] = ""
    return df[["member_id", "name", "phone"]].copy()

def save_members(df):
    # 표준 컬럼만 저장
    for c in ["member_id", "name", "phone"]:
        if c not in df.columns:
            df[c] = ""
    _write_csv_safe(df[["member_id", "name", "phone"]], MEMBER_FILE)

def ensure_record_file():
    if not os.path.exists(RECORD_FILE):
        _write_csv_safe(pd.DataFrame(columns=["created_at", "member_id", "payload_json"]), RECORD_FILE)

def load_records(member_id: str):
    ensure_record_file()
    df = _read_csv_safe(RECORD_FILE)
    if df.empty:
        return df
    for c in ["created_at", "member_id", "payload_json"]:
        if c not in df.columns:
            df[c] = ""
    return df[df["member_id"].astype(str) == str(member_id)].copy()

def append_record(member_id: str, values: dict):
    ensure_record_file()
    row = {
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "member_id": str(member_id),
        "payload_json": json.dumps(values, ensure_ascii=False),
    }
    # append
    pd.DataFrame([row]).to_csv(
        RECORD_FILE, mode="a", header=False, index=False, encoding="utf-8-sig"
    )

def safe_json_load(s):
    try:
        return json.loads(s) if isinstance(s, str) and s.strip() else {}
    except:
        return {}

def next_member_id(members_df: pd.DataFrame) -> str:
    """
    M0001 ~ 형태에서 max+1로 생성 (중복 방지)
    """
    if members_df is None or members_df.empty:
        return "M0001"
    series = members_df["member_id"].astype(str).str.replace("M", "", regex=False)
    nums = pd.to_numeric(series, errors="coerce")
    if nums.notna().any():
        return f"M{int(nums.max()) + 1:04d}"
    return f"M{len(members_df) + 1:04d}"


# =====================================
# 종이양식 필드 좌표(비율 기반)
# - 좌표만 조정하면 UI가 “종이와 동일하게” 따라감
# =====================================
FIELDS = [
    {"id": "name",         "label": "성명",     "type": "text",     "x": 0.06, "y": 0.11,  "w": 0.28, "h": 0.035},
    {"id": "birth",        "label": "생년월일", "type": "text",     "x": 0.38, "y": 0.11,  "w": 0.25, "h": 0.035},
    {"id": "address",      "label": "주소",     "type": "text",     "x": 0.06, "y": 0.155, "w": 0.57, "h": 0.035},
    {"id": "phone",        "label": "H.P",      "type": "text",     "x": 0.06, "y": 0.20,  "w": 0.28, "h": 0.035},

    {"id": "order_date",   "label": "주문일",   "type": "date",     "x": 0.06, "y": 0.245, "w": 0.22, "h": 0.035},
    {"id": "fitting_date", "label": "가봉일",   "type": "date",     "x": 0.34, "y": 0.20,  "w": 0.18, "h": 0.035},
    {"id": "delivery_date","label": "납품일",   "type": "date",     "x": 0.34, "y": 0.245, "w": 0.18, "h": 0.035},

    {"id": "total_price",  "label": "주문금액", "type": "number",   "x": 0.70, "y": 0.11,  "w": 0.23, "h": 0.035},
    {"id": "deposit",      "label": "선금",     "type": "number",   "x": 0.70, "y": 0.20,  "w": 0.23, "h": 0.035},
    {"id": "balance",      "label": "잔금",     "type": "number",   "x": 0.70, "y": 0.245, "w": 0.23, "h": 0.035},

    {"id": "order_detail", "label": "주문내역", "type": "textarea", "x": 0.28, "y": 0.33,  "w": 0.63, "h": 0.20},

    {"id": "height",       "label": "신장",     "type": "text",     "x": 0.06, "y": 0.33,  "w": 0.18, "h": 0.03},
    {"id": "neck",         "label": "목",       "type": "text",     "x": 0.06, "y": 0.37,  "w": 0.18, "h": 0.03},
    {"id": "armhole",      "label": "진동",     "type": "text",     "x": 0.06, "y": 0.41,  "w": 0.18, "h": 0.03},
    {"id": "shoulder",     "label": "어깨",     "type": "text",     "x": 0.06, "y": 0.49,  "w": 0.18, "h": 0.03},
    {"id": "sleeve",       "label": "소매",     "type": "text",     "x": 0.06, "y": 0.53,  "w": 0.18, "h": 0.03},
]
FIELD_IDS = [f["id"] for f in FIELDS]


# =====================================
# 태블릿 모드 CSS
# =====================================
def inject_css(tablet_mode: bool):
    base = """
    <style>
    .sheet {
        position: relative;
        background-size: contain;
        background-repeat: no-repeat;
        width: 100%;
        padding-top: 140%;
        border-radius: 8px;
    }
    .field { position: absolute; }
    div[data-baseweb="input"] input {
        background: rgba(255,255,255,0.55) !important;
        border: 1px solid rgba(0,0,0,0.25) !important;
    }
    textarea {
        background: rgba(255,255,255,0.55) !important;
        border: 1px solid rgba(0,0,0,0.25) !important;
    }
    </style>
    """
    st.markdown(base, unsafe_allow_html=True)

    if tablet_mode:
        tablet = """
        <style>
        html, body, [class*="css"]  { font-size: 18px !important; }
        div[data-baseweb="input"] input { font-size: 20px !important; height: 44px !important; }
        textarea { font-size: 20px !important; min-height: 120px !important; }
        section[data-testid="stSidebar"] { width: 280px !important; }
        </style>
        """
        st.markdown(tablet, unsafe_allow_html=True)


# =====================================
# 사이드바: 회원 선택 / 검색 / 태블릿 모드 / 기록 불러오기
# =====================================
members = load_members()

st.sidebar.title("회원 관리")
tablet_mode = st.sidebar.toggle("태블릿 모드", value=True)

# (A) 검색: 이름 / 전화번호
st.sidebar.subheader("회원 검색")
q_name = st.sidebar.text_input("이름 검색", value="")
q_phone = st.sidebar.text_input("전화번호 검색", value="")

filtered = members.copy()

if q_name.strip() or q_phone.strip():
    mask = False

    if q_name.strip():
        mask = members["name"].astype(str).str.contains(q_name.strip(), na=False)

    if q_phone.strip():
        phone_mask = members["phone"].astype(str).str.contains(q_phone.strip(), na=False)
        mask = mask | phone_mask if isinstance(mask, pd.Series) else phone_mask

    filtered = members[mask]

# (B) 신규 회원
with st.sidebar.expander("➕ 신규 회원 등록", expanded=False):
    new_name = st.text_input("이름", key="new_name")
    new_phone = st.text_input("전화번호", key="new_phone")
    if st.button("등록", key="btn_register"):
        new_id = next_member_id(members)
        row = {
            "member_id": new_id,
            "name": str(new_name).strip(),
            "phone": normalize_phone(new_phone),
        }
        members = pd.concat([members, pd.DataFrame([row])], ignore_index=True)
        save_members(members)
        st.session_state["selected_member"] = new_id
        st.success(f"등록 완료: {new_id}")
        st.rerun()

# =========================
# 회원 검색 (이름 OR 전화번호)
# =========================

filtered = members.copy()
if q_name.strip() or q_phone.strip():
    mask = pd.Series([False] * len(members))

    if q_name.strip():
        mask = mask | members["name"].astype(str).str.contains(q_name.strip(), na=False)

    if q_phone.strip():
        mask = mask | members["phone"].astype(str).str.contains(q_phone.strip(), na=False)

    filtered = members[mask].copy()

# =========================
# 회원 선택 (검색 결과 기반)
# =========================
if filtered.empty:
    st.sidebar.warning("검색 결과가 없습니다.")
    selected_member = None
else:
    options = (filtered["member_id"].astype(str) + " - " + filtered["name"].astype(str) + " (" + filtered["phone"].astype(str) + ")").tolist()
    option = st.sidebar.selectbox("회원 선택", options, key="member_select")
    selected_member = option.split(" - ")[0]


# (D) 기록 불러오기
loaded_payload = None
if selected_member:
    rec_df = load_records(selected_member).sort_values("created_at", ascending=False)

    with st.sidebar.expander("📌 저장 기록 불러오기", expanded=True):
        if rec_df.empty:
            st.info("저장된 기록이 없습니다.")
        else:
            choices = rec_df["created_at"].tolist()
            pick = st.selectbox("불러올 기록(저장시각)", choices, key="record_pick")

            if st.button("이 기록 불러오기", key="btn_load_record"):
                row = rec_df[rec_df["created_at"] == pick].iloc[0]
                loaded_payload = safe_json_load(row["payload_json"])

                # session_state 주입
                for fid in FIELD_IDS:
                    if fid in loaded_payload:
                        st.session_state[fid] = loaded_payload[fid]

                st.session_state["loaded_created_at"] = pick
                st.success("불러오기 완료")
                st.rerun()


# =====================================
# 메인 화면
# =====================================
inject_css(tablet_mode)

template_path = get_template_path()
if template_path is None:
    st.error("양식 이미지 파일을 찾을 수 없습니다.")
    st.write("아래 경로 중 하나에 파일이 있어야 합니다.")
    st.code(TEMPLATE_REL)
    st.code(TEMPLATE_ABS)
    st.stop()

bg_url = image_to_data_url(template_path)

if not selected_member:
    st.title("🧵 ELBURIM CRM")
    st.info("왼쪽에서 회원을 등록하거나 선택하세요.")
    st.stop()

member = members[members["member_id"].astype(str) == str(selected_member)].iloc[0]
st.title(f"🧵 고객 상담 기록지 - {member['name']} ({member['member_id']})")

# 상단 액션 바
bar1, bar2, bar3 = st.columns([2, 2, 6])

with bar1:
    if st.button("🆕 새 입력(초기화)", use_container_width=True):
        for fid in FIELD_IDS:
            if fid in st.session_state:
                del st.session_state[fid]
        st.session_state.pop("loaded_created_at", None)
        st.rerun()

with bar2:
    if st.button("💾 저장", use_container_width=True):
        values = {}
        for f in FIELDS:
            fid = f["id"]
            v = st.session_state.get(fid, "")
            # date는 이미 iso string으로 유지
            values[fid] = v
        append_record(selected_member, values)
        st.success("저장 완료")

with bar3:
    loaded_at = st.session_state.get("loaded_created_at", "")
    if loaded_at:
        st.caption(f"불러온 기록: {loaded_at}")

# 배경 시트
st.markdown(
    f"""
    <style>
    .sheet {{
        background-image: url('{bg_url}');
    }}
    </style>
    <div class="sheet">
    """,
    unsafe_allow_html=True
)

# 기본 프리필(회원정보)
if not str(st.session_state.get("name", "")).strip():
    st.session_state["name"] = str(member.get("name", ""))
if not str(st.session_state.get("phone", "")).strip():
    st.session_state["phone"] = str(member.get("phone", ""))

# 필드 렌더
for f in FIELDS:
    left = f["x"] * 100
    top = f["y"] * 100
    width = f["w"] * 100

    fid = f["id"]
    ftype = f["type"]

    st.markdown(
        f"<div class='field' style='left:{left}%; top:{top}%; width:{width}%;'>",
        unsafe_allow_html=True
    )

    if ftype == "text":
        st.text_input("", key=fid, label_visibility="collapsed")

    elif ftype == "number":
        # 종이 느낌 살리려면 text로 바꾸는 게 더 자연스럽지만,
        # 숫자 오입력 방지 위해 number 유지
        # (필요하면 다음 단계에서 text + 숫자검증으로 바꿔줄게)
        st.number_input("", key=fid, step=1000, min_value=0, label_visibility="collapsed")

    elif ftype == "date":
        # date_input은 위젯키를 분리하고, session_state에는 문자열(iso)로 유지
        prev = st.session_state.get(fid, "")
        if isinstance(prev, str) and prev.strip():
            try:
                d = pd.to_datetime(prev).date()
            except:
                d = date.today()
        else:
            d = date.today()

        picked = st.date_input("", value=d, key=f"__date_widget_{fid}", label_visibility="collapsed")
        st.session_state[fid] = picked.isoformat()

    elif ftype == "textarea":
        st.text_area("", key=fid, label_visibility="collapsed")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# 하단: 최근 저장 기록
st.markdown("---")
st.subheader("최근 저장 기록(이 회원)")
rec_df2 = load_records(selected_member).sort_values("created_at", ascending=False).head(5)

if rec_df2.empty:
    st.info("아직 저장된 기록이 없습니다.")
else:
    view = rec_df2.copy()
    view["payload_json"] = view["payload_json"].astype(str).str.slice(0, 80) + "..."
    st.dataframe(view, use_container_width=True)
