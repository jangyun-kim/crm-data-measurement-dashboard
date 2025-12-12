# scripts/transform_orders.py
import re
import math
import pandas as pd
from config import DATA_CLEAN_DIR, TARGET_YEAR

def parse_name_and_code(raw):
    """
    '홍길동(1234)' -> ('홍길동', '1234')
    괄호가 없으면 ('홍길동', None)
    """
    if not isinstance(raw, str):
        return None, None
    s = raw.strip()
    m = re.match(r"(.+)\((\d+)\)", s)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return s, None


def flatten_delivery_calendar(delivery_raw: pd.DataFrame, year: int) -> pd.DataFrame:
    """
    엘부림 납품달력(캘린더 구조)을 실제 '행 데이터'로 펼치는 로직.

    구조 가정 (실제 파일 확인해서 맞춰놓은 버전):
    - 어느 행엔가 0열에 '월/일', 1·5·9·13·17·21·25열에 '일,월,화,수,목,금,토'가 있음 → 요일 헤더
    - 그 아래 여러 구간에
        * 0열에 '1월', '2월' 등 월 정보
        * 요일 열들에 1,2,3 또는 '1(신정)' 같은 숫자가 있는 줄 → '날짜 헤더 줄'
        * 그 다음 줄들에서 각 요일 열에 '이름(코드)'가 들어 있음 → 실제 주문 레코드
    """

    df = delivery_raw
    n_rows, n_cols = df.shape

    # 1) 요일 헤더 행 찾기 (0열이 '월/일'인 행)
    weekday_row_idx = None
    for i in range(n_rows):
        if isinstance(df.iat[i, 0], str) and df.iat[i, 0].strip() == "월/일":
            weekday_row_idx = i
            break

    if weekday_row_idx is None:
        print("[flatten_delivery_calendar] '월/일' 헤더를 찾지 못했습니다.")
        return pd.DataFrame()

    weekday_row = df.iloc[weekday_row_idx]
    week_candidates = ["일", "월", "화", "수", "목", "금", "토"]

    # 요일이 들어있는 열 인덱스 (ex: 1,5,9,13,17,21,25)
    day_cols = [
        c for c in range(1, n_cols)
        if isinstance(weekday_row[c], str)
        and weekday_row[c].strip() in week_candidates
    ]

    records = []
    current_month = None

    # 2) 요일 헤더 아래쪽 전체를 스캔하면서
    #    '날짜 헤더 줄'과 그 아래 실제 이름이 있는 줄들을 처리
    r = weekday_row_idx + 1
    while r < n_rows:
        row0 = df.iat[r, 0]

        # 2-1) 월 정보 업데이트 (ex: '1월', '2월')
        if isinstance(row0, str) and "월" in row0:
            try:
                current_month = int(row0.replace("월", "").strip())
            except Exception:
                pass

        # 2-2) 이 줄이 '날짜 헤더 줄'인지 판단
        day_values = {}
        for c in day_cols:
            val = df.iat[r, c]

            if isinstance(val, (int, float)) and not (isinstance(val, float) and math.isnan(val)):
                day_values[c] = int(val)
            elif isinstance(val, str):
                # '1(신정)' 같은 경우 처리 → 숫자만 떼기
                m = re.match(r"(\d+)", val.strip())
                if m:
                    day_values[c] = int(m.group(1))

        # day_values에 뭔가 들어있으면 이 줄은 날짜 헤더 줄
        if day_values:
            header_row_idx = r
            r2 = header_row_idx + 1

            # 2-3) 다음 줄들(r2)을 내려가며, 또 다른 날짜 헤더 줄이 나오기 전까지 이름을 수집
            while r2 < n_rows:
                # 다음 날짜 헤더 줄인지 먼저 체크
                next_day_values = {}
                for c in day_cols:
                    v = df.iat[r2, c]
                    if isinstance(v, (int, float)) and not (isinstance(v, float) and math.isnan(v)):
                        next_day_values[c] = v
                    elif isinstance(v, str):
                        m = re.match(r"(\d+)", v.strip())
                        if m:
                            next_day_values[c] = int(m.group(1))

                if next_day_values:
                    # 새로운 날짜 헤더 줄 → 현재 블록 종료
                    break

                # 이 줄(r2)에서 각 요일 열에 있는 이름(코드)들을 체크
                for c in day_cols:
                    cell = df.iat[r2, c]
                    if isinstance(cell, str) and cell.strip() != "":
                        name, code = parse_name_and_code(cell)
                        day = day_values.get(c)

                        # 날짜 만들기
                        if current_month is not None and day is not None:
                            try:
                                date = pd.Timestamp(year=year, month=current_month, day=day)
                            except Exception:
                                date = None
                        else:
                            date = None

                        # 오른쪽 3칸 정도를 품목 정보로 사용
                        item1 = df.iat[r2, c + 1] if c + 1 < n_cols else None
                        item2 = df.iat[r2, c + 2] if c + 2 < n_cols else None
                        item3 = df.iat[r2, c + 3] if c + 3 < n_cols else None

                        records.append({
                            "order_date": date,
                            "customer_name_raw": name,
                            "customer_code_raw": code,
                            "weekday": weekday_row[c],
                            "month": current_month,
                            "day": day,
                            "item_info_1": item1,
                            "item_info_2": item2,
                            "item_info_3": item3,
                            "row_idx": r2,
                            "col_idx": c,
                        })

                r2 += 1

            # 다음 날짜 헤더 블록으로 이동
            r = r2
        else:
            # 날짜 헤더가 아니면 그냥 다음 줄로
            r += 1

    flat = pd.DataFrame(records)
    return flat


def generate_order_ids(flat: pd.DataFrame) -> pd.DataFrame:
    """
    A안: 연도 + customer_code_raw + 일련번호
    - customer_code_raw가 없으면 customer_name_raw 기준으로 surrogate code 생성
    """

    df = flat.copy()

    # 1) customer_code_raw 없으면 생성
    if "customer_code_raw" not in df.columns:
        # 이름 기준으로 임시 코드 만들기
        if "customer_name_raw" in df.columns:
            unique_names = df["customer_name_raw"].dropna().unique()
            name_to_code = {name: i + 1 for i, name in enumerate(unique_names)}
            df["customer_code_raw"] = df["customer_name_raw"].map(name_to_code)
            print("[generate_order_ids] customer_code_raw 컬럼이 없어 이름 기반 surrogate code를 생성했습니다.")
        else:
            # 이름도 없으면 그냥 모두 1로 (최악의 fallback)
            df["customer_code_raw"] = 1
            print("[generate_order_ids] customer_name_raw도 없어 모든 row에 동일 코드 1을 부여했습니다.")

    # 2) 정렬
    df = df.sort_values(["customer_code_raw", "order_date"]).reset_index(drop=True)

    # 3) 코드+연도 기준 일련번호 부여
    seq_list = []
    prev_code = None
    prev_year = None
    seq = 0

    for _, row in df.iterrows():
        code = row["customer_code_raw"]
        y = row["order_date"].year if pd.notna(row["order_date"]) else None

        if (code != prev_code) or (y != prev_year):
            seq = 1
            prev_code = code
            prev_year = y
        else:
            seq += 1

        seq_list.append(seq)

    df["order_seq"] = seq_list

    # 4) 주문번호 생성
    def _make_id(r):
        code = r["customer_code_raw"]
        if pd.isna(code):
            return None
        y = r["order_date"].year
        return f"{y}-{int(code):04d}-{int(r['order_seq']):02d}"

    df["order_id"] = df.apply(_make_id, axis=1)

    return df



def build_order_table(flat_with_id: pd.DataFrame) -> pd.DataFrame:
    """
    주문 테이블(주문별 1행)을 생성
    """

    def combine_items(row):
        items = []
        for col in ["item_info_1", "item_info_2", "item_info_3"]:
            v = row.get(col)
            if pd.notna(v):
                items.append(str(v))
        return ", ".join(items) if items else None

    df = flat_with_id.copy()
    df["items"] = df.apply(combine_items, axis=1)

    cols = [
        "order_id",
        "order_date",
        "customer_name_raw",
        "customer_code_raw",
        "items",
        "weekday",
        "month",
        "day",
    ]
    order_df = df[cols].drop_duplicates(subset=["order_id"]).reset_index(drop=True)
    return order_df


def transform_delivery_to_orders(delivery_raw: pd.DataFrame, year: int = TARGET_YEAR):
    """
    전체 파이프라인:
      - 캘린더 펼치기 → 주문번호 생성 → 주문 테이블 저장
    """
    flat = flatten_delivery_calendar(delivery_raw, year)
    print("[DEBUG] delivery_flat columns:", flat.columns)
    flat_with_id = generate_order_ids(flat)
    orders = build_order_table(flat_with_id)

    # 저장
    flat.to_excel(DATA_CLEAN_DIR / f"delivery_flat_{year}.xlsx", index=False)
    flat_with_id.to_excel(DATA_CLEAN_DIR / f"delivery_flat_with_id_{year}.xlsx", index=False)
    orders.to_excel(DATA_CLEAN_DIR / f"orders_{year}.xlsx", index=False)

    return flat_with_id, orders
