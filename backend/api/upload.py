from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from services.data_service import data_service
from models.schemas import UploadResponse
from dependencies.auth import get_current_user

router = APIRouter()

@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)                      
):
    print(f"用户 {current_user['username']} 上传了文件 {file.filename}")
    """上传CSV数据文件"""
    # 检查文件格式
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "只支持CSV格式文件")
    
    try:
        
        # 加载并分析数据
        df = data_service.load_data()
        file_info = data_service.get_file_info(df)
        
        return UploadResponse(
            filename=file.filename,
            rows=file_info["rows"],
            columns=file_info["columns"],
            message=f"成功上传 {file_info['rows']} 行数据"
        )
    except Exception as e:
        raise HTTPException(500, f"上传失败: {str(e)}")