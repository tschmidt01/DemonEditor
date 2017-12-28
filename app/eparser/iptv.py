from app.eparser.bouquets import BqServiceType
from . import Channel


def parse_m3u(path):
    with open(path, encoding="utf-8") as file:
        channels = []
        count = 0
        name = None
        for line in file.readlines():
            if line.startswith("#EXTINF"):
                name = line[1 + line.index(","):].strip()
                count += 1
            elif count == 1:
                count = 0
                fav_id = " 1:0:1:0:0:0:0:0:0:0:{}:{}\n#DESCRIPTION: {}\n".format(
                    line.strip().replace(":", "%3a"), name, name, None)
                channels.append(Channel(None, None, None, name,  None, None, None, BqServiceType.IPTV.name,
                                        None, None, None, None, None, None, None, None, fav_id, None))

    return channels


if __name__ == "__main__":
    pass
