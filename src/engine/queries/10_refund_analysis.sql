-- 10: Refund Analysis
-- Refund rate by category, product, and month.
-- Params: :start_date, :end_date

SELECT
    p.category,
    p.name AS product_name,
    STRFTIME('%Y-%m', o.order_date) AS month_label,
    COUNT(*) AS total_items,
    SUM(CASE WHEN oi.return_flag = 1 THEN 1 ELSE 0 END) AS returned_items,
    ROUND(
        SUM(CASE WHEN oi.return_flag = 1 THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    ) AS refund_rate_pct,
    SUM(CASE WHEN o.status = 'Refunded' THEN 1 ELSE 0 END) AS refunded_orders
FROM order_items oi
JOIN orders o  ON oi.order_id  = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE o.order_date BETWEEN :start_date AND :end_date
GROUP BY p.category, p.name, month_label
ORDER BY refund_rate_pct DESC;
