---
title: "Functors revisted with comby"
tags: ["elm", "programming"]
date: 2025-07-02
---

I [have previously described](/posts/poor-persons-functors) using `sed` to hack together a "poor-person's functor" to overcome an awkwardness encountered
when using [elm-program-test](https://package.elm-lang.org/packages/avh4/elm-program-test/latest/) to simulate HTTP events in the program being tested.

To recap briefly the issue is that using elm-program-test, means that the `update` function returns an `Effect` rather than a `Cmd Msg`.
When we apply this `update` function to `Browser.element|document|application` we need to create a function,`perform`, which translates the `Effect` type into a `Cmd Msg`. The reason we do this, is because for testing we instead create a function, `simulate`, that translates the `Effect` into a `SimulatedEffect` which can be simulated by `elm-program-test` and also interregated to test that we have produced the intended set of `Effect`s for the test in question.

The awkwardness is the fact that the `perform` and `simulate` functions are basically exactly the same, except that one uses functions such as that provided by `Http` (from elm/http) and one uses the equivalent functions from `SimulatedHttp` (part of elm-program-test), and similarly for other kinds of effects including ports.

This is a great scenario in which to use Ocaml/SML style functors. Since mostly what is changing is the imports.
Since Elm does not have functors, I hacked together a system using `sed` which means that the user can write the `perform` function (in its own module) and have that module automatically translated into a `Simulate` module.

## Comby

My `sed` scripts to do this were becoming a little unweildy. So I looked into other solutions and came across [comby](https://comby.dev), which somewhat appropriately is built using Ocaml.
I have found this quite workable. Comby can be simply called on the command-line, but you can also store your patterns and replacements in a configuration file in `toml` format. Here is the first part of the `perform-to-simulate.toml` file I use to translate my `Perform` module into an equivalent `Simulate` one.

```toml
[perform-module-update]

match="module Perform exposing (perform)"
rewrite="module Generated.Simulate exposing (simulate)"

[perform-decl-update]

match = '''
perform : { a | navigationKey : :[type] } -> Effect -> Cmd Msg
perform model effect ='''
rewrite = '''
simulate : Effect -> SimulatedEffect Msg
simulate effect ='''

[perform-recursive-call]

match = "(perform model)"
rewrite = "simulate"
```

So the first part simply translates the module definition at the top of the module file. I generate a module under the `Generated` directory mostly because then it is easy to ignore that folder for source-code-control purposes.

In this particular project the `simulate` function doesn't actually need the `model`. The `perform` function does because it needs the navigation key to actually perform `Browser.Navigation.push|load|reload`, but the simulated version doesn't require a navigation key. This means that we translate the function signature, definition-line, **and** any recursive calls. The recursive calls are typically just to implement `Effect.Batch`, which is how we make a single `Effect` from multiple effects.


You can see the [whole comby file (perform-to-simulate.toml) here](https://github.com/allanderek/elm-and-python-template/blob/main/perform-to-simulate.toml)

Lastly here is a part of the Makefile to run the tests, it depends on the generated modules (there are two, a `Simulate` one which depends on a `Ports` one), which in turn depend on their non-simulate counterparts, the `Perform` and `Ports` modules.

```make
GEN_TESTS_MODULES_DIR = ./tests/Generated
SIMULATE_MODULE = $(GEN_TESTS_MODULES_DIR)/Simulate.elm
PORTS_MODULE = $(GEN_TESTS_MODULES_DIR)/Ports.elm

$(SIMULATE_MODULE) $(PORTS_MODULE): src/Perform.elm src/Ports.elm perform-to-simulate.toml
	cp src/Perform.elm $(SIMULATE_MODULE)
	cp src/Ports.elm $(PORTS_MODULE)
	comby -config perform-to-simulate.toml -d $(GEN_TESTS_MODULES_DIR) -in-place -matcher .elm

# Frontend tests (Elm)
frontend-test: $(SIMULATE_MODULE) $(PORTS_MODULE)
	@echo "Running frontend tests..."
	elm-test
```

The interesting line here is `comby -config perform-to-simulate.toml -d $(GEN_TESTS_MODULES_DIR) -in-place -matcher .elm`.
