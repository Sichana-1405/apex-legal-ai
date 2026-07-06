# Security Agent implementation. Responsible for sanitizing raw CSV inputs.

import re
from typing import Union, IO
import pandas as pd
from src.core.state import InvestigationState

class SecurityAgent:
    """
    SecurityAgent is responsible for processing untrusted raw CSV comments data.
    It validates schemas, filters out corrupt or empty rows, and scrubs sensitive
    Personal Identifiable Information (PII) like phone numbers and email addresses
    to ensure compliance and client privacy before sending any data to downstream LLMs.
    """
    
    REQUIRED_COLUMNS = ["Username", "Comment", "Timestamp", "Platform"]
    
    # Standard email regex pattern
    EMAIL_REGEX = re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    )
    
    # Phone number regex supporting various international and national formats:
    # Matches patterns like +1-555-555-5555, (555) 555-5555, 555.555.5555, 5555555555.
    # It avoids capturing leading spaces before the phone number.
    PHONE_REGEX = re.compile(
        r'\b(?:\+?\d{1,3}[-. ]*)?\(?\d{3}\)?[-. ]*\d{3}[-. ]*\d{4}\b'
    )

    def __init__(self) -> None:
        pass

    def validate_and_sanitize(self, csv_source: Union[str, bytes, IO, pd.DataFrame]) -> pd.DataFrame:
        """
        Validates the structure of the CSV data, filters out rows with empty critical fields,
        and masks PII (emails and phone numbers) in the Comment column.

        Args:
            csv_source (Union[str, bytes, IO, pd.DataFrame]): The raw CSV input. Can be a file path,
                bytes, a file-like stream object, or an existing pandas DataFrame.

        Returns:
            pd.DataFrame: The sanitized and cleaned DataFrame containing only valid rows.

        Raises:
            ValueError: If the CSV format is invalid or required columns are missing.
        """
        # 1. Ingest input source into a pandas DataFrame
        if isinstance(csv_source, pd.DataFrame):
            df = csv_source.copy()
        else:
            try:
                df = pd.read_csv(csv_source)
            except Exception as e:
                raise ValueError(f"Failed to read CSV input source: {str(e)}") from e

        # 2. Schema Validation: Ensure required columns exist
        missing_columns = [col for col in self.REQUIRED_COLUMNS if col not in df.columns]
        if missing_columns:
            raise ValueError(
                f"Missing required columns in CSV: {', '.join(missing_columns)}. "
                f"Expected columns: {', '.join(self.REQUIRED_COLUMNS)}"
            )

        # 3. Data Cleaning: Drop rows that have missing values in any of the required columns
        # First, strip whitespace from string columns to handle empty strings
        for col in self.REQUIRED_COLUMNS:
            if df[col].dtype == object:
                df[col] = df[col].astype(str).str.strip()

        # Replace empty strings and whitespace-only strings with NaN
        df[self.REQUIRED_COLUMNS] = df[self.REQUIRED_COLUMNS].replace(r'^\s*$', pd.NA, regex=True)
        
        # Drop rows where any of the required columns are NA
        df = df.dropna(subset=self.REQUIRED_COLUMNS)

        # Reset index after dropping rows
        df = df.reset_index(drop=True)

        # 4. PII Scrubbing: Mask email addresses and phone numbers in the Comment column
        if not df.empty:
            df["Comment"] = df["Comment"].apply(self._mask_pii)

        return df

    def _mask_pii(self, text: str) -> str:
        """
        Helper method to mask email addresses and phone numbers inside comment strings.
        """
        if not isinstance(text, str):
            return ""
        
        # Mask emails
        text = self.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        
        # Mask phone numbers
        text = self.PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        
        return text

    async def run(self, state: InvestigationState) -> InvestigationState:
        """
        ADK-compliant execution interface. Converts state raw comments into a DataFrame,
        sanitizes them, and populates the sanitized comments list back to the state object.
        """
        if not state.raw_comments:
            return state

        # Convert raw comments in state to a pandas DataFrame
        raw_data = [comment.dict() for comment in state.raw_comments]
        df_raw = pd.DataFrame(raw_data)

        # Rename columns to match expected schema if needed (for state compatibility)
        column_mapping = {
            "username": "Username",
            "comment_text": "Comment",
            "timestamp": "Timestamp",
            "platform": "Platform"
        }
        df_raw = df_raw.rename(columns=column_mapping)

        # Sanitize data
        df_clean = self.validate_and_sanitize(df_raw)

        # Map back to state.sanitized_comments list
        from src.core.state import CommentData
        sanitized_list = []
        for _, row in df_clean.iterrows():
            sanitized_list.append(
                CommentData(
                    comment_id=row.get("comment_id", ""),
                    platform=row["Platform"],
                    username=row["Username"],
                    timestamp=row["Timestamp"],
                    comment_text=row["Comment"],
                    post_url=row.get("post_url"),
                    severity=row.get("severity"),
                    categories=row.get("categories", [])
                )
            )
        state.sanitized_comments = sanitized_list
        return state

