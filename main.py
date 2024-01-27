import enum
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional

import databases
import jwt
import sqlalchemy
from dotenv import load_dotenv
from email_validator import EmailNotValidError
from email_validator import validate_email as validate_e
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel, field_validator
from starlette.requests import Request

load_dotenv()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/clothes"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()


class UserRole(enum.Enum):
    super_admin = "super admin"
    admin = "admin"
    user = "user"


users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("email", sqlalchemy.String(120), unique=True),
    sqlalchemy.Column("password", sqlalchemy.String(255)),
    sqlalchemy.Column("full_name", sqlalchemy.String(200)),
    sqlalchemy.Column("phone", sqlalchemy.String(13)),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "last_modified_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "role",
        sqlalchemy.Enum(UserRole),
        nullable=False,
        server_default=UserRole.user.name,
    ),
)


class ColorEnum(enum.Enum):
    pink = "pink"
    black = "black"
    white = "white"
    yellow = "yellow"


class SizeEnum(enum.Enum):
    xs = "xs"
    s = "s"
    m = "m"
    l = "l"
    xl = "xl"
    xxl = "xxl"


clothes = sqlalchemy.Table(
    "clothes",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("name", sqlalchemy.String(120)),
    sqlalchemy.Column("color", sqlalchemy.Enum(ColorEnum), nullable=False),
    sqlalchemy.Column("size", sqlalchemy.Enum(SizeEnum), nullable=False),
    sqlalchemy.Column("photo_url", sqlalchemy.String(255)),
    sqlalchemy.Column(
        "created_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
    ),
    sqlalchemy.Column(
        "last_modified_at",
        sqlalchemy.DateTime,
        nullable=False,
        server_default=sqlalchemy.func.now(),
        onupdate=sqlalchemy.func.now(),
    ),
)


class BaseUser(BaseModel):
    email: str
    full_name: Optional[str]

    @field_validator("email")
    def validate_email(cls, value):
        try:
            validate_e(value)
            return value
        except EmailNotValidError:
            raise ValueError("Email is not valid")

    @field_validator("full_name")
    def validate_full_name(cls, value):
        try:
            first_name, last_name = value.split()
            return value
        except Exception:
            raise ValueError("You must provide at least two names")


class UserSignIn(BaseUser):
    password: str


class UserSignOut(BaseUser):
    phone: Optional[str]
    created_at: datetime
    last_modified_at: datetime


@asynccontextmanager
async def lifespan(app: FastAPI):
    await database.connect()
    yield
    await database.disconnect()


app = FastAPI(lifespan=lifespan)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CustomHTTPBearer(HTTPBearer):
    async def __call__(
        self, request: Request
    ) -> Optional[HTTPAuthorizationCredentials]:
        res = await super().__call__(request)
        try:
            payload = jwt.decode(
                res.credentials, os.getenv("JWT_SECRET"), algorithms=["HS256"]
            )
            user = await database.fetch_one(
                users.select().where(users.c.id == payload["sub"])
            )
            request.state.user = user
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(401, "Token is expired")
        except jwt.InvalidTokenError:
            raise HTTPException(401, "Invalid token")


outh2_scheme = CustomHTTPBearer()


def is_admin(request: Request):
    user = request.state.user
    if not user or user["role"] not in (UserRole.admin, UserRole.super_admin):
        raise HTTPException(403, "You do not have permissions for this resource")


def create_access_token(user):
    try:
        payload = {"sub": user["id"], "exp": datetime.utcnow() + timedelta(minutes=120)}
        return jwt.encode(payload, os.getenv("JWT_SECRET"), algorithm="HS256")
    except Exception as ex:
        return ex


@app.get("/clothes/", dependencies=[Depends(outh2_scheme)])
async def get_all_clothes(request: Request):
    user = request.state.user
    return await database.fetch_all(clothes.select())


class ClothesBase(BaseModel):
    name: str
    color: ColorEnum
    size: SizeEnum


class ClothesIn(ClothesBase):
    pass


class ClothesOut(ClothesBase):
    id: int
    created_at: datetime
    last_modified_at: datetime


@app.post(
    "/clothes/",
    response_model=ClothesOut,
    dependencies=[Depends(outh2_scheme), Depends(is_admin)],
    status_code=201,
)
async def create_clothes(clothes_data: ClothesIn):
    id_ = await database.execute(clothes.insert().values(**clothes_data.model_dump()))
    return await database.fetch_one(clothes.select().where(clothes.c.id == id_))


@app.post("/register/", status_code=201)
async def create_user(user: UserSignIn):
    user.password = pwd_context.hash(user.password)
    query = users.insert().values(**user.model_dump())
    id_ = await database.execute(query)
    created_user = await database.fetch_one(users.select().where(users.c.id == id_))
    token = create_access_token(created_user)
    return {"token": token}
