from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ChatRequest(BaseModel):
    user_message: str
    session_id: str


class ChatResponse(BaseModel):
    response: str
    awaiting_confirmation: bool
    session_id: str


class UserTokenModel(BaseModel):
    user_id: str
    access_token: str
    refresh_token: str
    expires_at: datetime


class UserInfo(BaseModel):
    user_id: str
    email: str
    name: str


class LoginResponse(BaseModel):
    message: str
    redirect_url: str


class CallbackResponse(BaseModel):
    token: str
    redirect_url: str


class ProjectInfo(BaseModel):
    id: str
    name: str
    status: str


class TaskInfo(BaseModel):
    id: str
    title: str
    status: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    priority: Optional[str] = None


class TaskDetailInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str
    priority: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None


class CreateTaskRequest(BaseModel):
    name: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None


class UpdateTaskRequest(BaseModel):
    fields: Dict[str, Any]


class MemberInfo(BaseModel):
    id: str
    name: str
    email: str
    role: str


class TaskUtilisation(BaseModel):
    assignee: str
    task_count: int
    task_list: List[str]


class PendingAction(BaseModel):
    action_type: str  # create_task, update_task, delete_task
    tool_name: str
    parameters: Dict[str, Any]
