#!/usr/bin/env python
"""
This script is used to statistics on a list of fastq files
copyright@fanjunpeng (jpfan@whu.edu.cn)

2018/1/15: init by fanjunpeng

"""
import argparse
from multiprocessing import Pool
import os.path

from FastqReader import open_fastq


def get_length(filename):
    """
    get the length of record
    :param filename:
    :return:
    """
    r = []

    for record in open_fastq(filename):
        r.append(record.length)

    return r


def N(number, lengths):
    """
    return N{number} information of lengths
    :param number: 0-100
    :param lengths: a list of length
    :return:
    """
    assert lengths

    sum_length = sum(lengths)
    accu_len = 0
    accu_num = 0

    for i in sorted(lengths, reverse=True):
        accu_len += i
        accu_num += 1

        if accu_len >= sum_length*number/100:
            return i, accu_num, accu_len

    return i, accu_num, accu_len


def over(number, lengths):
    """
    return length in lengths over {number}
    :param number:
    :param lengths:
    :return:
    """
    assert lengths
    accu_len = 0
    accu_num = 0

    for i in sorted(lengths, reverse=True):
        if i < number:
            return i, accu_num, accu_len

        accu_len += i
        accu_num += 1

    return i, accu_num, accu_len


def fofn2list(fofn):
    r = []
    with open(fofn) as fh:
        for line in fh.readlines():
            line = line.strip()
            if line == '':
                continue
            if line.startswith("#"):
                continue

            r.append(line)

    return r


def fastqStat(filename, fofn=False, concurrent=1):
    """
    statistics on fastq files
    :param filename:
    :param fofn: a file contain fastq file list
    :param concurrent: concurrent process to read fastq files
    :return:
    """
    # 1. get the lengths of each fastq file
    file_list = [filename]

    if fofn:
        file_list = fofn2list(filename)

    pool = Pool(processes=concurrent)
    results = pool.map(get_length, file_list)
    pool.close()
    pool.join()

    lengths = []

    for r in results:
        lengths += r

    # write lengths out
    lengths = sorted(lengths, reverse=True)
    with open("%s.len" % os.path.basename(filename), "w") as fh:
        fh.write("\n".join(map(str, lengths)))

    # 2. get the common statistics
    total_length = sum(lengths)
    reads_number = len(lengths)
    average_length = "{0:,}".format(int(total_length / reads_number))
    longest = "{0:,}".format(lengths[0])
    _total_length = "{0:,}".format(total_length)
    reads_number = "{0:,}".format(reads_number)

    print("""\
Statistics for all fastq reads

reads number:       \t{reads_number}
sum of read length: \t{_total_length}
read average length:\t{average_length}
longest read length:\t{longest}
""".format(**locals()))

    # 2. get the N10-N90 statstics
    # length: the N{i} value; number: number of reads which length >= N{i}
    print("Distribution of read length")
    print("%5s\t%15s\t%15s\t%10s" % ("Type", "Bases", "Count", "%Bases"))
    for i in [10, 20, 30, 40, 50, 60, 70, 80, 90]:
        read_length, read_number, read_length_sum = N(i, lengths)
        print("%5s\t%15s\t%15s\t%10.2f" % ("N%s" % i,
                                           "{0:,}".format(read_length),
                                           "{0:,}".format(read_number),
                                           100.0*read_length_sum/total_length))

    # length: the sum of read length which length >= i; number: the number of read which length >= i
    for i in [1, 5, 10, 20, 30, 40, 50, 60]:
        _, read_number, read_length_sum = over(i*1000, lengths)
        print("%5s\t%15s\t%15s\t%10.2f" % (">%skb" % i,
                                           "{0:,}".format(read_length_sum),
                                           "{0:,}".format(read_number),
                                           100.0*read_length_sum/total_length))


def get_args():
    """
    get args
    :return:
    """
    args = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                   description="""
description:
    Statistics on fastq files

author:  fanjunpeng (jpfan@whu.edu.cn)
version: v0.1
        """)

    group = args.add_mutually_exclusive_group(required=True)
    group.add_argument("-i", "--input", metavar='FASTQs', nargs="+", help="fastq files")
    group.add_argument("-f", "--fofn", help="file contains path of fastq files")
    args.add_argument("-c", "--concurrent", metavar='INT', type=int, default=1, help="number of concurrent process")

    return args.parse_args()


def main():
    args = get_args()
    fastqStat(args.input, args.fofn, args.concurrent)


if __name__ == "__main__":
    main()