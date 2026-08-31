"""认证接口：注册 / 登录 / 当前用户"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models import User, Wallet
from app.schemas import TokenOut, UserLogin, UserOut, UserRegister

router = APIRouter(prefix="/api/auth", tags=["认证"])


@router.post("/register", response_model=TokenOut, summary="注册（自动开通钱包）")
async def register(data: UserRegister, db: AsyncSession = Depends(get_db)):
    # 用户名/邮箱唯一性检查
    exists = await db.scalar(select(User).where(User.username == data.username))
    if exists:
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名已存在")
    if data.email:
        exists = await db.scalar(select(User).where(User.email == data.email))
        if exists:
            raise HTTPException(status.HTTP_409_CONFLICT, "邮箱已被注册")

    user = User(
        username=data.username,
        password_hash=hash_password(data.password),
        nickname=data.nickname,
        email=data.email,
        role="reader",
    )
    db.add(user)
    await db.flush()  # 拿到 user.id

    # 注册即开通钱包（0 书币）
    db.add(Wallet(user_id=user.id, balance=0))
    try:
        await db.commit()
    except IntegrityError:
        # 并发同名/同邮箱注册：唯一约束兜底
        await db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "用户名或邮箱已被注册")
    await db.refresh(user)

    token = create_access_token(user.id, user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenOut, summary="登录")
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await db.scalar(select(User).where(User.username == data.username))
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    if user.status != 1:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "账号已被封禁")

    token = create_access_token(user.id, user.role)
    return TokenOut(access_token=token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut, summary="当前登录用户")
async def me(user: User = Depends(get_current_user)):
    return user
