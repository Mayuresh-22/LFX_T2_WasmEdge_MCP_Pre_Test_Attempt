import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
import sqlite3
import sqlite_vec

from scripts.init import init
from utils.utils import get_embedding


mcp = FastMCP("LF_Certification_QA")


class MCPServer:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.enable_load_extension(True)
        sqlite_vec.load(self.conn)
        self.conn.enable_load_extension(False)
        self.cursor = self.conn.cursor()
    
    def init(self):
        init(self.cursor)

    def get_connection(self):
        return self.conn
    
    def get_cursor(self):
        return self.cursor

    def get_random_question(self) -> dict[str, str]:
        result = self.cursor.execute(
            "SELECT question, answer FROM questions ORDER BY RANDOM() LIMIT 1"
        ).fetchone()
        if result:
            return {"question": result[0], "answer": result[1]}
        return {"error": "No question found"}

    def get_question_answer(self, question: str) -> dict[str, str]:
        try:
            if not question:
                raise ValueError("Question cannot be empty")
            
            question_embedding = get_embedding(question)
            question_embedding = question_embedding[0].values
            
            result = self.cursor.execute(
                "SELECT question, answer, topic, diff_level, vec_distance_L2(embedding, vec_f32(?)) as score FROM questions ORDER BY score LIMIT 1",
                (str(question_embedding),)
            ).fetchall()
            if not result:
                raise ValueError("No matching question found")

            if result[0][4] > 0.6:
                raise ValueError("No matching question found")

            return {"question": result[0][0], 
                    "answer": result[0][1], 
                    "topic": result[0][2], 
                    "diff_level": result[0][3],
                    "score": result[0][4]}
        except ValueError as e:
            return {"error": str(e)}


if __name__ == "__main__":
    server = MCPServer()
    server.init()
    mcp.add_tool(server.get_random_question, 
                 "get_random_question",
                 """The function selects a random question from a list. 
                 It returns both the question and the answer. 
                 This function must be called when the user asked for a new practice question. 
                 Args: empty dict, Result: {question: str, answer: str}""")
    mcp.add_tool(server.get_question_answer,
                 "get_question_answer",
                 """The function searches an input text from the database
                 for a corresponding question and answer. Result: {
                 question: str, answer: str, topic: str, diff_level: str, score: float}""")
    mcp.run(transport="stdio")
