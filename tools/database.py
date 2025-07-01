import os
import re
from langchain_core.tools import tool
from langchain_community.utilities.sql_database import SQLDatabase
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    """Manages PostgreSQL database connections and operations."""
    
    def __init__(self, schema: str = None):
        self.schema = schema
        self.db_url = self._build_connection_url()
        self.engine = None
        self.db = None
        self._initialize_connection()
    
    def _build_connection_url(self) -> str:
        """Build PostgreSQL connection URL from environment variables."""
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5432")
        name = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")
        
        if not all([name, user, password]):
            raise ValueError(
                "Database connection requires DB_NAME, DB_USER, and DB_PASSWORD environment variables"
            )
        
        return f"postgresql://{user}:{password}@{host}:{port}/{name}"
    
    def _initialize_connection(self):
        """Initialize database connection with pooling."""
        try:
            self.engine = create_engine(
                self.db_url,
                poolclass=QueuePool,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )
            self.db = SQLDatabase(self.engine)
            
            # Set schema search path if specified
            if self.schema:
                with self.engine.connect() as conn:
                    conn.execute(text(f"SET search_path TO {self.schema}, public"))
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {str(e)}")
    
    def get_db(self) -> SQLDatabase:
        """Get the SQLDatabase instance."""
        if self.db is None:
            self._initialize_connection()
        return self.db
    
    def is_safe_query(self, query: str) -> bool:
        """Check if query is safe (read-only SELECT statements only)."""
        # Remove comments and normalize whitespace
        clean_query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        clean_query = re.sub(r'/\*.*?\*/', '', clean_query, flags=re.DOTALL)
        clean_query = clean_query.strip().upper()
        
        # Check for dangerous operations
        dangerous_patterns = [
            r'\bDROP\b', r'\bDELETE\b', r'\bUPDATE\b', r'\bINSERT\b',
            r'\bCREATE\b', r'\bALTER\b', r'\bTRUNCATE\b', r'\bGRANT\b',
            r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b'
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, clean_query):
                return False
        
        # Must start with SELECT
        return clean_query.startswith('SELECT')

# Global database manager instance
_db_manager = None

def get_database_manager() -> DatabaseManager:
    """Get or create the global database manager instance."""
    global _db_manager
    if _db_manager is None:
        try:
            _db_manager = DatabaseManager()
        except (ValueError, ConnectionError):
            return None
    return _db_manager

@tool
def list_database_tables() -> str:
    """
    List all available tables in the PostgreSQL database.
    Use this tool to discover what tables are available before querying.
    """
    try:
        db_manager = get_database_manager()
        if db_manager is None:
            return "Database connection not configured. Please set DB_NAME, DB_USER, DB_PASSWORD environment variables."
        
        db = db_manager.get_db()
        tables = db.get_usable_table_names()
        
        if not tables:
            return "No tables found in the database."
        
        return f"Available tables: {', '.join(tables)}"
    
    except Exception as e:
        return f"Error listing tables: {str(e)}"

@tool
def get_database_schema(table_names: str) -> str:
    """
    Get schema information and sample rows for specified database tables.
    
    Args:
        table_names: Comma-separated list of table names to get schema for
        
    Example: "users, orders, products"
    """
    try:
        db_manager = get_database_manager()
        if db_manager is None:
            return "Database connection not configured. Please set DB_NAME, DB_USER, DB_PASSWORD environment variables."
        
        db = db_manager.get_db()
        
        # Parse and validate table names
        tables = [name.strip() for name in table_names.split(',')]
        available_tables = db.get_usable_table_names()
        
        invalid_tables = [t for t in tables if t not in available_tables]
        if invalid_tables:
            return f"Invalid table names: {', '.join(invalid_tables)}. Available tables: {', '.join(available_tables)}"
        
        # Get schema information
        schema_info = db.get_table_info_no_throw(tables)
        return schema_info
    
    except Exception as e:
        return f"Error getting schema: {str(e)}"

@tool
def query_database(query: str) -> str:
    """
    Execute a SELECT query against the PostgreSQL database.
    Only read-only SELECT queries are allowed for security.
    
    Args:
        query: SQL SELECT query to execute
        
    Important: Only SELECT statements are permitted. No INSERT/UPDATE/DELETE operations.
    """
    try:
        db_manager = get_database_manager()
        if db_manager is None:
            return "Database connection not configured. Please set DB_NAME, DB_USER, DB_PASSWORD environment variables."
        
        # Validate query safety
        if not db_manager.is_safe_query(query):
            return "Error: Only SELECT queries are allowed. No INSERT, UPDATE, DELETE, or other modifying operations permitted."
        
        db = db_manager.get_db()
        
        # Execute query with timeout
        with db_manager.engine.connect() as conn:
            # Set query timeout (30 seconds)
            conn.execute(text("SET statement_timeout = 30000"))
            result = conn.execute(text(query))
            rows = result.fetchall()
            
            if not rows:
                return "Query executed successfully but returned no results."
            
            # Format results
            column_names = list(result.keys())
            formatted_rows = []
            
            # Limit to first 100 rows to prevent overwhelming output
            limited_rows = rows[:100]
            for row in limited_rows:
                formatted_rows.append(dict(zip(column_names, row)))
            
            result_text = f"Query returned {len(rows)} rows"
            if len(rows) > 100:
                result_text += f" (showing first 100)"
            result_text += f":\n\nColumns: {', '.join(column_names)}\n\n"
            
            # Format rows as readable text
            for i, row_dict in enumerate(formatted_rows[:10]):  # Show max 10 rows in detail
                result_text += f"Row {i+1}: {row_dict}\n"
            
            if len(formatted_rows) > 10:
                result_text += f"... and {len(formatted_rows) - 10} more rows"
            
            return result_text
    
    except Exception as e:
        return f"Query execution failed: {str(e)}"

@tool
def check_database_query(query: str) -> str:
    """
    Validate a SQL query before execution to check for syntax errors and safety.
    Use this tool before executing queries to avoid errors.
    
    Args:
        query: SQL query to validate
    """
    try:
        db_manager = get_database_manager()
        if db_manager is None:
            return "Database connection not configured. Please set DB_NAME, DB_USER, DB_PASSWORD environment variables."
        
        # Check safety first
        if not db_manager.is_safe_query(query):
            return "Query validation failed: Only SELECT queries are allowed. No INSERT, UPDATE, DELETE, or other modifying operations permitted."
        
        # Try to parse/validate the query
        db = db_manager.get_db()
        
        # Use EXPLAIN to validate syntax without executing
        explain_query = f"EXPLAIN {query}"
        
        with db_manager.engine.connect() as conn:
            conn.execute(text(explain_query))
        
        return "Query validation successful. The query appears to be syntactically correct and safe to execute."
    
    except Exception as e:
        return f"Query validation failed: {str(e)}. Please check your SQL syntax and table/column names."