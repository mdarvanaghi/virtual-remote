import json
from pathlib import Path

from fastapi import Cookie, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from itsdangerous import BadSignature, URLSafeSerializer
from pydantic import BaseModel

from .backends import get_backend
from .config import PIN, SECRET_KEY

app = FastAPI()
backend = get_backend()
signer = URLSafeSerializer(SECRET_KEY, salt="session")

STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def make_session_token() -> str:
    return signer.dumps({"auth": True})


def is_authenticated(session: str | None) -> bool:
    if not session:
        return False
    try:
        signer.loads(session)
        return True
    except BadSignature:
        return False


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def index(session: str | None = Cookie(default=None)):
    if is_authenticated(session):
        return FileResponse(STATIC_DIR / "remote.html")
    return FileResponse(STATIC_DIR / "login.html")


class LoginRequest(BaseModel):
    pin: str


@app.post("/login")
async def login(request_body: LoginRequest):
    if request_body.pin == PIN:
        token = make_session_token()
        response = JSONResponse({"ok": True})
        response.set_cookie("session", token, httponly=True, samesite="lax")
        return response
    return JSONResponse({"ok": False, "error": "Wrong PIN"}, status_code=401)


@app.post("/logout")
def logout():
    response = JSONResponse({"ok": True})
    response.delete_cookie("session")
    return response


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket, session: str | None = Cookie(default=None)):
    await ws.accept()
    if not is_authenticated(session):
        await ws.close(code=4401)
        return
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            action = msg.get("action")

            if action == "press":
                backend.press_key(msg["button"])

            elif action == "type":
                text = msg.get("text", "")
                if text:
                    backend.type_text(text)

            elif action == "mouse_move":
                backend.move_mouse(int(msg.get("dx", 0)), int(msg.get("dy", 0)))

            elif action == "mouse_click":
                backend.click(msg.get("button", "left"))

            elif action == "scroll":
                backend.scroll(int(msg.get("dx", 0)), int(msg.get("dy", 0)))

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket error: {e!r}")
        await ws.close(code=1011)
