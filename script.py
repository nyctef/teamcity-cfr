import requests


def get_tc_builds(args):
    baseurl = f"https://{args.username}:{args.password}@buildserver.red-gate.com/httpAuth/app/rest/"
    print(baseurl)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "username", help="domain user.name for teamcity (no red-gate)")
    parser.add_argument("password", help="domain password for teamcity")
    args = parser.parse_args()

    get_tc_builds(args)
