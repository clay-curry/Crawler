import os
import config
from typing import List
import json
from webpageNode import WebpageNode


initialized: bool = False


def get_excluded_urls() -> List[str]:
    return config.persistent_data['excluded_urls']


def add_excluded_url(url: str) -> List[str]:
    if url == '':
        return
    if url in config.persistent_data['excluded_urls']:
        return
    return config.persistent_data['excluded_urls'].append(url)


def remove_excluded_url(url: str) -> List[str]:
    if url not in config.persistent_data['excluded_urls']:
        return
    return config.persistent_data['excluded_urls'].remove(url)


def cache_exists() -> bool:
    return config.prev_cache_file_name != ""


def meta_exists() -> bool:
    return 'meta' in os.listdir(path="./cache") if cache_exists() else False


def set_nodes() -> None:
    config.persistent_data['internal'] = []
    for node in config.internal_have_visited:
        config.persistent_data['internal'].append(node.__dict__())

    config.persistent_data['external'] = []
    for node in config.external_have_visited:
        config.persistent_data['external'].append(node.__dict__())


def build_cache() -> None:
    # config.persistent_data['excluded_urls'] == already set

    with open(config.next_cache_file_name, mode='w+') as fp:

        print('{\n"excluded_urls":', file=fp)
        json.dump(config.persistent_data['excluded_urls'], fp, indent=2)

        print(',\n"internal":[', file=fp)
        first = True
        for page in config.persistent_data['internal']:
            if first:
                json.dump(page, fp, indent=2)
                first = False
            else:
                print(",", file=fp)
                json.dump(page, fp, indent=2)

        print('],\n"external":[', file=fp)
        first = True
        for page in config.persistent_data['external']:
            if first:
                json.dump(page, fp, indent=2)
                first = False
            else:
                print(",", file=fp)
                json.dump(page, fp, indent=2)
        print(']\n}', file=fp)


def remove_cache() -> None:
    if cache_exists():
        os.removedirs('cache')
        return


def make_nodes() -> None:
    for entry in config.persistent_data['internal']:
        new_node = WebpageNode(entry['url'])
        new_node.exit_url = entry['exit_url']
        new_node.base_url = entry['base_url']
        new_node.status_code = entry['status_code']
        new_node.status_history = entry['status_history']
        new_node.links = entry['links']
        new_node.text = entry['text']
        config.internal_have_visited.append(new_node)

    for entry in config.persistent_data['external']:
        new_node = WebpageNode(entry['url'])
        new_node.exit_url = entry['exit_url']
        new_node.base_url = entry['base_url']
        new_node.status_code = entry['status_code']
        new_node.status_history = entry['status_history']
        config.external_have_visited.append(new_node)


if __name__ == "__main__":
    print("running 'cache_site.py' as main")
