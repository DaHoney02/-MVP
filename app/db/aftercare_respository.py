from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AftercareRecord
from app.schemas.aftercare import AftercareCreate

# 增删查改操作
def create_record(
    db: Session,
    data: AftercareCreate,
) -> AftercareRecord:
    record = AftercareRecord(**data.model_dump())

    try:
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise

def get_record(
        db:Session,
        record_id:int
)->AftercareRecord | None:
    return db.get(AftercareRecord,record_id)

def list_records(
        db:Session,
        limit:int=50,
        offset:int=0
)->list[AftercareRecord]:
    statement=(
        select(AftercareRecord)
        .order_by(AftercareRecord.created_at.desc())
        .limit(limit)
    )
    return list(db.scalars(statement).all())

def update_record(
        db:Session,
        record:AftercareRecord,
        data:AftercareCreate
)->AftercareRecord:
    for field,value in data.model_dump().items():
        setattr(record,field,value)

    try:
        db.commit()
        db.refresh(record)
        return record
    except Exception:
        db.rollback()
        raise

def delete_record(
        db:Session,
        record:AftercareRecord
)->None:
    try:
        db.delete(record)
        db.commit()
    except Exception:
        db.rollback()
        raise