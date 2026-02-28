import chromadb
from chromadb.config import Settings
from openai import OpenAI
import hashlib


class FinancialSituationMemory:
    def __init__(self, name, config):
        embedding_backend_url = config.get("embedding_backend_url") or config["backend_url"]
        embedding_mode = config.get("embedding_mode")
        if embedding_mode is None:
            if embedding_backend_url == "http://localhost:11434/v1":
                embedding_mode = "remote"
            elif embedding_backend_url.startswith("https://api.openai.com/"):
                embedding_mode = "remote"
            else:
                embedding_mode = "local_hash"

        self.embedding_mode = embedding_mode
        if embedding_backend_url == "http://localhost:11434/v1":
            self.embedding = config.get("embedding_model") or "nomic-embed-text"
        else:
            self.embedding = config.get("embedding_model") or "text-embedding-3-small"

        self.client = None
        if self.embedding_mode == "remote":
            self.client = OpenAI(base_url=embedding_backend_url)
        self.chroma_client = chromadb.Client(Settings(allow_reset=True))
        self.situation_collection = self.chroma_client.create_collection(name=name)

    def get_embedding(self, text):
        if self.embedding_mode == "remote" and self.client is not None:
            try:
                response = self.client.embeddings.create(model=self.embedding, input=text)
                return response.data[0].embedding
            except Exception:
                pass

        dims = 256
        out: list[float] = []
        for i in range(dims // 32):
            digest = hashlib.sha256((str(i) + "\n" + text).encode("utf-8")).digest()
            out.extend([(b / 127.5) - 1.0 for b in digest])
        return out[:dims]

    def add_situations(self, situations_and_advice):
        """Add financial situations and their corresponding advice. Parameter is a list of tuples (situation, rec)"""

        situations = []
        advice = []
        ids = []
        embeddings = []

        offset = self.situation_collection.count()

        for i, (situation, recommendation) in enumerate(situations_and_advice):
            situations.append(situation)
            advice.append(recommendation)
            ids.append(str(offset + i))
            embeddings.append(self.get_embedding(situation))

        self.situation_collection.add(
            documents=situations,
            metadatas=[{"recommendation": rec} for rec in advice],
            embeddings=embeddings,
            ids=ids,
        )

    def get_memories(self, current_situation, n_matches=1):
        """Find matching recommendations using OpenAI embeddings"""
        query_embedding = self.get_embedding(current_situation)

        results = self.situation_collection.query(
            query_embeddings=[query_embedding],
            n_results=n_matches,
            include=["metadatas", "documents", "distances"],
        )

        matched_results = []
        for i in range(len(results["documents"][0])):
            matched_results.append(
                {
                    "matched_situation": results["documents"][0][i],
                    "recommendation": results["metadatas"][0][i]["recommendation"],
                    "similarity_score": 1 - results["distances"][0][i],
                }
            )

        return matched_results


if __name__ == "__main__":
    # Example usage
    matcher = FinancialSituationMemory()

    # Example data
    example_data = [
        (
            "High inflation rate with rising interest rates and declining consumer spending",
            "Consider defensive sectors like consumer staples and utilities. Review fixed-income portfolio duration.",
        ),
        (
            "Tech sector showing high volatility with increasing institutional selling pressure",
            "Reduce exposure to high-growth tech stocks. Look for value opportunities in established tech companies with strong cash flows.",
        ),
        (
            "Strong dollar affecting emerging markets with increasing forex volatility",
            "Hedge currency exposure in international positions. Consider reducing allocation to emerging market debt.",
        ),
        (
            "Market showing signs of sector rotation with rising yields",
            "Rebalance portfolio to maintain target allocations. Consider increasing exposure to sectors benefiting from higher rates.",
        ),
    ]

    # Add the example situations and recommendations
    matcher.add_situations(example_data)

    # Example query
    current_situation = """
    Market showing increased volatility in tech sector, with institutional investors 
    reducing positions and rising interest rates affecting growth stock valuations
    """

    try:
        recommendations = matcher.get_memories(current_situation, n_matches=2)

        for i, rec in enumerate(recommendations, 1):
            print(f"\nMatch {i}:")
            print(f"Similarity Score: {rec['similarity_score']:.2f}")
            print(f"Matched Situation: {rec['matched_situation']}")
            print(f"Recommendation: {rec['recommendation']}")

    except Exception as e:
        print(f"Error during recommendation: {str(e)}")
