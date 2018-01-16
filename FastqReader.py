"""
A module to read fastq files
Copyright@fanjunpeng (jpfan@whu.edu.cn)
Last modified: 2018/1/12 by fan junpeng
2018/1/12 init by fanjunpeng
2018/1/13 add support for .gz
"""
import gzip
from os.path import abspath, expanduser, splitext


class FastqRecord(object):
    """
    Object to process a fastq record
    """
    def __init__(self, description, seq, desc2, quality):
        self._description = description[1:]
        self._seq = seq
        self._desc2 = desc2
        self._quality = quality

    @property
    def identifier(self):
        """
        The 1st line of FASTQ file, @ is not included
        :return:
        """
        return self._description

    @property
    def name(self):
        """
        The name of the FASTQ record, equal to the identifier
        up to the first whitespace.
        :return:
        """
        return self._description.split()[0]

    @property
    def seq(self):
        """
        The sequence of the FASTQ record, the 2nd line
        :return:
        """
        return self._seq

    @property
    def quality(self):
        """
        The quality of the sequence, the 4th line
        :return:
        """
        return self._quality

    @property
    def length(self):
        return len(self._seq)

    @classmethod
    def from_string(cls, string):
        string = string.strip()
        lines = string.splitlines()

        assert len(lines) == 4
        assert lines[0].startswith("@")
        assert lines[2].startswith("+")

        return FastqRecord(*lines)

    def __str__(self):
        return "@{}\n{}\n{}\n{}".format(self.identifier, self.seq, self._desc2, self.quality)


def check_format(filename):
    """
    check the format of file
    :param filename:
    :return:
    """
    allowed_format = [".fq", ".fastq", ".fq.gz", ".fastq.gz"]
    file_format = splitext(filename)[1]

    if file_format not in allowed_format:
        msg = "file format %r is not in %s" % (file_format, allowed_format)
        raise Exception(msg)


def yield_fastq_records(stream):
    """
    yield fastq records from stream
    :param stream: a stream object
    :return:
    """

    n = 0
    string = ""

    for line in stream:
        line = line.strip()

        if not line:
            continue

        n += 1
        string += "%s\n" % line

        if n == 4:
            n = 0
            _string = string
            string = ""
            yield FastqRecord.from_string(_string)


def open_fastq(filename):
    """
    read fastq file and return fastq records
    :param filename:
    :return:
    """
    check_format(filename)

    filename = abspath(expanduser(filename))
    mode = 'r'

    if filename.endswith(".gz"):
        stream = gzip.open(filename, mode)
    else:
        stream = open(filename, mode)

    return yield_fastq_records(stream)
