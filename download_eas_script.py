import ssl
import socket
import sys
import os
import argparse
import base64
import ast
import csv
import io
import time
import datetime
import tarfile

import xml.etree.ElementTree as etree

try:
    from httplib import HTTPSConnection
    import httplib as httplib
    import urllib as urllib
except:
    from http.client import HTTPSConnection
    import http.client as httplib
    import urllib.request as urllib

try:
    sslcontext = ssl._create_unverified_context()
except:
    sslcontext = None


def check_content_length(rec):
    if "Content-Length" in rec:
        return True
    elif "content-length" in rec:
        return True
    elif "Content-Length" in rec:
        return True
    return False


def get_content_length(rec):
    if "Content-Length" in rec:
        return int(rec["Content-Length"])
    elif "content-length" in rec:
        return int(rec["content-length"])
    elif "Content-Length" in rec:
        return int(rec["Content-Length"])
    return -1


def getauthorization(username, password):
    return "Basic {}".format(base64.b64encode("{}:{}".format(username, password).encode()).decode("ascii"))


class HTTPSConnectionV3(HTTPSConnection):
    def __init__(self, *args, **kwargs):
        httplib.HTTPSConnection.__init__(self, *args, **kwargs)

    def connect(self):
        sock = socket.create_connection((self.host, self.port), self.timeout)
        if self._tunnel_host:
            self.sock = sock
            self._tunnel()
        ssl_version_list = [ssl.PROTOCOL_SSLv2, ssl.PROTOCOL_SSLv3, ssl.PROTOCOL_SSLv23, ssl.PROTOCOL_TLSv1]

        for ssl_i in ssl_version_list:
            try:
                self.sock = ssl.wrap_socket(
                    sock, self.key_file, self.cert_file, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv3
                )
                break
            except ssl.SSLError as e:
                print("Failed:" + ssl._PROTOCOL_NAMES[ssl_i])


#            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, cert_reqs=ssl.CERT_NONE, ssl_version=ssl.PROTOCOL_SSLv23)
#            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv23)
#            self.sock = ssl.wrap_socket(sock, self.key_file, self.cert_file, ssl_version=ssl.PROTOCOL_SSLv2)


BASE_EAS_URL = "https://eas-dps-rest-ops.esac.esa.int/REST?class_name="
BASE_DSS_URL = "https://euclidsoc.esac.esa.int/"
BASE_DSS_HOST = "euclidsoc.esac.esa.int"
BASE_DSS_PORT = 443
buffer_size = 16 * 1024
PRODUCT_ID_FIELD = "Header.ProductId.LimitedString"
MATCH_ALL_PRODUCT_FILTER = PRODUCT_ID_FIELD + '!=""'


def geturl(inpstring):
    url = ""
    jobstatus = ""
    try:
        retdic = ast.literal_eval(inpstring)
        #       print(retdic)
        if "url" in retdic:
            url = retdic["url"]
        if "status" in retdic:
            jobstatus = retdic["status"]
    #       print(url,jobstatus)
    except:
        print("Can not decode string: %s" % inpstring)
        exit()
    return url, jobstatus


def checkasyjob(url, auth):
    finished = False
    while True:
        time.sleep(1.0)
        request = urllib.Request(url)
        request.add_header("Authorization", auth)
        easResponse = urllib.urlopen(request)
        jobresponse = easResponse.read().decode()
        url, jobstatus = geturl(jobresponse)
        if jobstatus == "FINISHED":
            finished = True
            break
        elif jobstatus == "ERROR":
            break
    return url, finished


def build_eas_query(base_url, product_type, product_query, project, fields=None, file_format=None):
    query_parts = [base_url + product_type]
    query_parts.append(product_query.strip("&") or MATCH_ALL_PRODUCT_FILTER)
    query_parts.extend(["make_asy=True", "PROJECT=" + project])
    if file_format:
        query_parts.append("file_format=" + file_format)
    if fields:
        query_parts.append("fields=" + fields)
    return "&".join(query_parts)


def submit_async_query(product_query, auth):
    print("Query submitted at %s" % datetime.datetime.now())
    request = urllib.Request(product_query)
    request.add_header("Authorization", auth)
    easResponse = urllib.urlopen(request)
    jobresponse = easResponse.read().decode()
    url, jobstatus = geturl(jobresponse)
    url, finished = checkasyjob(url, auth)
    print("Job finished on server side at %s" % datetime.datetime.now())
    if not finished:
        raise RuntimeError("EAS async query failed")
    return url


def read_async_result(url, auth):
    request = urllib.Request(url)
    request.add_header("Authorization", auth)
    return urllib.urlopen(request)


def get_product_ids(base_url, product_type, product_query, project, username, password):
    auth = getauthorization(username, password)
    lookup_query = build_eas_query(
        base_url,
        product_type,
        product_query,
        project,
        fields=PRODUCT_ID_FIELD,
    )
    result_url = submit_async_query(lookup_query, auth)
    result_text = read_async_result(result_url, auth).read().decode()
    rows = list(csv.reader(io.StringIO(result_text)))
    if rows and rows[0] and "productid" in rows[0][0].lower():
        rows = rows[1:]

    product_ids = []
    seen = set()
    for row in rows:
        if not row:
            continue
        product_id = row[0].strip()
        if product_id and product_id not in seen:
            product_ids.append(product_id)
            seen.add(product_id)
    return product_ids


def getMetadataXml(base_url, product_type, product_query, project, username, password):
    metadata_query = build_eas_query(
        base_url,
        product_type,
        product_query,
        project,
        file_format="TGZ",
    )
    auth = getauthorization(username, password)
    result_url = submit_async_query(metadata_query, auth)
    easResponse = read_async_result(result_url, auth)
    timestamp = f"{datetime.datetime.now():%Y-%m-%dT%H:%M:%S.%f}"
    output_tgz = product_type + timestamp + ".tgz"
    with open(output_tgz, "wb") as f_out:
        f_out.write(easResponse.read())
    cip = 0
    ret_p = []
    if tarfile.is_tarfile(output_tgz):
        tarxml = tarfile.open(output_tgz, "r:gz")
        for i_file in tarxml.getmembers():
            i_f = tarxml.extractfile(i_file)
            if i_f:
                i_f_content = i_f.read().decode()
                if len(i_f_content.strip()) > 0:
                    ret_p.append(i_f_content)
                    cip = cip + 1
    else:
        errorfile = f"ERROR-{timestamp}"
        os.rename(output_tgz, errorfile)
        print(f"Error in executing query, see {errorfile}")
        return [], None
    print("Data products metadata retrieved at %s" % datetime.datetime.now())
    #  print(productList)
    # Workaround for the EAS response, when a list of products is provided
    #  productList = productList.replace('<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="UTF-8"?><dummyRoot>') + "</dummyRoot>"
    #  root_elem = etree.fromstring(productList)
    print("Found %d data products" % cip)
    return ret_p, output_tgz


def chunk_product_ids(product_ids, chunk_size):
    for index in range(0, len(product_ids), chunk_size):
        yield product_ids[index : index + chunk_size]


def build_chunk_query(product_query, product_ids):
    product_filter = "%s=includes(%s)" % (PRODUCT_ID_FIELD, ",".join(product_ids))
    return "&".join(part for part in (product_query.strip("&"), product_filter) if part)


def downloadDssFile(base_url, fname, username=None, password=None, output_directory="."):
    headers = {}
    if username and password:
        headers["Authorization"] = "Basic %s" % (
            base64.b64encode(b"%s:%s" % (username.encode("utf-8"), password.encode("utf-8"))).decode("utf-8")
        )
    headers["pragma"] = "DSSGET"
    os.makedirs(output_directory, exist_ok=True)
    output_path = os.path.join(output_directory, os.path.basename(fname))
    if sslcontext:
        conn = HTTPSConnection(BASE_DSS_HOST, BASE_DSS_PORT, context=sslcontext)
    else:
        conn = HTTPSConnection(BASE_DSS_HOST, BASE_DSS_PORT)
    conn.request("GET", "/" + fname, headers=headers)
    response = conn.getresponse()
    recvheader = {}
    for k, v in dict(response.getheaders()).items():
        recvheader[k.lower()] = v
    #  response = requests.get(fileurl, auth=(username, password))
    if response.status == 200:
        try:
            total_length = get_content_length(recvheader) if check_content_length(recvheader) else None
            downloaded_length = 0
            with open(output_path, "wb") as f:
                data = response.read(buffer_size)
                while data:
                    downloaded_length += len(data)
                    f.write(data)
                    if total_length:
                        done = min(50, int(50.0 * downloaded_length / total_length))
                        sys.stdout.write("\r[%s%s]" % ("=" * done, " " * (50 - done)))
                        sys.stdout.flush()
                    data = response.read(buffer_size)
            if total_length and downloaded_length < total_length:
                sys.stdout.write("Wrong size for file %s - need %d, got %d\n" % (fname, total_length, downloaded_length))
            sys.stdout.write("\n")
        except Exception as e:
            if os.path.isfile(output_path):
                os.remove(output_path)
            print("Can't write file %s - error %s" % (fname, str(e)))
    elif response.status == 403:
        sys.stdout.write("Wrong username or password supplied, exiting\n")
        conn.close()
        exit()
    elif response.status == 404:
        reason = ""
        if hasattr(response, "reason"):
            reason = response.reason
        out_message = "File %s not found: %s\n" % (fname, reason)
        sys.stdout.write(out_message)
    else:
        reason = ""
        if hasattr(response, "reason"):
            reason = response.reason
        out_message = "File %s can not be downloaded: %s\n" % (fname, reason)
        sys.stdout.write(out_message)
    conn.close()
    del conn


def saveMetaAndData(
    products,
    username=None,
    password=None,
    product_type="UNKNOWN",
    xml_output_directory="eas-xml",
    data_output_directory="eas-data",
    download_xml=True,
    download_data=False,
):
    if download_xml:
        os.makedirs(xml_output_directory, exist_ok=True)
    if download_data:
        os.makedirs(data_output_directory, exist_ok=True)

    count = 0
    downloaded_files = set()
    for p in products:
        # findProductId = etree.XPath("//ProductId")
        # findFiles = etree.XPath("//FileName")

        root = etree.XML(p)
        ptype_node = root.find(".//ProductType")
        pid_node = root.find(".//ProductId")
        if ptype_node:
            ptype = ptype_node.text
        else:
            ptype = product_type
        if hasattr(pid_node, "text") and pid_node.text:
            pid = pid_node.text
        else:
            id_node = root.find(".//Id")
            if id_node:
                pid = id_node.text
            else:
                pid = str(count)
        pfile = ptype[0].upper() + ptype[1:] + "__" + pid + ".xml"
        if download_xml:
            output_path = os.path.join(xml_output_directory, pfile)
            print("Saving " + output_path)
            with open(output_path, "w") as f:
                f.write(p)

        files = [f.text for f in root.findall(".//FileName") if f.text]
        for f in files:
            if not download_data or f in downloaded_files:
                continue
            downloaded_files.add(f)
            output_path = os.path.join(data_output_directory, os.path.basename(f))
            if os.path.isfile(output_path):
                print("File %s already exists locally. Skipping its download" % (output_path))
            else:
                print("Start retrieving of " + f + " at " + str(datetime.datetime.now()) + " :")
                downloadDssFile(BASE_DSS_URL, f, username, password, data_output_directory)
                print("Finished retrieving of " + f + " at " + str(datetime.datetime.now()))
        count = count + 1


if __name__ == "__main__":

    FIELD_ID = ["52926", "53401", "53402", "53403", "53876", "53877", "53878", "54348", "54349"]

    parser = argparse.ArgumentParser()
    parser.add_argument("--username", help="Cosmos or EAS username", required=True)
    parser.add_argument(
        "--password",
        help="user password",
    )
    parser.add_argument("--project", help="EAS project to query", default="EUCLID")
    parser.add_argument("--data_product", help="Data product type name, e.g. DpdMerFinalCatalog", required=True)
    parser.add_argument(
        "--query",
        default="",
        help="Optional product query string. Leave empty to match all products, e.g. \n"
        "Header.ProductId.ObjectId=like*EUC_MER_PPO-TILE*_SC3-PLAN-2-PPO-*-SDC-IT-RUN0-0-final_catalog-0",
    )
    parser.add_argument(
        "--query_chunk_size",
        type=int,
        default=100,
        help="Number of matching product IDs per EAS metadata request (default: 100)",
    )
    parser.add_argument(
        "--download",
        choices=("xml", "data", "both"),
        default="xml",
        help="Output type: xml metadata only, DSS data only, or both (default: xml)",
    )
    parser.add_argument(
        "--xml_output_dir",
        default="eas-xml",
        help="Directory for XML output (default: eas-xml)",
    )
    parser.add_argument(
        "--data_output_dir",
        default="eas-data",
        help="Directory for DSS data output (default: eas-data)",
    )

    args = parser.parse_args()

    username = args.username
    password = args.password

    if password and os.path.isfile(password):
        with open(password) as f:
            password = f.read().replace("\n", "").strip()

    if username and not password:
        import getpass

        password = getpass.getpass("Type password for %s: " % username)

    if args.query_chunk_size < 1:
        parser.error("--query_chunk_size must be a whole number greater than zero")

    product_ids = get_product_ids(BASE_EAS_URL, args.data_product, args.query, args.project, username, password)
    if not product_ids:
        print("No data products found")
        sys.exit(0)

    product_id_chunks = list(chunk_product_ids(product_ids, args.query_chunk_size))
    print(
        "Retrieving %d data products in %d chunk(s) of up to %d product IDs"
        % (len(product_ids), len(product_id_chunks), args.query_chunk_size)
    )

    products = []
    for chunk_index, product_id_chunk in enumerate(product_id_chunks, start=1):
        print(
            "Retrieving chunk %d/%d (%d product IDs)"
            % (chunk_index, len(product_id_chunks), len(product_id_chunk))
        )
        chunk_query = build_chunk_query(args.query, product_id_chunk)
        chunk_products, _ = getMetadataXml(
            BASE_EAS_URL,
            args.data_product,
            chunk_query,
            args.project,
            username,
            password,
        )
        products.extend(chunk_products)

    saveMetaAndData(
        products,
        username,
        password,
        args.data_product,
        args.xml_output_dir,
        args.data_output_dir,
        download_xml=args.download in ("xml", "both"),
        download_data=args.download in ("data", "both"),
    )
