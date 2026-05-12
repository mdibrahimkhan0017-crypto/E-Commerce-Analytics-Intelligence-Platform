-- 08: Cohort Retention
-- Monthly cohort retention table showing percentage of customers who
-- made a purchase in each subsequent month after their cohort month.
-- Params: :cohort_year

WITH cohorts AS (
    SELECT
        customer_id,
        STRFTIME('%Y-%m', MIN(order_date)) AS cohort_month
    FROM orders
    WHERE status = 'Completed'
    GROUP BY customer_id
),
activities AS (
    SELECT DISTINCT
        o.customer_id,
        c.cohort_month,
        STRFTIME('%Y-%m', o.order_date) AS activity_month,
        (
            (CAST(STRFTIME('%Y', o.order_date) AS INTEGER) -
             CAST(SUBSTR(c.cohort_month, 1, 4) AS INTEGER)) * 12
            + CAST(STRFTIME('%m', o.order_date) AS INTEGER)
            - CAST(SUBSTR(c.cohort_month, 6, 2) AS INTEGER)
        ) AS month_offset
    FROM orders o
    JOIN cohorts c ON o.customer_id = c.customer_id
    WHERE o.status = 'Completed'
      AND SUBSTR(c.cohort_month, 1, 4) = :cohort_year
)
SELECT
    cohort_month,
    month_offset,
    COUNT(DISTINCT customer_id) AS active_customers,
    ROUND(
        COUNT(DISTINCT customer_id) * 100.0
        / (SELECT COUNT(DISTINCT customer_id) FROM cohorts co
           WHERE co.cohort_month = activities.cohort_month),
        2
    ) AS retention_pct
FROM activities
GROUP BY cohort_month, month_offset
ORDER BY cohort_month, month_offset;
