-- 05: Category Performance
-- Revenue, margin%, units, and return rate per product category.
-- Params: :start_date, :end_date

SELECT
    p.category,
    SUM(oi.quantity * oi.unit_price) AS total_revenue,
    ROUND(
        SUM(oi.quantity * (oi.unit_price - p.cost_price)) * 100.0
        / SUM(oi.quantity * oi.unit_price), 2
    ) AS margin_pct,
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
GROUP BY p.category
ORDER BY total_revenue DESC;
