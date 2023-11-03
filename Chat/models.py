from sqlmodel import SQLModel, Field, Relationship,ForeignKey
from typing import List, Optional
from datetime import datetime

class User(SQLModel, table=True):
    id: int = Field(primary_key=True)
    username: str = Field(unique=True)
    email: str = Field(unique=True)
    password: str
    is_admin: bool = Field(default=False)

class Friendship(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user1_id: int = ForeignKey("user.id")
    user2_id: int = ForeignKey("user.id")
    created_at: datetime = Field(default=datetime.now())

class Group(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    description: str
    created_at: datetime = Field(default=datetime.now())

class GroupMember(SQLModel, table=True):
    id: int = Field(primary_key=True)
    user_id: int = ForeignKey("user.id")
    group_id: int = ForeignKey("group.id")

class Message(SQLModel, table=True):
    id: int = Field(primary_key=True)
    content: str
    timestamp: datetime = Field(default=datetime.now())
    sender_id: int = ForeignKey("user.id")
    group_id: int = ForeignKey("group.id", nullable=True)

class DirectMessage(SQLModel, table=True):
    id: int = Field(primary_key=True)
    sender_id: int = ForeignKey("user.id")
    receiver_id: int = ForeignKey("user.id")
    content: str
    timestamp: datetime = Field(default=datetime.now())