from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from loguru import logger


class UserService:
    async def get_user_by_email(self, db, email: str) -> Optional[User]:
        """ Retrieves a user by email """
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalars().first()

    async def create_user(self, db, user_in: UserCreate) -> User:
        """ Creates a new user in the system """
        logger.debug(f"Attempting to create user: {user_in.email}")
        existing_user = await self.get_user_by_email(db, email=user_in.email)
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
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        logger.info(f"User {user_in.email} created successfully (ID: {db_user.id}).")
        return db_user


user_service = UserService()
