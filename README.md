# Lox Interpreter in python (pyLox)

This project is simple, just converting from Lox(java) to pyLox(python)
Lox from [Lox Interpreter](https://craftinginterpreters.com/)

## Challenges things?

## Chapter 6 : Parsing Expression

- [ ] Added Comma Operator
- [ ] Added the Ternary Operator.
- [X] Error reporting on binary operators missing a left-hand operand.

## Chapter 7 : Evaluate Expression

- [ ] Added comparison operators to strings, chose not to allow comparison between mixed types.
- [ ] Added support for concatenating strings and numbers.
- [X] Error report for division by zero.

## Chapter 8 : Statement and State

- [X] REPL now works in the following way: statements are executed, while expressions are evaluted and displayed.
- [X] Accessing an undefined variable is now a runtime error.

## Chapter 9 : Control Flow

- [X] Support break statement

## Chapter 10 : Function

- [ ] Lambda/Anon functions are now supported.

## Chapter 11 : Resolving And Binding

- [ ] An unused & defined variable now raises a runtime error.
- [ ] Changed implementation of an environment to a list instead of a dictionary.


## Chapter 12 : Class

- [X] Added metaclasses, and through them added support for class methods.
- [X] Added support for get methods - more info here.

## Example/Samples

You can find more example on example folder
this are one example we can provide.

```python
class Animal {
  talk() {
    print "Generic animal talk";
  }
}

class Dog < Animal {
  talk() {
    print "Bark";
  }
}

class Duck < Animal {
}

class Squirrel < Animal {
  talk() {
    super.talk();
    print "Not that generic, this is a squirrel";
  }
}

var d1 = Dog();
d1.talk();

var d2 = Duck();
d2.talk();

var sq = Squirrel();
sq.talk();

```

## License

Under [MIT](https://choosealicense.com/licenses/mit/)