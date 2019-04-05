import requests
import xml.etree.ElementTree as ET


def get_tc_builds(args):
    baseurl = f"https://{args.username}:{args.password}@buildserver.red-gate.com/httpAuth/app/rest/"
    buildsUrl = f"{baseurl}builds/"
    buildsResponse = requests.get(
        buildsUrl, params={"locator": "count:4000,sinceDate:20190401T000000+0000"})
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
