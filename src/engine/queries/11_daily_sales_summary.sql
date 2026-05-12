-- 11: Daily Sales Summary
-- Daily KPI snapshot: revenue, orders, new customers, refunds.
-- Params: :target_date

SELECT
    :target_date AS report_date,
    COALESCE(SUM(CASE WHEN o.status = 'Completed'
        THEN o.total_amount - o.discount_amount ELSE 0 END), 0) AS daily_revenue,
    COUNT(DISTINCT CASE WHEN o.status = 'Completed'
        THEN o.order_id END) AS completed_orders,
    COUNT(DISTINCT CASE WHEN o.status = 'Refunded'
        THEN o.order_id END) AS refunded_orders,
    (
        SELECT COUNT(DISTINCT c.customer_id)
        FROM customers c
        WHERE c.registration_date = :target_date
    ) AS new_customers,
    COALESCE(SUM(CASE WHEN o.status = 'Completed'
        THEN o.discount_amount ELSE 0 END), 0) AS total_discounts
FROM orders o
WHERE o.order_date = :target_date;
