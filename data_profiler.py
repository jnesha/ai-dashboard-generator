import pandas as pd

def profile_dataframe(df: pd.DataFrame) -> dict:
    profile = {
        "n_rows": len(df),
        "n_columns": len(df.columns),
        "columns": [],
    }

    for col in df.columns:
        col_data = df[col]
        col_info = {
            "name": col,
            "dtype": str(col_data.dtype),
            "missing_pct": round(col_data.isna().mean() * 100, 1),
            "n_unique": int(col_data.nunique()),
        }

        if pd.api.types.is_numeric_dtype(col_data):
            non_null = col_data.dropna()
            if len(non_null) > 0:
                col_info["min"] = float(non_null.min())
                col_info["max"] = float(non_null.max())
                col_info["mean"] = round(float(non_null.mean()), 2)
        else:
            top_values = col_data.value_counts().head(5)
            col_info["top_values"] = {
                str(k): int(v) for k, v in top_values.items()
            }

        profile["columns"].append(col_info)

    return profile
