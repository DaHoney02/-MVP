
# 统一模型异常的表达方式
class BaseAppException(Exception):
    """应用基础异常"""
    def __init__(self,message:str,code:int):
        self.message=message
        self.code=code
        super().__init__(message)

class LLMException(BaseAppException):
    """大模型调用异常"""
    pass

class BusinessException(BaseAppException):
    """业务异常"""
    pass