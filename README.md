# Hierarchical Babel

A small, self-contained Library of Babel written in Python with a Tkinter GUI.

The library contains pages of **512 characters**, using the **95 printable ASCII characters**. You can search for text, get its address, or browse the library page by page.

## Requirements

* Python 3.10+
* Tkinter

## Run

```bash
python babel.py
```

## Features

* **Search** for text and get the corresponding page.
* **Browse** pages with Previous and Next.
* **Random** page navigation.
* **First** page: all spaces.
* **Last** page: all tildes.
* **Jump** directly to a page using its address.

## Address

Pages use this format:

```text
<hex_id>-w<wall>-s<shelf>-v<volume>-p<page>
```

Where:

* `wall`: 1–6
* `shelf`: 1–8
* `volume`: 1–16
* `page`: 1–64

Each hexagon contains **49,152 pages**.

The complete library contains:

```text
95^512 ≈ 10^1009 pages
```

## How It Works

Pages are not stored anywhere, they are generated from their index using base-95 conversion.

Searching works in reverse: the text is padded to 512 characters, converted to a base-95 number, and mapped directly to its page.

This makes searching effectively instant, without a database, index, or server.

## Notes

This is inspired by Borges' *Library of Babel*, but it is not an exact implementation, it uses a different alphabet, page size, and address structure.
