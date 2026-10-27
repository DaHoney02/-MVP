
from fastapi import APIRouter,status,HTTPException
from fastapi.params import Depends, Query
from langchain_core.language_models.llms import aupdate_cache
from sqlalchemy.orm import Session

from app.db.aftercare_respository import (
    create_record,
    list_records,
    get_record,
    update_record,
    delete_record
)

from app.db.database import get_db
from app.schemas.aftercare import AftercareResponse, AftercareCreate

router=APIRouter(prefix="/aftercare",tags=["后援记录"])

# 创建
@router.post(
    "",
    response_model=AftercareResponse,
    status_code=status.HTTP_201_CREATED
)
def create_aftercare(
        data:AftercareCreate,
        db:Session=Depends(get_db)
):
    return create_record(db,data)

# 列表查询
@router.get("",response_model=list[AftercareResponse])
def get_aftercare_list(
        limit:int=Query(default=50,ge=1,le=100),
        offset:int=Query(default=0,ge=0),
        db:Session=Depends(get_db)
):
    return list_records(db,limit,offset)

# 详情查询
@router.get("/{record_id}",response_model=AftercareResponse)
def get_aftercare_detail(
        record_id:int,
        db:Session=Depends(get_db)
):
    record=get_record(db,record_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="后援记录不存在"
        )
    return record

# 更新
@router.put("/{record_id}",response_model=AftercareResponse)
def update_aftercare(
        record_id:int,
        data:AftercareCreate,
        db:Session=Depends(get_db)
):
    record=get_record(db,record_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="后援记录不存在"
        )
    return update_record(db,record,data)

# 删除
@router.delete("/{record_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_aftercare(
        record_id:int,
        db:Session=Depends(get_db)
):
    record=get_record(db,record_id)
    if record is None:
        raise HTTPException(status_code=404,detail="后援记录不存在")
    delete_record(db,record)
