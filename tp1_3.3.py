import os
from src.controler import DatabaseController

if __name__ == '__main__':
    while True:
        print('(a) Dado um produto, listar os 5 comentários mais úteis e com maior avaliação e os 5 comentários mais úteis e com menor avaliação')
        print('(b) Dado um produto, listar os produtos similares com maiores vendas do que ele')
        print('(c) Dado um produto, mostrar a evolução diária das médias de avaliação ao longo do intervalo de tempo coberto no arquivo de entrada')
        print('(d) Listar os 10 produtos líderes de venda em cada grupo de produtos')
        print('(e) Listar os 10 produtos com a maior média de avaliações úteis positivas por produto')
        print('(f) Listar a 5 categorias de produto com a maior média de avaliações úteis positivas por produto')
        print('(g) Listar os 10 clientes que mais fizeram comentários por grupo de produto')
        print('\n(0) EXIT')

        op = input('\n\n - Select an option: ')

        if op == '0':
            break

        elif op == 'a':
            product_asin = input(' - Please enter the product ASIN: ')
            query = f"""
                    (
                    SELECT r.*, 'Maior Avaliação' AS tipo
                    FROM Review r
                    WHERE r.product_asin = '{product_asin}'
                    ORDER BY r.rating DESC, r.helpful DESC
                    LIMIT 5
                    )
                    UNION ALL
                    (
                    SELECT r.*, 'Menor Avaliação' AS tipo
                    FROM Review r
                    WHERE r.product_asin = '{product_asin}'
                    ORDER BY r.rating ASC, r.helpful DESC
                    LIMIT 5
                    );
                    """
            print()
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Customer ID', 'Product ASIN', 'Review Date', 'Rating', 'Votes', 'Helpful', 'Review ID', 'Tipo'], rows)
        
        elif op == 'b':
            product_asin = input(' - Please enter the product ASIN: ')
            query = f"""
                SELECT sp.similar_asin, p.title, p.salesrank
                FROM SimilarProduct sp
                JOIN Product p ON sp.similar_asin = p.asin
                JOIN Product p_orig ON sp.product_asin = p_orig.asin
                WHERE sp.product_asin = '{product_asin}'
                AND p.salesrank < p_orig.salesrank;
                """
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Similar ASIN', 'Title', 'Sales Rank'], rows)
            
        elif op == 'c':
            product_asin = input(' - Please enter the product ASIN: ')
            query = f"""
                SELECT review_date, AVG(rating) AS avg_rating
                FROM Review
                WHERE product_asin = '{product_asin}'
                GROUP BY review_date
                ORDER BY review_date;
                """
            print()
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Review Date', 'AVG Rating'], rows)
            
        elif op == 'd':
            query = f"""
                SELECT product_group, asin, title, salesrank
                FROM (
                SELECT p.*, ROW_NUMBER() OVER (PARTITION BY product_group ORDER BY salesrank) AS rn
                FROM Product p
                ) sub
                WHERE rn <= 10 AND salesrank > 0
                ORDER BY product_group, rn;
                """
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Product Group', 'ASIN', 'Title', 'Sales Rank'], rows)
            
        elif op == 'e':
            query = f"""
                SELECT product_asin, AVG(CASE WHEN votes > 0 THEN helpful::FLOAT / votes ELSE 0 END) AS avg_helpfulness
                FROM Review
                WHERE rating >= 4
                GROUP BY product_asin
                ORDER BY avg_helpfulness DESC
                LIMIT 10;
                """            
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Product ASIN', 'AVG Helpfulness'], rows)
            
        elif op == 'f':
            query = f"""
                WITH avg_helpfulness_per_product AS (
                SELECT product_asin, AVG(CASE WHEN votes > 0 THEN helpful::FLOAT / votes ELSE 0 END) AS avg_helpfulness
                FROM Review
                WHERE rating >= 4
                GROUP BY product_asin
                ),
                product_categories AS (
                SELECT pc.product_asin, c.category_id, c.name AS category_name
                FROM ProductCategory pc
                JOIN Category c ON pc.category_id = c.category_id
                )
                SELECT pc.category_id, pc.category_name, AVG(ah.avg_helpfulness) AS category_avg_helpfulness
                FROM product_categories pc
                JOIN avg_helpfulness_per_product ah ON pc.product_asin = ah.product_asin
                GROUP BY pc.category_id, pc.category_name
                ORDER BY category_avg_helpfulness DESC
                LIMIT 5;
                """
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Category ID', 'Category Name', 'AVG Helpfulness Category'], rows)
            
        elif op == 'g':
            query = f"""
                SELECT product_group, customer_id, num_reviews
                FROM (
                SELECT product_group, customer_id, COUNT(*) AS num_reviews,
                        ROW_NUMBER() OVER (PARTITION BY product_group ORDER BY COUNT(*) DESC) AS rn
                FROM Review r
                JOIN Product p ON r.product_asin = p.asin
                GROUP BY product_group, customer_id
                ) sub
                WHERE rn <= 10
                ORDER BY product_group, num_reviews DESC;
                """
            rows = DatabaseController.getRows(query)
            DatabaseController.print_table(['Product Group', 'Customer ID', 'Number of Reviews'], rows)
        
        else:
            print('Invalid input.')
        

