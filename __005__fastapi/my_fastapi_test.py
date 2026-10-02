
import requests

# FastAPI 服务地址
url = "http://127.0.0.1:8000/process"

# 传入的 JSON（就是 Python dict）
payload = {
    "data": {
        "user_id": "user_01",
        "session_id": "test_session_001",
        "user_content": "狗狗掉毛吃什么好？"
    }
}

# 发送 POST 请求
resp = requests.post(url, json=payload)
print(resp.json()['result'])
