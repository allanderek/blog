---
title: "Return a database from a query"
tags: [ databases ]
date: 2025-08-21T13:22:50+00:00
---

I use SQL in many projects, and that is often in the form of SQLite.
Something of a limitation I find is that only a single table can be returned from a single query. Whilst using SQLite, that's often not so much of an issue since making several queries is less of a performance issue when it does not involve multiple round trips to a server.

Nonetheless it can sometimes either mean extra computation, or doing more in the general purpose language to post-process the results of a single query. In addition, to sometimes the wastefulness of repeating the same answer. Anyway, I think this is best shown with an example in mind.


Suppose we are building a e-commerce solution, and we wish to display information about users and orders. Suppose you want two bits of data:

1. **Order details** - a list of orders with user information
2. **User summaries** - a list of users with their order counts

This can of course be achieved with two separate queries:

```sql
-- Query 1: Order details
select 
    U.id as user_id, 
    u.name as user_name,
    o.id as order_id,
    o.amount as order_amount,
    o.created_at as order_date
from users u
left join orders o ON u.id = o.user_id;

-- Query 2: User summaries  
select 
    u.id AS user_id, 
    u.name AS user_name,
    COUNT(o.id) AS order_count
from users u
left join orders o ON u.id = o.user_id
group BY u.id, u.name;
```

Aside from the just the overall clunkiness of being forced into two separate queries here, there is some waste. Both queries scan both the `users` and `orders` tables, and both perform the same `join` operation. 

This isn't quite the classic "N+1" query problem as we're not making N queries for N users. But it's kind of related.

One solution to this would be to allow a query to return a 'database', that is, a *collection* of tables, rather than a single table.

```sql
with shared_data as (
    select u.id as user_id, u.name, o.id as order_id, o.amount, o.created_at
    from users u left join orders o ON u.id = o.user_id
)
return MULTIPLE (
    order_details: select * from shared_data where order_id is not null,
    user_summaries: select user_id, name, count(order_id) as order_count 
                   from shared_data 
                   group BY user_id, name
);
```

(My preference is to *not* capitalise SQL keywords, since they are highlighted by the editor anyway. However since `MULTIPLE` here is a proposed new keyword, I've captilised it to highlight it).

This hypothetical query would return:

```javascript
{
  order_details: [
    {user_id: 1, name: "Alice", order_id: 101, amount: 250.00, created_at: "2023-01-15"},
    {user_id: 1, name: "Alice", order_id: 102, amount: 180.00, created_at: "2023-02-03"},
    {user_id: 2, name: "Bob", order_id: 103, amount: 95.00, created_at: "2023-01-20"},
    // ...
  ],
  user_summaries: [
    {user_id: 1, name: "Alice", order_count: 3},
    {user_id: 2, name: "Bob", order_count: 1},
    // ...
  ]
}
```

In this instance the second query is pretty simple, but the underlying computation might be relatively complicated.
The motivating example for this was scoring formula1/football season predictions. In season predictions the user orders the teams in the order they think they will finish at the end of the season. Each *line* is scored according to how far away (in points) they are from the predicted position. So what I end up with, is a leaderboard or users to total points, but what I *also* want is the breakdown for each user, of team+position to points.

Anyway, here I've had Claude produce a more complicated user+orders example, where there is some amount of shared computation:


```sql  
with enriched_orders as (
    select u.id as user_id, u.name, u.country,
           o.id as order_id, o.amount, 
           o.amount * 0.1 as tax,
           o.amount + (o.amount * 0.1) as total_due,
           case when o.amount > 1000 then 'high_value' else 'standard' end as risk_category
    from users u left join orders o ON u.id = o.user_id
)
return MULTIPLE (
    detailed_orders: select * from enriched_orders,
    user_balances: select user_id, name, country,
                          sum(total_due) as total_balance,
                          count(case when risk_category = 'high_value' then 1 end) as high_value_orders
                   from enriched_orders 
                   group by user_id, name, country,
    risk_summary: select risk_category, country,
                         count(*) as order_count,
                         avg(total_due) as avg_order_value
                  from enriched_orders
                  where order_id is not null
                  group by risk_category, country
);
```


The complex calculations (tax, total_due, risk_category) happen once and feed into three different result sets. This is difficult with single-table queries,
and/or means doing quite a bit of post-query processing in the general purpose language.


### Composibility

I haven't thought hard about this. Generally, any SQL query can be used as part of a larger query. If queries *may* return multiple tables, either the language
would need to be updated to allow incorporating such results into larger queries, or the user would be restricted to only returning multiple tables in a top-level query.

I'm aware that languages like Malloy and EdgeQL do allow something similar to this, but they then take that further to allow for generally nested results, whereas what I'm hoping to achieve is to retain the relational nature of the results, but simply allow multiple tables rather than a single one to be the result. I believe (but cannot demonstrate) that this would be a good trade-off from expressivity and constraint.

It could be that I just do not know databases well enough and that this is a solved problem?
