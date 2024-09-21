import re
import psycopg2
from psycopg2.extras import execute_values
from configparser import ConfigParser
from src.model import Product, Category, ProductCategory, SimilarProduct, Review
from tabulate import tabulate

class DatasetController:

    @staticmethod
    def extract(dataset_path:str):

        product_list = []
        category_dict = dict()
        prod_category_dict = dict()
        similars_list = []
        reviews_list = []

        with open(dataset_path, "r", encoding="utf8") as file:
            # Jump the 3 header lines 
            for i in range(3):
                _ = file.readline()
            
            # List that contains each line of information of a product information block
            product_block_lines = []

            for line in file:
                # If the line has only a '\n' it means that is the end of a product info block
                if line == '\n':    
                    # Extract objects from the product info block and store
                    product_obj, categories_objs, products_category_objs, similars_objs, reviews_objs = DatasetController._extract_objs(product_block_lines)
                    product_list.append(product_obj)
                    category_dict.update(categories_objs)
                    prod_category_dict.update(products_category_objs)
                    similars_list.extend(similars_objs)
                    reviews_list.extend(reviews_objs)

                    # After extracting reset the product block
                    product_block_lines = []
                    continue

                # If the current line is not the end of a block, add the line to the product block
                product_block_lines.append(line)

        return product_list, list(category_dict.values()), list(prod_category_dict.values()), similars_list, reviews_list

    def _extract_objs(block):
        # If the product is descontinued it will have only 3 lines

        categories_dict = {}
        products_category_dict = {}
        similars_list = []
        reviews_list = []

        product = Product(int(block[0][3:].strip()), block[1][5:].strip())

        # If the block contains only 3 lines it means that is discontinued product
        if len(block) == 3:
            return (product, {}, {}, [], [])

        # Extract easy information
        product.title = block[2][8:].strip()
        product.product_group = block[3][8:].strip()
        product.salesrank = int(block[4][12:].strip())
        # Get the number of similar products
        num_similar = block[5][11:12]
        # If there is similar products get all of them
        if num_similar != 0:
            similars_info_list = block[5][14:].split('  ')
            similars_info_list[-1] = similars_info_list[-1].strip()

            similars_list.extend([SimilarProduct(product.asin, similar_asin) for similar_asin in similars_info_list])
        # Get the number of categories
        num_categories_lines = int(block[6][13:].strip())
        # If there's categories, separate categories lines from block and elimite all read lines 
        if num_categories_lines != 0:
            # Separate categories lines
            categories_lines = block[7:7 + num_categories_lines]
            # Elimite all read lines 
            block = block[7+num_categories_lines:]

            # Iterate beteween the category lines
            for category_line in categories_lines:
                parent_id = None
                # Iterate beteween the each category info 'category[id]'
                for category_label in category_line.strip().split('|')[1:]:
                    
                    category_info_regex = re.compile(r'(.*?)\s*\[(\d+)\]')
                    category_info = re.search(category_info_regex, category_label).groups()
                    category_name = category_info[0] 
                    category_id = category_info[1]
                    
                    products_category_dict[product.product_id] = ProductCategory(product.asin, category_id)
                    categories_dict[category_id] = Category(category_id, category_name, parent_id)
                    parent_id = category_id
        else:
            block = block[7:]
                    

        review_info_regex = re.compile(r'reviews:\stotal:\s(\d+)\s{2}downloaded:\s(\d+)\s{2}avg\srating:\s(\d+)')

        review_info_line = block[0].strip()
        reviews_info = review_info_regex.search(review_info_line).groups()

        product.review_total, product.review_downloaded, product.review_avg = reviews_info

        # Remove read lines, leving only review lines
        block = block[1:]

        # If there's reviews, extract
        if reviews_info[0] != 0:
            review_regex = re.compile(r'(\d{4}-\d{1,2}-\d{1,2})\s{2}cutomer:\s+([A-Z0-9]+)\s{2}rating:\s+(\d+)\s{2}votes:\s+(\d+)\s{2}helpful:\s+(\d+)')
            
            for review_line in block:
                review_info = review_regex.search(review_line.strip()).groups()
                review = Review(product.asin, review_info[1], review_info[0])
                review.rating = int(review_info[2])
                review.votes = int(review_info[3])
                review.helpful = int(review_info[4])
                reviews_list.append(review)

        return (product, categories_dict, products_category_dict, similars_list, reviews_list)
        
                
class DatabaseController:
    amazondb_session = './config/amazondb.ini'

    @classmethod
    def insert_many(cls, table_name, data):
        amazondb_config = DatabaseController.getConfiguration(cls.amazondb_session, "amazondb")
        conn = DatabaseController.getConnection(amazondb_config)
        conn.autocommit = True
        cursor = conn.cursor()
        insert_query = f"""
            INSERT INTO {table_name}
            VALUES %s
        """
        execute_values(cursor, insert_query, data)
        cursor.close()
        conn.close()
        print(f"Inserted tuples in {table_name} successfully!")

    @classmethod
    def getConnection(cls, config):
        # Connect to the PostgreSQL database server
        try:
            with psycopg2.connect(**config) as conn:
                print('Connected to the PostgreSQL server.')
                return conn
        except (psycopg2.DatabaseError, Exception) as error:
            print(error)
    
    @classmethod
    def getConfiguration(cls, filename, section):
        parser = ConfigParser()
        parser.read(filename)
        config = {}
        if parser.has_section(section):
            params = parser.items(section)
            for param in params:
                config[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
        return config
    
    @classmethod
    def createDatabase(cls, database_first_session):
        init_config = DatabaseController.getConfiguration(database_first_session, "postgresql")
        conn = DatabaseController.getConnection(init_config)
        conn.autocommit = True
        cursor = conn.cursor()
        try:
            cursor.execute(f"CREATE DATABASE amazondb")
            print("Database was created!")
        except Exception as error:
            print(f"Something went wrong: {error}")
        cursor.close()
        conn.close()
    
    @classmethod
    def createTables(cls, sqlTablesFileName):
        with open(sqlTablesFileName, "r") as f:
            sqlTables = f.readlines()
            sqlTables = ''.join(sqlTables)
        try:
            DatabaseController.executeQuery(sqlTables)
            print("Tables succesfully created!")
        except Exception as error:
            print(f"Something went wrong: {error}")
        f.close()
    
    @classmethod
    def getRows(cls, query):
        amazondb_config = DatabaseController.getConfiguration(cls.amazondb_session, "amazondb")
        conn = DatabaseController.getConnection(amazondb_config)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    
    @classmethod
    def executeQuery(cls, query):
        amazondb_config = DatabaseController.getConfiguration(cls.amazondb_session, "amazondb")
        conn = DatabaseController.getConnection(amazondb_config)
        conn.autocommit = True
        cursor = conn.cursor()
        cursor.execute(query)
        cursor.close()
        conn.close()

    @classmethod
    def print_table(cls, headers, matrix):
        """
        Print a table with given headers and matrix of values.

        :param headers: List of column headers.
        :param matrix: List of lists, where each inner list represents a row of values.
        """
        # Create the table
        table = tabulate(matrix, headers=headers, tablefmt='grid')
        
        # Print the table
        print(table)


class ProductDAO(DatabaseController):
    TABLE_NAME = "Product"

    @classmethod
    def insert_many(cls, obj_list):
        return super().insert_many(cls.TABLE_NAME, [obj.to_tuple() for obj in obj_list])
class CategoryDAO(DatabaseController):
    TABLE_NAME = "Category"

    @classmethod
    def insert_many(cls, obj_list):
        return super().insert_many(cls.TABLE_NAME, [obj.to_tuple() for obj in obj_list])
class ProductCategoryDAO(DatabaseController):
    TABLE_NAME = "ProductCategory"
    
    @classmethod
    def insert_many(cls, obj_list):
        return super().insert_many(cls.TABLE_NAME, [obj.to_tuple() for obj in obj_list])
class SimilarProductDAO(DatabaseController):
    TABLE_NAME = "SimilarProduct"

    @classmethod
    def insert_many(cls, obj_list):
        return super().insert_many(cls.TABLE_NAME, [obj.to_tuple() for obj in obj_list])
class ReviewDAO(DatabaseController):
    TABLE_NAME = "Review"

    @classmethod
    def insert_many(cls, obj_list):
        return super().insert_many(cls.TABLE_NAME, [obj.to_tuple() for obj in obj_list])

           
