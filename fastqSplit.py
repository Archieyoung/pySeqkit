#!/usr/bin/env python
"""
Split fastq files by accumulated sequence length or number
Copyright@fanjunpeng (jpfan@whu.edu.cn)
"""

#from __future__ import absolute_import

import logging
import os
import argparse
from multiprocessing import Pool


from common import fofn2list, mkdir, touch
from FastqReader import open_fastq


LOG = logging.getLogger(__name__)


def split_fastq(filename, mode, number, output_dir="split", max_split=1000):
    """
    split Fastq file by {number} length per file
    :param filename: Fastq filename
    :param mode: length or number
    :param number: record length per file
    :param output_dir: the output directory of sub fastq files
    :param max_split: the max number of sub files, avoid too much sub files
    :return: list of sub file names
    """

    assert isinstance(number, int)
    assert mode in ["length", "number"]

    r = []

    head = os.path.splitext(os.path.basename(filename.rstrip(".gz")))[0]
    prefix = os.path.join(output_dir, head)

    if prefix.endswith("R1"):
        prefix = prefix.rstrip("R1")
        part = "R1."
    elif prefix.endswith("R2"):
        prefix = prefix.rstrip("R2")
        part = "R2."
    else:
        LOG.info("filename don't match '*R[12].fastq'")
        part = ""

    n = 1
    records = open_fastq(filename)

    while True:

        if n >= max_split:
            msg = "file %r cuts more than %s, break" % (filename, max_split)
            raise Exception(msg)

        out_filename = "%s%s.%sfastq" % (prefix, n, part)
        out = open(out_filename, "w")
        count = 0

        while count < number:

            try:
                record = records.next()
            except:
                break

            out.write(str(record)+"\n")
            if mode == "length":
                count += record.length
            else:
                count += 1

        out.close()

        if count == 0:
            os.remove(out_filename)  # remove the empty file
        else:
            r.append(out_filename)

        if count < number:
            break

        n += 1

    return r


def fastqSplit(filenames, mode, num, output_dir, concurrent=1, max_split=1000):
    """
    split fastq files, use multiprocess for parallel
    :param filenames: a list of fastq files
    :param mode: length or number
    :param num: 
    :param output_dir: output directory
    :param concurrent: see -h
    :param max_split: see -h
    :return: 
    """
    assert mode in ["number", "length"]
    num = int(num)

    output_dir = mkdir(output_dir)
    split_list = os.path.join(output_dir, "split_list")
    done = os.path.join(output_dir, "split_done")

    # avoid rerun
    if os.path.exists(done):
        LOG.info("%r exists, pass this step; if you want to rerun, delete the file" % done)
        return fofn2list(split_list)

    # for multiprocessing
    pool = Pool(processes=concurrent)
    results = []

    LOG.info("Split '{filenames}' by sequence {mode} =~ {num} per file".format(**locals()))

    for f in filenames:
        print("processing %s" % f)
        results.append(pool.apply_async(split_fastq, (f, mode, num, output_dir, max_split)))

    pool.close()
    pool.join()

    file_list = []
    for r in results:
        file_list += r.get()

    with open(split_list, "w") as fh:
        fh.write("\n".join(file_list))

    touch(done)
    return file_list


def set_args():
    args = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                   description="""
description:
    Split fastq files into sub files by accumulated sequence length or number

author:  fanjunpeng (jpfan@whu.edu.cn)
    """)

    args.add_argument("input", metavar="FASTQs", nargs="+", help="fastq files")
    args.add_argument("-m", "--mode", choices=["number", "length"], required=True, help="split by number or length")
    args.add_argument("-n", "--number", type=int, required=True, metavar="INT", help="the value of mode")
    args.add_argument("-o", "--output_dir", default="split", metavar="DIR", help="output directory")
    args.add_argument("-ms", "--max_split", type=int, default=6666, metavar="INT", help="the max number of sub files")
    args.add_argument("-c", "--concurrent", type=int, default=1, metavar="INT", help="number of concurrent process")
    return args.parse_args()


def main():
    args = set_args()
    filenames = args.input
    mode = args.mode
    number = args.number
    output_dir = args.output_dir
    concurrent = args.concurrent
    max_split = args.max_split

    fastqSplit(filenames, mode, number, output_dir, concurrent, max_split)


if __name__ == "__main__":
    main()
