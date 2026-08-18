from pydantic import BaseModel, EmailStr

# Schema for registering a new user
class UserCreate(BaseModel):
    email: EmailStr  # Ensures the input is a valid email format
    password: str    # Plain text password from the user

# Schema for returning user data (excluding sensitive password)
class UserResponse(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True  # Allows Pydantic to read data from ORM models
