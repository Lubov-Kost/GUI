from pathlib import Path
from typing import Iterator
import gzip
from abstract import SequenceReader
from record import SequenceRecord


class FastqReader(SequenceReader):
    """
    Реализация ридера для чтения FASTQ-файлов (включая сжатые .gz).

    Поддерживает итеративное чтение записей в формате FASTQ, автоматическое определение
    сжатия по расширению файла (.gz), валидацию структуры записей и преобразование
    ASCII-строк качества в числовые значения Phred+33.

    Attributes:
        filepath (Path): Путь к FASTQ-файлу (может быть сжатым).
        file (file object or None): Открытый файловый дескриптор (обычный или gzip).
    """

    def __init__(self, filepath: str | Path):
        """
        Инициализирует FastqReader с указанным путём к файлу.

        Args:
            filepath (str | Path): Путь к FASTQ-файлу. Поддерживается сжатие (.gz).
        """
        super().__init__(filepath)
        self.file = None

    def __enter__(self):
        """
        Поддержка контекстного менеджера (with-блока).

        Автоматически определяет, сжат ли файл (по расширению .gz),
        и открывает его в текстовом режиме с кодировкой ASCII.

        Returns:
            FastqReader: Текущий экземпляр после открытия файла.

        Raises:
            OSError: Если файл не может быть открыт (например, не существует или повреждён).
        """
        if str(self.filepath).endswith('.gz'):
            self.file = gzip.open(self.filepath, "rt", encoding="ascii")
        else:
            self.file = open(self.filepath, "r", encoding="ascii")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Завершение работы контекстного менеджера.

        Корректно закрывает файл (обычный или gzip) при выходе из with-блока.

        Args:
            exc_type (type or None): Тип исключения, если оно возникло.
            exc_value (Exception or None): Экземпляр исключения.
            traceback (traceback or None): Объект трассировки стека.
        """
        self.close()

    def close(self):
        """
        Закрывает открытый файл, если он существует и не закрыт.

        Устанавливает атрибут self.file в None после закрытия.
        """
        if self.file:
            self.file.close()
            self.file = None

    def read(self) -> Iterator[SequenceRecord]:
        """
        Итеративно читает FASTQ-файл и возвращает объекты SequenceRecord.

        Каждая запись FASTQ состоит из 4 строк:
            1. Заголовок (начинается с '@')
            2. Последовательность нуклеотидов
            3. Разделитель (начинается с '+')
            4. Строка качества (ASCII, Phred+33)

        Метод выполняет базовую валидацию структуры и длины данных.

        Yields:
            SequenceRecord: Объект с атрибутами id, sequence и quality (список int).

        Raises:
            ValueError: При нарушении формата FASTQ (неверные маркеры, несоответствие длины и т.д.).
            OSError: Если файл не может быть прочитан.
        """
        if not self.file:
            if str(self.filepath).endswith('.gz'):
                self.file = gzip.open(self.filepath, "rt", encoding="ascii")
            else:
                self.file = open(self.filepath, "r", encoding="ascii")

        while True:
            header = self.file.readline()
            if not header:
                break

            sequence = self.file.readline().rstrip('\n')
            plus_line = self.file.readline()
            quality = self.file.readline().rstrip('\n')

            if not (header and sequence and plus_line and quality):
                break

            if not header.startswith("@"):
                raise ValueError(f"Invalid FASTQ: expected '@', got {header.strip()!r}")
            if not plus_line.startswith("+"):
                raise ValueError(f"Invalid FASTQ: expected '+', got {plus_line.strip()!r}")

            seq_id = header[1:].split(maxsplit=1)[0] if len(header) > 1 else "unknown"

            seq_clean = sequence.upper()
            qual_clean = quality

            if len(seq_clean) != len(qual_clean):
                raise ValueError(f"Sequence and quality length mismatch for {seq_id}")

            if not seq_clean:
                raise ValueError(f"Empty sequence for {seq_id}")

            quality_scores = self._parse_quality(qual_clean)


            record = SequenceRecord(id=seq_id, sequence=seq_clean, quality=quality_scores)
            yield record

    @staticmethod
    def _parse_quality(quality_str: str) -> list[int]:
        """
        Преобразует строку качества FASTQ (ASCII) в список числовых значений Phred+33.

        Согласно стандарту Phred+33, символ '!' (ASCII 33) соответствует качеству 0,
        а максимальное значение обычно не превышает 93 (ASCII 126).

        Args:
            quality_str (str): Строка качества в формате ASCII (например, "IIIIJJI").

        Returns:
            list[int]: Список целых чисел — Phred-оценок качества для каждой позиции.

        Example:
            >>> FastqReader._parse_quality("!")
            [0]
            >>> FastqReader._parse_quality("I")
            [40]
        """
        return [ord(ch) - 33 for ch in quality_str]