"""
오피넷 API에서 전국 평균 유가를 가져와 fuel-prices.json을 업데이트하는 스크립트.

사용법:
  1. 오피넷 API 키를 GitHub Secrets에 OPINET_API_KEY로 등록
  2. GitHub Actions 워크플로우에서 자동 실행

오피넷 API 신청: https://www.opinet.co.kr/user/custapi/custApiInfo.do
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests

OPINET_BASE = "http://www.opinet.co.kr/api"
OUTPUT_FILE = "fuel-prices.json"

# 오피넷 API 유종 코드
# B027: 휘발유, D047: 경유, K015: LPG
FUEL_CODES = {
    "gasoline": "B027",
    "diesel": "D047",
    "lpg": "K015",
}


def fetch_opinet_prices(api_key: str) -> dict:
    """오피넷 API에서 전국 평균 유가를 가져옵니다."""
    url = f"{OPINET_BASE}/avgAllPrice.do"
    params = {
        "out": "json",
        "code": api_key,
    }

    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    # 오피넷 응답 파싱
    oil_list = data.get("RESULT", {}).get("OIL", [])
    prices = {}
    code_to_key = {v: k for k, v in FUEL_CODES.items()}

    for oil in oil_list:
        prod_cd = oil.get("PRODCD", "")
        price = oil.get("PRICE", 0)
        if prod_cd in code_to_key:
            prices[code_to_key[prod_cd]] = round(float(price), 1)

    return prices


def main():
    api_key = os.environ.get("OPINET_API_KEY", "").strip()

    if not api_key:
        print("⚠️  OPINET_API_KEY가 설정되지 않았습니다.")
        print("   GitHub Secrets에 OPINET_API_KEY를 등록하세요.")
        print("   오피넷 API 키 신청: https://www.opinet.co.kr/user/custapi/custApiInfo.do")
        print("   기존 fuel-prices.json을 유지합니다.")
        sys.exit(0)  # 에러가 아니므로 워크플로우는 성공 처리

    try:
        prices = fetch_opinet_prices(api_key)
    except Exception as e:
        print(f"❌ 오피넷 API 호출 실패: {e}")
        print("   기존 fuel-prices.json을 유지합니다.")
        sys.exit(0)

    if not prices.get("gasoline") or not prices.get("diesel"):
        print("❌ 유가 데이터가 비어 있습니다. 기존 파일 유지.")
        sys.exit(0)

    # 한국 시간 기준 날짜
    kst = timezone(timedelta(hours=9))
    today = datetime.now(kst).strftime("%Y-%m-%d")

    result = {
        "updated": today,
        "source": "opinet",
        "prices": prices,
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"✅ 유가 업데이트 완료 ({today})")
    for k, v in prices.items():
        name = {"gasoline": "휘발유", "diesel": "경유", "lpg": "LPG"}.get(k, k)
        print(f"   {name}: {v:,.1f}원/L")


if __name__ == "__main__":
    main()
