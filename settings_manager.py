# settings_manager.py
import os
import json
import re
from typing import Dict, Any, Tuple, Optional

SETTINGS_DIR = "data_settings"
SETTINGS_FILE = os.path.join(SETTINGS_DIR, "shop_settings.json")


def ensure_settings_file() -> None:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    if not os.path.exists(SETTINGS_FILE):
        default = {
            "단위설정": {
                "기본단위": "inch",          # inch / cm
                "저장단위": "inch"           # inch / cm (저장 포맷)
            },
            "약속표기": {
                # 직원들끼리 합의한 입력 표기 -> 숫자 표준값(기본단위 기준)
                # 예: "17 1/4"를 그대로 입력하면 17.25로 저장되도록
                "치수표기_치환": {
                    "17 1/4": "17.25",
                    "17 2/4": "17.5",
                    "17 3/4": "17.75"
                },
                # 자주 쓰는 기호/표기 정규화
                # 예: 17¼, 17-1/4, 17 ¼, 17+1/4 등 대응
                "문자정규화": {
                    "¼": " 1/4",
                    "½": " 1/2",
                    "¾": " 3/4"
                }
            }
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, ensure_ascii=False, indent=2)


def load_settings() -> Dict[str, Any]:
    ensure_settings_file()
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_settings(settings: Dict[str, Any]) -> None:
    os.makedirs(SETTINGS_DIR, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def _normalize_text(raw: str, char_map: Dict[str, str]) -> str:
    s = raw.strip()
    for k, v in (char_map or {}).items():
        s = s.replace(k, v)
    # 다양한 구분자 정리
    s = s.replace("-", " ")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def _parse_fraction_expr(s: str) -> Optional[float]:
    """
    지원:
    - "17 1/4"  -> 17.25
    - "1/4"     -> 0.25
    - "17.25"   -> 17.25
    - "17"      -> 17.0
    - "17 + 1/4" -> 17.25
    - "17 2/4" -> 17.5
    """
    ss = s.strip()
    ss = ss.replace("+", " ")
    ss = re.sub(r"\s+", " ", ss)

    # 숫자만
    if re.fullmatch(r"\d+(\.\d+)?", ss):
        return float(ss)

    # 분수만
    if re.fullmatch(r"\d+/\d+", ss):
        a, b = ss.split("/")
        b = float(b)
        if b == 0:
            return None
        return float(a) / b

    # "정수 분수"
    m = re.fullmatch(r"(\d+)\s+(\d+/\d+)", ss)
    if m:
        whole = float(m.group(1))
        frac = m.group(2)
        a, b = frac.split("/")
        b = float(b)
        if b == 0:
            return None
        return whole + (float(a) / b)

    return None


def convert_measure_input(raw_value: Any, settings: Dict[str, Any]) -> Tuple[Optional[float], str]:
    """
    raw_value: 사용자가 입력한 값(문자/숫자)
    반환: (표준숫자 or None, 정규화된 원문)
    """
    if raw_value is None:
        return None, ""

    if isinstance(raw_value, (int, float)):
        return float(raw_value), str(raw_value)

    raw = str(raw_value).strip()
    if raw == "":
        return None, ""

    char_map = settings.get("약속표기", {}).get("문자정규화", {})
    repl_map = settings.get("약속표기", {}).get("치수표기_치환", {})

    normalized = _normalize_text(raw, char_map)

    # 1) 약속표기 치환이 있으면 우선 적용
    if normalized in repl_map:
        try:
            return float(repl_map[normalized]), normalized
        except:
            pass

    # 2) 분수 표현 파싱
    parsed = _parse_fraction_expr(normalized)
    if parsed is not None:
        return float(parsed), normalized

    # 3) 숫자 추출(마지막 안전망)
    m = re.search(r"(\d+(\.\d+)?)", normalized)
    if m:
        return float(m.group(1)), normalized

    return None, normalized


def apply_unit(value: Optional[float], from_unit: str, to_unit: str) -> Optional[float]:
    if value is None:
        return None
    if from_unit == to_unit:
        return value
    # inch <-> cm
    if from_unit == "inch" and to_unit == "cm":
        return value * 2.54
    if from_unit == "cm" and to_unit == "inch":
        return value / 2.54
    return value
