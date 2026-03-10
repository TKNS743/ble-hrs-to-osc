# BLE Heart Rate → OSC Bridge

BLE対応心拍計から心拍数を取得し、OSC経由で送信するPythonコードです。  
本リポジトリは，心拍OSC連携の一例として公開しています。  
改変・再利用・発展を歓迎します。

---

> **Fork Information**  
> このリポジトリは元プロジェクトを Fork し、機能追加・改変を行ったバージョンです。  
> Original repository: （[takuu-o/ble-hrs-to-osc: BLE対応Heart rate serviceをVRChat向けOSCに送信するサンプルコード](https://github.com/takuu-o/ble-hrs-to-osc/)）

## Changes in this Fork

- Pulsoidから心拍数を取得し、OSC連携を実施するためのPythonコード`pulsoid_to_osc.py`を追加

  Pulsoid のリアルタイム WebSocket API から心拍を取得し、同じ OSC 形式で出力します。

### Pulsoid 側の準備

1. Pulsoid のアカウント作成
2. Pulsoid のドキュメントに従って **アクセストークン** を取得

### トークンの設定方法（JSON を触らなくてもOK）

`pulsoid_to_osc.py` では、次の順番でトークンを探します。

1. **環境変数 `PULSOID_ACCESS_TOKEN`**
2. **トークンファイル `pulsoid_token.txt`**
3. `config.json` の `pulsoid.access_token`

#### 1. `code\pulsoid_token.txt` を使う（おすすめ）

1. `code\pulsoid_token.txt.example` をコピー
2. `code\pulsoid_token.txt` にリネーム
3. 1行目に Pulsoid のアクセストークンだけを書き込む

#### 2. `config.json` に書く

```json
"pulsoid": {
  "access_token": "ここにPulsoidのトークン",
  "response_mode": "json"
}
```

#### 3. 環境変数で設定（Windows）

```cmd
set PULSOID_ACCESS_TOKEN=ここにトークン  REM 一時的にこのウィンドウで有効
```

JSON を編集しなくて良いので、慣れていない人にも安全です。

### 基本動作
- BLE Heart Rateからの入力をPulsoidへ変更しています。
- 出力形式はhrs_to_osc.pyに準じます。

---

## Overview

- BLE Heart Rate Service (0x180D) に対応
- 心拍数を取得しOSCで送信
- VRChatでのOSC連携を想定
- MIT License

---

## Features

- 心拍数（BPM）をそのまま送信
- ギミック向けの正規化値の計算例を含む
- 設定ファイル（config.json）によるカスタマイズ

---

## Getting Started

### 1. Python環境

Python 3.11 以上で検証しています。

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Rum

```bash
python hrs_to_osc.py
```

## OSC Parameters

デフォルトで以下のOSCパラメータを送信します：

OSC Address                     | Type  | Description
--------------------------------|-------|----------------------------
/avatar/parameters/taklabs/heartbeat_value     | Int   | Heart Rate in BPM
/avatar/parameters/taklabs/heartbeat_waittime  | Float | Normalized value (0.0-1.0)

---

## Configuration

`config.json` で以下を設定できます：

- OSC送信先IP/ポート番号
- OSC送信アドレス
- 再接続設定
- スキャン間隔など

---

## Related Project

本ツールは、以下のVRChat向け心音ギミックのために制作されました：

Booth:  
https://taklabs.booth.pm/items/8001371

※ 本ツールは単体で利用可能です。

---

## License

MIT License

Copyright (c) 2026 takuu-o

---

## Notes

- BLE動作はOS・デバイスに依存します
- 動作確認環境：
  - OS: Windows 11，
  - 心拍計: Coospo HW706

---
