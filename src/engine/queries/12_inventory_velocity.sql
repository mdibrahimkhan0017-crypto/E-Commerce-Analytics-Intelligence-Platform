-- 12: Inventory Velocity
-- Units sold per day per product (velocity metric).
-- Params: :start_date, :end_date

SELECT
    p.product_id,
    p.name AS product_name,
    p.category,
    SUM(oi.quantity) AS total_units_sold,
    JULIANDAY(:end_date) - JULIANDAY(:start_date) + 1 AS period_days,
    ROUND(
        SUM(oi.quantity) * 1.0
        / (JULIANDAY(:end_date) - JULIANDAY(:start_date) + 1), 2
    ) AS units_per_day
FROM order_items oi
JOIN orders o  ON oi.order_id  = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'Completed'
GROUP BY p.product_id, p.name, p.category
ORDER BY units_per_day DESC;
