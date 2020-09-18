import logging
import requests
import os
from bs4 import BeautifulSoup
from secrets.secrets import username, password

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('RestAPI')

# configuration
concept_guid = '2VWFE0qXKHuO00025QrE$V' # guid for pset_wall_common
concept_type = 'NEST'
my_relationship_type = 'COLLECTS'
response_type = 'application/json'

api_url_base = 'http://bsdd.buildingsmart.org/api/4.0'

concept_filter = 'ifc-2X4'


def get_session_id(username, password, response_type = 'application/json'):
    api_url_login = '/session/login'
    data = {
        'email': username,
        'password': password,
        'content-type': response_type
    }

    login_response = requests.post(api_url_base + api_url_login, data=data)
    logger.info(login_response.cookies)
    my_session_cookie = login_response.cookies
    session_id = my_session_cookie.__dict__['_cookies']['.bsdd.buildingsmart.org']['/']['peregrineapisessionid']
    session_id = session_id.__dict__['value']
    logger.info('session-id: ' + session_id)

    return session_id


def get_concept_by_concept_id(session_id, concept_guid, response_type = 'application/json'):
    api_url_concept = f'/IfdConcept/{concept_guid}'
    params = {
        'peregrineapisessionid': session_id,
        'guid': concept_guid
    }
    header = {
        'content-type': response_type
    }

    received_concept = requests.get(
        api_url_base + api_url_concept,
        params=params,
        headers=header
    )

    return received_concept


def get_page_by_page_id(session_id, page_id, concept_type, response_type = 'application/json'):
    api_url_concept_filter = f'/IfdConcept/filter/{concept_type}'
    params = {
        'peregrineapisessionid': session_id,
        'concept_type': concept_type
    }
    header = {
        'Cookie' : 'peregrineapisessionid=' + session_id,
        'Content-Type' : response_type
    }

    if page_id != 'first_page':
        params["page"] = page_id

    received_page = requests.get(
        api_url_base + api_url_concept_filter,
        params=params,
        headers=header
    )

    return received_page


def get_concepts_by_concept_type(session_id, concept_type, response_type = 'application/json', fullname_filter = None, max_pages = None):
    assert isinstance(fullname_filter, str)
    page_id = 'first_page'
    page_count = 0
    concept_count = 0
    all_concepts_of_type = BeautifulSoup('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><ifdconcepts></ifdconcepts>', 'html.parser')

    if fullname_filter:
        logger.info('concept filter set to ' + fullname_filter)
    else:
        logger.info('no filter set')

    while page_id:
        received_page = get_page_by_page_id(session_id, page_id, concept_type)
        parsed_content = BeautifulSoup(received_page.content, 'html.parser')

        concepts_on_page = parsed_content.find_all('ns2:ifdconcept')

        for concept in concepts_on_page:
            if fullname_filter:
                for fullname in concept.find_all('fullnames'):
                    if fullname_filter in str(fullname) and 'Pset_' in fullname.find('name').string:
                        all_concepts_of_type.ifdconcepts.append(concept)
                        concept_count += 1
            else:
                all_concepts_of_type.ifdconcepts.append(concept)
                concept_count += 1

        page_id = received_page.headers.get('Next-Page')
        page_count += 1
        logger.info('found ' + str(len(concepts_on_page)) + ' concepts on page ' + str(page_count))

        if max_pages:
            if page_count == max_pages:
                break

    logger.info('got ' + str(concept_count) + ' concepts by filter for export')

    return all_concepts_of_type




def get_children(session_id, parent_guid, relationship_type, response_type = 'application/json'):
    api_url_concept_children = f'/IfdConcept/{parent_guid}/children/{relationship_type}'
    params = {
        'peregrineapisessionid': session_id,
        'guid': parent_guid,
        'relationship_type': relationship_type
    }
    header = {
        'Cookie' : 'peregrineapisessionid=' + session_id,
        'Content-Type' : response_type
    }

    received_page = requests.get(
        api_url_base + api_url_concept_children,
        params=params,
        headers=header
    )

    children = BeautifulSoup(received_page.content, 'html.parser')

    return children


def write_to_xml (content, output_path = os.getcwd(), file_name_extension = ''):
    file_path = f'{output_path}'
    print(content)
    file_name = f'/output/concepts_{file_name_extension}.xml'
    with open(file_path + file_name, 'w', encoding='utf-8') as file:
        file.write(str(content.prettify()))


def main():
    session_id = get_session_id(username, password)
    all_concepts_of_type = get_concepts_by_concept_type(session_id, concept_type, fullname_filter = concept_filter, max_pages = 1)
    write_to_xml(all_concepts_of_type, file_name_extension = concept_type)


if __name__ == "__main__":
    main()
