-- 04: Bottom Products by Revenue
-- Bottom N products by revenue.
-- Params: :start_date, :end_date, :limit

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    SUM(oi.quantity * oi.unit_price) AS total_revenue,
    SUM(oi.quantity) AS units_sold,
    ROUND(
        SUM(CASE WHEN oi.return_flag = 1 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    ) AS return_rate_pct
FROM order_items oi
JOIN orders o  ON oi.order_id  = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'Completed'
GROUP BY p.product_id, p.name, p.category
ORDER BY total_revenue ASC
LIMIT :limit;
