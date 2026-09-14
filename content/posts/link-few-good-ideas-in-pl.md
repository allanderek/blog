---
title: "Link: A few good ideas in programming languages"
tags: [ programming ]
date: 2026-09-13T15:43:19+00:00
---

Pranoy Dutta has [written a post describing three good features of programming languages](https://prydt.xyz/blog/a-few-good-ideas-in-pl/).
I love such posts. It's also good to hear of good features that seem somewhat orthogonal to the point of the language. For example, laziness may or may not be a useful feature, but how well it might work is definitely dependent on the otherwise shape of the language. Whereas many languages have minor quality-of-life improvement features that should work in **most** languages. For example, some language some time ago started allowing large numbers to contain underscores, so that 1000000 can be written as 1_000_000, making it a bit easier to read. That's obviously fairly independent of how the rest of the language works and as such several languages have copied that. Of course this is something of a spectrum, you may find a feature that works pretty well in any functional language for example.

In the linked post, Pranoy describes three features that they think are generally useful, good ideas. I'll go through each of them.

## Flow Typing

I agree flow-typing can be useful. I think the example given here is pretty useless. Re-assignment is generally not particularly useful. In the example, and in the vast majority of other cases, you can either simply use a different variable, or use **type narrowing**. The standard example is a nullable variable which cannot be null after a null-check:

```typescript
const user = findUser(req);        // User | null
  if (!user) {
    // User is null within this 'if branch' do whatever is appropriate.
    // Importantly, user.role is not accessible here.
  } else {
    // Now, user has been narrowed from User | null to simply User.
    // So now, one can access user.role
      if (user.role !== "admin") {
        // Do something appropriate for non-admin users.
      } else {
        // Do something appropriate for admin users.
  }
```

In a functional language we would likely use tagged-union types for this, specifically a `Maybe` or `Option` type.
```elm
case findUser req of
    Nothing ->
        -- User is null within this 'if branch' do whatever is appropriate.
        -- Importantly, user.role is not accessible here.
    Just user ->
        -- This new `user` variable is necessarily a `User` type
        -- So now, one can access user.role
        case user.role of
            "admin" ->
                -- Do something appropriate for admin users.
            _ ->
                -- Do something appropriate for non-admin users.
```

On the one hand with tagged-union types, flow-typing is largely unnecessary. However, the tagged-union types can become
somewhat unweildy, and in paticular because most languages have *nominal tagged union types* (as opposed to [structural tagged union types](/posts/structural-custom-types/)) it can be awkward to design your types in a way that makes it appropriate. Suppose you have a `User` tagged type, in which a user can be an `Admin` or some other types (e.g. Free, Premium, Gold etc.):

```elm
type User
    = Admin
    | Free
    | Premium
    | Gold
```

Then you can use flow-typing to narrow the type of `user`:

```elm
case user of
    Admin ->
        -- Do something appropriate for admin users.
    _ ->
        -- It would be nice if here we could use `user`
        -- knowing that it cannot be `Admin`.
```
You can get around this by re-designing your User type:
```elm
type User
    = Admin
    | NonAdmin NonAdminUser
type NonAdminUser
    = Free
    | Premium
    | Gold
case user of
    Admin ->
        -- Do something appropriate for admin users.
    NonAdminUser naUser ->
        -- Here naUser **cannot** be `Admin`.
```
But what if you later wish to write a function that does one thing for `Free` users and something else for `Admin`, `Premium`, and `Gold` users?

The amalgamation of flow-typing with *structural* union types would, I think, be a useful combination to see, but I don't know of any examples of it.

Finally, just to note that functional languages do lend themselves well to an *implementation* of flow-typing, because *"everything is an expression"* the scope of a variable tends to be just the sub-expression in which it is defined. 
In an imperative language you can do something like:

```typescript
const user = findUser(req);        // User | null
  if (!user) {
    // User is null within this 'if branch' do whatever is appropriate.
    // Importantly, user.role is not accessible here.
    return ...;
  }
  // Because the 'if` branch returns from the function, we should be able to use
  // 'user' here knowing that it cannot be null.
```
But that might also explain why flow-typing tends to have a bigger pay-off for imperative languages. Which is another way of saying that functional languages already enjoy *some* of the benefits of flow-typing.

## Borrow Checking

I strongly agree here, I think there are two parts here:
1. Borrow checking is a very useful addition to the choices of manual-memory management and garbage collection.
2. As an added bonus, borrow checking can be used to prevent data-races.

I think the second one here is just the very definition of an added bonus. You *could* implement borrow-checking in a language that either has garbage collection or unchecked-manual memory management to prevent data races.

Regarding memory management. I agree with [Joel Spolsky](https://www.joelonsoftware.com/category/reading-lists/ceo/) who wrote (in 2010):
> A lot of us thought in the 1990s that the big battle would be between procedural and object oriented programming, and we thought that object oriented programming would provide a big boost in programmer productivity. I thought that, too. Some people still think that. It turns out we were wrong. Object oriented programming is handy dandy, but it’s not really the productivity booster that was promised. The real significant productivity advance we’ve had in programming has been from languages which manage memory for you automatically. It can be with reference counting or garbage collection; it can be Java, Lisp, Visual Basic (even 1.0), Smalltalk, or any of a number of scripting languages. If your programming language allows you to grab a chunk of memory without thinking about how it’s going to be released when you’re done with it, you’re using a managed-memory language, and you are going to be much more efficient than someone using a language in which you have to explicitly manage memory. Whenever you hear someone bragging about how productive their language is, they’re probably getting most of that productivity from the automated memory management, even if they misattribute it.

However, some tasks really do require manual memory management for various reasons. Before borrow checking, one was forced to choose between manual memory management, and all the bugs and security issues that come with it, or garbage collection, and all the performance unpredictability that comes with that. Borrow checking has represented an excellent compromise between the two. I still think that for many applications garbage collection is simply easier and more productive. But there are now precious few reasons to choose unchecked manual memory management over borrow checking.

## Contract Programming

Again I agree this is mostly a good idea. If you look at most of the examples that Pranoy gives most of them seem little better than a bit of syntactic sugar. Regarding asserts they write:
> But D also has `enforce` which is used to mark a difference in semantics. Asserts are used for program invariant violations. If an assert is triggered, this should indicate a correctness bug in our program. `enforce` instead throws an exception due to some external issue: something like a user input out of bounds or environment issue.

Well, sure, but some languages implement `assert` as an exception in the first place. When you do that, you can then choose to treat the situation as recoverable (as a normal exception) or not (as a traditional `assert`).

So then we move on to this example of post-conditions on a function:
```d
int daysInFebruary(int year)
out (result) {
    assert((result == 28) || (result == 29));

} do {
    return isLeapYear(year) ? 29 : 28;
}
```

This is pretty nicely *"executably documented"*. It's mostly syntactic sugar though, without this you could probably just write the conditions above the `return`, though you'd have to be careful to do that before **every** `return` in the function.

But then we get into class invariants, and there yes, although technically it's syntactic sugar for inserting the `assert` statements in all the right places, it's definitely cleaner, less error prone, and better at self-documenting. Pranoy writes:

> This invariant() block is far cleaner and easier to maintain than having some consistency check function run at the beginning and end of every class method, and it has idomatic meaning.

Agreed.
