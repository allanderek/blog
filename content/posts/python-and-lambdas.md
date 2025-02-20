---
title: Python and Lambdas
date: 2017-02-10T14:39:20Z
tags: ["python", "lambda"]
---
I come from a functional programming background, so I a lot of love for functions and so-called anonymous functions or lambdas. However, I have realised that I don't make use of Python's lambda syntax much, and I wanted to articulate why. This may mostly sound pretty negative towards lambdas, but bear in mind I'm certainly not against lambdas in general.

A `lambda` expression could always be avoided by simply defining the function in question. So the question becomes when is a `lambda` more readable than a definition? That is almost always because the function you're attempting to create is so simple that the definition syntax gets in the way. It is often used when the function in question is going to be used as an argument to some method. For example the `sort` method on a list takes as argument they `key` to be used when comparing the elements. So if you have a list of items and you want to sort them by their prices you can do something such as:

```python
list_of_items.sort(key=lambda x: x.price)
```

We could of course have gotten the use of `lambda` with a definition:

```python
def price(item):
    return item.price
list_of_items.sort(key=price)
```

This is not **quite** equivalent because it introduces a new name into the current scope that would not otherwise have been there, but I don't ever recall reaching for a `lambda` expression in order to avoid polluting the name space.

We could even define a generic higher-order function to make a function out of attribute access.

```python
def f_attr(attr_name):
    def attr_getter(item):
        return getattr(item, attr_name)
    return attr_getter

list_of_items.sort(key=f_attr('price'))
```

This is surely worse than the first two attempts, but if you have multiple sorts to do, then using definitions can get tedious:

```python
def price(item):
    return item.price
list_of_items.sort(key=price)
do_something(list_of_items)

def quantity(item):
    return item.quantity
list_of_items.sort(key=quantity)
do_something(list_of_items)

def margin(item):
    return item.margin
list_of_items.sort(key=margin)
do_something(list_of_items)
```

as compared with the lambda version:

```python
list_of_items.sort(key=lambda x: x.price)
do_something(list_of_items)
list_of_items.sort(key=lambda x: x.quantity)
do_something(list_of_items)
list_of_items.sort(key=lambda x: x.margin)
do_something(list_of_items)
```

The `f_attr` version is similar:

```python
list_of_items.sort(key=f_attr('price'))
do_something(list_of_items)
list_of_items.sort(key=f_attr('quantity'))
do_something(list_of_items)
list_of_items.sort(key=f_attr('margin'))
do_something(list_of_items)
```

In fact that could be done with a loop:

```python
for attribute in ['price', 'quantity', 'margin']:
    list_of_items.sort(key=f_attr(attribute))
    do_something(list_of_items)
```

I think the `lambda` version is at least sometimes more readable. However, I often miss the self-documenting nature of a definition, in that giving the function a name acts as some pretty decent documentation especially for the kind of simple function you might otherwise use a `lambda` expression for.

So, for a `lambda` expression to be the right choice, the function in question has to be so simple as to not benefit from the extra documentation afforded by its name (such as simple attribute access). 

I just don't seem to find myself in that situation very often. Perhaps I'm just not making my own functions general enough by accepting functions as arguments.

