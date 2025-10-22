---
title: "Links - Syntax Highlighting posts"
tags: [link, web, programming]
date: 2025-10-21T13:47:02+00:00
---

Syntax highlighting is having something of a moment. Three posts have popped up on my feed:
1. Niki is [sorry, but everyone is getting syntax highlighting wrong](https://tonsky.me/blog/syntax-highlighting/)
2. Words and Buttons speak about [Lexical differential highlighting](https://wordsandbuttons.online/lexical_differential_highlighting_instead_of_syntax_highlighting.html)
3. Hillel Wayne complains that [Syntax highlighting is a waste of an information channel](https://buttondown.com/hillelwayne/archive/syntax-highlighting-is-a-waste-of-an-information/).


## Sorry, but everyone is getting syntax highlighting wrong

In the first [post](https://tonsky.me/blog/syntax-highlighting/) Niki allows themselves to wander a little from the main point with several interesting syntax-highlighting related points. However, I think the **main** point is made with:
> Most color themes have a unique bright color for literally everything: one for variables, another for language keywords, constants, punctuation, functions, classes, calls, comments, etc.

> Sometimes it gets so bad one can’t see the base text color: everything is highlighted. What’s the base text color here?

and actually even better paraphrasing the Incredibles:

> If everything is highlighted, nothing is highlighted.

I find the metaphor of Christmas tree lights quite apt for some colour schemes.
Generally speaking I reasonate with this main point. Just because you can syntactically distinguish some part of your language, doesn't mean you have to highlight it.

In particular, keywords are often **highlighted**, I'm not saying they should not be styled differently, but keywords are pretty boring, dampen them back, so that I can read the *rest* of the code.

Note, it is important in some cases to style keywords differently. I code SQL with lowercase keywords, because the syntax highlighter does the same job as capitalising them does, and capitals are annoying to type. SQL is interesting because it has a lot of keywords, many of which I do not know, so in particular when reading someone eles's SQL code it's important to me that the keywords are styled differently. But, styling differently doesn't have to meant highlighting.

## Lexical differential highlighting instead of syntax highlighting 

In the second [post](https://wordsandbuttons.online/lexical_differential_highlighting_instead_of_syntax_highlighting.html) words-and-buttons talk about using colour schemes to make things which are similar but different **look** very different.

> What's worse, the standard approach to syntax highlighting doesn't help at all. It's fine that `mov` doesn't look like `eax`, but I'd rather prefer `pmulhw` and `pmulhuw` to be shown as differently as possible.

It's better to go and look at the actual post where the author has some sample code in their preferred syntax highlighting, but to give the idea here is some assembly code:

```asm
  imull  %eax, %eax
  movl  -8(%r12,%rbx,4), %ecx
  addl  $-1, %ecx
  imull  %ecx, %ecx
  addl  %eax, %ecx
```

In traditional syntax highlighting all the instruction names (`imull`, `movl`, `addl`) are coloured the same colour, which would be different from all the register names (`%eax`, `%r12`, `%rbx`, `%ecx`), and their point is that the positioning (and the `%` character) already do that work for us, so we can use colour to distinguish between names in the same lexical catagory (instructions or registers). So in the author's example, the `imull` instructions are all coloured the same, but that is different from all the `movl`, which is different again from the `addl` instructions. Similarly for the registers so that `imull %ecx, %ecx` somewhat stands out because both arguments are the same colour because they are the same register where as the arguments in `addl %eax, %ecx` are helpfully different.

In this post the author is careful to make similar looking names take very different colours, which seems useful. I've seen the idea of using the same colour for the same identifier, but not different identifiers before. A search online revealed [this post](https://zwabel.wordpress.com/2009/01/08/c-ide-evolution-from-syntax-highlighting-to-semantic-highlighting/), which may have been the one I was thinking of. If you look at the screenshot under the third heading there you can see a good example of choosing different colours for different variable names and how that might help comprehension of the code.

## Syntax highlighting is a waste of an information channel

Lastly Hillel Wayne discusses other uses for colour rather than highlighting the syntax:
> Color carries a huge amount of information. Color draws our attention. Color distinguishes things. And we just use it to distinguish syntax.
> Nothing wrong with distinguishing syntax. It's the "just" that bothers me.

More importantly he suggests using different highlighting modes for different tasks:

> The information we want from code depends on what we're trying to do. I'm interesting in different things if I'm writing greenfield code vs optimizing code vs debugging code vs doing a code review. I should be able to swap different highlighting rules in and out depending on what I need. I should be able to combine different rules into task-level overlays that I can toggle on and off.


He then discusses different possible uses for highlighting, I list them with my comments:

Rainbow parentheses
: This is a good use-case though I think most editors have plugins that do this, in neovim for example there is `"HiPhish/rainbow-delimiters.nvim"`

Context Highlighting
: Different levels of nesting. I feel like the indentation does this already for you. I guess it could be useful if you are in a non-significant whitespace
language, but even then I think you should use a formatter. It also means you need quite a bit of your code to be otherwise non-highlighted so that there is something to change on each scope level. Still I could see for some languages it might be a win.

Import highlighting
: Personally I almost exclusively use qualified imports so this wouldn't really help me. But maybe if I had import highlighting I wouldn't need qualified imports? I think I prefer the qualified imports, but I could see myself add a few 'bare' imported names if they were highlighted as such.

Argument highlighting
: "Arguments passed into the function are highlighted differently from local variables or global identifiers.", perhaps, but why? I might also say **global** variables should be highlighted.

Type highlighting
: "Highlight all list variables and integer variables with different colors." **Maybe**, this is a bit like the [wrong kind of hungarian notation](https://www.joelonsoftware.com/2005/05/11/making-wrong-code-look-wrong/), but maybe if you use colours it's okay? I'm somewhat skeptical of this one.

Exception highlighting
: Highlight functions that can raise exceptions. Cool, sounds like a good plan. The language could also help by enforcing some kind of naming convention, such as all functions that may raise an exception have to start with `exn`. So sort of hungarian-exception-notation. Hillel offers a couple of variations on this, and I would add general 'effect' highlighting, such as functions which can have side-effects. All of these have the small issue that what do you do if a function satisfies more than one of these conditions?

Meta data highlighting
: "Highlight functions that were directly called in the bodies of tests that failed in the last test run." so this is quite a dynamic/configurable one. Perhaps, though I think for these sort of things the squiggle-underlines is probably appropriate.


He also lists a few other random ideas which he didn't mock up. Which reminds me you should [read his post](https://buttondown.com/hillelwayne/archive/syntax-highlighting-is-a-waste-of-an-information/) as it has good mockups of these possibilities.


So yes, it's been a week or so of syntax highlighting posts. I think it's worth reviewing.
