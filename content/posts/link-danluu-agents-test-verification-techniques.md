---
title: "Link: Danluu: How well do agents use test/verification techniques?"
tags: [programming, link, llm]
date: 2026-09-14T14:42:23+00:00
---

Dan Luu, who is now fast becoming for me an unmissable blogger, has written-up another [excellent study in using coding agents](https://danluu.com/agentic-testing/).
In this post he explores how well coding agents make use of various testing and verification techniques when instructed to do so.
It's a fascinating read, highly recommended. The sort of tl;dr is: Agents are not really very good at using testing and verification techniques and when doing so their coding accuracy (on hidden tests) is not a significant upgrade on no particular instructions. In fact, most of the techniques under-performed the default of no instructions, and some increased the cost whilst providing no major benefit.

The setup is basically getting agents to write an implementation of Zstd. There are some hidden tests (never shown to the agents) which he uses to grade each implementation for correctness. The agents are also graded on cost.

> All implementations were in Rust. The 26 prompt conditions tested were ACL2, Alloy, "Audit and fuzz risky areas", "Audit first", Creusot, Default (no additional instructions), Differential testing, Fuzzing, Hegel, Insta, Judgement (agents asked to use the best technique), Kani, Lean 4, "Make no mistakes", Metamorphic testing, Mutation testing, Property-based testing, Proptest, QuickCheck, rstest, Rust built-in test framework, SMT solvers (with Z3, cvc5, and Yices, all available), Spin, TDD, TLA+, and Verus.


So there is quite a spread of techniques, and a couple of interesting 'controls' such as "Make no mistakes". The author also pre-registered some predictions, which were mostly predictions of a null result, which is mostly what happened. Here is what he says regarding the default:

> Default gave the agent no test or verification instructions.
> 
> Given what we've seen so far, it's not surprising that Default scored above average. Agents generally did things that were not useful when asked to use particular libraries or use particular test techniques. It stands to reason that not telling agents to do things that will make them do useless work does better than telling them to do things that will make them do useless work.

So the default just told the agent to write the implementation and didn't mention any testing or verification techniques to use, and it turned out that was above average. Which means that the instructions on testing and verification techniques mostly just added complications and noise.

Also reading through the analyses of the other instruction conditions, showed that the agents basically didn't use the prescribed techniques very well if at all. So these null results are not an indictment of the test and verification techniques themselves. Here for example is Dan regarding 'Alloy' a model checker:

> As we saw with Verus, agents using Alloy pretty much relied on standard Rust #[test] for correctness and mostly faffed about with Alloy. Once again, using a formal tool poorly did not help with correctness.

So what is happening is that the agents are basically doing the implementation as they would have, and then also adding an Alloy model file and *maybe* checking some trivial properties with it, such that the agent can claim to have used Alloy. So it's not the fact that using Alloy well doesn't help with an implementation of Zstd (it may or may not we do not know because) it's that the agents didn't use Alloy well. Similarly for most of the other test and verification techniques.

It's hard to draw concrete conclusions, but I would say this is a little bearish on AGI. I would expect an AI agent exhibiting AGI would be able to, for example, write useful property-based tests when given the instruction to do so, even if they also need the proptest manual. Here Dan states:

> For whatever reason, agents seemed to be somewhat better at using proptest, although the level of testing was well below what I'd expect out of a reasonable human who's read the proptest manual and is given some direction on how to test.

I read this as essentially saying that if some technique is well represented in the training data, and use of it is specifically trained, then the model can simply use it when asked. But, there is currently limited success from trying to explain to an agent how to use a technique and then expecting them to be able to do so.

I see a few implications/thoughts:
1. There is a debate regarding whether AI agents will be good for new/novel languages. Some thinking they are bullish because the eco-system gap can be made up using AI agents and also it's less of a risk to try out a new language since you can always have an agent later port your work if it doesn't work out. I view these results as being a little bearish for this idea.
2. The results here do *not* suggest that AI agents cannot use testing and verification techniques. It's only that 'prompting' and 'skilling' doesn't seem to work. You have to iteratively prompt them which still requires some kind of expert.
3. It is also bearish on the idea of a kind of 'prompt-store' or 'skill-store'. The idea is that if someone can just write down how to use a particular technique then those instructions could be given to any agent. But that looks in doubt given these results.
