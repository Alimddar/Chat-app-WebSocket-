from fastapi import FastAPI,Depends,HTTPException,WebSocket
from fastapi import (
    Cookie,
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketException,

    status,
)
from typing import List
from sqlmodel import SQLModel, Session, create_engine, select
from fastapi.middleware.cors import CORSMiddleware
from Chat.models import User,Group,GroupMember,Friendship,DirectMessage,Message
from sqlalchemy.orm import aliased
from fastapi.responses import HTMLResponse
import threading
import bcrypt


db_url = 'app.db'
DATABASE_URL = f"sqlite:///{db_url}"

engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)

thread_local = threading.local()

html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Chat</title>
    </head>
    <body>
        <h1>WebSocket Chat</h1>
        <form action="" onsubmit="sendMessage(event)">
            <input type="text" id="messageText" autocomplete="off"/>
            <button>Send</button>
        </form>
        <ul id='messages'>
        </ul>
        <script>
            var ws = new WebSocket("ws://192.168.0.103:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages')
                var message = document.createElement('li')
                var content = document.createTextNode(event.data)
                message.appendChild(content)
                messages.appendChild(message)
            };
            function sendMessage(event) {
                var input = document.getElementById("messageText")
                ws.send(input.value)
                input.value = ''
                event.preventDefault()
            }
        </script>
    </body>
</html>
"""


def get_db():
    if not hasattr(thread_local, "session"):
        thread_local.session = Session(engine)
    return thread_local.session

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "http://192.168.0.103:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: str):
        for connection in self.active_connections:
            await connection.send_text(data)

manager = ConnectionManager()


def hash_password(password: str) -> str:
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    return hashed_pw.decode('utf-8')

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(f"Message text was: {data}")  
    except WebSocketException:
        pass
    finally:
        manager.disconnect(websocket)


@app.post("/create_user/",tags=['user'])
def create_user_endpoint(username: str, email: str, password: str, session: Session = Depends(get_db)):
    user = User(username=username, email=email, password=hash_password(password))
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"user created"}

@app.get("/get_user/{user_id}",tags=['user'])
def get_user(user_id: int, session: Session = Depends(get_db)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.post("/create_group/", tags=['group'])
def create_group_endpoint(name: str, description: str, session: Session = Depends(get_db)):
    group = Group(name=name, description=description)
    session.add(group)
    session.commit()
    session.refresh(group)
    return {"group created"}

@app.get("/get_group/", tags=['group'])
def get_group(group_id: int, session: Session = Depends(get_db)):
    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="User not found")
    return group

@app.post("/add_user_to_group/", tags=['group'])
def add_user_to_group(user_id: int, group_id: int, session: Session = Depends(get_db)):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    group = session.get(Group, group_id)
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    existing_member = session.exec(select(GroupMember).where(GroupMember.user_id == user_id, GroupMember.group_id == group_id)).first()
    if existing_member:
        raise HTTPException(status_code=400, detail="User is already a member of the group")

    group_member = GroupMember(user_id=user_id, group_id=group_id)
    session.add(group_member)
    session.commit()
    session.refresh(group_member)

    return {"message": "User added to group successfully"}

@app.get("/group/{group_id}/users/")
def get_users_in_group(group_id: int, session: Session = Depends(get_db)):
    user = (
        session
        .exec(
            select(User.username)
            .join(GroupMember, GroupMember.user_id == User.id)
            .where(GroupMember.group_id == group_id)
        )
        .all()
    )

    return user

@app.post("/create_friendship/")
def create_friendship(user1_id: int, user2_id: int, session: Session = Depends(get_db)):
    user1 = session.get(User, user1_id)
    user2 = session.get(User, user2_id)

    if not user1 or not user2:
        raise HTTPException(status_code=404, detail="One or both users not found")

    existing_friendship = (
        session
        .exec(
            select(Friendship)
            .where(
                (Friendship.user1_id == user1_id) & (Friendship.user2_id == user2_id) |
                (Friendship.user1_id == user2_id) & (Friendship.user2_id == user1_id)
            )
        )
        .first()
    )

    if existing_friendship:
        raise HTTPException(status_code=400, detail="Friendship already exists between these users")

    friendship = Friendship(user1_id=user1_id, user2_id=user2_id)
    session.add(friendship)
    session.commit()
    session.refresh(friendship)
    
    return {"message": "Friend created"}

@app.post("/send_message/")
def send_message(sender_id: int, receiver_id: int, content: str, session: Session = Depends(get_db)):
    friendship = (
        session
        .exec(
            select(Friendship)
            .where(
                (Friendship.user1_id == sender_id) & (Friendship.user2_id == receiver_id) |
                (Friendship.user1_id == receiver_id) & (Friendship.user2_id == sender_id)
            )
        )
        .first()
    )

    if not friendship:
        raise HTTPException(status_code=403, detail="Users are not friends, cannot send message.")

    message = DirectMessage(sender_id=sender_id, receiver_id=receiver_id, content=content)
    session.add(message)
    session.commit()
    session.refresh(message)
    return {"message": "Message sent", "message_id": message.id}

@app.get("/conversation/{user1_id}/{user2_id}/")
def get_conversation(user1_id: int, user2_id: int, session: Session = Depends(get_db)):
    SenderUser = aliased(User)
    ReceiverUser = aliased(User)
    
    messages_query = (
        select(DirectMessage, SenderUser.username.label("sender_username"), ReceiverUser.username.label("receiver_username"))
        .join(SenderUser, SenderUser.id == DirectMessage.sender_id)
        .join(ReceiverUser, ReceiverUser.id == DirectMessage.receiver_id)
        .where(
            (DirectMessage.sender_id == user1_id) & (DirectMessage.receiver_id == user2_id) |
            (DirectMessage.sender_id == user2_id) & (DirectMessage.receiver_id == user1_id)
        )
        .order_by(DirectMessage.timestamp)
    )

    results = session.exec(messages_query).all()
    
    messages = [{"content": message.content, "sender": sender, "receiver": receiver, "timestamp": message.timestamp} for message, sender, receiver in results]

    return {"conversation": messages}

@app.post("/group/{group_id}/send/")
def send_group_message(group_id: int, sender_id: int, content: str, session: Session = Depends(get_db)):
    message = Message(group_id=group_id, sender_id=sender_id, content=content)
    session.add(message)
    session.commit()
    session.refresh(message)
    return {"message": "Message sent", "sent_message": message}

@app.get("/group/{group_id}/messages/")
def get_group_messages(group_id: int, session: Session = Depends(get_db)):
    messages = session.exec(select(Message).where(Message.group_id == group_id).order_by(Message.timestamp)).all()
    return {"group_messages": messages}

