import requests
from bs4 import BeautifulSoup
import logging
from secrets.secrets import username, password

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('RestAPI')

# configuration
concept_guid = '1yoC2q3nn6lQ0yog8mbuQa'
concept_type = 'NEST'
relationship_type = 'COLLECTS'
content_type = 'application/json'

api_url_base = 'http://test.bsdd.buildingsmart.org/api/4.0'
api_url_login = '/session/login'
api_url_concept = f'/IfdConcept/{concept_guid}'
api_url_concept_filter = f'/IfdConcept/filter/{concept_type}'
api_url_concept_children = f'/IfdConcept/{concept_guid}/children/{relationship_type}'


def get_session_id():
    data = {
        'email': username,
        'password': password,
        'content-type': content_type
    }

    login_response = requests.post(api_url_base + api_url_login, data=data)
    logger.info(login_response.cookies)
    my_session_cookie = login_response.cookies
    session_id = my_session_cookie.__dict__['_cookies']['.test.bsdd.buildingsmart.org']['/']['peregrineapisessionid']
    session_id = session_id.__dict__['value']
    logger.info('session-id: ' + session_id)

    return session_id


def get_concept_by_concept_id(session_id):
    params = {
        'peregrineapisessionid': session_id,
        'guid': concept_guid
    }
    header = {
        'content-type': content_type
    }

    received_concept = requests.get(
        api_url_base + api_url_concept,
        params=params,
        headers=header
    )

    return received_concept


def get_page_by_page_id(session_id, page_id):
    params = {
        'peregrineapisessionid': session_id,
        'concept_type': concept_type
    }
    header = {
        'Cookie' : 'peregrineapisessionid=' + session_id,
        'Content-Type' : content_type
    }

    if page_id != 'first_page':
        params["page"] = page_id

    received_page = requests.get(
        api_url_base + api_url_concept_filter,
        params=params,
        headers=header
    )

    return received_page


def get_concepts_by_concept_type(session_id):
    page_id = 'first_page'
    page_count = 0
    all_concepts_of_type = None
    concept_count = 0

    while page_id:
        received_page = get_page_by_page_id(session_id, page_id)
        parsed_content = BeautifulSoup(received_page.content, 'html.parser')

        if page_id == 'first_page':
            all_concepts_of_type = parsed_content
            for concept in parsed_content.find_all('ns2:ifdconcept'):
                concept_count += 1
        else:
            for concept in parsed_content.find_all('ns2:ifdconcept'):
                all_concepts_of_type.ifdconcepts.append(concept)
                concept_count += 1
        page_id = received_page.headers.get('Next-Page')

        page_count += 1
        if page_count == 2:
            break

    logger.info('received number of concepts ' + str(concept_count))

    return all_concepts_of_type


def get_children(session_id):
    params = {
        'peregrineapisessionid': session_id,
        'guid': guid,
        'relationship_type': relationship_type
    }
    header = {
        'Cookie' : 'peregrineapisessionid='+session_id,
        'Content-Type' : content_type
    }

    children = requests.get(
        api_url_base + api_url_concept_children,
        params=params,
        headers=header
    )
    logger.debug(children.headers)
    logger.debug(children.content)


def write_to_xml (content, typeOfData):
    file_path = f'./output/'
    file_name = f'concepts_by_type_{typeOfData}.xml'
    with open(file_path + file_name, 'w', encoding='utf-8') as file:
        file.write(str(content.prettify()))


def main():
    session_id = get_session_id()
    all_concepts_of_type = get_concepts_by_concept_type(session_id)
    write_to_xml(all_concepts_of_type, concept_type)
    # children(session_id)


if __name__ == "__main__":
    main()
