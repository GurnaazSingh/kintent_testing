import re
from src.definitions.status_codes import key_mapper


class CmsProcess:

    @staticmethod
    def drop_dupli(df, processed_df, db_data, criteria, group):
        df = df.append(processed_df)
        duplicate = df[df.duplicated([criteria])]
        duplicate[key_mapper.REJECTION_REASON] = "Duplicate on " + criteria
        db_data[key_mapper.REJECTED_DATA] = duplicate.to_dict(orient="records")
        db_data[key_mapper.PROCESSED_DATA] = df.drop_duplicates([criteria]).to_dict(
            orient="records")
        db_data[key_mapper.GROUP] = group
        r, c = duplicate.shape
        db_data[key_mapper.REJECTED] = r
        db_data[key_mapper.PROCESSED] = db_data[key_mapper.TOTAL] - db_data[key_mapper.REJECTED]
        return db_data

    @staticmethod
    def excel_validation_check(criteria, df):
        row = df.iloc[1, 0]
        if len(list(df.columns)) > 1:
            return False
        elif criteria == "Email":
            if re.search(r"@", row):
                return True
            else:
                return False
        elif criteria == "Phone No":
            row = str(row)
            if re.search(r"^(\+\d{1,2})?\(?\d{3}\)?\d{3}\d{4}$", row):
                return True
            else:
                return False
        elif criteria == "Customer ID":
            if re.search(r"^[A-Z]\d$", row):
                return True
            else:
                return False