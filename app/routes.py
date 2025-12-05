class Routes:
    def __init__(self):
        self._mappings = {}

    def save(self, short_code: str, url: str):
        self._mappings[short_code] = url

    def get(self, short_code: str):
        return self._mappings.get(short_code)

    def delete(self, short_code: str):
        del self._mappings[short_code]
        return True if short_code not in self._mappings else False

    def exists(self, short_code: str):
        return True if short_code in self._mappings else False