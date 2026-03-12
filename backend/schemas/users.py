from pydantic import BaseModel,EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    model_config = {"from_attributes": True}

class login(BaseModel):
    email: EmailStr
    password: str
# Alias used as API response schema
UserResponse = User