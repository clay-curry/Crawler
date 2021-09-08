import os
import cache_site
import config
import json

cache_site.initialized = True


def run():
    try:
        if 'cache' not in os.listdir(path="."):
            os.mkdir("cache")
        if 'data.txt' in os.listdir(path="./cache"):
            # at this point, we know "cache folder" exists with previous data => both file name fields must be updated
            config.prev_cache_file_name = "cache/data.txt"
            prev_file_name_index = 0
            while f"data({prev_file_name_index + 1}).txt" in os.listdir('cache'):
                prev_file_name_index += 1
            if prev_file_name_index > 0:
                config.prev_cache_file_name = f"cache/data({prev_file_name_index}).txt"
            config.next_cache_file_name = f"cache/data({prev_file_name_index + 1}).txt"

            with open(config.prev_cache_file_name, mode='r') as prev_cache_file:
                config.persistent_data = json.loads(prev_cache_file.read())

    except OSError as e:
        raise e


run()
cache_site.build_cache()
cache_site.make_nodes()
