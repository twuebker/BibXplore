import hnswlib

class VectorIndex:
    def __init__(self, M=16, ef_construction=200, ef_search=100):
        self.M = M
        self.ef_construction = ef_construction
        self.ef_search = ef_search
        self.index = None
        self.lookup_table = None

    def build_index(self, isbns, data):
        dim = len(data[0])
        num_isbns = len(isbns)
        self.index = hnswlib.Index(space='cosine', dim=dim)
        self.index.init_index(max_elements=len(data), M=self.M, ef_construction=self.ef_construction)
        self.index.add_items(data)
        self.lookup_table = {i:isbns[i] for i in range(num_isbns)}

    def search(self, query, k=10):
        self.index.set_ef(self.ef_search)
        n, d = self.index.knn_query([query], k=k)
        isbn_list = [self.lookup_table[i] for i in n[0]]
        return isbn_list


