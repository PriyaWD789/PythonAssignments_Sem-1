#!/usr/bin/env python3
"""
Single-file Library Inventory Manager
Author : Priya
Date   : 29/11/2025
Title  : Library Inventory Manager - single file version"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

# ------------------------ Logging Setup ------------------------
LOG_FILE = "library.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ------------------------ Book Class ------------------------


class Book:
    def __init__(self, title: str, author: str, isbn: str, status: str = "available"):
        self.title = title.strip()
        self.author = author.strip()
        self.isbn = isbn.strip()
        self.status = status.strip().lower()

    def __str__(self):
        return f"{self.title} by {self.author} (ISBN: {self.isbn}) - {self.status.capitalize()}"

    def to_dict(self) -> Dict:
        """Convert Book object to a serializable dict"""
        return {
            "title": self.title,
            "author": self.author,
            "isbn": self.isbn,
            "status": self.status,
            "type": self.__class__.__name__,  # store class type for reconstruction
        }

    @classmethod
    def from_dict(cls, data: Dict):
        """Create a Book (or subclass) from dict data"""
        book_type = data.get("type", "Book")
        if book_type == "ReferenceBook":
            return ReferenceBook(data["title"], data["author"], data["isbn"], data.get("status", "available"))
        else:
            return Book(data["title"], data["author"], data["isbn"], data.get("status", "available"))

    def is_available(self) -> bool:
        return self.status == "available"

    def issue(self) -> bool:
        """Attempt to issue the book. Return True if issued, False otherwise."""
        if self.is_available():
            self.status = "issued"
            return True
        return False

    def return_book(self) -> bool:
        """Return the book. Return True if returned (i.e., status changed), False otherwise."""
        if not self.is_available():
            self.status = "available"
            return True
        return False


class ReferenceBook(Book):
    """A reference book that cannot be issued (only available in library)."""

    def issue(self) -> bool:
        # Reference books cannot be issued
        return False

    def __str__(self):
        return f"{self.title} by {self.author} (ISBN: {self.isbn}) - Reference (Always in-library)"


# ------------------------ LibraryInventory Class ------------------------


class LibraryInventory:

    def __init__(self, catalog_path: str = "catalog.json"):
        self.books: List[Book] = []
        self.catalog_path = Path(catalog_path)
        # Attempt to load existing catalog at initialization
        self.load_catalog()

    # ----- Book management -----
    def add_book(self, book: Book) -> bool:
        """Adds a book if ISBN is unique. Returns True if added, False if duplicate."""
        if self.search_by_isbn(book.isbn) is not None:
            logger.info(f"Attempt to add duplicate ISBN: {book.isbn}")
            return False
        self.books.append(book)
        logger.info(f"Book added: {book}")
        return True

    def search_by_title(self, title_query: str) -> List[Book]:
        """Return list of books where title contains the query (case-insensitive)."""
        q = title_query.strip().lower()
        results = [b for b in self.books if q in b.title.lower()]
        logger.info(f"Search by title '{title_query}' found {len(results)} results.")
        return results

    def search_by_isbn(self, isbn_query: str) -> Optional[Book]:
        """Return single Book with exact ISBN match or None."""
        isbn_q = isbn_query.strip()
        for b in self.books:
            if b.isbn == isbn_q:
                logger.info(f"Search by ISBN '{isbn_query}' found: {b}")
                return b
        logger.info(f"Search by ISBN '{isbn_query}' found nothing.")
        return None

    def display_all(self) -> List[str]:
        """Return list of string representations for all books."""
        logger.info("Display all books requested.")
        return [str(b) for b in self.books]

    # ----- Persistence -----
    def save_catalog(self) -> bool:
        """Save catalog to JSON file. Returns True on success, False on failure."""
        data = [b.to_dict() for b in self.books]
        try:
            with self.catalog_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info(f"Catalog saved to {self.catalog_path}.")
            return True
        except Exception as e:
            logger.error(f"Error saving catalog to {self.catalog_path}: {e}")
            return False

    def load_catalog(self) -> bool:
        if not self.catalog_path.exists():
            logger.info(f"Catalog file {self.catalog_path} not found. Starting with empty catalog.")
            self.books = []
            return True

        try:
            with self.catalog_path.open("r", encoding="utf-8") as f:
                raw = f.read()
                if not raw.strip():
                    # empty file
                    logger.warning(f"Catalog file {self.catalog_path} is empty. Starting with empty catalog.")
                    self.books = []
                    return True
                data = json.loads(raw)
                self.books = [Book.from_dict(item) for item in data]
            logger.info(f"Catalog loaded from {self.catalog_path} ({len(self.books)} books).")
            return True
        except json.JSONDecodeError as jde:
            logger.error(f"JSON decode error while loading catalog: {jde}")
            # handle corrupted JSON gracefully - offer to reset
            print("\nERROR: Catalog file is corrupted or not valid JSON.")
            print("You can choose to (R)eset the catalog (this will overwrite the file), or (B)ackup & start fresh.")
            choice = input("Type R to reset, B to backup and start fresh, any other key to abort load: ").strip().lower()
            if choice == "r":
                try:
                    with self.catalog_path.open("w", encoding="utf-8") as f:
                        json.dump([], f)
                    self.books = []
                    logger.info("Catalog file reset to empty list.")
                    print("Catalog reset. Starting with empty catalog.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to reset catalog file: {e}")
                    print("Failed to reset catalog file.")
                    return False
            elif choice == "b":
                # backup current corrupted file
                backup_path = self.catalog_path.with_suffix(".backup.json")
                try:
                    self.catalog_path.replace(backup_path)
                    with backup_path.open("w", encoding="utf-8") as f:
                        f.write(raw)
                    # create new empty catalog
                    with self.catalog_path.open("w", encoding="utf-8") as f:
                        json.dump([], f)
                    self.books = []
                    logger.info(f"Corrupted catalog backed up to {backup_path}. New empty catalog created.")
                    print(f"Corrupted file backed up to {backup_path}. Starting with empty catalog.")
                    return True
                except Exception as e:
                    logger.error(f"Failed to backup corrupted catalog: {e}")
                    print("Failed to backup corrupted catalog.")
                    return False
            else:
                print("Aborted loading catalog. Program will continue with empty in-memory catalog (not saved).")
                self.books = []
                return True
        except Exception as e:
            logger.error(f"Unexpected error loading catalog: {e}")
            print(f"Unexpected error loading catalog: {e}")
            self.books = []
            return False


# ------------------------ Helper Functions ------------------------


def input_nonempty(prompt: str) -> str:
    """Prompt until user enters a non-empty string."""
    while True:
        val = input(prompt).strip()
        if val:
            return val
        print("Input cannot be empty. Try again.")


def confirm(prompt: str) -> bool:
    """Simple yes/no confirmation."""
    ans = input(prompt + " (y/n): ").strip().lower()
    return ans == "y"


def add_book_cli(inventory: LibraryInventory):
    print("\n---- Add a New Book ----")
    title = input_nonempty("Title: ")
    author = input_nonempty("Author: ")
    isbn = input_nonempty("ISBN (unique): ")
    # Ask if reference book
    is_ref = input("Is this a reference book (cannot be issued)? (y/n): ").strip().lower() == "y"
    if is_ref:
        book = ReferenceBook(title, author, isbn, status="available")
    else:
        book = Book(title, author, isbn, status="available")

    added = inventory.add_book(book)
    if added:
        print("Book added successfully.")
    else:
        print("A book with that ISBN already exists. Add aborted.")


def issue_book_cli(inventory: LibraryInventory):
    print("\n---- Issue a Book ----")
    isbn = input_nonempty("Enter ISBN of the book to issue: ")
    book = inventory.search_by_isbn(isbn)
    if book is None:
        print("No book found with that ISBN.")
        return
    # check if ReferenceBook
    if isinstance(book, ReferenceBook):
        print("This is a reference book and cannot be issued.")
        return
    if book.issue():
        logger.info(f"Book issued: {book.isbn}")
        print("Book issued successfully.")
    else:
        print("Book is not available for issue (may already be issued).")


def return_book_cli(inventory: LibraryInventory):
    print("\n---- Return a Book ----")
    isbn = input_nonempty("Enter ISBN of the book to return: ")
    book = inventory.search_by_isbn(isbn)
    if book is None:
        print("No book found with that ISBN.")
        return
    if book.return_book():
        logger.info(f"Book returned: {book.isbn}")
        print("Book returned successfully.")
    else:
        print("Book was already available in the library (not issued).")


def view_all_cli(inventory: LibraryInventory):
    print("\n---- All Books in Catalog ----")
    lines = inventory.display_all()
    if not lines:
        print("Catalog is empty.")
        return
    for line in lines:
        print(line)


def search_cli(inventory: LibraryInventory):
    print("\n---- Search ----")
    print("1. Search by title")
    print("2. Search by ISBN")
    choice = input("Choice (1/2): ").strip()
    if choice == "1":
        q = input_nonempty("Enter title keyword: ")
        results = inventory.search_by_title(q)
        if results:
            print(f"Found {len(results)} result(s):")
            for b in results:
                print(str(b))
        else:
            print("No books found with that title keyword.")
    elif choice == "2":
        q = input_nonempty("Enter ISBN: ")
        b = inventory.search_by_isbn(q)
        if b:
            print("Found:")
            print(str(b))
        else:
            print("No book found with that ISBN.")
    else:
        print("Invalid choice.")


# ------------------------ CLI Main Loop ------------------------


def main():
    print("############################################")
    print("## Welcome to Library Inventory Manager!  ##")
    print("############################################")
    inv = LibraryInventory()  # loads existing catalog or starts fresh

    while True:
        print("\n--- Main Menu ---")
        print("1. Add Book")
        print("2. Issue Book")
        print("3. Return Book")
        print("4. View All Books")
        print("5. Search")
        print("6. Save Catalog")
        print("7. Exit (save and quit)")
        print("8. Exit without saving")
        choice = input("Enter your choice (1-8): ").strip()

        try:
            if choice == "1":
                add_book_cli(inv)

            elif choice == "2":
                issue_book_cli(inv)

            elif choice == "3":
                return_book_cli(inv)

            elif choice == "4":
                view_all_cli(inv)

            elif choice == "5":
                search_cli(inv)

            elif choice == "6":
                ok = inv.save_catalog()
                if ok:
                    print("Catalog saved to disk.")
                else:
                    print("Failed to save catalog. Check logs.")

            elif choice == "7":
                # Save then exit
                ok = inv.save_catalog()
                if ok:
                    print("Catalog saved. Exiting now. Goodbye!")
                else:
                    print("Save failed. Exiting without saving. Check logs.")
                break

            elif choice == "8":
                if confirm("Are you sure you want to exit WITHOUT saving?"):
                    print("Exiting without saving. Goodbye!")
                    break
                else:
                    print("Exit aborted. Returning to menu.")
            else:
                print("Invalid choice. Enter a number between 1 and 8.")

        except Exception as e:
            # Catch unexpected exceptions so program doesn't crash
            logger.error(f"Unhandled exception in CLI loop: {e}", exc_info=True)
            print(f"An unexpected error occurred: {e}")

    # End of main loop
    print("Program terminated.")


if __name__ == "__main__":
    main()
