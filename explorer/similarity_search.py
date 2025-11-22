import hnswlib

class VectorIndex:
    def __init__(self, M=16, ef_construction=200, ef_search=100):
        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.index = None

    def build_index(self, data):
        dim = data.shape[1]
        self.index = hnswlib.Index(space='cosine', dim=dim)
        self.index.init_index(max_elements=len(data), M=self.M, ef_construction=self.ef_construction)

    def search(self, query, k=10):
        self.index.set_ef(self.ef_search)
        d, n = self.index.knn_query([query], k=k)
        return n


