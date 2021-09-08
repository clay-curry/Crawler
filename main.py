import config
import requests
import __init__
import stats
import cache_site
import innersitecrawler


def main():
    user_wants_to_use_cache = False
    user_wants_to_run_web_crawler = False

    # Allows the user to optionally use data stored from the previous scan, if it exists.
    if cache_site.cache_exists():
        user_wants_to_use_cache = config.get_yes_no(
            f"A previous report ({config.prev_cache_file_name.split('/')[1]}) was discovered in the cache. "
            f"Would you like to use it to run the report? ")
    # Makes function call to the web crawler, or skips if the user wants to use the cache.
    if user_wants_to_use_cache:
        cache_site.make_nodes()
    elif config.get_yes_no(f"Would you like to run the web crawler at {config.DEFAULT_BASE_URL}? "):
        from datetime import datetime
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        config.persistent_data['last_checked'] = now
        innersitecrawler.start(config.DEFAULT_BASE_URL, config.DEFAULT_NUM_THREADS)
    elif config.get_yes_no(f"Would you like to scan any URL?"):
        url = input("url to scan:")
        innersitecrawler.start(url, config.DEFAULT_NUM_THREADS)
    else:
        return


    while True:
        print("\nOptions:")
        print("[1] View Excluded Links")
        print("[2] Add an Excluded Link")
        print("[3] Remove Excluded Link")
        print("[4] Run Broken Link Report")
        print("[5] Find expression")
        print("[6] Re-crawl Website")
        print("[7] Check people")
        print("[8] Save and Exit")
        response = ""
        while not response.isdigit():
            response = input()

        response = int(response)

        if response == 1:
            print("Excluded Links:")
            exclude = cache_site.get_excluded_urls()
            if len(exclude) == 0:
                print("None\n")
            else:
                i = 1
                for link in cache_site.get_excluded_urls():
                    print(f"{i}) {link}")
                    i += 1
        elif response == 2:
            print("Add an Excluded Link")
            cache_site.add_excluded_url(input("url:").strip())
        elif response == 3:
            link = input("Removing URL\nlink/index: ")
            if link.isdigit():
                if config.get_yes_no(f"Remove {cache_site.get_excluded_urls()[int(link)-1]}? "):
                    cache_site.remove_excluded_url(cache_site.get_excluded_urls()[int(link)-1])
            else:
                cache_site.remove_excluded_url(link)
        elif response == 4:
            msg = stats.print_by_location()
            print(msg)
            with open("broken nodes.txt", mode='w') as fp:
                print(msg, file=fp)
        elif response == 5:
            msg = stats.print_occurrences(input("regex:"))
            print(msg)
        elif response == 6:
            innersitecrawler.start(config.DEFAULT_BASE_URL, config.DEFAULT_NUM_THREADS)
        elif response == 7:
            stats.check_people()
        elif response == 8:
            break

    cache_site.build_cache()


if __name__ == '__main__':
    __init__.run()
    main()
    #cache_site.build_cache()
