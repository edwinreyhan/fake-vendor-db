UPDATE products SET amount = CAST(ROUND(amount * 100) AS INTEGER);
