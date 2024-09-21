from src.controler import DatasetController, DatabaseController
from src.controler import ProductDAO, CategoryDAO, ProductCategoryDAO, SimilarProductDAO, ReviewDAO
from datetime import datetime

DATASET_PATH = './data/amazon-meta.txt'
DATABASE_TABLES = './config/database.sql'
DATABASE_CREATION_SESSION = './config/database.ini'
DATABASE_AMAZONDB_SESSION = './config/amazondb.ini'

def main():
    start_time = datetime.now()
    
    # Create database
    DatabaseController.createDatabase(DATABASE_CREATION_SESSION)
    DatabaseController.createTables(DATABASE_TABLES)

    product_list, category_list, prod_category_list, similars_list, reviews_list = DatasetController.extract(DATASET_PATH)

    # Insert the objects in the database
    DatabaseController.amazondb_session = DATABASE_AMAZONDB_SESSION
    ProductDAO.insert_many(product_list)
    CategoryDAO.insert_many(category_list)
    ProductCategoryDAO.insert_many(prod_category_list)
    SimilarProductDAO.insert_many(similars_list)
    ReviewDAO.insert_many(reviews_list)

    print(f'Tempo execução = {datetime.now() - start_time}')

if __name__ == "__main__":
    main()
