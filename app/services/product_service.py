from app.services.base_service import BaseService
from app.repositories.product_repository import ProductRepository

class ProductService (BaseService) :
    
    def __init__(self):
        super().__init__(ProductRepository())
        
    