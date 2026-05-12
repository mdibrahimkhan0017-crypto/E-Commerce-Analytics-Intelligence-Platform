-- 06: Customer Order History
-- Full order history for a specific customer.
-- Params: :customer_id

SELECT
    c.customer_id,
    c.email,
    c.region,
    c.segment,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(AVG(o.total_amount - o.discount_amount), 2) AS avg_order_value,
    MAX(o.order_date) AS last_order_date,
    SUM(o.total_amount - o.discount_amount) AS total_spend
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id AND o.status = 'Completed'
WHERE c.customer_id = :customer_id
GROUP BY c.customer_id, c.email, c.region, c.segment;
