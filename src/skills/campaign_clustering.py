# Clustering skills (using TF-IDF, CountVectorizer, or edit distance).

import logging
from typing import List, Dict, Set
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


def _levenshtein_similarity(s1: str, s2: str) -> float:
    """
    Compute Levenshtein distance-based similarity (0.0-1.0) between two strings.
    Uses dynamic programming; no external dependencies.
    
    Normalizes by the length of the longer string, so:
    - 1.0 = identical
    - 0.0 = completely different
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Similarity score from 0.0 (completely different) to 1.0 (identical)
    """
    s1, s2 = s1.lower(), s2.lower()
    
    if not s1 and not s2:
        return 1.0
    if not s1 or not s2:
        return 0.0
    
    if s1 == s2:
        return 1.0
    
    # Levenshtein distance using dynamic programming
    len1, len2 = len(s1), len(s2)
    prev_row = list(range(len2 + 1))
    
    for i in range(1, len1 + 1):
        curr_row = [i] + [0] * len2
        for j in range(1, len2 + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            curr_row[j] = min(
                curr_row[j - 1] + 1,      # insertion
                prev_row[j] + 1,          # deletion
                prev_row[j - 1] + cost    # substitution
            )
        prev_row = curr_row
    
    # Normalize by max length to get similarity (0-1 scale)
    distance = prev_row[len2]
    max_len = max(len1, len2)
    return 1.0 - (distance / max_len)


def cluster_similar_comments(texts: List[str], threshold: float = 0.8) -> Dict[int, List[int]]:
    """
    Clusters comment texts by semantic/structural similarity.
    Uses difflib (no external dependencies) as a fallback when scikit-learn is unavailable.
    
    Args:
        texts: List of comment text strings to cluster.
        threshold: Similarity score (0.0-1.0) above which two texts are considered similar.
        
    Returns:
        Dictionary mapping cluster_id (int) to list of text indices belonging to that cluster.
    """
    if not texts:
        return {}
    
    if len(texts) == 1:
        return {0: [0]}
    
    try:
        # Try to use scikit-learn for better clustering if available
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        
        logger.debug("Using scikit-learn for clustering")
        
        # Vectorize texts using TF-IDF
        vectorizer = TfidfVectorizer(
            analyzer='char',
            ngram_range=(2, 3),
            min_df=1,
            lowercase=True,
            stop_words=None
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # Compute pairwise cosine similarities
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
    except ImportError:
        # Fallback: use Levenshtein distance-based similarity
        logger.debug("scikit-learn not available; using Levenshtein-based fallback clustering")
        n = len(texts)
        similarity_matrix = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(n):
                if i == j:
                    similarity_matrix[i][j] = 1.0
                else:
                    similarity_matrix[i][j] = _levenshtein_similarity(texts[i], texts[j])
    
    # Cluster using union-find (greedy clustering)
    clusters: Dict[int, Set[int]] = {}
    visited: Set[int] = set()
    cluster_id = 0
    
    for i in range(len(texts)):
        if i in visited:
            continue
        
        # Start a new cluster with text i
        cluster_members: Set[int] = {i}
        visited.add(i)
        
        # Find all texts similar to i or to any member of the growing cluster
        queue = [i]
        while queue:
            current = queue.pop(0)
            for j in range(len(texts)):
                if j not in visited:
                    # Handle both numpy array and list similarity matrix
                    try:
                        sim_score = float(similarity_matrix[current][j])
                    except (TypeError, IndexError):
                        sim_score = 0.0
                    
                    if sim_score >= threshold:
                        cluster_members.add(j)
                        visited.add(j)
                        queue.append(j)
        
        # Only store clusters with more than one member
        if len(cluster_members) > 1:
            clusters[cluster_id] = cluster_members
            cluster_id += 1
    
    # Convert sets to sorted lists
    result = {cid: sorted(list(members)) for cid, members in clusters.items()}
    logger.debug(f"Clustered {len(texts)} texts into {len(result)} clusters with threshold {threshold}")
    
    return result
