from __future__ import annotations

from database.connection import get_connection


def initialize_database() -> None:
    connection = get_connection()

    try:
        # Ativa o funcionamento real das chaves estrangeiras
        # e das exclusões em cascata no SQLite.
        connection.execute(
            """
            PRAGMA foreign_keys = ON
            """
        )

        cursor = connection.cursor()

        # =========================================================
        # PROJETOS
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                report_id TEXT NOT NULL UNIQUE,

                name TEXT NOT NULL,
                template TEXT NOT NULL,

                inspection_type TEXT NOT NULL
                    DEFAULT 'Inspeção dimensional',

                analysis_mode TEXT NOT NULL
                    DEFAULT 'Peça única',

                quantity INTEGER NOT NULL
                    DEFAULT 1,

                technology TEXT,

                template_version TEXT NOT NULL
                    DEFAULT '1.0',

                client TEXT,

                part_name TEXT NOT NULL,
                part_code TEXT,

                equipment TEXT,

                description TEXT,

                status TEXT NOT NULL DEFAULT 'Em edição',
                version TEXT NOT NULL DEFAULT 'V1.0',

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )


        # =========================================================
        # VERSÕES / EMISSÕES DO RELATÓRIO
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS report_versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL,

                version TEXT NOT NULL,

                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,

                status TEXT NOT NULL DEFAULT 'Emitido',

                created_by TEXT,
                reviewed_by TEXT,

                created_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                UNIQUE (
                    project_id,
                    version
                )
            )
            """
        )

        # =========================================================
        # MEDIÇÃO
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS measurements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL UNIQUE,

                responsible TEXT,
                measurement_datetime TEXT,

                drawing_reference TEXT,

                alignment TEXT,
                fixture TEXT,

                machine_details TEXT,
                accessories TEXT,

                sensors TEXT,

                special_instructions TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # IMAGENS
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL,

                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,

                image_type TEXT NOT NULL DEFAULT 'Fotografia',

                caption TEXT,

                position INTEGER NOT NULL DEFAULT 0,

                is_primary INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # MARCAÇÕES
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                image_id INTEGER NOT NULL,

                annotation_type TEXT NOT NULL,

                x REAL NOT NULL,
                y REAL NOT NULL,

                width REAL NOT NULL,
                height REAL NOT NULL,

                text TEXT,

                marker_text TEXT,

                font_size INTEGER NOT NULL DEFAULT 18,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (image_id)
                    REFERENCES project_images(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # CONTROLE TÉCNICO
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS technical_controls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL UNIQUE,

                prepared_by TEXT,
                prepared_at TEXT,

                reviewed_by TEXT,
                reviewed_at TEXT,

                status TEXT NOT NULL DEFAULT 'Em elaboração',

                review_notes TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # DOCUMENTOS DO PROCESSO
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS project_documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL,

                file_path TEXT NOT NULL,
                file_name TEXT NOT NULL,
                stored_name TEXT,

                specimen_identifier TEXT,

                document_order INTEGER NOT NULL DEFAULT 0,

                analysis_status TEXT NOT NULL DEFAULT 'Pendente',
                analysis_message TEXT,

                source_type TEXT NOT NULL DEFAULT 'UNKNOWN',

                page_count INTEGER NOT NULL DEFAULT 0,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # EXTRAÇÃO DO RELATÓRIO
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS report_extractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                project_id INTEGER NOT NULL,

                document_id INTEGER,

                source_type TEXT NOT NULL DEFAULT 'UNKNOWN',

                part_name TEXT,

                machine_name TEXT,
                machine_number TEXT,

                operator TEXT,

                part_number TEXT,

                measurement_datetime TEXT,

                measurement_count INTEGER,

                out_of_tolerance_count INTEGER,

                measurement_duration TEXT,

                software_name TEXT,
                software_version TEXT,

                page_count INTEGER NOT NULL DEFAULT 0,

                reviewed INTEGER NOT NULL DEFAULT 0,

                analysis_type TEXT,
                alignment TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (project_id)
                    REFERENCES projects(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (document_id)
                    REFERENCES project_documents(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # CARACTERÍSTICAS EXTRAÍDAS
        # =========================================================

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS characteristics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,

                extraction_id INTEGER NOT NULL,

                name TEXT NOT NULL,

                group_name TEXT,

                datum TEXT,
                property_name TEXT,

                measured_value REAL,
                nominal_value REAL,

                upper_tolerance REAL,
                lower_tolerance REAL,

                deviation REAL,

                unit TEXT,

                status TEXT NOT NULL DEFAULT 'UNKNOWN',

                check_value TEXT,
                out_value TEXT,

                confidence REAL NOT NULL DEFAULT 0.0,

                extraction_method TEXT,

                source_page INTEGER,

                raw_text TEXT,

                extra_data_json TEXT,

                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,

                FOREIGN KEY (extraction_id)
                    REFERENCES report_extractions(id)
                    ON DELETE CASCADE
            )
            """
        )

        # =========================================================
        # MIGRAÇÕES: PROJECTS
        # =========================================================

        cursor.execute(
            """
            PRAGMA table_info(projects)
            """
        )

        project_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        project_migrations = {
            "inspection_type":
                (
                    "TEXT NOT NULL "
                    "DEFAULT 'Inspeção dimensional'"
                ),

            "analysis_mode":
                (
                    "TEXT NOT NULL "
                    "DEFAULT 'Peça única'"
                ),

            "quantity":
                "INTEGER NOT NULL DEFAULT 1",

            "technology":
                "TEXT",

            "template_version":
                "TEXT NOT NULL DEFAULT '1.0'",
        }

        for (
            column_name,
            column_type,
        ) in project_migrations.items():
            if column_name in project_columns:
                continue

            cursor.execute(
                f"""
                ALTER TABLE projects
                ADD COLUMN {column_name} {column_type}
                """
            )

        # Atualiza projetos antigos para códigos de template atuais.
        #
        # A conversão é conservadora: reconhece nomes comuns já usados
        # no sistema e mantém como PERSONALIZADO qualquer valor que não
        # possa ser classificado com segurança.
        cursor.execute(
            """
            UPDATE projects
            SET template =
                CASE
                    WHEN UPPER(template) IN (
                        'DIMENSIONAL_INDIVIDUAL',
                        'DIMENSIONAL_LOTE',
                        'TOMOGRAFIA_INDUSTRIAL',
                        'PERSONALIZADO'
                    )
                    THEN UPPER(template)

                    WHEN LOWER(template) LIKE '%tomograf%'
                    THEN 'TOMOGRAFIA_INDUSTRIAL'

                    WHEN LOWER(template) LIKE '%lote%'
                      OR LOWER(template) LIKE '%estat%'
                    THEN 'DIMENSIONAL_LOTE'

                    WHEN LOWER(template) LIKE '%dimension%'
                    THEN 'DIMENSIONAL_INDIVIDUAL'

                    ELSE 'PERSONALIZADO'
                END
            """
        )

        cursor.execute(
            """
            UPDATE projects
            SET inspection_type =
                CASE
                    WHEN template = 'TOMOGRAFIA_INDUSTRIAL'
                    THEN 'Inspeção tomográfica'

                    WHEN template IN (
                        'DIMENSIONAL_INDIVIDUAL',
                        'DIMENSIONAL_LOTE'
                    )
                    THEN 'Inspeção dimensional'

                    ELSE COALESCE(
                        NULLIF(inspection_type, ''),
                        'Outro'
                    )
                END
            """
        )

        cursor.execute(
            """
            UPDATE projects
            SET analysis_mode =
                CASE
                    WHEN template = 'DIMENSIONAL_LOTE'
                    THEN 'Lote / estatística'

                    WHEN template = 'DIMENSIONAL_INDIVIDUAL'
                    THEN 'Peça única'

                    WHEN template = 'TOMOGRAFIA_INDUSTRIAL'
                    THEN 'Análise qualitativa'

                    ELSE COALESCE(
                        NULLIF(analysis_mode, ''),
                        'Personalizada'
                    )
                END
            """
        )

        cursor.execute(
            """
            UPDATE projects
            SET quantity =
                CASE
                    WHEN quantity IS NULL OR quantity < 1
                    THEN 1
                    ELSE quantity
                END
            """
        )

        cursor.execute(
            """
            UPDATE projects
            SET template_version = '1.0'
            WHERE
                template_version IS NULL
                OR TRIM(template_version) = ''
            """
        )

        # =========================================================
        # MIGRAÇÕES: PROJECT_IMAGES
        # =========================================================

        cursor.execute(
            """
            PRAGMA table_info(project_images)
            """
        )

        image_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "is_primary" not in image_columns:
            cursor.execute(
                """
                ALTER TABLE project_images
                ADD COLUMN is_primary INTEGER NOT NULL DEFAULT 0
                """
            )

        # Somente uma imagem principal pode existir por processo.
        cursor.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS
                idx_project_images_one_primary
            ON project_images(project_id)
            WHERE is_primary = 1
            """
        )

        # =========================================================
        # MIGRAÇÕES: ANNOTATIONS
        # =========================================================

        cursor.execute(
            """
            PRAGMA table_info(annotations)
            """
        )

        annotation_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "marker_text" not in annotation_columns:
            cursor.execute(
                """
                ALTER TABLE annotations
                ADD COLUMN marker_text TEXT
                """
            )

        if "font_size" not in annotation_columns:
            cursor.execute(
                """
                ALTER TABLE annotations
                ADD COLUMN font_size INTEGER NOT NULL DEFAULT 18
                """
            )

        cursor.execute(
            """
            PRAGMA table_info(annotations)
            """
        )

        annotation_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "number" in annotation_columns:
            cursor.execute(
                """
                UPDATE annotations
                SET marker_text = printf('%02d', number)
                WHERE
                    marker_text IS NULL
                    AND number IS NOT NULL
                """
            )

            cursor.execute(
                """
                UPDATE annotations
                SET annotation_type = 'marker'
                WHERE annotation_type = 'number'
                """
            )

        # =========================================================
        # MIGRAÇÕES: REPORT_EXTRACTIONS
        # =========================================================

        cursor.execute(
            """
            PRAGMA table_info(report_extractions)
            """
        )

        extraction_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        if "document_id" not in extraction_columns:
            cursor.execute(
                """
                ALTER TABLE report_extractions
                ADD COLUMN document_id INTEGER
                """
            )

        if "analysis_type" not in extraction_columns:
            cursor.execute(
                """
                ALTER TABLE report_extractions
                ADD COLUMN analysis_type TEXT
                """
            )

        if "alignment" not in extraction_columns:
            cursor.execute(
                """
                ALTER TABLE report_extractions
                ADD COLUMN alignment TEXT
                """
            )

        # =========================================================
        # MIGRAÇÕES: CHARACTERISTICS
        # =========================================================

        cursor.execute(
            """
            PRAGMA table_info(characteristics)
            """
        )

        characteristic_columns = {
            row["name"]
            for row in cursor.fetchall()
        }

        characteristic_migrations = {
            "datum":
                "TEXT",

            "property_name":
                "TEXT",

            "check_value":
                "TEXT",

            "out_value":
                "TEXT",

            "confidence":
                "REAL NOT NULL DEFAULT 0.0",

            "extraction_method":
                "TEXT",

            "extra_data_json":
                "TEXT",
        }

        for (
            column_name,
            column_type,
        ) in characteristic_migrations.items():
            if column_name in characteristic_columns:
                continue

            cursor.execute(
                f"""
                ALTER TABLE characteristics
                ADD COLUMN {column_name} {column_type}
                """
            )

        # =========================================================
        # ÍNDICES
        # =========================================================


        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_report_versions_project
            ON report_versions(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_report_versions_created_at
            ON report_versions(created_at)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_projects_template
            ON projects(template)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_projects_inspection_type
            ON projects(inspection_type)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_projects_status
            ON projects(status)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_project_documents_project
            ON project_documents(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_report_extractions_project
            ON report_extractions(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_report_extractions_document
            ON report_extractions(document_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_characteristics_extraction
            ON characteristics(extraction_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_project_images_project
            ON project_images(project_id)
            """
        )

        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS
                idx_annotations_image
            ON annotations(image_id)
            """
        )

        connection.commit()

    finally:
        connection.close()