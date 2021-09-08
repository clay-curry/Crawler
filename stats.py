import config
import re
from html.parser import HTMLParser
import requests
from webpageNode import WebpageNode
from typing import List, Dict

initialized: bool = False

successful: List[WebpageNode] = []
timeouts: List[WebpageNode] = []
redirected: List[WebpageNode] = []
excluded: List[WebpageNode] = []
client_errors: List[WebpageNode] = []
server_errors: List[WebpageNode] = []
unknown: List[WebpageNode] = []

people_node: WebpageNode = None
faculty_node: WebpageNode = None
emeriti_node: WebpageNode = None
postdoc_node: WebpageNode = None
gradstudent_node: WebpageNode = None
staff_node: WebpageNode = None
affiliates_node: WebpageNode = None


def initialize() -> None:
    global initialized
    if initialized:
        return
    initialized = True

    global excluded
    global people_node
    global faculty_node
    global emeriti_node
    global postdoc_node
    global gradstudent_node
    global staff_node
    global affiliates_node

    excluded = config.persistent_data['excluded_urls']

    for node in config.internal_have_visited:
        organize_by_status_code(node)
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people":
            people_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/faculty":
            faculty_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/emeriti":
            emeriti_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/post-docs":
            postdoc_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/grad-students":
            gradstudent_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/staff":
            staff_node = node
        if node.exit_url == "https://ou.edu/cas/physics-astronomy/people/affiliates":
            affiliates_node = node

    for node in config.external_have_visited:
        organize_by_status_code(node)


def organize_by_status_code(node: WebpageNode) -> None:
    global timeouts
    global redirected
    global client_errors
    global server_errors
    global unknown

    if node in config.persistent_data['excluded_urls']:
        return
    elif node.status_code < 200:
        unknown.append(node)
    elif node.status_code < 300:
        global successful
        successful.append(node)
    elif node.status_code < 400:
        redirected.append(node)
    elif node.status_code < 500:
        client_errors.append(node)
    elif node.status_code < 600:
        server_errors.append(node)
    else:
        unknown.append(node)


def print_node_error(broken_node: WebpageNode) -> str:
    msg = f"✗ {broken_node} ({broken_node.status_code}: "
    if broken_node.status_code in requests.status_codes._codes.keys():
        msg += requests.status_codes._codes[broken_node.status_code][0] + ")"
    else:
        msg += "unknown, probably my fault)"
    return msg


def print_message() -> str:
    global successful
    global timeouts
    global redirected
    global excluded
    global client_errors
    global server_errors
    global unknown

    msg = f"Link Checker Report" + '\n'
    msg += "📝 Summary" + '\n'
    msg += "----------------------" + '\n'
    msg += f"🔍 Total..........{len(config.internal_have_visited) + len(config.external_have_visited)}" + '\n'
    msg += f"✅ Successful......{len(successful)}" + '\n'
    msg += f"⏳ Timeouts.......{0}" + '\n'
    msg += f"🔀 Redirected.......{len(redirected)}" + '\n'
    msg += f"👻 Excluded.........{len(excluded)}" + '\n'
    msg += f"🚫 Client Errors....{len(client_errors)}" + '\n'
    msg += f"Server Errors.......{len(server_errors)}" + '\n'
    msg += f"Unknown Errors......{len(unknown)}" + '\n'
    msg += '\n'

    return msg


def print_by_location() -> List[str]:
    global successful
    global timeouts
    global redirected
    global client_errors
    global server_errors
    global unknown
    initialize()
    broken_union = timeouts + redirected + client_errors + server_errors + unknown
    # Make a dict of parents to broken children
    broken_msg_entries: Dict[WebpageNode, List[WebpageNode]] = {}
    for site_node in config.internal_have_visited:
        broken_msg_entries[site_node] = []
        for link in site_node.links:
            for i in range(len(broken_union)):
                if link == broken_union[i] and link not in excluded:
                    broken_msg_entries[site_node].append(broken_union[i])
        if len(broken_msg_entries[site_node]) == 0:
            del broken_msg_entries[site_node]

    msg = ""
    for site_node in broken_msg_entries.keys():
        msg += f"The crawler discovered {len(broken_msg_entries[site_node])} broken links at {site_node}\n"
        for broken_node in broken_msg_entries[site_node]:
            msg += print_node_error(broken_node) + "\n"
        msg += "\n"
    return msg


def print_occurrences(regex: str = ""):
    initialize()
    expression = re.compile(pattern=regex)
    msg = ""
    for page in config.internal_have_visited:
        occurrences = expression.findall(page.text)
        if len(occurrences) > 0:
            msg += f"pattern discovered at {page}:\n"
            for occurrence in occurrences:
                msg += f"  - {str(occurrence)}\n"
    return msg


def check_people():
    global people_node
    global faculty_node
    global emeriti_node
    global postdoc_node
    global gradstudent_node
    global staff_node
    global affiliates_node

    initialize()
    # use People to make a list of Faculty, Emeriti, Post Docs, Grad Students, Staff, Affiliates
    person_position_parser = \
        re.compile('<b>(.*?)\\s*?-\\s*?.{0,100}(Emeritus|Affiliate|Professor|Staff|Graduate Student|Post)')

    people = person_position_parser.findall(people_node.text)
    faculty = person_position_parser.findall(faculty_node.text)
    emeriti = person_position_parser.findall(emeriti_node.text)
    postdoc = person_position_parser.findall(postdoc_node.text)
    gradstudent = person_position_parser.findall(gradstudent_node.text)
    staff = person_position_parser.findall(staff_node.text)
    affiliate = person_position_parser.findall(affiliates_node.text)

    for p in [p for p in people if p[1] == "Professor"]:
        if p not in faculty:
            print(f"{p} is not in faculty")

    for p in [p for p in people if p[1] == "Emeritus"]:
        if p not in emeriti:
            print(f"{p} is not in emeriti")

    for p in [p for p in people if p[1] == "Post"]:
        if p not in postdoc:
            print(f"{p} is not in post doc")

    for p in [p for p in people if p[1] == "Graduate Student"]:
        if p not in gradstudent:
            print(f"{p} is not in grad student")

    for p in [p for p in people if p[1] == "Staff"]:
        if p not in staff:
            print(f"{p} is not in staff")

    for p in [p for p in people if p[1] == "Affiliate"]:
        if p not in affiliate:
            print(f"{p} is not in affiliate")


if __name__ == "__main__":
    import cache_site as c
    c.init()
    prev = c.persistent_data.get('prev')
