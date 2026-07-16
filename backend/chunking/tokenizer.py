

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Tuple

from transformers import AutoTokenizer

# Local path to the saved tokenizer
_LOCAL_TOKENIZER_DIR = os.path.join(
    os.path.dirname(__file__), "..", "models", "Qwen3-8B-tokenizer"
)


# ==========================================================
# Configuration
# ==========================================================

@dataclass
class TokenizerConfig:

    model_name: str = _LOCAL_TOKENIZER_DIR

    add_special_tokens: bool = False


# ==========================================================
# Tokenizer
# ==========================================================

class BPETokenizer:

    def __init__(

            self,

            config: TokenizerConfig | None = None

    ):

        self.config = config or TokenizerConfig()

        self.tokenizer = AutoTokenizer.from_pretrained(self.config.model_name)

    # ------------------------------------------------------

    def encode(self, text: str) -> List[int]:
        """
        Convert text -> token ids
        """

        return self.tokenizer.encode(

            text,

            add_special_tokens=self.config.add_special_tokens

        )

    # ------------------------------------------------------

    def decode(self, token_ids: List[int]) -> str:
        """
        Convert token ids -> text
        """

        return self.tokenizer.decode(

            token_ids,

            skip_special_tokens=True

        )

    # ------------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """
        Number of BPE tokens
        """

        return len(

            self.encode(text)

        )

    # ------------------------------------------------------

    def batch_count_tokens(

            self,

            texts: List[str]

    ) -> List[int]:

        return [

            self.count_tokens(text)

            for text in texts

        ]

    # ------------------------------------------------------

    def token_offsets(

            self,

            text: str

    ) -> List[Tuple[int, int]]:
        """
        Returns

        [(start,end), (start,end)...]
        """

        encoding = self.tokenizer(

            text,

            return_offsets_mapping=True,

            add_special_tokens=False

        )

        return encoding["offset_mapping"]

    # ------------------------------------------------------

    def tokenize_with_offsets(

            self,

            text: str

    ):

        ids = self.encode(text)

        offsets = self.token_offsets(text)

        tokens = self.tokenizer.convert_ids_to_tokens(ids)

        result = []

        for token, span in zip(tokens, offsets):

            result.append(

                {

                    "token": token,

                    "start": span[0],

                    "end": span[1],

                    "text": text[span[0]:span[1]]

                }

            )

        return result

    # ------------------------------------------------------

    def last_tokens(

            self,

            text: str,

            overlap: int

    ) -> str:
        """
        Return last N tokens as text.
        """

        ids = self.encode(text)

        return self.decode(

            ids[-overlap:]

        )

    # ------------------------------------------------------

    def first_tokens(

            self,

            text: str,

            count: int

    ) -> str:

        ids = self.encode(text)

        return self.decode(

            ids[:count]

        )

    # ------------------------------------------------------

    def truncate(

            self,

            text: str,

            max_tokens: int

    ) -> str:

        ids = self.encode(text)

        ids = ids[:max_tokens]

        return self.decode(ids)

    # ------------------------------------------------------

    def chunk_token_ranges(

            self,

            text: str,

            chunk_size: int,

            overlap: int

    ):
        """
        Utility for debugging.

        Returns token ranges only.

        Example

        [(0,512),(448,960)...]
        """

        ids = self.encode(text)

        ranges = []

        start = 0

        while start < len(ids):

            end = min(

                start + chunk_size,

                len(ids)

            )

            ranges.append(

                (start, end)

            )

            if end == len(ids):

                break

            start = end - overlap

        return ranges

    #----------------------------------
    def get_overlap_text(
            self,
            text: str,
            overlap_tokens: int
    ) -> str:
        """
        Returns the last N tokens from the text as a string.
        Used for chunk overlap.
        """
        token_ids = self.encode(text)

        # If the text is smaller than the overlap,
        # just return the original text.
        if len(token_ids) <= overlap_tokens:
            return text

        overlap_ids = token_ids[-overlap_tokens:]
        return self.decode(overlap_ids)


# ==========================================================
# Example
# ==========================================================

if __name__ == "__main__":

    tokenizer = BPETokenizer()

    sample = """
LangGraph provides a stateful execution framework.

CheckpointSaver stores execution state.

RedisSaver persists graph checkpoints.
"""

    print("=" * 60)

    print("Token Count")

    print(tokenizer.count_tokens(sample))

    print("=" * 60)

    print("Offsets")

    for item in tokenizer.tokenize_with_offsets(sample)[:10]:

        print(item)

    print("=" * 60)

    print("Last 20 Tokens")

    print(

        tokenizer.last_tokens(

            sample,

            20

        )

    )

    print("=" * 60)

    print("Chunk Ranges")

    print(

        tokenizer.chunk_token_ranges(

            sample,

            chunk_size=64,

            overlap=16

        )

    )