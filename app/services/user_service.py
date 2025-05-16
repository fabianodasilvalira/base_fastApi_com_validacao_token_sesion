from typing import Optional, Union
from uuid import UUID
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from loguru import logger


class UserService:
    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Retrieves a user by email."""
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """Retrieves a user by ID."""
        logger.debug(f"Attempting to retrieve user by ID: {user_id}")
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalars().first()
        if user:
            logger.info(f"User with ID {user_id} found: {user.email}")
        else:
            logger.warning(f"User with ID {user_id} not found.")
        return user

    @staticmethod
    async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
        """Creates a new user in the system"""
        logger.debug(f"Attempting to create user: {user_in.email}")
        existing_user = await UserService.get_user_by_email(db, email=user_in.email)
        if existing_user:
            logger.warning(f"User creation failed: Email {user_in.email} already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The user with this email already exists in the system.",
            )

        hashed_password = get_password_hash(user_in.password)
        db_user = User(
            email=user_in.email,
            hashed_password=hashed_password,
            is_active=user_in.is_active if user_in.is_active is not None else True,
            is_superuser=user_in.is_superuser if user_in.is_superuser is not None else False,
            # Adicionando campos que podem estar faltando no modelo User, baseado em UserCreate
            username=user_in.username,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            phone=user_in.phone,
            imagem_url=user_in.imagem_url
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User {user_in.email} created successfully (ID: {db_user.id}).")
        return db_user


user_service = UserService()
