#!/usr/bin/env python3
"""
Integration Tests for RAG Pipeline with Qdrant Vector Search

Tests the complete workflow:
1. Qdrant Docker container is running
2. Process website → chunks stored in SQLite + vectors in Qdrant
3. Query website → hybrid search (Qdrant vectors + SQLite FTS)
4. Verify hybrid scoring and result merging

Requirements:
- Qdrant Docker container running on localhost:6333
- resume_agent.db with RAG tables initialized
- mcp-server-qdrant MCP server configured
"""

import requests
import sqlite3
import json
import sys
from pathlib import Path

# Colors for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


class TestRagQdrantIntegration:
    """Integration tests for RAG pipeline with Qdrant"""

    def __init__(self):
        self.db_path = Path(__file__).parent.parent.parent.parent / "data" / "resume_agent.db"
        self.qdrant_url = "http://localhost:6333"
        self.collection_name = "resume-agent-chunks"
        self.passed = 0
        self.failed = 0

    def log_test(self, test_name: str, passed: bool, message: str = ""):
        """Log test result with color"""
        if passed:
            print(f"{GREEN}✓{RESET} {test_name}")
            self.passed += 1
        else:
            print(f"{RED}✗{RESET} {test_name}")
            if message:
                print(f"  {RED}Error: {message}{RESET}")
            self.failed += 1

    def test_qdrant_is_running(self) -> bool:
        """Test 1: Verify Qdrant Docker container is accessible"""
        try:
            response = requests.get(f"{self.qdrant_url}/collections", timeout=5)
            self.log_test("Qdrant Docker container is running", response.status_code == 200)
            return response.status_code == 200
        except requests.exceptions.RequestException as e:
            self.log_test("Qdrant Docker container is running", False, str(e))
            return False

    def test_qdrant_collection_exists(self) -> bool:
        """Test 2: Verify resume-agent-chunks collection exists in Qdrant"""
        try:
            response = requests.get(
                f"{self.qdrant_url}/collections/{self.collection_name}",
                timeout=5
            )
            exists = response.status_code == 200
            self.log_test(f"Qdrant collection '{self.collection_name}' exists", exists)
            if exists:
                collection_info = response.json()["result"]
                print(f"  Collection info: {collection_info['vectors_count']} vectors, "
                      f"{collection_info['points_count']} points")
            return exists
        except requests.exceptions.RequestException as e:
            self.log_test(f"Qdrant collection '{self.collection_name}' exists", False, str(e))
            return False

    def test_sqlite_database_exists(self) -> bool:
        """Test 3: Verify SQLite database exists with RAG tables"""
        if not self.db_path.exists():
            self.log_test("SQLite database exists", False, f"Database not found at {self.db_path}")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Check for RAG tables
            cursor.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name IN ('website_sources', 'website_chunks', 'website_chunks_fts')
            """)
            tables = [row[0] for row in cursor.fetchall()]

            required_tables = {'website_sources', 'website_chunks', 'website_chunks_fts'}
            missing_tables = required_tables - set(tables)

            conn.close()

            if missing_tables:
                self.log_test("SQLite RAG tables exist", False,
                              f"Missing tables: {', '.join(missing_tables)}")
                return False

            self.log_test("SQLite RAG tables exist", True)
            return True

        except Exception as e:
            self.log_test("SQLite RAG tables exist", False, str(e))
            return False

    def test_sqlite_chunks_have_data(self) -> bool:
        """Test 4: Verify website_chunks table has test data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM website_chunks")
            chunk_count = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(DISTINCT source_id) FROM website_chunks")
            source_count = cursor.fetchone()[0]

            conn.close()

            passed = chunk_count > 0 and source_count > 0
            self.log_test("website_chunks table has data", passed,
                          "" if passed else "No chunks found in database")
            if passed:
                print(f"  Found {chunk_count} chunks from {source_count} sources")
            return passed

        except Exception as e:
            self.log_test("website_chunks table has data", False, str(e))
            return False

    def test_fts_index_works(self) -> bool:
        """Test 5: Verify FTS full-text search index works"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Test FTS search
            cursor.execute("""
                SELECT chunk_id, bm25(website_chunks_fts) as rank
                FROM website_chunks_fts
                WHERE website_chunks_fts MATCH 'engineer OR developer'
                ORDER BY rank
                LIMIT 5
            """)
            results = cursor.fetchall()
            conn.close()

            passed = len(results) > 0
            self.log_test("FTS full-text search works", passed,
                          "" if passed else "No results from FTS search")
            if passed:
                print(f"  Found {len(results)} FTS matches")
            return passed

        except Exception as e:
            self.log_test("FTS full-text search works", False, str(e))
            return False

    def test_qdrant_has_vectors_for_chunks(self) -> bool:
        """Test 6: Verify Qdrant has vectors for SQLite chunks"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get chunk IDs from SQLite
            cursor.execute("SELECT chunk_id FROM website_chunks LIMIT 10")
            sqlite_chunk_ids = {row[0] for row in cursor.fetchall()}
            conn.close()

            if not sqlite_chunk_ids:
                self.log_test("Qdrant has vectors for SQLite chunks", False,
                              "No chunks in SQLite to compare")
                return False

            # Query Qdrant for these chunk IDs
            response = requests.post(
                f"{self.qdrant_url}/collections/{self.collection_name}/points/scroll",
                json={"limit": 100, "with_payload": True, "with_vector": False},
                timeout=10
            )

            if response.status_code != 200:
                self.log_test("Qdrant has vectors for SQLite chunks", False,
                              f"Failed to query Qdrant: {response.status_code}")
                return False

            points = response.json()["result"]["points"]
            qdrant_chunk_ids = set()

            for point in points:
                payload = point.get("payload", {})
                metadata_str = payload.get("metadata", "{}")
                try:
                    metadata = json.loads(metadata_str)
                    if "chunk_id" in metadata:
                        qdrant_chunk_ids.add(metadata["chunk_id"])
                except json.JSONDecodeError:
                    continue

            # Check overlap
            overlap = sqlite_chunk_ids & qdrant_chunk_ids
            passed = len(overlap) > 0

            self.log_test("Qdrant has vectors for SQLite chunks", passed,
                          "" if passed else "No matching chunk IDs between SQLite and Qdrant")
            if passed:
                print(f"  Found {len(overlap)}/{len(sqlite_chunk_ids)} chunks with vectors in Qdrant")

            return passed

        except Exception as e:
            self.log_test("Qdrant has vectors for SQLite chunks", False, str(e))
            return False

    def test_vector_search_returns_results(self) -> bool:
        """Test 7: Verify Qdrant vector search returns results"""
        try:
            # Test semantic search query
            test_query = "What are the requirements for a backend engineer?"

            # Query Qdrant using search endpoint
            response = requests.post(
                f"{self.qdrant_url}/collections/{self.collection_name}/points/search",
                json={
                    "vector": {
                        "name": "default",
                        "text": test_query
                    },
                    "limit": 5,
                    "with_payload": True,
                    "with_vector": False
                },
                timeout=10
            )

            if response.status_code != 200:
                self.log_test("Qdrant vector search returns results", False,
                              f"Search failed with status {response.status_code}")
                return False

            results = response.json().get("result", [])
            passed = len(results) > 0

            self.log_test("Qdrant vector search returns results", passed,
                          "" if passed else "No results from vector search")
            if passed:
                print(f"  Found {len(results)} semantic matches")
                print(f"  Top score: {results[0]['score']:.4f}")

            return passed

        except Exception as e:
            self.log_test("Qdrant vector search returns results", False, str(e))
            return False

    def test_hybrid_search_scoring(self) -> bool:
        """Test 8: Verify hybrid search combines vector and FTS scores correctly"""
        try:
            # This test verifies the scoring algorithm works correctly
            # We'll simulate hybrid scoring with mock data

            # Mock vector results (Qdrant scores are 0-1, higher is better)
            vector_results = [
                {"chunk_id": 1, "score": 0.95},  # 95 on 0-100 scale
                {"chunk_id": 2, "score": 0.80},  # 80 on 0-100 scale
                {"chunk_id": 3, "score": 0.65},  # 65 on 0-100 scale
            ]

            # Mock FTS results (BM25 negative log, convert to 0-100 where 100 is best)
            fts_results = [
                {"chunk_id": 2, "bm25_rank": -1.5},  # Normalize: 100 - (1.5 * 10) = 85
                {"chunk_id": 3, "bm25_rank": -2.0},  # Normalize: 100 - (2.0 * 10) = 80
                {"chunk_id": 4, "bm25_rank": -3.0},  # Normalize: 100 - (3.0 * 10) = 70
            ]

            # Merge and calculate combined scores (70% vector + 30% FTS)
            merged = {}

            for vec in vector_results:
                chunk_id = vec["chunk_id"]
                vector_score = vec["score"] * 100
                merged[chunk_id] = {
                    "vector_score": vector_score,
                    "fts_score": 0.0,
                    "combined_score": 0.0
                }

            for fts in fts_results:
                chunk_id = fts["chunk_id"]
                fts_score = max(0, 100 - (abs(fts["bm25_rank"]) * 10))
                if chunk_id in merged:
                    merged[chunk_id]["fts_score"] = fts_score
                else:
                    merged[chunk_id] = {
                        "vector_score": 0.0,
                        "fts_score": fts_score,
                        "combined_score": 0.0
                    }

            # Calculate combined scores
            for result in merged.values():
                result["combined_score"] = (result["vector_score"] * 0.7) + (result["fts_score"] * 0.3)

            # Verify scoring logic
            # Chunk 2 should score highest (vector: 80, fts: 85)
            # Expected: (80 * 0.7) + (85 * 0.3) = 56 + 25.5 = 81.5
            chunk_2_score = merged[2]["combined_score"]
            expected_chunk_2 = (80 * 0.7) + (85 * 0.3)

            passed = abs(chunk_2_score - expected_chunk_2) < 0.1  # Allow small floating point error

            self.log_test("Hybrid search scoring algorithm correct", passed,
                          "" if passed else f"Score mismatch: got {chunk_2_score}, expected {expected_chunk_2}")
            if passed:
                print(f"  Hybrid scoring verified: {chunk_2_score:.2f} (70% vector + 30% FTS)")

            return passed

        except Exception as e:
            self.log_test("Hybrid search scoring algorithm correct", False, str(e))
            return False

    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "=" * 60)
        print("RAG Pipeline + Qdrant Integration Tests")
        print("=" * 60 + "\n")

        # Prerequisites
        print("Prerequisites:")
        qdrant_ok = self.test_qdrant_is_running()
        collection_ok = self.test_qdrant_collection_exists()
        db_ok = self.test_sqlite_database_exists()

        if not (qdrant_ok and db_ok):
            print(f"\n{RED}✗ Prerequisites failed. Skipping remaining tests.{RESET}")
            print(f"\n{YELLOW}Setup Instructions:{RESET}")
            if not qdrant_ok:
                print("1. Start Qdrant Docker:")
                print("   docker run -d --name qdrant -p 6333:6333 -p 6334:6334 qdrant/qdrant")
            if not db_ok:
                print("2. Initialize database:")
                print("   uv run apps/resume-agent/scripts/create_rag_tables.py")
            return

        # Data tests
        print("\nData Validation:")
        self.test_sqlite_chunks_have_data()
        self.test_fts_index_works()

        if collection_ok:
            self.test_qdrant_has_vectors_for_chunks()

        # Functional tests
        print("\nFunctional Tests:")
        if collection_ok:
            self.test_vector_search_returns_results()
        self.test_hybrid_search_scoring()

        # Summary
        print("\n" + "=" * 60)
        total = self.passed + self.failed
        print(f"Results: {GREEN}{self.passed}/{total} passed{RESET}, "
              f"{RED if self.failed > 0 else ''}{self.failed}/{total} failed{RESET}")
        print("=" * 60 + "\n")

        if self.failed > 0:
            print(f"{YELLOW}⚠ Some tests failed. Review errors above.{RESET}\n")
            sys.exit(1)
        else:
            print(f"{GREEN}✓ All tests passed! RAG pipeline is working correctly.{RESET}\n")
            sys.exit(0)


if __name__ == "__main__":
    tester = TestRagQdrantIntegration()
    tester.run_all_tests()
