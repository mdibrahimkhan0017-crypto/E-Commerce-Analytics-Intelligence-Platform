-- 13: Discount Impact
-- Correlation view: orders with/without discount vs AOV and refund rate.
-- Params: :start_date, :end_date

SELECT
    CASE WHEN o.discount_amount > 0 THEN 'With Discount' ELSE 'No Discount' END AS discount_group,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(AVG(o.total_amount - o.discount_amount), 2) AS avg_order_value,
    ROUND(AVG(o.total_amount), 2) AS avg_gross_value,
    ROUND(AVG(o.discount_amount), 2) AS avg_discount,
    ROUND(
        SUM(CASE WHEN o.status = 'Refunded' THEN 1 ELSE 0 END) * 100.0
        / COUNT(*), 2
    ) AS refund_rate_pct
FROM orders o
WHERE o.order_date BETWEEN :start_date AND :end_date
GROUP BY discount_group
ORDER BY discount_group;
