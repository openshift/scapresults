import argparse
import sys
import os
import os.path
import base64
import gzip

import kubernetes
from kubernetes.client.rest import ApiException

CRD_GROUP = "complianceoperator.compliance.openshift.io"
CRD_API_VERSION = "v1alpha1"
CRD_PLURALS = "compliancescans"


COMPRESSED_ANNOTATION = "openscap-scan-result/compressed"


def get_args():
    parser = argparse.ArgumentParser(description='Script fetches all configmaps owned'
                                                 'by an OpenScap object and then'
                                                 'extracts the contents to files')
    parser.add_argument(
        '--configmap', type=str, help='Just retrieve this one configmap, no questions asked', dest='configmap',
        default=None)
    parser.add_argument(
        '--owner', type=str, help='The openscap scan that owns the configMap objects', dest='scan_name',
        default=None)
    parser.add_argument(
        '--namespace', type=str, help='Running pod namespace', dest='namespace',
        default=None, required=True)
    parser.add_argument(
        '--dir', type=str, help='The directory to write the results to', dest='directory',
        default=".")
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


def is_same_owner(cm_owner_reference, scan_instance):
    for reference in cm_owner_reference:
        if reference.api_version == scan_instance['apiVersion'] and \
           reference.kind == scan_instance['kind'] and \
           reference.name == scan_instance['metadata']['name'] and \
           reference.uid == scan_instance['metadata']['uid']:
            return True

    return False


def get_config_maps(k8sv1api, scan_instance, namespace):
    try:
        cmap_list = k8sv1api.list_namespaced_config_map(namespace)
    except ApiException as e:
        print("Exception when calling CoreV1Api->list_namespaced_config_map: %s\n" % e)

    # Filter only those maps that are owned by the scan CR
    return [cm for cm in cmap_list.items if is_same_owner(cm.metadata.owner_references, scan_instance)]


def decompress_results(contents):
    return gzip.decompress(base64.b64decode(contents)).decode()


def write_map_results(maps, directory):
    os.makedirs(directory, exist_ok=True)

    for m in maps:
        decompress = False
        if m.metadata.annotations and COMPRESSED_ANNOTATION in m.metadata.annotations:
            decompress = True

        for key, value in m.data.items():
            if decompress:
                value = decompress_results(value)

            filename = m.metadata.name + '-' + key
            with open(os.path.join(directory, filename), 'w') as f:
                f.write(value)


def main():
    """Main entrypoint"""

    kubernetes.config.load_kube_config()
    args = get_args()

    k8sv1api = kubernetes.client.CoreV1Api()

    configuration = kubernetes.client.Configuration()
    api_instance = kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient(configuration))
    scan_instance = get_openscap_scan_instance(api_instance,
                                               args.scan_name,
                                               args.namespace)
    if scan_instance is None:
        print(f"Scan {args.scan_name} in namespace {args.namespace} does not exist")
        return 0

    maps = get_config_maps(k8sv1api, scan_instance, args.namespace)
    write_map_results(maps, args.directory)
    return 0

if __name__ == "__main__":
    rv = main()
    sys.exit(rv)
