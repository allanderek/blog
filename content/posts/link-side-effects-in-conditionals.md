---
title: "Link: Keep if-clauses side-effect free"
tags: []
date: 2026-10-02T11:23:13+00:00
---

Interesting small post from teamten concerning [keeping side-effects out of if-clauses](https://www.teamten.com/lawrence/programming/keep-if-clauses-side-effect-free.html). I think this post is getting at something important, but I'm not *quite* sure the framing is exactly correct. Here is the main point:

> Avoid writing if clauses that have side effects:
>
> ```java
> if (enqueueMessage(message)) {
>     ...
> }
> ```
>
> The only function of an if statement is to test whether a condition is true. It’s not for executing code as a side-effect of the test. One problem with using the return value directly, as in the above, is that the meaning of the returned value is unclear. Does enqueueMessage() return true if the message was enqueued or true if the queue is full? Make it explicit by using a variable:
> ```java
> boolean success = enqueueMessage(message);
> if (success) {
>     ...
> }
> ```

Of course, I agree with this. But I **think** the framing is slightly off, but maybe useful.
Let me first explain the framing and then why it might nonetheless be useful.

Basically, the framing is off, because the problem is that side-effects are allowing the function to do two things, and that makes naming it awkward.
Because the 'result' of the function is a side-effect, that is, for example adding something to the queue, the actual return value is used to indicate status, such as whether the item was actually added to the queue or not. In a language (or just a function) without side-effects, we would be forced to return the new queue, so we would have to encode the status in the return value. Which probably means the code would look something like this:
```elm
case enqueueMessage message queue of
    Added newQueue -> ...
    QueueFull -> ...
```

In which case the naming of the function is fine. So the problems with naming are a symptom of the side-effect allowing for essentially two separate return values (one of which is the side-effect). Note also, that this isn't restricted to if-clauses. If the `enqueueMessage` function returns the *number* of messages added to the queue, you get a similar issue:
```java
int added = 0;
for (message in messages) {
    added += enqueueMessage(message);
}
```

That seems fine, unless some kind of error, such as the queue being full, is returned as -1, maybe -1 means the queue was full, and zero means the message was already in the queue. This is basically the same problem but doesn't use any if-clauses. But I agree that if-clauses is probably where this issue is more likely to manifest itself.

In summary, the main problem is that side-effects, allow your function to sneakily return more than one thing.

As I said, the framing is perhaps useful. I think what this suggests is that you shouldn't write functions (or methods) that sneakily return more than one thing. However, if you're in the situation where you're consuming an API/interface that has made that mistake, then the advice to keep side-effects out of if-clauses is good. As demonstrated above, the problem may manifest itself outwith an if-clause, but by keeping that in mind you're more likely to catch that problem as well.

The [post](https://www.teamten.com/lawrence/programming/keep-if-clauses-side-effect-free.html) is short and worth reading, including showing this code:

```java
if (!categorySeen.add(categoryID)) continue;
```

Which I agree is pretty unreadable.


