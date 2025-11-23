from abc import ABC, abstractmethod
from typing import Iterator
from record import Record, SequenceRecord
from pathlib import Path


class Reader(ABC):
    """
    Абстрактный базовый класс для чтения биологических данных из файлов.

    Предоставляет общий интерфейс и базовую логику открытия/закрытия файлов,
    а также поддержку контекстного менеджера (with-блоков).

    Attributes:
        filepath (Path): Путь к файлу, из которого будут читаться данные.
        file (file object or None): Открытый файловый дескриптор или None, если файл закрыт.
    """

    def __init__(self, filepath: str | Path):
        """
        Инициализирует Reader с указанным путём к файлу.

        Args:
            filepath (str | Path): Путь к файлу в виде строки или объекта pathlib.Path.
        """
        self.filepath = Path(filepath)
        self.file = None

    @abstractmethod
    def read(self) -> Iterator[Record]:
        """
        Абстрактный метод для чтения записей из файла.

        Должен быть реализован в подклассах. Возвращает итератор по объектам типа Record,
        представляющим биологические данные (например, последовательности, выравнивания или варианты).

        Yields:
            Record: Объект записи, содержащий данные из файла.

        Raises:
            NotImplementedError: Если метод не переопределён в подклассе.
        """
        pass

    def close(self):
        """
        Закрывает открытый файл, если он ещё не закрыт.

        Устанавливает атрибут self.file в None после закрытия.
        """
        if self.file and not self.file.closed:
            self.file.close()
            self.file = None

    def __enter__(self):
        """
        Поддержка контекстного менеджера (with-блока).

        Открывает файл в режиме чтения и возвращает экземпляр Reader.

        Returns:
            Reader: Текущий экземпляр класса после открытия файла.
        """
        self.file = open(self.filepath, "r")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Завершение работы контекстного менеджера.

        Автоматически закрывает файл при выходе из with-блока,
        независимо от того, произошло ли исключение.

        Args:
            exc_type (type or None): Тип исключения, если оно возникло.
            exc_val (Exception or None): Экземпляр исключения.
            exc_tb (traceback or None): Объект трассировки стека.
        """
        self.close()


class SequenceReader(Reader):
    """
    Абстрактный класс для чтения последовательностей (например, FASTA или FASTQ).

    Наследуется от Reader и специализируется на работе с SequenceRecord.

    Attributes:
        filepath (Path): Путь к файлу с последовательностями.
        file (file object or None): Открытый файловый дескриптор.
    """

    def __init__(self, filepath: str | Path):
        """
        Инициализирует SequenceReader с указанным путём к файлу.

        Args:
            filepath (str | Path): Путь к файлу в виде строки или объекта pathlib.Path.
        """
        super().__init__(filepath)

    @abstractmethod
    def read(self) -> Iterator[SequenceRecord]:
        """
        Абстрактный метод для чтения последовательностей из файла.

        Должен возвращать итератор по объектам SequenceRecord,
        каждый из которых содержит идентификатор, последовательность и, возможно, качество (для FASTQ).

        Yields:
            SequenceRecord: Объект, представляющий одну биологическую последовательность.

        Raises:
            NotImplementedError: Если метод не реализован в подклассе.
        """
        pass


class GenomicDataReader(Reader):
    """
    Абстрактный класс для чтения геномных данных с заголовком (например, SAM, VCF).

    Поддерживает парсинг заголовка при открытии файла и чтение записей после заголовка.

    Attributes:
        filepath (Path): Путь к геномному файлу.
        file (file object or None): Открытый файловый дескриптор.
        _header_parsed (bool): Флаг, указывающий, был ли уже распарсен заголовок.
    """

    def __init__(self, filepath: str | Path):
        """
        Инициализирует GenomicDataReader с указанным путём к файлу.

        Args:
            filepath (str | Path): Путь к файлу в виде строки или объекта pathlib.Path.
        """
        super().__init__(filepath)
        self._header_parsed = False

    def __enter__(self):
        """
        Поддержка контекстного менеджера с автоматическим парсингом заголовка.

        Открывает файл и вызывает метод _parse_header() для обработки заголовочных строк.
        В случае ошибки корректно закрывает файл и выбрасывает исключение.

        Returns:
            GenomicDataReader: Текущий экземпляр после успешного открытия и парсинга заголовка.

        Raises:
            RuntimeError: Если произошла ошибка при открытии файла или парсинге заголовка.
        """
        try:
            self.file = open(self.filepath, "r")
            self._parse_header()
            return self
        except Exception as e:
            # если ошибка — аккуратно закрываем файл, чтобы не остался висеть
            if self.file and not self.file.closed:
                self.file.close()
            raise RuntimeError(f"Ошибка при открытии или парсинге файла {self.filepath}: {e}")

    @abstractmethod
    def _parse_header(self):
        """
        Абстрактный метод для парсинга заголовка геномного файла.

        Должен быть реализован в подклассах (например, для VCF или SAM).
        Обычно читает и обрабатывает строки, начинающиеся с символа '#'.

        Raises:
            NotImplementedError: Если метод не реализован в подклассе.
        """
        pass

    @abstractmethod
    def read(self) -> Iterator[Record]:
        """
        Чтение записей из файла после заголовка.

        Пропускает заголовочные строки и возвращает итератор по объектам Record,
        представляющим строки данных (например, выравнивания в SAM или варианты в VCF).

        Yields:
            Record: Объект записи геномных данных.

        Raises:
            NotImplementedError: Если метод не реализован в подклассе.
        """
        pass

    def close(self):
        """
        Закрывает файл и сбрасывает флаг парсинга заголовка.

        Вызывает родительский метод close() и дополнительно устанавливает
        _header_parsed в False для корректного состояния объекта после закрытия.
        """
        super().close()
        self._header_parsed = False