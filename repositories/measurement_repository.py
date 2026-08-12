from typing import Optional

from database.connection import get_connection
from models.measurement import Measurement


class MeasurementRepository:
    def save(
        self,
        measurement: Measurement,
    ) -> Measurement:
        """
        Cria os dados da medição ou atualiza os existentes
        para o mesmo projeto.
        """

        existing = self.find_by_project_id(
            measurement.project_id
        )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            if existing is None:
                cursor.execute(
                    """
                    INSERT INTO measurements (
                        project_id,
                        responsible,
                        measurement_datetime,
                        drawing_reference,
                        alignment,
                        fixture,
                        machine_details,
                        accessories,
                        sensors,
                        special_instructions,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        measurement.project_id,
                        measurement.responsible,
                        measurement.measurement_datetime,
                        measurement.drawing_reference,
                        measurement.alignment,
                        measurement.fixture,
                        measurement.machine_details,
                        measurement.accessories,
                        measurement.sensors,
                        measurement.special_instructions,
                        measurement.created_at,
                        measurement.updated_at,
                    ),
                )

                measurement.id = cursor.lastrowid

            else:
                cursor.execute(
                    """
                    UPDATE measurements
                    SET
                        responsible = ?,
                        measurement_datetime = ?,
                        drawing_reference = ?,
                        alignment = ?,
                        fixture = ?,
                        machine_details = ?,
                        accessories = ?,
                        sensors = ?,
                        special_instructions = ?,
                        updated_at = ?
                    WHERE project_id = ?
                    """,
                    (
                        measurement.responsible,
                        measurement.measurement_datetime,
                        measurement.drawing_reference,
                        measurement.alignment,
                        measurement.fixture,
                        measurement.machine_details,
                        measurement.accessories,
                        measurement.sensors,
                        measurement.special_instructions,
                        measurement.updated_at,
                        measurement.project_id,
                    ),
                )

                measurement.id = existing.id
                measurement.created_at = existing.created_at

            connection.commit()

            return measurement

        finally:
            connection.close()

    def find_by_project_id(
        self,
        project_id: int,
    ) -> Optional[Measurement]:
        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                SELECT *
                FROM measurements
                WHERE project_id = ?
                """,
                (project_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            return Measurement(
                id=row["id"],
                project_id=row["project_id"],
                responsible=row["responsible"],
                measurement_datetime=row["measurement_datetime"],
                drawing_reference=row["drawing_reference"],
                alignment=row["alignment"],
                fixture=row["fixture"],
                machine_details=row["machine_details"],
                accessories=row["accessories"],
                sensors=row["sensors"],
                special_instructions=row["special_instructions"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

        finally:
            connection.close()