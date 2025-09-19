import urllib.parse
import urllib.request

class PaperGenerator:
    def __init__(self):
        self.url = None

    def generate_paper(self, query):
        encoded_query = urllib.parse.quote(query)
        self.url = f'http://export.arxiv.org/api/query?search_query={encoded_query}&start=0&max_results=1'
        try:
            r = urllib.request.urlopen(self.url)
            return r.read().decode('utf-8')
        except Exception as e:
            return None

if __name__ == '__main__':
    paper_generator = PaperGenerator()
    print(paper_generator.generate_paper('machine learning'))