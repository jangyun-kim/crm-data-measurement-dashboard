import sys
from pathlib import Path

import os
from datetime import datetime, date
import pandas as pd
import numpy as np
import streamlit as st
import base64
import re


# -------------------------
# 경로/모듈 설정
# -------------------------
BASE_DIR = Path(__file__).resolve().parent
SCRIPTS_DIR = BASE_DIR / "scripts"
sys.path.append(str(SCRIPTS_DIR))


from config import DATA_RAW_DIR, DATA_CLEAN_DIR, REPORT_DIR, TARGET_YEAR
from settings_manager import load_settings, save_settings, convert_measure_input, apply_unit


# 필요하면 모듈 import
try:
    from transform_stock import transform_stock_table
except Exception:
    transform_stock_table = None


# ==========================
# 설정 파일 경로
# ==========================
SETTINGS_DIR = "data_settings"
TERMS_FILE = os.path.join(SETTINGS_DIR, "용어설정.xlsx")          # 17 1/4 -> 17.25 같은 매장 약속용어
DATA_DIR = "data_members"
MASTER_FILE = os.path.join(DATA_DIR, "members_master.xlsx")
MEASURE_FILE = os.path.join(DATA_DIR, "members_measurements.xlsx")
CONSULT_DIR = "data_consult"
CONSULT_FILE = os.path.join(CONSULT_DIR, "consultations.xlsx")
SETTINGS_DIR = "data_settings"
TERM_MAP_FILE = os.path.join(SETTINGS_DIR, "term_map.json")
FABRIC_FILE = os.path.join(SETTINGS_DIR, "fabric_master.xlsx")  # A0-001 등 원단 일련번호 마스터
LEGACY_FILE = os.path.join("data_raw", "회원정보.xlsx")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONSULT_DIR, exist_ok=True)
os.makedirs(SETTINGS_DIR, exist_ok=True)

def ensure_settings_files():
    # 1) 용어설정.xlsx 보장
    if not os.path.exists(TERMS_FILE):
        df = pd.DataFrame([
            {"표기(입력)": "17 1/4", "inch값": 17.25, "설명": "카라/목 등 1/4 표기"},
            {"표기(입력)": "17-1/4", "inch값": 17.25, "설명": "하이픈 표기"},
            {"표기(입력)": "17¼",    "inch값": 17.25, "설명": "유니코드 분수"},
        ])
        df.to_excel(TERMS_FILE, index=False)

    # 2) 원단마스터.xlsx 보장
    if not os.path.exists(FABRIC_FILE):
        df = pd.DataFrame(columns=[
            "원단코드",      # 예: A0-001
            "원단명",        # 예: 허리노프리즈
            "색상",
            "구분(계절)",    # 여름/사계절 등
            "공급처",
            "원단특이사항",
            "등록일",
            "비고"
        ])
        df.to_excel(FABRIC_FILE, index=False)

def load_terms_dict():
    """용어설정.xlsx를 dict로 로드: 입력문자 -> inch(float)"""
    ensure_settings_files()
    df = pd.read_excel(TERMS_FILE)
    df = df.dropna(subset=["표기(입력)", "inch값"])
    return {str(r["표기(입력)"]).strip(): float(r["inch값"]) for _, r in df.iterrows()}

def parse_inch_input(raw: str, terms_dict: dict):
    """
    inch 입력을 float로 변환.
    - 설정된 약속용어 우선 적용(예: '17 1/4')
    - '17 1/4', '17-1/4', '17¼' 같은 분수 표기 처리
    - 숫자만/소수만도 처리
    실패 시 None
    """
    if raw is None:
        return None

    s = str(raw).strip()
    if s == "":
        return None

    # 1) 설정 용어 우선
    if s in terms_dict:
        return float(terms_dict[s])

    # 2) 유니코드 분수 치환(¼, ½, ¾)
    frac_map = {"¼": "1/4", "½": "1/2", "¾": "3/4"}
    for k, v in frac_map.items():
        s = s.replace(k, f" {v}")

    # 3) '17-1/4' -> '17 1/4'
    s = s.replace("-", " ")

    # 4) '17 1/4' 형태
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s+(\d+)\s*/\s*(\d+)\s*$", s)
    if m:
        whole = float(m.group(1))
        num = float(m.group(2))
        den = float(m.group(3))
        if den != 0:
            return whole + (num / den)

    # 5) '1/4' 단독
    m2 = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*$", s)
    if m2:
        num = float(m2.group(1))
        den = float(m2.group(2))
        if den != 0:
            return num / den

    # 6) 일반 숫자/소수
    try:
        return float(s)
    except:
        return None

def inch_to_cm(x):
    if x is None:
        return None
    try:
        return float(x) * 2.54
    except:
        return None
    

# ==========================
# 좌표(라벨 위치) 설정 파일
# ==========================
LABEL_POS_FILE = os.path.join(SETTINGS_DIR, "치수라벨좌표설정.xlsx")

def ensure_label_pos_file():
    ensure_settings_files()

    if not os.path.exists(LABEL_POS_FILE):
        df = pd.DataFrame([
            # 카테고리: 자켓 / 바지
            {"구분": "자켓", "항목": "어깨", "top(%)": 10, "left(%)": 40},
            {"구분": "자켓", "항목": "가슴", "top(%)": 30, "left(%)": 45},
            {"구분": "자켓", "항목": "허리", "top(%)": 50, "left(%)": 45},
            {"구분": "자켓", "항목": "엉덩이", "top(%)": 70, "left(%)": 45},
            {"구분": "자켓", "항목": "소매", "top(%)": 25, "left(%)": 5},
            {"구분": "자켓", "항목": "총장", "top(%)": 85, "left(%)": 45},

            {"구분": "바지", "항목": "허리", "top(%)": 5, "left(%)": 50},
            {"구분": "바지", "항목": "허벅지", "top(%)": 35, "left(%)": 50},
            {"구분": "바지", "항목": "밑위", "top(%)": 50, "left(%)": 50},
            {"구분": "바지", "항목": "총장", "top(%)": 90, "left(%)": 50},
        ])
        df.to_excel(LABEL_POS_FILE, index=False)

def load_label_positions(kind: str):
    """
    kind: '자켓' or '바지'
    return: {항목: {"top":x,"left":y}}
    """
    ensure_label_pos_file()
    df = pd.read_excel(LABEL_POS_FILE)
    df = df[df["구분"] == kind].copy()
    pos = {}
    for _, r in df.iterrows():
        item = str(r["항목"]).strip()
        pos[item] = {"top": float(r["top(%)"]), "left": float(r["left(%)"])}
    return pos

    

# -------------------------
# 유틸 함수
# -------------------------
def safe_read_excel(path: Path, parse_dates=None):
    if not path.exists():
        return pd.DataFrame()
    return pd.read_excel(path, parse_dates=parse_dates)

def kpi_card(label: str, value, help_text: str = ""):
    """간단 KPI 카드"""
    st.metric(label, value)
    if help_text:
        st.caption(help_text)

# -------------------------
# 데이터 로더들
# -------------------------
def load_orders(year: int = TARGET_YEAR) -> pd.DataFrame:
    f = DATA_CLEAN_DIR / f"orders_{year}.xlsx"
    df = safe_read_excel(f, parse_dates=["order_date"])
    return df

def load_delivery_flat(year: int = TARGET_YEAR) -> pd.DataFrame:
    f = DATA_CLEAN_DIR / f"delivery_flat_with_id_{year}.xlsx"
    df = safe_read_excel(f, parse_dates=["order_date"])
    return df

def load_stock_movement() -> pd.DataFrame:
    f = DATA_CLEAN_DIR / "stock_movement.xlsx"
    if f.exists():
        df = pd.read_excel(f, parse_dates=["date"])
        return df
    # 없으면 data_raw의 재고입출고.xlsx 로부터 생성 시도
    raw_path = DATA_RAW_DIR / "재고입출고.xlsx"
    if raw_path.exists() and transform_stock_table is not None:
        df = transform_stock_table()
        return df
    return pd.DataFrame()

def load_stock_master() -> pd.DataFrame:
    f = DATA_RAW_DIR / "stock_master.xlsx"
    return safe_read_excel(f)

def load_fabric_usage(year: int = TARGET_YEAR) -> pd.DataFrame:
    f = DATA_CLEAN_DIR / f"fabric_usage_{year}.xlsx"
    return safe_read_excel(f, parse_dates=["order_date"])

def load_costing(year: int = TARGET_YEAR) -> pd.DataFrame:
    f = DATA_CLEAN_DIR / f"costing_{year}.xlsx"
    return safe_read_excel(f)

# ==========================================================
# 사이즈 기준 테이블 (반드시 함수보다 위에 위치)
# ==========================================================

JACKET_SIZE_TABLE = [
    {"kr": 90,  "us": 36, "min": 94,  "max": 99},
    {"kr": 95,  "us": 38, "min": 100, "max": 103},
    {"kr": 100, "us": 40, "min": 104, "max": 107},
    {"kr": 105, "us": 42, "min": 108, "max": 111},
    {"kr": 110, "us": 44, "min": 112, "max": 115},
    {"kr": 115, "us": 46, "min": 116, "max": 119},
    {"kr": 120, "us": 48, "min": 120, "max": 124},
]

PANTS_SIZE_TABLE = [
    {"kr": 28, "us": 28, "min": 74,  "max": 79},
    {"kr": 30, "us": 30, "min": 80,  "max": 85},
    {"kr": 32, "us": 32, "min": 86,  "max": 90},
    {"kr": 34, "us": 34, "min": 91,  "max": 95},
    {"kr": 36, "us": 36, "min": 96,  "max": 100},
    {"kr": 38, "us": 38, "min": 101, "max": 105},
    {"kr": 40, "us": 40, "min": 106, "max": 110},
]

# ==========================
# 치수 추천 기능
# ==========================
def recommend_jacket_size(chest):
    for row in JACKET_SIZE_TABLE:
        if row["min"] <= chest <= row["max"]:
            return f"Korea {row['kr']} / US·UK {row['us']}"
    return "사이즈 범위 초과"

def recommend_pants_size(waist):
    for row in PANTS_SIZE_TABLE:
        if row["min"] <= waist <= row["max"]:
            return f"Korea {row['kr']} / US·UK {row['us']}"
    return "사이즈 범위 초과"


# -------------------------
# Streamlit 기본 설정
# -------------------------
st.set_page_config(
    page_title="양복점 데이터 대시보드",
    layout="wide",
)

st.sidebar.title("ELBURIM 양복점")
page = st.sidebar.radio(
    "메뉴 선택",
    ["홈", "회원 관리", "설정"]
)



year = st.sidebar.selectbox("연도 선택", [TARGET_YEAR, TARGET_YEAR - 1, TARGET_YEAR - 2])

st.sidebar.markdown("---")
st.sidebar.caption(f"데이터 기준 경로: `{BASE_DIR}`")


# -------------------------
# 전체 대시보드
# -------------------------
if page == "홈":
    st.title("ELBURIM 양복점")

    orders = load_orders(year)
    stock_mov = load_stock_movement()
    stock_master = load_stock_master()
    fabric_usage = load_fabric_usage(year)

    col1, col2, col3, col4 = st.columns(4)

    # KPI 1: 올해 주문 수
    total_orders = int(orders["order_id"].nunique()) if not orders.empty else 0
    with col1:
        kpi_card("올해 주문 수", total_orders, f"{year}년 기준")

    # KPI 2: 월평균 주문 수
    if not orders.empty:
        orders["month"] = orders["order_date"].dt.to_period("M")
        month_cnt = orders.groupby("month")["order_id"].nunique().mean()
        with col2:
            kpi_card("월평균 주문 수", f"{month_cnt:.1f}건/월")
    else:
        with col2:
            kpi_card("월평균 주문 수", "0")

    # KPI 3: 재고 품목 수
    n_stock_items = int(stock_master["stock_id"].nunique()) if not stock_master.empty else 0
    with col3:
        kpi_card("등록된 자재 품목 수", n_stock_items, "stock_master 기준")

    # KPI 4: 원단 사용량 합계
    if not fabric_usage.empty:
        total_fabric = fabric_usage["fabric_usage"].sum()
        with col4:
            kpi_card("연간 원단 사용량(추정)", f"{total_fabric:.1f} m")
    else:
        with col4:
            kpi_card("연간 원단 사용량(추정)", "0 m")

    st.markdown("---")
    st.subheader("최근 주문 목록")

    if orders.empty:
        st.info("아직 정규화된 주문 데이터(orders_*.xlsx)가 없습니다. run_all.py를 먼저 실행해주세요.")
    else:
        recent = orders.sort_values("order_date", ascending=False).head(20)
        st.dataframe(recent, use_container_width=True)

    st.markdown("---")
    st.subheader("최근 재고 입출고 이벤트")

    if stock_mov.empty:
        st.info("재고입출고 기록이 없습니다. `data_raw/재고입출고.xlsx`에 기록 후 transform_stock_table()을 실행하세요.")
    else:
        latest_stock = stock_mov.sort_values("date", ascending=False).head(30)
        st.dataframe(latest_stock, use_container_width=True)


# -------------------------
# 주문 & 원단 사용량
# -------------------------
elif page == "주문 & 원단 사용량":
    st.title("주문 & 원단 사용량")

    orders = load_orders(year)
    delivery_flat = load_delivery_flat(year)
    fabric_usage = load_fabric_usage(year)

    st.subheader("1) 정규화된 주문 테이블 (orders)")
    if orders.empty:
        st.warning("orders 테이블이 없습니다. run_all.py 또는 transform_delivery_to_orders()를 먼저 실행하세요.")
    else:
        st.dataframe(orders, use_container_width=True, height=400)

    st.subheader("2) 납품달력 원본 정규화 데이터 (delivery_flat_with_id)")
    if delivery_flat.empty:
        st.info("delivery_flat_with_id 데이터가 없습니다.")
    else:
        st.dataframe(delivery_flat.head(50), use_container_width=True, height=300)

    st.subheader("3) 주문별 원단 사용량 (fabric_usage)")
    if fabric_usage.empty:
        st.info("fabric_usage_*.xlsx가 아직 없습니다. fabric_usage.py에서 계산 후 저장하도록 구성하세요.")
    else:
        st.dataframe(fabric_usage, use_container_width=True, height=300)
        st.markdown("#### 월별 원단 사용량 합계")
        tmp = fabric_usage.copy()
        tmp["month"] = tmp["order_date"].dt.to_period("M")
        month_sum = tmp.groupby("month")["fabric_usage"].sum().reset_index()
        month_sum["month"] = month_sum["month"].astype(str)
        st.bar_chart(month_sum.set_index("month"))

# -------------------------
# 재고 관리
# -------------------------
elif page == "재고 관리":
    st.title("재고 관리")

    stock_mov = load_stock_movement()
    stock_master = load_stock_master()

    st.subheader("1) 재고 마스터 (stock_master.xlsx)")
    if stock_master.empty:
        st.warning("stock_master.xlsx가 없습니다. create_stock_master.py / stock_register.py로 생성하세요.")
    else:
        st.dataframe(stock_master, use_container_width=True, height=300)

    st.subheader("2) 재고 입출고 내역 (stock_movement.xlsx)")
    if stock_mov.empty:
        st.info("stock_movement.xlsx가 없습니다. transform_stock_table()을 먼저 실행하세요.")
    else:
        st.dataframe(stock_mov.sort_values("date", ascending=False), use_container_width=True, height=400)

        # 재고 잔량 계산
        bal = stock_mov.groupby("stock_id")["quantity_signed"].sum().reset_index()
        bal = bal.merge(stock_master[["stock_id", "stock_name", "unit"]], how="left", on="stock_id")
        bal = bal.sort_values("stock_id")

        st.markdown("#### 현재 자재별 재고잔량")
        st.dataframe(bal, use_container_width=True, height=300)

        # 간단 부족 경고 (임계값: 원단 10m, 단추/지퍼 20ea)
        st.markdown("#### 재고 부족 경고")
        def threshold(row):
            unit = row.get("unit", "")
            if unit == "m":
                return 10
            elif unit == "ea":
                return 20
            return 5

        bal["threshold"] = bal.apply(threshold, axis=1)
        alert = bal[bal["quantity_signed"] <= bal["threshold"]]

        if alert.empty:
            st.success("현재 재고 부족 경고 품목은 없습니다.")
        else:
            st.error("재고 부족 경고 품목 목록")
            st.dataframe(alert, use_container_width=True, height=200)

# -------------------------
# 원가/마진 분석
# -------------------------
elif page == "원가/마진 분석":
    st.title("원가/마진 분석")

    orders = load_orders(year)
    fabric_usage = load_fabric_usage(year)
    stock_master = load_stock_master()
    costing = load_costing(year)

    st.subheader("1) 원단 단가 정보 (stock_master.xlsx)")
    if stock_master.empty:
        st.warning("stock_master.xlsx가 없습니다. stock_register.py로 원단/자재를 먼저 등록하세요.")
    else:
        st.dataframe(
            stock_master[["stock_id", "stock_name", "category", "unit", "cost_per_unit"]],
            use_container_width=True,
            height=300,
        )

    st.subheader("2) 주문별 원단 사용량 및 재료비")
    if fabric_usage.empty or stock_master.empty:
        st.info("fabric_usage 또는 stock_master가 없어 원단비를 계산할 수 없습니다.")
    else:
        # 아주 간단하게: 특정 원단(F001) 기준으로 원단비 계산 예시
        fabric_id = "F001"
        cost_row = stock_master[stock_master["stock_id"] == fabric_id]

        if cost_row.empty:
            st.warning("F001 원단의 단가 정보가 없습니다. stock_master에서 cost_per_unit을 입력해주세요.")
        else:
            cost_per_m = cost_row["cost_per_unit"].values[0]

            df = fabric_usage.copy()
            df["material_cost"] = df["fabric_usage"] * cost_per_m

            st.dataframe(df[["order_id", "order_date", "item_type", "fabric_usage", "material_cost"]], use_container_width=True)

            total_cost = df["material_cost"].sum()
            st.markdown(f"**총 원단비(추정)**: {total_cost:,.0f} 원 (기준 원단: {fabric_id})")

    st.markdown("---")
    st.subheader("3) 마진 분석(향후 확장)")

    st.info(
        "지금 단계에서는 원단비까지만 계산했습니다.\n"
        "향후에는 주문별 판매가, 공임비 등을 추가해 총원가/마진률까지 계산하도록 확장할 수 있습니다."
    )

# -------------------------
# 자동 원단 출고 처리
# -------------------------
elif page == "자동 원단 출고 처리":
    st.title("주문 기반 원단 자동 출고 시스템")

    # 데이터 로드
    orders = load_orders(year)
    stock_master = load_stock_master()
    stock_mov = load_stock_movement()

    if orders.empty:
        st.warning("주문 데이터가 없습니다. 먼저 run_all.py를 실행하세요.")
        st.stop()

    if stock_master.empty:
        st.warning("stock_master.xlsx가 없습니다. 먼저 신규 원단을 등록하세요.")
        st.stop()

    # 주문 선택
    st.subheader("1) 출고할 주문 선택")
    order_list = orders["order_id"].unique().tolist()
    selected_order = st.selectbox("주문 선택", order_list)

    # 주문 상세정보 표시
    if selected_order:
        selected_row = orders[orders["order_id"] == selected_order]
        st.write("### 선택된 주문 상세")
        st.dataframe(selected_row, use_container_width=True)

    # 원단 OUT 자동 처리 버튼
    st.subheader("2) 자동 원단 출고 실행")

    if st.button("원단 자동 출고 처리하기"):
        from auto_stock_out import auto_stock_out

        success = auto_stock_out(selected_order, orders, stock_master)

        if success:
            st.success(f"주문 {selected_order} → 원단 자동 출고 완료!")
            st.info("재고입출고.xlsx에 OUT 기록이 자동 추가되었습니다.")
        else:
            st.error("원단 출고 처리 도중 문제가 발생했습니다. 로그를 확인하세요.")

    st.markdown("---")

    # 현재 재고 상황
    st.subheader("3) 현재 원단 재고 잔량 확인")

    if stock_mov.empty:
        st.info("현재 재고 이동 내역이 없습니다.")
    else:
        bal = stock_mov.groupby("stock_id")["quantity_signed"].sum().reset_index()
        bal = bal.merge(stock_master[["stock_id", "stock_name", "unit"]], on="stock_id", how="left")
        st.dataframe(bal, use_container_width=True)

# =========================================
# 회원 관리 기능 (상담 입력 + 치수 입력)
# =========================================
elif page == "회원 관리":
    st.title("회원 관리")

    # 신규 회원 등록 UI 상태 관리
    if "show_register" not in st.session_state:
        st.session_state.show_register = False

    # ==========================
    # 치수 시각화
    # ==========================

    # HTML 기반 시각화 함수
    def render_measure_image(image_path, labels):
        # 이미지 파일이 없을 경우 안내만 표시
        if not os.path.exists(image_path):
            st.warning(f"치수 시각화 이미지가 없습니다: {image_path}")
            return

        with open(image_path, "rb") as f:
            img_base = base64.b64encode(f.read()).decode()

        html = f"""
        <div style="position: relative; width: 100%; max-width: 400px; margin:auto;">
            <img src="data:image/png;base64,{img_base}" style="width:100%;">
        """

        for label, info in labels.items():
            value = info.get("value")

            if value is None or pd.isna(value) or value <= 0:
                continue

            html += f"""
            <div style="
                position: absolute;
                top: {info['top']}%;
                left: {info['left']}%;
                background: rgba(255,255,255,0.8);
                padding: 3px 6px;
                border-radius: 4px;
                font-size: 12px;
                border: 1px solid #666;
                white-space: nowrap;
            ">
                {label}: {round(float(value),1)}
            </div>
            """

        html += "</div>"

        st.components.v1.html(html, height = 450)

    # ===================================================================
    # 생년월일 정규화
    # ===================================================================
    def normalize_birth_date(val):
        if pd.isna(val):
            return ""
        if isinstance(val, str):
            try:
                return pd.to_datetime(val).strftime("%Y-%m-%d")
            except:
                return ""
        if isinstance(val, (int, float)):
            try:
                d = pd.to_datetime(val, unit="D", origin="1899-12-30")
                return d.strftime("%Y-%m-%d")
            except:
                return ""
        return ""

    # ===================================================================
    # 전화번호 + note 정규화
    # ===================================================================
    def clean_phone_and_note(value):
        if pd.isna(value):
            return "", ""

        raw = str(value).strip()
        if raw == "":
            return "", ""

        # 한국 010 패턴만 정상으로 인정
        phone_match = re.search(r"010[^\d]*\d{3,4}[^\d]*\d{4}", raw)
        phone = ""
        note = ""

        # ---------- 정상 한국 휴대폰 ----------
        if phone_match:
            phone_part = phone_match.group(0)
            digits = re.sub(r"[^0-9]", "", phone_part)

            if len(digits) == 11 and digits.startswith("010"):
                phone = f"{digits[0:3]}-{digits[3:7]}-{digits[7:11]}"

                # 전화번호 제외한 문자 가져오기
                text_part = re.sub(r"[0-9\-\s:+]+", "", raw).strip()
                if text_part:
                    note = f"{text_part} 전화번호"
                return phone, note

        # ---------- 한국번호가 아닌 경우 ----------
        if any(c.isalpha() for c in raw) or any(c in raw for c in ["+", ":"]):
            return "", f"한국 번호 아님: {raw}"

        # ---------- 숫자만 있는 쓰레기 데이터 ----------
        return "", ""

    # ===================================================================
    # 회원정보.xlsx → 자동 정규화 + 병합 + ID 생성
    # ===================================================================
    def load_or_create_members():
        # 이미 정상 파일 있으면 그대로 로드
        if os.path.exists(MASTER_FILE):
            df = pd.read_excel(MASTER_FILE)

            # 혹시라도 Unnamed 컬럼이 남아 있으면 제거
            df = df.loc[:, ~df.columns.str.contains("Unnamed")]
            return df

        # raw 파일 없으면 빈 파일 생성
        if not os.path.exists(LEGACY_FILE):
            df = pd.DataFrame(columns=[
                "member_id", "name", "birth_date", "phone",
                "address", "job", "first_visit", "note"
            ])
            df.to_excel(MASTER_FILE, index=False)
            return df

        # -----------------------------
        # 회원정보.xlsx → 시트 병합
        # -----------------------------
        xls = pd.ExcelFile(LEGACY_FILE)
        frames = []
        for s in xls.sheet_names:
            if "회원" in s:
                frames.append(pd.read_excel(xls, sheet_name=s))

        legacy = pd.concat(frames, ignore_index=True)

        # -----------------------------
        # mapping (대표님 제공)
        # -----------------------------
        mapping = {
            "이름": "name",
            "전화번호": "phone",
            "생년월일": "birth_date",
            "주소": "address",
            "직업": "job",
            "메모": "note"
        }
        for k, v in mapping.items():
            if k in legacy.columns:
                legacy.rename(columns={k: v}, inplace=True)

        # 필수 컬럼만 유지
        keep_cols = ["name", "phone", "birth_date", "address", "job", "note"]
        for col in keep_cols:
            if col not in legacy.columns:
                legacy[col] = ""

        legacy = legacy[keep_cols]  # 여기서 완전히 정리됨

        # -----------------------------
        # 생년월일 정규화
        # -----------------------------
        legacy["birth_date"] = legacy["birth_date"].apply(normalize_birth_date)

        # -----------------------------
        # 전화번호 + note 정규화
        # -----------------------------
        new_phone = []
        new_note = []

        for _, row in legacy.iterrows():
            p, n = clean_phone_and_note(row["phone"])

            base_note = str(row.get("note", "")).strip()
            final_note = base_note

            if n:
                if final_note:
                    final_note += " / "
                final_note += n

            new_phone.append(p)
            new_note.append(final_note)

        legacy["phone"] = new_phone
        legacy["note"] = new_note

        # -----------------------------
        # 중복 제거
        # -----------------------------
        dup1 = legacy[legacy["phone"] != ""].drop_duplicates("phone")
        dup2 = legacy[legacy["phone"] == ""].drop_duplicates(["name", "birth_date"])
        merged = pd.concat([dup1, dup2], ignore_index=True)

        # -----------------------------
        # 회원번호 생성
        # -----------------------------
        merged = merged.reset_index(drop=True)
        merged["member_id"] = merged.index + 1
        merged["member_id"] = merged["member_id"].apply(lambda x: f"M{x:04d}")

        # 첫 방문일
        today = datetime.now().strftime("%Y-%m-%d")
        merged["first_visit"] = today

        # -----------------------------
        # 컬럼 순서 확정 + 저장
        # -----------------------------
        final = merged[[
            "member_id", "name", "birth_date", "phone",
            "address", "job", "first_visit", "note"
        ]]

        final.to_excel(MASTER_FILE, index=False)
        return final

    # ===================================================================
    # 경로 및 파일명 정의
    # ===================================================================
    DATA_DIR = "data_members"
    MASTER_FILE = os.path.join(DATA_DIR, "members_master.xlsx")
    MEASURE_FILE = os.path.join(DATA_DIR, "members_measurements.xlsx")
    LEGACY_FILE = os.path.join("data_raw", "회원정보.xlsx")

    os.makedirs(DATA_DIR, exist_ok=True)


    # ===================================================================
    # 파일 로드
    # ===================================================================
    members = load_or_create_members()

    # ===================================================================
    # 치수 파일 보장
    # ===================================================================
    if not os.path.exists(MEASURE_FILE):
        pd.DataFrame(columns=[
            "member_id", "measure_date",

            # inch 원본
            "shoulder_in", "chest_in", "waist_in", "hip_in",
            "sleeve_in", "jacket_length_in",
            "pants_waist_in", "thigh_in", "rise_in", "pants_length_in",

            # cm 변환
            "shoulder_cm", "chest_cm", "waist_cm", "hip_cm",
            "sleeve_cm", "jacket_length_cm",
            "pants_waist_cm", "thigh_cm", "rise_cm", "pants_length_cm",

            # 참고 신체
            "weight", "height"
        ]).to_excel(MEASURE_FILE, index=False)
    else:
        # 기존 파일에 컬럼이 부족하면 추가
        dfm = pd.read_excel(MEASURE_FILE)
        need_cols = [
            "shoulder_in","chest_in","waist_in","hip_in","sleeve_in","jacket_length_in",
            "pants_waist_in","thigh_in","rise_in","pants_length_in",
            "shoulder_cm","chest_cm","waist_cm","hip_cm","sleeve_cm","jacket_length_cm",
            "pants_waist_cm","thigh_cm","rise_cm","pants_length_cm"
        ]
        for c in need_cols:
            if c not in dfm.columns:
                dfm[c] = pd.NA
        dfm.to_excel(MEASURE_FILE, index=False)


    # ===================================================================
    # 회원 검색
    # ===================================================================
    st.markdown("---")
    st.subheader("1) 회원 검색 및 조회")

    search_mode = st.radio("검색 방식 선택", ["회원번호 검색", "이름 검색"])
    selected_member = None

    if search_mode == "회원번호 검색":
        keyword = st.text_input("회원번호 입력 (예: M0012)")
        if keyword:
            result = members[members["member_id"].str.contains(keyword, case=False, na=False)]
            st.dataframe(result, use_container_width=True)
            if len(result) == 1:
                selected_member = result.iloc[0]["member_id"]

    else:
        key = st.text_input("이름 입력")
        if key:
            matched = members[members["name"].str.contains(key, na=False)]
            st.dataframe(matched, use_container_width=True)

            if len(matched) > 0:
                pick = st.selectbox(
                    "회원 선택", ["선택 안 함"] +
                    (matched["member_id"] + " - " + matched["name"]).tolist()
                )
                if pick != "선택 안 함":
                    selected_member = pick.split(" - ")[0]

    # ===================================================================
    # 회원 상세 + 치수 입력
    # ===================================================================
    if selected_member:
        st.markdown("---")
        st.subheader("회원 상세 정보")

        info = members[members["member_id"] == selected_member].iloc[0]

        c1, c2 = st.columns(2)
        with c1:
            st.write(f"이름: {info['name']}")
            st.write(f"생년월일: {info['birth_date']}")

            try:
                age = int((datetime.now().date() - pd.to_datetime(info["birth_date"]).date()).days / 365.25)
                st.write(f"나이: {age}세")
            except:
                pass

        with c2:
            st.write(f"전화번호: {info['phone']}")
            st.write(f"주소: {info['address']}")
            st.write(f"직업: {info['job']}")

        st.markdown("### 치수 입력")

        terms_dict = load_terms_dict()

        with st.form(f"measure_form_{selected_member}"):
            m_date = st.date_input("측정일")

            st.caption("치수 입력은 inch 기준입니다. 예: 17 1/4, 17-1/4, 17¼, 18.5")

            a, b, c = st.columns(3)
            with a:
                shoulder_raw = st.text_input("어깨(inch)", value="")
                chest_raw = st.text_input("가슴둘레(inch)", value="")
                waist_raw = st.text_input("허리둘레(inch)", value="")
            with b:
                hip_raw = st.text_input("엉덩이둘레(inch)", value="")
                sleeve_raw = st.text_input("소매길이(inch)", value="")
                jlen_raw = st.text_input("총장(자켓)(inch)", value="")
            with c:
                pwaist_raw = st.text_input("바지 허리(inch)", value="")
                thigh_raw = st.text_input("허벅지(inch)", value="")
                rise_raw = st.text_input("밑위(inch)", value="")
                plen_raw = st.text_input("바지 총장(inch)", value="")

            w1, w2 = st.columns(2)
            with w1:
                weight = st.number_input("몸무게(kg)", step=0.1)
            with w2:
                height = st.number_input("키(cm)", step=0.1)

            # 변환 미리보기
            def show_cm(label, raw):
                inch_val = parse_inch_input(raw, terms_dict)
                cm_val = inch_to_cm(inch_val)
                if inch_val is None:
                    st.caption(f"{label}: 입력 대기")
                else:
                    st.caption(f"{label}: {inch_val:.2f} inch → {cm_val:.1f} cm")

            st.markdown("#### 변환 미리보기")
            p1, p2 = st.columns(2)
            with p1:
                show_cm("어깨", shoulder_raw)
                show_cm("가슴", chest_raw)
                show_cm("허리", waist_raw)
                show_cm("엉덩이", hip_raw)
                show_cm("소매", sleeve_raw)
            with p2:
                show_cm("자켓 총장", jlen_raw)
                show_cm("바지 허리", pwaist_raw)
                show_cm("허벅지", thigh_raw)
                show_cm("밑위", rise_raw)
                show_cm("바지 총장", plen_raw)

            save_btn = st.form_submit_button("치수 저장")

        if save_btn:
            shoulder_in = parse_inch_input(shoulder_raw, terms_dict)
            chest_in = parse_inch_input(chest_raw, terms_dict)
            waist_in = parse_inch_input(waist_raw, terms_dict)
            hip_in = parse_inch_input(hip_raw, terms_dict)
            sleeve_in = parse_inch_input(sleeve_raw, terms_dict)
            jlen_in = parse_inch_input(jlen_raw, terms_dict)

            pwaist_in = parse_inch_input(pwaist_raw, terms_dict)
            thigh_in = parse_inch_input(thigh_raw, terms_dict)
            rise_in = parse_inch_input(rise_raw, terms_dict)
            plen_in = parse_inch_input(plen_raw, terms_dict)

            new_row = {
                "member_id": selected_member,
                "measure_date": m_date.strftime("%Y-%m-%d"),

                # inch 원본
                "shoulder_in": shoulder_in,
                "chest_in": chest_in,
                "waist_in": waist_in,
                "hip_in": hip_in,
                "sleeve_in": sleeve_in,
                "jacket_length_in": jlen_in,
                "pants_waist_in": pwaist_in,
                "thigh_in": thigh_in,
                "rise_in": rise_in,
                "pants_length_in": plen_in,

                # cm 변환
                "shoulder_cm": inch_to_cm(shoulder_in),
                "chest_cm": inch_to_cm(chest_in),
                "waist_cm": inch_to_cm(waist_in),
                "hip_cm": inch_to_cm(hip_in),
                "sleeve_cm": inch_to_cm(sleeve_in),
                "jacket_length_cm": inch_to_cm(jlen_in),
                "pants_waist_cm": inch_to_cm(pwaist_in),
                "thigh_cm": inch_to_cm(thigh_in),
                "rise_cm": inch_to_cm(rise_in),
                "pants_length_cm": inch_to_cm(plen_in),

                "weight": weight,
                "height": height
            }

            measures = pd.concat([measures, pd.DataFrame([new_row])], ignore_index=True)
            measures.to_excel(MEASURE_FILE, index=False)
            st.success("치수 저장 완료")


        st.write("### 치수 이력")
        st.dataframe(
            measures[measures["member_id"] == selected_member].sort_values("measure_date", ascending=False),
            use_container_width=True
        )

        # 최근 치수 1건 불러오기
        recent = measures[measures["member_id"] == selected_member].copy()
        if not recent.empty:
            recent["measure_date_dt"] = pd.to_datetime(recent["measure_date"], errors="coerce")
            recent = recent.sort_values("measure_date_dt", ascending=False).iloc[0]


            st.markdown("## 체형 시각화")

            colJ, colP = st.columns(2)

            # -----------------------------
            # 자켓 이미지 시각화
            # -----------------------------
            with colJ:
                st.markdown("### 자켓 치수 시각화")
                
                render_measure_image("data_members/measure_images/jacket.png", {
                        "어깨": {"value": recent["shoulder"], "top": 10, "left": 40},
                        "가슴": {"value": recent["chest"], "top": 30, "left": 45},
                        "허리": {"value": recent["waist"], "top": 50, "left": 45},
                        "엉덩이": {"value": recent["hip"], "top": 70, "left": 45},
                        "소매": {"value": recent["sleeve"], "top": 25, "left": 5},
                        "총장": {"value": recent["jacket_length"], "top": 85, "left": 45},
                    }
                )

            # -----------------------------
            # 바지 이미지 시각화
            # -----------------------------
            with colP:
                st.markdown("### 바지 치수 시각화")

                render_measure_image("data_members/measure_images/pants.png", {
                        "허리": {"value": recent["pants_waist"], "top": 5, "left": 50},
                        "허벅지": {"value": recent["thigh"], "top": 35, "left": 50},
                        "밑위": {"value": recent["rise"], "top": 50, "left": 50},
                        "총장": {"value": recent["pants_length"], "top": 90, "left": 50},
                    }
                )

            # ==========================================================
            # 자동 사이즈 추천
            # ==========================================================
            st.markdown("## 자동 사이즈 추천")

            if not recent.empty:
                # 기존 추천(너가 쓰던 함수 유지 가능)
                jacket_size = recommend_jacket_size(recent.get("chest_cm", None))
                pants_size = recommend_pants_size(recent.get("pants_waist_cm", None))

                # 추가: 기성 호칭 추천(설정 규칙 기반)
                jacket_k = recommend_size_by_rule("자켓", recent.get("chest_cm", None))

                colA, colB = st.columns(2)
                with colA:
                    st.markdown("### 자켓 추천 사이즈")
                    st.info(jacket_size)
                    st.markdown("### 자켓 기성 호칭 추천")
                    st.success(jacket_k)

                with colB:
                    st.markdown("### 바지 추천 사이즈")
                    st.info(pants_size)



    # ===================================================================
    # 신규 회원 등록 버튼
    # ===================================================================
    st.markdown("---")
    st.subheader("2) 회원 관리 기능")

    if st.button("신규 회원 등록"):
        st.session_state.show_register = True

    # ===================================================================
    # 신규 회원 등록 UI
    # ===================================================================
    if st.session_state.show_register:
        st.markdown("---")
        st.subheader("신규 회원 등록")

        name = st.text_input("이름")
        bdate = st.date_input(
            "생년월일",
            min_value = date(1900, 1, 1),
            max_value = date.today(),
            value = date(2000, 1, 1) # 기본 표시 연도
        )
        phone = st.text_input("전화번호")
        address = st.text_input("주소")
        job = st.text_input("직업")
        note = st.text_area("메모")

        if st.button("등록하기"):
            df = pd.read_excel(MASTER_FILE)

            if df.empty:
                new_id = "M0001"
            else:
                last = df["member_id"].iloc[-1]
                num = int(last[1:])
                new_id = f"M{num + 1:04d}"

            today = datetime.now().strftime("%Y-%m-%d")

            # 입력된 전화번호 정규화
            p, n = clean_phone_and_note(phone)
            final_note = note
            if n:
                if final_note:
                    final_note += " / "
                final_note += n

            new_row = {
                "member_id": new_id,
                "name": name,
                "birth_date": bdate.strftime("%Y-%m-%d"),
                "phone": p,
                "address": address,
                "job": job,
                "first_visit": today,
                "note": final_note
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            df.to_excel(MASTER_FILE, index=False)

            st.success(f"신규 회원 등록 완료 (ID: {new_id})")

            # 신규 등록 UI 닫기
            st.session_state.show_register = False


elif page == "설정":
    st.title("설정")

    ensure_settings_files()

    tab1, tab2, tab3, tab4 = st.tabs(["용어 설정(치수 표기)", "원단 마스터(일련번호)", "치수 라벨 위치(좌표)", "기성 사이즈 규칙"])

    # ==========================
    # 1) 용어 설정(치수 표기)
    # ==========================
    with tab1:
        st.subheader("1) 매장 약속 치수 표기 설정")
        st.write("예: 17 1/4, 17-1/4, 17¼ 같은 입력을 inch 값으로 통일하기 위한 규칙을 관리합니다.")

        df_terms = pd.read_excel(TERMS_FILE)
        df_terms = df_terms.loc[:, ~df_terms.columns.str.contains("Unnamed", na=False)]

        edited = st.data_editor(
            df_terms,
            num_rows="dynamic",
            use_container_width=True
        )

        c1, c2 = st.columns([1, 1])
        with c1:
            if st.button("용어 설정 저장"):
                # 필수 컬럼 보장
                for col in ["표기(입력)", "inch값", "설명"]:
                    if col not in edited.columns:
                        edited[col] = ""

                # 정리
                edited["표기(입력)"] = edited["표기(입력)"].astype(str).str.strip()
                edited["inch값"] = pd.to_numeric(edited["inch값"], errors="coerce")
                edited = edited.dropna(subset=["표기(입력)", "inch값"])
                edited = edited.drop_duplicates(subset=["표기(입력)"], keep="last")

                edited.to_excel(TERMS_FILE, index=False)
                st.success("저장 완료")

        with c2:
            st.markdown("**입력 예시**")
            st.code(
                "17 1/4\n17-1/4\n17¼\n18\n18.5\n1/4",
                language="text"
            )

    # ==========================
    # 2) 원단 마스터 CRUD
    # ==========================
    with tab2:
        st.subheader("2) 원단 일련번호 마스터 관리")
        st.write("예: A0-001 같은 원단코드와 원단명/색상/공급처/계절 구분 등을 관리합니다.")

        df_fabric = pd.read_excel(FABRIC_FILE)
        df_fabric = df_fabric.loc[:, ~df_fabric.columns.str.contains("Unnamed", na=False)]

        edited2 = st.data_editor(
            df_fabric,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("원단 마스터 저장"):
            # 필수 컬럼 보장
            must_cols = ["원단코드", "원단명", "색상", "구분(계절)", "공급처", "원단특이사항", "등록일", "비고"]
            for col in must_cols:
                if col not in edited2.columns:
                    edited2[col] = ""

            edited2["원단코드"] = edited2["원단코드"].astype(str).str.strip()
            edited2["원단명"] = edited2["원단명"].astype(str).str.strip()
            edited2["등록일"] = edited2["등록일"].astype(str).str.strip()

            # 코드 비어있는 행 제거
            edited2 = edited2[edited2["원단코드"] != ""].copy()

            # 동일 코드면 마지막 값으로 유지
            edited2 = edited2.drop_duplicates(subset=["원단코드"], keep="last")

            edited2.to_excel(FABRIC_FILE, index=False)
            st.success("저장 완료")

    with tab3:
        st.subheader("3) 치수 라벨 위치(좌표) 설정")
        st.write("자켓/바지 이미지 위에 표시되는 수치 라벨의 위치(top/left)를 매장에서 직접 조정합니다.")

        ensure_label_pos_file()
        df_pos = pd.read_excel(LABEL_POS_FILE)
        df_pos = df_pos.loc[:, ~df_pos.columns.str.contains("Unnamed", na=False)]

        edited_pos = st.data_editor(
            df_pos,
            num_rows="dynamic",
            use_container_width=True
        )

        if st.button("라벨 좌표 저장"):
            # 필수 컬럼 보장
            for col in ["구분", "항목", "top(%)", "left(%)"]:
                if col not in edited_pos.columns:
                    edited_pos[col] = ""

            edited_pos["구분"] = edited_pos["구분"].astype(str).str.strip()
            edited_pos["항목"] = edited_pos["항목"].astype(str).str.strip()
            edited_pos["top(%)"] = pd.to_numeric(edited_pos["top(%)"], errors="coerce")
            edited_pos["left(%)"] = pd.to_numeric(edited_pos["left(%)"], errors="coerce")

            edited_pos = edited_pos.dropna(subset=["구분", "항목", "top(%)", "left(%)"])
            edited_pos = edited_pos[(edited_pos["top(%)"] >= 0) & (edited_pos["top(%)"] <= 100)]
            edited_pos = edited_pos[(edited_pos["left(%)"] >= 0) & (edited_pos["left(%)"] <= 100)]

            edited_pos.to_excel(LABEL_POS_FILE, index=False)
            st.success("저장 완료")

    with tab4:
        st.subheader("4) 기성/가봉 사이즈 규칙 관리")
        st.write("치수(cm) 기준으로 K52 같은 기성 호칭을 추천하는 규칙을 관리합니다. (매장 룰대로 수정)")

        ensure_size_rule_file()
        df_rule = pd.read_excel(SIZE_RULE_FILE)
        df_rule = df_rule.loc[:, ~df_rule.columns.str.contains("Unnamed", na=False)]

        edited_rule = st.data_editor(df_rule, num_rows="dynamic", use_container_width=True)

        if st.button("사이즈 규칙 저장"):
            for col in ["종류", "기준항목", "최소(cm)", "최대(cm)", "추천호칭"]:
                if col not in edited_rule.columns:
                    edited_rule[col] = ""

            edited_rule["종류"] = edited_rule["종류"].astype(str).str.strip()
            edited_rule["기준항목"] = edited_rule["기준항목"].astype(str).str.strip()
            edited_rule["추천호칭"] = edited_rule["추천호칭"].astype(str).str.strip()
            edited_rule["최소(cm)"] = pd.to_numeric(edited_rule["최소(cm)"], errors="coerce")
            edited_rule["최대(cm)"] = pd.to_numeric(edited_rule["최대(cm)"], errors="coerce")

            edited_rule = edited_rule.dropna(subset=["종류", "기준항목", "최소(cm)", "최대(cm)", "추천호칭"])
            edited_rule.to_excel(SIZE_RULE_FILE, index=False)
            st.success("저장 완료")



    SIZE_RULE_FILE = os.path.join(SETTINGS_DIR, "기성사이즈규칙.xlsx")

    def ensure_size_rule_file():
        ensure_settings_files()

        if not os.path.exists(SIZE_RULE_FILE):
            # 예시는 "가슴둘레(cm)" 기준. (매장 룰로 수정 가능)
            df = pd.DataFrame([
                {"종류": "자켓", "기준항목": "가슴", "최소(cm)": 88, "최대(cm)": 92, "추천호칭": "K48"},
                {"종류": "자켓", "기준항목": "가슴", "최소(cm)": 93, "최대(cm)": 97, "추천호칭": "K50"},
                {"종류": "자켓", "기준항목": "가슴", "최소(cm)": 98, "최대(cm)": 102, "추천호칭": "K52"},
                {"종류": "자켓", "기준항목": "가슴", "최소(cm)": 103, "최대(cm)": 107, "추천호칭": "K54"},
            ])
            df.to_excel(SIZE_RULE_FILE, index=False)

    def recommend_size_by_rule(kind: str, 기준값_cm: float):
        """
        kind: '자켓' 같은 종류
        기준값_cm: float
        return: 추천호칭 or "규칙없음"
        """
        ensure_size_rule_file()
        if 기준값_cm is None or pd.isna(기준값_cm):
            return "추천 불가(기준값 없음)"

        df = pd.read_excel(SIZE_RULE_FILE)
        df = df[df["종류"] == kind].copy()

        for col in ["최소(cm)", "최대(cm)"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df = df.dropna(subset=["최소(cm)", "최대(cm)", "추천호칭"])

        for _, r in df.iterrows():
            if r["최소(cm)"] <= 기준값_cm <= r["최대(cm)"]:
                return str(r["추천호칭"]).strip()

        return "해당 구간 규칙 없음"
