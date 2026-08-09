---
title: "Video Link: Reliability lessons from SQLite at Software Should Work"
tags: [ software development, SQLite, video link ]
date: 2026-08-07T11:08:51+00:00
---

[Video Link: Reliability lessons from SQLite at Software Should Work](https://www.youtube.com/watch?v=V_qzqY1bb7I)

Richard Hipp the creator of SQLite, clearly one of the best pieces of software in the world, gives a talk on reliability lessons from SQLite.
This is very good talk that is well worth watching.

There is a certain kind of time-warped feel to this talk, Richard discusses several testing strategies that I think have been at least in the standard vocabularly for two to three decades, if not always standard practice. He sometimes seems to kind of refuse to use the standard vocabulary for these things, I wonder if he kind of independently discovered these things himself. Again though, it's well worth watching, the reliability techniques he points out are things *most* seasoned software developers would already know about, but still he is essentially saying "these are the most important things for SQLite". There are hundreds of relability techniques that software developers already know, picking out the most important ones for a piece of software as successful as SQLite is a great way to prioritise what you already know.

## Mocking

He has a section towards the start where he talks about what is essentially mocking. This is an important practice for testing and particularly important for software that requires a high degree of reliability. But he never (I think) uses the verb 'mock'.

## Rubber Ducking

Again he describes this phenomenon and I think uses an original comic (i.e. one he has produced himself) to describe it, but I suspect 90% (and maybe even 100%) of the audience would have immediately known what he was talking about if he had simply said 'rubber ducking'.

## Mutation testing

Here is the example he gives that he describes as problematic for mutation testing. It is a hash function for strings:

```c
unsigned int strHash(const char *z){
    unsigned int h = 0;
    unsigned char c;
    while ( (c = (unsigned char)*z++) != 0 ) {
        h += sqlite3UpperToLower[c];
        h *= 0x9e3779b1;
    }
    return h;
}
```

If the mutation tester changes the condition `!= 0` to an unconditional jump (or even if you just change it to `==`, which is more likely for a mutation tester, though not sure what happens with the empty string), then what happens is this function always skips over the loop and we always return 0 (since that's what `h` is initialised to).

He states that this is problematic for mutation testing because in that case all strings will hash to zero, but then the hash table (which deals with collisions) will degenerate in to a linked list. The problem is that the tests will not fail, because although the hash table degenerates into a linked list, it's still giving the correct answer, so none of your tests fail.

However, I think this is not problematic at all. I think this is a massive advertisement for mutation testing. If the mutation tester does this, and your test suite only tests the correctness of the **hash table** (rather than the hash function directly) then the mutation test will highlight a shortcoming of your test suite. The mutation test will fail saying "I modified this condition and none of your tests failed". That's great, it's telling you that you do not have a test for the hash table degenerating into a linked list.

The fix is to include a test for the hash function itself. A simple test would hash some set of strings and checks that they do not all (or some high proportion) hash to the same value. If you add that test function to your test suite then it would fail under the proposed mutation and the mutation tester would be happy. So I don't really understand why Richard thinks this is problematic.  You would want a test that checked your hash table has not degenerated into a linked list. Mutation testing has correctly alerted you to the fact that you don't have a test for that.

He generalises this with some pseudo code:

```c
if (shortCutWorks() ) {
    FastShortCutCase()
} else {
    SlowerGeneralCase()
}
```
Since `SlowerGeneralCase()` always works it is difficult to detect false-negatives in `shortCutWorks()`.
But again, this just means that you aren't directly testing `shortCutWorks()` and mutation testing would correctly alert you to that fact.

Hash functions can [be quite hard to test](/posts/link-ned-batchelder-testing-conundrum/). 

## More

There is quite a bit more in the talk worth watching. He talks about full 'MCDC' testing (modified condition/decision coverage) and gives a usefully simplified version of that. He also talks about fuzzing and asserts. I hadn't known that Richard had clashed with the Go lang development team and in his words:
> They agreed to tone down their rhetoric towards assertions and I agreed to tone down my rhetoric towards Go.

This is what the [go lang faq as to say about assertions](https://go.dev/doc/faq#assertions):
> Why does Go not have assertions?
>
> Go doesn’t provide assertions. They are undeniably convenient, but our experience has been that programmers use them as a crutch to avoid thinking about proper error handling and reporting. Proper error handling means that servers continue to operate instead of crashing after a non-fatal error. Proper error reporting means that errors are direct and to the point, saving the programmer from interpreting a large crash trace. Precise errors are particularly important when the programmer seeing the errors is not familiar with the code.
>
> We understand that this is a point of contention. There are many things in the Go language and libraries that differ from modern practices, simply because we feel it’s sometimes worth trying a different approach.

That does sound as if it has been rather toned down from a more aggressive stance. I find myself with Richard on this one.

I will say he is an advocate for production builds with asserts compiled out (he says they are a 'no-op', but I presume they are compiled out entirely).
Tony Hoare once compared compiling-out asserts for production builds to a sailing enthusiast who wore a life jacket whilst training on dry land and then took it off before putting out to sea. Richard's talk sugggests that SQLite performs 4x faster with asserts compiled out. That is pretty compelling. I'll also say that I assume developers are a lot more liberal with asserts if they assume they will be compiled out for production builds. If one does not have to trade-off any performance penalty for the extra documentation provided by the asserts I imagine one uses them more liberally.

I do not know whether asserts should be compiled out for production builds or not, seems like an unsettled question.

I will say that I've often longed for an 'assert' **statement** in purely functional languages, such as Elm. Elm of course does not have any statements, nonetheless I could imagine an 'assert' statement that can be dropped in to any place in the code. It would have to be designed well.

There is also some brief talk on the use of LLMs for programming.

## Generally

I think the general theme of this talk is that we have a bunch of good practices but that each one must be used mindfully. Mutation testing does indeed test your test suite, but if you understand it deeply you will get more out of it, than simply pressing the button to go. This is also true of test suites in general, source code control (which he touches on), asserts, fuzzing and LLMs.

Lastly, this talk is very inspiring for anyone that wants to produce very reliable software, perhaps even software described as bulletproof.

