-- 02: Revenue Growth (Month-over-Month)
-- Month-over-month revenue growth percentage using LAG window function.
-- Params: :year

SELECT
    month_label,
    monthly_revenue,
    prev_month_revenue,
    CASE
        WHEN prev_month_revenue IS NULL OR prev_month_revenue = 0 THEN NULL
        ELSE ROUND(
            (monthly_revenue - prev_month_revenue) * 100.0
            / prev_month_revenue, 2
        )
    END AS growth_pct
FROM (
    SELECT
        STRFTIME('%Y-%m', o.order_date) AS month_label,
        SUM(o.total_amount - o.discount_amount) AS monthly_revenue,
        LAG(SUM(o.total_amount - o.discount_amount))
            OVER (ORDER BY STRFTIME('%Y-%m', o.order_date)) AS prev_month_revenue
    FROM orders o
    WHERE STRFTIME('%Y', o.order_date) = :year
      AND o.status = 'Completed'
    GROUP BY month_label
)
ORDER BY month_label;
