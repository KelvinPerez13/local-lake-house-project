CREATE TABLE customers (id bigint PRIMARY KEY, name text NOT NULL, country text NOT NULL);
CREATE TABLE orders (
  id bigint PRIMARY KEY, customer_id bigint NOT NULL REFERENCES customers(id),
  amount numeric(12,2) NOT NULL CHECK(amount >= 0),
  status text NOT NULL CHECK(status IN ('paid','pending','cancelled')),
  ordered_at timestamptz NOT NULL
);
INSERT INTO customers VALUES (1,'Ana','BR'),(2,'Bruno','BR'),(3,'Carla','PT');
INSERT INTO orders VALUES
 (1,1,100.00,'paid','2025-01-01T10:00:00Z'),
 (2,2,50.00,'paid','2025-01-01T11:00:00Z'),
 (3,3,75.50,'paid','2025-01-02T12:00:00Z'),
 (4,1,20.00,'pending','2025-01-02T13:00:00Z'),
 (5,3,10.00,'cancelled','2025-01-02T14:00:00Z');
