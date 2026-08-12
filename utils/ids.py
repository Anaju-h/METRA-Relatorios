from datetime import datetime

from database.connection import get_connection


def generate_report_id() -> str:
    """
    Gera identificadores no formato:

    MET-2026-0001
    MET-2026-0002
    MET-2026-0003
    """

    year = datetime.now().year

    connection = get_connection()

    try:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT report_id
            FROM projects
            WHERE report_id LIKE ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (f"MET-{year}-%",),
        )

        row = cursor.fetchone()

        if row is None:
            next_number = 1

        else:
            last_report_id = row["report_id"]

            try:
                last_number = int(
                    last_report_id.split("-")[-1]
                )
            except (ValueError, IndexError):
                last_number = 0

            next_number = last_number + 1

        return f"MET-{year}-{next_number:04d}"

    finally:
        connection.close()