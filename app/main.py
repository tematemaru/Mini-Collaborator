from fastapi import FastAPI, Request, Depends
from sqlalchemy.orm import Session
import uuid
import json
from datetime import datetime, timedelta
import asyncio
from app.database import get_db, Base, engine
from app.models import Callback
from app.config import Config

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mini Collaborator",
    version="2.0.0",
    debug=Config.DEBUG
)

@app.on_event("startup")
async def startup_event():
    """Запуск фоновых задач"""
    asyncio.create_task(cleanup_old_callbacks())

async def cleanup_old_callbacks():
    """Автоматическая очистка старых записей"""
    while True:
        await asyncio.sleep(Config.CLEANUP_INTERVAL)
        db = next(get_db())
        try:
            cutoff = datetime.utcnow() - timedelta(hours=Config.CLEANUP_HOURS)
            deleted = db.query(Callback).filter(Callback.created_at < cutoff).delete()
            db.commit()
            if Config.DEBUG and deleted:
                print(f"[CLEANUP] Удалено {deleted} старых записей")
        except Exception as e:
            print(f"[ERROR] Очистка БД: {e}")
        finally:
            db.close()

@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Mini Collaborator",
        "version": "2.0.0",
        "server_ip": Config.LOCAL_IP
    }

@app.get("/generate")
def generate_token():
    token = str(uuid.uuid4())
    return {
        "token": token,
        "callback_url": f"http://{Config.LOCAL_IP}:{Config.PORT}/c/{token}",
        "dns": f"{token}.collab.local",  # если настроен DNS
        "created_at": datetime.utcnow().isoformat()
    }

@app.api_route("/c/{token}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def collect(token: str, request: Request, db: Session = Depends(get_db)):
    try:
        body = await request.body()
        
        callback = Callback(
            token=token,
            ip=request.client.host if request.client else "unknown",
            method=request.method,
            headers=json.dumps(dict(request.headers)),
            query=json.dumps(dict(request.query_params)),
            body=body.decode(errors="ignore")
        )
        
        db.add(callback)
        db.commit()
        
        return {
            "status": "received",
            "token": token,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {"error": str(e)}, 500

@app.get("/logs/{token}")
def get_logs(token: str, db: Session = Depends(get_db)):
    rows = db.query(Callback).filter(Callback.token == token).order_by(Callback.created_at.desc()).all()
    
    return [
        {
            "id": row.id,
            "ip": row.ip,
            "method": row.method,
            "headers": json.loads(row.headers),
            "query": json.loads(row.query),
            "body": row.body,
            "created_at": row.created_at.isoformat()
        }
        for row in rows
    ]

@app.get("/tokens")
def list_tokens(db: Session = Depends(get_db)):
    rows = db.query(Callback.token).distinct().all()
    return {"tokens": [row[0] for row in rows]}

@app.get("/stats/{token}")
def get_stats(token: str, db: Session = Depends(get_db)):
    rows = db.query(Callback).filter(Callback.token == token).all()
    
    if not rows:
        return {"error": "Token not found"}, 404
    
    return {
        "total": len(rows),
        "unique_ips": len(set(r.ip for r in rows)),
        "methods": {m: len([r for r in rows if r.method == m]) for m in set(r.method for r in rows)},
        "first_request": min(r.created_at for r in rows).isoformat(),
        "last_request": max(r.created_at for r in rows).isoformat(),
        "recent": [
            {
                "time": r.created_at.isoformat(),
                "method": r.method,
                "ip": r.ip
            }
            for r in rows[-10:]
        ]
    }

@app.delete("/logs/{token}")
def delete_logs(token: str, db: Session = Depends(get_db)):
    deleted = db.query(Callback).filter(Callback.token == token).delete()
    db.commit()
    return {"deleted": deleted, "token": token}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG
    )