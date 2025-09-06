"""
用户认证相关API - 集成Supabase
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import jwt
import os
import logging
from supabase import create_client, Client
from gotrue.errors import AuthApiError

router = APIRouter()
security = HTTPBearer()

# 配置日志
logger = logging.getLogger(__name__)

# Supabase配置
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    logger.warning("Supabase配置缺失，使用本地认证模式")
    supabase: Optional[Client] = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        logger.info("✅ Supabase客户端初始化成功")
    except Exception as e:
        logger.error(f"❌ Supabase客户端初始化失败: {e}")
        supabase = None

# JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24小时

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
    user: Optional[Dict[str, Any]] = None

class User(BaseModel):
    user_id: str
    username: Optional[str] = None
    email: str
    created_at: str
    preferences: Optional[Dict[str, Any]] = None
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None

# 工具函数
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

def verify_supabase_token(token: str) -> Optional[Dict]:
    """验证Supabase JWT令牌"""
    if not supabase:
        return None
    
    try:
        # 使用Supabase验证JWT令牌
        user = supabase.auth.get_user(token)
        if user and user.user:
            return {
                "user_id": user.user.id,
                "email": user.user.email,
                "created_at": user.user.created_at
            }
    except Exception as e:
        logger.error(f"Supabase令牌验证失败: {e}")
    
    return None

async def get_or_create_user_profile(user_id: str, email: str, username: Optional[str] = None) -> Dict:
    """获取或创建用户配置文件"""
    if not supabase:
        return {
            "user_id": user_id,
            "email": email,
            "username": username or email.split('@')[0],
            "created_at": datetime.now().isoformat(),
            "preferences": {}
        }
    
    try:
        # 查询用户配置文件
        result = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if result.data:
            user_data = result.data[0]
            return {
                "user_id": user_data['id'],
                "email": user_data['email'],
                "username": user_data.get('display_name') or username or email.split('@')[0],
                "created_at": user_data['created_at'],
                "preferences": user_data.get('preferences', {}),
                "display_name": user_data.get('display_name'),
                "avatar_url": user_data.get('avatar_url')
            }
        else:
            # 创建新的用户配置文件
            new_user = {
                "id": user_id,
                "email": email,
                "display_name": username or email.split('@')[0],
                "preferences": {},
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            result = supabase.table('users').insert(new_user).execute()
            if result.data:
                user_data = result.data[0]
                return {
                    "user_id": user_data['id'],
                    "email": user_data['email'],
                    "username": user_data.get('display_name'),
                    "created_at": user_data['created_at'],
                    "preferences": user_data.get('preferences', {}),
                    "display_name": user_data.get('display_name'),
                    "avatar_url": user_data.get('avatar_url')
                }
    except Exception as e:
        logger.error(f"用户配置文件操作失败: {e}")
    
    # 降级到基本用户信息
    return {
        "user_id": user_id,
        "email": email,
        "username": username or email.split('@')[0],
        "created_at": datetime.now().isoformat(),
        "preferences": {}
    }

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """用户登录 - 使用Supabase认证"""
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务不可用"
        )
    
    try:
        logger.info(f"🔐 尝试登录用户: {user_credentials.email}")
        
        # 使用Supabase进行认证
        response = supabase.auth.sign_in_with_password({
            "email": user_credentials.email,
            "password": user_credentials.password
        })
        
        if not response.user or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="邮箱或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user = response.user
        session = response.session
        
        logger.info(f"✅ 用户登录成功: {user.email} (ID: {user.id})")
        
        # 获取或创建用户配置文件
        user_profile = await get_or_create_user_profile(
            user.id, 
            user.email,
            user.user_metadata.get('username') if user.user_metadata else None
        )
        
        # 创建自定义JWT令牌（可选，也可以直接使用Supabase的access_token）
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id, "email": user.email},
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": session.access_token,  # 使用Supabase的access_token
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user_id": user.id,
            "user": user_profile
        }
        
    except AuthApiError as e:
        logger.error(f"❌ Supabase认证错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"❌ 登录过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="登录服务暂时不可用"
        )

@router.post("/register", response_model=Dict[str, Any])
async def register(user_data: UserRegister):
    """用户注册 - 使用Supabase认证"""
    if not supabase:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="认证服务不可用"
        )
    
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
    
    try:
        logger.info(f"📝 尝试注册用户: {user_data.email}")
        
        # 使用Supabase进行注册
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "username": user_data.username,
                    "display_name": user_data.username
                }
            }
        })
        
        if not response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="注册失败，请检查邮箱格式或稍后重试"
            )
        
        user = response.user
        logger.info(f"✅ 用户注册成功: {user.email} (ID: {user.id})")
        
        # 创建用户配置文件
        user_profile = await get_or_create_user_profile(
            user.id, 
            user.email, 
            user_data.username
        )
        
        return {
            "message": "注册成功！请检查邮箱验证链接",
            "user_id": user.id,
            "username": user_data.username,
            "email": user.email,
            "email_confirmed": user.email_confirmed_at is not None
        }
        
    except AuthApiError as e:
        logger.error(f"❌ Supabase注册错误: {e}")
        if "already registered" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已注册"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="注册失败，请检查输入信息"
        )
    except Exception as e:
        logger.error(f"❌ 注册过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册服务暂时不可用"
        )

@router.get("/me", response_model=User)
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """获取当前用户信息"""
    token = credentials.credentials
    
    # 首先尝试验证Supabase令牌
    if supabase:
        supabase_user = verify_supabase_token(token)
        if supabase_user:
            user_profile = await get_or_create_user_profile(
                supabase_user["user_id"],
                supabase_user["email"]
            )
            return User(**user_profile)
    
    # 降级到本地JWT验证
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        email = payload.get("email")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        user_profile = await get_or_create_user_profile(user_id, email)
        return User(**user_profile)
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """用户登出"""
    if supabase:
        try:
            # 使用Supabase登出
            supabase.auth.sign_out()
            logger.info("✅ 用户已登出")
        except Exception as e:
            logger.error(f"登出过程中发生错误: {e}")
    
    return {"message": "登出成功"}

@router.put("/profile", response_model=User)
async def update_profile(
    preferences: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """更新用户偏好设置"""
    token = credentials.credentials
    
    # 验证用户身份
    user_info = None
    if supabase:
        user_info = verify_supabase_token(token)
    
    if not user_info:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_info = {
                "user_id": payload.get("sub"),
                "email": payload.get("email")
            }
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效的认证令牌"
            )
    
    if not user_info or not user_info.get("user_id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌"
        )
    
    # 更新用户偏好
    if supabase:
        try:
            result = supabase.table('users').update({
                "preferences": preferences,
                "updated_at": datetime.now().isoformat()
            }).eq('id', user_info["user_id"]).execute()
            
            if result.data:
                user_data = result.data[0]
                return User(
                    user_id=user_data['id'],
                    email=user_data['email'],
                    username=user_data.get('display_name'),
                    created_at=user_data['created_at'],
                    preferences=user_data.get('preferences', {}),
                    display_name=user_data.get('display_name'),
                    avatar_url=user_data.get('avatar_url')
                )
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
    
    # 降级到基本响应
    user_profile = await get_or_create_user_profile(
        user_info["user_id"],
        user_info["email"]
    )
    user_profile["preferences"] = preferences
    return User(**user_profile)

@router.get("/health")
async def auth_health():
    """认证服务健康检查"""
    return {
        "status": "healthy",
        "supabase_available": supabase is not None,
        "timestamp": datetime.now().isoformat()
    }