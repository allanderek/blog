---
title: "LLMs and code duplication"
tags: [ A.I., llms, productivity]
date: 2025-12-16T19:19:01+00:00
---

I'm working on a project for which I'm using Go, as well as LLMs, mostly Sonnet 4.5 via Claude Code.
I've  noticed that it is frequently passing up on opportunities to factor out common code. But I'm not at all sure this is a bad thing.

Here is an example, which I've chosen as relatively short but it illustrates a pattern which is relatively common:

```go
	if config.DatabaseType == "postgres" {
		query = `
			SELECT p.slug,
			       COALESCE(NULLIF(p.menu_title, ''), p.title) as menu_title
			FROM pages p
			INNER JOIN site_pages sp ON sp.page_id = p.id AND sp.site_id = $1
			WHERE sp.is_homepage = false AND sp.site_id = $1
			ORDER BY p.title
		`
	} else {
		query = `
			SELECT p.slug,
			       COALESCE(NULLIF(p.menu_title, ''), p.title) as menu_title
			FROM pages p
			INNER JOIN site_pages sp ON sp.page_id = p.id AND sp.site_id = ?
			WHERE sp.is_homepage = 0 AND sp.site_id = ?
			ORDER BY p.title
		`
	}
```

Ignore the fact that there may be better ways to handle differences between database flavours.
The point here is that these two queries are almost identical, except for the parameter placeholder and boolean value.
A much better way to write this would be to have a single query with the differences parameterized:

```go
    var placeholder, booleanValue string
	if config.DatabaseType == "postgres" {
        placeholder = "$1"
        booleanValue = "false"
    } else {
        placeholder = "?"
        booleanValue = "0"
    }
    query := fmt.Sprintf(`
        SELECT p.slug,
               COALESCE(NULLIF(p.menu_title, ''), p.title) as menu_title
        FROM pages p
        INNER JOIN site_pages sp ON sp.page_id = p.id AND sp.site_id = %s
        WHERE sp.is_homepage = %s AND sp.site_id = %s
        ORDER BY p.title
    `, placeholder, booleanValue, placeholder)
```

This ensures that if I need to change the query I don't make the mistake of changing it for the development sqlite and forgetting about postgres.

However, I've also noticed myself being a little less worried about this kind of code duplication, because when it does change such a query, the LLM appears to be pretty good about changing it in both places. Nevertheless I also find the de-duplicated code a little easier to read, in particular I don't have to scan the two queries to figure out what the differences are.

I have [written before](/posts/dry-can-cost-you/) about how DRY can cost you, in that case in terms of performance (but a fairly large performance hit).
[Others have written](https://medium.com/@ss-tech/the-dark-side-of-dont-repeat-yourself-2dad61c5600a) before regarding the sin of premature abstraction. That is, DRYing up your code too early so you end up with the *wrong* abstraction. So LLMs *might* be helping to avoid that problem.

I still feel that in the case above, my de-duplicated effort is just better than the original written by the LLM. But the fact that LLMs appear to be pretty good at faithfully updating duplicated code gives you the *option* to avoid DRYing up your code too early.
