import requests
import sys


def main():
    try:
        response = requests.get("http://localhost:32032/status")
        if response.status_code < 200 or response.status_code >= 400:
            sys.stderr.write(
                f"Request failed with status code: {response.status_code}\n"
            )
            sys.exit(1)
    except requests.RequestException as err:
        sys.stderr.write(f"Failed to fetch URL: {err}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
