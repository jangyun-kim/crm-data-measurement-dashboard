# scripts/load_data.py
import pandas as pd
from config import FILE_CUSTOMER, FILE_PROD_CAL, FILE_STOCK_CAL

def load_customers() -> pd.DataFrame:
    """
    회원정보.xlsx 로드 + 기본 컬럼명 정리
    """
    df = pd.read_excel(FILE_CUSTOMER)
    df = df.rename(columns={
        "회원번호": "customer_id",
        "이름": "name",
        "전화번호(H.P)": "phone_mobile",
        "전화번호☎": "phone_home",
        "유입경로": "source",
        "특이사항": "note",
        "주소": "address",
        "사진번호": "photo_id",
        "생일": "birthday_raw",
    })
    if "customer_id" in df.columns:
        df["customer_id"] = df["customer_id"].astype("Int64")

    cols = [
        "customer_id", "name", "phone_mobile", "phone_home",
        "source", "note", "address", "photo_id", "birthday_raw"
    ]
    df = df[[c for c in cols if c in df.columns]]
    return df


def load_delivery_calendar() -> pd.DataFrame:
    """
    납품달력(캘린더 형식) 원본을 그대로 로드 (header=None)
    실제 정규화는 transform_orders.py에서 수행
    """
    df = pd.read_excel(FILE_PROD_CAL, header=None)
    return df


def load_stock_calendar() -> pd.DataFrame:
    """
    입출고달력(캘린더 형식) 원본 로드 (header=None)
    실제 정규화는 transform_stock.py에서 수행
    """
    df = pd.read_excel(FILE_STOCK_CAL, header=None)
    return df


def load_all():
    """
    run_all.py에서 한 번에 호출할 용도
    """
    customers = load_customers()
    delivery_raw = load_delivery_calendar()
    stock_raw = load_stock_calendar()
    return customers, delivery_raw, stock_raw
