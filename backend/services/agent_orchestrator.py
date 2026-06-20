import asyncio
import json
import base64
import sys
import traceback
from pathlib import Path

from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect 
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import uvicorn

app = FastAPI()

current_dir = Path(__file__).parent
mcp_server_path = current_dir / "mcp_server.py"

if not mcp_server_path.exists():
    mcp_server_path = current_dir.parent / "mcp_server.py"

if not mcp_server_path.exists():
    raise RuntimeError(f"Cannot find mcp_server.py near {current_dir}")

print(f"MCP server path: {mcp_server_path}", file=sys.stderr)

server_params = StdioServerParameters(
    command=sys.executable,
    args=[str(mcp_server_path)],
)

@app.websocket("/ws/agent-therapy")
async def agent_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Agent connected")

    audio_buffer = bytearray()
    target_text = "hello"

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("text"):
                data = json.loads(message["text"])

                if data.get("action") == "set_target":
                    target_text = data.get("target", "hello")
                    await websocket.send_text(f"Target set: {target_text}")

                elif data.get("action") == "stop":
                    audio_b64 = base64.b64encode(bytes(audio_buffer)).decode()

                    await websocket.send_text("Processing started")

                    try:
                        async with stdio_client(server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                await websocket.send_text("MCP connected")
                                await session.initialize()

                                await websocket.send_text("Transcribing")
                                transcript = await session.call_tool(
                                    "transcribe_audio",
                                    {"audio_bytes_base64": audio_b64},
                                )

                                spoken_text = transcript.content[0].text
                                await websocket.send_text(f"Transcript: {spoken_text}")

                                await websocket.send_text("Analyzing")
                                result = await session.call_tool(
                                    "evaluate_english_phonetics",
                                    {"target_word": target_text, "spoken_text": spoken_text},
                                )

                                raw = result.content[0].text
                                data = json.loads(raw)

                                if "error" in data:
                                    raise RuntimeError(data["error"])

                                await session.call_tool(
                                    "log_session_for_finetuning",
                                    {
                                        "audio_bytes_base64": audio_b64,
                                        "target_text": target_text,
                                        "spoken_text": spoken_text,
                                        "diagnostic_result": json.dumps(data),
                                    },
                                )

                                await websocket.send_json({
                                    "type": "diagnostic",
                                    "target": target_text,
                                    "spoken": spoken_text,
                                    **data,
                                })

                    except Exception as e:
                        traceback.print_exc()
                        try:
                            await websocket.send_text(f"Error: {str(e)}")
                        except Exception:
                            pass 

                    audio_buffer.clear()

            elif message.get("bytes"):
                audio_buffer.extend(message["bytes"])

    except WebSocketDisconnect:
        print("Client disconnected gracefully.")
    except Exception as e:
        print(f"WebSocket Error: {e}")
        try:
            await websocket.send_text(f"Error: {str(e)}")
        except Exception:
            pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)