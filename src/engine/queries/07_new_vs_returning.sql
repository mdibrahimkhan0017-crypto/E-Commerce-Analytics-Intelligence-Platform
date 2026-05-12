-- 07: New vs Returning Customers
-- Count and revenue split between new and returning customers by month.
-- A "new" customer's first completed order falls in that month.
-- Params: :year

WITH first_orders AS (
    SELECT
        customer_id,
        MIN(order_date) AS first_order_date
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
)
SELECT
    STRFTIME('%Y-%m', o.order_date) AS month_label,
    SUM(CASE
        WHEN STRFTIME('%Y-%m', fo.first_order_date) = STRFTIME('%Y-%m', o.order_date)
        THEN 1 ELSE 0
    END) AS new_customers,
    SUM(CASE
        WHEN STRFTIME('%Y-%m', fo.first_order_date) < STRFTIME('%Y-%m', o.order_date)
        THEN 1 ELSE 0
    END) AS returning_customers,
    SUM(CASE
        WHEN STRFTIME('%Y-%m', fo.first_order_date) = STRFTIME('%Y-%m', o.order_date)
        THEN o.total_amount - o.discount_amount ELSE 0
    END) AS new_customer_revenue,
    SUM(CASE
        WHEN STRFTIME('%Y-%m', fo.first_order_date) < STRFTIME('%Y-%m', o.order_date)
        THEN o.total_amount - o.discount_amount ELSE 0
    END) AS returning_customer_revenue
FROM orders o
JOIN first_orders fo ON o.customer_id = fo.customer_id
WHERE STRFTIME('%Y', o.order_date) = :year
  AND o.status = 'Completed'
GROUP BY month_label
ORDER BY month_label;
