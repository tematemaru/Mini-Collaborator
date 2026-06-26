from fastapi import FastAPI, Request
from sqlalchemy import create_engine, Integer, String, Text
from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
    Mapped,
    mapped_column,
)
import uuid
import json
from datetime import datetime

DATABASE_URL = "sqlite:///callbacks.db"

engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


class Callback(Base):
    __tablename__ = "callbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    token: Mapped[str] = mapped_column(
        String,
        index=True,
    )

    ip: Mapped[str] = mapped_column(String)

    method: Mapped[str] = mapped_column(String)

    headers: Mapped[str] = mapped_column(Text)

    query: Mapped[str] = mapped_column(Text)

    body: Mapped[str] = mapped_column(Text)

    created_at: Mapped[str] = mapped_column(String)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Collaborator",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Mini Collaborator",
    }


@app.get("/generate")
def generate_token():
    token = str(uuid.uuid4())

    return {
        "token": token,
        "callback_url": f"http://localhost:8000/c/{token}",
    }


@app.api_route(
    "/c/{token}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
)
async def collect(token: str, request: Request):
    db = SessionLocal()

    try:
        body = await request.body()

        callback = Callback(
            token=token,
            ip=request.client.host if request.client else "unknown",
            method=request.method,
            headers=json.dumps(dict(request.headers)),
            query=json.dumps(dict(request.query_params)),
            body=body.decode(errors="ignore"),
            created_at=datetime.utcnow().isoformat(),
        )

        db.add(callback)
        db.commit()

        return {
            "status": "received",
            "token": token,
        }

    finally:
        db.close()


@app.get("/logs/{token}")
def get_logs(token: str):
    db = SessionLocal()

    try:
        rows = (
            db.query(Callback)
            .filter(Callback.token == token)
            .all()
        )

        result = []

        for row in rows:
            result.append(
                {
                    "id": row.id,
                    "ip": row.ip,
                    "method": row.method,
                    "headers": json.loads(row.headers),
                    "query": json.loads(row.query),
                    "body": row.body,
                    "created_at": row.created_at,
                }
            )

        return result

    finally:
        db.close()


@app.get("/tokens")
def list_tokens():
    db = SessionLocal()

    try:
        rows = db.query(Callback.token).distinct().all()

        return {
            "tokens": [row[0] for row in rows]
        }

    finally:
        db.close()