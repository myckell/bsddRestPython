import logging
import os
import sys
from bs4 import BeautifulSoup
import pandas as pd
from bsdd_rest import get_session_id, get_concepts_by_concept_type, get_children
from secrets.secrets import username, password

dirpath = os.getcwd()
sourcename = "output/concepts_by_type_NEST.xml"

concept_type = 'NEST'
concept_filter = 'ifc-2X4'
my_relationship_type = 'COLLECTS'

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
    base_tag = 'ns2:ifdconcept'
    columns = ['guid', 'ifc_name', 'source_url']
    dataframe = pd.DataFrame(columns=columns)
    concepts = content.find_all(base_tag)
    for concept in concepts:
        # guid
        guid = concept.find('guid').string

        # ifc_name
        for fullname in concept.find_all('fullnames'):
            if fullname.parent.name != base_tag:
                pass
            elif 'ifc-2X4' in str(fullname.find('languagecode')):
                ifc_name = fullname.find('name').string

        # source
        source_url = 'http://bsdd.buildingsmart.org/#concept/details/' + guid

        datacolumn = pd.Series([guid, ifc_name, source_url], index=columns)
        dataframe = dataframe.append(datacolumn, ignore_index=True)

    logger.info(str(len(dataframe)) + ' of ' + str(len(concepts)) + ' found concepts in dataframe')

    return dataframe

# def fullnames_tag_has_right_parent(tag):
#     return tag.name('fullnames') and tag.parent('ns2:ifdconceptinrelationship')
    # and not tag.has_attr('id')

def concept_relationship_to_dataframe(content, parent_guid):
    base_tag = 'ns2:ifdconceptinrelationship'
    columns = ['guid', 'ifc_name', 'ifc_definition', 'source_url', 'parent_guid']
    dataframe = pd.DataFrame(columns=columns)
    concepts = content.find_all(base_tag)

    for concept in concepts:
        # guid
        guid = concept.find('guid').string

        # ifc_name
        for fullname in concept.find_all('fullnames'):
            if fullname.parent.name != base_tag:
                pass
            elif 'ifc-2X4' in str(fullname.find('languagecode')):
                ifc_name = fullname.find('name').string

        # ifc_definition
        for definition in concept.find_all('definitions'):
            if 'ifc-2X4' in str(definition.find('languagecode')):
                ifc_definition = definition.find('description').string

        # source
        source_url = 'http://bsdd.buildingsmart.org/#concept/details/' + guid

        datacolumn = pd.Series([guid, ifc_name, ifc_definition, source_url, parent_guid], index=columns)
        dataframe = dataframe.append(datacolumn, ignore_index=True)

    logger.info(str(len(dataframe)) + ' of ' + str(len(concepts)) + ' found concepts in dataframe')

    return dataframe

def write_to_csv(dataframe, file_name):
    dataframe.to_csv(file_name, sep=";", index=False)
    logger.info('wrote content to ' + file_name)


def main():
    source_mode = 'web'
    session_id = get_session_id(username, password)


    if source_mode == 'file':
        df_all_concepts_of_type = pd.read_csv(f'./output/concepts_by_type_{concept_type}.csv', sep=";")
    elif source_mode == 'web':
        all_concepts_of_type = get_concepts_by_concept_type(session_id, concept_type, fullname_filter = concept_filter)
        df_all_concepts_of_type = concepts_to_dataframe(all_concepts_of_type)
        write_to_csv(df_all_concepts_of_type, f'./output/concepts_by_type_{concept_type}.csv')
    else:
        sys.exit('source_mode was not correct')




    # to wrap into a function
    df_all_children = pd.DataFrame(columns = ['guid', 'ifc_name', 'ifc_definition', 'source_url', 'parent_guid'])

    for concept in all_concepts_of_type.find_all ('ns2:ifdconcept'):
        concept_guid = concept.guid.string
        logger.info('working on concept ' + concept_guid)
        children_of_concept = get_children(session_id, concept_guid, my_relationship_type)
        df_children_of_concept = concept_relationship_to_dataframe(children_of_concept, concept_guid)

        df_to_edit = pd.merge(df_all_children, df_children_of_concept, on='guid')
        with pd.option_context('display.max_columns', None):  # more options can be specified also
            logger.info(df_to_edit)
        if len(df_all_children) == 0 or len(df_to_edit) == 0:
            df_all_children = df_all_children.append(df_children_of_concept, ignore_index=True)
        else:
            try:
              df_to_edit['parent_guid'] = df_to_edit['parent_guid_x'].astype(str) + ', ' + df_to_edit['parent_guid_y'].astype(str)
            except:
              logger.debug("combination of names failed for concept " + concept_guid)
              logger.debug(df_to_edit)
              pass
            list_guids_to_edit = df_to_edit['guid'].tolist()

            df_to_append = df_children_of_concept[(~df_children_of_concept.guid.isin(df_to_edit.guid))]

            df_all_children = df_all_children.append(df_to_append, ignore_index=True)
            logger.info('appended ' + str(len(df_to_append)) + ' of ' + str(len(df_children_of_concept)) + ' children')

            df_all_children = df_all_children.set_index('guid')
            df_to_edit = df_to_edit.set_index('guid')

            for guid in list_guids_to_edit:
                df_all_children.loc[str(guid)].parent_guid = df_to_edit.loc[str(guid)].parent_guid
            logger.info('edited ' + str(len(df_to_edit)) + ' of ' + str(len(df_children_of_concept)) + ' children')

            df_all_children.reset_index(level=['guid'])

        with pd.option_context('display.max_columns', None):  # more options can be specified also
            logger.info(df_all_children)

    write_to_csv(df_all_children, f'./output/children_of_concepts_by_type_{concept_type}.csv')




if __name__ == "__main__":
    main()
