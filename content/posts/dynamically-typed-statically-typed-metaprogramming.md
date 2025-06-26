---
title: "Dynamically/Statically typed language and meta-programming"
tags: ["programming"]
date: 2025-03-28
---

The following was written for a colleague who suggested I post it more publically, so here we are.

We're going to compare dynamically and statically typed languages in the context of writing admin panels for a variety of data stores. We assume that the data is actually stored within a relational SQL database, but that's not important because we further assume that we need to send/receive JSON data.

## First a  point of terminology

This section is skippable, but defines the difference between the statically-dynamically and weakly-strongly typed axes. If you're sure you know, you can skip this.

There are two axes on which type systems are categorised which are often confused.
The first axis is strongly vs weakly typed systems, this regards how strongly the types are enforced, not **when** then are enforced.
The second axis is statically vs dynamically typed system, this regards **when** the types are enforced, it's important to note that you can have any combination of these two.

Consider the expression:
1 + "2"

In a strongly typed language this would result in an error. In a weakly typed language, this would be evaluated, the result would depend upon the choices the language made for casting types in such expressions but it could commonly result in the string "12", or sometimes the integer 3.

Assuming this a strongly typed system, a statically typed language would not allow this at compile time and wouldn't allow the program to be run. A dynamically typed language would allow the program to be run, but, if this expression is ever evaluated in a particular run of the program, it would raise some kind of error. How the error is raised depends on the language, it might be a catchable exception, or it might simply halt the program with an error.

Note that it is possible to have a weakly-statically typed language, but it is less common as the use cases are not entirely clear but they tend to be low-level, C for example is arguably a statically-weak type system.

Note, as well I say 'arguably', although we tend to treat these two axes as binary, they are of course a spectrum. For example, most statically typed languages that allow array access `a[10]` do **not** check at compile time if the array `a` is of at least length 11. Some insert a runtime check, so in that sense the language is not fully statically typed. It is possible to have a language that **does** check at compile time if the array index is always valid.

## Example scenario

Suppose we want to write a web form for updating a row of the database. Let's assume each column can be either an integer or a string. We receive the row to update as JSON, and must output a form with fields for each of the columns.

The first thing to understand is how, at runtime, such a row would be represented. Let's start with an example row, suppose it arrives as JSON as `{ name: "allan", number: 1 }`. In both dynamically and statically typed languages, this row may be represented by some object defined by a class, or some other complex data structure, but ultimately this information is stored as a record/struct type. The difference is, the dynamically typed language stores the whole record including the names of the fields. How it does this depends on the language, but you can think of it as a map from string to 'value', where value can be anything (but remember, that anything will also be storing the type of itself.) So you can imagine it looks something like this in memory:
```
( type-struct
   [ ("name", (type-string, "allan")
   , ("number", (type-int, 1))
   ]
)
```

Now in the dynamically typed language, when you encounter an expression such as:
`row.name` it can first check if `row` is a `type-struct`, if not then it raises an error. If so, then it checks if in the mapping there is a pair in which the first value is `name`, if not then it raises an error. If so, then it returns whatever the second value of that pair is, in this case `(type-string, "allan")`. Presumably after the access you wish to do something with that value, but whatever that is, it has the type information with it, so it can decide if that something is valid (e.g. printing it out to the screen would be valid, adding it to the integer 1 would raise an error.)

In the statically typed language, you would have to define a type for the row [footnote 1]. You might define it as `type alias Row = { name : String, number : Int }` The representation of the same struct (`{name: "allan", number: 1})` would simply be a two word long heap allocated value `["allan", 1]` (of course actually the value `"allan"` would likely be a pointer to a slice of bytes in memory). When the **compiler** encounters an expression `row.name` it outputs code which assumes `row` is a pointer to some memory and simply takes the first word of that, so equivalent to `row[0]`, it knows that the `name` field of a value of that kind of struct is stored in that position, because it has control of how all such values are created, it just always puts the name field in position 0.

## Decoding

In a dynamically typed language we can simply say `JSON.parse(value)` why does this work? Because it can produce the in memory version of the row we saw above:
```
( type-struct
   [ ("name", (type-string, "allan")
   , ("number", (type-int, 1))
   ]
)
```

But if the JSON is different it can simply produce a different struct with all the type information, depending on what the json is, for example if the JSON happened to be `{league_position: 1, team: { name: "Celtic", founded: 1888 }}` then it can produce the value:
```
( type-struct)
    [ ("league_position", (type-int 1))
    , ("team", (type-struct ([ ("name", (type-string "Celtic"), ("founded", type-int 1888))])))
    ]
```

Now if we then did `row.name` again, in the first case, that would work, but in the case the interpreter would raise an error because the struct doesn't contain a 'name' field at the top-level.

In a statically typed language we cannot simply do `JSON.parse(value)` [footnote 2], because we cannot just create any value, we must create a value of type `Row` which has the correct layout in memory, because when you wish to do something with that value, e.g. `row.name` the compiler will have omitted code assuming that there is a string value at position 0 of the `row` value. So you have to tell the compiler how to do that given **arbitrary** JSON. That's where Elm json decoders come in. In other words the parser for the JSON value is specific to the type of value you wish to create. 

A succinct way to put all this is that:
1. In a dynamically typed language given arbitrary JSON you can just create a value of arbitrary type, since all the type information is stored with the value.
2. In a statically typed language, you cannot do that, since you must create a value of the type expected since all the rest of the code depends on that.

Now, of course, if you create an arbitrary value it might not be the type that the rest of your code is expecting and you may get a run time error. That is why people like statically typed languages, you **fail fast**, if the JSON is not of the correct shape, your decoder fails. In a dynamically typed language you can validate the JSON, but if not, and the JSON is not of the correct shape, then something will fail later and it's not always obvious what or where.

## Outputting a form.

In a dynamically typed language all the type information must be kept with all the values at runtime, so that the runtime can check operations are appropriate (strong typing) or do the best it can (weak typing). Because the runtime needs to inspect the types of values at runtime, often the programmer is afforded that option as well. I'll invent a syntax similar to Python's for doing this, it varies from language to language and some are homoiconic (where code and data share the same representation) they don't need a special syntax for it, but anyway.

Let's suppose that for any value `v` you can inspect the fields it has by writing `v.__fields__` if the value is not of type `type-struct` then it just returns the empty list. Otherwise it returns a mapping from string to value. Additionally, we can also simply ask `typeof(v)`, which in our little language will return one of `type-struct`, `type-int`, or `type-string`.

I'm also going to assume some kind of templating here to output the HTML values:

Let's say we wish to output a form, suppose we have a row, which has been collected from some request:

```
row = JSON.parse(request.data)
for (field, value) in row.__fields__:
    if typeof(value) == type-int:
        <label>{field}</label>
        <input type="number" name="{field}" value="{value}">
    elif typeof(value):
        <label>{field}</label>
        <textarea name="{field}">{value}</textarea>
    else:
	    # We ignore sub-structs, or any other type.
	    continue
```

I used a textarea for the string fields just to make it a bit more different to int fields. The point is, we can take **arbitrary** JSON and output a form for updating it, without knowing what the shape (or schema) of the JSON might be. 

### Statically typed language

In a statically typed language, we don't really have anyway to do this. There are two solutions:
1. If we know at compile time the schema of the JSON, then we can (manually  or using codegen) create a type and decoder for that schema of JSON, and then write a specific function to output an update form for that type of data. Again, we could use codegen to output such a function. But what we wouldn't be able to do is handle any JSON we didn't know about at compile time.
2. Create our own 'arbitrary JSON' type, and decode into that. 

For number two, assuming that we expected only 'flat' JSON, no nested structures we could do the following:
```
type JsonValue
   = JsonInt Int
   | JsonString String
type alias JsonStruct =
   List (String, JsonValue) # or Dict String JsonValue if we prefer
```

If we wished to allow for nested structs you can do:
```
type JsonValue
   = JsonInt Int
   | JsonString String
   | JsonStruct JsonStruct
type alias JsonStruct =
   List (String, JsonValue) # or Dict String JsonValue if we prefer

```

Note that these two are mutually recursive, but let's stick to the first version since we didn't allow nested structs above for the dynamically typed language, assuming we have some decoder for this type (which accepts arbitrary json but presumably ignores nested structs), we can do:
```
row : JsonStruct
row = jsonParseRow(request.data)
for (field, value ) in row:
   case value of
	   JsonInt i ->
	        <label>{field}</label>
	        <input type="number" name="{field}" value="{i}">
	   JsonString s ->
        <label>{field}</label>
        <textarea name="{field}">{s}</textarea>
```

### Why is this bad?

Suppose I have two rows and I want to add together their numbers? In the dynamically typed language I can simply do: `row1.number + row2.number`, done.

In the statically typed language, I have to write a function to add together two values of type `JsonValue`:

```
addJson : JsonValue -> JsonValue -> JsonValue
addJson left right =
   case (left, right) of
      (JsonInt l, JsonInt r) ->
          JsonInt (l + r)
      (JsonString l, JsonString r) ->
          JsonString (String.cat l r)
       _ ->
         ??? raise some kind of error or maybe I can match
         ??? JsonInt l, JsonString r and produce "12" or whatever.
```

The point is, I'm now implementing an interpreter for a dynamically typed language. I've lost the statically typed guarantees that I will never attempt to add a string to an int. You can bet that my implementation of the interpreter will not be as good as the one for Python, Lisp, Ruby, or whatever. 

## Non solutions

Macros do not solve this. Macros are really just a way to write custom syntax sugar, but you cannot write anything in macros that you cannot write without them.

Codegen half solves this. It means you can write one generic code generator, that takes as input the JSON schema, and outputs all of:
- A `Row` type
- A JSON decoder that produces values of type `Row`
- A function that outputs a form from a value of type `Row`

But you still need to know at codegeneration (i.e. at compile time) the schema of the JSON. You cannot codegen your way to accepting arbitrary JSON and generating an arbitrary form for that JSON.

## Footnotes
1. Elm is a little different here, it allows extensible and anonmous record types. That is because it compiles to the dynamically typed language Javascript. Even without that it **could** figure out how to achieve this but it would be a whole program transformation. But anyway, it's mostly by-the-by. The point is, the statically typed language code cannot *inspect* the type of a value at runtime, because that information is not stored together with the value. 
2. Technically we could do that, but it would still involve either manually or automatically creating a decoder that parses the JSON and creates the correct value in memory.
