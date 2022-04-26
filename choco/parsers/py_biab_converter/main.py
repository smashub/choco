import os
import pprint

from choco.parsers.py_biab_converter.biab_reader import *

FILE_PATH = '/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData/African ' \
            'Journey_id_06916_allanah.MGU '

ALL_FILES_PATH = '/Users/andreapoltronieri/Downloads/BiabInternetCorpus2014-06-04/allBiabData'

if __name__ == '__main__':

    filelist = []
    success = 0
    error = 0

    for filename in os.listdir(ALL_FILES_PATH):
        with open(os.path.join(ALL_FILES_PATH, filename), 'r') as f:
            filelist.append(f"{str(f.name)}")
    # print(filelist)
    if len(filelist) > 0:
        for f in filelist:
            try:
                read_biab_file(f)
                print(pprint.pprint(read_biab_file(f)))
                success += 1
            except Exception as ex:
                error += 1
                print(f)
                print(ex)

    else:
        print(pprint.pprint(read_biab_file(
            FILE_PATH)))

    print(f'Parsed correctly {success}\nEncountered {error} errors')
