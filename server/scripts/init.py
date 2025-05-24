"""
    This init script initializes the sqlite in memory database with the
    required tables and data. It creates a table for questions and their
    embeddings, and populates it with data from a CSV file. The embeddings
    are generated using the get_embedding function from the utils module.
"""

import os
from sqlite3 import Cursor
import pandas as pd

from utils.utils import get_embedding

DATASET_NAME = "jsnad_qna.csv"
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 
    "data", 
    DATASET_NAME
)

def init(cursor: Cursor) -> bool:
    """
    Initialize the database with the required tables and data.
    """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            topic TEXT NOT NULL,
            diff_level TEXT NOT NULL,
            embedding FLOAT[768] check(
                typeof(embedding) == 'blob'
                and vec_length(embedding) == 768
            )
        )
    ''')

    try:
        df = pd.read_csv(DATASET_PATH)
        df = df.dropna()
        dataset: list = df.to_records(index=False).tolist()

        questions = [row[0] for row in dataset]
        embeddings = get_embedding(questions)

        for row, embedding in zip(dataset, embeddings):
            question = row[0]
            answer = row[1]
            topic = row[2]
            diff_level = row[3]

            cursor.execute('''
                INSERT INTO questions (question, answer, topic, diff_level, embedding)
                VALUES (?, ?, ?, ?, vec_f32(?))
            ''', (question, answer, topic, diff_level, str(embedding.values)))
        cursor.connection.commit()
    except Exception as e:
        print(f"Error: {e}")
        return False
    return True
