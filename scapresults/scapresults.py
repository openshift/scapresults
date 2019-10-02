import argparse
import time
import os
import sys
import base64
import gzip

import kubernetes


def get_args():
    parser = argparse.ArgumentParser(description='Script watches for existence of a file'
                                                 'and then uploads it to a configMap')
    parser.add_argument('--mode', dest='mode', choices=['incluster', 'outcluster', 'debug'], default='incluster')
    parser.add_argument(
        '--file', type=str, help='The file to watch', dest='filename',
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
    return parser.parse_args()


def create_config_map(name, file_name, result_contents, compressed=False):
    annotations = {}
    if compressed:
        annotations = {
            "openscap-scan-result/compressed": ""
        }
    return kubernetes.client.V1ConfigMap(
        api_version="v1",
        kind="ConfigMap",
        metadata=kubernetes.client.V1ObjectMeta(
            name=name,
            annotations=annotations
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
    args = get_args()
    if args.mode == 'incluster':
        kubernetes.config.load_incluster_config()
    elif args.mode == 'outcluster':
        kubernetes.config.load_kube_config()
    elif args.mode == 'debug':
        # This will just print out the configmap
        pass
    else:
        print(f"Invalid mode {args.mode}")
        return 1

    k8sv1api = kubernetes.client.CoreV1Api()

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

        if result_needs_compression(contents):
            contents = compress_results(contents)
            compressed = True
            print("The results needs compressing")

        confmap = create_config_map(args.config_map,
                                    "results",
                                    contents, compressed=compressed)
        if args.mode == 'debug':
            print(confmap)
        else:
            resp = k8sv1api.create_namespaced_config_map(
                    body=confmap,
                    namespace=args.namespace)
            print("ConfigMap created: %s" % resp.metadata.name)
    return 0

if __name__ == "__main__":
    rv = main()
    sys.exit(rv)
