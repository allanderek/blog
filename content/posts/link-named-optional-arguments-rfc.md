---
title: "Link: Named and optional arguments Proposoal"
tags: [ programming, syntax ]
date: 2026-09-23T12:20:21+00:00
---

A [very detailed and thorough post regarding named and optional arguments](https://botahamec.dev/named-optional-args), in particular a proposal to include them in Rust. Until reading this, I hadn't really thought of named/optional arguments as much of a big deal. I've used them in Python, but rarely, and of course Elm doesn't have them at all. I've always thought of them as being a small quality of life improvement but easy to live without them. Throughout this I'll use named arguments and optional arguments as interchangeable.

# Why Rust needs Optional Arguments

First the easy one:

>  Another problem that comes up is the fact that, when the parameters are unnamed, it can be easier to make mistakes. Consider the following print function.

> `fn print(text: &str, bold: bool, italics: bool, underline: bool);`

I do not find this a very compelling argument for the inclusion of a whole new feature by itself, but could be an added perk. In Elm, there are two ways in which we deal with such a scenario. The first is for the argument to take a single record type, so you effectively have named arguments.
```elm
print : { text: String, bold : Bool, italics: Bool, underline: Bool } -> String
print config =
    ... config.text ... config.bold etc.
```

The second is not to use `Bool`, but create custom types for the options:
```elm
type Bold = Bold | NotBold
type Italics = Italics | NotItalics
type Underline = Underline | NotUnderline
print : String -> Bold -> Italics -> Underline -> String
print text bold italics underline =
    case bold of
        Bold -> ...
        NotBold -> ...
```

Both have their advantages and disadvantages. The first is more difficult to partially apply, but that tends not to happen often in functions with many arguments.
The second tends to be disliked but without many concrete reasons. I understand it introduces a lot more boilerplate.

The author does anticipate the record tactic but dismisses it:
> And I don't see much reason to name a new struct if it's only going to be used for the one function.

But I don't see why? What's the inherently bad thing with defining a struct only to be used for one function? I'd argue that named arguments are doing exactly that, with admittedly less ceremony. In other words, named arguments are syntactic sugar for a single-use struct argument. It may even mean you're less likely to define a struct that could actually be used in multiple functions.

The more substantive argument for named arguments is that they allow to combine what would otherwise have to be separate function definitions. The example the author gives is a `HashMap` factory. However, in the full proposal the author notes that this particular `HashMap` example is not fully solved by named/optional parameters:

>  All of these functions are shown in the documentation, polluting the API. The number of functions is exponential with respect to the number of parameters. If we ignore the differences in generic parameters (a possible solution to which is discussed in the "Future possibilities" section), then we could imagine having a single function.
> 
> ```rust
> pub fn new(
> 	pub capacity: usize = 0,
> 	pub alloc: A = Global,
> 	pub hasher: S = RandomState,
> );
> ```

So the crucial point here is **if** we ignore the differences in generic parameters. The solution discussed in the "Future possibilities" section, **if** I understand correctly, would **also** work for having a default struct and doing the named/optional parameters that way. So I'm still not *overly* convinced that named/optional parameters are really anything more than syntactic sugar for a single-use struct argument. But *maybe* (or arguably haha) it is a worthwhile syntax sugar?


## Small points

The author really has put a lot of thought into this. It's worth going through this. Here is the author regarding making named arguments opt-in:

> Although many languages, such as Kotlin and C#, allow any argument to be named, this is not practical for Rust. Changing an argument is currently not a breaking change, but would become one as soon as named arguments are introduced. The solution is to allow authors to decide if their argument names are an implementation detail or not.

The author seems to regard 'breaking changes' as more serious than I do. In this case, when we talk about 'breaking changes' we mean changes that result in compilation errors. However, when you're changing a function, I'm not at all worried by the fact that all call-sites may be forced into changing their code. This is often a good thing. For example, if you add a new option parameter to the function, the author seems very keen that you can give that option a default (and that default result in the current behaviour), this means no consumers of your function need to change their code. If you used a struct, all call-sites would have to update for the change, but this would mean all call-sites would have to consider whether or not they want the default behaviour, that seems like a feature to me, not a bug.

It's also interesting to read the author's review of named/optional arguments in other languages.
