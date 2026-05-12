-- 15: Geographic Revenue
-- Revenue by customer region.
-- Params: :start_date, :end_date

SELECT
    c.region,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COUNT(DISTINCT o.order_id) AS order_count,
    SUM(o.total_amount - o.discount_amount) AS total_revenue,
    ROUND(
        SUM(o.total_amount - o.discount_amount) * 1.0
        / COUNT(DISTINCT o.order_id), 2
    ) AS aov
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'Completed'
GROUP BY c.region
ORDER BY total_revenue DESC;
