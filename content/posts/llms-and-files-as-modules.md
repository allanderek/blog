---
title: "AI agent programming and files as  modules"
tags: ["compilation", "language-design", "llms", "agents" ]
date: 2025-07-03
---

For a long time [I've been sceptical that using the file system to denote modules](/posts/files-as-modules) in a programming language is necessary.
There are many good reasons to do this as things currently stand, but most of these reasons can, and arguably should, be solved with better tooling.
For example from the post linked to above:
> why would we equate a file to a form of encapsulation? Why, would we wish to divide any application into a bunch of files in the first place. If you ask this question, you get a bunch of answers, but they mostly fall into two categories: 1. some vague notion about organisation and modularising your code and 2. it is easier to navigate whilst coding. I would argue that the first is nonsense, since no one is arguing against modularising code, only that the file system does not need to come into it. The second is potentially true, but rather speaks to a deficiency in your coding environment (text editor/IDE) rather than to the efficacy of using files to modularise a program's source code.

So my thesis is that modularising code is a great idea, but there is no compelling reason to tie the modularisation of your code to the file system.
Ocaml for example allows for nested modules within the same file, so you could if you wish write your entire project in a single file. 

A new reason to split your code into separate files has emerged this decade. Programming with LLMs and now agents (tools in a loop).
The context is what matters here. It is relatively easy to put an entire file into the context. However, often a project is large enough that it is too large to put the entire project into the context. So this might lead one two split code into many smaller files that can easily be put into the context. 

A counter point to this argument is similar to the common response to arguments for splitting code across multiple files. This is mostly a tool issue. It could be solved by models gaining larger and larger context, but even today could be solved by providing a tool that the agent can use to extract a portion of a file into the context. In fact, doing this might make context more manageable. If all your modules are in one file, and delineated by syntax, it is pretty simple to write a tool that, given the name (or path) of a module can return just the source code of that particular module. In fact, we should be doing this generally for other syntax elements. For example we should have tools which can return a particular type definition, or function declaration. We could similarly extend this tool to allow **updating** (or deleting) syntactical elements. This is generally what the agents are doing, they are just cobbling together common command-line tools, such as `rg` to do so.

Another argument one might give for splitting code into multiple files is that it makes it relatively easy to refer to particular code when prompting the agent. One might say something like "Okay now use that new auxiliary function to refactor the code defined in src/View/Post.elm". But again, I see no reason why one could not prompt with simply the module name "Okay now use that new auxiliary function to refactor the code in the module View.Post".


One final point that is a bit more compelling. Concurrent editing. Sometimes agents can be given a task that may take some time to complete, of the order of a few minutes to a few hours in some cases. Whilst the agent is off doing that, one can be busy (either using another agent or entirely manually) with some other task, such a refactoring some code. I still believe this is doable if everything is in a single file, for example you could use a separate checkout of the repo, but I admit that it might be more ergonomic to simply work on a file that the agent won't need to modify.

Still overall, I think I'm sticking to my conviction that there is no particularly compelling reason that we still split our code into separate files.
