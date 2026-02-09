from pydantic import BaseModel, Field
from typing import List, Optional

class ProcessRequest(BaseModel):
    file_id: str
    chunk_size: Optional[int] = 100
    overlab: Optional[int] = 20
    do_reset: Optional[int] = 0
     