CREATE TABLE Product(
  id INTEGER UNIQUE NOT NULL,
  asin VARCHAR(10) PRIMARY KEY,
  title VARCHAR(500),
  product_group VARCHAR(50),
  salesrank INTEGER,
  review_total INTEGER,
  review_downloaded INTEGER,
  review_avg DECIMAL(10, 2)

);

CREATE TABLE Category(
  category_id INTEGER PRIMARY KEY,
  name VARCHAR(100),
  super_id INTEGER,
  
  FOREIGN KEY(super_id) REFERENCES Category(category_id)
);

CREATE TABLE ProductCategory(
  product_asin VARCHAR(10),
  category_id INTEGER,
  
  PRIMARY KEY(product_asin, category_id),
  
  FOREIGN KEY(category_id) REFERENCES Category(category_id),
  FOREIGN KEY(product_asin) REFERENCES Product(asin)
);

CREATE TABLE SimilarProduct(
  product_asin VARCHAR(10),
  similar_asin VARCHAR(10),
  
  PRIMARY KEY(product_asin, similar_asin),
  
  FOREIGN KEY(product_asin) REFERENCES Product(asin)
);

CREATE TABLE Review(
  customer_id VARCHAR(50),
  product_asin VARCHAR(10),
  review_date DATE,
  rating INTEGER,
  votes INTEGER,
  helpful INTEGER,
  review_id SERIAL PRIMARY KEY,
  
  FOREIGN KEY(product_asin) REFERENCES Product(asin)
);