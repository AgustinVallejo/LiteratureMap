import os
from datetime import datetime, timedelta, timezone
from typing import Dict
import sys
import signal

from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

app = FastAPI()

# In-memory database for demonstration purposes
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "full_name": "John Doe",
        "email": "johndoe@example.com",
        "hashed_password": "$2b$12$ZbALtj2F9YyagrWLDXrT9.SfESLyKbxcFOR27a4Yhzot8zjCCB./a",
        "disabled": False,
    }
}

# Secret key for JWT encoding/decoding
SECRET_KEY = "a_very_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer instance
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None

class UserInDB(User):
    hashed_password: str


class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    full_name: str | None = None
    
    
def verify_password(plain_password, hashed_password):
    print(plain_password,hashed_password)
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: int | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(tz=timezone.utc) + timedelta(expires_delta)
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str|None = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = "None"
    if token_data.username:
        user = get_user(fake_users_db, username=token_data.username)
    else:
        raise credentials_exception
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    acces_token_mins=access_token_expires.total_seconds() // 60
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=int(acces_token_mins)
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    return current_user


@app.get("/", response_class=HTMLResponse)
async def get_form():
    users_html = "<ul>"
    for username, user in fake_users_db.items():
        users_html += f"<li>{username} - {user['full_name']} ({user['email']})</li>"
    users_html += "</ul>"
    form_html = f"""
    <html>
        <head>
            <title>Create User</title>
            <script src="https://accounts.google.com/gsi/client" async defer></script>
        </head>
        <body>
            <h1>Create User</h1>
            <form action="/users/" method="post">
                <label for="username">Username:</label><br>
                <input type="text" id="username" name="username"><br>
                <label for="password">Password:</label><br>
                <input type="password" id="password" name="password"><br>
                <label for="email">Email:</label><br>
                <input type="text" id="email" name="email"><br>
                <label for="full_name">Full Name:</label><br>
                <input type="text" id="full_name" name="full_name"><br><br>
                <input type="submit" value="Submit">
            </form>
            <h2>Current Users</h2>
            {users_html}
            <div id="g_id_onload"
                data-client_id="estevelaguco"
                data-context="signup"
                data-ux_mode="popup"
                data-login_uri="login"
                data-itp_support="true">
            </div>

            <div class="g_id_signin"
                data-type="standard"
                data-shape="rectangular"
                data-theme="outline"
                data-text="signin_with"
                data-size="large"
                data-logo_alignment="left">
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=form_html)

    
@app.post("/users/", response_class=HTMLResponse)
async def create_user(username: str = Form(...), password: str = Form(...), email: str = Form(None), full_name: str = Form(None)):
    if username in fake_users_db:
        return HTMLResponse(content="Username already registered", status_code=400)
    hashed_password = get_password_hash(password)
    user_in_db = UserInDB(username=username, email=email, full_name=full_name, hashed_password=hashed_password, disabled=False)
    fake_users_db[username] = user_in_db.dict()
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__)))

@app.get("/authors", response_class=HTMLResponse)
async def read_embeddings(request: Request):
    return templates.TemplateResponse("authorToAuthor.html", {"request": request})
#http://127.0.0.1:8000/authors Doesn't show the data now

# python -m http.server 8000for embeddings dockerize and port as routes and service maybe

# TODO Generate an iframe for the github.io hosting add comments, score and a navbar left with Carl

def signal_handler(sig, frame):
    print('Shutting down gracefully')
    sys.exit(0)

if __name__ == "__main__":
    import uvicorn
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    uvicorn.run(app, host="0.0.0.0", port=8000)
