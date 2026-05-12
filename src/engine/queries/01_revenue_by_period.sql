-- 01: Revenue by Period
-- Total revenue, order count, and average order value grouped by
-- the specified time period (day, week, month, quarter).
-- Params: :start_date, :end_date, :period

SELECT
    CASE :period
        WHEN 'day'     THEN DATE(o.order_date)
        WHEN 'week'    THEN DATE(o.order_date, 'weekday 0', '-6 days')
        WHEN 'month'   THEN STRFTIME('%Y-%m', o.order_date)
        WHEN 'quarter' THEN STRFTIME('%Y', o.order_date) || '-Q' ||
                            ((CAST(STRFTIME('%m', o.order_date) AS INTEGER) - 1) / 3 + 1)
    END AS period_label,
    SUM(o.total_amount - o.discount_amount) AS total_revenue,
    COUNT(DISTINCT o.order_id)              AS order_count,
    ROUND(
        SUM(o.total_amount - o.discount_amount) * 1.0
        / COUNT(DISTINCT o.order_id), 2
    ) AS aov
FROM orders o
WHERE o.order_date BETWEEN :start_date AND :end_date
  AND o.status = 'Completed'
GROUP BY period_label
ORDER BY period_label;
