-- 14: Customer Segments
-- Count and revenue per customer segment label.
-- Params: none

SELECT
    c.segment,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    COALESCE(SUM(CASE WHEN o.status = 'Completed'
        THEN o.total_amount - o.discount_amount ELSE 0 END), 0) AS total_revenue,
    ROUND(
        COALESCE(SUM(CASE WHEN o.status = 'Completed'
            THEN o.total_amount - o.discount_amount ELSE 0 END), 0) * 1.0
        / NULLIF(COUNT(DISTINCT c.customer_id), 0), 2
    ) AS revenue_per_customer
FROM customers c
LEFT JOIN orders o ON c.customer_id = o.customer_id
GROUP BY c.segment
ORDER BY total_revenue DESC;
