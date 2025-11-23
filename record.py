class Record:
    """
    Базовый класс для представления биологических записей.

    Содержит общий идентификатор записи, который может использоваться
    в различных форматах (FASTA, FASTQ, SAM, VCF и др.).

    Attributes:
        id (str): Уникальный идентификатор записи (например, имя последовательности или координата).
    """

    def __init__(self, id: str):
        """
        Инициализирует базовую запись с заданным идентификатором.

        Args:
            id (str): Идентификатор биологической записи.
        """
        self.id = id

    def __repr__(self) -> str:
        """
        Возвращает строковое представление объекта для отладки.

        Returns:
            str: Строка вида "<Record id=...>".
        """
        return f"<Record id={self.id}>"


class SequenceRecord(Record):
    """
    Класс для представления последовательностей нуклеотидов или аминокислот.

    Используется для хранения данных из FASTA (без качества) и FASTQ (с качеством).

    Attributes:
        id (str): Идентификатор последовательности.
        sequence (str): Биологическая последовательность (например, "ATGCGTA").
        quality (list[int] | None): Список Phred-оценок качества для каждой позиции
            (только для FASTQ). Для FASTA — None.
    """

    def __init__(self, id: str, sequence: str, quality: list[int] | None = None):
        """
        Инициализирует запись последовательности.

        Args:
            id (str): Идентификатор последовательности.
            sequence (str): Строка последовательности (обычно в верхнем регистре).
            quality (list[int] | None, optional): Список целочисленных оценок качества.
                По умолчанию None (для FASTA).
        """
        super().__init__(id)
        self.sequence = sequence
        self.quality = quality


class AlignmentRecord(Record):
    """
    Класс для представления выравнивания рида на референсный геном (формат SAM/BAM).

    Хранит информацию о положении, качестве и параметрах выравнивания.

    Attributes:
        id (str): Идентификатор рида (QNAME в SAM).
        chrom (str): Название хромосомы или референсной последовательности (RNAME).
        start (int): Начальная позиция выравнивания (1-based или 0-based в зависимости от контекста;
            здесь используется 0-based для внутренней логики).
        end (int): Конечная позиция выравнивания (вычисляется на основе CIGAR, по умолчанию = start).
        cigar (str): Строка CIGAR, описывающая операции выравнивания (например, "100M").
        mapq (int): Качество отображения (MAPQ), целое число от 0 до 255.
        flag (int): Флаг выравнивания (битовое поле, по умолчанию 0).
    """

    def __init__(self, id: str, chrom: str, start: int, cigar: str, mapq: int):
        """
        Инициализирует запись выравнивания.

        Args:
            id (str): Идентификатор рида.
            chrom (str): Название хромосомы или референса.
            start (int): Начальная позиция выравнивания (обычно 0-based).
            cigar (str): CIGAR-строка (например, "50M2D30M").
            mapq (int): Качество отображения (MAPQ score).
        """
        super().__init__(id)
        self.chrom = chrom
        self.start = start
        self.cigar = cigar
        self.mapq = mapq
        self.end: int = start  # Может быть обновлено позже на основе CIGAR
        self.flag: int = 0     # Может быть установлен при парсинге SAM

    def __repr__(self) -> str:
        """
        Возвращает строковое представление объекта выравнивания.

        Returns:
            str: Строка вида "<AlignmentRecord id=..., chrom:start-end, MAPQ=..., FLAG=...>".
        """
        return (
            f"<AlignmentRecord id={self.id}, {self.chrom}:{self.start}-{self.end}, "
            f"MAPQ={self.mapq}, FLAG={self.flag}>"
        )


class VariantRecord(Record):
    """
    Класс для представления генетического варианта (формат VCF).

    Хранит информацию о положении, референсном и альтернативном аллелях,
    а также дополнительных аннотациях.

    Attributes:
        id (str): Идентификатор вида "chrom:pos" (например, "chr1:12345").
        chrom (str): Название хромосомы.
        pos (int): Позиция варианта (1-based, как в VCF).
        ref (str): Референсный аллель (например, "A").
        alt (str): Альтернативный аллель (например, "T").
        info (dict): Словарь с дополнительной информацией из поля INFO VCF
            (например, {"DP": 30, "AF": 0.5}).
    """

    def __init__(self, chrom: str, pos: int, ref: str, alt: str, info: dict):
        """
        Инициализирует запись генетического варианта.

        Args:
            chrom (str): Название хромосомы (например, "chr1").
            pos (int): Позиция варианта (1-based, как в спецификации VCF).
            ref (str): Референсный аллель.
            alt (str): Альтернативный аллель.
            info (dict): Словарь с аннотациями из поля INFO.
        """
        super().__init__(f"{chrom}:{pos}")
        self.chrom = chrom
        self.pos = pos
        self.ref = ref
        self.alt = alt
        self.info = info

    def __repr__(self) -> str:
        """
        Возвращает строковое представление объекта варианта.

        Returns:
            str: Строка вида "<VariantRecord chrom:pos ref>alt>".
        """
        return f"<VariantRecord {self.chrom}:{self.pos} {self.ref}>{self.alt}>"