from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from loguru import logger

from app.core.session import get_db_session
from app.schemas.user import UserPublic, UserUpdate, UserCreate # UserCreate might be admin-only here
from app.models.user import User
from app.api import deps # For current_user dependency
from app.services import auth_service

# from app.services.user_service import user_service # If you have a dedicated user_service

router = APIRouter()

# Note: User creation is often handled via a /signup endpoint in auth.py for public signups.
# This endpoint could be for admin-created users or a different flow.
@router.post("/", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(deps.get_current_active_superuser) # Example: Only superusers can create users here
):
    """
    Create a new user. (Protected, e.g., for admin use)
    Public user creation is typically via /auth/signup.
    """
    logger.info(f"Admin user {current_user.email} attempting to create user: {user_in.email}")
    # Re-using create_user from auth_service, or you might have a dedicated user_service
    # Check if user already exists (auth_service.create_user already does this)
    # existing_user = await auth_service.get_user_by_email(db, email=user_in.email)
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="The user with this email already exists in the system.",
    #     )
    created_user = await auth_service.create_user(db, user_in=user_in) # auth_service.create_user handles hashing
    logger.info(f"User {created_user.email} created successfully by admin {current_user.email}.")
    return created_user

@router.get("/me", response_model=UserPublic)
async def read_users_me(
    current_user: User = Depends(deps.get_current_active_user)
):
    """
    Get current logged-in user's details.
    """
    logger.info(f"Fetching details for current user: {current_user.email}")
    return current_user

@router.get("/{user_id}", response_model=UserPublic)
async def read_user_by_id(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(deps.get_current_active_superuser) # Example: Only superusers can fetch by ID
):
    """
    Get a specific user by ID. (Protected)
    """
    logger.info(f"Admin user {current_user.email} attempting to fetch user by ID: {user_id}")
    user = await auth_service.get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning(f"User with ID {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    logger.info(f"User {user.email} (ID: {user_id}) fetched successfully by admin {current_user.email}.")
    return user

# Example: Get all users (Protected, for admins)
# @router.get("/", response_model=List[UserPublic])
# async def read_users(
#     db: AsyncSession = Depends(get_db_session),
#     skip: int = 0,
#     limit: int = 100,
#     current_user: User = Depends(deps.get_current_active_superuser)
# ):
#     """
#     Retrieve all users. (Protected, e.g., for admin use)
#     Implement pagination with skip and limit.
#     """
#     logger.info(f"Admin user {current_user.email} attempting to fetch all users (skip={skip}, limit={limit}).")
#     # users = await user_service.get_users(db, skip=skip, limit=limit) # Assuming a user_service.get_users
#     # For now, this is a placeholder as get_users is not in auth_service
#     # You would need to implement this in a user_service or here.
#     # from sqlalchemy.future import select
#     # stmt = select(User).offset(skip).limit(limit)
#     # result = await db.execute(stmt)
#     # users = result.scalars().all()
#     # logger.info(f"Fetched {len(users)} users.")
#     # return users
#     raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Endpoint not fully implemented")

@router.put("/{user_id}", response_model=UserPublic)
async def update_user_by_id(
    user_id: UUID,
    user_in: UserUpdate, # Schema for updating user data
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(deps.get_current_active_superuser) # Or allow user to update self
):
    """
    Update a user's details by ID. (Protected)
    Admins can update any user. Users might be able to update their own info via /me endpoint.
    """
    logger.info(f"User {current_user.email} attempting to update user ID: {user_id}")
    user = await auth_service.get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning(f"Update failed: User with ID {user_id} not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Update user fields from user_in
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data and update_data["password"]:
        # If password is being updated, hash it
        hashed_password = auth_service.get_password_hash(update_data["password"])
        user.hashed_password = hashed_password
        del update_data["password"] # Remove plain password from update_data
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    logger.info(f"User {user.email} (ID: {user_id}) updated successfully by {current_user.email}.")
    return user

# Como adicionar novas rotas de usuário:
# 1. Defina a função da rota (ex: `async def get_user_profile(...)`).
# 2. Adicione o decorador `@router.get(...)`, `@router.put(...)`, etc.
# 3. Implemente a lógica, utilizando `auth_service` (ou um `user_service` dedicado) e a sessão `db`.
# 4. Use as dependências apropriadas de `app.api.deps` para proteger a rota.
# 5. Defina os schemas Pydantic para request body e response model.

