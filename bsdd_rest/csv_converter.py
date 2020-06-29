from bs4 import BeautifulSoup
import pandas as pd
import logging
import os
# from bsddRestPython import session_id

dirpath = os.getcwd()
sourcename = "output/concepts_by_type_NEST.xml"

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('CsvBuilder')


def get_data(source):
    assert isinstance(source, (str, list))
    if type(source) == str:
        try:
            with open(source, "r") as f:
                parsed_content = BeautifulSoup(f.read(), 'html.parser')
        except:
            print("Uuups. Something went wrong.")

    return parsed_content

def concepts_to_dataframe(content):
    dataframe = pd.DataFrame(columns=['guid', 'ifc_name', 'source'])
    concepts = content.find_all('ns2:ifdconcept')
    for concept in concepts:
        guid = concept.find('guid').text
        guid = str(guid)
        guid = guid[4:-3]

        for fullname in concept.find_all('fullnames'):
            if 'ifc-2X4' in str(fullname.find('languagecode')):
                ifc_name = fullname.find('name').text
                ifc_name = ifc_name[5:-4]

        source = 'http://bsdd.buildingsmart.org/#concept/details/' + guid

        column = pd.DataFrame([[guid, ifc_name, source]], columns=['guid', 'ifc_name', 'source'])
        dataframe = dataframe.append(column)

    dataframe = dataframe.set_index('guid')

    return dataframe


def main():
    content = get_data(sourcename)
    dataframe = concepts_to_dataframe(content)
    dataframe.to_csv(dirpath + '/' + sourcename[0:-4] + '.csv', sep=";")
    # build_pandas_dataframe()


if __name__ == "__main__":
    main()
