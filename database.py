from dotenv import load_dotenv
load_dotenv() 

import psycopg2
import psycopg2.extras
import os
from typing import List, Dict, Optional
from datetime import datetime

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    '''
    Get database connection
    Inputs:
        - None
    Returns: database connection object
    '''

    if not DATABASE_URL:
        raise ValueError(
            "DATABASE_URL environment variable not set. "
            "For local development, set it to your PostgreSQL connection string. "
            "For Render deployment, it will be set automatically."
        )
    return psycopg2.connect(DATABASE_URL)


def init_db() -> None:
    '''
    Initialize database with schema
    Inputs:
        - None
    Returns: None
    '''

    conn = get_connection()
    c = conn.cursor()
    
    # Members table
    c.execute('''CREATE TABLE IF NOT EXISTS members (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        preferred_length INTEGER DEFAULT 300,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
    
    # Member genre preferences
    c.execute('''CREATE TABLE IF NOT EXISTS member_genre_preferences (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL,
        genre TEXT NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(id)
        )''')
    
    # Books pool
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        genre TEXT NOT NULL,
        page_count INTEGER NOT NULL,
        suggested_by INTEGER,
        FOREIGN KEY (suggested_by) REFERENCES members(id)
        )''')
    
    # Reading history
    c.execute('''CREATE TABLE IF NOT EXISTS reading_history (
        id SERIAL PRIMARY KEY,
        book_id INTEGER NOT NULL,
        read_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        round_number INTEGER NOT NULL,
        FOREIGN KEY (book_id) REFERENCES books(id)
        )''')
    
    # Vetoes (per round)
    c.execute('''CREATE TABLE IF NOT EXISTS vetoes (
        id SERIAL PRIMARY KEY,
        member_id INTEGER NOT NULL,
        genre TEXT NOT NULL,
        round_number INTEGER NOT NULL,
        FOREIGN KEY (member_id) REFERENCES members(id)
        )''')
    
    conn.commit()
    conn.close()


def add_member(name: str, preferred_length: int, liked_genres: List[str]) -> int:
    '''
    Add a new member with preferences
    Inputs:
        - name (str): member's name
        - preferred_length (int): preferred book length in pages
        - liked_genres (list of strings) : list of genres the member likes
    Returns: member ID (int)
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("INSERT INTO members (name, preferred_length) VALUES (%s, %s) RETURNING id",
              (name, preferred_length))
    member_id = c.fetchone()[0]
    
    for genre in liked_genres:
        c.execute("INSERT INTO member_genre_preferences (member_id, genre) VALUES (%s, %s)",
                  (member_id, genre))
    
    conn.commit()
    conn.close()

    return member_id


def add_book(title: str, author: str, genre: str, page_count: int, suggested_by: Optional[int] = None) -> int:
    '''
    Add a book to the pool
    Inputs:
        - title (str): book title
        - author (str): book author
        - genre (str): book genre
        - page_count (int): number of pages in the book
        - suggested_by (Optional[int]): member ID who suggested the book (optional)
    Returns: book ID (int)
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""INSERT INTO books (title, author, genre, page_count, suggested_by) 
                 VALUES (%s, %s, %s, %s, %s) RETURNING id""",
              (title, author, genre, page_count, suggested_by))
    book_id = c.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return book_id


def get_members() -> List[Dict]:
    '''
    Get all members with their preferences
    Inputs:
        - None
    Returns: list of dictionaries containing member information
    '''

    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute("SELECT * FROM members")
    members = [dict(row) for row in c.fetchall()]
    
    # Get genre preferences for each member
    for member in members:
        c.execute("""SELECT genre FROM member_genre_preferences 
                     WHERE member_id = %s""", (member['id'],))
        member['liked_genres'] = [row['genre'] for row in c.fetchall()]
    
    conn.close()
    return members


def get_books() -> List[Dict]:
    '''
    Get all books in the pool
    Inputs:
        - None
    Returns: list of dictionaries containing book information
    '''

    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute("""SELECT b.*, m.name as suggested_by_name 
                 FROM books b 
                 LEFT JOIN members m ON b.suggested_by = m.id""")
    books = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return books


def get_reading_history() -> List[Dict]:
    '''
    Get reading history ordered by round
    Inputs:
        - None
    Returns: list of dictionaries containing reading history
    '''

    conn = get_connection()
    c = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    c.execute("""SELECT rh.*, b.title, b.author, b.genre, b.page_count
                 FROM reading_history rh
                 JOIN books b ON rh.book_id = b.id
                 ORDER BY rh.round_number DESC""")
    history = [dict(row) for row in c.fetchall()]
    
    conn.close()
    return history


def get_current_round() -> int:
    '''
    Get the current round number
    Inputs:
        - None
    Returns: current round number (int)
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT MAX(round_number) as max_round FROM reading_history")
    result = c.fetchone()
    
    conn.close()

    return (result[0] or 0) + 1


def add_veto(member_id: int, genre: str, round_number: int) -> None:
    '''
    Add a genre veto for a member in a specific round
    Inputs:
        - member_id (int): ID of the member
        - genre (str): genre to veto
        - round_number (int): round number for the veto
    Returns: None
    '''

    conn = get_connection()
    c = conn.cursor()
    
    # Remove existing veto for this member in this round
    c.execute("DELETE FROM vetoes WHERE member_id = %s AND round_number = %s",
              (member_id, round_number))
    
    # Add new veto
    c.execute("INSERT INTO vetoes (member_id, genre, round_number) VALUES (%s, %s, %s)",
              (member_id, genre, round_number))
    
    conn.commit()
    conn.close()


def get_vetoes(round_number: int) -> List[str]:
    '''
    Get all vetoed genres for a specific round
    Inputs:
        - round_number (int): round number to get vetoes for
    Returns: list of vetoed genres (list of strings)
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("SELECT genre FROM vetoes WHERE round_number = %s", (round_number,))
    vetoed_genres = [row[0] for row in c.fetchall()]
    
    conn.close()
    return vetoed_genres


def mark_book_as_read(book_id: int, round_number: int) -> None:
    '''
    Mark a book as read in a specific round
    Inputs:
        - book_id (int): ID of the book
        - round_number (int): round number when the book was read
    Returns: None
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("INSERT INTO reading_history (book_id, round_number) VALUES (%s, %s)",
              (book_id, round_number))
    
    conn.commit()
    conn.close()


def get_last_n_genres(n: int = 2) -> List[str]:
    '''
    Get the last N genres read
    Inputs:
        - n (int): number of last genres to retrieve (default: 2)
    Returns: list of genre names (list of strings)
    '''

    conn = get_connection()
    c = conn.cursor()
    
    c.execute("""SELECT b.genre 
                 FROM reading_history rh
                 JOIN books b ON rh.book_id = b.id
                 ORDER BY rh.round_number DESC
                 LIMIT %s""", (n,))
    genres = [row[0] for row in c.fetchall()]
    
    conn.close()

    return genres


def reset_database() -> None:
    '''
    Reset the entire database (useful for testing)
    Inputs:
        - None
    Returns: None
    '''

    conn = get_connection()
    c = conn.cursor()
    
    # Drop tables in reverse order due to foreign key constraints
    tables = ['vetoes', 'reading_history', 'books', 'member_genre_preferences', 'members']

    for table in tables:
        c.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    
    conn.commit()
    conn.close()
    
    init_db()
