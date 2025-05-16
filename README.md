# Kantor Interpreter

## Overview

Kantor is a declarative language designed for defining, manipulating, and querying data primarily through set-theoretic concepts. It allows users to:
*   **Define custom data structures** (records) with named fields and associated types.
*   **Work with collections of data as sets**, ensuring uniqueness of elements.
*   **Perform common set operations** like union, intersection, and cross product.
*   **Construct new sets from existing ones** using powerful comprehensions, which include filtering, transformation, and destructuring of elements.

The language aims to provide an expressive and mathematically-grounded way to interact with structured data.

## Core Features

*   Define custom data types (records).
*   Create and manipulate sets of data (numbers, strings, tuples, records).
*   Perform set operations: Union (`|`), Intersection (`&`), Cross Product (`*`).
*   Use set comprehensions for powerful data querying and transformation.

## Project Files

*   `keval.py`: Main interpreter and evaluator.
*   `klexer.py`: Tokenizer.
*   `ktokens.py`: Token definitions.
*   `kparser.py`: Parser.
*   `kast.py`: Abstract Syntax Tree definitions.

## How to Run

1.  Ensure you have Python 3.x installed.
2.  Navigate to the project directory in your terminal.
3.  Run the main script:
    ```bash
    python keval.py
    ```
    This will execute an embedded test suite, showing each Kantor statement and its result.

## Example Kantor Snippet

```kantor
type Item: Record(id: int, category: string)

let Inventory: Item = {
    (id: 1, category: "Fruit"),
    (id: 2, category: "Dairy")
}

let FruitItems: Item = { item | item of Inventory, item.category == "Fruit" }
```