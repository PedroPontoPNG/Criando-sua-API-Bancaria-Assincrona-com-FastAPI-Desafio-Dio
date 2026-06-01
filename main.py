from datetime import datetime, timedelta
from enum import Enum
from typing import List

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, select
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext
from jose import JWTError, jwt

# ==========================================
# CONFIGURAÇÕES DE SEGURANÇA (JWT)
# ==========================================
SECRET_KEY = "chave-secreta-muito-segura-para-o-desafio"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ==========================================
# CONFIGURAÇÕES DE BANCO DE DADOS (ASYNC)
# ==========================================
DATABASE_URL = "sqlite+aiosqlite:///./banco.db"
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# ==========================================
# MODELOS DO BANCO DE DADOS (SQLAlchemy)
# ==========================================
class AccountDB(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    balance = Column(Float, default=0.0)
    
    transactions = relationship("TransactionDB", back_populates="account")

class TransactionDB(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("accounts.id"))
    type = Column(String, nullable=False) # 'deposito' ou 'saque'
    amount = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship("AccountDB", back_populates="transactions")

# ==========================================
# SCHEMAS DE VALIDAÇÃO (Pydantic)
# ==========================================
class TransactionType(str, Enum):
    DEPOSIT = "deposito"
    WITHDRAW = "saque"

class TransactionCreate(BaseModel):
    type: TransactionType
    # O requisito de impedir valores negativos é resolvido aqui com gt=0 (greater than 0)
    amount: float = Field(..., gt=0, description="O valor deve ser maior que zero")

class TransactionResponse(BaseModel):
    id: int
    type: str
    amount: float
    created_at: datetime

    class Config:
        from_attributes = True

class AccountCreate(BaseModel):
    username: str
    password: str

class StatementResponse(BaseModel):
    username: str
    balance: float
    transactions: List[TransactionResponse]

# ==========================================
# DEPENDÊNCIA DE AUTENTICAÇÃO
# ==========================================
async def get_current_account(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(AccountDB).filter(AccountDB.username == username))
    account = result.scalars().first()
    if account is None:
        raise credentials_exception
    return account

# ==========================================
# APLICAÇÃO FASTAPI
# ==========================================
app = FastAPI(
    title="API Bancária Assíncrona",
    description="Desafio de API bancária com FastAPI, JWT e operações assíncronas.",
    version="1.0.0"
)

@app.on_event("startup")
async def startup():
    # Cria as tabelas no banco de dados SQLite ao iniciar a aplicação
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# --- ROTAS DE AUTENTICAÇÃO ---

@app.post("/register", status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(account: AccountCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccountDB).filter(AccountDB.username == account.username))
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    
    new_account = AccountDB(
        username=account.username,
        hashed_password=get_password_hash(account.password)
    )
    db.add(new_account)
    await db.commit()
    return {"message": "Conta criada com sucesso"}

@app.post("/login", tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AccountDB).filter(AccountDB.username == form_data.username))
    account = result.scalars().first()
    
    if not account or not verify_password(form_data.password, account.hashed_password):
        raise HTTPException(status_code=400, detail="Usuário ou senha incorretos")
    
    access_token = create_access_token(data={"sub": account.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROTAS BANCÁRIAS PROTEGIDAS ---

@app.post("/transactions", response_model=TransactionResponse, tags=["Banking"])
async def create_transaction(
    transaction: TransactionCreate, 
    current_account: AccountDB = Depends(get_current_account),
    db: AsyncSession = Depends(get_db)
):
    # Validação de saldo para saque
    if transaction.type == TransactionType.WITHDRAW:
        if current_account.balance < transaction.amount:
            raise HTTPException(status_code=400, detail="Saldo insuficiente para realizar o saque.")
        current_account.balance -= transaction.amount
    
    # Depósito
    elif transaction.type == TransactionType.DEPOSIT:
        current_account.balance += transaction.amount
    
    # Registra a transação
    new_transaction = TransactionDB(
        account_id=current_account.id,
        type=transaction.type,
        amount=transaction.amount
    )
    
    db.add(new_transaction)
    await db.commit()
    await db.refresh(new_transaction)
    
    return new_transaction

@app.get("/statement", response_model=StatementResponse, tags=["Banking"])
async def get_statement(
    current_account: AccountDB = Depends(get_current_account),
    db: AsyncSession = Depends(get_db)
):
    # Busca todas as transações vinculadas à conta do usuário autenticado
    result = await db.execute(
        select(TransactionDB).filter(TransactionDB.account_id == current_account.id)
    )
    transactions = result.scalars().all()
    
    return StatementResponse(
        username=current_account.username,
        balance=current_account.balance,
        transactions=transactions
    )
