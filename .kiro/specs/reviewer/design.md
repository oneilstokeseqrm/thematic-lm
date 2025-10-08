# Design: Codebook Reviewer

## Architecture Overview

The reviewer updates the adaptive codebook with new codes using semantic similarity search. It generates embeddings, queries Pinecone for similar codes, and decides whether to merge or add new codes based on similarity thresholds.

## Key Classes/Functions

### ReviewerAgent

```python
class ReviewerAgent:
    def __init__(
        self,
        openai_client: OpenAIClient,
        pinecone_client: PineconeClient,
        similarity_threshold: float = 0.85
    ):
        self.openai_client = openai_client
        self.pinecone_client = pinecone_client
        self.similarity_threshold = similarity_threshold
    
    async def update_codebook(
        self,
        aggregated_codes: List[Dict],
        existing_codebook: Dict,
        account_id: str
    ) -> Dict:
        """Update codebook with new codes."""
        updated_codes = list(existing_codebook["codes"])
        
        for new_code in aggregated_codes:
            # Generate embedding
            embedding = await self._generate_embedding(new_code["label"])
            
            # Find similar codes
            similar_codes = await self._find_similar_codes(
                embedding, account_id, k=5
            )
            
            # Merge or add
            if similar_codes and similar_codes[0]["score"] > self.similarity_threshold:
                updated_codes = self._merge_code(new_code, similar_codes[0], updated_codes)
            else:
                updated_codes.append(self._create_new_code(new_code))
            
            # Upsert embedding to Pinecone
            await self._upsert_embedding(new_code, embedding, account_id)
        
        # Create new version
        new_version = self._increment_version(existing_codebook["version"])
        
        return {
            "version": new_version,
            "account_id": account_id,
            "codes": updated_codes,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
```

## Embedding Pipeline

### Batch Processing

```python
async def _generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
    """Generate embeddings in batches (up to 100 per batch)."""
    embeddings = []
    
    for i in range(0, len(texts), 100):
        batch = texts[i:i+100]
        response = await self.openai_client.embeddings_create(
            model="text-embedding-3-large",
            input=batch
        )
        embeddings.extend([e.embedding for e in response.data])
    
    return embeddings
```

## Pinecone Integration

### Index Configuration

```python
# Pinecone index setup (one-time)
pinecone.create_index(
    name="thematic-codes",
    dimension=3072,  # text-embedding-3-large
    metric="cosine",
    metadata_config={
        "indexed": ["account_id", "code_id"]
    }
)
```

### Upsert Operation

```python
async def _upsert_embedding(
    self,
    code: Dict,
    embedding: List[float],
    account_id: str
):
    """Upsert code embedding to Pinecone."""
    await self.pinecone_client.upsert(
        vectors=[{
            "id": code["code_id"],
            "values": embedding,
            "metadata": {
                "account_id": account_id,
                "code_id": code["code_id"],
                "label": code["label"]
            }
        }],
        namespace=account_id  # Tenant isolation
    )
```

### Query Operation

```python
async def _find_similar_codes(
    self,
    embedding: List[float],
    account_id: str,
    k: int = 5
) -> List[Dict]:
    """Find top-k similar codes."""
    results = await self.pinecone_client.query(
        vector=embedding,
        top_k=k,
        filter={"account_id": account_id},  # Tenant isolation
        namespace=account_id,
        include_metadata=True
    )
    
    return [{
        "code_id": match.id,
        "score": match.score,
        "label": match.metadata["label"]
    } for match in results.matches]
```

## Codebook Versioning Strategy

### Version Increment

```python
def _increment_version(self, current_version: str) -> str:
    """Increment codebook version (e.g., v42 → v43)."""
    version_num = int(current_version.lstrip("v"))
    return f"v{version_num + 1}"
```

### Snapshot Persistence

```sql
-- codebook_versions table
CREATE TABLE codebook_versions (
    version VARCHAR(50) NOT NULL,
    account_id UUID NOT NULL,
    codebook JSONB NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    PRIMARY KEY (account_id, version)
);

-- RLS policy
CREATE POLICY tenant_isolation ON codebook_versions
    FOR SELECT USING (account_id = current_setting('app.current_account_id')::uuid);
```

## Decay Scoring Algorithm

```python
import math
from datetime import datetime, timedelta

def calculate_decay_score(
    code: Dict,
    lambda_decay: float = 0.01
) -> float:
    """Calculate decay score for a code."""
    # Time decay factor
    days_since_update = (datetime.utcnow() - code["updated_at"]).days
    time_decay = math.exp(-lambda_decay * days_since_update)
    
    # Usage factor (saturates at 10 quotes)
    quote_count = len(code["quotes"])
    usage_factor = min(1.0, quote_count / 10)
    
    # Combined score
    decay_score = time_decay * usage_factor
    
    return max(0.0, min(1.0, decay_score))
```

## Error Handling

- **Embedding API Failure**: Retry 3x, then abort job
- **Pinecone Query Failure**: Retry 3x, then abort job
- **Database Persistence Failure**: Retry 3x, then abort job
- **Invalid Code Format**: Log error, skip code
