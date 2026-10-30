from typing import Any


# class giup share giua nhieu file
class Share:
    def __str__(self) -> str:  # ham print instance
        return str(self.__dict__)


CONFIG: Any = Share()  # tranh bao loi lsp
