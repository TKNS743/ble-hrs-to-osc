import asyncio
import json
import os
from pathlib import Path

import websockets
from pythonosc import udp_client


# トークンだけ書くファイル名（JSON を触らなくてよい）
PULSOID_TOKEN_FILENAME = "pulsoid_token.txt"

# 設定値
CONFIG = {
    "osc": {
        "server_ip": "127.0.0.1",
        "server_port": 9000,
        "address": "/avatar/parameters/",
    },
    "pulsoid": {
        # Pulsoid WebSocket エンドポイント
        "url": "wss://dev.pulsoid.net/api/v1/data/real_time",
        # access_token は get_pulsoid_token() で取得（環境変数・トークン用ファイル・config.json）
        "access_token": "",
        # "json" か "text"（text_plain_only_heart_rate）
        "response_mode": "json",
        "reconnect_delay": 5,
        "max_retries": 0,  # 0 は無限リトライ
    },
}


def merge_config(default_config: dict, user_config: dict) -> dict:
    result = default_config.copy()
    for key, value in user_config.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = value
    return result


def initialize_config(config_file: str = "config.json") -> dict:
    """
    設定ファイル読み込み
    """
    global CONFIG

    try:
        config_path = Path(config_file)
        if not config_path.exists():
            print(f"{config_file} が見つかりません。")

        with open(config_path, "r", encoding="utf-8") as f:
            user_config = json.load(f)

        # デフォルト値とユーザー設定を深くマージ
        CONFIG = merge_config(CONFIG, user_config)

    except json.JSONDecodeError:
        print(f"{config_file} のJSONフォーマットが不正です。")
    except Exception as e:
        print(f"設定ファイルの読み込みに失敗しました: {e}")

    return CONFIG


def get_pulsoid_token() -> str:
    """
    Pulsoid トークンを取得する。
    優先順位: 環境変数 PULSOID_ACCESS_TOKEN > code/pulsoid_token.txt > config.json
    """
    # 1. 環境変数
    token = os.environ.get("PULSOID_ACCESS_TOKEN", "").strip()
    if token:
        return token

    # 2. トークン用ファイル（1行目だけ。JSON を触らなくてよい）
    # `pulsoid_to_osc.py` と同じフォルダ（code/）に置く
    path = Path(__file__).resolve().parent / PULSOID_TOKEN_FILENAME
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                token = f.readline().strip()
            if token:
                return token
        except OSError:
            pass

    # 3. config.json
    return (CONFIG.get("pulsoid") or {}).get("access_token", "") or ""


def send_osc(osc_client, osc_address: str, send_list):
    """OSC送信"""
    try:
        for data in send_list:
            osc_client.send_message(osc_address + data["address"], data["value"])
            print(f"OSC送信: {data['address']} -> {data['value']}")
    except Exception as e:
        print(f"OSC送信エラー: {e}")


def handle_heart_rate(osc_client, osc_address: str, heart_rate: int):
    """Pulsoid から受け取った心拍数を OSC へ変換して送信"""
    if not heart_rate:
        return

    print(f"心拍数: {heart_rate} BPM")

    # hrs_to_osc.py と同じロジックで正規化値を計算
    HR_CONST = 0.2
    HR_FLEX = 0.2

    try:
        calculated_hr = 1 / (1 / HR_CONST * (60 / heart_rate - HR_FLEX))
    except ZeroDivisionError:
        calculated_hr = 0.0

    normalized_hr = max(0.0, min(1.0, calculated_hr))

    send_osc(
        osc_client,
        osc_address,
        [
            {
                "address": "heartbeat_value",
                "value": int(heart_rate),
            },
            {
                "address": "heartbeat_waittime",
                "value": float(normalized_hr),
            },
        ],
    )


async def pulsoid_loop():
    """Pulsoid WebSocket から心拍数を受信して OSC に流すメインループ"""
    initialize_config()

    osc_client = udp_client.SimpleUDPClient(
        CONFIG["osc"]["server_ip"],
        CONFIG["osc"]["server_port"],
    )
    osc_address = CONFIG["osc"]["address"]

    url = CONFIG["pulsoid"]["url"]
    token = get_pulsoid_token()
    response_mode = CONFIG["pulsoid"]["response_mode"]
    reconnect_delay = CONFIG["pulsoid"]["reconnect_delay"]
    max_retries = CONFIG["pulsoid"]["max_retries"]

    if not token:
        print("Pulsoid のアクセストークンが設定されていません。")
        print("次のいずれかで設定してください（JSON を触らなくてOK）:")
        print(f"  1. 環境変数: PULSOID_ACCESS_TOKEN")
        print(
            f"  2. code\\{PULSOID_TOKEN_FILENAME} を作り、1行目にトークンだけ書く"
        )
        print("  3. config.json の pulsoid.access_token に書く")
        return

    # URL にクエリパラメータでトークンとレスポンスモードを付与
    query_params = f"?access_token={token}"
    if response_mode == "text":
        query_params += "&response_mode=text_plain_only_heart_rate"

    full_url = url + query_params

    print(f"OSC設定: {CONFIG['osc']['server_ip']}:{CONFIG['osc']['server_port']}")
    print(f"OSCアドレス: {osc_address}")
    print(f"Pulsoid WebSocket: {url} (トークン設定済み)")
    print("-" * 40)

    retry_count = 0

    while True:
        try:
            async with websockets.connect(full_url) as ws:
                print("Pulsoid に接続しました。心拍モニタリング開始 (Ctrl+C で停止)")
                print("OSC送信開始")
                retry_count = 0

                async for message in ws:
                    try:
                        if response_mode == "text":
                            # プレーンテキスト (例: "85")
                            heart_rate = int(message.strip())
                        else:
                            # JSON 形式
                            payload = json.loads(message)
                            heart_rate = int(payload["data"]["heart_rate"])

                        handle_heart_rate(osc_client, osc_address, heart_rate)
                    except (ValueError, KeyError, TypeError, json.JSONDecodeError) as e:
                        print(f"受信データの解析エラー: {e}, message={message}")

        except asyncio.CancelledError:
            raise
        except Exception as e:
                print(f"Pulsoid 接続エラー: {e}")
            retry_count += 1

            if max_retries and retry_count > max_retries:
                print("最大リトライ回数に到達しました。終了します。")
                break

            print(f"{reconnect_delay}秒後に再接続を試みます... (試行 {retry_count})")
            await asyncio.sleep(reconnect_delay)


def main():
    try:
        asyncio.run(pulsoid_loop())
    except KeyboardInterrupt:
        print("\nモニタリング停止")


if __name__ == "__main__":
    main()

