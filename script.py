import requests
import xml.etree.ElementTree as ET
from jsoncomment import JsonComment
from datetime import datetime, timedelta
from pprint import pprint
from collections import Counter, namedtuple

LightboardConfig = namedtuple("LightboardConfig", ["overall"])

LightboardSection = namedtuple(
    "LightboardSection", ["projects", "bts", "ignored_bts"])

TeamcityBuild = namedtuple("TeamcityBuild", ["id", "build_type_id", "status"])


def get_lightboard_config():
    try:
        overall = LightboardSection(
            projects=set(), bts=set(), ignored_bts=set())
        with open('./BoardConfig.json') as config_file:
            # we use jsoncomment instead of stdlib json since the file contains trailing commas
            config_data = JsonComment().load(config_file)
            for entry in config_data:
                overall.projects.update(entry.get("Projects", []))
                overall.bts.update(entry.get("Buildtypes", []))
                overall.ignored_bts.update(entry.get("BuildtypesIgnore", []))
        return LightboardConfig(overall)
    except Exception as e:
        raise Exception("Failed to load BoardConfig.json") from e


def get_tc_builds(username, password, projectId=None, buildTypeId=None):
    baseurl = f"https://{args.username}:{args.password}@buildserver.red-gate.com/httpAuth/app/rest/"
    buildsUrl = f"{baseurl}builds/"
    maxResultCount = 4000

    now = datetime.utcnow()
    weekago = now - timedelta(days=7)
    sinceDate = weekago.strftime("%Y%m%dT%H%M%S+0000")

    locator = f"count:{maxResultCount},sinceDate:{sinceDate}"
    if buildTypeId is not None:
        locator += ",buildType:id:"+buildTypeId
    elif projectId is not None:
        locator += ",project:id:"+projectId

    buildsResponse = requests.get(
        buildsUrl, params={"locator": locator})
    if not buildsResponse:
        raise Exception("Error from teamcity: " + buildsResponse.text)

    buildsResult = ET.fromstring(buildsResponse.text)
    if int(buildsResult.attrib["count"]) == maxResultCount:
        raise Exception("too many build results and paging isn't implemented")

    buildElements = buildsResult.findall("build")
    return list(map(lambda be: TeamcityBuild(
        id=be.attrib["id"],
        build_type_id=be.attrib["buildTypeId"],
        status=be.attrib["status"]
    ), buildElements))


def get_all_tc_builds(args):

    lightboard_config = get_lightboard_config()

    # pull data for lightboard_config.overall.projects
    # pull data for lightboard_config.overall.bts
    # dedupe by build id
    # filter out lightboard_config.overall.ignored_bts

    allBuilds = []
    print("sending requests to teamcity: ")
    for project in lightboard_config.overall.projects:
        allBuilds.extend(get_tc_builds(
            args.username, args.password, projectId=project))
        print(".", end="", flush=True)
    for buildType in lightboard_config.overall.bts:
        allBuilds.extend(get_tc_builds(
            args.username, args.password, buildTypeId=buildType))
        print(".", end="", flush=True)

    print("\n")
    print(f"Got {len(allBuilds)} builds before filtering...")
    # use a dictionary comprehension to dedupe builds by build id
    allBuilds = list({b.id: b for b in allBuilds}.values())
    print(f"...deduped to {len(allBuilds)}...")
    allBuilds = list(filter(
        lambda b: b.build_type_id not in lightboard_config.overall.ignored_bts, allBuilds))
    print(f"...and {len(allBuilds)} after filtering.")

    failTypes = Counter()

    successCount = 0
    failureCount = 0
    otherCount = 0
    for build in allBuilds:
        if build.status == "SUCCESS":
            successCount += 1
        elif build.status == "FAILURE":
            failureCount += 1
            failTypes[build.build_type_id] += 1
        else:
            otherCount += 1

    if otherCount > 0:
        print("Got some builds which didn't fail or pass: not sure what to do here")
        exit(1)

    print(
        f"success: {successCount}, failure: {failureCount}")
    print(
        f"fail%: {100*float(failureCount)/float(failureCount + successCount)}")
    print("Most failed build types:")
    pprint(failTypes)


if __name__ == '__main__':
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument(
        "username", help="domain user.name for teamcity (no red-gate)")
    parser.add_argument("password", help="domain password for teamcity")
    args = parser.parse_args()

    get_all_tc_builds(args)
