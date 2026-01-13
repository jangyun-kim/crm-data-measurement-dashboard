# scripts/run_all.py
import traceback
from datetime import datetime

from config import LOG_DIR, TARGET_YEAR
from load_data import load_all
from transform_orders import transform_delivery_to_orders
from transform_stock import transform_stock_table
from analysis_production import analyze_production
from analysis_stock import analyze_stock
from analysis_crm import analyze_crm


def main():
    start_time = datetime.now()
    print(f"=== 양복점 데이터 자동화 시작: {start_time} ===")

    try:
        # 1) 데이터 로드
        customers, delivery_raw, stock_raw = load_all()
        print("[run_all] 원본 데이터 로드 완료")

        # 2) 납품달력 → 주문/제작 데이터 변환
        delivery_flat_with_id, orders = transform_delivery_to_orders(
            delivery_raw, year=TARGET_YEAR
        )
        print("[run_all] 납품달력 정규화 및 주문 테이블 생성 완료")

        # 3) 입출고달력 → 재고 이동 데이터 변환
        stock_mov = transform_stock_table()
        analyze_stock(stock_mov)
        print("[run_all] 입출고달력 정규화 및 재고 이동 테이블 생성 완료")

        # 4) 분석: 생산/공정
        analyze_production(orders, year=TARGET_YEAR)

        # 5) 분석: 재고
        analyze_stock(stock_mov)

        # 6) 분석: CRM
        analyze_crm(customers, orders, year=TARGET_YEAR)

        end_time = datetime.now()
        print(f"=== 자동화 완료: {end_time}, 소요 시간: {end_time - start_time} ===")

    except Exception as e:
        print("[run_all] 오류 발생:", e)
        traceback_str = traceback.format_exc()
        print(traceback_str)

        # 로그 파일 저장
        log_path = LOG_DIR / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(traceback_str)
        print(f"[run_all] 에러 로그 저장: {log_path}")


if __name__ == "__main__":
    main()
