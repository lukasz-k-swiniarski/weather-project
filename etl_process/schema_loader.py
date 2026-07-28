class SchemaLoader:
    def load_columns(self, schema_config: dict) -> list[str]:
        columns = schema_config.get("columns")
        if not isinstance(columns, list) or not columns:
            raise ValueError("Schema config must contain a non-empty 'columns' list")

        normalized_columns = [str(column).strip().lower() for column in columns]
        if any(not column for column in normalized_columns):
            raise ValueError("Schema columns must not be empty")
        if len(normalized_columns) != len(set(normalized_columns)):
            raise ValueError("Schema columns must be unique")

        return normalized_columns
