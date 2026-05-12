-- 09: Channel Performance
-- Revenue, order count, and AOV per sales channel.
-- Params: :start_date, :end_date

SELECT
    o.channel,
    SUM(o.total_amount - o.discount_amount) AS total_revenue,
    COUNT(DISTINCT o.order_id) AS order_count,
    ROUND(
        SUM(o.total_amount - o.discount_amount) * 1.0
        / COUNT(DISTINCT o.order_id), 2
    ) AS aov
FROM orders o
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'Completed'
GROUP BY o.channel
ORDER BY total_revenue DESC;
