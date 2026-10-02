
from fastapi import FastAPI, Query, Path, Body
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any
from __004__langgraph_agent.__004__langgraph_more_agent import call_langgraph_ai, call_xiaohongshu_ai, stream_langgraph_ai
from common.llm import set_session_history

# 创建 FastAPI 应用
app = FastAPI(title="宠知通·宠物知识图谱服务", version="1.0.0")


# 定义请求体模型（通用 dict）
class DataRequest(BaseModel):
    data: Dict[str, Any]


# 定义响应模型（也是 dict）
class DataResponse(BaseModel):
    result: Dict[str, Any]


@app.post("/process", response_model=DataResponse)
def process_data(req: DataRequest):
    """接收一个 dict(JSON)，再返回一个 dict(JSON)"""
    input_dict = req.data
    print(input_dict)

    user_content = input_dict.get("user_content", "")
    session_id = input_dict.get("session_id", "")
    user_id = input_dict.get("user_id", "")
    history = input_dict.get("history") or []
    if "history" in input_dict:
        set_session_history(session_id, history)

    is_has_xhs_intent, reply = call_langgraph_ai(user_id, session_id, user_content)

    return {"result": {"is_has_xhs_intent": is_has_xhs_intent, "reply": reply}}


@app.post("/process/xiaohongshu", response_model=DataResponse)
def process_xiaohongshu(req: DataRequest):
    """显式生成宠物养护类小红书图文内容。"""
    input_dict = req.data
    user_content = input_dict.get("user_content", "")
    session_id = input_dict.get("session_id", "")
    user_id = input_dict.get("user_id", "")
    history = input_dict.get("history") or []
    if "history" in input_dict:
        set_session_history(session_id, history)

    result = call_xiaohongshu_ai(user_id, session_id, user_content)
    return {"result": result}


@app.post("/process/stream")
def process_data_stream(req: DataRequest):
    """接收一个 dict(JSON)，以纯文本流式返回最终答案。"""
    input_dict = req.data
    print(input_dict)

    user_content = input_dict.get("user_content", "")
    session_id = input_dict.get("session_id", "")
    user_id = input_dict.get("user_id", "")
    history = input_dict.get("history") or []
    if "history" in input_dict:
        set_session_history(session_id, history)

    def generate():
        for token in stream_langgraph_ai(user_id, session_id, user_content):
            yield token

    return StreamingResponse(
        generate(),
        media_type="text/plain; charset=utf-8",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
