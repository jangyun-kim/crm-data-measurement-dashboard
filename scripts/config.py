# scripts/config.py
from pathlib import Path

# 프로젝트 루트 = scripts 상위 폴더
BASE_DIR = Path(__file__).resolve().parent.parent

# 폴더 경로
DATA_RAW_DIR = BASE_DIR / "data_raw"
DATA_CLEAN_DIR = BASE_DIR / "data_clean"
REPORT_DIR = BASE_DIR / "reports"
LOG_DIR = BASE_DIR / "logs"

# 기본 연도 (필요 시 바꿔서 사용)
TARGET_YEAR = 2025

# 파일 이름 (data_raw 기준)
FILE_CUSTOMER = DATA_RAW_DIR / "회원정보.xlsx"
FILE_PROD_CAL = DATA_RAW_DIR / "3. 납품달력(2025).xlsx"
FILE_STOCK_CAL = DATA_RAW_DIR / "4. 입출고달력(2025).xlsx"

# 디렉토리 없는 경우 생성
for d in [DATA_RAW_DIR, DATA_CLEAN_DIR, REPORT_DIR, LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)
