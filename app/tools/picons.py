import glob
import os
import re
import shutil
from collections import namedtuple
from html.parser import HTMLParser

import requests

from app.commons import run_task, log
from app.settings import SettingsType
from .satellites import _HEADERS

_ENIGMA2_PICON_KEY = "{:X}:{:X}:{}"
_NEUTRINO_PICON_KEY = "{:x}{:04x}{:04x}.png"

Provider = namedtuple("Provider", ["logo", "name", "pos", "url", "on_id", "ssid", "single", "selected"])
Picon = namedtuple("Picon", ["ref", "ssid"])


class PiconsParser(HTMLParser):
    """ Parser for package html page. (https://www.lyngsat.com/packages/*provider-name*.html) """
    _BASE_URL = "https://www.lyngsat.com"

    def __init__(self, entities=False, separator=' ', single=None):

        HTMLParser.__init__(self)

        self._parse_html_entities = entities
        self._separator = separator
        self._single = single
        self._is_td = False
        self._is_th = False
        self._current_row = []
        self._current_cell = []
        self.picons = []

    def handle_starttag(self, tag, attrs):
        if tag == "td":
            self._is_td = True
        if tag == "th":
            self._is_th = True
        if tag == "img":
            self._current_row.append(attrs[0][1])

    def handle_data(self, data):
        """ Save content to a cell """
        if self._is_td or self._is_th:
            self._current_cell.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "td":
            self._is_td = False
        elif tag == "th":
            self._is_th = False

        if tag in ("td", "th"):
            final_cell = self._separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == "tr":
            row = self._current_row
            ln = len(row)

            if self._single and ln == 4 and row[0].startswith("/logo/"):
                self.picons.append(Picon(row[0].strip(), "0"))
            else:
                if ln == 9:
                    url = None
                    if row[0].startswith("/logo/"):
                        url = row[0]
                    elif row[1].startswith("/logo/"):
                        url = row[1]

                    if url and row[-3].isdigit():
                        self.picons.append(Picon(url, row[-3]))

            self._current_row = []

    def error(self, message):
        pass

    @staticmethod
    def parse(provider, picons_path, picon_ids, s_type=SettingsType.ENIGMA_2):
        """ Returns tuple(url, picon file name) list. """
        req = requests.get(provider.url, timeout=5)
        if req.status_code == 200:
            logo_data = req.text
        else:
            log("Provider picons downloading error: {} {}".format(provider.url, req.reason))
            return

        on_id, pos, ssid, single = provider.on_id, provider.pos, provider.ssid, provider.single
        neg_pos = pos.endswith("W")
        pos = int("".join(c for c in pos if c.isdigit()))
        # For negative (West) positions 3600 - numeric position value!!!
        if neg_pos:
            pos = 3600 - pos

        parser = PiconsParser(single=provider.single)
        parser.reset()
        parser.feed(logo_data)
        picons = parser.picons
        picons_data = []

        if picons:
            for p in picons:
                try:
                    if single:
                        on_id, freq = on_id.strip().split("::")
                        namespace = "{:X}{:X}".format(int(pos), int(freq))
                    else:
                        namespace = "{:X}0000".format(int(pos))
                    name = PiconsParser.format(ssid if single else p.ssid, on_id, namespace, picon_ids, s_type)
                    p_name = picons_path + (name if name else os.path.basename(p.ref))
                    picons_data.append(("{}{}".format(PiconsParser._BASE_URL, p.ref), p_name))
                except (TypeError, ValueError) as e:
                    msg = "Picons format parse error: {}".format(p) + "\n" + str(e)
                    log(msg)

        return picons_data

    @staticmethod
    def format(ssid, on_id, namespace, picon_ids, s_type):
        if s_type is SettingsType.ENIGMA_2:
            return picon_ids.get(_ENIGMA2_PICON_KEY.format(int(ssid), int(on_id), namespace), None)
        elif s_type is SettingsType.NEUTRINO_MP:
            tr_id = int(ssid[:-2] if len(ssid) < 4 else ssid[:2])
            return _NEUTRINO_PICON_KEY.format(tr_id, int(on_id), int(ssid))
        else:
            return "{}.png".format(ssid)


class ProviderParser(HTMLParser):
    """ Parser for satellite html page. (https://www.lyngsat.com/*sat-name*.html) """

    _POSITION_PATTERN = re.compile("at\s\d+\..*(?:E|W)']")
    _ONID_TID_PATTERN = re.compile("^\d+-\d+.*")
    _TRANSPONDER_FREQUENCY_PATTERN = re.compile("^\d+ [HVLR]+")
    _DOMAINS = {"/tvchannels/", "/radiochannels/", "/packages/", "/logo/"}
    _BASE_URL = "https://www.lyngsat.com"

    def __init__(self, entities=False, separator=' '):

        HTMLParser.__init__(self)
        self.convert_charrefs = False

        self._parse_html_entities = entities
        self._separator = separator
        self._is_td = False
        self._is_th = False
        self._is_onid_tid = False
        self._is_provider = False
        self._current_row = []
        self._current_cell = []
        self.rows = []
        self._ids = set()
        self._prv_names = set()
        self._positon = None
        self._on_id = None
        self._freq = None

    def handle_starttag(self, tag, attrs):
        if tag == 'td':
            self._is_td = True
        if tag == 'tr':
            self._is_th = True
        if tag == "img":
            if attrs[0][1].startswith("/logo/"):
                self._current_row.append(attrs[0][1])
        if tag == "a":
            url = attrs[0][1]
            if any(d in url for d in self._DOMAINS):
                self._current_row.append(url)
        if tag == "font" and len(attrs) == 1:
            atr = attrs[0]
            if len(atr) == 2 and atr[1] == "darkgreen":
                self._is_onid_tid = True

    def handle_data(self, data):
        """ Save content to a cell """
        if self._is_td or self._is_th:
            self._current_cell.append(data.strip())
        if self._is_onid_tid:
            m = self._ONID_TID_PATTERN.match(data)
            if m:
                self._on_id, tid = m.group().split("-")
            self._is_onid_tid = False

    def handle_endtag(self, tag):
        if tag == 'td':
            self._is_td = False
        elif tag == 'tr':
            self._is_th = False

        if tag in ('td', 'th'):
            final_cell = self._separator.join(self._current_cell).strip()
            self._current_row.append(final_cell)
            self._current_cell = []
        elif tag == 'tr':
            row = self._current_row
            # Satellite position
            if not self._positon:
                pos = re.findall(self._POSITION_PATTERN, str(row))
                if pos:
                    self._positon = "".join(c for c in str(pos) if c.isdigit() or c in ".EW")

            len_row = len(row)
            if len_row > 2:
                m = self._TRANSPONDER_FREQUENCY_PATTERN.match(row[1])
                if m:
                    self._freq = m.group().split()[0]

            if len_row == 14:
                # Providers
                name = row[6]
                self._prv_names.add(name)
                m = self._ONID_TID_PATTERN.match(str(row[9]))
                if m:
                    on_id, tid = m.group().split("-")
                    if on_id not in self._ids:
                        row[-2] = on_id
                        self._ids.add(on_id)
                        row[0] = self._positon
                    if name + on_id not in self._prv_names:
                        self._prv_names.add(name + on_id)
                        logo_data = None
                        req = requests.get(self._BASE_URL + row[3], timeout=5)
                        if req.status_code == 200:
                            logo_data = req.content
                        else:
                            log("Downloading provider logo error: {}".format(req.reason))
                        self.rows.append(Provider(logo=logo_data, name=name, pos=self._positon, url=row[5], on_id=on_id,
                                                  ssid=None, single=False, selected=True))
            elif 6 < len_row < 14:
                # Single services
                name, url, ssid = None, None, None
                if row[0].startswith("http"):
                    name, url, ssid = row[1], row[0], row[0]
                elif row[1].startswith("http"):
                    name, url, ssid = row[2], row[1], row[0]

                if name and url:
                    on_id = "{}::{}".format(self._on_id if self._on_id else "1", self._freq)
                    self.rows.append(Provider(logo=None, name=name, pos=self._positon, url=url, on_id=on_id,
                                              ssid=ssid, single=True, selected=False))

            self._current_row = []

    def error(self, message):
        pass

    def reset(self):
        super().reset()


def parse_providers(url):
    """ Returns a list of providers sorted by logo [single channels after providers]. """
    parser = ProviderParser()

    request = requests.get(url=url, headers=_HEADERS)
    if request.status_code == 200:
        parser.feed(request.text)
    else:
        log("Parse providers error [{}]: {}".format(url, request.reason))

    def srt(p):
        if p.logo is None:
            return 1
        return 0

    providers = parser.rows
    providers.sort(key=srt)

    return providers


def download_picon(src_url, dest_path, callback):
    """ Downloads and saves the picon to file.  """
    err_msg = "Picon download error: {}  [{}]"
    timeout = (3, 5)  # connect and read timeouts

    if callback:
        callback("Downloading: {}.\n".format(os.path.basename(dest_path)))

    req = requests.get(src_url, timeout=timeout, stream=True)
    if req.status_code != 200:
        err_msg = err_msg.format(src_url, req.reason)
        log(err_msg)
        if callback:
            callback(err_msg + "\n")
    else:
        try:
            with open(dest_path, "wb") as f:
                for chunk in req:
                    f.write(chunk)
        except OSError as e:
            err_msg = "Saving picon [{}] error: {}".format(dest_path, e)
            log(err_msg)
            if callback:
                callback(err_msg + "\n")


@run_task
def convert_to(src_path, dest_path, s_type, callback, done_callback):
    """ Converts names format of picons.

        Copies resulting files from src to dest and writes state to callback.
    """
    pattern = "/*_0_0_0.png" if s_type is SettingsType.ENIGMA_2 else "/*.png"
    for file in glob.glob(src_path + pattern):
        base_name = os.path.basename(file)
        pic_data = base_name.rstrip(".png").split("_")
        dest_file = _NEUTRINO_PICON_KEY.format(int(pic_data[4], 16), int(pic_data[5], 16), int(pic_data[3], 16))
        dest = "{}/{}".format(dest_path, dest_file)
        callback('Converting "{}" to "{}"\n'.format(base_name, dest_file))
        shutil.copyfile(file, dest)

    done_callback()


if __name__ == "__main__":
    pass
