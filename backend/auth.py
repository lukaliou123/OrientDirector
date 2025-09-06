"""
用户认证相关API
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
import hashlib
import secrets
import json
import os
from pathlib import Path

router = APIRouter()
security = HTTPBearer()

# JWT配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# 用户数据存储文件
USERS_FILE = Path("data/users.json")

# 确保数据目录存在
USERS_FILE.parent.mkdir(exist_ok=True)

# 数据模型
class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    user_id: str

class User(BaseModel):
    user_id: str
    username: str
    email: str
    created_at: str
    preferences: Optional[Dict[str, Any]] = None

# 工具函数
def hash_password(password: str) -> str:
    """哈希密码"""
    salt = secrets.token_hex(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return f"{salt}:{pwd_hash.hex()}"

def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, pwd_hash = hashed.split(':')
        pwd_hash_bytes = bytes.fromhex(pwd_hash)
        new_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
        return pwd_hash_bytes == new_hash
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """创建访问令牌"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def load_users() -> Dict[str, Dict]:
    """加载用户数据"""
    if USERS_FILE.exists():
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_users(users: Dict[str, Dict]):
    """保存用户数据"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def get_user_by_email(email: str) -> Optional[Dict]:
    """根据邮箱获取用户"""
    users = load_users()
    for user_id, user_data in users.items():
        if user_data.get('email') == email:
            return user_data
    return None

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """用户登录"""
    user_data = get_user_by_email(user_credentials.email)
    
    if not user_data or not verify_password(user_credentials.password, user_data['password']):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data['user_id'], "email": user_data['email']},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "user_id": user_data['user_id']
    }

@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserRegister):
    """用户注册"""
    # 验证密码确认
    if user_data.password != user_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="两次输入的密码不一致"
        )
    
    # 验证密码长度
    if len(user_data.password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码长度至少为6位"
        )
    
    # 检查用户是否已存在
    if get_user_by_email(user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该邮箱已注册"
        )
    
    # 创建新用户
    users = load_users()
    user_id = f"user_{secrets.token_hex(8)}"
    
    new_user = {
        "user_id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "created_at": datetime.now().isoformat(),
        "preferences": {}
    }
    
    users[user_id] = new_user
    save_users(users)
    
    return {
        "message": "注册成功",
        "user_id": user_id,
        "username": user_data.username
    }

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    users = load_users()
    user_data = users.get(user_id)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 移除密码字段
    user_data.pop('password', None)
    return User(**user_data)

@router.post("/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}

@router.put("/profile", response_model=User)
async def update_profile(
    preferences: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """更新用户偏好设置"""
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    users = load_users()
    if user_id not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    # 更新用户偏好
    users[user_id]['preferences'] = preferences
    save_users(users)
    
    # 返回更新后的用户信息
    user_data = users[user_id].copy()
    user_data.pop('password', None)
    return User(**user_data)
