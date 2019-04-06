import requests
import xml.etree.ElementTree as ET
import json
from datetime import datetime, timedelta


class Bunch:
    """Handy dummy class which stores attributes for anything we pass into it"""
    __init__ = lambda self, **kw: setattr(self, '__dict__', kw)


def get_lightboard_config():
    try:
        overall = Bunch(projects=set(), bts=set(), ignored_bts=set())
        with open('./BoardConfig.json') as config_file:
            config_data = json.load(config_file)
            for entry in config_data:
                overall.projects.update(entry["Projects"])
                overall.bts.update(entry["Buildtypes"])
                overall.ignored_bts.update(entry["BuildtypesIgnore"])
        return Bunch(overall=overall)
    except:
        print("Failed to load BoardConfig.json: skipping")
        return None


def get_tc_builds(args):

    lightboard_config = get_lightboard_config()
    # TODO:
    # check if lightboard config is not None
    # pull data for lightboard_config.overall.projects
    # pull data for lightboard_config.overall.bts
    # dedupe by build id
    # filter out lightboard_config.overall.ignored_bts

    baseurl = f"https://{args.username}:{args.password}@buildserver.red-gate.com/httpAuth/app/rest/"
    buildsUrl = f"{baseurl}builds/"

    now = datetime.utcnow()
    weekago = now - timedelta(days=7)
    sinceDate = weekago.strftime("%Y%m%dT%H%M%SZ")

    buildsResponse = requests.get(
        buildsUrl, params={"locator": f"count:4000,sinceDate:{sinceDate}"})
    buildsResult = ET.fromstring(buildsResponse.text)
    if int(buildsResult.attrib["count"]) == 4000:
        print("too many build results and paging isn't implemented")
        exit(1)

    successCount = 0
    failureCount = 0
    otherCount = 0
    for build in buildsResult.findall("build"):
        if build.attrib["status"] == "SUCCESS":
            successCount += 1
        elif build.attrib["status"] == "FAILURE":
            failureCount += 1
        else:
            otherCount += 1

    if otherCount > 0:
        print("Got some builds which didn't fail or pass: not sure what to do here")
        exit(1)

    print(
        f"success: {successCount}, failure: {failureCount}")
    print(
        f"fail%: {100*float(failureCount)/float(failureCount + successCount)}")


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "username", help="domain user.name for teamcity (no red-gate)")
    parser.add_argument("password", help="domain password for teamcity")
    args = parser.parse_args()

    get_tc_builds(args)
