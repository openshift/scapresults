import argparse
import time
import os
import sys
import base64
import gzip

import kubernetes
from kubernetes.client.rest import ApiException

# CRD definitions
CRD_GROUP = "openscap.compliance.openshift.io"
CRD_API_VERSION = "v1alpha1"
CRD_PLURALS = "openscaps"

def get_args():
    parser = argparse.ArgumentParser(description='Script watches for existence of a file'
                                                 'and then uploads it to a configMap')
    parser.add_argument(
        '--file', type=str, help='The file to watch', dest='filename',
        default=None, required=True)
    parser.add_argument(
        '--owner', type=str, help='The openscap scan that owns the configMap objects', dest='scan_name',
        default=None, required=True)
    parser.add_argument(
        '--config-map-name', type=str, help='The configMap to upload to, typically the podname', dest='config_map',
        default=None, required=True)
    parser.add_argument(
        '--namespace', type=str, help='Running pod namespace', dest='namespace',
        default=None, required=True)
    parser.add_argument(
        '--timeout', type=int, help='How long to wait for the file', dest='timeout',
        default=3600)
    parser.add_argument(
        '--compress', type=bool, help='Always compress the results', dest='compress',
        default=False)
    return parser.parse_args()


def get_openscap_scan_instance(custom_api, scan_name, namespace):
    try:
        openscap_scan = custom_api.get_namespaced_custom_object(
                CRD_GROUP,
                CRD_API_VERSION,
                namespace,
                CRD_PLURALS,
                scan_name)
    except ApiException as e:
        if e.status == 404:
            return None
        raise e
    return openscap_scan


def create_config_map(owner, name, file_name, result_contents, compressed=False):
    annotations = {}
    if compressed:
        annotations = {
            "openscap-scan-result/compressed": ""
        }

    scan_reference = kubernetes.client.V1OwnerReference(
        api_version=owner['apiVersion'],
        kind=owner['kind'],
        name=owner['metadata']['name'],
        uid=owner['metadata']['uid'],
    )

    return kubernetes.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=kubernetes.client.V1ObjectMeta(
            name=name,
            annotations=annotations,
            owner_references = [ scan_reference ],
        ),
        data={
            file_name: result_contents
        }
    )


def result_needs_compression(contents):
    return len(contents) > 1048570


def compress_results(contents):
    # Encode the contents ascii, compress it with gzip, b64encode it so it
    # can be stored in the configmap, and finally pass the bytes to a UTF-8
    # python3 string.
    return base64.b64encode(gzip.compress(contents.encode('ascii'))).decode()


def main():
    """Main entrypoint"""

    if 'KUBERNETES_PORT' in os.environ:
        kubernetes.config.load_incluster_config()
    else:
        kubernetes.config.load_kube_config()

    args = get_args()
    k8sv1api = kubernetes.client.CoreV1Api()

    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient(configuration))
    scan_instance = get_openscap_scan_instance(api_instance,
                                               args.scan_name,
                                               args.namespace)
    if scan_instance == None:
        print(f"Scan {scan_name} in namespace {namespace} does not exist")
        return 0

    time_waited = 0
    while not os.path.exists(args.filename):
        time.sleep(1)
        time_waited += 1
        if time_waited > args.timeout:
            print("Timeout")
            return 1

    print(f"file {args.filename} found, will upload it")
    with open(args.filename, 'r') as result_file:
        contents = result_file.read()
        compressed = False

        if result_needs_compression(contents) or args.compress:
            contents = compress_results(contents)
            compressed = True
            print("The results needs compressing")

        confmap = create_config_map(scan_instance,
                                    args.config_map,
                                    "results",
                                    contents, compressed=compressed)
        print(confmap)
        resp = k8sv1api.create_namespaced_config_map(
                body=confmap,
                namespace=args.namespace)
        print("ConfigMap created: %s" % resp.metadata.name)
    return 0

if __name__ == "__main__":
    rv = main()
    sys.exit(rv)
