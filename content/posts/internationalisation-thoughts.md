---
title: "Internationalisation and automatic translation"
tags: [ software development ]
date: 2026-08-03T10:36:03+00:00
---

The following post [23 languages, one I can check](https://jva.lol/weblog/23-languages-one-i-can-check/) showed up on my feed.
The author talks about using `gettext` for internationalisation (i18n) and how they used an LLM to translate into 23 languages other than English, with only one of those 23 (German) being one the author could personally check. 

If you look into translation engines, such as `gettext` which the author is using, and ICU message format, you will find that there are a lot of differences between languages and dealing with these differences is tough. A particularly thorny problem is choosing the correct form of a sentence depending on the number of some noun. In English, we have it pretty easy, it's usually one for 1, and another for all other numbers. If zero is possible, that's often a special case as well, but it's also usually special cased in the actual functionality as well. For example, suppose you have a webstore, on a past order, you may have a button that allows the user to add all the items from that order to the current cart. In English there will be three cases 

| n | Sentence |
|---|---|
| 0 | Button doesn't exist | 
| 1 | Add item to cart |
| 2+ | Add all {number} items to cart |

Let's assume the 0 case has no text to translate. However, in Spanish we have more than the other 2 cases:

| n | Sentence | CLDR category | Noun form |
|---|---|---|---|
| 1 | Añadir el artículo al carrito | one | singular |
| 2 | Añadir ambos artículos al carrito | other | plural |
| 3+ | Añadir los *n* artículos al carrito | other | plural |

In Russian things are even worse:

| n | Sentence | CLDR category | Noun form |
|---|---|---|---|
| 1 | Добавить **товар** в корзину | one | nominative singular |
| 2 | Добавить **оба товара** в корзину | few | genitive singular |
| 3–4 | Добавить все *n* **товара** в корзину | few | genitive singular |
| 5–20 | Добавить все *n* **товаров** в корзину | many | genitive plural |
| 21 | Добавить все 21 **товар** в корзину | one | nominative singular |

Now in `gettext` you can mostly handle this, however, if I understand things correctly, then the `21` case is not solved and you will just have the incorrect form of the sentence.

But all of this brings up an important question. Translation of web pages by the user is relatively standard. Many people have a browser extension such as Google Translate installed. There are definitely some issues, in particular websites that work with a shadow dom or similar can have problems with an extension that changes the dom (like Google Translate). Nonetheless, I think it's worth asking, would the author of the above article be better simply writing their application in English and allowing those that need the translation to do the translation themselves in the way that they are used to?

The author is developing [Popsicle Boat](https://popsicleboat.com/), described as, A small social web for creators. So an obvious question arises, does the author wish those using the app translated into Ukrainian to be able to talk to those using the app translated into Thai? For a social network, *most* of what is on the website will be user content. Translating the shell of the application won't really make much difference if all of the content is not something they can read. Perhaps the author wants separate sites/instances/groups for each language, i.e. not expecting people who speak different languages to talk to each other. If not, then any user who needs the shell translated for them, will need the content also translated, so they will likely be using some translation extension anyway. If that's the case it could do the translation of the shell at the same time.

There are some obvious disadvantages of both approaches:
1. If the user does the translation it gets done a large number of times, whereas if the application developer does it, it is done only relatively infrequently (perhaps once per deploy).
2. Context is often key for translating a single word such as "Post". This could mean the LLM attempting to translate the author's `.po` files without context will make mistakes, but perhaps the LLM is given the full context (i.e. can look at the source code and see where each translation string is used). Perhaps, it's actually more difficult for the user's translation extension to get it correct. But it could also be the other way around.
3. If the application developer does it, they *could* fix mistakes when users report them.
4. If a potential user doesn't have a translation extension installed they won't be able to read it at all.
5. Maintaining the translation scheme in the source code is a slight bit of friction for the application developer, that friction is helped by coding agents.
6. That friction may be helpful in some ways.

I'm sure there are further advantages / disadvantages.

Overall, it's not clear to me that the effort of translating the application shell is worth it. It's also not clear that it is *not* worth it.
So it is a difficult decision. I say this as someone who created a translation scheme for Elm applications and used this for web stores. We fortunately only needed to support two languages, English and Spanish, that were close enough we didn't really brush up against any of the thornier issues. We also had native speakers of both languages on the team and caught any issues pretty quickly.

One thing that coding agents now give, is the ability to refactor a codebase to use i18n. A large reason for writing our own scheme was that we thought it would be absolutely miserable to refactor a codebase to use i18n after years of development without it. I think I was correct in that assessment, but now with coding agents that refactor could probably be done relatively painlessly.

For this reason, when developing new applications, I simply develop assuming no translation will ever be required. If at a later date we make the decision that by-developer translations are required, we'll tackle that then, and can use coding agents to make any refactor relatively painless.

