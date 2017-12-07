from __future__ import print_function
import sys
import argparse
import libvirt
import sched
import time
from prometheus_client import start_http_server, Gauge
from xml.etree import ElementTree


parser = argparse.ArgumentParser(description='libvirt_exporter scrapes domains metrics from libvirt daemon')
parser.add_argument('-si','--scrape_interval', help='scrape interval for metrics in seconds', default= 5)
parser.add_argument('-uri','--uniform_resource_identifier', help='Libvirt Uniform Resource Identifier', default= "qemu:///system")
args = vars(parser.parse_args())
uri = args["uniform_resource_identifier"]


def connect_to_uri(uri):
    conn = libvirt.open(uri)

    if conn == None:
        print('Failed to open connection to ' + uri, file = sys.stderr)
    else:
        print('Successfully connected to ' + uri)
    return conn


def get_domains(conn):

    domains = []

    for id in conn.listDomainsID():
        dom = conn.lookupByID(id)

        if dom == None:
            print('Failed to find the domain ' + dom.name(), file=sys.stderr)
        else:
            domains.append(dom)

    if len(domains) == 0:
        print('No running domains in URI')
        return None
    else:
        return domains


def get_metrics_collections(metric_names, labels, stats):
    dimensions = []
    metrics_collection = {}

    for mn in metric_names:
        if type(stats) is list:
            dimensions = [[stats[0][mn], labels]]
        elif type(stats) is dict:
            dimensions = [[stats[mn], labels]]
        metrics_collection[mn] = dimensions

    return metrics_collection


def get_metrics_multidim_collections(dom, metric_names, device):

    tree = ElementTree.fromstring(dom.XMLDesc())
    targets = []

    for target in tree.findall("devices/" + device + "/target"): # !
        targets.append(target.get("dev"))

    metrics_collection = {}

    for mn in metric_names:
        dimensions = []
        for target in targets:
            labels = {'domain': dom.name()}
            labels['target_device'] = target
            if device == "interface":
                stats = dom.interfaceStats(target) # !
            elif device == "disk":
                stats= dom.blockStats(target)
            stats = dict(zip(metric_names, stats))
            dimension = [stats[mn], labels]
            dimensions.append(dimension)
            labels = None
        metrics_collection[mn] = dimensions

    return metrics_collection


def add_metrics(dom, header_mn, g_dict):

    labels = {'domain':dom.name()}

    if header_mn == "libvirt_cpu_stats_":

        stats = dom.getCPUStats(True)
        metric_names = stats[0].keys()
        metrics_collection = get_metrics_collections(metric_names, labels, stats)
        unit = "_nanosecs"

    elif header_mn == "libvirt_mem_stats_":
        stats = dom.memoryStats()
        metric_names = stats.keys()
        metrics_collection = get_metrics_collections(metric_names, labels, stats)
        unit = ""

    elif header_mn == "libvirt_block_stats_":

        metric_names = \
        ['read_requests_issued',
        'read_bytes' ,
        'write_requests_issued',
        'write_bytes',
        'errors_number']

        metrics_collection = get_metrics_multidim_collections(dom, metric_names, device="disk")
        unit = ""

    elif header_mn == "libvirt_interface_":

        metric_names = \
        ['read_bytes',
        'read_packets',
        'read_errors',
        'read_drops',
        'write_bytes',
        'write_packets',
        'write_errors',
        'write_drops']

        metrics_collection = get_metrics_multidim_collections(dom, metric_names, device="interface")
        unit = ""

    for mn in metrics_collection:
        metric_name = header_mn + mn + unit
        dimensions = metrics_collection[mn]

        if metric_name not in g_dict.keys():

            metric_help = 'help'
            labels_names = metrics_collection[mn][0][1].keys()

            g_dict[metric_name] = Gauge(metric_name, metric_help, labels_names)

            for dimension in dimensions:
                dimension_metric_value = dimension[0]
                dimension_label_values = dimension[1].values()
                g_dict[metric_name].labels(*dimension_label_values).set(dimension_metric_value)
        else:
            for dimension in dimensions:
                dimension_metric_value = dimension[0]
                dimension_label_values = dimension[1].values()
                g_dict[metric_name].labels(*dimension_label_values).set(dimension_metric_value)
    return g_dict


def job(uri, g_dict, scheduler):
    print('BEGIN JOB :', time.time())
    conn = connect_to_uri(uri)
    domains = get_domains(conn)
    while domains is None:
        domains = get_domains(conn)
        time.sleep(int(args["scrape_interval"]))

    for dom in domains:

        print(dom.name())

        headers_mn = ["libvirt_cpu_stats_", "libvirt_mem_stats_", \
                      "libvirt_block_stats_", "libvirt_interface_"]

        for header_mn in headers_mn:
            g_dict = add_metrics(dom, header_mn, g_dict)

    conn.close()
    print('FINISH JOB :', time.time())
    scheduler.enter((int(args["scrape_interval"])), 1, job, (uri, g_dict, scheduler))


def main():

    start_http_server(9177)

    g_dict = {}

    scheduler = sched.scheduler(time.time, time.sleep)
    print('START:', time.time())
    scheduler.enter(0, 1, job, (uri, g_dict, scheduler))
    scheduler.run()

if __name__ == '__main__':
    main()
