import sqlparse
from sqlalchemy.sql.elements import TextClause

from pytest_mock_resources.fixture.database.mock_s3_copy import _strip, execute_mock_s3_copy_command
from pytest_mock_resources.fixture.database.mock_s3_unload import execute_mock_s3_unload_command


def substitute_execute_with_custom_execute(redshift):
    """Substitute the default execute method with a custom execute for copy and unload command."""
    default_execute = redshift.execute

    def custom_execute(statement, *args, **kwargs):
        if not isinstance(statement, TextClause) and _strip(statement).lower().startswith("copy"):
            return execute_mock_s3_copy_command(statement, redshift)
        if not isinstance(statement, TextClause) and _strip(statement).lower().startswith("unload"):
            return execute_mock_s3_unload_command(statement, redshift)
        return default_execute(statement, *args, **kwargs)

    def handle_multiple_statements(statement, *args, **kwargs):
        """Split statement into individual sql statements and execute.

        Splits multiple statements by ';' and executes each.
        NOTE: Only the result of the last statements is returned.
        """
        statements_list = _parse_multiple_statements(statement)
        result = None
        for statement in statements_list:
            result = custom_execute(statement, *args, **kwargs)

        return result

    # Now each statement is handled as if it contains multiple sql statements
    redshift.execute = handle_multiple_statements
    return redshift


def _parse_multiple_statements(statement):
    """Split the given sql statement into a list of individual sql statements."""
    statements_list = []

    # Ignore SQLAlchemy Text Objects.
    if isinstance(statement, TextClause):
        statements_list.append(statement)
        return statements_list

    # Prprocess input statement
    statement = _preprocess(statement)

    statements_list = [str(statement) for statement in sqlparse.split(statement)]

    return statements_list


def _preprocess(statement):
    """Preporcess the input statement."""
    statement = statement.strip()
    # Replace any occourance of " with '.
    statement = statement.replace('"', "'")
    if statement[-1] != ";":
        statement += ";"
    return statement
