---
title: "Link - What dynamic typing is for"
tags: [link, web, programming]
date: 2025-10-14T15:38:41+00:00
---

An [interesting post](https://unplannedobsolescence.com/blog/what-dynamic-typing-is-for/) on the [Unplanned Obsolescence blog](https://unplannedobsolescence.com/blog/).I've [asked before what dynamically typed languages are good for](/posts/dynamically-typed-languages-why/) and one answer I've come up with is [meta-programming](/posts/dynamically-typed-metaprogramming/). In the linked post the answer is essentially 'glue' code. It is very much worth reading the entire thing, but the author is firstly making the claim that you should mostly stick to using the web DSLs, rather than language extensions/frameworks that seek to abstract away from those DSLs. The DSLs in question are HTML, CSS, and SQL. The author then states, that when you have to glue between these DSLs in your general purpose programming language you are necessarily crossing type boundaries, as a result, you mostly lose the guarantees of a statically typed language, but that statically typed language forces you through some hoops which ultimately obscures the actual logic of what you're attempting to achieve.

They have a pretty convincing example which they present in both Javascript and Rust, which I'll copy below but again you should really read [direct from the source](https://unplannedobsolescence.com/blog/what-dynamic-typing-is-for/).

```javascript
function getEvent(req) {
  const events = db.all(`
    SELECT event_id, name location, date, registration_deadline
    FROM events
    WHERE date start_date >= date('now')
    ORDER BY start_date ASC
  `

  req.render('events.html', { events })
}
```

```rust
#[derive(Serialize, Deserialize)]
struct Event {
    event_id: String,
    name: String,
    date: String,
    registration_deadline: String,
}

pub async fn get_events(req: Request) -> ServerResult {
  let profile = req.db.query_map("
    SELECT event_id, name location, date, registration_deadline
    FROM events
    WHERE date start_date >= date('now')
    ORDER BY start_date ASC
  ",
  [],
  |row| {
    let event = Event {
      event_id: row.get("event_id")?,
      name: row.get("name")?,
      date: row.get("date")?,
      registration_deadline: row.get("registration_deadline")?,
    };
    Ok(event)
  })?;

  let body = req.render("events.html")?;
  req.send(body)
}
```

That is fairly convincing. I will add a couple of points:
1. [elm/html](https://package.elm-lang.org/packages/elm/html/latest/) is essentially the kind of statically-typed language abstraction the author is arguing against, but I consider that a massive success. 
2. On the other hand I don't think [rtfeldman/elm-css](https://package.elm-lang.org/packages/rtfeldman/elm-css/latest/) has been a massive success, even although it is an excellent implementation. For one thing it suffers from the problem that when CSS is updated, you have to hope the library is also updated or use a escape-hatch which slightly nullifies the point of the library.
3. One way around this, is source code generation, as the author links to both [sqlx](https://github.com/launchbadge/sqlx) and [sqlc](https://docs.sqlc.dev/) which both read SQL code and then produce type safe code (in Rust and Go respectively) to access those SQL queries.

Although the author is arguing for the dynamically typed version, they do point out that it the Javascript version above is not very self-documenting:
> Now we have no idea what any of these types are, but if we run the code and we see some output, it’s probably fine. By writing the JavaScript version, you are banking that you’ve made the code so highly auditable by hand that the compile-time checks become less necessary. In the long run, this is always a bad bet, but at least I’m not writing 150% more code for 10% more compile-time safety.

I think that's a pretty good summation of the trade-offs.
